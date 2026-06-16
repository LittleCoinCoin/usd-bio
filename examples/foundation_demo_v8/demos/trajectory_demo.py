#!/usr/bin/env python3
"""
Demo: ABL kinase trajectory playback via Value Clips.

Composes the static assembly topology with time-varying positions
from MD trajectory data using UsdClipsAPI. Scrubbing the usdview
timeline shows protein motion across simulation frames.

Pattern applied (from docs):
- Value Clips: topology/clip separation (like animation clips in film)
- Static topology (bonds, metadata, colors) + dynamic positions
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf, Vt

REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]


def create_trajectory_demo(output_path: str, assembly_path: str,
                           clip_path: str, n_frames: int):
    """Create demo scene with trajectory playback via Value Clips."""
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.SetDefaultPrim(stage.DefinePrim("/World"))

    # Set timeline range
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(n_frames - 1)
    stage.SetFramesPerSecond(10)  # 10 fps for trajectory playback

    # SubLayer the assembly (static topology with hierarchy, variants, metadata)
    output_dir = os.path.dirname(output_path)
    stage.GetRootLayer().subLayerPaths.append(
        os.path.relpath(assembly_path, output_dir)
    )

    world = stage.GetPrimAtPath("/World")

    # World-level representation VariantSet
    world_vset = world.GetVariantSets().AddVariantSet("representation")
    for mode in REPRESENTATIONS:
        world_vset.AddVariant(mode)

    complex_prim = stage.GetPrimAtPath("/ABLComplex")

    # World variant cascade -> complex
    for mode in REPRESENTATIONS:
        world_vset.SetVariantSelection(mode)
        with world_vset.GetVariantEditContext():
            complex_prim.GetVariantSets().GetVariantSet(
                "representation").SetVariantSelection(mode)

    # Default to "points" for trajectory (faster rendering with 4676 atoms)
    world_vset.SetVariantSelection("points")

    # =========================================================================
    # VALUE CLIPS SETUP
    # =========================================================================
    # Attach clips to the complex root prim. The clip file contains
    # time-sampled xformOp:translate values for all atom prims under
    # /ABLComplex, which override the static positions from the topology.
    clips_api = Usd.ClipsAPI(complex_prim)

    # Path to clip file (relative to this output file)
    clip_rel_path = os.path.relpath(clip_path, output_dir)
    clips_api.SetClipAssetPaths([Sdf.AssetPath(clip_rel_path)])

    # Root prim path within the clip file
    clips_api.SetClipPrimPath("/ABLComplex")

    # Map stage time 1:1 to clip time
    clip_times = Vt.Vec2dArray(
        [Gf.Vec2d(float(i), float(i)) for i in range(n_frames)]
    )
    clips_api.SetClipTimes(clip_times)

    # Clip 0 is active from frame 0 onward
    clips_api.SetClipActive(Vt.Vec2dArray([Gf.Vec2d(0.0, 0.0)]))

    stage.Save()

    print(f"Created: {output_path}")
    print(f"  Timeline: 0-{n_frames - 1} ({n_frames} frames at 10 fps)")
    print(f"  Clip: {clip_rel_path}")
    print(f"  Default representation: points")


def verify_trajectory(output_path: str, n_frames: int):
    """Verify trajectory demo setup."""
    stage = Usd.Stage.Open(output_path)

    print("\n--- Trajectory Demo Verification ---")

    # Check timeline
    start = stage.GetStartTimeCode()
    end = stage.GetEndTimeCode()
    assert start == 0, f"Expected start=0, got {start}"
    assert end == n_frames - 1, f"Expected end={n_frames-1}, got {end}"
    print(f"  PASS: timeline 0-{int(end)} ({n_frames} frames)")

    # Check clips API on complex prim
    complex_prim = stage.GetPrimAtPath("/ABLComplex")
    clips_api = Usd.ClipsAPI(complex_prim)

    asset_paths = clips_api.GetClipAssetPaths()
    assert len(asset_paths) == 1, f"Expected 1 clip, got {len(asset_paths)}"
    print(f"  PASS: clip asset path set")

    prim_path = clips_api.GetClipPrimPath()
    assert prim_path == "/ABLComplex", f"Expected /ABLComplex, got {prim_path}"
    print(f"  PASS: clip prim path = {prim_path}")

    # Check position changes between frames
    sample_path = "/ABLComplex/Chain_A/ACE_1/HH31"
    sample = stage.GetPrimAtPath(sample_path)
    xformable = UsdGeom.Xformable(sample)

    pos_start = xformable.ComputeLocalToWorldTransform(Usd.TimeCode(0)).ExtractTranslation()
    pos_end = xformable.ComputeLocalToWorldTransform(
        Usd.TimeCode(n_frames - 1)).ExtractTranslation()
    diff = (pos_start - pos_end).GetLength()
    assert diff > 0.1, f"Positions should differ between frames (diff={diff})"
    print(f"  PASS: atom moves between frames (diff={diff:.2f} A)")

    print("\n  ALL VERIFICATIONS PASSED")


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    assembly_path = os.path.join(
        root_dir, "assets", "level4_assemblies", "abl_kinase_complex.usda"
    )
    clip_path = os.path.join(root_dir, "output", "clips", "trajectory_clip.usda")

    if not os.path.exists(assembly_path):
        print(f"ERROR: Assembly not found: {assembly_path}")
        print("Run templates/04_create_assembly.py first")
        sys.exit(1)

    if not os.path.exists(clip_path):
        print(f"ERROR: Clip file not found: {clip_path}")
        print("Run converters/xtc_to_clips.py first")
        sys.exit(1)

    # Read frame count from clip file
    clip_stage = Usd.Stage.Open(clip_path)
    sample = clip_stage.GetPrimAtPath("/ABLComplex/Chain_A/ACE_1/HH31")
    xformable = UsdGeom.Xformable(sample)
    n_frames = len(xformable.GetOrderedXformOps()[0].GetTimeSamples())
    del clip_stage

    output_path = os.path.join(output_dir, "trajectory_demo.usda")
    create_trajectory_demo(output_path, assembly_path, clip_path, n_frames)
    verify_trajectory(output_path, n_frames)
    print(f"\nView with: usdview {output_path}")
