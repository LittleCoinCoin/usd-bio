#!/usr/bin/env python3
"""
Demo: ABL kinase trajectory playback via Value Clips.

Composes the static assembly topology with time-varying positions
from MD trajectory data using UsdClipsAPI. Scrubbing the usdview
timeline shows protein motion across simulation frames.

Pattern applied (from docs):
- Value Clips: topology/clip separation (like animation clips in film)
- Static topology (bonds, metadata, colors) + dynamic positions

WHY NOT a /World wrapper prim (this demo's pattern before the v8-gap-closure
representation-variant-cascade fix): USD variant-selection fallthrough only
cascades a GetVariantEditContext()-scoped edit to prims that are NAMESPACE
DESCENDANTS of the variant-owning prim in the same composed site. /World and
/ABLComplex were SIBLINGS here -- /ABLComplex arrived via SubLayer at its own
top-level path, not as a child of /World -- so the per-mode
`with world_vset.GetVariantEditContext(): complex_prim...SetVariantSelection(
mode)` loop did not scope an opinion under /World's variant at all; each
iteration instead wrote an unconditional `over "ABLComplex" { variants =
{...} }` block at /ABLComplex's own path, and only the LAST iteration's
value survived composition (verified directly in the previously-committed
output/trajectory_demo.usda: /World's emitted variant blocks are empty `{}`
and /ABLComplex carries one unconditional opinion regardless of which
/World variant is selected in usdview). This was invisible in practice only
because Sphere+Cylinder happen to both be visible in ballstick and the
pinned selection ("points") also renders something under every mode --
see demos/curves_demo.py's WHY-NOT comment (same defect, but there it WAS
gate-3-visible because Bonds is genuinely visibility-gated per mode).
Canonical fix (USD model-hierarchy convention, confirmed via context7
/websites/openusd_release docs on GetVariantEditContext/EditTarget scoping):
make the actual geometry root ALSO the defaultPrim and the variant owner,
so cascade and lookup happen on the same prim -- no dispatcher indirection
to go stale. No /World prim is created.
"""

import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from pxr import Usd, UsdGeom, Sdf, Gf, Vt

REPRESENTATIONS = ["points", "balls", "vdw", "ballstick"]
DEFAULT_MODE = "points"  # faster rendering with 4676 atoms


def create_trajectory_demo(output_path: str, assembly_path: str,
                           clip_path: str, n_frames: int):
    """Create demo scene with trajectory playback via Value Clips."""
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # coordinates in Ångström (1 Å = 1e-10 m)
    # NOTE: authored explicitly on this root layer (not just relied on via
    # sublayer fallthrough) because usdchecker's StageMetadataChecker.
    # MissingMetersPerUnitMetadata validates the root layer's own authored
    # metadata, not the composed/resolved value -- discovered while
    # regenerating this file for the /World-removal fix (this stage
    # previously carried metersPerUnit only because a prior generation of
    # this script authored it; the source in this repo at the start of this
    # fix cycle did not, which is a latent gap fixed here while already
    # touching this generator).

    # Set timeline range
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(n_frames - 1)
    stage.SetFramesPerSecond(10)  # 10 fps for trajectory playback

    # SubLayer the assembly (static topology with hierarchy, variants, metadata)
    output_dir = os.path.dirname(output_path)
    stage.GetRootLayer().subLayerPaths.append(
        os.path.relpath(assembly_path, output_dir)
    )

    # defaultPrim = the actual geometry root. /ABLComplex's own
    # `representation` VariantSet is the single selection surface for this
    # stage -- no proxy dispatcher prim needed.
    complex_prim = stage.GetPrimAtPath("/ABLComplex")
    stage.SetDefaultPrim(complex_prim)

    complex_prim.GetVariantSets().GetVariantSet(
        "representation").SetVariantSelection(DEFAULT_MODE)

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
    print(f"  Default representation: {DEFAULT_MODE} (defaultPrim=/ABLComplex)")


def verify_trajectory(output_path: str, n_frames: int):
    """Verify trajectory demo setup."""
    stage = Usd.Stage.Open(output_path)

    print("\n--- Trajectory Demo Verification ---")

    # Check timeline
    start = stage.GetStartTimeCode()
    end = stage.GetEndTimeCode()
    assert start == 0, f"Expected start=0, got {start}"
    assert end == n_frames - 1, f"Expected end={n_frames-1}, got {end}"

    # defaultPrim + default representation selection resolve on fresh open
    default_prim = stage.GetDefaultPrim()
    assert default_prim.IsValid() and default_prim.GetPath() == Sdf.Path("/ABLComplex"), (
        f"Expected defaultPrim=/ABLComplex, got "
        f"{default_prim.GetPath() if default_prim else None}"
    )
    default_sel = default_prim.GetVariantSets().GetVariantSet(
        "representation").GetVariantSelection()
    assert default_sel == DEFAULT_MODE, (
        f"Expected default representation selection {DEFAULT_MODE!r}, got {default_sel!r}"
    )
    print(f"  PASS: fresh-open default representation resolves to {default_sel!r}")

    assert stage.GetPrimAtPath("/World").IsValid() is False, (
        "Decorative /World dispatcher prim should no longer be authored"
    )
    print("  PASS: no decorative /World dispatcher prim on stage")

    sample_atom_check = stage.GetPrimAtPath("/ABLComplex/Chain_A/ACE_1/HH31")
    assert sample_atom_check.IsValid(), "sample atom prim missing"
    atom_children = sample_atom_check.GetChildren()
    assert len(atom_children) == 1, (
        f"Expected exactly 1 gprim child on fresh-open atom ({DEFAULT_MODE} default), "
        f"got {len(atom_children)}: {[c.GetName() for c in atom_children]}"
    )
    print(f"  PASS: fresh-open sample atom has exactly 1 child gprim "
          f"({atom_children[0].GetTypeName()})")
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
