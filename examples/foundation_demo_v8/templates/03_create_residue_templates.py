#!/usr/bin/env python3
"""
Create amino acid residue class templates with variant cascade.

Patterns applied:
- 02_inherits_arc.md: Atoms inherit from element class templates
- 01_local_opinions.md: Atom positions are LOCAL (strongest in LIVRPS)
- 03_variantsets_arc.md: Variant cascade from residue to atoms
"""

import os
import sys
import math

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf
from data import (
    RESIDUES, get_residue_atoms, get_residue_bonds,
    get_residue_coordinates, get_residue_type, get_type_color
)

REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]
BOND_RADIUS = 0.1  # Å


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

    # Use Gf.Rotation to properly convert axis-angle to quaternion
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


def create_residue_class(stage, residue_code):
    """Create a single residue class template."""
    class_path = f"/_class_/{residue_code}"
    residue_class = stage.CreateClassPrim(class_path)
    residue_data = RESIDUES[residue_code]
    coords = get_residue_coordinates(residue_code)

    # Scientific metadata
    residue_class.CreateAttribute("bio:residueName", Sdf.ValueTypeNames.Token).Set(residue_code)
    residue_class.CreateAttribute("bio:oneLetterCode", Sdf.ValueTypeNames.Token).Set(residue_data["one_letter"])
    residue_class.CreateAttribute("bio:residueType", Sdf.ValueTypeNames.Token).Set(residue_data["type"])
    residue_class.CreateAttribute("bio:atomCount", Sdf.ValueTypeNames.Int).Set(len(residue_data["atoms"]))
    residue_class.CreateAttribute("bio:bondCount", Sdf.ValueTypeNames.Int).Set(len(residue_data["bonds"]))

    # Residue-level variant set
    res_vset = residue_class.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        res_vset.AddVariant(mode)

    # Create atoms
    atom_prims = []
    for atom_name, element in residue_data["atoms"]:
        if atom_name not in coords:
            continue
        atom_path = f"{class_path}/{atom_name}"
        atom_xform = UsdGeom.Xform.Define(stage, atom_path)
        atom_prim = atom_xform.GetPrim()

        atom_prim.GetInherits().AddInherit(f"/_class_/{element}")
        atom_xform.AddTranslateOp().Set(Gf.Vec3d(*coords[atom_name]))

        atom_vset = atom_prim.GetVariantSets().AddVariantSet("representation")
        for mode in REPRESENTATIONS:
            atom_vset.AddVariant(mode)
        atom_vset.ClearVariantSelection()
        atom_prims.append(atom_prim)

    # Create bonds
    bond_prims = []
    for atom1, atom2 in residue_data["bonds"]:
        if atom1 not in coords or atom2 not in coords:
            continue
        bond_name = f"Bond_{atom1}_{atom2}"
        bond_path = f"{class_path}/{bond_name}"
        bond_prim = create_bond_geometry(stage, bond_path, coords[atom1], coords[atom2])

        bond_vset = bond_prim.GetVariantSets().AddVariantSet("representation")
        for mode in REPRESENTATIONS:
            bond_vset.AddVariant(mode)

        for mode in REPRESENTATIONS:
            bond_vset.SetVariantSelection(mode)
            with bond_vset.GetVariantEditContext():
                vis = "inherited" if mode == "ballstick" else "invisible"
                UsdGeom.Imageable(bond_prim).CreateVisibilityAttr(vis)
        bond_vset.ClearVariantSelection()
        bond_prims.append(bond_prim)

    # Variant cascade: residue -> atoms + bonds
    for mode in REPRESENTATIONS:
        res_vset.SetVariantSelection(mode)
        with res_vset.GetVariantEditContext():
            for atom_prim in atom_prims:
                atom_prim.GetVariantSets().GetVariantSet("representation").SetVariantSelection(mode)
            for bond_prim in bond_prims:
                bond_prim.GetVariantSets().GetVariantSet("representation").SetVariantSelection(mode)

    res_vset.ClearVariantSelection()
    return residue_class


def create_residue_templates(output_path: str, element_template_path: str):
    """Create USD file with all residue class templates."""
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # coordinates in Ångström (1 Å = 1e-10 m)
    stage.SetMetadata("comment", "Amino acid residue templates")
    stage.GetRootLayer().subLayerPaths.append(element_template_path)

    for residue_code in RESIDUES.keys():
        create_residue_class(stage, residue_code)
        print(f"  Created: {residue_code}")

    stage.Save()
    print(f"\nCreated: {output_path}")
    print(f"Residues: {len(RESIDUES)}")


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "assets", "level3_residues")
    os.makedirs(output_dir, exist_ok=True)

    element_template_path = os.path.join(
        root_dir, "assets", "level1_elements", "element_templates.usda"
    )

    if not os.path.exists(element_template_path):
        print(f"ERROR: Element templates not found: {element_template_path}")
        sys.exit(1)

    output_path = os.path.join(output_dir, "residue_templates.usda")
    create_residue_templates(output_path, element_template_path)
