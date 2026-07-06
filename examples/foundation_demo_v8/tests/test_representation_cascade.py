#!/usr/bin/env python3
"""
test_representation_cascade.py
===============================
Falsification-resistant read-back proof that the `representation` VariantSet
cascade genuinely resolves on freshly-opened, regenerated demo artifacts,
covering the v8-gap-closure "scalable representation variant-cascade fix"
mandate (item (c)).

BACKGROUND — the defect this test guards against
--------------------------------------------------
Before this fix, demos/assembly_demo.py and demos/trajectory_demo.py each
created a decorative `/World` Xform, set it as defaultPrim, and looped
`with world_vset.GetVariantEditContext(): complex_prim...SetVariantSelection(
mode)` hoping to cascade a selection from /World down to the SIBLING prim
/ABLComplex (brought in via SubLayer, not as a child of /World). USD variant
fallthrough only cascades a GetVariantEditContext()-scoped edit to NAMESPACE
DESCENDANTS of the variant-owning prim -- siblings are unreachable that way.
The loop's real effect was to write ONE unconditional opinion (the last
iteration's value) directly onto /ABLComplex's own path; /World's own
variant selection was pure decoration with zero effect in usdview.

THE FIX
-------
/ABLComplex (the actual geometry root already produced by
templates/04_create_assembly.py's own internal variant cascade) is now ALSO
the defaultPrim, and the demo authors its `representation` selection
directly on that same prim -- no proxy dispatcher prim, so cascade and
lookup happen on the same namespace subtree by construction. See the
WHY-NOT comments at the top of demos/assembly_demo.py and
demos/trajectory_demo.py, and demos/curves_demo.py /
demos/departmental_demo.py for the same pattern applied earlier in this
gap-closure effort.

DESIGN CONTRACT (falsification-resistance)
-------------------------------------------
- Every stage is opened FRESH via Usd.Stage.Open() in this process -- the
  demo generator modules are never imported, so no in-memory generator
  state can leak into the assertions.
- Expectations (radius values, bond visibility per mode) are independently
  re-derived from OTHER already-committed artifacts (element_templates.usda
  radius values via data.ELEMENTS, and the topology's own Bond_* Cylinder
  child) rather than assumed from what assembly_demo.py/trajectory_demo.py
  happen to emit.
- Asserts switching between at least two representation modes yields a
  measurably different COMPOSED result (radius and/or visibility), not
  merely that GetVariantSelection() echoes back the string that was set.

Usage (from examples/foundation_demo_v8/):
    source ../../load_env.sh
    /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 tests/test_representation_cascade.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

try:
    from pxr import Usd, UsdGeom, Sdf
except ImportError as exc:
    raise ImportError(
        "pxr not importable. Run under the OpenUSD Python interpreter "
        "with load_env.sh sourced."
    ) from exc

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEMO_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _DEMO_ROOT)

from data import get_scaled_radius  # noqa: E402  [source: examples/foundation_demo_v8/data]

_OUTPUT_DIR = os.path.join(_DEMO_ROOT, "output")
_ASSEMBLY_DEMO_PATH = os.path.join(_OUTPUT_DIR, "assembly_demo.usda")
_TRAJECTORY_DEMO_PATH = os.path.join(_OUTPUT_DIR, "trajectory_demo.usda")

_EXPECTED_VARIANTS = frozenset({"points", "balls", "vdw", "ballstick"})
_SAMPLE_ATOM_PATH = "/ABLComplex/Chain_A/ACE_1/HH31"  # hydrogen atom
_SAMPLE_BOND_PATH = "/ABLComplex/Chain_A/ACE_1/Bond_CH3_C/Cylinder"

# Independently-derived expected radii for a Hydrogen atom Sphere per mode.
# [source: examples/foundation_demo_v8/data/element_properties.py
#  get_scaled_radius()/RADIUS_SCALES/ELEMENTS -- the SAME data module
#  templates/01_create_element_templates.py uses to author /_class_/H's own
#  variant geometry, called directly here rather than duplicating the scale
#  factors, but NOT reading assembly_demo.usda or importing the demo
#  generator modules themselves]
_EXPECTED_H_RADII = {
    mode: round(get_scaled_radius("H", mode), 4)
    for mode in ("points", "balls", "vdw", "ballstick")
}
_RADIUS_TOLERANCE = 0.005


@dataclass
class TestResult:
    name: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    detail: dict = field(default_factory=dict)


def _fresh(path: str) -> "Usd.Stage":
    """Open path FRESH -- independent Usd.Stage.Open() call per test, never
    a shared/cached stage object, so no test's SetVariantSelection() call
    can leak into another test's 'fresh' expectations."""
    stage = Usd.Stage.Open(path)
    if stage is None:
        raise RuntimeError(f"Usd.Stage.Open failed: {path}")
    return stage


# ---------------------------------------------------------------------------
# 1. No decorative /World dispatcher prim remains
# ---------------------------------------------------------------------------

def test_no_decorative_world_prim(path: str, label: str) -> TestResult:
    errors: list[str] = []
    detail: dict = {}
    stage = _fresh(path)

    world = stage.GetPrimAtPath("/World")
    detail["world_prim_valid"] = world.IsValid()
    if world.IsValid():
        errors.append(
            f"{label}: /World still authored on stage -- the decorative "
            "dispatcher pattern should have been removed"
        )

    default_prim = stage.GetDefaultPrim()
    detail["default_prim_path"] = str(default_prim.GetPath()) if default_prim else None
    if not default_prim or not default_prim.IsValid():
        errors.append(f"{label}: stage has no valid defaultPrim")
    elif str(default_prim.GetPath()) != "/ABLComplex":
        errors.append(
            f"{label}: expected defaultPrim=/ABLComplex, got {default_prim.GetPath()}"
        )

    return TestResult(f"test_no_decorative_world_prim[{label}]",
                       len(errors) == 0, errors, detail)


# ---------------------------------------------------------------------------
# 2. Root `representation` selection is namespace-scoped on the defaultPrim
#    itself (the structural precondition for genuine fallthrough) and a
#    default is authored on fresh open.
# ---------------------------------------------------------------------------

def test_root_selection_on_default_prim(path: str, label: str,
                                          expected_default: str) -> TestResult:
    errors: list[str] = []
    detail: dict = {}
    stage = _fresh(path)

    default_prim = stage.GetDefaultPrim()
    if not default_prim or not default_prim.IsValid():
        errors.append(f"{label}: no valid defaultPrim")
        return TestResult(f"test_root_selection_on_default_prim[{label}]",
                           False, errors, detail)

    vsets = default_prim.GetVariantSets()
    if "representation" not in vsets.GetNames():
        errors.append(f"{label}: defaultPrim has no 'representation' VariantSet")
        return TestResult(f"test_root_selection_on_default_prim[{label}]",
                           False, errors, detail)

    vset = vsets.GetVariantSet("representation")
    actual_variants = frozenset(vset.GetVariantNames())
    detail["variants"] = sorted(actual_variants)
    if not _EXPECTED_VARIANTS.issubset(actual_variants):
        errors.append(
            f"{label}: missing expected variants "
            f"{sorted(_EXPECTED_VARIANTS - actual_variants)}"
        )

    sel = vset.GetVariantSelection()
    detail["default_selection"] = sel
    if sel != expected_default:
        errors.append(
            f"{label}: default selection={sel!r}, expected {expected_default!r}"
        )

    # Sample atom must be a genuine namespace DESCENDANT of the variant-owning
    # defaultPrim -- the structural precondition that makes fallthrough work
    # at all (this is what /World lacked: /ABLComplex was a SIBLING).
    atom = stage.GetPrimAtPath(_SAMPLE_ATOM_PATH)
    detail["sample_atom_is_descendant"] = atom.IsValid() and str(
        atom.GetPath()).startswith(str(default_prim.GetPath()) + "/")
    if not detail["sample_atom_is_descendant"]:
        errors.append(
            f"{label}: sample atom {_SAMPLE_ATOM_PATH} is not a namespace "
            f"descendant of defaultPrim {default_prim.GetPath()}"
        )

    return TestResult(f"test_root_selection_on_default_prim[{label}]",
                       len(errors) == 0, errors, detail)


# ---------------------------------------------------------------------------
# 3. Cascade proof: switching the ROOT selection changes DESCENDANT composed
#    state (radius), matching independently-derived expectations, and at
#    least two modes differ from each other.
# ---------------------------------------------------------------------------

def test_assembly_cascade_changes_atom_radius(path: str) -> TestResult:
    errors: list[str] = []
    detail: dict = {}
    stage = _fresh(path)

    default_prim = stage.GetDefaultPrim()
    vset = default_prim.GetVariantSets().GetVariantSet("representation")
    sphere_path = _SAMPLE_ATOM_PATH + "/Sphere"

    observed: dict[str, float] = {}
    for mode in sorted(_EXPECTED_VARIANTS):
        vset.SetVariantSelection(mode)
        sphere = stage.GetPrimAtPath(sphere_path)
        if not sphere.IsValid():
            errors.append(f"mode={mode}: {sphere_path} not valid after selection")
            continue
        r = sphere.GetAttribute("radius").Get()
        observed[mode] = float(r) if r is not None else float("nan")

    detail["observed_radii"] = observed
    detail["expected_radii"] = _EXPECTED_H_RADII

    for mode, expected_r in _EXPECTED_H_RADII.items():
        actual_r = observed.get(mode, float("nan"))
        if actual_r != actual_r:  # NaN check without importing math
            continue
        if abs(actual_r - expected_r) > _RADIUS_TOLERANCE:
            errors.append(
                f"mode={mode}: composed radius={actual_r:.4f} does not match "
                f"independently-derived expected={expected_r:.4f} "
                "(from data.ELEMENTS['H'], not the generator)"
            )

    distinct = len(set(round(v, 4) for v in observed.values() if v == v))
    detail["distinct_radius_count"] = distinct
    if distinct < 2:
        errors.append(
            f"root-level variant switch produced only {distinct} distinct "
            f"radius value(s) across {len(observed)} modes -- cascade is NOT "
            "reaching the descendant atom (this is exactly the /World "
            "no-op regression)"
        )

    return TestResult("test_assembly_cascade_changes_atom_radius",
                       len(errors) == 0, errors, detail)


def test_trajectory_cascade_changes_bond_visibility(path: str) -> TestResult:
    """Independently-derived expectation: the Bond_* Cylinder is part of the
    'ballstick' representation only (templates/04_create_assembly.py's own
    bonds_vset cascade authors Cylinder visibility=invisible in every mode
    except ballstick). If the root-level switch on /ABLComplex genuinely
    cascades, that must be reflected in ComputeVisibility() for a bond
    reached only through defaultPrim's own descendant subtree."""
    errors: list[str] = []
    detail: dict = {}
    stage = _fresh(path)

    default_prim = stage.GetDefaultPrim()
    vset = default_prim.GetVariantSets().GetVariantSet("representation")
    bond = stage.GetPrimAtPath(_SAMPLE_BOND_PATH)
    if not bond.IsValid():
        errors.append(f"{_SAMPLE_BOND_PATH} not found")
        return TestResult("test_trajectory_cascade_changes_bond_visibility",
                           False, errors, detail)

    per_mode_vis = {}
    for mode in sorted(_EXPECTED_VARIANTS):
        vset.SetVariantSelection(mode)
        vis = UsdGeom.Imageable(bond).ComputeVisibility()
        per_mode_vis[mode] = str(vis)

    detail["per_mode_visibility"] = per_mode_vis

    if per_mode_vis.get("ballstick") != UsdGeom.Tokens.inherited:
        errors.append(
            f"mode=ballstick: expected Bond Cylinder visibility="
            f"{UsdGeom.Tokens.inherited!r}, got {per_mode_vis.get('ballstick')!r}"
        )
    for mode in _EXPECTED_VARIANTS - {"ballstick"}:
        if per_mode_vis.get(mode) != UsdGeom.Tokens.invisible:
            errors.append(
                f"mode={mode}: expected Bond Cylinder visibility="
                f"{UsdGeom.Tokens.invisible!r} (variant-gated), got "
                f"{per_mode_vis.get(mode)!r} -- if this stays 'inherited' in "
                "every mode the root selection is not cascading (the /World "
                "no-op regression)"
            )

    distinct = len(set(per_mode_vis.values()))
    detail["distinct_visibility_count"] = distinct
    if distinct < 2:
        errors.append(
            f"root-level variant switch produced only {distinct} distinct "
            "bond-visibility outcome(s) across all modes -- cascade is not "
            "reaching the descendant bond"
        )

    return TestResult("test_trajectory_cascade_changes_bond_visibility",
                       len(errors) == 0, errors, detail)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run() -> list[TestResult]:
    results: list[TestResult] = []

    for path, label in [(_ASSEMBLY_DEMO_PATH, "assembly_demo"),
                         (_TRAJECTORY_DEMO_PATH, "trajectory_demo")]:
        if not os.path.isfile(path):
            results.append(TestResult(f"file_exists[{label}]", False,
                                       [f"File not found: {path}"]))
            continue
        results.append(test_no_decorative_world_prim(path, label))

    if os.path.isfile(_ASSEMBLY_DEMO_PATH):
        results.append(test_root_selection_on_default_prim(
            _ASSEMBLY_DEMO_PATH, "assembly_demo", "balls"))
        results.append(test_assembly_cascade_changes_atom_radius(_ASSEMBLY_DEMO_PATH))

    if os.path.isfile(_TRAJECTORY_DEMO_PATH):
        results.append(test_root_selection_on_default_prim(
            _TRAJECTORY_DEMO_PATH, "trajectory_demo", "points"))
        results.append(test_trajectory_cascade_changes_bond_visibility(
            _TRAJECTORY_DEMO_PATH))

    return results


if __name__ == "__main__":
    results = run()

    all_passed = True
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {result.name}")
        if result.detail:
            for k, v in result.detail.items():
                print(f"         {k} = {v}")
        for err in result.errors:
            print(f"         ERROR: {err}")
        if not result.passed:
            all_passed = False
        print()

    total = len(results)
    passed_count = sum(1 for r in results if r.passed)
    failed_count = total - passed_count

    if all_passed:
        print(f"ALL PASS ({passed_count}/{total})")
        sys.exit(0)
    else:
        print(f"FAILED ({failed_count}/{total} failed)")
        sys.exit(1)
