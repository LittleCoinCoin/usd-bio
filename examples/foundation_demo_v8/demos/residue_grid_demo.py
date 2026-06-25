#!/usr/bin/env python3
"""
Demo: Grid of all 20 amino acid residues with variant switching.

Shows all standard amino acids in a 5×4 grid with coordinated
representation switching via variant cascade.
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf
from data import RESIDUES, get_residue_type, get_type_color

REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]
GRID_SPACING = 8.0  # Å between residue centers


def create_residue_grid_demo(output_path: str, residue_template_path: str):
    """Create demo scene with all residues in a grid."""
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # coordinates in Ångström (1 Å = 1e-10 m)
    stage.SetDefaultPrim(stage.DefinePrim("/World"))
    stage.GetRootLayer().subLayerPaths.append(residue_template_path)

    world = stage.GetPrimAtPath("/World")
    world_vset = world.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        world_vset.AddVariant(mode)

    residue_codes = list(RESIDUES.keys())
    cols, rows = 5, 4
    residue_prims = []

    for i, code in enumerate(residue_codes):
        col, row = i % cols, i // cols
        x = (col - cols / 2 + 0.5) * GRID_SPACING
        z = (row - rows / 2 + 0.5) * GRID_SPACING

        inst_path = f"/World/{code}"
        inst_xform = UsdGeom.Xform.Define(stage, inst_path)
        inst_prim = inst_xform.GetPrim()

        inst_prim.GetInherits().AddInherit(f"/_class_/{code}")
        inst_xform.AddTranslateOp().Set(Gf.Vec3d(x, 0, z))

        inst_vset = inst_prim.GetVariantSets().AddVariantSet("representation")
        for mode in REPRESENTATIONS:
            inst_vset.AddVariant(mode)
        inst_vset.ClearVariantSelection()

        residue_prims.append(inst_prim)

    # World variant cascade
    for mode in REPRESENTATIONS:
        world_vset.SetVariantSelection(mode)
        with world_vset.GetVariantEditContext():
            for prim in residue_prims:
                prim.GetVariantSets().GetVariantSet("representation").SetVariantSelection(mode)

    world_vset.SetVariantSelection("balls")
    stage.Save()

    print(f"Created: {output_path}")
    print(f"Residues: {len(residue_codes)} in {cols}×{rows} grid")
    print(f"Grid spacing: {GRID_SPACING} Å")


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    residue_template_path = os.path.join(
        root_dir, "assets", "level3_residues", "residue_templates.usda"
    )

    if not os.path.exists(residue_template_path):
        print(f"ERROR: Residue templates not found: {residue_template_path}")
        print("Run templates/03_create_residue_templates.py first")
        sys.exit(1)

    output_path = os.path.join(output_dir, "residue_grid_demo.usda")
    create_residue_grid_demo(output_path, residue_template_path)
    print(f"\nView with: usdview {output_path}")
