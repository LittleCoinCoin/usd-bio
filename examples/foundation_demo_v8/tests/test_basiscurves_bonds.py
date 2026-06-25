"""
test_basiscurves_bonds.py
==========================
Read-back tests for the BasisCurves bond encoding artifacts (Exp 5).

Opens all three BasisCurves artifacts fresh (no generator code in scope) and
asserts structural correctness, size improvements over cylinder counterparts,
and trajectory animation coverage.

Bond count reference: 2428 bonds confirmed from Step 1 assembly read-back.
[source: examples/foundation_demo_v8/assets/level4_assemblies/abl_kinase_complex_curves.usda]

Falsification-resistance: expectations are independently derived from the leaf
spec and Success Gates, not from generator state.

Usage (from examples/foundation_demo_v8/):
    source ../../load_env.sh
    python3 tests/test_basiscurves_bonds.py
"""

import os
import sys

from pxr import Usd, UsdGeom, Sdf

# ---------------------------------------------------------------------------
# Constants derived from Step 1 verified read-back
# [source: e054e18 — curveVertexCounts length: 2428, points length: 4856]
# ---------------------------------------------------------------------------
EXPECTED_BOND_COUNT = 2428
EXPECTED_POINTS_COUNT = EXPECTED_BOND_COUNT * 2  # 4856


# ---------------------------------------------------------------------------
# Test functions
# ---------------------------------------------------------------------------

def test_curves_assembly_structure(assembly_path: str) -> None:
    """Assert BasisCurves prim structure in the curves assembly.

    Checks:
    - /ABLComplex/Bonds is UsdGeomBasisCurves
    - curveVertexCounts length == EXPECTED_BOND_COUNT (2428)
    - points length == EXPECTED_BOND_COUNT * 2 (4856)
    - No Cylinder type prims under /ABLComplex/Bonds
    - type == 'linear', wrap == 'nonperiodic'
    """
    stage = Usd.Stage.Open(assembly_path)
    assert stage, f"Failed to open assembly: {assembly_path}"

    bonds_prim = stage.GetPrimAtPath("/ABLComplex/Bonds")
    assert bonds_prim.IsValid(), "/ABLComplex/Bonds prim not found in curves assembly"

    bc = UsdGeom.BasisCurves(bonds_prim)
    assert bc, "/ABLComplex/Bonds is not UsdGeomBasisCurves"

    counts = bc.GetCurveVertexCountsAttr().Get()
    assert counts is not None, "curveVertexCounts attribute is None"
    assert len(counts) == EXPECTED_BOND_COUNT, (
        f"curveVertexCounts length: expected {EXPECTED_BOND_COUNT}, got {len(counts)}"
    )

    pts = bc.GetPointsAttr().Get()
    assert pts is not None, "points attribute is None"
    assert len(pts) == EXPECTED_POINTS_COUNT, (
        f"points length: expected {EXPECTED_POINTS_COUNT}, got {len(pts)}"
    )

    # No Cylinder prims under /ABLComplex/Bonds
    bonds_prefix = "/ABLComplex/Bonds"
    cylinder_found = any(
        p.GetTypeName() == "Cylinder"
        for p in stage.Traverse()
        if str(p.GetPath()).startswith(bonds_prefix)
    )
    assert not cylinder_found, "Found unexpected Cylinder prim(s) under /ABLComplex/Bonds"

    type_val = bonds_prim.GetAttribute("type").Get()
    wrap_val = bonds_prim.GetAttribute("wrap").Get()
    assert type_val == "linear", f"Expected type='linear', got {type_val}"
    assert wrap_val == "nonperiodic", f"Expected wrap='nonperiodic', got {wrap_val}"

    print(
        f"  PASS test_curves_assembly_structure: "
        f"{len(counts)} bonds, {len(pts)} points, type={type_val}, wrap={wrap_val}, "
        f"no Cylinder prims"
    )


def test_curves_clip_time_samples(clip_path: str) -> None:
    """Assert /ABLComplex/Bonds.points has >= 20 time samples in the clip.

    The clip was generated with n_frames=20, so at least 20 time samples
    must be present on the points attribute.
    """
    stage = Usd.Stage.Open(clip_path)
    assert stage, f"Failed to open clip: {clip_path}"

    bonds_prim = stage.GetPrimAtPath("/ABLComplex/Bonds")
    assert bonds_prim.IsValid(), "/ABLComplex/Bonds not found in clip"

    bc = UsdGeom.BasisCurves(bonds_prim)
    assert bc, "/ABLComplex/Bonds in clip is not UsdGeomBasisCurves"

    ts = bc.GetPointsAttr().GetTimeSamples()
    assert len(ts) >= 20, (
        f"Expected >= 20 time samples on points attribute, got {len(ts)}"
    )

    print(
        f"  PASS test_curves_clip_time_samples: "
        f"{len(ts)} time samples on /ABLComplex/Bonds.points"
    )


def test_assembly_size_reduction(curves_assembly_path: str,
                                  cylinder_assembly_path: str) -> None:
    """Assert curves assembly is smaller than cylinder assembly.

    BasisCurves (one prim) must produce a smaller .usda than 2,428
    Xform+Cylinder prim pairs.
    """
    assert os.path.exists(curves_assembly_path), (
        f"Curves assembly not found: {curves_assembly_path}"
    )
    assert os.path.exists(cylinder_assembly_path), (
        f"Cylinder assembly not found: {cylinder_assembly_path}"
    )

    curves_bytes = os.path.getsize(curves_assembly_path)
    cylinder_bytes = os.path.getsize(cylinder_assembly_path)
    ratio = curves_bytes / cylinder_bytes if cylinder_bytes > 0 else float("inf")

    assert curves_bytes < cylinder_bytes, (
        f"Expected curves assembly ({curves_bytes:,} bytes) < "
        f"cylinder assembly ({cylinder_bytes:,} bytes); ratio={ratio:.4f}"
    )

    print(
        f"  PASS test_assembly_size_reduction: "
        f"curves={curves_bytes:,} bytes < cylinder={cylinder_bytes:,} bytes "
        f"(ratio={ratio:.4f})"
    )


def test_clip_size_reduction(curves_clip_path: str,
                              cylinder_clip_path: str) -> None:
    """Assert curves clip is smaller than cylinder clip.

    One Vec3fArray per frame (points) vs per-bond translate+orient+height
    writes per frame yields a much smaller clip file.
    """
    assert os.path.exists(curves_clip_path), (
        f"Curves clip not found: {curves_clip_path}"
    )
    assert os.path.exists(cylinder_clip_path), (
        f"Cylinder clip not found: {cylinder_clip_path}"
    )

    curves_bytes = os.path.getsize(curves_clip_path)
    cylinder_bytes = os.path.getsize(cylinder_clip_path)
    ratio = curves_bytes / cylinder_bytes if cylinder_bytes > 0 else float("inf")

    assert curves_bytes < cylinder_bytes, (
        f"Expected curves clip ({curves_bytes:,} bytes) < "
        f"cylinder clip ({cylinder_bytes:,} bytes); ratio={ratio:.4f}"
    )

    print(
        f"  PASS test_clip_size_reduction: "
        f"curves={curves_bytes:,} bytes < cylinder={cylinder_bytes:,} bytes "
        f"(ratio={ratio:.4f})"
    )


def test_curves_demo_trajectory(demo_path: str) -> None:
    """Assert demo stage wires UsdClipsAPI and animates bonds.

    Checks:
    - UsdClipsAPI on /ABLComplex has non-empty clip asset paths
    - Bond-endpoint positions at frame 0 differ from frame 9
      (confirms trajectory clip is actively driving the stage)
    """
    stage = Usd.Stage.Open(demo_path)
    assert stage, f"Failed to open demo stage: {demo_path}"

    abl = stage.GetPrimAtPath("/ABLComplex")
    assert abl.IsValid(), "/ABLComplex not found in demo stage"

    clips_api = Usd.ClipsAPI(abl)
    asset_paths = clips_api.GetClipAssetPaths()
    assert len(asset_paths) > 0, (
        "UsdClipsAPI.GetClipAssetPaths() is empty on /ABLComplex"
    )

    # Sample first bond endpoint position at frame 0 vs frame 9
    bc = UsdGeom.BasisCurves(stage.GetPrimAtPath("/ABLComplex/Bonds"))
    assert bc, "/ABLComplex/Bonds not found in demo stage"

    pts_0 = bc.GetPointsAttr().Get(Usd.TimeCode(0))
    pts_9 = bc.GetPointsAttr().Get(Usd.TimeCode(9))

    assert pts_0 is not None, "points at frame 0 is None"
    assert pts_9 is not None, "points at frame 9 is None"

    # Compare first endpoint position (index 0)
    from pxr import Gf
    p0 = Gf.Vec3f(pts_0[0])
    p9 = Gf.Vec3f(pts_9[0])
    diff = (p0 - p9).GetLength()

    assert diff > 0.0, (
        f"Frame 0 and frame 9 bond positions are identical (diff={diff}); "
        "trajectory clip is not animating the bonds"
    )

    print(
        f"  PASS test_curves_demo_trajectory: "
        f"{len(asset_paths)} clip asset path(s), "
        f"frame0 vs frame9 diff={diff:.4f} Å"
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all(base_dir: str) -> bool:
    """Run all read-back tests. Returns True if all pass."""
    assets_dir = os.path.join(base_dir, "assets", "level4_assemblies")
    clips_dir = os.path.join(base_dir, "output", "clips")
    output_dir = os.path.join(base_dir, "output")

    curves_assembly = os.path.join(assets_dir, "abl_kinase_complex_curves.usda")
    cylinder_assembly = os.path.join(assets_dir, "abl_kinase_complex.usda")
    curves_clip = os.path.join(clips_dir, "trajectory_clip_curves.usda")
    cylinder_clip = os.path.join(clips_dir, "trajectory_clip.usda")
    demo = os.path.join(output_dir, "curves_demo.usda")

    print("=== BasisCurves Bonds Read-back Tests ===\n")

    print("test_curves_assembly_structure")
    test_curves_assembly_structure(curves_assembly)

    print("test_curves_clip_time_samples")
    test_curves_clip_time_samples(curves_clip)

    print("test_assembly_size_reduction")
    test_assembly_size_reduction(curves_assembly, cylinder_assembly)

    print("test_clip_size_reduction")
    test_clip_size_reduction(curves_clip, cylinder_clip)

    print("test_curves_demo_trajectory")
    test_curves_demo_trajectory(demo)

    print("\nPASS: all BasisCurves bonds read-back tests passed")
    return True


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    try:
        run_all(base_dir)
    except AssertionError as e:
        print(f"\nFAIL: {e}")
        sys.exit(1)
