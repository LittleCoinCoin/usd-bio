"""test_perturbation_variantset.py — Step 3 of Exp 5 (perturbation_variantset).

Read-back tests for genotype_assembly.usda: opens the stage fresh (no
generator state in scope), switches Genotype variants, and asserts the
composed bio:residueName and atom sentinel positions differ per variant.

Falsification-resistance: the crux assertion is that switching Genotype
CHANGES the resolved bio:residueName AND atom position — proving the Reference
swap operates at the composition level, not just at authoring time. If the
value does not change when the variant changes, that is a real failure and the
test MUST report it as such — not be weakened.

API confirmed via context7 /websites/openusd_release:
  - Usd.Stage.Open(path) — open the assembled stage
  - prim.GetVariantSet("Genotype").SetVariantSelection(name)
  - attr.Get() — sample a composed attribute (no time code needed for static)
  - stage.GetCompositionErrors() — check for composition faults

Usage (from repo root):
    . ./load_env.sh
    /path/to/forOUSD/bin/python3 tests/composition_advanced/test_perturbation_variantset.py
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
    "examples", "composition_advanced", "perturbation_variantset", "genotype_assembly.usda"
)
_KINASE_PATH = Sdf.Path("/ABLKinase")
_RES315_PATH = "/ABLKinase/Res315"

# Sentinel values as authored in the geometry stubs
# [source: examples/composition_advanced/perturbation_variantset/geometries/res315_wt.usda]
# [source: examples/composition_advanced/perturbation_variantset/geometries/res315_t315i.usda]
WT_OG1_PATH = "/ABLKinase/Res315/Atom_OG1"
WT_OG1_SENTINEL = Gf.Vec3d(5.0, 0.0, 0.0)

T315I_CG1_PATH = "/ABLKinase/Res315/Atom_CG1"
T315I_CG1_SENTINEL = Gf.Vec3d(6.0, 0.0, 0.0)


def _open_stage() -> Usd.Stage:
    """Open the assembly stage (cold consumer — no build_genotype state)."""
    assert os.path.exists(_ASSEMBLY), (
        f"genotype_assembly.usda not found at {_ASSEMBLY} — run build_genotype.py first"
    )
    stage = Usd.Stage.Open(_ASSEMBLY)
    assert stage, f"Failed to open stage at {_ASSEMBLY}"
    return stage


# ---------------------------------------------------------------------------
# Test functions
# ---------------------------------------------------------------------------

def test_no_composition_errors() -> None:
    """Stage must compose cleanly — no composition errors under either variant."""
    stage = _open_stage()
    errors = stage.GetCompositionErrors()
    assert errors == [], f"Expected no composition errors, got: {errors}"
    print("  PASS test_no_composition_errors")


def test_kinase_prim_exists() -> None:
    """/ABLKinase must exist as a valid Xform prim with bio:mutationSite."""
    stage = _open_stage()
    prim = stage.GetPrimAtPath(_KINASE_PATH)
    assert prim.IsValid(), "Expected /ABLKinase to be a valid prim"
    assert prim.IsA(UsdGeom.Xform), "/ABLKinase must be typed as Xform"
    site_attr = prim.GetAttribute("bio:mutationSite")
    assert site_attr.IsValid(), "Expected bio:mutationSite attribute on /ABLKinase"
    assert site_attr.Get() == "T315", (
        f"Expected bio:mutationSite='T315', got '{site_attr.Get()}'"
    )
    print("  PASS test_kinase_prim_exists")


def test_genotype_variantset_has_two_variants() -> None:
    """Genotype VariantSet must have exactly 2 variants: WildType and T315I."""
    stage = _open_stage()
    prim = stage.GetPrimAtPath(_KINASE_PATH)
    vset = prim.GetVariantSet("Genotype")
    assert vset, "Expected Genotype VariantSet to exist on /ABLKinase"
    variants = set(vset.GetVariantNames())
    assert variants == {"WildType", "T315I"}, (
        f"Expected variants {{WildType, T315I}}, got {variants}"
    )
    print(f"  PASS test_genotype_variantset_has_two_variants (variants={sorted(variants)})")


def test_default_variant_is_wildtype() -> None:
    """Default variant selection must be WildType (as authored in build_genotype.py)."""
    stage = _open_stage()
    prim = stage.GetPrimAtPath(_KINASE_PATH)
    vset = prim.GetVariantSet("Genotype")
    selection = vset.GetVariantSelection()
    assert selection == "WildType", (
        f"Expected default variant 'WildType', got '{selection}'"
    )
    print(f"  PASS test_default_variant_is_wildtype (selection='{selection}')")


def test_wildtype_residue_name() -> None:
    """WildType variant must resolve bio:residueName = 'THR' on /ABLKinase/Res315.

    Opens the stage fresh and forces WildType selection before reading.
    [source: geometries/res315_wt.usda — bio:residueName = 'THR']
    """
    stage = _open_stage()
    prim = stage.GetPrimAtPath(_KINASE_PATH)
    vset = prim.GetVariantSet("Genotype")
    vset.SetVariantSelection("WildType")

    res315 = stage.GetPrimAtPath(_RES315_PATH)
    assert res315.IsValid(), (
        f"[WildType] Expected {_RES315_PATH} to be valid after variant selection"
    )
    attr = res315.GetAttribute("bio:residueName")
    assert attr.IsValid(), f"[WildType] Expected bio:residueName on {_RES315_PATH}"
    val = attr.Get()
    assert val == "THR", (
        f"[WildType] bio:residueName mismatch: expected 'THR', got '{val}'. "
        "Reference swap is NOT delivering the expected composition result."
    )
    print(f"  PASS test_wildtype_residue_name (bio:residueName='{val}')")


def test_t315i_residue_name() -> None:
    """T315I variant must resolve bio:residueName = 'ILE' on /ABLKinase/Res315.

    Opens the stage fresh and forces T315I selection before reading.
    [source: geometries/res315_t315i.usda — bio:residueName = 'ILE']
    """
    stage = _open_stage()
    prim = stage.GetPrimAtPath(_KINASE_PATH)
    vset = prim.GetVariantSet("Genotype")
    vset.SetVariantSelection("T315I")

    res315 = stage.GetPrimAtPath(_RES315_PATH)
    assert res315.IsValid(), (
        f"[T315I] Expected {_RES315_PATH} to be valid after variant selection"
    )
    attr = res315.GetAttribute("bio:residueName")
    assert attr.IsValid(), f"[T315I] Expected bio:residueName on {_RES315_PATH}"
    val = attr.Get()
    assert val == "ILE", (
        f"[T315I] bio:residueName mismatch: expected 'ILE', got '{val}'. "
        "Reference swap is NOT delivering the expected composition result."
    )
    print(f"  PASS test_t315i_residue_name (bio:residueName='{val}')")


def test_wildtype_sentinel_position() -> None:
    """WildType Oγ1 atom must be at sentinel (5, 0, 0).

    [source: geometries/res315_wt.usda — Atom_OG1.xformOp:translate = (5.0, 0.0, 0.0)]
    """
    stage = _open_stage()
    prim = stage.GetPrimAtPath(_KINASE_PATH)
    prim.GetVariantSet("Genotype").SetVariantSelection("WildType")

    og1 = stage.GetPrimAtPath(WT_OG1_PATH)
    assert og1.IsValid(), (
        f"[WildType] Expected {WT_OG1_PATH} to exist — Oγ1 atom absent"
    )
    translate_attr = og1.GetAttribute("xformOp:translate")
    assert translate_attr.IsValid(), (
        f"[WildType] Expected xformOp:translate on {WT_OG1_PATH}"
    )
    val = translate_attr.Get()
    assert val == WT_OG1_SENTINEL, (
        f"[WildType] Oγ1 position mismatch: expected {WT_OG1_SENTINEL}, got {val}. "
        "WT sentinel not resolved — Reference swap is broken."
    )
    print(f"  PASS test_wildtype_sentinel_position (Atom_OG1 translate={tuple(val)})")


def test_t315i_sentinel_position() -> None:
    """T315I Cγ1 atom must be at sentinel (6, 0, 0).

    [source: geometries/res315_t315i.usda — Atom_CG1.xformOp:translate = (6.0, 0.0, 0.0)]
    """
    stage = _open_stage()
    prim = stage.GetPrimAtPath(_KINASE_PATH)
    prim.GetVariantSet("Genotype").SetVariantSelection("T315I")

    cg1 = stage.GetPrimAtPath(T315I_CG1_PATH)
    assert cg1.IsValid(), (
        f"[T315I] Expected {T315I_CG1_PATH} to exist — Cγ1 atom absent"
    )
    translate_attr = cg1.GetAttribute("xformOp:translate")
    assert translate_attr.IsValid(), (
        f"[T315I] Expected xformOp:translate on {T315I_CG1_PATH}"
    )
    val = translate_attr.Get()
    assert val == T315I_CG1_SENTINEL, (
        f"[T315I] Cγ1 position mismatch: expected {T315I_CG1_SENTINEL}, got {val}. "
        "T315I sentinel not resolved — Reference swap is broken."
    )
    print(f"  PASS test_t315i_sentinel_position (Atom_CG1 translate={tuple(val)})")


def test_variant_swap_updates_position() -> None:
    """Switching Genotype on the SAME stage must change the resolved residueName.

    This is the crux falsification test: the composition is live, not cached.
    If both variants return the same residueName, Reference swapping is NOT
    operating at the composition level — that is a real failure, not a quirk.

    WildType → THR; then same stage, T315I → ILE.
    """
    stage = _open_stage()
    prim = stage.GetPrimAtPath(_KINASE_PATH)
    vset = prim.GetVariantSet("Genotype")

    vset.SetVariantSelection("WildType")
    res315_wt = stage.GetPrimAtPath(_RES315_PATH)
    wt_name = res315_wt.GetAttribute("bio:residueName").Get()

    vset.SetVariantSelection("T315I")
    # Re-fetch prim after variant switch
    res315_t315i = stage.GetPrimAtPath(_RES315_PATH)
    t315i_name = res315_t315i.GetAttribute("bio:residueName").Get()

    assert wt_name != t315i_name, (
        f"Genotype switch did NOT change bio:residueName: "
        f"WildType='{wt_name}', T315I='{t315i_name}'. "
        "Reference swapping is NOT working at composition level."
    )
    assert wt_name == "THR", (
        f"WildType resolved '{wt_name}' instead of 'THR'"
    )
    assert t315i_name == "ILE", (
        f"T315I resolved '{t315i_name}' instead of 'ILE'"
    )
    print(
        f"  PASS test_variant_swap_updates_position "
        f"(WildType→'{wt_name}', then same stage T315I→'{t315i_name}')"
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all() -> None:
    """Run all test functions and report results."""
    tests = [
        test_no_composition_errors,
        test_kinase_prim_exists,
        test_genotype_variantset_has_two_variants,
        test_default_variant_is_wildtype,
        test_wildtype_residue_name,
        test_t315i_residue_name,
        test_wildtype_sentinel_position,
        test_t315i_sentinel_position,
        test_variant_swap_updates_position,
    ]
    print(f"\n=== test_perturbation_variantset ===")
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
