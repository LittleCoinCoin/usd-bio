#!/usr/bin/env python3
"""
Demo: BasisCurves bond encoding vs Cylinder bonds — size comparison and trajectory.

Composes the BasisCurves assembly + UsdClipsAPI trajectory clip, prints a
size-comparison table against the cylinder counterparts, and validates the stage.

Pattern applied:
- BasisCurves replaces 2,428 Xform/Cylinder prim pairs with one draw-call prim
- Value Clips: time-sampled points on /ABLComplex/Bonds across MD frames
- SubLayer composition: static topology + dynamic clip wired via UsdClipsAPI
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf, Vt


def compare_file_sizes(curves_assembly_path: str, cylinder_assembly_path: str,
                       curves_clip_path: str, cylinder_clip_path: str):
    """Print METRIC lines comparing BasisCurves vs Cylinder file sizes.

    Prints two lines:
      METRIC artifact=assembly cylinder_bytes=N curves_bytes=N ratio=F
      METRIC artifact=clip cylinder_bytes=N curves_bytes=N ratio=F

    ratio = curves_bytes / cylinder_bytes (< 1.0 means curves is smaller).
    """
    def _size(p):
        return os.path.getsize(p) if os.path.exists(p) else 0

    asm_cyl = _size(cylinder_assembly_path)
    asm_crv = _size(curves_assembly_path)
    asm_ratio = asm_crv / asm_cyl if asm_cyl > 0 else float("inf")
    print(f"METRIC artifact=assembly cylinder_bytes={asm_cyl} "
          f"curves_bytes={asm_crv} ratio={asm_ratio:.4f}")

    clip_cyl = _size(cylinder_clip_path)
    clip_crv = _size(curves_clip_path)
    clip_ratio = clip_crv / clip_cyl if clip_cyl > 0 else float("inf")
    print(f"METRIC artifact=clip cylinder_bytes={clip_cyl} "
          f"curves_bytes={clip_crv} ratio={clip_ratio:.4f}")


def create_curves_demo(output_path: str, curves_assembly_path: str,
                       curves_clip_path: str):
    """Create output/curves_demo.usda composing BasisCurves assembly + clip.

    SubLayers the BasisCurves assembly for static topology, then wires
    UsdClipsAPI on /ABLComplex to animate bond-endpoint positions from the
    BasisCurves trajectory clip.

    Args:
        output_path: Absolute path for the output .usda demo stage.
        curves_assembly_path: Absolute path to abl_kinase_complex_curves.usda.
        curves_clip_path: Absolute path to trajectory_clip_curves.usda.
    """
    # Determine frame count from clip
    clip_stage = Usd.Stage.Open(curves_clip_path)
    bc_clip = UsdGeom.BasisCurves(clip_stage.GetPrimAtPath("/ABLComplex/Bonds"))
    ts = bc_clip.GetPointsAttr().GetTimeSamples()
    n_frames = len(ts)
    del clip_stage

    if os.path.exists(output_path):
        os.remove(output_path)

    output_dir = os.path.dirname(output_path)
    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(n_frames - 1)
    stage.SetFramesPerSecond(10)
    stage.SetMetadata("comment",
        "BasisCurves demo stage: single-prim bond encoding + MD trajectory clip. "
        "Bonds prim uses time-sampled points (one Vec3fArray/frame) vs "
        "per-bond Xform+Cylinder translate+orient+height for the cylinder approach.")

    # SubLayer the BasisCurves assembly (static topology: atoms, bonds, metadata)
    stage.GetRootLayer().subLayerPaths.append(
        os.path.relpath(curves_assembly_path, output_dir)
    )

    # defaultPrim comes from the SubLayered assembly (/ABLComplex)
    stage.SetDefaultPrim(stage.GetPrimAtPath("/ABLComplex"))

    # Wire UsdClipsAPI on /ABLComplex to animate bond-endpoint positions
    complex_prim = stage.GetPrimAtPath("/ABLComplex")
    clips_api = Usd.ClipsAPI(complex_prim)

    clip_rel_path = os.path.relpath(curves_clip_path, output_dir)
    clips_api.SetClipAssetPaths([Sdf.AssetPath(clip_rel_path)])
    clips_api.SetClipPrimPath("/ABLComplex")

    clip_times = Vt.Vec2dArray(
        [Gf.Vec2d(float(i), float(i)) for i in range(n_frames)]
    )
    clips_api.SetClipTimes(clip_times)
    clips_api.SetClipActive(Vt.Vec2dArray([Gf.Vec2d(0.0, 0.0)]))

    stage.Save()

    print(f"Created: {output_path}")
    print(f"  Timeline: 0-{n_frames - 1} ({n_frames} frames at 10 fps)")
    print(f"  SubLayer: {os.path.basename(curves_assembly_path)}")
    print(f"  Clip: {os.path.basename(curves_clip_path)}")

    # Structural assertions
    reopen = Usd.Stage.Open(output_path)
    bonds_prim = reopen.GetPrimAtPath("/ABLComplex/Bonds")
    assert bonds_prim.IsValid(), "/ABLComplex/Bonds not found in demo stage"
    bc = UsdGeom.BasisCurves(bonds_prim)
    assert bc, "/ABLComplex/Bonds is not UsdGeomBasisCurves"
    print("  PASS: /ABLComplex/Bonds is UsdGeomBasisCurves")

    chain_a = reopen.GetPrimAtPath("/ABLComplex/Chain_A")
    assert chain_a.IsValid(), "Chain_A missing from demo stage"
    print("  PASS: /ABLComplex/Chain_A exists")

    clips_check = Usd.ClipsAPI(reopen.GetPrimAtPath("/ABLComplex"))
    asset_paths = clips_check.GetClipAssetPaths()
    assert len(asset_paths) > 0, "UsdClipsAPI clip not wired on /ABLComplex"
    print(f"  PASS: UsdClipsAPI clip wired ({len(asset_paths)} asset path(s))")

    return output_path


if __name__ == "__main__":
    output_dir = os.path.join(root_dir, "output")
    assets_dir = os.path.join(root_dir, "assets", "level4_assemblies")
    clips_dir = os.path.join(output_dir, "clips")

    curves_assembly = os.path.join(assets_dir, "abl_kinase_complex_curves.usda")
    cylinder_assembly = os.path.join(assets_dir, "abl_kinase_complex.usda")
    curves_clip = os.path.join(clips_dir, "trajectory_clip_curves.usda")
    cylinder_clip = os.path.join(clips_dir, "trajectory_clip.usda")
    demo_output = os.path.join(output_dir, "curves_demo.usda")

    for path, label in [
        (curves_assembly, "BasisCurves assembly"),
        (curves_clip, "BasisCurves clip"),
    ]:
        if not os.path.exists(path):
            print(f"ERROR: {label} not found: {path}")
            sys.exit(1)

    create_curves_demo(demo_output, curves_assembly, curves_clip)

    print("\n--- File Size Comparison ---")
    compare_file_sizes(curves_assembly, cylinder_assembly, curves_clip, cylinder_clip)
