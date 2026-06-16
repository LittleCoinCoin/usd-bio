#!/usr/bin/env python3
"""
Create element class templates with scientific metadata and variant representations.

Pattern applied (from docs):
- 02_inherits_arc.md: CreateClassPrim() for templates
- 03_variantsets_arc.md: SetVariantSelection() BEFORE GetVariantEditContext()
- 08_schemas_attributes.md: Custom bio: namespace for scientific data
"""

import os
import sys

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf
from data import ELEMENTS, get_scaled_radius


REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]


def create_element_templates(output_path: str):
    """Create USD file with element class templates."""

    # Clean start
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.SetMetadata("comment", "Element templates with scientific metadata")

    # Create class scope
    stage.CreateClassPrim("/_class_")

    for symbol, data in ELEMENTS.items():
        class_path = f"/_class_/{symbol}"

        # Create class prim (abstract, not rendered directly)
        class_prim = stage.CreateClassPrim(class_path)

        # =====================================================================
        # SCIENTIFIC METADATA (bio: namespace)
        # =====================================================================
        class_prim.CreateAttribute("bio:symbol", Sdf.ValueTypeNames.Token).Set(symbol)
        class_prim.CreateAttribute("bio:name", Sdf.ValueTypeNames.String).Set(data["name"])
        class_prim.CreateAttribute("bio:atomicNumber", Sdf.ValueTypeNames.Int).Set(data["atomic_number"])
        class_prim.CreateAttribute("bio:atomicMass", Sdf.ValueTypeNames.Float).Set(data["atomic_mass"])
        class_prim.CreateAttribute("bio:vdwRadius", Sdf.ValueTypeNames.Float).Set(data["vdw_radius"])
        class_prim.CreateAttribute("bio:covalentRadius", Sdf.ValueTypeNames.Float).Set(data["covalent_radius"])
        class_prim.CreateAttribute("bio:electronegativity", Sdf.ValueTypeNames.Float).Set(data["electronegativity"])
        class_prim.CreateAttribute("bio:notes", Sdf.ValueTypeNames.String).Set(data["bio_notes"])

        # =====================================================================
        # VARIANT SET: representation
        # Pattern: SetVariantSelection() BEFORE GetVariantEditContext()
        # =====================================================================
        vset = class_prim.GetVariantSets().AddVariantSet("representation")

        # Add all variants first
        for mode in REPRESENTATIONS:
            vset.AddVariant(mode)

        # Define geometry INSIDE each variant
        for mode in REPRESENTATIONS:
            # CRITICAL: SetVariantSelection BEFORE GetVariantEditContext
            vset.SetVariantSelection(mode)

            with vset.GetVariantEditContext():
                # Create sphere with mode-specific radius
                sphere_path = f"{class_path}/Sphere"
                sphere = UsdGeom.Sphere.Define(stage, sphere_path)

                # Radius from scientific VDW data, scaled by mode
                radius = get_scaled_radius(symbol, mode)
                sphere.CreateRadiusAttr(radius)

                # CPK color
                color = Gf.Vec3f(*data["cpk_color"])
                sphere.CreateDisplayColorAttr([color])

                # Extent (required for proper bounds)
                sphere.CreateExtentAttr([(-radius, -radius, -radius), (radius, radius, radius)])

        # Clear variant selection (let instances choose)
        vset.ClearVariantSelection()

    stage.Save()
    print(f"Created: {output_path}")
    print(f"Elements: {len(ELEMENTS)}")
    print(f"Representations: {REPRESENTATIONS}")

    return output_path


def verify_templates(usd_path: str):
    """Verify the templates are correctly structured."""
    stage = Usd.Stage.Open(usd_path)

    print("\n--- Verification ---")

    # Check a sample element
    carbon = stage.GetPrimAtPath("/_class_/C")
    assert carbon.IsValid(), "Carbon class not found"

    # Check scientific metadata
    atomic_num = carbon.GetAttribute("bio:atomicNumber").Get()
    assert atomic_num == 6, f"Wrong atomic number: {atomic_num}"
    print(f"✓ Carbon bio:atomicNumber = {atomic_num}")

    # Check variant set exists
    vsets = carbon.GetVariantSets()
    assert vsets.HasVariantSet("representation"), "Missing representation variant set"
    print(f"✓ Carbon has 'representation' variant set")

    # Check each variant has geometry with correct radius
    vset = vsets.GetVariantSet("representation")
    for mode in REPRESENTATIONS:
        vset.SetVariantSelection(mode)
        sphere = stage.GetPrimAtPath("/_class_/C/Sphere")
        assert sphere.IsValid(), f"Sphere not found in {mode} variant"

        radius = UsdGeom.Sphere(sphere).GetRadiusAttr().Get()
        expected = get_scaled_radius("C", mode)
        assert abs(radius - expected) < 0.001, f"Wrong radius in {mode}: {radius} != {expected}"
        print(f"✓ Carbon/{mode}: radius = {radius:.3f} Å")

    print("\n✓ All verifications passed")


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "assets", "level1_elements")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "element_templates.usda")
    create_element_templates(output_path)
    verify_templates(output_path)
