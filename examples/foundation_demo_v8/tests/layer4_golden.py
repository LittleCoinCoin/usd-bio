"""
Layer 4 — golden/baseline diffing.

Compares key attribute values from committed .usda artifacts against the
small hand-authored reference fixtures in tests/fixtures/. Targeted
key-attribute diffing is used rather than full-file diffing because:
  - Full-file diffing is fragile (timestamps, precision rounding change it)
  - Targeted fixtures are stable and document the intent explicitly

Three fixture checks:
  1. fixture_carbon_element.usda — /_class_/C prim attributes
     (bio:vdwRadius, bio:symbol) verified against assembly_demo.usda.
  2. fixture_atom_inherit.usda — atom prim inherit arc (bio:element = "C",
     inherits = /_class_/C) verified against first carbon atom in assembly.
  3. fixture_representation_variants.usda — representation VariantSet has
     all 4 canonical variants (points, balls, vdw, ballstick) verified
     against assembly_demo.usda (which has the correct set, unlike
     element_grid_demo.usda which has 'sticks' instead of 'ballstick').

All comparisons use the uv CPython 3.11 pxr interpreter — never usdcat/grep.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

try:
    from pxr import Usd, Sdf
except ImportError as exc:
    raise ImportError(
        "pxr not importable. Run under the OpenUSD Python interpreter "
        "with load_env.sh sourced."
    ) from exc


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

@dataclass
class GoldenResult:
    """Result of one golden fixture comparison."""
    fixture_path: str
    artifact_path: str
    check_name: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Individual golden checks
# ---------------------------------------------------------------------------

def _check_carbon_element(fixture_dir: str, output_dir: str) -> GoldenResult:
    """
    fixture_carbon_element.usda defines /_class_/C with expected attributes.
    Verify that the same prim in assembly_demo.usda matches on:
      - bio:vdwRadius = 1.7 (float, ±0.001)
      - bio:symbol = "C" (token)

    [source: tests/fixtures/fixture_carbon_element.usda]
    [source: examples/foundation_demo_v8/output/assembly_demo.usda via sublayer chain]
    """
    fixture_path = os.path.join(fixture_dir, "fixture_carbon_element.usda")
    artifact_path = os.path.join(output_dir, "assembly_demo.usda")
    errors: list[str] = []
    detail: dict = {}

    # Load the fixture to get expected values
    fixture_stage = Usd.Stage.Open(fixture_path)
    fixture_c = fixture_stage.GetPrimAtPath("/_class_/C")
    if not fixture_c.IsValid():
        errors.append(f"fixture: /_class_/C not found in {fixture_path}")
        return GoldenResult(
            fixture_path=fixture_path,
            artifact_path=artifact_path,
            check_name="carbon_element_fixture",
            passed=False,
            errors=errors,
        )

    expected_vdw = float(fixture_c.GetAttribute("bio:vdwRadius").Get())
    expected_symbol = str(fixture_c.GetAttribute("bio:symbol").Get())
    detail["fixture_vdwRadius"] = expected_vdw
    detail["fixture_symbol"] = expected_symbol

    # Load the artifact
    artifact_stage = Usd.Stage.Open(artifact_path)
    artifact_c = artifact_stage.GetPrimAtPath("/_class_/C")
    if not artifact_c.IsValid():
        errors.append(f"artifact: /_class_/C not found in {artifact_path}")
        return GoldenResult(
            fixture_path=fixture_path,
            artifact_path=artifact_path,
            check_name="carbon_element_fixture",
            passed=False,
            errors=errors,
            detail=detail,
        )

    # Compare bio:vdwRadius
    actual_vdw_attr = artifact_c.GetAttribute("bio:vdwRadius")
    if not actual_vdw_attr.IsValid() or actual_vdw_attr.Get() is None:
        errors.append(f"artifact: bio:vdwRadius missing on /_class_/C")
    else:
        actual_vdw = float(actual_vdw_attr.Get())
        detail["artifact_vdwRadius"] = actual_vdw
        if abs(actual_vdw - expected_vdw) > 0.001:
            errors.append(
                f"bio:vdwRadius mismatch: artifact={actual_vdw:.4f}, "
                f"fixture={expected_vdw:.4f}"
            )

    # Compare bio:symbol
    actual_sym_attr = artifact_c.GetAttribute("bio:symbol")
    if not actual_sym_attr.IsValid() or actual_sym_attr.Get() is None:
        errors.append(f"artifact: bio:symbol missing on /_class_/C")
    else:
        actual_sym = str(actual_sym_attr.Get())
        detail["artifact_symbol"] = actual_sym
        if actual_sym != expected_symbol:
            errors.append(
                f"bio:symbol mismatch: artifact='{actual_sym}', "
                f"fixture='{expected_symbol}'"
            )

    return GoldenResult(
        fixture_path=fixture_path,
        artifact_path=artifact_path,
        check_name="carbon_element_fixture",
        passed=len(errors) == 0,
        errors=errors,
        detail=detail,
    )


def _check_atom_inherit(fixture_dir: str, output_dir: str) -> GoldenResult:
    """
    fixture_atom_inherit.usda defines an atom with bio:element = "C" and
    inherits = /_class_/C. Verify the first carbon atom in assembly_demo.usda
    matches the same structural contract.

    [source: tests/fixtures/fixture_atom_inherit.usda]
    [source: examples/foundation_demo_v8/output/assembly_demo.usda]
    """
    fixture_path = os.path.join(fixture_dir, "fixture_atom_inherit.usda")
    artifact_path = os.path.join(output_dir, "assembly_demo.usda")
    errors: list[str] = []
    detail: dict = {}

    # Load fixture to extract expected structural contract
    fixture_stage = Usd.Stage.Open(fixture_path)
    fixture_atom = fixture_stage.GetPrimAtPath("/TestResidue/C_alpha")
    if not fixture_atom.IsValid():
        errors.append(f"fixture: /TestResidue/C_alpha not found in {fixture_path}")
        return GoldenResult(
            fixture_path=fixture_path,
            artifact_path=artifact_path,
            check_name="atom_inherit_fixture",
            passed=False,
            errors=errors,
        )

    expected_element = str(fixture_atom.GetAttribute("bio:element").Get())
    expected_inherit = "/_class_/C"
    detail["fixture_element"] = expected_element
    detail["fixture_expected_inherit"] = expected_inherit

    # Load artifact: find first carbon atom
    artifact_stage = Usd.Stage.Open(artifact_path)
    carbon_atom = None
    for prim in artifact_stage.Traverse():
        elem_attr = prim.GetAttribute("bio:element")
        if elem_attr.IsValid() and str(elem_attr.Get()) == "C":
            carbon_atom = prim
            break

    if carbon_atom is None:
        errors.append(f"artifact: no carbon atom found in {artifact_path}")
        return GoldenResult(
            fixture_path=fixture_path,
            artifact_path=artifact_path,
            check_name="atom_inherit_fixture",
            passed=False,
            errors=errors,
            detail=detail,
        )

    detail["artifact_atom_path"] = str(carbon_atom.GetPath())

    # Compare bio:element
    actual_element = str(carbon_atom.GetAttribute("bio:element").Get())
    detail["artifact_element"] = actual_element
    if actual_element != expected_element:
        errors.append(
            f"bio:element mismatch: artifact='{actual_element}', "
            f"fixture='{expected_element}'"
        )

    # Compare inherit arc
    actual_inherits = [
        str(p) for p in carbon_atom.GetInherits().GetAllDirectInherits()
    ]
    detail["artifact_inherits"] = actual_inherits
    if expected_inherit not in actual_inherits:
        errors.append(
            f"inherit arc mismatch: artifact inherits={actual_inherits}, "
            f"fixture expects {expected_inherit}"
        )

    return GoldenResult(
        fixture_path=fixture_path,
        artifact_path=artifact_path,
        check_name="atom_inherit_fixture",
        passed=len(errors) == 0,
        errors=errors,
        detail=detail,
    )


def _check_representation_variants(fixture_dir: str, output_dir: str) -> GoldenResult:
    """
    fixture_representation_variants.usda defines a prim with all 4 canonical
    representation variants. Verify assembly_demo.usda's ABLComplex prim
    has the same variant names.

    Note: element_grid_demo.usda has 'sticks' instead of 'ballstick' — this
    check targets assembly_demo.usda which has the correct convention.

    [source: tests/fixtures/fixture_representation_variants.usda]
    [source: examples/foundation_demo_v8/output/assembly_demo.usda]
    """
    fixture_path = os.path.join(fixture_dir, "fixture_representation_variants.usda")
    artifact_path = os.path.join(output_dir, "assembly_demo.usda")
    errors: list[str] = []
    findings: list[str] = []
    detail: dict = {}

    # Load fixture to extract expected variant names
    fixture_stage = Usd.Stage.Open(fixture_path)
    fixture_prim = fixture_stage.GetPrimAtPath("/TestPrim")
    if not fixture_prim.IsValid():
        errors.append(f"fixture: /TestPrim not found in {fixture_path}")
        return GoldenResult(
            fixture_path=fixture_path,
            artifact_path=artifact_path,
            check_name="representation_variants_fixture",
            passed=False,
            errors=errors,
        )

    fixture_vs = fixture_prim.GetVariantSets().GetVariantSet("representation")
    expected_variants = frozenset(fixture_vs.GetVariantNames())
    detail["fixture_variants"] = sorted(expected_variants)

    # Load artifact: check ABLComplex (top-level assembly prim)
    artifact_stage = Usd.Stage.Open(artifact_path)
    abl_prim = artifact_stage.GetPrimAtPath("/ABLComplex")
    if not abl_prim.IsValid():
        errors.append(f"artifact: /ABLComplex not found in {artifact_path}")
        return GoldenResult(
            fixture_path=fixture_path,
            artifact_path=artifact_path,
            check_name="representation_variants_fixture",
            passed=False,
            errors=errors,
            detail=detail,
        )

    artifact_vs = abl_prim.GetVariantSets().GetVariantSet("representation")
    actual_variants = frozenset(artifact_vs.GetVariantNames())
    detail["artifact_variants"] = sorted(actual_variants)

    missing = expected_variants - actual_variants
    extra = actual_variants - expected_variants

    if missing:
        errors.append(
            f"assembly_demo /ABLComplex missing variants={sorted(missing)} "
            f"relative to fixture (fixture has: {sorted(expected_variants)})"
        )
    if extra:
        findings.append(
            f"assembly_demo /ABLComplex has extra variants={sorted(extra)} "
            "not in fixture (may be intentional)"
        )

    # Also probe element_grid_demo.usda for the known 'sticks' finding
    grid_path = os.path.join(output_dir, "element_grid_demo.usda")
    if os.path.isfile(grid_path):
        grid_stage = Usd.Stage.Open(grid_path)
        for prim in grid_stage.Traverse():
            vs_names = prim.GetVariantSets().GetNames()
            if "representation" not in vs_names:
                continue
            vs = prim.GetVariantSets().GetVariantSet("representation")
            grid_variants = frozenset(vs.GetVariantNames())
            if "sticks" in grid_variants and "ballstick" not in grid_variants:
                findings.append(
                    f"FINDING: element_grid_demo.usda {prim.GetPath()} has 'sticks' "
                    "instead of 'ballstick' — naming inconsistency with CLAUDE.md convention"
                )
                break  # report once

    return GoldenResult(
        fixture_path=fixture_path,
        artifact_path=artifact_path,
        check_name="representation_variants_fixture",
        passed=len(errors) == 0,
        errors=errors,
        findings=findings,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(output_dir: str, fixture_dir: str) -> list[GoldenResult]:
    """
    Run all golden fixture comparisons.

    Parameters
    ----------
    output_dir : str
        Path to the output/ directory containing committed .usda artifacts.
    fixture_dir : str
        Path to the tests/fixtures/ directory containing hand-authored fixtures.

    Returns
    -------
    list of GoldenResult
        One result per fixture check.
    """
    results: list[GoldenResult] = []
    results.append(_check_carbon_element(fixture_dir, output_dir))
    results.append(_check_atom_inherit(fixture_dir, output_dir))
    results.append(_check_representation_variants(fixture_dir, output_dir))
    return results
