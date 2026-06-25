"""test_analysis_attributes.py — Step 3 of analysis_attributes leaf.

Read-back tests for time-sampled bio: analysis attributes in analysis_layer.usda.
Opens the stage FRESH (no generator state in scope) and asserts each attribute
returns non-default values that vary across time, plus held-last-value boundary
behavior at time codes beyond the authored range.

[source: examples/composition_advanced/analysis_attributes/analysis_layer.usda]
[source: __roadmap__/v8-gap-closure/gap_closure/composition_advanced/analysis_attributes.md — Step 3]

Attribute placement:
  - bio:rmsd  (float, Å)        on /ABLComplex
    10 time samples, frames 0..9, linear ramp 1.2→3.8 Å
    Generated values: 1.2 + 2.6 * i / 9.0 for i in 0..9
    At t=0: 1.2, t=4: ~2.3556, t=9: 3.8

  - bio:pmf   (float, kcal/mol) on /ABLComplex/Analysis/PMFProfile
    21 time samples, bins 0..20, Gaussian well centered at bin 10
    f(b) = 8.0 * ((b - 10) / 10.0)^2
    At t=0: 8.0, t=10: 0.0, t=20: 8.0

  - bio:contactCount (int)       on /ABLComplex/Chain_A/Lig_ATP
    10 time samples, frames 0..9
    Values: 12, 11, 13, 10, 14, 11, 12, 9, 13, 12
    At t=0: 12, t=7: 9

Boundary behavior (USD held interpolation):
  Sampling beyond the last authored time returns the last sample value.
  [source: context7 /websites/openusd_release — UsdInterpolationTypeHeld]

Usage (from repo root):
    . ./load_env.sh
    /path/to/forOUSD/bin/python3 tests/composition_advanced/test_analysis_attributes.py
"""

import math
import os
import sys

from pxr import Usd, UsdGeom

# ---------------------------------------------------------------------------
# Locate the USDA output — path relative to repo root
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_STAGE_PATH = os.path.join(
    _REPO_ROOT,
    "examples", "composition_advanced", "analysis_attributes", "analysis_layer.usda",
)

# Tolerance for float comparisons (Å and kcal/mol)
_TOL = 0.01


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open_fresh_stage() -> Usd.Stage:
    """Open analysis_layer.usda with a fresh, isolated stage (no shared state)."""
    assert os.path.isfile(_STAGE_PATH), f"Stage not found: {_STAGE_PATH}"
    stage = Usd.Stage.Open(_STAGE_PATH)
    errors = stage.GetCompositionErrors()
    assert not errors, f"Composition errors: {errors}"
    return stage


def _get_attr(stage: Usd.Stage, prim_path: str, attr_name: str) -> Usd.Attribute:
    """Retrieve a named attribute from the given prim path; assert it exists."""
    prim = stage.GetPrimAtPath(prim_path)
    assert prim.IsValid(), f"Prim not found: {prim_path}"
    attr = prim.GetAttribute(attr_name)
    assert attr.IsValid(), f"Attribute not found: {prim_path}.{attr_name}"
    return attr


# ---------------------------------------------------------------------------
# Test 1: bio:rmsd time samples on /ABLComplex
# ---------------------------------------------------------------------------

def test_rmsd_time_samples() -> None:
    """bio:rmsd on /ABLComplex must return non-default, time-varying values."""
    stage = _open_fresh_stage()
    attr = _get_attr(stage, "/ABLComplex", "bio:rmsd")

    # Must have 10 authored time samples
    ts = attr.GetTimeSamples()
    assert len(ts) == 10, f"Expected 10 time samples for bio:rmsd, got {len(ts)}"

    # Sample at t=0: expect 1.2 Å (ramp start)
    val0 = attr.Get(Usd.TimeCode(0))
    assert val0 is not None, "bio:rmsd returned None at t=0"
    assert abs(val0 - 1.2) <= _TOL, f"bio:rmsd@0 expected ~1.2, got {val0}"

    # Sample at t=4: expect 1.2 + 2.6 * 4/9 = ~2.3556 Å (mid-ramp)
    expected_t4 = 1.2 + 2.6 * 4.0 / 9.0  # ≈ 2.3556
    val4 = attr.Get(Usd.TimeCode(4))
    assert val4 is not None, "bio:rmsd returned None at t=4"
    assert abs(val4 - expected_t4) <= _TOL, (
        f"bio:rmsd@4 expected ~{expected_t4:.4f}, got {val4}"
    )

    # Sample at t=9: expect 3.8 Å (ramp end)
    val9 = attr.Get(Usd.TimeCode(9))
    assert val9 is not None, "bio:rmsd returned None at t=9"
    assert abs(val9 - 3.8) <= _TOL, f"bio:rmsd@9 expected ~3.8, got {val9}"

    # Values must vary: t=0 < t=4 < t=9 (monotone ramp)
    assert val0 < val4 < val9, (
        f"bio:rmsd must increase monotonically: {val0} < {val4} < {val9}"
    )

    print(f"  PASS: bio:rmsd — @0={val0:.4f}, @4={val4:.4f}, @9={val9:.4f} Å")


# ---------------------------------------------------------------------------
# Test 2: bio:pmf time samples on /ABLComplex/Analysis/PMFProfile
# ---------------------------------------------------------------------------

def test_pmf_time_samples() -> None:
    """bio:pmf on /ABLComplex/Analysis/PMFProfile must reflect a Gaussian well."""
    stage = _open_fresh_stage()
    attr = _get_attr(stage, "/ABLComplex/Analysis/PMFProfile", "bio:pmf")

    # Must have 21 authored time samples (bins 0..20)
    ts = attr.GetTimeSamples()
    assert len(ts) == 21, f"Expected 21 time samples for bio:pmf, got {len(ts)}"

    # Sample at t=10 (well minimum): expect ~0.0 kcal/mol
    val10 = attr.Get(Usd.TimeCode(10))
    assert val10 is not None, "bio:pmf returned None at t=10"
    assert abs(val10 - 0.0) <= _TOL, f"bio:pmf@10 expected ~0.0, got {val10}"

    # Sample at t=0 (left flank): expect ~8.0 kcal/mol
    val0 = attr.Get(Usd.TimeCode(0))
    assert val0 is not None, "bio:pmf returned None at t=0"
    assert abs(val0 - 8.0) <= _TOL, f"bio:pmf@0 expected ~8.0, got {val0}"

    # Sample at t=20 (right flank): expect ~8.0 kcal/mol (symmetric well)
    val20 = attr.Get(Usd.TimeCode(20))
    assert val20 is not None, "bio:pmf returned None at t=20"
    assert abs(val20 - 8.0) <= _TOL, f"bio:pmf@20 expected ~8.0, got {val20}"

    # Well minimum must be strictly less than flanks
    assert val10 < val0, (
        f"bio:pmf well minimum at t=10 ({val10}) must be less than flank at t=0 ({val0})"
    )
    assert val10 < val20, (
        f"bio:pmf well minimum at t=10 ({val10}) must be less than flank at t=20 ({val20})"
    )

    # Values must be non-negative (PMF ≥ 0 for this sentinel)
    for t in [0, 5, 10, 15, 20]:
        v = attr.Get(Usd.TimeCode(t))
        assert v >= 0.0, f"bio:pmf@{t} must be non-negative, got {v}"

    print(f"  PASS: bio:pmf — @0={val0:.4f}, @10={val10:.4f}, @20={val20:.4f} kcal/mol")


# ---------------------------------------------------------------------------
# Test 3: bio:contactCount time samples on /ABLComplex/Chain_A/Lig_ATP
# ---------------------------------------------------------------------------

def test_contact_count_time_samples() -> None:
    """bio:contactCount on /ABLComplex/Chain_A/Lig_ATP must return integer time series."""
    stage = _open_fresh_stage()
    attr = _get_attr(stage, "/ABLComplex/Chain_A/Lig_ATP", "bio:contactCount")

    # Must have 10 authored time samples (frames 0..9)
    ts = attr.GetTimeSamples()
    assert len(ts) == 10, f"Expected 10 time samples for bio:contactCount, got {len(ts)}"

    # Full expected sequence
    expected = [12, 11, 13, 10, 14, 11, 12, 9, 13, 12]

    # Sample at t=0: expect 12
    val0 = attr.Get(Usd.TimeCode(0))
    assert val0 is not None, "bio:contactCount returned None at t=0"
    assert val0 == expected[0], f"bio:contactCount@0 expected {expected[0]}, got {val0}"

    # Sample at t=7: expect 9
    val7 = attr.Get(Usd.TimeCode(7))
    assert val7 is not None, "bio:contactCount returned None at t=7"
    assert val7 == expected[7], f"bio:contactCount@7 expected {expected[7]}, got {val7}"

    # Verify the full sequence across all 10 frames
    for i, exp_val in enumerate(expected):
        v = attr.Get(Usd.TimeCode(i))
        assert v == exp_val, (
            f"bio:contactCount@{i} expected {exp_val}, got {v}"
        )

    # Values must vary (not all identical)
    all_vals = [attr.Get(Usd.TimeCode(i)) for i in range(10)]
    assert len(set(all_vals)) > 1, "bio:contactCount values must vary across time"

    print(f"  PASS: bio:contactCount — @0={val0}, @7={val7}; full series={all_vals}")


# ---------------------------------------------------------------------------
# Test 4: held-last-value boundary behavior
# ---------------------------------------------------------------------------

def test_boundary_time_code_behavior() -> None:
    """Sampling beyond the authored range returns the held last value.

    USD uses UsdInterpolationTypeHeld by default for custom attributes —
    the last authored sample is held at any time code greater than the
    final sample time.
    [source: context7 /websites/openusd_release — UsdInterpolationTypeHeld]
    """
    stage = _open_fresh_stage()

    # bio:rmsd: last sample at t=9 (value=3.8). Query at t=50 — must return 3.8.
    rmsd_attr = _get_attr(stage, "/ABLComplex", "bio:rmsd")
    val_beyond = rmsd_attr.Get(Usd.TimeCode(50))
    assert val_beyond is not None, "bio:rmsd returned None at t=50 (beyond range)"
    assert abs(val_beyond - 3.8) <= _TOL, (
        f"bio:rmsd@50 (beyond authored range) expected held last value ~3.8, got {val_beyond}"
    )

    # bio:contactCount: last sample at t=9 (value=12). Query at t=100 — must return 12.
    cc_attr = _get_attr(stage, "/ABLComplex/Chain_A/Lig_ATP", "bio:contactCount")
    cc_beyond = cc_attr.Get(Usd.TimeCode(100))
    assert cc_beyond is not None, "bio:contactCount returned None at t=100 (beyond range)"
    assert cc_beyond == 12, (
        f"bio:contactCount@100 (beyond authored range) expected held last value 12, got {cc_beyond}"
    )

    # bio:pmf: last sample at t=20 (value=8.0). Query at t=99 — must return 8.0.
    pmf_attr = _get_attr(stage, "/ABLComplex/Analysis/PMFProfile", "bio:pmf")
    pmf_beyond = pmf_attr.Get(Usd.TimeCode(99))
    assert pmf_beyond is not None, "bio:pmf returned None at t=99 (beyond range)"
    assert abs(pmf_beyond - 8.0) <= _TOL, (
        f"bio:pmf@99 (beyond authored range) expected held last value ~8.0, got {pmf_beyond}"
    )

    print(
        f"  PASS: boundary held-last-value — "
        f"rmsd@50={val_beyond:.4f}, contactCount@100={cc_beyond}, pmf@99={pmf_beyond:.4f}"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_rmsd_time_samples,
        test_pmf_time_samples,
        test_contact_count_time_samples,
        test_boundary_time_code_behavior,
    ]
    passed = 0
    failed = 0
    for fn in tests:
        print(f"Running {fn.__name__} ...")
        try:
            fn()
            passed += 1
        except AssertionError as exc:
            print(f"  FAIL: {exc}")
            failed += 1
        except Exception as exc:
            print(f"  ERROR: {type(exc).__name__}: {exc}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
    print("All tests PASSED.")
