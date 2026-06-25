"""
test_references_vs_sublayers.py
================================
Read-back tests for Exp 6 — References vs SubLayers (Exp 6).

Opens both assemblies FRESH (no generator code in scope) and asserts:
  1. Both stages open without composition errors.
  2. Atom count (prims with bio:element) is equal in both.
  3. representation VariantSet exists on /ABLComplex in both.
  4. SubLayer style: /_class_/C is valid at the stage root.
  5. Reference style: /_class_/C is NOT valid at root; /ElementLib IS valid.
  6. Inherited bio:vdwRadius on a carbon atom equals in both (same source data).

Design notes:
  - All expected values derive from source data (data/element_properties.py)
    and the leaf spec — not from generator in-memory state.
  - Atom count (4676) is independently confirmed from PDB atom count
    [source: examples/foundation_demo_v8/assets/level4_assemblies/abl_kinase_complex.usda bio:atomCount]
  - Carbon vdwRadius (1.7 Å) derives from ELEMENTS["C"]["vdw_radius"]
    [source: examples/foundation_demo_v8/data/element_properties.py]

Usage (from examples/foundation_demo_v8/):
    source ../../load_env.sh
    python3 tests/test_references_vs_sublayers.py
"""

import os
import sys

from pxr import Usd, Sdf

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEMO_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _DEMO_ROOT)

from data.element_properties import ELEMENTS  # type: ignore[import]

# ---------------------------------------------------------------------------
# Constants — independently derived, not from generator state
# ---------------------------------------------------------------------------

# Carbon vdwRadius from source data
_C_VDW_RADIUS: float = ELEMENTS["C"]["vdw_radius"]  # 1.7 Å

# Expected atom count from PDB (ATOM records in atp-complex-solv35.pdb)
_EXPECTED_ATOM_COUNT: int = 4676

# Asset paths
_ASSETS_DIR = os.path.join(_DEMO_ROOT, "assets", "level4_assemblies")
_SUBLAYER_PATH = os.path.join(_ASSETS_DIR, "abl_kinase_complex.usda")
_REFSTYLE_PATH = os.path.join(_ASSETS_DIR, "abl_kinase_complex_refstyle.usda")

# Tolerance for float comparisons (USD stores float32 attributes)
_FLOAT_TOL = 1e-5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open_stages() -> tuple:
    """Open both assemblies. Raises AssertionError if files are missing."""
    for path in [_SUBLAYER_PATH, _REFSTYLE_PATH]:
        assert os.path.exists(path), (
            f"Assembly not found: {path}\n"
            f"Run the corresponding template script first."
        )
    stage_sub = Usd.Stage.Open(_SUBLAYER_PATH)
    stage_ref = Usd.Stage.Open(_REFSTYLE_PATH)
    assert stage_sub, f"Failed to open sublayer assembly: {_SUBLAYER_PATH}"
    assert stage_ref, f"Failed to open refstyle assembly: {_REFSTYLE_PATH}"
    return stage_sub, stage_ref


def _count_atoms(stage: Usd.Stage) -> int:
    """Count prims carrying a non-None bio:element attribute."""
    return sum(
        1
        for p in stage.Traverse()
        if p.GetAttribute("bio:element").IsValid()
        and p.GetAttribute("bio:element").Get() is not None
    )


# ---------------------------------------------------------------------------
# Test functions
# ---------------------------------------------------------------------------

def test_both_stages_open() -> None:
    """Both assemblies open without composition errors."""
    stage_sub, stage_ref = _open_stages()

    errors_sub = stage_sub.GetCompositionErrors()
    assert not errors_sub, (
        f"Sublayer assembly has composition errors: {errors_sub}"
    )

    errors_ref = stage_ref.GetCompositionErrors()
    assert not errors_ref, (
        f"Refstyle assembly has composition errors: {errors_ref}"
    )

    print("  PASS: test_both_stages_open — no composition errors in either assembly")


def test_atom_count_parity() -> None:
    """Atom count (prims with bio:element) is equal in both assemblies."""
    stage_sub, stage_ref = _open_stages()

    sub_count = _count_atoms(stage_sub)
    ref_count = _count_atoms(stage_ref)

    assert sub_count == _EXPECTED_ATOM_COUNT, (
        f"Sublayer atom count: expected {_EXPECTED_ATOM_COUNT}, got {sub_count}"
    )
    assert ref_count == _EXPECTED_ATOM_COUNT, (
        f"Refstyle atom count: expected {_EXPECTED_ATOM_COUNT}, got {ref_count}"
    )
    assert sub_count == ref_count, (
        f"Atom count mismatch: sublayer={sub_count}, refstyle={ref_count}"
    )

    print(
        f"  PASS: test_atom_count_parity — "
        f"sublayer={sub_count} == refstyle={ref_count} == {_EXPECTED_ATOM_COUNT}"
    )


def test_representation_variantset() -> None:
    """representation VariantSet exists on /ABLComplex in both assemblies."""
    stage_sub, stage_ref = _open_stages()

    for label, stage in [("sublayer", stage_sub), ("refstyle", stage_ref)]:
        complex_prim = stage.GetPrimAtPath("/ABLComplex")
        assert complex_prim.IsValid(), (
            f"{label}: /ABLComplex prim not found"
        )
        vsets = complex_prim.GetVariantSets()
        assert vsets.HasVariantSet("representation"), (
            f"{label}: /ABLComplex missing 'representation' VariantSet"
        )
        vset = vsets.GetVariantSet("representation")
        names = set(vset.GetVariantNames())
        expected = {"points", "balls", "vdw", "ballstick"}
        assert names == expected, (
            f"{label}: unexpected variant names: {names} (expected {expected})"
        )

    print(
        "  PASS: test_representation_variantset — "
        "both /ABLComplex prims have representation VariantSet {points, balls, vdw, ballstick}"
    )


def test_sublayer_root_class_prim() -> None:
    """SubLayer style: /_class_/C is valid at the stage root."""
    stage_sub, _ = _open_stages()

    class_c = stage_sub.GetPrimAtPath("/_class_/C")
    assert class_c.IsValid(), (
        "Sublayer assembly: expected /_class_/C to be valid at stage root "
        "(element_templates.usda is a sublayer, merging /_class_/ into root)"
    )
    # Confirm it has the expected specifier (class prim)
    assert class_c.GetSpecifier() == Sdf.SpecifierClass, (
        f"/_class_/C should be a class prim, got specifier: {class_c.GetSpecifier()}"
    )

    print(
        f"  PASS: test_sublayer_root_class_prim — "
        f"/_class_/C IsValid={class_c.IsValid()}, specifier={class_c.GetSpecifier()}"
    )


def test_reference_namespaced_class_prim() -> None:
    """Reference style: /_class_/C invalid at root; /ElementLib valid."""
    _, stage_ref = _open_stages()

    # The element library is namespaced under /ElementLib — root /_class_/C must NOT exist
    root_class_c = stage_ref.GetPrimAtPath("/_class_/C")
    assert not root_class_c.IsValid(), (
        "Refstyle assembly: /_class_/C should NOT be valid at the stage root "
        "(element_library.usda is referenced into /ElementLib, not sublayered). "
        f"Got IsValid={root_class_c.IsValid()}"
    )

    # /ElementLib must exist (the reference target prim)
    elem_lib = stage_ref.GetPrimAtPath("/ElementLib")
    assert elem_lib.IsValid(), (
        "Refstyle assembly: /ElementLib prim not found. "
        "AddReference on /ElementLib must compose element_library.usda here."
    )

    # The class hierarchy is accessible under /ElementLib/_class_/C
    namespaced_class_c = stage_ref.GetPrimAtPath("/ElementLib/_class_/C")
    assert namespaced_class_c.IsValid(), (
        "Refstyle assembly: /ElementLib/_class_/C not found. "
        "The composed hierarchy from element_library.usda should be accessible here."
    )

    print(
        "  PASS: test_reference_namespaced_class_prim — "
        "/_class_/C=False at root, /ElementLib=True, /ElementLib/_class_/C=True"
    )


def test_inherited_radius_parity() -> None:
    """Inherited bio:vdwRadius on a carbon atom equals in both assemblies."""
    stage_sub, stage_ref = _open_stages()

    # Use first carbon atom in ACE_1 (CH3 is carbon; element 'C')
    # Confirmed in 04_create_assembly.py: ACE_1 has CH3 (C) and C (C) atoms
    c_atom_path = "/ABLComplex/Chain_A/ACE_1/CH3"

    sub_atom = stage_sub.GetPrimAtPath(c_atom_path)
    ref_atom = stage_ref.GetPrimAtPath(c_atom_path)

    assert sub_atom.IsValid(), f"Sublayer: {c_atom_path} not found"
    assert ref_atom.IsValid(), f"Refstyle: {c_atom_path} not found"

    # Verify both are carbon atoms
    sub_elem = sub_atom.GetAttribute("bio:element").Get()
    ref_elem = ref_atom.GetAttribute("bio:element").Get()
    assert sub_elem == "C", f"Expected bio:element='C', got '{sub_elem}' in sublayer"
    assert ref_elem == "C", f"Expected bio:element='C', got '{ref_elem}' in refstyle"

    # bio:vdwRadius is inherited — should resolve from the element class in both styles
    sub_vdw = sub_atom.GetAttribute("bio:vdwRadius").Get()
    ref_vdw = ref_atom.GetAttribute("bio:vdwRadius").Get()

    assert sub_vdw is not None, (
        f"Sublayer: bio:vdwRadius not resolved on {c_atom_path}. "
        "Inherit arc from /_class_/C may be broken."
    )
    assert ref_vdw is not None, (
        f"Refstyle: bio:vdwRadius not resolved on {c_atom_path}. "
        "Inherit arc from /ElementLib/_class_/C may be broken."
    )

    assert abs(sub_vdw - _C_VDW_RADIUS) < _FLOAT_TOL, (
        f"Sublayer: bio:vdwRadius={sub_vdw}, expected {_C_VDW_RADIUS}"
    )
    assert abs(ref_vdw - _C_VDW_RADIUS) < _FLOAT_TOL, (
        f"Refstyle: bio:vdwRadius={ref_vdw}, expected {_C_VDW_RADIUS}"
    )
    assert abs(sub_vdw - ref_vdw) < _FLOAT_TOL, (
        f"bio:vdwRadius mismatch: sublayer={sub_vdw}, refstyle={ref_vdw}"
    )

    print(
        f"  PASS: test_inherited_radius_parity — "
        f"sublayer={sub_vdw:.4f} == refstyle={ref_vdw:.4f} == {_C_VDW_RADIUS} Å"
    )


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_both_stages_open,
        test_atom_count_parity,
        test_representation_variantset,
        test_sublayer_root_class_prim,
        test_reference_namespaced_class_prim,
        test_inherited_radius_parity,
    ]

    print("=== test_references_vs_sublayers ===")
    failures = []
    for test_fn in tests:
        try:
            test_fn()
        except AssertionError as exc:
            print(f"  FAIL: {test_fn.__name__} — {exc}")
            failures.append(test_fn.__name__)
        except Exception as exc:
            print(f"  ERROR: {test_fn.__name__} — {type(exc).__name__}: {exc}")
            failures.append(test_fn.__name__)

    print()
    if failures:
        print(f"RESULT: {len(failures)}/{len(tests)} FAILED: {failures}")
        sys.exit(1)
    else:
        print(f"RESULT: {len(tests)}/{len(tests)} PASSED")
        sys.exit(0)
