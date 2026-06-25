#!/usr/bin/env python3
"""
Element grid demo - all elements arranged on X-Y plane.

Pattern applied (from docs):
- 02_inherits_arc.md: Instances inherit from class templates
- 01_local_opinions.md: LOCAL position via AddTranslateOp() (strongest in LIVRPS)
- 03_variantsets_arc.md: Variant cascade from root to instances
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf
from data import ELEMENTS

REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]


def create_element_grid_demo(output_path: str, template_path: str):
    """Create a grid of all elements with variant cascade."""

    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # coordinates in Ångström (1 Å = 1e-10 m)

    # Reference the element templates
    # This brings in /_class_/* prims
    stage.GetRootLayer().subLayerPaths.append(template_path)

    # Create world root
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # Root variant set for global control
    root_prim = world.GetPrim()
    root_vset = root_prim.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        root_vset.AddVariant(mode)

    # Grid layout
    elements = list(ELEMENTS.keys())
    cols = 5
    spacing = 8.0  # Angstroms (enough for largest VDW sphere ~2.75Å radius)

    all_instances = []

    for idx, symbol in enumerate(elements):
        row = idx // cols
        col = idx % cols

        # X-Y plane grid (Z=0)
        x = col * spacing
        y = row * spacing
        z = 0.0

        # Create instance as Xform (required for transforms to apply)
        inst_path = f"/World/{symbol}"
        inst_xform = UsdGeom.Xform.Define(stage, inst_path)
        inst_prim = inst_xform.GetPrim()

        # =====================================================================
        # INHERIT from class template (02_inherits_arc.md)
        # =====================================================================
        inst_prim.GetInherits().AddInherit(f"/_class_/{symbol}")

        # =====================================================================
        # LOCAL position (01_local_opinions.md) - STRONGEST in LIVRPS
        # =====================================================================
        inst_xform.AddTranslateOp().Set(Gf.Vec3d(x, y, z))

        # Instance variant set for cascade
        inst_vset = inst_prim.GetVariantSets().AddVariantSet("representation")
        for mode in REPRESENTATIONS:
            inst_vset.AddVariant(mode)
        inst_vset.ClearVariantSelection()

        all_instances.append(inst_prim)

    # =========================================================================
    # VARIANT CASCADE: Root -> Instances (03_variantsets_arc.md)
    # Pattern: SetVariantSelection BEFORE GetVariantEditContext
    # =========================================================================
    for mode in REPRESENTATIONS:
        root_vset.SetVariantSelection(mode)
        with root_vset.GetVariantEditContext():
            for inst_prim in all_instances:
                inst_prim.GetVariantSets().GetVariantSet("representation").SetVariantSelection(mode)

    # Set default representation
    root_vset.SetVariantSelection("balls")

    # Scene bounds for camera framing
    num_rows = (len(elements) + cols - 1) // cols
    extent_x = cols * spacing
    extent_y = num_rows * spacing
    UsdGeom.Boundable(root_prim).CreateExtentAttr([
        (0, 0, -2),
        (extent_x, extent_y, 2)
    ])

    stage.Save()

    print(f"Created: {output_path}")
    print(f"Grid: {cols} columns x {num_rows} rows = {len(elements)} elements")
    print(f"Spacing: {spacing} Å")
    print(f"Default representation: balls")
    print(f"\nTo switch representations in usdview:")
    print(f"  Select /World, change variant 'representation' to: {REPRESENTATIONS}")


def verify_demo(usd_path: str):
    """Verify the demo is correctly structured."""
    stage = Usd.Stage.Open(usd_path)

    print("\n--- Verification ---")

    # Check world prim
    world = stage.GetPrimAtPath("/World")
    assert world.IsValid(), "World not found"

    # Check variant cascade works
    vset = world.GetVariantSets().GetVariantSet("representation")

    for mode in ["points", "vdw"]:
        vset.SetVariantSelection(mode)

        # Check Carbon instance
        carbon = stage.GetPrimAtPath("/World/C")
        assert carbon.IsValid(), "Carbon instance not found"

        # Check it has geometry
        sphere = stage.GetPrimAtPath("/World/C/Sphere")
        assert sphere.IsValid(), f"Carbon/Sphere not found in {mode} mode"

        # Check position is LOCAL (not from template)
        xform = UsdGeom.Xformable(carbon)
        ops = xform.GetOrderedXformOps()
        assert len(ops) > 0, "No transform ops on instance"
        print(f"✓ Carbon in {mode} mode: has Sphere, has transform")

    # Reset to balls
    vset.SetVariantSelection("balls")
    print("\n✓ Variant cascade verified")


if __name__ == "__main__":
    # Paths
    output_dir = os.path.join(root_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    template_path = os.path.join(root_dir, "assets", "level1_elements", "element_templates.usda")
    output_path = os.path.join(output_dir, "element_grid_demo.usda")

    # Check template exists
    if not os.path.exists(template_path):
        print(f"ERROR: Template not found: {template_path}")
        print("Run templates/01_create_element_templates.py first")
        sys.exit(1)

    create_element_grid_demo(output_path, template_path)
    verify_demo(output_path)
