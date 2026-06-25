"""test_ensemble_payload.py — Step 3 of Exp 4 (ensemble_payload).

Read-back tests for ensemble_assembly.usda: opens the stage fresh (no
generator state in scope), switches ReplicaID variants, loads the payload,
and asserts the composed sentinel points value per replica.

Falsification-resistance: the crux assertion is that switching variants
CHANGES the resolved sentinel value — proving payload swapping operates at
the composition level, not just at authoring time. If the value does not
change when the variant changes, that is a real failure.

API confirmed via context7 /websites/openusd_release:
  - Usd.Stage.Open(path, Usd.Stage.LoadNone) — open with payloads unloaded
  - prim.GetVariantSet("ReplicaID").SetVariantSelection(rep)
  - stage.Load(SdfPath) — load payload for current variant selection
  - attr.Get(time) — sample the composed attribute

Usage (from repo root):
    . ./load_env.sh
    /path/to/forOUSD/bin/python3 tests/composition_advanced/test_ensemble_payload.py
"""

import os
import sys

from pxr import Gf, Sdf, Usd, UsdGeom

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ASSEMBLY = os.path.join(
    _REPO_ROOT,
    "examples", "composition_advanced", "ensemble_payload", "ensemble_assembly.usda"
)
_ENSEMBLE_PATH = Sdf.Path("/ABLEnsemble")
_POINTS_PATH = "/ABLEnsemble/Chain_A/Res_001/Atom_CA"
_ATTR_NAME = "points"
_TIME = 1.0

# Sentinel values authored in Step 1 clip stubs
SENTINELS = {
    "rep_01": Gf.Vec3f(1.0, 0.0, 0.0),
    "rep_02": Gf.Vec3f(2.0, 0.0, 0.0),
    "rep_03": Gf.Vec3f(3.0, 0.0, 0.0),
}


def _open_stage_no_payloads() -> Usd.Stage:
    """Open the assembly stage with payloads unloaded (cold consumer)."""
    assert os.path.exists(_ASSEMBLY), (
        f"ensemble_assembly.usda not found at {_ASSEMBLY} — run build_ensemble.py first"
    )
    stage = Usd.Stage.Open(_ASSEMBLY, Usd.Stage.LoadNone)
    assert stage, f"Failed to open stage at {_ASSEMBLY}"
    return stage


# ---------------------------------------------------------------------------
# Individual test functions
# ---------------------------------------------------------------------------

def test_no_composition_errors() -> None:
    """Stage must compose cleanly with no errors (payloads unloaded)."""
    stage = _open_stage_no_payloads()
    errors = stage.GetCompositionErrors()
    assert errors == [], f"Expected no composition errors, got: {errors}"
    print("  PASS test_no_composition_errors")


def test_ensemble_prim_exists() -> None:
    """'/ABLEnsemble' must exist as a valid Xform prim."""
    stage = _open_stage_no_payloads()
    prim = stage.GetPrimAtPath(_ENSEMBLE_PATH)
    assert prim.IsValid(), f"Expected /ABLEnsemble to be a valid prim"
    assert prim.IsA(UsdGeom.Xform), f"/ABLEnsemble must be typed as Xform"
    print("  PASS test_ensemble_prim_exists")


def test_replicaid_variantset_has_three_variants() -> None:
    """ReplicaID VariantSet must have exactly 3 variants: rep_01, rep_02, rep_03."""
    stage = _open_stage_no_payloads()
    prim = stage.GetPrimAtPath(_ENSEMBLE_PATH)
    vset = prim.GetVariantSet("ReplicaID")
    assert vset, "Expected ReplicaID VariantSet to exist on /ABLEnsemble"
    variants = vset.GetVariantNames()
    assert set(variants) == {"rep_01", "rep_02", "rep_03"}, (
        f"Expected variants {{rep_01, rep_02, rep_03}}, got {set(variants)}"
    )
    print(f"  PASS test_replicaid_variantset_has_three_variants (variants={variants})")


def test_default_variant_is_rep_01() -> None:
    """Default variant selection must be rep_01 (as authored in build_ensemble.py)."""
    stage = _open_stage_no_payloads()
    prim = stage.GetPrimAtPath(_ENSEMBLE_PATH)
    vset = prim.GetVariantSet("ReplicaID")
    selection = vset.GetVariantSelection()
    assert selection == "rep_01", (
        f"Expected default variant 'rep_01', got '{selection}'"
    )
    print(f"  PASS test_default_variant_is_rep_01 (selection='{selection}')")


def test_variant_swaps_payload_path() -> None:
    """Switching variants must change which payload asset is active.

    Confirmed via UsdPrimCompositionQuery that each variant's payload arc
    points to a distinct asset. Here we confirm indirectly by checking that
    the resolved child namespace (contributed by the payload) is accessible
    after load and changes per variant.
    """
    stage = _open_stage_no_payloads()
    prim = stage.GetPrimAtPath(_ENSEMBLE_PATH)
    vset = prim.GetVariantSet("ReplicaID")

    resolved_values = {}
    for rep in ("rep_01", "rep_02", "rep_03"):
        # Switch variant on the SAME fresh-opened stage
        vset.SetVariantSelection(rep)
        # Load the payload for this variant
        stage.Load(_ENSEMBLE_PATH)
        atom_prim = stage.GetPrimAtPath(_POINTS_PATH)
        assert atom_prim.IsValid(), (
            f"After loading payload for {rep}, expected {_POINTS_PATH} to exist"
        )
        attr = atom_prim.GetAttribute(_ATTR_NAME)
        assert attr.IsValid(), (
            f"Expected 'points' attribute at {_POINTS_PATH} after loading {rep}"
        )
        val = attr.Get(_TIME)
        assert val is not None, (
            f"Expected non-None 'points' value at t={_TIME} for {rep}"
        )
        resolved_values[rep] = val

    # All three resolved values must be distinct — proving variant switching
    # swaps the payload at composition level
    all_vals = list(resolved_values.values())
    for i in range(len(all_vals)):
        for j in range(i + 1, len(all_vals)):
            assert all_vals[i] != all_vals[j], (
                f"Variants produced identical resolved values: {resolved_values} — "
                "payload swapping is NOT working at composition level"
            )
    print(
        f"  PASS test_variant_swaps_payload_path "
        f"(all 3 variants resolved to distinct values: "
        f"rep_01={resolved_values['rep_01']}, "
        f"rep_02={resolved_values['rep_02']}, "
        f"rep_03={resolved_values['rep_03']})"
    )


def test_sentinel_positions_per_replica() -> None:
    """Each replica variant must resolve its exact sentinel (1,0,0)/(2,0,0)/(3,0,0).

    This is the crux falsification test: reads the composed value through the
    loaded payload, NOT from any build-time constant.
    [source: examples/composition_advanced/ensemble_payload/clips/rep_0N.usda —
     each clip stub authors a distinct sentinel in point3f[] points.timeSamples]
    """
    stage = _open_stage_no_payloads()
    prim = stage.GetPrimAtPath(_ENSEMBLE_PATH)
    vset = prim.GetVariantSet("ReplicaID")

    for rep, expected_vec in SENTINELS.items():
        vset.SetVariantSelection(rep)
        stage.Load(_ENSEMBLE_PATH)
        atom_prim = stage.GetPrimAtPath(_POINTS_PATH)
        assert atom_prim.IsValid(), (
            f"[{rep}] Expected {_POINTS_PATH} to be valid after payload load"
        )
        attr = atom_prim.GetAttribute(_ATTR_NAME)
        val = attr.Get(_TIME)
        assert val is not None, f"[{rep}] points attribute returned None at t={_TIME}"
        # val is a Vt.Vec3fArray with one element
        assert len(val) == 1, f"[{rep}] Expected 1 point, got {len(val)}: {val}"
        got_vec = val[0]
        assert got_vec == expected_vec, (
            f"[{rep}] Sentinel mismatch: expected {expected_vec}, got {got_vec}. "
            "Payload swapping did not deliver the expected composition result."
        )
        print(
            f"  PASS [{rep}] sentinel=({got_vec[0]:.0f},{got_vec[1]:.0f},{got_vec[2]:.0f}) "
            f"== expected=({expected_vec[0]:.0f},{expected_vec[1]:.0f},{expected_vec[2]:.0f})"
        )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all() -> None:
    """Run all test functions and report results."""
    tests = [
        test_no_composition_errors,
        test_ensemble_prim_exists,
        test_replicaid_variantset_has_three_variants,
        test_default_variant_is_rep_01,
        test_variant_swaps_payload_path,
        test_sentinel_positions_per_replica,
    ]
    print(f"\n=== test_ensemble_payload ===")
    print(f"Assembly: {_ASSEMBLY}\n")
    passed = 0
    failed = 0
    for fn in tests:
        try:
            fn()
            passed += 1
        except AssertionError as exc:
            print(f"  FAIL {fn.__name__}: {exc}")
            failed += 1
        except Exception as exc:
            print(f"  ERROR {fn.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n--- {passed} passed, {failed} failed ---")
    if failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    run_all()
