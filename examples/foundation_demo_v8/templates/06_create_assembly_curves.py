#!/usr/bin/env python3
"""
Create ABL kinase + ATP assembly using BasisCurves for bonds.

Instead of 2,428 Xform/Cylinder prim pairs, all bonds are encoded as a single
UsdGeomBasisCurves prim at /ABLComplex/Bonds with linear segments. This reduces
draw calls from 2,428 to 1, and file size significantly.

WHY linear curves: each covalent bond is a straight line; no basis needed.
WHY one prim: Hydra Storm draws all segments in a single draw call.

Patterns applied:
- Same as 04_create_assembly.py (LIVERPS, class prims, VariantSets)
- Bond geometry accumulated into BasisCurves instead of per-prim Cylinders.
"""

import os
import sys

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from usdbio_env import get_data_dir
from pxr import Usd, UsdGeom, Sdf, Gf, Vt
from converters.pdb_parser import parse_pdb
from data import RESIDUES


REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]
BOND_RADIUS = 0.1  # Å

# Default PDB path
DEFAULT_PDB = os.path.join(get_data_dir(), "files", "atp-complex-solv35.pdb")

# Bond connectivity for residues not in RESIDUES (heavy atoms only)
EXTRA_BONDS = {
    "ACE": [("CH3", "C"), ("C", "O")],
    "NME": [("N", "CH3")],
    "HID": RESIDUES["HIS"]["bonds"],
    "HIE": RESIDUES["HIS"]["bonds"],
    "HIP": RESIDUES["HIS"]["bonds"],
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


def sanitize_name(name: str) -> str:
    """Make a string safe for use as a USD prim name."""
    result = name.replace("+", "plus").replace("-", "minus")
    result = result.replace("*", "s").replace("'", "p")
    if result and result[0].isdigit():
        result = "_" + result
    return result


def get_bond_pairs(residue_name: str) -> list:
    """Get bond pairs for a residue, checking RESIDUES then EXTRA_BONDS."""
    if residue_name in RESIDUES:
        return RESIDUES[residue_name]["bonds"]
    if residue_name in EXTRA_BONDS:
        return EXTRA_BONDS[residue_name]
    return []


def accumulate_bond_curves(structure) -> tuple:
    """Accumulate all bond endpoint positions and curve vertex counts.

    Returns:
        (points, curveVertexCounts) where:
          - points is a flat list of Gf.Vec3f, 2 per bond (4,856 total for 2,428 bonds)
          - curveVertexCounts is a list of ints, each == 2 (one per bond)
    """
    points = []
    curve_vertex_counts = []

    for chain_id, chain in structure.chains.items():
        res_seq_list = list(chain.residues.keys())

        for res_seq, residue in chain.residues.items():
            # Build atom name -> position lookup for this residue
            atom_positions = {}
            for atom in residue.atoms:
                atom_positions[atom.name] = Gf.Vec3f(atom.x, atom.y, atom.z)

            # Intra-residue bonds
            for atom1_name, atom2_name in get_bond_pairs(residue.name):
                if atom1_name not in atom_positions or atom2_name not in atom_positions:
                    continue
                points.append(atom_positions[atom1_name])
                points.append(atom_positions[atom2_name])
                curve_vertex_counts.append(2)

        # Inter-residue peptide bonds (C_i -> N_{i+1})
        for idx in range(len(res_seq_list) - 1):
            seq_i = res_seq_list[idx]
            seq_j = res_seq_list[idx + 1]
            res_i = chain.residues[seq_i]
            res_j = chain.residues[seq_j]

            c_pos = None
            n_pos = None
            for atom in res_i.atoms:
                if atom.name == "C":
                    c_pos = Gf.Vec3f(atom.x, atom.y, atom.z)
                    break
            for atom in res_j.atoms:
                if atom.name == "N":
                    n_pos = Gf.Vec3f(atom.x, atom.y, atom.z)
                    break

            if c_pos is None or n_pos is None:
                continue
            points.append(c_pos)
            points.append(n_pos)
            curve_vertex_counts.append(2)

    return points, curve_vertex_counts


def write_bond_curves(stage, prim_path: str, points: list, counts: list):
    """Write a single UsdGeomBasisCurves prim encoding all bonds as linear segments.

    Args:
        stage: USD stage.
        prim_path: Sdf path string for the BasisCurves prim (e.g. '/ABLComplex/Bonds').
        points: Flat list of Gf.Vec3f, 2 per bond.
        counts: List of ints, each == 2 (curveVertexCounts).

    Returns:
        The UsdGeomBasisCurves schema object.
    """
    bc = UsdGeom.BasisCurves.Define(stage, prim_path)

    # Linear type — straight line segments, no basis matrix needed
    bc.CreateTypeAttr("linear")
    # Non-periodic — segments have distinct endpoints (not closed loops)
    bc.CreateWrapAttr("nonperiodic")

    # Points: all bond endpoint positions (2 per bond)
    pts_array = Vt.Vec3fArray(points)
    bc.CreatePointsAttr(pts_array)

    # curveVertexCounts: one entry per bond, value = 2
    counts_array = Vt.IntArray(counts)
    bc.CreateCurveVertexCountsAttr(counts_array)

    # Widths: constant — one value for all segments
    widths_array = Vt.FloatArray([BOND_RADIUS * 2])
    bc.CreateWidthsAttr(widths_array)
    bc.SetWidthsInterpolation(UsdGeom.Tokens.constant)

    # Display color: uniform gray
    bc.CreateDisplayColorAttr(Vt.Vec3fArray([Gf.Vec3f(0.5, 0.5, 0.5)]))

    return bc


def create_assembly_curves(output_path: str, element_template_path: str, pdb_path: str):
    """Create USD assembly with BasisCurves bonds from PDB data.

    Atom hierarchy, element class inheritance, representation VariantSet, and
    bio: metadata are identical to 04_create_assembly.py. Only the bond
    representation changes: 2,428 Xform/Cylinder prims -> one BasisCurves prim.
    """
    print(f"Parsing PDB: {pdb_path}")
    structure = parse_pdb(pdb_path)
    print(f"  Chains: {structure.chain_ids}, Atoms: {structure.atom_count}")

    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # coordinates in Angstrom
    stage.SetMetadata("comment",
        "ABL kinase + ATP assembly — BasisCurves bond encoding "
        "(single prim vs 2428 Xform/Cylinder prims)")

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

    complex_prim.CreateAttribute("bio:systemName", Sdf.ValueTypeNames.String).Set(
        "ABL kinase + ATP complex")
    complex_prim.CreateAttribute("bio:source", Sdf.ValueTypeNames.String).Set(
        "ShinobuLab MD simulation")
    complex_prim.CreateAttribute("bio:atomCount", Sdf.ValueTypeNames.Int).Set(
        structure.atom_count)
    complex_prim.CreateAttribute("bio:chainCount", Sdf.ValueTypeNames.Int).Set(
        len(structure.chains))

    complex_vset = complex_prim.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        complex_vset.AddVariant(mode)

    # =========================================================================
    # BUILD HIERARCHY: Complex -> Chain -> Residue -> Atom
    # =========================================================================
    chain_prims = []

    for chain_id, chain in structure.chains.items():
        chain_label = f"Chain_{chain_id}"
        chain_path = f"{complex_path}/{chain_label}"
        chain_xform = UsdGeom.Xform.Define(stage, chain_path)
        chain_prim = chain_xform.GetPrim()

        chain_atom_count = sum(len(r.atoms) for r in chain.residues.values())
        chain_prim.CreateAttribute("bio:chainID", Sdf.ValueTypeNames.Token).Set(chain_id)
        chain_prim.CreateAttribute("bio:chainType", Sdf.ValueTypeNames.Token).Set(
            chain.chain_type)
        chain_prim.CreateAttribute("bio:residueCount", Sdf.ValueTypeNames.Int).Set(
            len(chain.residues))
        chain_prim.CreateAttribute("bio:atomCount", Sdf.ValueTypeNames.Int).Set(
            chain_atom_count)

        chain_vset = chain_prim.GetVariantSets().AddVariantSet("representation")
        for mode in REPRESENTATIONS:
            chain_vset.AddVariant(mode)
        chain_vset.ClearVariantSelection()
        chain_prims.append(chain_prim)

        residue_prims = []
        for res_seq, residue in chain.residues.items():
            res_label = f"{sanitize_name(residue.name)}_{res_seq}"
            res_path = f"{chain_path}/{res_label}"
            res_xform = UsdGeom.Xform.Define(stage, res_path)
            res_prim = res_xform.GetPrim()

            res_prim.CreateAttribute("bio:residueName", Sdf.ValueTypeNames.Token).Set(
                residue.name)
            res_prim.CreateAttribute("bio:residueSeq", Sdf.ValueTypeNames.Int).Set(res_seq)
            res_prim.CreateAttribute("bio:atomCount", Sdf.ValueTypeNames.Int).Set(
                len(residue.atoms))

            res_vset = res_prim.GetVariantSets().AddVariantSet("representation")
            for mode in REPRESENTATIONS:
                res_vset.AddVariant(mode)
            res_vset.ClearVariantSelection()

            res_atom_prims = []
            for atom in residue.atoms:
                atom_label = sanitize_name(atom.name)
                atom_path = f"{res_path}/{atom_label}"
                atom_xform = UsdGeom.Xform.Define(stage, atom_path)
                atom_prim = atom_xform.GetPrim()

                atom_prim.GetInherits().AddInherit(f"/_class_/{atom.element}")
                atom_xform.AddTranslateOp().Set(Gf.Vec3d(atom.x, atom.y, atom.z))

                atom_prim.CreateAttribute("bio:atomName", Sdf.ValueTypeNames.Token).Set(
                    atom.name)
                atom_prim.CreateAttribute("bio:element", Sdf.ValueTypeNames.Token).Set(
                    atom.element)
                atom_prim.CreateAttribute("bio:serial", Sdf.ValueTypeNames.Int).Set(
                    atom.serial)

                atom_vset = atom_prim.GetVariantSets().AddVariantSet("representation")
                for mode in REPRESENTATIONS:
                    atom_vset.AddVariant(mode)
                atom_vset.ClearVariantSelection()
                res_atom_prims.append(atom_prim)

            # Residue variant cascade -> atoms
            for mode in REPRESENTATIONS:
                res_vset.SetVariantSelection(mode)
                with res_vset.GetVariantEditContext():
                    for ap in res_atom_prims:
                        ap.GetVariantSets().GetVariantSet(
                            "representation").SetVariantSelection(mode)
            res_vset.ClearVariantSelection()
            residue_prims.append(res_prim)

        # Chain variant cascade -> residues
        chain_res_prims = [
            stage.GetPrimAtPath(
                f"{chain_path}/{sanitize_name(r.name)}_{r.seq}"
            )
            for r in chain.residues.values()
        ]
        for mode in REPRESENTATIONS:
            chain_vset.SetVariantSelection(mode)
            with chain_vset.GetVariantEditContext():
                for rp in chain_res_prims:
                    rp.GetVariantSets().GetVariantSet(
                        "representation").SetVariantSelection(mode)
        chain_vset.ClearVariantSelection()

    # =========================================================================
    # BASISCURVES BONDS: all 2,428 bonds as a single prim
    # =========================================================================
    print("Accumulating bond endpoint positions...")
    points, curve_vertex_counts = accumulate_bond_curves(structure)
    bond_count = len(curve_vertex_counts)
    print(f"  {bond_count} bonds, {len(points)} points")

    bonds_prim_path = f"{complex_path}/Bonds"
    bc = write_bond_curves(stage, bonds_prim_path, points, curve_vertex_counts)

    # Bonds VariantSet: visible only in ballstick mode
    bonds_prim = bc.GetPrim()
    bonds_vset = bonds_prim.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        bonds_vset.AddVariant(mode)
    for mode in REPRESENTATIONS:
        bonds_vset.SetVariantSelection(mode)
        with bonds_vset.GetVariantEditContext():
            vis = "inherited" if mode == "ballstick" else "invisible"
            UsdGeom.Imageable(bonds_prim).CreateVisibilityAttr(vis)
    bonds_vset.ClearVariantSelection()

    # =========================================================================
    # COMPLEX VARIANT CASCADE -> CHAINS + BONDS
    # =========================================================================
    for mode in REPRESENTATIONS:
        complex_vset.SetVariantSelection(mode)
        with complex_vset.GetVariantEditContext():
            for cp in chain_prims:
                cp.GetVariantSets().GetVariantSet(
                    "representation").SetVariantSelection(mode)
            bonds_vset.SetVariantSelection(mode)
    complex_vset.ClearVariantSelection()

    # =========================================================================
    # SAVE
    # =========================================================================
    stage.Save()

    print(f"\nCreated: {output_path}")
    print(f"  Chains: {len(structure.chains)}")
    print(f"  Residues: {structure.residue_count}")
    print(f"  Atoms: {structure.atom_count}")
    print(f"  Bonds (as BasisCurves segments): {bond_count}")
    print(f"  Representations: {REPRESENTATIONS}")

    return output_path


def verify_assembly_curves(usd_path: str):
    """Verify the BasisCurves assembly is correctly structured."""
    from pxr import Usd, UsdGeom, Sdf

    stage = Usd.Stage.Open(usd_path)
    print("\n--- BasisCurves Assembly Verification ---")

    complex_prim = stage.GetPrimAtPath("/ABLComplex")
    assert complex_prim.IsValid(), "ABLComplex prim not found"
    print("  PASS: /ABLComplex exists")

    # Verify BasisCurves prim
    bonds_prim = stage.GetPrimAtPath("/ABLComplex/Bonds")
    assert bonds_prim.IsValid(), "/ABLComplex/Bonds not found"
    bc = UsdGeom.BasisCurves(bonds_prim)
    assert bc, "/ABLComplex/Bonds is not BasisCurves"
    print("  PASS: /ABLComplex/Bonds is UsdGeomBasisCurves")

    pts = bc.GetPointsAttr().Get()
    counts = bc.GetCurveVertexCountsAttr().Get()
    print(f"  Points: {len(pts)}, Counts: {len(counts)}")
    assert len(pts) == len(counts) * 2, (
        f"Expected {len(counts)*2} points for {len(counts)} bonds, got {len(pts)}"
    )
    print(f"  PASS: {len(counts)} bonds, {len(pts)} points")

    # Verify NO Cylinder prims under Bonds
    has_cylinder = any(
        p.GetTypeName() == "Cylinder"
        for p in stage.Traverse()
        if str(p.GetPath()).startswith("/ABLComplex/Bonds")
    )
    assert not has_cylinder, "Found unexpected Cylinder prims under /ABLComplex/Bonds"
    print("  PASS: No Cylinder prims under /ABLComplex/Bonds")

    # Verify chains still exist
    for chain_id in ["A", "B", "L"]:
        chain = stage.GetPrimAtPath(f"/ABLComplex/Chain_{chain_id}")
        assert chain.IsValid(), f"Chain_{chain_id} not found"
    print("  PASS: All chains (A, B, L) present")

    # Verify type and wrap
    type_val = bonds_prim.GetAttribute("type").Get()
    wrap_val = bonds_prim.GetAttribute("wrap").Get()
    assert type_val == "linear", f"Expected type='linear', got {type_val}"
    assert wrap_val == "nonperiodic", f"Expected wrap='nonperiodic', got {wrap_val}"
    print(f"  PASS: type={type_val}, wrap={wrap_val}")

    print("\n  ALL VERIFICATIONS PASSED")
    return len(counts)


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

    output_path = os.path.join(output_dir, "abl_kinase_complex_curves.usda")
    create_assembly_curves(output_path, element_template_path, pdb_path)
    bond_count = verify_assembly_curves(output_path)
    print(f"\nFinal bond count: {bond_count}")
