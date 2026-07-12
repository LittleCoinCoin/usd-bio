#!/usr/bin/env python3
"""
Build a topology-only USD assembly from a parsed PDB structure.

Generalized from foundation_demo_v8/templates/04_create_assembly.py (R00:
generalize -- the reference LIVERPS-applied architecture). What is carried:

- Inherits arc as biological taxonomy: every atom ``inherits`` /_class_/<symbol>.
- Local opinions: atom positions authored as LOCAL xformOp:translate (Ångström).
- VariantSet cascade: a ``representation`` VariantSet at complex -> chain ->
  residue -> atom, so switching the root switches the whole hierarchy.
- Intra-residue + inter-residue (peptide) bonds as cylinders visible only in
  the ``ballstick`` mode.

What is generalized off ABL specifics (anti-chimera invariants, R00):

- The ``/ABLComplex`` root literal is GONE; the root prim path is the
  ``root_path`` PARAMETER (default :data:`p53_env.DEFAULT_ROOT_PATH`).
- v8's duplicated ATP/cap ``EXTRA_BONDS`` table is GONE; non-standard bond
  connectivity is a caller-supplied ``extra_bonds`` dict (default empty).
- The fragile ``sys.path`` reach into ``composition_advanced`` and the
  ShinobuLab provenance import are GONE (provenance is a Pipeline-2 concern).
- Element class templates are authored INLINE into the same stage (only the
  elements the structure actually uses), so the emitted artifact is a single
  self-contained .usda whose /_class_/<symbol> inherits resolve on open.
- No hard-coded atom counts; ``bio:atomCount`` is computed from the structure.
"""

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from pxr import Usd, UsdGeom, Sdf, Gf

from p53_mdm2 import p53_env
from p53_mdm2.data import RESIDUES
from p53_mdm2.converters.pdb_parser import parse_pdb, DEFAULT_SOLVENT_IONS
from p53_mdm2.builders.element_templates import build_element_classes

REPRESENTATIONS = list(p53_env.DEFAULT_REPRESENTATIONS)
BOND_RADIUS = 0.1  # Ångström


def sanitize_name(name: str) -> str:
    """Make a string safe as a USD prim name (no +, -, *, ', no leading digit)."""
    result = name.replace("+", "plus").replace("-", "minus")
    result = result.replace("*", "s").replace("'", "p")
    if result and result[0].isdigit():
        result = "_" + result
    return result


def get_bond_pairs(residue_name: str, extra_bonds: dict) -> list:
    """Bond pairs for a residue: standard RESIDUES table, then caller extras."""
    if residue_name in RESIDUES:
        return RESIDUES[residue_name]["bonds"]
    if residue_name in extra_bonds:
        return extra_bonds[residue_name]
    return []


def create_bond_geometry(stage, bond_path, pos1, pos2):
    """Create a cylinder bond aligned between two atom positions."""
    p1 = Gf.Vec3d(*pos1)
    p2 = Gf.Vec3d(*pos2)
    midpoint = (p1 + p2) / 2
    bond_vec = p2 - p1
    bond_length = bond_vec.GetLength()

    bond_xform = UsdGeom.Xform.Define(stage, bond_path)
    bond_prim = bond_xform.GetPrim()
    bond_xform.AddTranslateOp().Set(midpoint)

    y_axis = Gf.Vec3d(0, 1, 0)
    bond_dir = bond_vec.GetNormalized()
    rot_axis = y_axis ^ bond_dir
    if rot_axis.GetLength() > 0.001:
        rot_axis = rot_axis.GetNormalized()
        cos_angle = y_axis * bond_dir
        angle_deg = math.degrees(math.acos(max(-1, min(1, cos_angle))))
        rotation = Gf.Rotation(Gf.Vec3d(rot_axis), angle_deg)
        bond_xform.AddOrientOp().Set(Gf.Quatf(rotation.GetQuat()))

    cyl = UsdGeom.Cylinder.Define(stage, f"{bond_path}/Cylinder")
    cyl.CreateHeightAttr(bond_length)
    cyl.CreateRadiusAttr(BOND_RADIUS)
    cyl.CreateAxisAttr("Y")
    cyl.CreateDisplayColorAttr([Gf.Vec3f(0.5, 0.5, 0.5)])
    return bond_prim


def _add_representation_variants(prim, representations):
    """Add a representation VariantSet with the given modes (no selection)."""
    vset = prim.GetVariantSets().AddVariantSet("representation")
    for mode in representations:
        vset.AddVariant(mode)
    vset.ClearVariantSelection()
    return vset


def _set_bond_visibility_variants(bond_prim, representations):
    """Bond is visible only in ballstick; invisible in every other mode."""
    vset = bond_prim.GetVariantSets().AddVariantSet("representation")
    for mode in representations:
        vset.AddVariant(mode)
    for mode in representations:
        vset.SetVariantSelection(mode)
        with vset.GetVariantEditContext():
            vis = "inherited" if mode == "ballstick" else "invisible"
            UsdGeom.Imageable(bond_prim).CreateVisibilityAttr(vis)
    vset.ClearVariantSelection()
    return vset


def build_assembly(
    output_path: str,
    pdb_path: str,
    *,
    root_path: str = None,
    system_name: str = "p53-MDM2 complex",
    exclude_residues=DEFAULT_SOLVENT_IONS,
    ligand_residues=frozenset(),
    extra_bonds: dict = None,
    representations=None,
) -> str:
    """Emit a topology-only .usda for the parsed PDB structure.

    Args:
        output_path: destination .usda path.
        pdb_path: source PDB file.
        root_path: USD root prim path (PARAMETER; default
            :data:`p53_env.DEFAULT_ROOT_PATH` -- never ``/ABLComplex``).
        system_name: value for ``bio:systemName`` on the root prim.
        exclude_residues / ligand_residues: passed through to ``parse_pdb``.
        extra_bonds: optional {residue_name: [(a1,a2),...]} for non-standard
            connectivity (default empty -- standard residues use RESIDUES).
        representations: visual-mode variant names (default the 4 canonical).

    Returns:
        ``output_path``.
    """
    if root_path is None:
        root_path = p53_env.DEFAULT_ROOT_PATH
    if extra_bonds is None:
        extra_bonds = {}
    if representations is None:
        representations = REPRESENTATIONS

    print(f"Parsing PDB: {pdb_path}")
    structure = parse_pdb(
        pdb_path, exclude_residues=exclude_residues, ligand_residues=ligand_residues
    )
    print(f"  Chains: {structure.chain_ids}, Atoms: {structure.atom_count}, "
          f"Elements: {sorted(structure.elements)}")

    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    # Stage metadata authored directly (no patch_stage_metadata tool -- PI Q-001).
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, p53_env.METERS_PER_UNIT)  # 1 Å = 1e-10 m
    stage.SetMetadata("comment",
                      f"{system_name} topology from {os.path.basename(pdb_path)}")

    # Element class templates authored INLINE (only elements in use) so the
    # artifact is self-contained and /_class_/<symbol> inherits resolve on open.
    build_element_classes(stage, symbols=sorted(structure.elements),
                          representations=representations)

    # ----- COMPLEX ROOT -----
    complex_xform = UsdGeom.Xform.Define(stage, root_path)
    complex_prim = complex_xform.GetPrim()
    stage.SetDefaultPrim(complex_prim)

    complex_prim.CreateAttribute("bio:systemName", Sdf.ValueTypeNames.String).Set(system_name)
    complex_prim.CreateAttribute("bio:sourceStructure", Sdf.ValueTypeNames.String).Set(
        os.path.basename(pdb_path))
    complex_prim.CreateAttribute("bio:atomCount", Sdf.ValueTypeNames.Int).Set(
        structure.atom_count)
    complex_prim.CreateAttribute("bio:chainCount", Sdf.ValueTypeNames.Int).Set(
        len(structure.chains))
    complex_vset = _add_representation_variants(complex_prim, representations)

    chain_prims = []

    for chain_id, chain in structure.chains.items():
        chain_path = f"{root_path}/Chain_{sanitize_name(chain_id)}"
        chain_prim = UsdGeom.Xform.Define(stage, chain_path).GetPrim()
        chain_atom_count = sum(len(r.atoms) for r in chain.residues.values())
        chain_prim.CreateAttribute("bio:chainID", Sdf.ValueTypeNames.Token).Set(chain_id)
        chain_prim.CreateAttribute("bio:chainType", Sdf.ValueTypeNames.Token).Set(chain.chain_type)
        chain_prim.CreateAttribute("bio:residueCount", Sdf.ValueTypeNames.Int).Set(len(chain.residues))
        chain_prim.CreateAttribute("bio:atomCount", Sdf.ValueTypeNames.Int).Set(chain_atom_count)
        chain_vset = _add_representation_variants(chain_prim, representations)
        chain_prims.append(chain_prim)

        for res_seq, residue in chain.residues.items():
            res_label = f"{sanitize_name(residue.name)}_{res_seq}"
            res_path = f"{chain_path}/{res_label}"
            res_prim = UsdGeom.Xform.Define(stage, res_path).GetPrim()
            res_prim.CreateAttribute("bio:residueName", Sdf.ValueTypeNames.Token).Set(residue.name)
            res_prim.CreateAttribute("bio:residueSeq", Sdf.ValueTypeNames.Int).Set(res_seq)
            res_prim.CreateAttribute("bio:atomCount", Sdf.ValueTypeNames.Int).Set(len(residue.atoms))
            res_vset = _add_representation_variants(res_prim, representations)

            res_atom_prims = []
            res_bond_prims = []
            atom_positions = {}

            for atom in residue.atoms:
                atom_path = f"{res_path}/{sanitize_name(atom.name)}"
                atom_xform = UsdGeom.Xform.Define(stage, atom_path)
                atom_prim = atom_xform.GetPrim()
                # Inherits arc -> element-class taxonomy.
                atom_prim.GetInherits().AddInherit(f"/_class_/{atom.element}")
                # LOCAL position (strongest local opinion).
                atom_xform.AddTranslateOp().Set(Gf.Vec3d(atom.x, atom.y, atom.z))
                atom_prim.CreateAttribute("bio:atomName", Sdf.ValueTypeNames.Token).Set(atom.name)
                atom_prim.CreateAttribute("bio:element", Sdf.ValueTypeNames.Token).Set(atom.element)
                atom_prim.CreateAttribute("bio:serial", Sdf.ValueTypeNames.Int).Set(atom.serial)
                _add_representation_variants(atom_prim, representations)
                res_atom_prims.append(atom_prim)
                atom_positions[atom.name] = (atom.x, atom.y, atom.z)

            # intra-residue bonds
            for a1, a2 in get_bond_pairs(residue.name, extra_bonds):
                if a1 not in atom_positions or a2 not in atom_positions:
                    continue
                bond_path = f"{res_path}/Bond_{sanitize_name(a1)}_{sanitize_name(a2)}"
                bond_prim = create_bond_geometry(
                    stage, bond_path, atom_positions[a1], atom_positions[a2])
                _set_bond_visibility_variants(bond_prim, representations)
                res_bond_prims.append(bond_prim)

            # residue cascade -> atoms + bonds
            for mode in representations:
                res_vset.SetVariantSelection(mode)
                with res_vset.GetVariantEditContext():
                    for ap in res_atom_prims:
                        ap.GetVariantSets().GetVariantSet("representation").SetVariantSelection(mode)
                    for bp in res_bond_prims:
                        bp.GetVariantSets().GetVariantSet("representation").SetVariantSelection(mode)
            res_vset.ClearVariantSelection()

        # inter-residue peptide bonds (C_i -> N_{i+1})
        peptide_bond_prims = []
        res_seq_list = list(chain.residues.keys())
        for idx in range(len(res_seq_list) - 1):
            res_i = chain.residues[res_seq_list[idx]]
            res_j = chain.residues[res_seq_list[idx + 1]]
            c_pos = next((( a.x, a.y, a.z) for a in res_i.atoms if a.name == "C"), None)
            n_pos = next(((a.x, a.y, a.z) for a in res_j.atoms if a.name == "N"), None)
            if c_pos is None or n_pos is None:
                continue
            ri = f"{sanitize_name(res_i.name)}_{res_i.seq}"
            rj = f"{sanitize_name(res_j.name)}_{res_j.seq}"
            bond_path = f"{chain_path}/PeptideBond_{ri}__{rj}"
            bond_prim = create_bond_geometry(stage, bond_path, c_pos, n_pos)
            _set_bond_visibility_variants(bond_prim, representations)
            peptide_bond_prims.append(bond_prim)

        # chain cascade -> residues + peptide bonds
        chain_res_prims = [
            stage.GetPrimAtPath(f"{chain_path}/{sanitize_name(r.name)}_{r.seq}")
            for r in chain.residues.values()
        ]
        for mode in representations:
            chain_vset.SetVariantSelection(mode)
            with chain_vset.GetVariantEditContext():
                for rp in chain_res_prims:
                    rp.GetVariantSets().GetVariantSet("representation").SetVariantSelection(mode)
                for bp in peptide_bond_prims:
                    bp.GetVariantSets().GetVariantSet("representation").SetVariantSelection(mode)
        chain_vset.ClearVariantSelection()

    # complex cascade -> chains
    for mode in representations:
        complex_vset.SetVariantSelection(mode)
        with complex_vset.GetVariantEditContext():
            for cp in chain_prims:
                cp.GetVariantSets().GetVariantSet("representation").SetVariantSelection(mode)
    complex_vset.ClearVariantSelection()

    stage.Save()

    bond_count = sum(
        1 for p in stage.Traverse()
        if p.GetName().startswith(("Bond_", "PeptideBond_"))
    )
    print(f"\nCreated: {output_path}")
    print(f"  Root: {root_path}")
    print(f"  Chains: {len(structure.chains)}  Residues: {structure.residue_count}  "
          f"Atoms: {structure.atom_count}  Bonds: {bond_count}")
    return output_path


if __name__ == "__main__":
    out_dir = p53_env.output_dir()
    os.makedirs(out_dir, exist_ok=True)
    build_assembly(
        os.path.join(out_dir, "p53_mdm2_topology.usda"),
        p53_env.get_structure_path("1ycr.pdb"),
        system_name="p53-MDM2 complex (1YCR)",
    )
