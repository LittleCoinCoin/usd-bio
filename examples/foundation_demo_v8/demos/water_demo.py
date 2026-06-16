#!/usr/bin/env python3
"""
Water molecule demo - single H2O molecule for visualization testing.

Patterns applied:
- Inherit from water class template
- Local position for molecule placement
- Variant cascade for representation modes
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf

REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]


def create_water_demo(output_path: str, water_template_path: str):
    """Create a simple water molecule demo."""

    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    # Reference the water template (brings in /_class_/Water and element classes)
    stage.GetRootLayer().subLayerPaths.append(water_template_path)

    # Create world root
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # Root variant set for global control
    root_prim = world.GetPrim()
    root_vset = root_prim.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        root_vset.AddVariant(mode)

    # Create water molecule instance
    water_xform = UsdGeom.Xform.Define(stage, "/World/Water")
    water_prim = water_xform.GetPrim()

    # Inherit from water class
    water_prim.GetInherits().AddInherit("/_class_/Water")

    # Position at origin (molecule's atoms have their own relative positions)
    water_xform.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0))

    # Molecule variant set for cascade
    mol_vset = water_prim.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        mol_vset.AddVariant(mode)

    # Variant cascade: Root -> Molecule
    for mode in REPRESENTATIONS:
        root_vset.SetVariantSelection(mode)
        with root_vset.GetVariantEditContext():
            mol_vset.SetVariantSelection(mode)

    # Set default
    root_vset.SetVariantSelection("balls")

    # Scene extent
    UsdGeom.Boundable(root_prim).CreateExtentAttr([(-2, -2, -2), (2, 2, 2)])

    stage.Save()

    print(f"Created: {output_path}")
    print(f"Water molecule at origin")
    print(f"Default representation: balls")
    print(f"\nTo view: usdview {output_path}")
    print(f"Switch representations via /World variant 'representation'")


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    water_template_path = os.path.join(
        root_dir, "assets", "level2_molecules", "water_template.usda"
    )

    if not os.path.exists(water_template_path):
        print(f"ERROR: Water template not found: {water_template_path}")
        print("Run templates/02_create_water_template.py first")
        sys.exit(1)

    output_path = os.path.join(output_dir, "water_demo.usda")
    create_water_demo(output_path, water_template_path)
