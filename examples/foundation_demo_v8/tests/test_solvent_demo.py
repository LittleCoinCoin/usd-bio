#!/usr/bin/env python3
"""
Read-back tests for output/solvent_demo.usda.

Opens the committed artifact FRESH with Usd.Stage.Open() and asserts every
structural and compositional invariant required by the pointinstancer_solvent
leaf spec.  No generator code is in scope — all expected values are derived
from the source PDB data or from the committed leaf spec.

Success Gates (from leaf):
  1. /SolvatedComplex/Solvent is a UsdGeomPointInstancer prim.
  2. positions primvar length >= 61,000 (WAT oxygen atoms in PDB).
  3. protoIndices length == positions length.
  4. /SolvatedComplex/Protein/Chain_A exists (protein hierarchy present).
  5. representation VariantSet with points/balls/vdw/ballstick on /SolvatedComplex/Solvent.

FINDING note: The domain layer (layer2_domain.py) check_atom_invariant traverses
all prims looking for bio:element. The PointInstancer /SolvatedComplex/Solvent has
no bio:element attributes (it uses positions/protoIndices, not per-atom Xforms),
so it is correctly excluded by _is_atom_prim(). No false-positive expected.

Standalone: run as __main__; exits non-zero on any failure.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# USD import guard
# ---------------------------------------------------------------------------
try:
    from pxr import Usd, UsdGeom, Sdf
except ImportError as exc:
    raise ImportError(
        "pxr not importable. Run under the OpenUSD Python interpreter "
        "with load_env.sh sourced."
    ) from exc

# ---------------------------------------------------------------------------
# Path setup — locate solvent_demo.usda relative to this test file
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_DEMO_ROOT = os.path.dirname(_HERE)
_SOLVENT_DEMO_PATH = os.path.join(_DEMO_ROOT, "output", "solvent_demo.usda")

# Minimum expected water molecule count — source: ShinobuLab PDB WAT oxygen atoms
_MIN_WATER_COUNT = 61_000

# Canonical representation variants per CLAUDE.md and leaf spec
_EXPECTED_VARIANTS = frozenset({"points", "balls", "vdw", "ballstick"})


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class TestResult:
    """Result of a single read-back test function."""
    name: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Test 1: PointInstancer present
# ---------------------------------------------------------------------------

def test_pointinstancer_exists(stage: Usd.Stage) -> TestResult:
    """
    Assert /SolvatedComplex/Solvent is a UsdGeomPointInstancer prim.

    [source: output/solvent_demo.usda — composed from solvent_instancer.usda sublayer]
    """
    errors: list[str] = []
    detail: dict = {}

    prim = stage.GetPrimAtPath("/SolvatedComplex/Solvent")
    detail["prim_valid"] = prim.IsValid()
    detail["prim_type"] = prim.GetTypeName() if prim.IsValid() else "N/A"

    if not prim.IsValid():
        errors.append("/SolvatedComplex/Solvent prim does not exist in stage")
        return TestResult(name="test_pointinstancer_exists", passed=False,
                          errors=errors, detail=detail)

    # UsdGeomPointInstancer resolves iff the prim type is PointInstancer
    instancer = UsdGeom.PointInstancer(prim)
    detail["instancer_valid"] = bool(instancer)

    if not instancer:
        errors.append(
            f"/SolvatedComplex/Solvent is type '{prim.GetTypeName()}', "
            "expected PointInstancer. "
            "(Likely cause: a Define() call overrode the type from the sublayer.)"
        )

    return TestResult(name="test_pointinstancer_exists",
                      passed=len(errors) == 0,
                      errors=errors, detail=detail)


# ---------------------------------------------------------------------------
# Test 2: Water count
# ---------------------------------------------------------------------------

def test_water_count(stage: Usd.Stage) -> TestResult:
    """
    Assert positions primvar length >= 61,000 AND protoIndices length == positions length.

    [source: WAT oxygen count in $USDBIO_DATA_DIR/files/atp-complex-solv35.pdb]
    [source: pointinstancer_solvent.md leaf spec Success Gates]
    """
    errors: list[str] = []
    detail: dict = {}

    prim = stage.GetPrimAtPath("/SolvatedComplex/Solvent")
    if not prim.IsValid():
        errors.append("/SolvatedComplex/Solvent prim not found — cannot check water count")
        return TestResult(name="test_water_count", passed=False,
                          errors=errors, detail=detail)

    # Positions — read via attribute directly (works even if type is overridden)
    pos_attr = prim.GetAttribute("positions")
    positions = pos_attr.Get() if pos_attr.IsValid() else None
    pos_len = len(positions) if positions is not None else 0
    detail["positions_length"] = pos_len

    if positions is None:
        errors.append("/SolvatedComplex/Solvent: 'positions' attribute missing or empty")
    elif pos_len < _MIN_WATER_COUNT:
        errors.append(
            f"/SolvatedComplex/Solvent: positions length={pos_len} < "
            f"expected >= {_MIN_WATER_COUNT} "
            "(anti-tautology: expected count from leaf spec Success Gate, "
            "not from generator in-memory state)"
        )

    # protoIndices
    proto_attr = prim.GetAttribute("protoIndices")
    proto_indices = proto_attr.Get() if proto_attr.IsValid() else None
    proto_len = len(proto_indices) if proto_indices is not None else 0
    detail["proto_indices_length"] = proto_len

    if proto_indices is None:
        errors.append("/SolvatedComplex/Solvent: 'protoIndices' attribute missing or empty")
    elif proto_len != pos_len:
        errors.append(
            f"/SolvatedComplex/Solvent: protoIndices length={proto_len} != "
            f"positions length={pos_len} (must be equal per UsdGeomPointInstancer spec)"
        )

    return TestResult(name="test_water_count",
                      passed=len(errors) == 0,
                      errors=errors, detail=detail)


# ---------------------------------------------------------------------------
# Test 3: Protein hierarchy
# ---------------------------------------------------------------------------

def test_protein_hierarchy(stage: Usd.Stage) -> TestResult:
    """
    Assert /SolvatedComplex/Protein/Chain_A exists (protein subtree present).

    [source: output/solvent_demo.usda — composed from abl_kinase_complex.usda sublayer]
    [source: pointinstancer_solvent.md leaf spec Success Gate: 4,676 protein atoms]
    """
    errors: list[str] = []
    detail: dict = {}

    protein_prim = stage.GetPrimAtPath("/SolvatedComplex/Protein")
    detail["protein_valid"] = protein_prim.IsValid()

    if not protein_prim.IsValid():
        errors.append("/SolvatedComplex/Protein prim not found")
        return TestResult(name="test_protein_hierarchy", passed=False,
                          errors=errors, detail=detail)

    chain_a = stage.GetPrimAtPath("/SolvatedComplex/Protein/Chain_A")
    detail["chain_a_valid"] = chain_a.IsValid()

    if not chain_a.IsValid():
        errors.append(
            "/SolvatedComplex/Protein/Chain_A not found — "
            "protein reference may not have resolved correctly"
        )

    # Spot-check: first ACE residue should be present
    ace_1 = stage.GetPrimAtPath("/SolvatedComplex/Protein/Chain_A/ACE_1")
    detail["ace_1_valid"] = ace_1.IsValid()
    if not ace_1.IsValid():
        errors.append(
            "/SolvatedComplex/Protein/Chain_A/ACE_1 not found — "
            "protein per-atom hierarchy did not compose correctly"
        )

    return TestResult(name="test_protein_hierarchy",
                      passed=len(errors) == 0,
                      errors=errors, detail=detail)


# ---------------------------------------------------------------------------
# Test 4: Representation variants
# ---------------------------------------------------------------------------

def test_representation_variants(stage: Usd.Stage) -> TestResult:
    """
    Assert representation VariantSet with all 4 canonical variants
    (points, balls, vdw, ballstick) exists on /SolvatedComplex/Solvent.

    [source: CLAUDE.md canonical representation variants]
    [source: pointinstancer_solvent.md leaf spec Step 2 Implementation Logic]
    """
    errors: list[str] = []
    detail: dict = {}

    prim = stage.GetPrimAtPath("/SolvatedComplex/Solvent")
    if not prim.IsValid():
        errors.append("/SolvatedComplex/Solvent prim not found — cannot check variants")
        return TestResult(name="test_representation_variants", passed=False,
                          errors=errors, detail=detail)

    vs_names = prim.GetVariantSets().GetNames()
    detail["variant_set_names"] = vs_names

    if "representation" not in vs_names:
        errors.append(
            "/SolvatedComplex/Solvent: 'representation' VariantSet not found. "
            f"VariantSets present: {vs_names}"
        )
        return TestResult(name="test_representation_variants", passed=False,
                          errors=errors, detail=detail)

    vs = prim.GetVariantSets().GetVariantSet("representation")
    actual_variants = frozenset(vs.GetVariantNames())
    detail["actual_variants"] = sorted(actual_variants)
    detail["expected_variants"] = sorted(_EXPECTED_VARIANTS)

    missing = _EXPECTED_VARIANTS - actual_variants
    extra = actual_variants - _EXPECTED_VARIANTS

    if missing:
        errors.append(
            f"/SolvatedComplex/Solvent: representation VariantSet missing variants: "
            f"{sorted(missing)} "
            "(anti-tautology: expected variants from CLAUDE.md, not generator state)"
        )
    if extra:
        # Extra variants are a FINDING, not a failure
        detail["extra_variants"] = sorted(extra)

    return TestResult(name="test_representation_variants",
                      passed=len(errors) == 0,
                      errors=errors, detail=detail)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run(solvent_demo_path: str | None = None) -> list[TestResult]:
    """Run all four read-back tests.

    Parameters
    ----------
    solvent_demo_path : str or None
        Path to solvent_demo.usda. Defaults to output/solvent_demo.usda relative
        to this test file's parent directory.

    Returns
    -------
    list of TestResult
    """
    path = solvent_demo_path or _SOLVENT_DEMO_PATH

    results: list[TestResult] = []

    if not os.path.isfile(path):
        missing = TestResult(
            name="solvent_demo_file_exists",
            passed=False,
            errors=[f"File not found: {path}"],
        )
        results.append(missing)
        return results

    stage = Usd.Stage.Open(path)

    results.append(test_pointinstancer_exists(stage))
    results.append(test_water_count(stage))
    results.append(test_protein_hierarchy(stage))
    results.append(test_representation_variants(stage))

    return results


# ---------------------------------------------------------------------------
# __main__ entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Read-back tests for output/solvent_demo.usda"
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Path to solvent_demo.usda (default: output/solvent_demo.usda)",
    )
    args = parser.parse_args()

    path = args.path or _SOLVENT_DEMO_PATH
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
