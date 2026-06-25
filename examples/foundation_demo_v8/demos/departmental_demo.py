"""
departmental_demo.py
====================
Compose a 5-layer departmental stage for the ABL kinase system.

SubLayers all five department layers (biology → protocol → dynamics →
analysis → review) into a single root stage and verifies clean composition.

Usage (from examples/foundation_demo_v8/):
    source ../../load_env.sh
    python3 demos/departmental_demo.py
"""

import os
import sys

from pxr import Usd, UsdGeom, Sdf


def create_departmental_stage(output_path: str, layer_dir: str) -> Usd.Stage:
    """
    Create output/departmental_demo.usda SubLayering all 5 department layers.

    SubLayer order: biology → protocol → dynamics → analysis → review
    (review opinions are strongest in SubLayer LIVERPS ordering; biology
    topology is the base — weakest).  In USD subLayerPaths, index 0 is
    the *strongest* override.  We therefore list them: review first,
    analysis, dynamics, protocol, biology last.
    """
    output_dir = os.path.dirname(os.path.abspath(output_path))
    layer_abs = os.path.abspath(layer_dir)

    # Resolve relative paths from output_path to each layer file
    def rel(name: str) -> str:
        abs_path = os.path.join(layer_abs, name)
        return os.path.relpath(abs_path, output_dir)

    # Create (or overwrite) the root stage
    stage = Usd.Stage.CreateNew(output_path)
    root_layer = stage.GetRootLayer()

    # Stage metadata
    stage.SetMetadata("metersPerUnit", 1e-10)
    stage.SetMetadata("upAxis", "Y")
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(19)
    stage.SetFramesPerSecond(10)

    # SubLayer order: strongest override first (review), weakest last (biology)
    layer_names = ["review.usda", "analysis.usda", "dynamics.usda",
                   "protocol.usda", "biology.usda"]
    for name in layer_names:
        root_layer.subLayerPaths.append(rel(name))

    # Set default prim to /ABLComplex
    abl = stage.DefinePrim("/ABLComplex")
    stage.SetDefaultPrim(abl)

    stage.Save()
    return stage


def verify_departmental_stage(output_path: str) -> bool:
    """
    Open the written stage fresh and verify composition invariants.
    Returns True if all checks pass, raises AssertionError otherwise.
    """
    stage = Usd.Stage.Open(output_path)

    # 1. No composition errors
    errors = stage.GetCompositionErrors()
    assert errors == [], f"Composition errors: {errors}"

    # 2. Five sublayers
    sublayers = stage.GetRootLayer().subLayerPaths
    assert len(sublayers) == 5, f"Expected 5 sublayers, got {len(sublayers)}: {sublayers}"

    # 3. Traverse and count prims
    prims = list(stage.Traverse())
    prim_count = len(prims)

    # 4. bio:rmsd time-sampled
    abl = stage.GetPrimAtPath("/ABLComplex")
    rmsd_attr = abl.GetAttribute("bio:rmsd")
    rmsd_sampled = rmsd_attr and len(rmsd_attr.GetTimeSamples()) >= 20

    # 5. Attribute count on /ABLComplex
    attr_count = len(abl.GetAttributes())

    print("=" * 60)
    print("Departmental Stage Composition Summary")
    print("=" * 60)
    print(f"  Stage:          {output_path}")
    print(f"  Sublayers:      {len(sublayers)}")
    for sl in sublayers:
        print(f"    - {sl}")
    print(f"  Total prims:    {prim_count}")
    print(f"  /ABLComplex attrs: {attr_count}")
    print(f"  bio:rmsd time-sampled (≥20): {rmsd_sampled}")
    print(f"  Composition errors: {len(errors)}")
    print("PASS: stage.GetCompositionErrors() is empty, 5 sublayers confirmed")
    print("=" * 60)

    return True


if __name__ == "__main__":
    # Run from examples/foundation_demo_v8/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    output_path = os.path.join(base_dir, "output", "departmental_demo.usda")
    layer_dir = os.path.join(base_dir, "assets", "level6_departmental")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print("Creating departmental stage ...")
    create_departmental_stage(output_path, layer_dir)
    print(f"Written: {output_path}")

    print("Verifying ...")
    verify_departmental_stage(output_path)

    sys.exit(0)
