#!/usr/bin/env python3
"""
Create ABL kinase + ATP assembly from real PDB data.

Patterns applied:
- 02_inherits_arc.md: Atoms inherit from element class templates (/_class_/C, etc.)
- 01_local_opinions.md: Atom positions are LOCAL (strongest in LIVRPS)
- 03_variantsets_arc.md: Variant cascade from complex -> chain -> residue -> atom
- 08_schemas_attributes.md: Custom bio: namespace for scientific metadata

Hierarchy:
  /ABLComplex
    /Chain_A
      /ACE_1
        /HH31  (inherits /_class_/H)
        /CH3   (inherits /_class_/C)
        ...
      /SER_2
        /N     (inherits /_class_/N)
        ...
    /Chain_B
      ...
    /Chain_L
      /atp_293
        ...
"""

import os
import sys
import math

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

# Structured provenance helper — lives in examples/composition_advanced/provenance_metadata/
_provenance_dir = os.path.join(
    os.path.dirname(root_dir), "composition_advanced", "provenance_metadata"
)
sys.path.insert(0, _provenance_dir)
from provenance_schema import apply_provenance_metadata  # noqa: E402
from provenance_source import load_shinobulab_provenance  # noqa: E402

from usdbio_env import get_data_dir
from pxr import Usd, UsdGeom, Sdf, Gf
from converters.pdb_parser import parse_pdb
from data import RESIDUES


REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]

# Default PDB path — root from environment; fails loudly if USDBIO_DATA_DIR is unset
DEFAULT_PDB = os.path.join(get_data_dir(), "files", "atp-complex-solv35.pdb")


def sanitize_name(name: str) -> str:
    """Make a string safe for use as a USD prim name.

    USD prim names cannot contain +, -, *, ', or start with a digit.
    """
    result = name.replace("+", "plus").replace("-", "minus")
    result = result.replace("*", "s").replace("'", "p")
    # Prim names cannot start with a digit
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
    """Create a cylinder bond between two atom positions.

    Same pattern as 03_create_residue_templates.py.
    """
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


def create_assembly(output_path: str, element_template_path: str, pdb_path: str):
    """Create USD assembly from PDB data with element class inheritance."""

    # Parse PDB
    print(f"Parsing PDB: {pdb_path}")
    structure = parse_pdb(pdb_path)
    print(f"  Chains: {structure.chain_ids}, Atoms: {structure.atom_count}")

    # Clean start
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # coordinates in Ångström (1 Å = 1e-10 m)
    stage.SetMetadata("comment",
        "ABL kinase + ATP assembly from ShinobuLab MD simulation PDB")

    # SubLayer element templates for /_class_/ inheritance
    stage.GetRootLayer().subLayerPaths.append(
        os.path.relpath(element_template_path, os.path.dirname(output_path))
    )

    # =========================================================================
    # COMPLEX ROOT
    # =========================================================================
    complex_path = "/ABLComplex"
    complex_xform = UsdGeom.Xform.Define(stage, complex_path)
    complex_prim = complex_xform.GetPrim()
    stage.SetDefaultPrim(complex_prim)

    # Bio metadata on complex root
    complex_prim.CreateAttribute("bio:systemName", Sdf.ValueTypeNames.String).Set(
        "ABL kinase + ATP complex")
    # Structured provenance replaces the legacy flat bio:source string.
    # Six lineage fields, DATA-DRIVEN: parsed at generation time from the
    # real ShinobuLab GENESIS run artifacts (equilibration/5-eq2 .inp/.log)
    # rather than hard-coded sentinels. See provenance_source.py for the
    # extraction logic and per-field source paths.
    # [source: examples/composition_advanced/provenance_metadata/provenance_schema.py]
    # [source: examples/composition_advanced/provenance_metadata/provenance_source.py]
    _provenance = load_shinobulab_provenance(get_data_dir())
    if _provenance.unresolved:
        print(
            f"  WARNING: provenance fields unresolved from data, set to "
            f"'unknown': {_provenance.unresolved}"
        )
    apply_provenance_metadata(complex_prim, _provenance.record)
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
    # Track all prims for variant cascade
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

            # Track this residue's atom and bond prims for its cascade
            res_atom_prims = []
            res_bond_prims = []

            # Build position lookup for bond geometry
            atom_positions = {}

            for atom in residue.atoms:
                atom_label = sanitize_name(atom.name)
                atom_path = f"{res_path}/{atom_label}"
                atom_xform = UsdGeom.Xform.Define(stage, atom_path)
                atom_prim = atom_xform.GetPrim()

                # Inherit from element class template
                atom_prim.GetInherits().AddInherit(f"/_class_/{atom.element}")

                # LOCAL position (strongest in LIVRPS — overrides inherited transforms)
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
                # Bond VariantSet: visible only in ballstick
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

            # Find C atom in residue i and N atom in residue j
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

    # Count bonds for summary
    bond_count = 0
    for prim in stage.Traverse():
        if prim.GetName().startswith("Bond_") or prim.GetName().startswith("PeptideBond_"):
            bond_count += 1

    print(f"\nCreated: {output_path}")
    print(f"  Chains: {len(structure.chains)}")
    print(f"  Residues: {structure.residue_count}")
    print(f"  Atoms: {structure.atom_count}")
    print(f"  Bonds: {bond_count} (intra-residue + peptide)")
    print(f"  Representations: {REPRESENTATIONS}")

    return output_path


def verify_assembly(usd_path: str):
    """Verify the assembly is correctly structured."""
    stage = Usd.Stage.Open(usd_path)

    print("\n--- Assembly Verification ---")

    # Check complex root
    complex_prim = stage.GetPrimAtPath("/ABLComplex")
    assert complex_prim.IsValid(), "ABLComplex prim not found"
    print("  PASS: /ABLComplex exists")

    # Check atom count via metadata
    atom_count = complex_prim.GetAttribute("bio:atomCount").Get()
    assert atom_count == 4676, f"Expected 4676 atoms, got {atom_count}"
    print(f"  PASS: bio:atomCount = {atom_count}")

    # Check chains exist
    chain_a = stage.GetPrimAtPath("/ABLComplex/Chain_A")
    chain_b = stage.GetPrimAtPath("/ABLComplex/Chain_B")
    chain_l = stage.GetPrimAtPath("/ABLComplex/Chain_L")
    assert chain_a.IsValid(), "Chain_A not found"
    assert chain_b.IsValid(), "Chain_B not found"
    assert chain_l.IsValid(), "Chain_L not found"
    print("  PASS: all chains (A, B, L) exist")

    # Check a sample atom inherits from element class
    # First atom in Chain A should be HH31 in ACE_1
    sample_atom = stage.GetPrimAtPath("/ABLComplex/Chain_A/ACE_1/HH31")
    assert sample_atom.IsValid(), "Sample atom ACE_1/HH31 not found"
    inherits = sample_atom.GetInherits().GetAllDirectInherits()
    assert Sdf.Path("/_class_/H") in inherits, \
        f"Expected /_class_/H inheritance, got {inherits}"
    print("  PASS: sample atom inherits from element class")

    # Check position is set
    xformable = UsdGeom.Xformable(sample_atom)
    xform_ops = xformable.GetOrderedXformOps()
    assert len(xform_ops) > 0, "No xform ops on atom"
    translate = xform_ops[0].Get()
    assert abs(translate[0]) > 0.1 or abs(translate[1]) > 0.1, \
        "Translate seems to be at origin"
    print(f"  PASS: sample atom has position ({translate[0]:.1f}, {translate[1]:.1f}, {translate[2]:.1f})")

    # Check variant set exists at complex level
    vsets = complex_prim.GetVariantSets()
    assert vsets.HasVariantSet("representation"), "Missing representation variant set"
    vset = vsets.GetVariantSet("representation")
    variants = vset.GetVariantNames()
    assert set(variants) == set(REPRESENTATIONS), \
        f"Expected {REPRESENTATIONS}, got {variants}"
    print(f"  PASS: representation VariantSet with {variants}")

    # Check ligand ATP atoms (exclude bond prims)
    atp_prim = stage.GetPrimAtPath("/ABLComplex/Chain_L/atp_293")
    assert atp_prim.IsValid(), "ATP residue prim not found"
    atp_atoms = [c for c in atp_prim.GetChildren()
                 if c.GetTypeName() == "Xform" and not c.GetName().startswith("Bond_")]
    atp_bonds = [c for c in atp_prim.GetChildren()
                 if c.GetName().startswith("Bond_")]
    assert len(atp_atoms) == 43, f"Expected 43 ATP atom prims, got {len(atp_atoms)}"
    assert len(atp_bonds) > 0, "Expected ATP bonds"
    print(f"  PASS: ATP has {len(atp_atoms)} atom prims, {len(atp_bonds)} bonds")

    # Check a phosphorus atom inherits correctly
    pg_atom = stage.GetPrimAtPath("/ABLComplex/Chain_L/atp_293/PG")
    assert pg_atom.IsValid(), "PG atom not found"
    pg_inherits = pg_atom.GetInherits().GetAllDirectInherits()
    assert Sdf.Path("/_class_/P") in pg_inherits, \
        f"PG should inherit from /_class_/P, got {pg_inherits}"
    print("  PASS: ATP phosphorus inherits from /_class_/P")

    # Check bonds exist
    bond_count = 0
    for prim in stage.Traverse():
        if prim.GetName().startswith("Bond_") or prim.GetName().startswith("PeptideBond_"):
            bond_count += 1
    assert bond_count > 0, "No bonds found"
    print(f"  PASS: {bond_count} bonds created")

    # Check a sample bond has correct variant behavior
    # Find first bond in SER_2 (N-CA is a standard bond)
    sample_bond = stage.GetPrimAtPath("/ABLComplex/Chain_A/SER_2/Bond_N_CA")
    if sample_bond.IsValid():
        bond_vset = sample_bond.GetVariantSets().GetVariantSet("representation")
        bond_vset.SetVariantSelection("ballstick")
        vis = UsdGeom.Imageable(sample_bond).ComputeVisibility()
        print(f"  PASS: sample bond visibility in ballstick = {vis}")
        bond_vset.SetVariantSelection("balls")
        vis = UsdGeom.Imageable(sample_bond).ComputeVisibility()
        assert vis == UsdGeom.Tokens.invisible, f"Bond should be invisible in balls, got {vis}"
        print(f"  PASS: sample bond invisible in balls mode")

    # Check a peptide bond exists
    peptide_bonds = [p for p in stage.GetPrimAtPath("/ABLComplex/Chain_A").GetChildren()
                     if p.GetName().startswith("PeptideBond_")]
    assert len(peptide_bonds) > 0, "No peptide bonds in Chain A"
    print(f"  PASS: {len(peptide_bonds)} peptide bonds in Chain A")

    print("\n  ALL VERIFICATIONS PASSED")


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "assets", "level4_assemblies")
    os.makedirs(output_dir, exist_ok=True)

    element_template_path = os.path.join(
        root_dir, "assets", "level1_elements", "element_templates.usda"
    )
    if not os.path.exists(element_template_path):
        print(f"ERROR: Element templates not found: {element_template_path}")
        print("Run templates/01_create_element_templates.py first")
        sys.exit(1)

    pdb_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDB
    if not os.path.exists(pdb_path):
        print(f"ERROR: PDB file not found: {pdb_path}")
        sys.exit(1)

    output_path = os.path.join(output_dir, "abl_kinase_complex.usda")
    create_assembly(output_path, element_template_path, pdb_path)
    verify_assembly(output_path)
