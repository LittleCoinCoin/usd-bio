"""test_parameter_variantset.py — Step 3 of parameter_variantset leaf.

Read-back tests for forcefield_assembly.usda: opens the stage fresh (no
generator state in scope), switches ForceField variants, and asserts that
bio:partialCharge on representative atoms resolves to the correct force-field
sentinel value per variant.

Falsification-resistance: the crux assertion is that switching ForceField
CHANGES the resolved bio:partialCharge — proving the Reference arc mechanism
operates at the composition level, not just at authoring time. If the value
does not change when the variant changes, that is a real failure and the test
MUST report it as such — not be weakened.

## Key finding: SubLayer-in-variant does NOT work

SubLayers are a stage-level / layer-stack construct; they cannot be scoped
to a variant edit context. The assembly uses Reference arcs instead (authored
inside GetVariantEditContext()), pointing to param overlay files with explicit
primPath="/ABLFragment". This correctly brings the 'over' opinions into variant
scope.
[source: examples/composition_advanced/parameter_variantset/build_forcefield.py
 — docstring documents the investigation and chosen mechanism]

Sentinel values:
  Atom_CA bio:partialCharge: AMBER = -0.0518, CHARMM = -0.02
  Atom_N  bio:partialCharge: AMBER = -0.4157, CHARMM = -0.47
[source: examples/composition_advanced/parameter_variantset/params/amber99.usda]
[source: examples/composition_advanced/parameter_variantset/params/charmm36.usda]

API confirmed via context7 /websites/openusd_release:
  - Usd.Stage.Open(path) — open the assembled stage fresh
  - prim.GetVariantSet("ForceField").SetVariantSelection(name)
  - attr.Get() — sample a composed attribute (no time code needed for static)
  - stage.GetCompositionErrors() — check for composition faults

Usage (from repo root):
    . ./load_env.sh
    /path/to/forOUSD/bin/python3 tests/composition_advanced/test_parameter_variantset.py
"""

import math
import os
import sys

from pxr import Sdf, Usd, UsdGeom

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ASSEMBLY = os.path.join(
    _REPO_ROOT,
    "examples", "composition_advanced", "parameter_variantset", "forcefield_assembly.usda"
)
_FRAG_PATH = Sdf.Path("/ABLFragment")
_ATOM_CA_PATH = "/ABLFragment/Chain_A/Res_001/Atom_CA"
_ATOM_N_PATH = "/ABLFragment/Chain_A/Res_001/Atom_N"

# Sentinel values — must match param overlay files exactly.
# [source: examples/composition_advanced/parameter_variantset/params/amber99.usda]
# [source: examples/composition_advanced/parameter_variantset/params/charmm36.usda]
# [assumption: representative values from AMBER99SB-ILDN and CHARMM36m;
#  not from literal parameter files — see param layer comments]
AMBER_CHARGE_CA = -0.0518
CHARMM_CHARGE_CA = -0.02
AMBER_CHARGE_N = -0.4157
CHARMM_CHARGE_N = -0.47
AMBER_FF_NAME = "AMBER99SB-ILDN"
CHARMM_FF_NAME = "CHARMM36m"

# Float tolerance for attribute round-trip comparisons
_FLOAT_TOL = 1e-5


def _open_stage() -> Usd.Stage:
    """Open forcefield_assembly.usda as a cold consumer — no build state in scope."""
    assert os.path.exists(_ASSEMBLY), (
        f"forcefield_assembly.usda not found at {_ASSEMBLY} — run build_forcefield.py first"
    )
    stage = Usd.Stage.Open(_ASSEMBLY)
    assert stage, f"Failed to open stage at {_ASSEMBLY}"
    return stage


def _approx_equal(a: float, b: float, tol: float = _FLOAT_TOL) -> bool:
    """Return True if |a - b| <= tol."""
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tol


# ---------------------------------------------------------------------------
# Test functions
# ---------------------------------------------------------------------------

def test_no_composition_errors() -> None:
    """Stage must compose cleanly — no composition errors under either variant."""
    stage = _open_stage()
    errors = stage.GetCompositionErrors()
    assert errors == [], f"Expected no composition errors, got: {errors}"
    print("  PASS test_no_composition_errors")


def test_fragment_prim_exists() -> None:
    """/ABLFragment must exist as a valid Xform prim."""
    stage = _open_stage()
    prim = stage.GetPrimAtPath(_FRAG_PATH)
    assert prim.IsValid(), "Expected /ABLFragment to be a valid prim"
    assert prim.IsA(UsdGeom.Xform), "/ABLFragment must be typed as Xform"
    print("  PASS test_fragment_prim_exists")


def test_forcefield_variantset_has_two_variants() -> None:
    """ForceField VariantSet must have exactly 2 variants: Amber99 and Charmm36."""
    stage = _open_stage()
    prim = stage.GetPrimAtPath(_FRAG_PATH)
    vset = prim.GetVariantSet("ForceField")
    assert vset, "Expected ForceField VariantSet to exist on /ABLFragment"
    variants = set(vset.GetVariantNames())
    assert variants == {"Amber99", "Charmm36"}, (
        f"Expected variants {{Amber99, Charmm36}}, got {variants}"
    )
    print(f"  PASS test_forcefield_variantset_has_two_variants (variants={sorted(variants)})")


def test_default_variant_is_amber99() -> None:
    """Default variant selection must be Amber99 (as authored in build_forcefield.py)."""
    stage = _open_stage()
    prim = stage.GetPrimAtPath(_FRAG_PATH)
    vset = prim.GetVariantSet("ForceField")
    selection = vset.GetVariantSelection()
    assert selection == "Amber99", (
        f"Expected default variant 'Amber99', got '{selection}'"
    )
    print(f"  PASS test_default_variant_is_amber99 (selection='{selection}')")


def test_amber_partial_charge() -> None:
    """Amber99 variant must resolve bio:partialCharge = AMBER sentinel on Atom_CA.

    Opens fresh stage, forces Amber99 selection, reads Atom_CA bio:partialCharge.
    Sentinel: -0.0518 [source: params/amber99.usda]
    """
    stage = _open_stage()
    frag = stage.GetPrimAtPath(_FRAG_PATH)
    frag.GetVariantSet("ForceField").SetVariantSelection("Amber99")

    atom_ca = stage.GetPrimAtPath(_ATOM_CA_PATH)
    assert atom_ca.IsValid(), (
        f"[Amber99] Expected {_ATOM_CA_PATH} to be valid after variant selection"
    )
    attr = atom_ca.GetAttribute("bio:partialCharge")
    assert attr.IsValid(), f"[Amber99] Expected bio:partialCharge attribute on {_ATOM_CA_PATH}"
    val = attr.Get()
    assert val is not None, f"[Amber99] bio:partialCharge returned None — attribute has no value"
    assert _approx_equal(val, AMBER_CHARGE_CA), (
        f"[Amber99] bio:partialCharge mismatch on Atom_CA: "
        f"expected {AMBER_CHARGE_CA}, got {val}. "
        "Reference arc is NOT delivering the AMBER parameter overlay."
    )
    print(f"  PASS test_amber_partial_charge (Atom_CA bio:partialCharge={val})")


def test_charmm_partial_charge() -> None:
    """Charmm36 variant must resolve bio:partialCharge = CHARMM sentinel on Atom_CA.

    Opens fresh stage, forces Charmm36 selection, reads Atom_CA bio:partialCharge.
    Sentinel: -0.02 [source: params/charmm36.usda]
    """
    stage = _open_stage()
    frag = stage.GetPrimAtPath(_FRAG_PATH)
    frag.GetVariantSet("ForceField").SetVariantSelection("Charmm36")

    atom_ca = stage.GetPrimAtPath(_ATOM_CA_PATH)
    assert atom_ca.IsValid(), (
        f"[Charmm36] Expected {_ATOM_CA_PATH} to be valid after variant selection"
    )
    attr = atom_ca.GetAttribute("bio:partialCharge")
    assert attr.IsValid(), f"[Charmm36] Expected bio:partialCharge attribute on {_ATOM_CA_PATH}"
    val = attr.Get()
    assert val is not None, f"[Charmm36] bio:partialCharge returned None — attribute has no value"
    assert _approx_equal(val, CHARMM_CHARGE_CA), (
        f"[Charmm36] bio:partialCharge mismatch on Atom_CA: "
        f"expected {CHARMM_CHARGE_CA}, got {val}. "
        "Reference arc is NOT delivering the CHARMM parameter overlay."
    )
    print(f"  PASS test_charmm_partial_charge (Atom_CA bio:partialCharge={val})")


def test_forcefield_name_metadata() -> None:
    """bio:forceFieldName on /ABLFragment must differ per variant.

    Amber99 → 'AMBER99SB-ILDN'; Charmm36 → 'CHARMM36m'.
    [source: build_forcefield.py — CreateAttribute in each variant's edit context]
    """
    # Amber99
    stage_a = _open_stage()
    frag_a = stage_a.GetPrimAtPath(_FRAG_PATH)
    frag_a.GetVariantSet("ForceField").SetVariantSelection("Amber99")
    ff_attr_a = frag_a.GetAttribute("bio:forceFieldName")
    assert ff_attr_a.IsValid(), "[Amber99] Expected bio:forceFieldName on /ABLFragment"
    name_amber = ff_attr_a.Get()
    assert name_amber == AMBER_FF_NAME, (
        f"[Amber99] bio:forceFieldName: expected '{AMBER_FF_NAME}', got '{name_amber}'"
    )

    # Charmm36
    stage_c = _open_stage()
    frag_c = stage_c.GetPrimAtPath(_FRAG_PATH)
    frag_c.GetVariantSet("ForceField").SetVariantSelection("Charmm36")
    ff_attr_c = frag_c.GetAttribute("bio:forceFieldName")
    assert ff_attr_c.IsValid(), "[Charmm36] Expected bio:forceFieldName on /ABLFragment"
    name_charmm = ff_attr_c.Get()
    assert name_charmm == CHARMM_FF_NAME, (
        f"[Charmm36] bio:forceFieldName: expected '{CHARMM_FF_NAME}', got '{name_charmm}'"
    )

    assert name_amber != name_charmm, (
        f"bio:forceFieldName did not differ between variants: both='{name_amber}'"
    )
    print(
        f"  PASS test_forcefield_name_metadata "
        f"(Amber99='{name_amber}', Charmm36='{name_charmm}')"
    )


def test_variant_swap_updates_charge() -> None:
    """Switching ForceField on the SAME stage must change the resolved bio:partialCharge.

    This is the crux falsification test: the composition is live, not cached.
    If both variants return the same bio:partialCharge, the Reference swap is NOT
    operating at the composition level — that is a real failure, not a quirk.

    Amber99 → -0.0518; then same stage, Charmm36 → -0.02 (Atom_CA).
    """
    stage = _open_stage()
    frag = stage.GetPrimAtPath(_FRAG_PATH)
    vset = frag.GetVariantSet("ForceField")
    atom_ca = stage.GetPrimAtPath(_ATOM_CA_PATH)

    # Read under Amber99
    vset.SetVariantSelection("Amber99")
    val_amber = atom_ca.GetAttribute("bio:partialCharge").Get()
    assert val_amber is not None, "[Amber99] bio:partialCharge returned None"

    # Switch to Charmm36 on the same stage object
    vset.SetVariantSelection("Charmm36")
    val_charmm = atom_ca.GetAttribute("bio:partialCharge").Get()
    assert val_charmm is not None, "[Charmm36] bio:partialCharge returned None"

    assert not _approx_equal(val_amber, val_charmm), (
        f"ForceField switch did NOT change bio:partialCharge on Atom_CA: "
        f"Amber99={val_amber}, Charmm36={val_charmm}. "
        "Reference arc swapping is NOT working at the composition level."
    )
    assert _approx_equal(val_amber, AMBER_CHARGE_CA), (
        f"Amber99 resolved {val_amber} instead of sentinel {AMBER_CHARGE_CA}"
    )
    assert _approx_equal(val_charmm, CHARMM_CHARGE_CA), (
        f"Charmm36 resolved {val_charmm} instead of sentinel {CHARMM_CHARGE_CA}"
    )
    print(
        f"  PASS test_variant_swap_updates_charge "
        f"(same stage: Amber99→{val_amber}, then Charmm36→{val_charmm})"
    )


def test_atom_n_charges_differ() -> None:
    """bio:partialCharge on Atom_N must also differ between ForceField variants.

    Amber99 N = -0.4157; Charmm36 N = -0.47.
    [source: params/amber99.usda, params/charmm36.usda]
    """
    stage = _open_stage()
    frag = stage.GetPrimAtPath(_FRAG_PATH)
    vset = frag.GetVariantSet("ForceField")
    atom_n = stage.GetPrimAtPath(_ATOM_N_PATH)

    vset.SetVariantSelection("Amber99")
    val_n_amber = atom_n.GetAttribute("bio:partialCharge").Get()
    assert val_n_amber is not None, "[Amber99] Atom_N bio:partialCharge returned None"
    assert _approx_equal(val_n_amber, AMBER_CHARGE_N), (
        f"[Amber99] Atom_N bio:partialCharge: expected {AMBER_CHARGE_N}, got {val_n_amber}"
    )

    vset.SetVariantSelection("Charmm36")
    val_n_charmm = atom_n.GetAttribute("bio:partialCharge").Get()
    assert val_n_charmm is not None, "[Charmm36] Atom_N bio:partialCharge returned None"
    assert _approx_equal(val_n_charmm, CHARMM_CHARGE_N), (
        f"[Charmm36] Atom_N bio:partialCharge: expected {CHARMM_CHARGE_N}, got {val_n_charmm}"
    )

    assert not _approx_equal(val_n_amber, val_n_charmm), (
        f"Atom_N bio:partialCharge did not differ between variants: "
        f"Amber={val_n_amber}, Charmm={val_n_charmm}"
    )
    print(
        f"  PASS test_atom_n_charges_differ "
        f"(Atom_N: Amber99={val_n_amber}, Charmm36={val_n_charmm})"
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all() -> None:
    """Run all test functions and report results."""
    tests = [
        test_no_composition_errors,
        test_fragment_prim_exists,
        test_forcefield_variantset_has_two_variants,
        test_default_variant_is_amber99,
        test_amber_partial_charge,
        test_charmm_partial_charge,
        test_forcefield_name_metadata,
        test_variant_swap_updates_charge,
        test_atom_n_charges_differ,
    ]
    print(f"\n=== test_parameter_variantset ===")
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
