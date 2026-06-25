#!/usr/bin/env python3
"""
Read-back tests for .usdc binary conversion and clip template wiring.

Opens .usdc artifacts and the clip-template manifest FRESH via Usd.Stage.Open
and asserts compositional equivalence and clip template metadata correctness.

Falsification-resistance contract:
  - All expected values are derived from SOURCE data (prim counts from fresh
    .usda traversal, file sizes from os.path.getsize) — NOT from generator
    in-memory state.
  - Prim count assertion compares usdc vs independently-read usda traversal.
  - Frame position assertion uses two independent TimeCode reads and verifies
    non-zero displacement (not a tautological identity comparison).
  - File size assertions use os.path.getsize at test time.

Usage (from examples/foundation_demo_v8/):
    source load_env.sh
    python3 tests/test_binary_clips.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEMO_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _DEMO_ROOT)

from pxr import Usd, UsdGeom, Gf

# ---------------------------------------------------------------------------
# Artifact paths — all derived from _DEMO_ROOT, never hard-coded absolute paths
# ---------------------------------------------------------------------------
_ASSEMBLY_USDA = os.path.join(_DEMO_ROOT, "assets", "level4_assemblies", "abl_kinase_complex.usda")
_ASSEMBLY_USDC = os.path.join(_DEMO_ROOT, "assets", "level4_assemblies", "abl_kinase_complex.usdc")
_CLIP_USDA = os.path.join(_DEMO_ROOT, "output", "clips", "trajectory_clip.usda")
_CLIP_USDC = os.path.join(_DEMO_ROOT, "output", "clips", "trajectory_clip.usdc")
_CLIP_MANIFEST = os.path.join(_DEMO_ROOT, "output", "clips", "clip_template_manifest.usda")
_BINARY_DEMO = os.path.join(_DEMO_ROOT, "output", "binary_demo.usda")
# Template clip files — dot-separated naming required by USD clipTemplateAssetPath spec
_CLIP_TEMPLATE_001 = os.path.join(_DEMO_ROOT, "output", "clips", "clip.001.usdc")
_CLIP_TEMPLATE_002 = os.path.join(_DEMO_ROOT, "output", "clips", "clip.002.usdc")

# Representative atom prim used across tests
_SAMPLE_ATOM_PATH = "/ABLComplex/Chain_A/ACE_1/HH31"


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    name: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Test 1: usdc assembly prim count parity
# ---------------------------------------------------------------------------

def test_usdc_assembly_prim_count() -> TestResult:
    """Assert .usdc assembly has same prim count as the .usda source.

    Opens both stages independently and compares Traverse() output length.
    The .usda prim count is the independently-derived expectation; the .usdc
    count is what is being verified.
    """
    errors = []
    notes = []

    # Independent expected value: traverse the .usda source
    stage_usda = Usd.Stage.Open(_ASSEMBLY_USDA)
    if stage_usda is None:
        return TestResult("usdc_assembly_prim_count", False,
                          [f"Failed to open .usda source: {_ASSEMBLY_USDA}"])
    usda_prims = list(stage_usda.Traverse())
    expected_count = len(usda_prims)
    notes.append(f"usda prim count (reference): {expected_count}")

    # Value under test: traverse the .usdc
    stage_usdc = Usd.Stage.Open(_ASSEMBLY_USDC)
    if stage_usdc is None:
        return TestResult("usdc_assembly_prim_count", False,
                          [f"Failed to open .usdc: {_ASSEMBLY_USDC}"])
    usdc_prims = list(stage_usdc.Traverse())
    actual_count = len(usdc_prims)
    notes.append(f"usdc prim count (actual): {actual_count}")

    if actual_count != expected_count:
        errors.append(
            f"Prim count mismatch: usda={expected_count}, usdc={actual_count}"
        )
    else:
        notes.append(f"PASS: prim counts match ({actual_count})")

    return TestResult("usdc_assembly_prim_count", len(errors) == 0, errors, notes)


# ---------------------------------------------------------------------------
# Test 2: class prims present in usdc assembly
# ---------------------------------------------------------------------------

def test_usdc_class_prims() -> TestResult:
    """Assert /_class_/C and /_class_/N exist in the .usdc assembly.

    Class prims are abstract and don't appear in Traverse() — uses
    GetPrimAtPath() directly to confirm they are in the layer.
    """
    errors = []
    notes = []

    stage = Usd.Stage.Open(_ASSEMBLY_USDC)
    if stage is None:
        return TestResult("usdc_class_prims", False,
                          [f"Failed to open: {_ASSEMBLY_USDC}"])

    for class_path in ("/_class_/C", "/_class_/N"):
        prim = stage.GetPrimAtPath(class_path)
        if not prim.IsValid():
            errors.append(f"Class prim not found: {class_path}")
        else:
            notes.append(f"PASS: {class_path} present")

    return TestResult("usdc_class_prims", len(errors) == 0, errors, notes)


# ---------------------------------------------------------------------------
# Test 3: clip template manifest wiring
# ---------------------------------------------------------------------------

def test_clip_template_manifest() -> TestResult:
    """Assert UsdClipsAPI.GetClipTemplateAssetPath() returns non-empty string.

    Opens clip_template_manifest.usda and reads the template metadata on
    /ABLComplex. Verifies:
      - Stage opens successfully
      - /ABLComplex prim exists
      - GetClipTemplateAssetPath() returns a non-empty string
    """
    errors = []
    notes = []

    stage = Usd.Stage.Open(_CLIP_MANIFEST)
    if stage is None:
        return TestResult("clip_template_manifest", False,
                          [f"Failed to open: {_CLIP_MANIFEST}"])

    prim = stage.GetPrimAtPath("/ABLComplex")
    if not prim.IsValid():
        return TestResult("clip_template_manifest", False,
                          ["/ABLComplex prim not found in manifest"])

    clips_api = Usd.ClipsAPI(prim)
    template_path = clips_api.GetClipTemplateAssetPath()
    notes.append(f"GetClipTemplateAssetPath() returned: {repr(template_path)}")

    if not template_path:
        errors.append("GetClipTemplateAssetPath() returned empty string")
    else:
        notes.append(f"PASS: template path = {template_path!r}")

    # Also verify stride and start time are non-zero/sensible
    stride = clips_api.GetClipTemplateStride()
    start = clips_api.GetClipTemplateStartTime()
    notes.append(f"templateStride={stride}, templateStartTime={start}")
    if stride <= 0:
        errors.append(f"clipTemplateStride should be > 0, got {stride}")

    return TestResult("clip_template_manifest", len(errors) == 0, errors, notes)


# ---------------------------------------------------------------------------
# Test 3b: clip.001.usdc and clip.002.usdc contain populated time-sampled data
# ---------------------------------------------------------------------------

def test_template_clip_files_have_time_samples() -> TestResult:
    """Assert clip.001.usdc and clip.002.usdc each contain real time-sampled positions.

    Opens each .usdc clip file FRESH via Usd.Stage.Open (independent reads) and
    asserts:
      - Stage opens successfully
      - Sample atom /ABLComplex/Chain_A/ACE_1/HH31 is present
      - xformOp:translate has a non-empty GetTimeSamples() list (real data, not manifest)
      - The first and last frame positions DIFFER (animation is not a constant value)

    These clip files were previously unread by any test. This closes the gap.
    """
    errors = []
    notes = []

    for clip_path, label in [(_CLIP_TEMPLATE_001, "clip.001.usdc"),
                              (_CLIP_TEMPLATE_002, "clip.002.usdc")]:
        if not os.path.isfile(clip_path):
            errors.append(f"Missing template clip file: {clip_path}")
            continue

        stage = Usd.Stage.Open(clip_path)
        if stage is None:
            errors.append(f"Failed to open: {clip_path}")
            continue

        prim = stage.GetPrimAtPath(_SAMPLE_ATOM_PATH)
        if not prim.IsValid():
            errors.append(f"{label}: sample atom not found: {_SAMPLE_ATOM_PATH}")
            continue

        xf = UsdGeom.Xformable(prim)
        ops = xf.GetOrderedXformOps()
        if not ops:
            errors.append(f"{label}: no xform ops on sample atom")
            continue

        translate_op = ops[0]
        time_samples = translate_op.GetTimeSamples()
        notes.append(f"{label}: time samples count = {len(time_samples)}")

        if len(time_samples) < 2:
            errors.append(
                f"{label}: expected >= 2 time samples, got {len(time_samples)}"
            )
            continue

        # First and last frame positions must differ (data is live, not constant)
        pos_first = translate_op.Get(Usd.TimeCode(time_samples[0]))
        pos_last = translate_op.Get(Usd.TimeCode(time_samples[-1]))
        notes.append(f"{label}: pos[first] = {pos_first}")
        notes.append(f"{label}: pos[last]  = {pos_last}")

        displacement = (Gf.Vec3d(pos_first) - Gf.Vec3d(pos_last)).GetLength()
        notes.append(f"{label}: first-to-last displacement = {displacement:.4f} Å")

        if displacement < 0.01:
            errors.append(
                f"{label}: first and last frame positions are too similar "
                f"(displacement={displacement:.4f} Å); data may be constant"
            )
        else:
            notes.append(f"PASS: {label} has live time-sampled data (disp={displacement:.4f} Å)")

    return TestResult("template_clip_files_have_time_samples",
                      len(errors) == 0, errors, notes)


# ---------------------------------------------------------------------------
# Test 3c: clip-template manifest resolves LIVE, DIFFERING values via clips
# ---------------------------------------------------------------------------

def test_clip_template_resolves_live_data() -> TestResult:
    """Assert the clip-template manifest delivers live clip values via UsdClipsAPI.

    This test constructs a minimal composed stage that sublayers:
      1. clip_template_manifest.usda  (provides clipTemplateAssetPath metadata on /ABLComplex)
      2. abl_kinase_complex.usda      (provides the atom prim hierarchy)

    It then samples xformOp:translate on the sample atom at two stage timecodes
    derived from GetTimeSamples() on the composed attribute (the USD clip system
    exposes the underlying clip frame times translated to stage time) and asserts:
      - GetTimeSamples() returns >= 2 timecodes (clip system is active)
      - ResolveInfoSource is ValueClips (not Default, not TimeSamples)
      - Values at both timecodes are populated (non-None)
      - Values at the two timecodes DIFFER (proves template drives live clip data,
        not a constant fallback)

    WHY in-test composition instead of opening the manifest directly: the manifest
    only carries the template metadata on /ABLComplex; it does not define the atom
    prim hierarchy. A consumer stage must supply the topology (via subLayer of the
    assembly) for the clip values to bind to attributes. This mirrors the real usage
    pattern and is documented here for clarity.
    """
    errors = []
    notes = []

    _ASSEMBLY_USDA_PATH = os.path.join(
        _DEMO_ROOT, "assets", "level4_assemblies", "abl_kinase_complex.usda"
    )

    if not os.path.isfile(_CLIP_MANIFEST):
        return TestResult("clip_template_resolves_live_data", False,
                          [f"Missing manifest: {_CLIP_MANIFEST}"])
    if not os.path.isfile(_ASSEMBLY_USDA_PATH):
        return TestResult("clip_template_resolves_live_data", False,
                          [f"Missing assembly: {_ASSEMBLY_USDA_PATH}"])

    # Build the composed consumer stage in memory.
    # subLayerPaths order: manifest is stronger (overrides assembly defaults).
    composed = Usd.Stage.CreateInMemory()
    composed.GetRootLayer().subLayerPaths = [_CLIP_MANIFEST, _ASSEMBLY_USDA_PATH]

    comp_errors = composed.GetCompositionErrors()
    if comp_errors:
        errors.append(f"Composition errors: {comp_errors}")
        return TestResult("clip_template_resolves_live_data", False, errors, notes)

    # Verify template metadata is present on /ABLComplex
    abl_prim = composed.GetPrimAtPath("/ABLComplex")
    if not abl_prim.IsValid():
        return TestResult("clip_template_resolves_live_data", False,
                          ["/ABLComplex not found in composed stage"])

    clips_api = Usd.ClipsAPI(abl_prim)
    template_path = clips_api.GetClipTemplateAssetPath()
    notes.append(f"templateAssetPath on composed /ABLComplex: {template_path!r}")
    computed_paths = clips_api.ComputeClipAssetPaths()
    notes.append(
        f"ComputeClipAssetPaths: {[os.path.basename(p.resolvedPath) for p in computed_paths]}"
    )

    if len(computed_paths) < 2:
        errors.append(
            f"Template resolved {len(computed_paths)} clip(s), expected >= 2. "
            f"ComputeClipAssetPaths returned: {computed_paths}"
        )
        return TestResult("clip_template_resolves_live_data", False, errors, notes)

    # Sample the atom at t=1 (clip.001) and t=2 (clip.002)
    prim = composed.GetPrimAtPath(_SAMPLE_ATOM_PATH)
    if not prim.IsValid():
        return TestResult("clip_template_resolves_live_data", False,
                          [f"Sample atom not found: {_SAMPLE_ATOM_PATH}"])

    xf = UsdGeom.Xformable(prim)
    ops = xf.GetOrderedXformOps()
    if not ops:
        return TestResult("clip_template_resolves_live_data", False,
                          ["No xform ops on sample atom in composed stage"])

    translate_op = ops[0]

    # Verify value source is ValueClips (not Default fallback) at the first
    # reported clip time sample.
    # Implementation note: USD clip template time mapping is "stage_time = local_clip_time"
    # (absolute, not relative to startTime) within each clip's active window.
    # The clip system reports the underlying clip time samples translated to stage time;
    # these are the timecodes at which the clip data is directly sampled (no hold).
    clip_time_samples = translate_op.GetTimeSamples()
    notes.append(f"GetTimeSamples on composed attr: {clip_time_samples}")

    if len(clip_time_samples) < 2:
        errors.append(
            f"Expected >= 2 time samples from the clip system on the composed stage, "
            f"got {len(clip_time_samples)}. "
            f"The clip template may not be resolving correctly."
        )
        return TestResult("clip_template_resolves_live_data",
                          len(errors) == 0, errors, notes)

    tc_a = clip_time_samples[0]
    tc_b = clip_time_samples[-1]

    # Confirm both timecodes resolve via ValueClips (not Default)
    for tc_val in [tc_a, tc_b]:
        ri = translate_op.GetAttr().GetResolveInfo(Usd.TimeCode(tc_val))
        source = ri.GetSource()
        notes.append(f"ResolveInfoSource @ t={tc_val}: {source}")
        if source != Usd.ResolveInfoSourceValueClips:
            errors.append(
                f"Expected ResolveInfoSourceValueClips at t={tc_val}, got {source}. "
                f"The clip template is not resolving — check templateAssetPath format "
                f"(must be 'basename.###.ext', dot-separated hash group)."
            )

    # Sample at the two clip time-sample boundaries and assert values differ.
    # These two timecodes map to time samples from clip.001 and clip.002 respectively
    # (the template stride places clip.001 at lower stage times, clip.002 at higher).
    pos_a = translate_op.Get(Usd.TimeCode(tc_a))
    pos_b = translate_op.Get(Usd.TimeCode(tc_b))
    notes.append(f"pos @ t={tc_a} (early clip): {pos_a}")
    notes.append(f"pos @ t={tc_b} (late clip):  {pos_b}")

    if pos_a is None:
        errors.append(f"Resolved value is None at t={tc_a}")
    if pos_b is None:
        errors.append(f"Resolved value is None at t={tc_b}")

    if pos_a is not None and pos_b is not None:
        displacement = (Gf.Vec3d(pos_a) - Gf.Vec3d(pos_b)).GetLength()
        notes.append(f"Displacement t={tc_a} vs t={tc_b}: {displacement:.4f} Å")

        # Values must differ: the two timecodes address different frames from the clips.
        # If the template were falling back to a constant default, both would be identical.
        if displacement < 0.01:
            errors.append(
                f"Positions at t={tc_a} and t={tc_b} are too similar "
                f"(disp={displacement:.4f} Å). "
                f"The template may be resolving a constant fallback."
            )
        else:
            notes.append(
                f"PASS: values differ by {displacement:.4f} Å between clip time samples "
                f"(t={tc_a} vs t={tc_b}) — template drives live clip data"
            )

    return TestResult("clip_template_resolves_live_data",
                      len(errors) == 0, errors, notes)


# ---------------------------------------------------------------------------
# Test 4: binary_demo trajectory — frame 0 vs frame 9 positions differ
# ---------------------------------------------------------------------------

def test_binary_demo_trajectory() -> TestResult:
    """Assert frame 0 and frame 9 positions differ on /ABLComplex/Chain_A/ACE_1/HH31.

    Opens binary_demo.usda (which SubLayers .usdc files) fresh and reads
    xformOp:translate at the first and last available time sample in
    the range 0..9. The two reads are independent; non-zero displacement
    confirms the clip data is live.
    """
    errors = []
    notes = []

    stage = Usd.Stage.Open(_BINARY_DEMO)
    if stage is None:
        return TestResult("binary_demo_trajectory", False,
                          [f"Failed to open: {_BINARY_DEMO}"])

    prim = stage.GetPrimAtPath(_SAMPLE_ATOM_PATH)
    if not prim.IsValid():
        return TestResult("binary_demo_trajectory", False,
                          [f"Prim not found: {_SAMPLE_ATOM_PATH}"])

    xf = UsdGeom.Xformable(prim)
    ops = xf.GetOrderedXformOps()
    if not ops:
        return TestResult("binary_demo_trajectory", False,
                          ["No xform ops on sample atom"])

    translate_op = ops[0]
    time_samples = translate_op.GetTimeSamples()
    notes.append(f"Time samples count: {len(time_samples)}")

    if len(time_samples) < 2:
        errors.append(f"Expected >= 2 time samples, got {len(time_samples)}")
        return TestResult("binary_demo_trajectory", False, errors, notes)

    # Frame 0: first available time sample
    tc0 = Usd.TimeCode(time_samples[0])
    # Frame 9: 10th time sample (index 9), or last if fewer than 10
    idx9 = min(9, len(time_samples) - 1)
    tc9 = Usd.TimeCode(time_samples[idx9])

    pos0 = translate_op.Get(tc0)
    pos9 = translate_op.Get(tc9)
    notes.append(f"pos @ t={time_samples[0]:.3f}: {pos0}")
    notes.append(f"pos @ t={time_samples[idx9]:.3f}: {pos9}")

    # Independently verify displacement is non-zero
    displacement = (Gf.Vec3d(pos0) - Gf.Vec3d(pos9)).GetLength()
    notes.append(f"Displacement frame0 vs frame9: {displacement:.4f} Å")

    # Threshold: positions must differ by at least 0.01 Å (detector sensitivity)
    if displacement < 0.01:
        errors.append(
            f"Frame 0 and frame 9 positions are too similar: displacement={displacement:.4f} Å"
        )
    else:
        notes.append(f"PASS: positions differ by {displacement:.4f} Å")

    return TestResult("binary_demo_trajectory", len(errors) == 0, errors, notes)


# ---------------------------------------------------------------------------
# Test 5: .usdc file sizes are smaller than .usda counterparts
# ---------------------------------------------------------------------------

def test_file_sizes() -> TestResult:
    """Assert .usdc files are smaller than their .usda counterparts.

    Uses os.path.getsize at test time — sizes are independently read from
    disk, not cached from generation. Checks:
      - trajectory_clip.usdc < trajectory_clip.usda
      - abl_kinase_complex.usdc < abl_kinase_complex.usda
    """
    errors = []
    notes = []

    pairs = [
        (_CLIP_USDA, _CLIP_USDC, "trajectory_clip"),
        (_ASSEMBLY_USDA, _ASSEMBLY_USDC, "abl_kinase_complex"),
    ]

    for usda_path, usdc_path, label in pairs:
        if not os.path.isfile(usda_path):
            errors.append(f"Missing .usda: {usda_path}")
            continue
        if not os.path.isfile(usdc_path):
            errors.append(f"Missing .usdc: {usdc_path}")
            continue

        usda_bytes = os.path.getsize(usda_path)
        usdc_bytes = os.path.getsize(usdc_path)
        ratio = usdc_bytes / usda_bytes if usda_bytes > 0 else float("inf")
        notes.append(
            f"{label}: usda={usda_bytes:,} bytes, usdc={usdc_bytes:,} bytes, "
            f"ratio={ratio:.4f}"
        )

        if usdc_bytes >= usda_bytes:
            errors.append(
                f"{label}: .usdc ({usdc_bytes:,}) is NOT smaller than .usda ({usda_bytes:,})"
            )
        else:
            notes.append(f"PASS: {label} usdc < usda (ratio={ratio:.4f})")

    return TestResult("file_sizes", len(errors) == 0, errors, notes)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def _run_all() -> bool:
    """Run all tests and print results. Returns True if all pass."""
    tests = [
        test_usdc_assembly_prim_count,
        test_usdc_class_prims,
        test_clip_template_manifest,
        test_template_clip_files_have_time_samples,
        test_clip_template_resolves_live_data,
        test_binary_demo_trajectory,
        test_file_sizes,
    ]

    all_passed = True
    print()
    print("=" * 70)
    print("test_binary_clips — read-back tests for .usdc conversion + clip template")
    print("=" * 70)

    for test_fn in tests:
        result = test_fn()
        status = "PASS" if result.passed else "FAIL"
        print(f"\n[{status}] {result.name}")
        for note in result.notes:
            print(f"  {note}")
        if not result.passed:
            for err in result.errors:
                print(f"  ERROR: {err}")
            all_passed = False

    print()
    print("=" * 70)
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 70)
    print()

    return all_passed


if __name__ == "__main__":
    passed = _run_all()
    sys.exit(0 if passed else 1)
