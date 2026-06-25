#!/usr/bin/env python3
"""
Create water molecule (H2O) template with scientific data.

Water geometry (TIP3P model):
- O-H bond length: 0.9572 Å
- H-O-H angle: 104.52°

Patterns applied:
- 02_inherits_arc.md: Atoms inherit from element class templates
- 01_local_opinions.md: Atom positions are LOCAL (strongest in LIVRPS)
- 03_variantsets_arc.md: Variant cascade from molecule to atoms
"""

import os
import sys
import math

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf

# TIP3P water model parameters (scientific data)
WATER_DATA = {
    "name": "Water",
    "formula": "H2O",
    "molecular_weight": 18.015,  # Da
    "bond_length_OH": 0.9572,    # Å
    "bond_angle_HOH": 104.52,    # degrees
    "dipole_moment": 1.85,       # Debye
    "model": "TIP3P",
}

REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]

BOND_RADIUS = 0.1  # Å


def compute_water_positions():
    """Compute H2O atom positions with O at origin."""
    bond_length = WATER_DATA["bond_length_OH"]
    angle_deg = WATER_DATA["bond_angle_HOH"]
    angle_rad = math.radians(angle_deg)

    # Oxygen at origin
    O_pos = (0.0, 0.0, 0.0)

    # Hydrogens symmetric about Y axis in XY plane
    half_angle = angle_rad / 2
    H1_pos = (
        bond_length * math.sin(half_angle),
        bond_length * math.cos(half_angle),
        0.0
    )
    H2_pos = (
        -bond_length * math.sin(half_angle),
        bond_length * math.cos(half_angle),
        0.0
    )

    return {"O": O_pos, "H1": H1_pos, "H2": H2_pos}


def create_water_template(output_path: str, element_template_path: str):
    """Create water molecule class template."""

    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # coordinates in Ångström (1 Å = 1e-10 m)

    # Reference element templates (brings in /_class_/H, /_class_/O, etc.)
    stage.GetRootLayer().subLayerPaths.append(element_template_path)

    # Compute atom positions
    positions = compute_water_positions()

    # =========================================================================
    # CREATE WATER CLASS TEMPLATE
    # =========================================================================
    class_path = "/_class_/Water"
    water_class = stage.CreateClassPrim(class_path)

    # =========================================================================
    # SCIENTIFIC METADATA (bio: namespace)
    # =========================================================================
    water_class.CreateAttribute("bio:name", Sdf.ValueTypeNames.String).Set(WATER_DATA["name"])
    water_class.CreateAttribute("bio:formula", Sdf.ValueTypeNames.String).Set(WATER_DATA["formula"])
    water_class.CreateAttribute("bio:molecularWeight", Sdf.ValueTypeNames.Float).Set(WATER_DATA["molecular_weight"])
    water_class.CreateAttribute("bio:bondLengthOH", Sdf.ValueTypeNames.Float).Set(WATER_DATA["bond_length_OH"])
    water_class.CreateAttribute("bio:bondAngleHOH", Sdf.ValueTypeNames.Float).Set(WATER_DATA["bond_angle_HOH"])
    water_class.CreateAttribute("bio:dipoleMoment", Sdf.ValueTypeNames.Float).Set(WATER_DATA["dipole_moment"])
    water_class.CreateAttribute("bio:model", Sdf.ValueTypeNames.Token).Set(WATER_DATA["model"])

    # =========================================================================
    # MOLECULE VARIANT SET
    # =========================================================================
    mol_vset = water_class.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        mol_vset.AddVariant(mode)

    # =========================================================================
    # CREATE ATOMS (as Xform children with inherited element properties)
    # =========================================================================
    atom_definitions = [
        ("O", "O", positions["O"]),
        ("H1", "H", positions["H1"]),
        ("H2", "H", positions["H2"]),
    ]

    atom_prims = []
    for atom_name, element, pos in atom_definitions:
        atom_path = f"{class_path}/{atom_name}"

        # Define as Xform for transforms to work
        atom_xform = UsdGeom.Xform.Define(stage, atom_path)
        atom_prim = atom_xform.GetPrim()

        # Inherit from element class (gets geometry, color, scientific data)
        atom_prim.GetInherits().AddInherit(f"/_class_/{element}")

        # LOCAL position (strongest in LIVRPS)
        atom_xform.AddTranslateOp().Set(Gf.Vec3d(*pos))

        # Atom-level variant set for cascade
        atom_vset = atom_prim.GetVariantSets().AddVariantSet("representation")
        for mode in REPRESENTATIONS:
            atom_vset.AddVariant(mode)
        atom_vset.ClearVariantSelection()

        atom_prims.append(atom_prim)

    # =========================================================================
    # VARIANT CASCADE: Molecule -> Atoms
    # Pattern: SetVariantSelection BEFORE GetVariantEditContext
    # =========================================================================
    for mode in REPRESENTATIONS:
        mol_vset.SetVariantSelection(mode)
        with mol_vset.GetVariantEditContext():
            for atom_prim in atom_prims:
                atom_prim.GetVariantSets().GetVariantSet("representation").SetVariantSelection(mode)

    # =========================================================================
    # CREATE BONDS (visible only in ballstick mode)
    # =========================================================================
    bonds = [
        ("Bond_O_H1", positions["O"], positions["H1"]),
        ("Bond_O_H2", positions["O"], positions["H2"]),
    ]

    for bond_name, pos1, pos2 in bonds:
        bond_path = f"{class_path}/{bond_name}"

        # Calculate bond geometry
        p1 = Gf.Vec3d(*pos1)
        p2 = Gf.Vec3d(*pos2)
        midpoint = (p1 + p2) / 2
        bond_vec = p2 - p1
        bond_length = bond_vec.GetLength()

        # Create bond Xform
        bond_xform = UsdGeom.Xform.Define(stage, bond_path)
        bond_prim = bond_xform.GetPrim()

        # Position at midpoint
        bond_xform.AddTranslateOp().Set(midpoint)

        # Rotate to align cylinder (Y-axis) with bond vector
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

        # Create cylinder inside bond Xform
        cyl = UsdGeom.Cylinder.Define(stage, f"{bond_path}/Cylinder")
        cyl.CreateHeightAttr(bond_length)
        cyl.CreateRadiusAttr(BOND_RADIUS)
        cyl.CreateAxisAttr("Y")
        cyl.CreateDisplayColorAttr([Gf.Vec3f(0.5, 0.5, 0.5)])  # Gray bonds

        # Bond visibility variant set
        bond_vset = bond_prim.GetVariantSets().AddVariantSet("representation")
        for mode in REPRESENTATIONS:
            bond_vset.AddVariant(mode)

        # Bonds visible only in ballstick mode
        for mode in REPRESENTATIONS:
            bond_vset.SetVariantSelection(mode)
            with bond_vset.GetVariantEditContext():
                if mode == "ballstick":
                    UsdGeom.Imageable(bond_prim).CreateVisibilityAttr("inherited")
                else:
                    UsdGeom.Imageable(bond_prim).CreateVisibilityAttr("invisible")

        bond_vset.ClearVariantSelection()

        # Add to molecule variant cascade
        for mode in REPRESENTATIONS:
            mol_vset.SetVariantSelection(mode)
            with mol_vset.GetVariantEditContext():
                bond_prim.GetVariantSets().GetVariantSet("representation").SetVariantSelection(mode)

    # Clear selection (let instances choose)
    mol_vset.ClearVariantSelection()

    stage.Save()

    print(f"Created: {output_path}")
    print(f"Water molecule: {WATER_DATA['formula']}")
    print(f"Bond length O-H: {WATER_DATA['bond_length_OH']} Å")
    print(f"Bond angle H-O-H: {WATER_DATA['bond_angle_HOH']}°")
    print(f"Atom positions:")
    for name, pos in positions.items():
        print(f"  {name}: ({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f})")


def verify_template(usd_path: str):
    """Verify the water template."""
    stage = Usd.Stage.Open(usd_path)

    print("\n--- Verification ---")

    # Check class exists
    water = stage.GetPrimAtPath("/_class_/Water")
    assert water.IsValid(), "Water class not found"

    # Check scientific metadata
    mol_weight = water.GetAttribute("bio:molecularWeight").Get()
    assert abs(mol_weight - 18.015) < 0.001, f"Wrong molecular weight: {mol_weight}"
    print(f"✓ bio:molecularWeight = {mol_weight}")

    # Check atoms exist
    for atom_name in ["O", "H1", "H2"]:
        atom = stage.GetPrimAtPath(f"/_class_/Water/{atom_name}")
        assert atom.IsValid(), f"Atom {atom_name} not found"

        # Check it has a transform
        xform = UsdGeom.Xformable(atom)
        ops = xform.GetOrderedXformOps()
        assert len(ops) > 0, f"{atom_name} has no transform"

    print("✓ All atoms (O, H1, H2) have transforms")

    # Check variant cascade
    vset = water.GetVariantSets().GetVariantSet("representation")
    vset.SetVariantSelection("vdw")

    # Check O atom has correct variant selection
    o_atom = stage.GetPrimAtPath("/_class_/Water/O")
    o_vset = o_atom.GetVariantSets().GetVariantSet("representation")
    selection = o_vset.GetVariantSelection()
    assert selection == "vdw", f"Variant cascade failed: O has '{selection}'"
    print("✓ Variant cascade working (molecule -> atoms)")

    print("\n✓ All verifications passed")


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "assets", "level2_molecules")
    os.makedirs(output_dir, exist_ok=True)

    element_template_path = os.path.join(
        root_dir, "assets", "level1_elements", "element_templates.usda"
    )

    if not os.path.exists(element_template_path):
        print(f"ERROR: Element templates not found: {element_template_path}")
        print("Run templates/01_create_element_templates.py first")
        sys.exit(1)

    output_path = os.path.join(output_dir, "water_template.usda")
    create_water_template(output_path, element_template_path)
    verify_template(output_path)
