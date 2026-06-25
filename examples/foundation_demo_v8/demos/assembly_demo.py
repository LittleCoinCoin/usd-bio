#!/usr/bin/env python3
"""
Demo: ABL kinase + ATP assembly with variant switching.

Loads the assembly from level4_assemblies and wraps it in a /World
prim with a top-level representation VariantSet for coordinated
visualization mode switching across the entire complex.
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf

REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]


def create_assembly_demo(output_path: str, assembly_path: str):
    """Create demo scene with ABL kinase assembly."""
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # coordinates in Ångström (1 Å = 1e-10 m)
    stage.SetDefaultPrim(stage.DefinePrim("/World"))

    # SubLayer the assembly (brings in /ABLComplex and /_class_/)
    stage.GetRootLayer().subLayerPaths.append(
        os.path.relpath(assembly_path, os.path.dirname(output_path))
    )

    world = stage.GetPrimAtPath("/World")

    # World-level representation VariantSet
    world_vset = world.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        world_vset.AddVariant(mode)

    # Reference the complex under /World
    complex_prim = stage.GetPrimAtPath("/ABLComplex")

    # World variant cascade -> complex
    for mode in REPRESENTATIONS:
        world_vset.SetVariantSelection(mode)
        with world_vset.GetVariantEditContext():
            complex_prim.GetVariantSets().GetVariantSet(
                "representation").SetVariantSelection(mode)

    # Default to "balls" representation
    world_vset.SetVariantSelection("balls")

    stage.Save()

    print(f"Created: {output_path}")
    print(f"Representations: {REPRESENTATIONS}")
    print(f"Default: balls")


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    assembly_path = os.path.join(
        root_dir, "assets", "level4_assemblies", "abl_kinase_complex.usda"
    )

    if not os.path.exists(assembly_path):
        print(f"ERROR: Assembly not found: {assembly_path}")
        print("Run templates/04_create_assembly.py first")
        sys.exit(1)

    output_path = os.path.join(output_dir, "assembly_demo.usda")
    create_assembly_demo(output_path, assembly_path)
    print(f"\nView with: usdview {output_path}")
