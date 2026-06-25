#!/usr/bin/env python3
"""
Create ABL kinase + ATP assembly using AddReference for element templates.

Patterns applied:
- 05_references_arc.md: AddReference to pull element library into a namespace
- 02_inherits_arc.md: Atoms inherit from namespaced element class templates
- 01_local_opinions.md: Atom positions are LOCAL (strongest in LIVRPS)
- 03_variantsets_arc.md: Variant cascade from complex -> chain -> residue -> atom
- 08_schemas_attributes.md: Custom bio: namespace for scientific metadata

Key difference from 04_create_assembly.py (SubLayer style):
    SubLayer style:
        stage.GetRootLayer().subLayerPaths.append("element_templates.usda")
        atom_prim.GetInherits().AddInherit("/_class_/C")

    Reference style (this script):
        elem_lib_prim.GetReferences().AddReference("element_library.usda")
        atom_prim.GetInherits().AddInherit("/ElementLib/_ElementLibrary/_class_/C")

    The dependency is now explicit and namespace-encapsulated under /ElementLib.
    /_class_/C is NOT visible at the stage root — the library is hidden
    behind the /ElementLib prim path.

Hierarchy:
  /ABLComplex
    /Chain_A
      /ACE_1
        /HH31  (inherits /ElementLib/_ElementLibrary/_class_/H)
        /CH3   (inherits /ElementLib/_ElementLibrary/_class_/C)
        ...
      /SER_2
        /N     (inherits /ElementLib/_ElementLibrary/_class_/N)
        ...
    /Chain_B
      ...
    /Chain_L
      /atp_293
        ...
  /ElementLib  (references element_library.usda; default prim /_ElementLibrary maps here)
"""

import os
import sys
import math

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from usdbio_env import get_data_dir
from pxr import Usd, UsdGeom, Sdf, Gf
from converters.pdb_parser import parse_pdb
from data import RESIDUES


REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]

# Default PDB path — root from environment; fails loudly if USDBIO_DATA_DIR is unset
DEFAULT_PDB = os.path.join(get_data_dir(), "files", "atp-complex-solv35.pdb")

# The /ElementLib prim path where element_library.usda is referenced in
ELEMENT_LIB_PRIM = "/ElementLib"

# The class prim namespace after reference composition:
# /ElementLib + /_ElementLibrary + /_class_/<Symbol>
# (because element_library.usda's default prim is /_ElementLibrary, it maps
# onto /ElementLib; children of /_ElementLibrary become children of /ElementLib)
ELEMENT_CLASS_PREFIX = f"{ELEMENT_LIB_PRIM}/_class_"


def sanitize_name(name: str) -> str:
    """Make a string safe for use as a USD prim name."""
    result = name.replace("+", "plus").replace("-", "minus")
    result = result.replace("*", "s").replace("'", "p")
    if result and result[0].isdigit():
        result = "_" + result
    return result


BOND_RADIUS = 0.1  # Å

# Bond connectivity for residues not in RESIDUES (heavy atoms only)
EXTRA_BONDS = {
    "ACE": [("CH3", "C"), ("C", "O")],
    "NME": [("N", "CH3")],
    # AMBER histidine variants — same heavy-atom bonds as HIS
    "HID": RESIDUES["HIS"]["bonds"],
    "HIE": RESIDUES["HIS"]["bonds"],
    "HIP": RESIDUES["HIS"]["bonds"],
    # ATP: triphosphate + ribose + adenine (heavy atoms)
    "atp": [
        ("PG", "O1G"), ("PG", "O2G"), ("PG", "O3G"), ("PG", "O3B"),
        ("O3B", "PB"), ("PB", "O1B"), ("PB", "O2B"), ("PB", "O3A"),
        ("O3A", "PA"), ("PA", "O1A"), ("PA", "O2A"), ("PA", "O5*"),
        ("O5*", "C5*"), ("C5*", "C4*"), ("C4*", "O4*"), ("C4*", "C3*"),
        ("O4*", "C1*"), ("C1*", "N9"), ("C1*", "C2*"),
        ("C2*", "O2*"), ("C2*", "C3*"), ("C3*", "O3*"),
        ("N9", "C8"), ("N9", "C4"), ("C8", "N7"), ("N7", "C5"),
        ("C5", "C6"), ("C5", "C4"), ("C6", "N6"), ("C6", "N1"),
        ("N1", "C2"), ("C2", "N3"), ("N3", "C4"),
    ],
}


def get_bond_pairs(residue_name: str) -> list:
    """Get bond pairs for a residue, checking RESIDUES then EXTRA_BONDS."""
    if residue_name in RESIDUES:
        return RESIDUES[residue_name]["bonds"]
    if residue_name in EXTRA_BONDS:
        return EXTRA_BONDS[residue_name]
    return []


def create_bond_geometry(stage, bond_path, pos1, pos2):
    """Create a cylinder bond between two atom positions."""
    p1 = Gf.Vec3d(*pos1)
    p2 = Gf.Vec3d(*pos2)
    midpoint = (p1 + p2) / 2
    bond_vec = p2 - p1
    bond_length = bond_vec.GetLength()

    bond_xform = UsdGeom.Xform.Define(stage, bond_path)
    bond_prim = bond_xform.GetPrim()
    bond_xform.AddTranslateOp().Set(midpoint)

    # Rotate cylinder (Y-axis) to align with bond direction
    y_axis = Gf.Vec3d(0, 1, 0)
    bond_dir = bond_vec.GetNormalized()

    rot_axis = y_axis ^ bond_dir  # cross product
    if rot_axis.GetLength() > 0.001:
        rot_axis = rot_axis.GetNormalized()
        cos_angle = y_axis * bond_dir  # dot product
        angle_deg = math.degrees(math.acos(max(-1, min(1, cos_angle))))
        rotation = Gf.Rotation(Gf.Vec3d(rot_axis), angle_deg)
        quat = rotation.GetQuat()
        bond_xform.AddOrientOp().Set(Gf.Quatf(quat))

    cyl = UsdGeom.Cylinder.Define(stage, f"{bond_path}/Cylinder")
    cyl.CreateHeightAttr(bond_length)
    cyl.CreateRadiusAttr(BOND_RADIUS)
    cyl.CreateAxisAttr("Y")
    cyl.CreateDisplayColorAttr([Gf.Vec3f(0.5, 0.5, 0.5)])

    return bond_prim


def create_assembly_refstyle(
    output_path: str,
    pdb_path: str,
    element_library_path: str,
):
    """
    Create USD assembly from PDB data using AddReference for element templates.

    Parameters
    ----------
    output_path : str
        Path to write abl_kinase_complex_refstyle.usda.
    pdb_path : str
        Path to the PDB file (atp-complex-solv35.pdb).
    element_library_path : str
        Path to element_library.usda (the reference-friendly asset with
        default prim /_ElementLibrary).
    """
    # Parse PDB
    print(f"Parsing PDB: {pdb_path}")
    structure = parse_pdb(pdb_path)
    print(f"  Chains: {structure.chain_ids}, Atoms: {structure.atom_count}")

    # Clean start
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # coordinates in Ångström
    stage.SetMetadata(
        "comment",
        "ABL kinase + ATP assembly (reference style) — element templates "
        "loaded via AddReference into /ElementLib rather than SubLayer.",
    )

    # =========================================================================
    # ELEMENT LIBRARY REFERENCE — pulls element_library.usda into /ElementLib
    #
    # USD resolves the reference by mapping element_library.usda's default
    # prim (/_ElementLibrary) onto /ElementLib.  The class hierarchy becomes
    # reachable as /ElementLib/_class_/<Symbol>.
    # =========================================================================
    elem_lib_xform = UsdGeom.Xform.Define(stage, ELEMENT_LIB_PRIM)
    elem_lib_prim = elem_lib_xform.GetPrim()

    # Compute a relative path from the output file's directory to the library
    rel_lib_path = os.path.relpath(
        element_library_path, os.path.dirname(output_path)
    )
    elem_lib_prim.GetReferences().AddReference(rel_lib_path)

    # =========================================================================
    # COMPLEX ROOT
    # =========================================================================
    complex_path = "/ABLComplex"
    complex_xform = UsdGeom.Xform.Define(stage, complex_path)
    complex_prim = complex_xform.GetPrim()
    stage.SetDefaultPrim(complex_prim)

    # Bio metadata on complex root
    complex_prim.CreateAttribute("bio:systemName", Sdf.ValueTypeNames.String).Set(
        "ABL kinase + ATP complex (reference style)")
    complex_prim.CreateAttribute("bio:source", Sdf.ValueTypeNames.String).Set(
        "ShinobuLab MD simulation")
    complex_prim.CreateAttribute("bio:atomCount", Sdf.ValueTypeNames.Int).Set(
        structure.atom_count)
    complex_prim.CreateAttribute("bio:chainCount", Sdf.ValueTypeNames.Int).Set(
        len(structure.chains))

    # Complex-level representation VariantSet
    complex_vset = complex_prim.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        complex_vset.AddVariant(mode)

    # =========================================================================
    # BUILD HIERARCHY: Complex -> Chain -> Residue -> Atom
    # =========================================================================
    chain_prims = []
    residue_prims = []
    atom_prims = []

    for chain_id, chain in structure.chains.items():
        chain_label = f"Chain_{chain_id}"
        chain_path = f"{complex_path}/{chain_label}"
        chain_xform = UsdGeom.Xform.Define(stage, chain_path)
        chain_prim = chain_xform.GetPrim()

        # Chain bio metadata
        chain_atom_count = sum(len(r.atoms) for r in chain.residues.values())
        chain_prim.CreateAttribute("bio:chainID", Sdf.ValueTypeNames.Token).Set(chain_id)
        chain_prim.CreateAttribute("bio:chainType", Sdf.ValueTypeNames.Token).Set(chain.chain_type)
        chain_prim.CreateAttribute("bio:residueCount", Sdf.ValueTypeNames.Int).Set(
            len(chain.residues))
        chain_prim.CreateAttribute("bio:atomCount", Sdf.ValueTypeNames.Int).Set(chain_atom_count)

        # Chain-level VariantSet
        chain_vset = chain_prim.GetVariantSets().AddVariantSet("representation")
        for mode in REPRESENTATIONS:
            chain_vset.AddVariant(mode)
        chain_vset.ClearVariantSelection()
        chain_prims.append(chain_prim)

        for res_seq, residue in chain.residues.items():
            res_label = f"{sanitize_name(residue.name)}_{res_seq}"
            res_path = f"{chain_path}/{res_label}"
            res_xform = UsdGeom.Xform.Define(stage, res_path)
            res_prim = res_xform.GetPrim()

            # Residue bio metadata
            res_prim.CreateAttribute("bio:residueName", Sdf.ValueTypeNames.Token).Set(
                residue.name)
            res_prim.CreateAttribute("bio:residueSeq", Sdf.ValueTypeNames.Int).Set(res_seq)
            res_prim.CreateAttribute("bio:atomCount", Sdf.ValueTypeNames.Int).Set(
                len(residue.atoms))

            # Residue-level VariantSet
            res_vset = res_prim.GetVariantSets().AddVariantSet("representation")
            for mode in REPRESENTATIONS:
                res_vset.AddVariant(mode)
            res_vset.ClearVariantSelection()
            residue_prims.append(res_prim)

            res_atom_prims = []
            res_bond_prims = []
            atom_positions = {}

            for atom in residue.atoms:
                atom_label = sanitize_name(atom.name)
                atom_path = f"{res_path}/{atom_label}"
                atom_xform = UsdGeom.Xform.Define(stage, atom_path)
                atom_prim = atom_xform.GetPrim()

                # Inherit from NAMESPACED element class template.
                # Reference style: /ElementLib/_class_/<Symbol>
                # (SubLayer style used /_class_/<Symbol> at root)
                inherit_path = f"{ELEMENT_CLASS_PREFIX}/{atom.element}"
                atom_prim.GetInherits().AddInherit(inherit_path)

                # LOCAL position (strongest in LIVRPS)
                atom_xform.AddTranslateOp().Set(Gf.Vec3d(atom.x, atom.y, atom.z))

                # Atom bio metadata
                atom_prim.CreateAttribute("bio:atomName", Sdf.ValueTypeNames.Token).Set(
                    atom.name)
                atom_prim.CreateAttribute("bio:element", Sdf.ValueTypeNames.Token).Set(
                    atom.element)
                atom_prim.CreateAttribute("bio:serial", Sdf.ValueTypeNames.Int).Set(
                    atom.serial)

                # Atom-level VariantSet
                atom_vset = atom_prim.GetVariantSets().AddVariantSet("representation")
                for mode in REPRESENTATIONS:
                    atom_vset.AddVariant(mode)
                atom_vset.ClearVariantSelection()

                atom_prims.append(atom_prim)
                res_atom_prims.append(atom_prim)
                atom_positions[atom.name] = (atom.x, atom.y, atom.z)

            # =================================================================
            # INTRA-RESIDUE BONDS (heavy-atom connectivity)
            # =================================================================
            bond_pairs = get_bond_pairs(residue.name)
            for atom1_name, atom2_name in bond_pairs:
                if atom1_name not in atom_positions or atom2_name not in atom_positions:
                    continue
                bond_label = f"Bond_{sanitize_name(atom1_name)}_{sanitize_name(atom2_name)}"
                bond_path = f"{res_path}/{bond_label}"
                bond_prim = create_bond_geometry(
                    stage, bond_path,
                    atom_positions[atom1_name], atom_positions[atom2_name]
                )
                bond_vset = bond_prim.GetVariantSets().AddVariantSet("representation")
                for mode in REPRESENTATIONS:
                    bond_vset.AddVariant(mode)
                for mode in REPRESENTATIONS:
                    bond_vset.SetVariantSelection(mode)
                    with bond_vset.GetVariantEditContext():
                        vis = "inherited" if mode == "ballstick" else "invisible"
                        UsdGeom.Imageable(bond_prim).CreateVisibilityAttr(vis)
                bond_vset.ClearVariantSelection()
                res_bond_prims.append(bond_prim)

            # Residue variant cascade -> atoms + bonds
            for mode in REPRESENTATIONS:
                res_vset.SetVariantSelection(mode)
                with res_vset.GetVariantEditContext():
                    for ap in res_atom_prims:
                        ap.GetVariantSets().GetVariantSet(
                            "representation").SetVariantSelection(mode)
                    for bp in res_bond_prims:
                        bp.GetVariantSets().GetVariantSet(
                            "representation").SetVariantSelection(mode)
            res_vset.ClearVariantSelection()

        # =================================================================
        # INTER-RESIDUE PEPTIDE BONDS (C_i -> N_{i+1})
        # =================================================================
        peptide_bond_prims = []
        res_seq_list = list(chain.residues.keys())
        for idx in range(len(res_seq_list) - 1):
            seq_i = res_seq_list[idx]
            seq_j = res_seq_list[idx + 1]
            res_i = chain.residues[seq_i]
            res_j = chain.residues[seq_j]

            c_pos = None
            n_pos = None
            for atom in res_i.atoms:
                if atom.name == "C":
                    c_pos = (atom.x, atom.y, atom.z)
                    break
            for atom in res_j.atoms:
                if atom.name == "N":
                    n_pos = (atom.x, atom.y, atom.z)
                    break

            if c_pos is None or n_pos is None:
                continue

            res_i_label = f"{sanitize_name(res_i.name)}_{seq_i}"
            res_j_label = f"{sanitize_name(res_j.name)}_{seq_j}"
            bond_label = f"PeptideBond_{res_i_label}__{res_j_label}"
            bond_path = f"{chain_path}/{bond_label}"
            bond_prim = create_bond_geometry(stage, bond_path, c_pos, n_pos)

            bond_vset = bond_prim.GetVariantSets().AddVariantSet("representation")
            for mode in REPRESENTATIONS:
                bond_vset.AddVariant(mode)
            for mode in REPRESENTATIONS:
                bond_vset.SetVariantSelection(mode)
                with bond_vset.GetVariantEditContext():
                    vis = "inherited" if mode == "ballstick" else "invisible"
                    UsdGeom.Imageable(bond_prim).CreateVisibilityAttr(vis)
            bond_vset.ClearVariantSelection()
            peptide_bond_prims.append(bond_prim)

        if peptide_bond_prims:
            print(f"  Chain {chain_id}: {len(peptide_bond_prims)} peptide bonds")

        # Chain variant cascade -> residues + peptide bonds
        chain_res_prims = [
            stage.GetPrimAtPath(f"{chain_path}/{sanitize_name(r.name)}_{r.seq}")
            for r in chain.residues.values()
        ]
        for mode in REPRESENTATIONS:
            chain_vset.SetVariantSelection(mode)
            with chain_vset.GetVariantEditContext():
                for rp in chain_res_prims:
                    rp.GetVariantSets().GetVariantSet(
                        "representation").SetVariantSelection(mode)
                for bp in peptide_bond_prims:
                    bp.GetVariantSets().GetVariantSet(
                        "representation").SetVariantSelection(mode)
        chain_vset.ClearVariantSelection()

    # =========================================================================
    # COMPLEX VARIANT CASCADE -> CHAINS
    # =========================================================================
    for mode in REPRESENTATIONS:
        complex_vset.SetVariantSelection(mode)
        with complex_vset.GetVariantEditContext():
            for cp in chain_prims:
                cp.GetVariantSets().GetVariantSet(
                    "representation").SetVariantSelection(mode)
    complex_vset.ClearVariantSelection()

    # =========================================================================
    # SAVE
    # =========================================================================
    stage.Save()

    bond_count = 0
    for prim in stage.Traverse():
        if prim.GetName().startswith("Bond_") or prim.GetName().startswith("PeptideBond_"):
            bond_count += 1

    print(f"\nCreated: {output_path}")
    print(f"  Chains: {len(structure.chains)}")
    print(f"  Residues: {structure.residue_count}")
    print(f"  Atoms: {structure.atom_count}")
    print(f"  Bonds: {bond_count} (intra-residue + peptide)")
    print(f"  Element library ref prim: {ELEMENT_LIB_PRIM}")
    print(f"  Class prefix: {ELEMENT_CLASS_PREFIX}")
    print(f"  Representations: {REPRESENTATIONS}")

    return output_path


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "assets", "level4_assemblies")
    os.makedirs(output_dir, exist_ok=True)

    element_library_path = os.path.join(
        root_dir, "assets", "level1_elements", "element_library.usda"
    )
    if not os.path.exists(element_library_path):
        print(f"ERROR: Element library not found: {element_library_path}")
        print("Run templates/07_create_element_library.py first")
        sys.exit(1)

    pdb_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDB
    if not os.path.exists(pdb_path):
        print(f"ERROR: PDB file not found: {pdb_path}")
        sys.exit(1)

    output_path = os.path.join(output_dir, "abl_kinase_complex_refstyle.usda")
    create_assembly_refstyle(output_path, pdb_path, element_library_path)

    # -------------------------------------------------------------------------
    # Consistency check
    # -------------------------------------------------------------------------
    from pxr import Usd as _Usd
    s = _Usd.Stage.Open(output_path)
    elem_lib = s.GetPrimAtPath("/ElementLib")
    assert elem_lib.IsValid(), "/ElementLib prim not found after composition"
    chain_a = s.GetPrimAtPath("/ABLComplex/Chain_A")
    assert chain_a.IsValid(), "/ABLComplex/Chain_A not found"
    errors = s.GetCompositionErrors()
    assert not errors, f"Composition errors: {errors}"
    print("PASS — /ElementLib valid, /ABLComplex/Chain_A valid, no composition errors")
