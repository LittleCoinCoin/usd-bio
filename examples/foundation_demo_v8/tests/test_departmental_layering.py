"""
test_departmental_layering.py
==============================
Read-back tests for the 5-layer departmental composition stage.

Opens output/departmental_demo.usda as a cold consumer (no generator code
in scope) and asserts all structural and compositional invariants.

Falsification-resistance: expectations are independently derived from the
leaf spec, not from the generator state — this test would catch a generator
that writes a structurally invalid file.

Usage (from examples/foundation_demo_v8/):
    source ../../load_env.sh
    python3 tests/test_departmental_layering.py
"""

import os
import sys

from pxr import Usd, UsdGeom, Sdf


def _open_stage(stage_path: str) -> Usd.Stage:
    """Open the departmental demo stage as a cold consumer."""
    stage = Usd.Stage.Open(stage_path)
    assert stage, f"Failed to open stage at {stage_path}"
    return stage


# ---------------------------------------------------------------------------
# Individual test functions
# ---------------------------------------------------------------------------

def test_no_composition_errors(stage: Usd.Stage) -> None:
    """Stage must compose cleanly — any error is a build or authoring bug."""
    errors = stage.GetCompositionErrors()
    assert errors == [], f"Expected no composition errors, got: {errors}"
    print("  PASS test_no_composition_errors")


def test_sublayer_count(stage: Usd.Stage) -> None:
    """Root stage must have exactly 5 sublayers — one per department."""
    sublayers = stage.GetRootLayer().subLayerPaths
    assert len(sublayers) == 5, (
        f"Expected 5 sublayers, got {len(sublayers)}: {sublayers}"
    )
    print(f"  PASS test_sublayer_count ({len(sublayers)} sublayers)")


def test_protocol_metadata(stage: Usd.Stage) -> None:
    """Protocol layer must contribute ProtocolMetadata with bio:solventModel."""
    prim = stage.GetPrimAtPath("/ABLComplex/ProtocolMetadata")
    assert prim.IsValid(), (
        "Expected /ABLComplex/ProtocolMetadata to exist (contributed by protocol layer)"
    )
    attr = prim.GetAttribute("bio:solventModel")
    assert attr.IsValid(), (
        "/ABLComplex/ProtocolMetadata must have attribute bio:solventModel"
    )
    value = attr.Get()
    assert value is not None, "bio:solventModel attribute has no value"
    print(f"  PASS test_protocol_metadata (bio:solventModel = '{value}')")


def test_analysis_rmsd(stage: Usd.Stage) -> None:
    """Analysis layer must contribute ≥20 time samples of bio:rmsd on /ABLComplex."""
    abl = stage.GetPrimAtPath("/ABLComplex")
    assert abl.IsValid(), "Expected /ABLComplex prim to exist"

    attr = abl.GetAttribute("bio:rmsd")
    assert attr.IsValid(), (
        "/ABLComplex must have attribute bio:rmsd (contributed by analysis layer)"
    )
    samples = attr.GetTimeSamples()
    assert len(samples) >= 20, (
        f"Expected ≥20 time samples on bio:rmsd, got {len(samples)}: {samples}"
    )
    print(f"  PASS test_analysis_rmsd ({len(samples)} time samples on bio:rmsd)")


def test_review_camera(stage: Usd.Stage) -> None:
    """Review layer must contribute a UsdGeomCamera at /ABLComplex/ReviewCamera."""
    cam_prim = stage.GetPrimAtPath("/ABLComplex/ReviewCamera")
    assert cam_prim.IsValid(), (
        "Expected /ABLComplex/ReviewCamera prim to exist (contributed by review layer)"
    )
    cam = UsdGeom.Camera(cam_prim)
    assert cam, (
        f"/ABLComplex/ReviewCamera must be a valid UsdGeomCamera, "
        f"got type: {cam_prim.GetTypeName()}"
    )
    print(f"  PASS test_review_camera (typeName={cam_prim.GetTypeName()})")


def test_dynamics_clips(stage: Usd.Stage) -> None:
    """Dynamics layer must contribute non-empty clip asset paths on /ABLComplex."""
    abl = stage.GetPrimAtPath("/ABLComplex")
    assert abl.IsValid(), "Expected /ABLComplex prim to exist"

    clips_api = Usd.ClipsAPI(abl)
    asset_paths = clips_api.GetClipAssetPaths()
    assert asset_paths, (
        "UsdClipsAPI.GetClipAssetPaths() must be non-empty (contributed by dynamics layer)"
    )
    print(f"  PASS test_dynamics_clips ({len(asset_paths)} clip asset path(s))")


def test_representation_variantset(stage: Usd.Stage) -> None:
    """Biology layer must contribute a 'representation' VariantSet on /ABLComplex."""
    abl = stage.GetPrimAtPath("/ABLComplex")
    assert abl.IsValid(), "Expected /ABLComplex prim to exist"

    vsets = abl.GetVariantSets()
    names = vsets.GetNames()
    assert "representation" in names, (
        f"Expected 'representation' VariantSet on /ABLComplex, found: {names}"
    )
    print(f"  PASS test_representation_variantset (variantSets={names})")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all(stage_path: str) -> bool:
    """
    Run all read-back tests against stage_path.
    Returns True if all pass; raises AssertionError on first failure.
    """
    print(f"Opening stage: {stage_path}")
    stage = _open_stage(stage_path)
    print()

    test_no_composition_errors(stage)
    test_sublayer_count(stage)
    test_protocol_metadata(stage)
    test_analysis_rmsd(stage)
    test_review_camera(stage)
    test_dynamics_clips(stage)
    test_representation_variantset(stage)

    print()
    print("PASS: all departmental layering read-back tests passed")
    return True


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    stage_path = os.path.join(base_dir, "output", "departmental_demo.usda")

    if not os.path.exists(stage_path):
        print(f"ERROR: stage not found at {stage_path}")
        print("Run demos/departmental_demo.py first to generate the stage.")
        sys.exit(1)

    run_all(stage_path)
    sys.exit(0)
