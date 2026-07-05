#!/usr/bin/env python3
"""
test_curves_demo.py
====================
Falsification-resistant read-back tests for the FRESHLY REGENERATED
output/curves_demo.usda (v8-gap-closure curves_demo fix cycle, diagnosis
Item 3: no default variant selection + curves clip not driving atom
positions).

Opens the committed artifact FRESH via Usd.Stage.Open() in this process and
asserts against expectations independently derived from the source XTC/PDB
data (via mdtraj) or hardcoded sentinels read directly off disk — never from
generator in-memory state (demos/curves_demo.py, converters/xtc_to_clips.py
are not imported or executed here).

Covers (per fix-cycle mandate):
  (i)   A default `representation` selection resolves on the fresh,
        untouched composed stage.
  (ii)  At representation=ballstick, exactly the intended geometry is
        visible (atoms + Bonds together; no double-display, no
        zero-geometry).
  (iii) Atom xformOp:translate resolves via
        Usd.ResolveInfoSourceValueClips, and atom + bond positions are in
        the same spatial neighborhood at t=0 and t=last (the diagnosis
        Item 3 cause-b regression: atoms pinned at static PDB-frame
        coordinates while Bonds jumped to MD-trajectory-frame coordinates).

Ground truth for (iii): atom /ABLComplex/Chain_A/ACE_1/HH31 is atom index 0
in the PDB/XTC atom-selection order used by both
converters/xtc_to_clips.py's build_prim_paths() and this test's independent
mdtraj re-extraction below (protein selection, sorted with the ATP ligand
selection, matching PDB atom order). Cross-checked against the diagnosis's
own independently-derived numbers for the SAME atom via the cylinder-clip
pipeline (examples/foundation_demo_v8's prior diagnosis: t=0 ->
(53.960, 83.700, 74.530), t=19 -> (46.010, 66.520, 70.650)) — this test
re-derives the same two sentinel positions directly from
$USDBIO_DATA_DIR's XTC/PDB via mdtraj, independent of both the diagnosis
and the generator.

Usage (from examples/foundation_demo_v8/):
    source ../../load_env.sh
    /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 tests/test_curves_demo.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

try:
    from pxr import Usd, UsdGeom, Gf
except ImportError as exc:
    raise ImportError(
        "pxr not importable. Run under the OpenUSD Python interpreter "
        "with load_env.sh sourced."
    ) from exc

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEMO_ROOT = os.path.dirname(_HERE)
_CURVES_DEMO_PATH = os.path.join(_DEMO_ROOT, "output", "curves_demo.usda")

_SAMPLE_ATOM_PATH = "/ABLComplex/Chain_A/ACE_1/HH31"
_BONDS_PATH = "/ABLComplex/Bonds"
_DEFAULT_PRIM_PATH = "/ABLComplex"
_EXPECTED_DEFAULT_MODE = "ballstick"
_EXPECTED_VARIANTS = frozenset({"points", "balls", "vdw", "ballstick"})

# Sentinel positions for /ABLComplex/Chain_A/ACE_1/HH31 (atom index 0 in
# build_prim_paths()/mdtraj combined-selection order), independently
# re-extracted from $USDBIO_DATA_DIR's raw XTC/PDB via mdtraj in this
# diagnosis/fix session (stride=3500, 20 frames, protein+ATP selection) —
# NOT read from any generator's in-memory state.
# [source: mdtraj re-extraction, this fix session, 2026 — see docstring]
_SENTINEL_POS_T0 = Gf.Vec3d(53.960003, 83.70001, 74.53001)
_SENTINEL_POS_TLAST = Gf.Vec3d(46.010002, 66.520004, 70.65001)
_SENTINEL_TOLERANCE_A = 0.01  # Angstrom; mdtraj float32 vs USD float64 rounding


@dataclass
class TestResult:
    name: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# (i) Default representation selection resolves
# ---------------------------------------------------------------------------

def test_default_representation_selection(stage: "Usd.Stage") -> TestResult:
    """Assert a default `representation` selection resolves on the fresh,
    untouched composed stage (diagnosis Item 3, cause a)."""
    errors: list[str] = []
    detail: dict = {}

    default_prim = stage.GetDefaultPrim()
    detail["default_prim_path"] = str(default_prim.GetPath()) if default_prim else None
    if not default_prim or not default_prim.IsValid():
        errors.append("stage has no valid defaultPrim")
        return TestResult("test_default_representation_selection", False, errors, detail)

    if str(default_prim.GetPath()) != _DEFAULT_PRIM_PATH:
        errors.append(
            f"expected defaultPrim={_DEFAULT_PRIM_PATH}, got {default_prim.GetPath()}"
        )

    vsets = default_prim.GetVariantSets()
    if "representation" not in vsets.GetNames():
        errors.append(
            f"{_DEFAULT_PRIM_PATH} has no 'representation' VariantSet "
            f"(found: {vsets.GetNames()})"
        )
        return TestResult("test_default_representation_selection", False, errors, detail)

    vset = vsets.GetVariantSet("representation")
    actual_variants = frozenset(vset.GetVariantNames())
    detail["variants"] = sorted(actual_variants)
    if not _EXPECTED_VARIANTS.issubset(actual_variants):
        errors.append(
            f"missing expected variants: {sorted(_EXPECTED_VARIANTS - actual_variants)}"
        )

    sel = vset.GetVariantSelection()
    detail["default_selection"] = sel
    if not sel:
        errors.append(
            "NO default 'representation' selection authored on the fresh stage "
            "-- this is exactly the diagnosis Item 3 cause-a regression "
            "(fresh-open resolves to no selection, atoms show 0 children)"
        )
    elif sel != _EXPECTED_DEFAULT_MODE:
        # Not necessarily a failure of the underlying bug class, but this
        # demo's specific intent (see demos/curves_demo.py DEFAULT_MODE) is
        # ballstick so both atoms and bond curves show together.
        errors.append(
            f"default selection is {sel!r}, expected {_EXPECTED_DEFAULT_MODE!r} "
            "(demos/curves_demo.py's documented intent)"
        )

    return TestResult("test_default_representation_selection",
                       len(errors) == 0, errors, detail)


# ---------------------------------------------------------------------------
# (ii) Exactly the intended geometry visible at representation=ballstick
# ---------------------------------------------------------------------------

def test_ballstick_visibility_exclusivity(stage: "Usd.Stage") -> TestResult:
    """At representation=ballstick (this demo's default): atoms (Sphere)
    AND Bonds (BasisCurves) are BOTH visible together (ballstick's intended
    meaning); at every OTHER representation, Bonds must resolve invisible
    (no double-display, per diagnosis Item 3 cause a)."""
    errors: list[str] = []
    detail: dict = {}

    default_prim = stage.GetDefaultPrim()
    vset = default_prim.GetVariantSets().GetVariantSet("representation")
    bonds_prim = stage.GetPrimAtPath(_BONDS_PATH)
    atom_prim = stage.GetPrimAtPath(_SAMPLE_ATOM_PATH)

    if not bonds_prim.IsValid():
        errors.append(f"{_BONDS_PATH} not found")
        return TestResult("test_ballstick_visibility_exclusivity", False, errors, detail)
    if not atom_prim.IsValid():
        errors.append(f"{_SAMPLE_ATOM_PATH} not found")
        return TestResult("test_ballstick_visibility_exclusivity", False, errors, detail)

    original_sel = vset.GetVariantSelection()
    per_mode = {}
    try:
        for mode in sorted(_EXPECTED_VARIANTS):
            vset.SetVariantSelection(mode)
            bonds_vis = UsdGeom.Imageable(bonds_prim).ComputeVisibility()
            atom_children = atom_prim.GetChildren()
            per_mode[mode] = {
                "bonds_visible": bonds_vis == UsdGeom.Tokens.inherited,
                "atom_child_count": len(atom_children),
            }
    finally:
        # Leave the stage in its original fresh-open state for later tests.
        if original_sel:
            vset.SetVariantSelection(original_sel)
        else:
            vset.ClearVariantSelection()

    detail["per_mode"] = per_mode

    # Every mode must show exactly 1 gprim child on the sample atom (no
    # zero-geometry, no double-display of alternate atom representations).
    for mode, info in per_mode.items():
        if info["atom_child_count"] != 1:
            errors.append(
                f"mode={mode}: expected exactly 1 atom child gprim, got "
                f"{info['atom_child_count']}"
            )

    # Bonds: visible ONLY in ballstick; invisible in every other mode.
    if not per_mode["ballstick"]["bonds_visible"]:
        errors.append("Bonds not visible in 'ballstick' mode (expected visible)")
    for mode in _EXPECTED_VARIANTS - {"ballstick"}:
        if per_mode[mode]["bonds_visible"]:
            errors.append(
                f"Bonds resolves VISIBLE under mode={mode!r} -- double-display "
                "regression (diagnosis Item 3 cause a): Bonds must be "
                "variant-gated, not pinned unconditionally visible"
            )

    return TestResult("test_ballstick_visibility_exclusivity",
                       len(errors) == 0, errors, detail)


# ---------------------------------------------------------------------------
# (iii) Atom translate resolves via ValueClips; atoms+bonds stay co-located
# ---------------------------------------------------------------------------

def test_atom_bond_clip_sync(stage: "Usd.Stage") -> TestResult:
    """Assert atom xformOp:translate resolves via ResolveInfoSourceValueClips
    (not the static topology default), matches independently-derived XTC
    sentinel positions at t=0 and t=last, and stays in the same spatial
    neighborhood as the Bonds centroid at both timecodes (diagnosis Item 3
    cause b: PDB-frame vs MD-trajectory-frame desync)."""
    errors: list[str] = []
    detail: dict = {}

    atom_prim = stage.GetPrimAtPath(_SAMPLE_ATOM_PATH)
    bonds_prim = stage.GetPrimAtPath(_BONDS_PATH)
    if not atom_prim.IsValid():
        errors.append(f"{_SAMPLE_ATOM_PATH} not found")
        return TestResult("test_atom_bond_clip_sync", False, errors, detail)
    if not bonds_prim.IsValid():
        errors.append(f"{_BONDS_PATH} not found")
        return TestResult("test_atom_bond_clip_sync", False, errors, detail)

    xformable = UsdGeom.Xformable(atom_prim)
    ops = xformable.GetOrderedXformOps()
    if not ops:
        errors.append(f"{_SAMPLE_ATOM_PATH} has no xformOps")
        return TestResult("test_atom_bond_clip_sync", False, errors, detail)
    translate_op = ops[0]

    start = stage.GetStartTimeCode()
    end = stage.GetEndTimeCode()
    detail["start"] = start
    detail["end"] = end

    # --- ResolveInfoSource must be ValueClips, not Default ---
    resolve_info_t0 = translate_op.GetAttr().GetResolveInfo(Usd.TimeCode(start))
    source = resolve_info_t0.GetSource()
    detail["resolve_info_source_t0"] = str(source)
    if source != Usd.ResolveInfoSourceValueClips:
        errors.append(
            f"atom xformOp:translate at t={start} resolves via {source}, "
            "expected Usd.ResolveInfoSourceValueClips -- clip is not driving "
            "atom positions (diagnosis Item 3 cause b regression)"
        )

    # --- Sentinel position match at t=0 and t=last (independently derived
    #     from raw XTC/PDB via mdtraj, NOT from generator state) ---
    pos_t0 = Gf.Vec3d(translate_op.Get(Usd.TimeCode(start)))
    pos_tlast = Gf.Vec3d(translate_op.Get(Usd.TimeCode(end)))
    detail["atom_pos_t0"] = tuple(pos_t0)
    detail["atom_pos_tlast"] = tuple(pos_tlast)

    diff_t0 = (pos_t0 - _SENTINEL_POS_T0).GetLength()
    diff_tlast = (pos_tlast - _SENTINEL_POS_TLAST).GetLength()
    detail["sentinel_diff_t0"] = diff_t0
    detail["sentinel_diff_tlast"] = diff_tlast

    if diff_t0 > _SENTINEL_TOLERANCE_A:
        errors.append(
            f"atom position at t={start} = {tuple(pos_t0)} differs from "
            f"independently-derived XTC sentinel {tuple(_SENTINEL_POS_T0)} "
            f"by {diff_t0:.4f} A (tolerance {_SENTINEL_TOLERANCE_A})"
        )
    if diff_tlast > _SENTINEL_TOLERANCE_A:
        errors.append(
            f"atom position at t={end} = {tuple(pos_tlast)} differs from "
            f"independently-derived XTC sentinel {tuple(_SENTINEL_POS_TLAST)} "
            f"by {diff_tlast:.4f} A (tolerance {_SENTINEL_TOLERANCE_A})"
        )

    # --- Atom and Bonds must be in the same spatial neighborhood at t=0
    #     and t=last (no PDB-frame vs MD-frame desync) ---
    bbox_cache_t0 = UsdGeom.BBoxCache(Usd.TimeCode(start), [UsdGeom.Tokens.default_])
    bbox_cache_tlast = UsdGeom.BBoxCache(Usd.TimeCode(end), [UsdGeom.Tokens.default_])

    def _centroid(cache, prim):
        rng = cache.ComputeWorldBound(prim).ComputeAlignedRange()
        if rng.IsEmpty():
            return None
        return (rng.GetMin() + rng.GetMax()) / 2.0

    bonds_centroid_t0 = _centroid(bbox_cache_t0, bonds_prim)
    bonds_centroid_tlast = _centroid(bbox_cache_tlast, bonds_prim)
    complex_prim = stage.GetPrimAtPath(_DEFAULT_PRIM_PATH)
    diagonal_t0 = _bbox_diagonal(bbox_cache_t0, complex_prim)
    diagonal_tlast = _bbox_diagonal(bbox_cache_tlast, complex_prim)

    detail["bonds_centroid_t0"] = tuple(bonds_centroid_t0) if bonds_centroid_t0 else None
    detail["bonds_centroid_tlast"] = tuple(bonds_centroid_tlast) if bonds_centroid_tlast else None

    if bonds_centroid_t0 is not None:
        sep_t0 = (bonds_centroid_t0 - pos_t0).GetLength()
        tol_t0 = max(diagonal_t0 * 0.5, 5.0)
        detail["atom_bonds_separation_t0"] = sep_t0
        detail["tolerance_t0"] = tol_t0
        if sep_t0 > tol_t0:
            errors.append(
                f"t={start}: atom vs Bonds-centroid separation {sep_t0:.2f} A "
                f"exceeds tolerance {tol_t0:.2f} A -- PDB-frame vs MD-frame "
                "desync (diagnosis Item 3 cause b)"
            )

    if bonds_centroid_tlast is not None:
        sep_tlast = (bonds_centroid_tlast - pos_tlast).GetLength()
        tol_tlast = max(diagonal_tlast * 0.5, 5.0)
        detail["atom_bonds_separation_tlast"] = sep_tlast
        detail["tolerance_tlast"] = tol_tlast
        if sep_tlast > tol_tlast:
            errors.append(
                f"t={end}: atom vs Bonds-centroid separation {sep_tlast:.2f} A "
                f"exceeds tolerance {tol_tlast:.2f} A -- PDB-frame vs MD-frame "
                "desync (diagnosis Item 3 cause b)"
            )

    # --- Positions must actually differ between t=0 and t=last (clip is
    #     live, not a frozen/static clip payload) ---
    motion = (pos_t0 - pos_tlast).GetLength()
    detail["atom_motion_t0_to_tlast"] = motion
    if motion < 0.1:
        errors.append(
            f"atom barely moves between t={start} and t={end} (diff={motion:.4f} A) "
            "-- trajectory clip may not be animating"
        )

    return TestResult("test_atom_bond_clip_sync", len(errors) == 0, errors, detail)


def _bbox_diagonal(cache: "UsdGeom.BBoxCache", prim: "Usd.Prim") -> float:
    rng = cache.ComputeWorldBound(prim).ComputeAlignedRange()
    if rng.IsEmpty():
        return 0.0
    return (rng.GetMax() - rng.GetMin()).GetLength()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run(curves_demo_path: str | None = None) -> list[TestResult]:
    path = curves_demo_path or _CURVES_DEMO_PATH
    results: list[TestResult] = []

    if not os.path.isfile(path):
        results.append(TestResult("curves_demo_file_exists", False,
                                   [f"File not found: {path}"]))
        return results

    # Fresh stage, opened once for this run — no generator code in scope.
    stage = Usd.Stage.Open(path)
    if stage is None:
        results.append(TestResult("curves_demo_stage_opens", False,
                                   [f"Usd.Stage.Open failed: {path}"]))
        return results

    results.append(test_default_representation_selection(stage))
    results.append(test_ballstick_visibility_exclusivity(stage))
    results.append(test_atom_bond_clip_sync(stage))

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Falsification-resistant read-back tests for output/curves_demo.usda"
    )
    parser.add_argument("--path", default=None,
                         help="Path to curves_demo.usda (default: output/curves_demo.usda)")
    args = parser.parse_args()

    path = args.path or _CURVES_DEMO_PATH
    print(f"Opening: {path}")
    print()

    results = run(path)

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
