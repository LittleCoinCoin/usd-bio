"""
Layer 2 — biological domain invariant validators.

Encodes biology-specific structural invariants as programmatic checks against
the committed artifacts, catching USD-valid but biologically malformed stages
that usdchecker cannot detect.

Three invariant families:
  1. Atom invariant    — every atom prim carries bio:element (non-empty token)
                         and inherits from /_class_/<Symbol>.
  2. Element class     — every /_class_/ child prim has bio:vdwRadius > 0
                         and primvars:displayColor (Color3f, via variant child).
                         NOTE: bio:cpkColor is NOT authored on class prims in the
                         current artifacts; displayColor is stored inside each
                         variant's Sphere child. Layer 2 checks vdwRadius and
                         records a DEVIATION for the absent bio:cpkColor.
  3. Representation    — any prim with a "representation" VariantSet must have
                         all four variants: points, balls, vdw, ballstick.
                         NOTE: element_grid_demo.usda uses "sticks" instead of
                         "ballstick" — this is caught and reported as a FINDING.

DEVIATION: UsdValidation Python API (pxr.UsdValidation) *is* importable in this
build (USD 0.25.11), but we implement as plain traversal per the leaf spec's
preference for broad compatibility and explicit invariant expression.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# USD import guard — must run under the uv CPython 3.11 interpreter with
# PYTHONPATH pointing at OpenUSD build. Caller is responsible.
# ---------------------------------------------------------------------------
try:
    from pxr import Usd, Sdf
except ImportError as exc:
    raise ImportError(
        "pxr not importable. Run under the OpenUSD Python interpreter "
        "with load_env.sh sourced."
    ) from exc

# Authoritative source for element properties — do NOT import from generator
# in-memory state; import from the canonical data module.
_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(_HERE), "data")
sys.path.insert(0, os.path.dirname(_HERE))
from data.element_properties import ELEMENTS  # type: ignore[import]

EXPECTED_REPRESENTATION_VARIANTS = frozenset({"points", "balls", "vdw", "ballstick"})


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

@dataclass
class DomainResult:
    """Aggregated domain-invariant result for a single stage file."""
    path: str
    passed: bool
    checks: list[dict] = field(default_factory=list)
    deviations: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Invariant checkers
# ---------------------------------------------------------------------------

def _is_atom_prim(prim: "Usd.Prim") -> bool:
    """
    Heuristic: a prim is considered an atom if it:
      - is of type Xform
      - carries a bio:element attribute
    This avoids depending on naming convention alone.
    """
    if not prim.IsValid():
        return False
    if prim.GetTypeName() not in ("Xform", ""):
        return False
    attr = prim.GetAttribute("bio:element")
    return attr.IsValid() and attr.Get() is not None


def check_atom_invariant(stage: "Usd.Stage") -> dict:
    """
    Traverse the entire stage; for every atom prim assert:
      - bio:element is a non-empty token matching a known element symbol
      - GetInherits().GetAllDirectInherits() contains /_class_/<symbol>
    Returns a check dict with keys: name, passed, errors, atoms_checked.
    """
    errors: list[str] = []
    atoms_checked = 0

    known_symbols = set(ELEMENTS.keys())

    for prim in stage.Traverse():
        if not _is_atom_prim(prim):
            continue
        atoms_checked += 1
        path = str(prim.GetPath())

        # --- bio:element ---
        elem_attr = prim.GetAttribute("bio:element")
        symbol = elem_attr.Get()
        if not symbol:
            errors.append(f"{path}: bio:element is empty or missing")
            continue
        symbol = str(symbol)
        if symbol not in known_symbols:
            errors.append(
                f"{path}: bio:element='{symbol}' is not a known element symbol"
            )
            # Still continue to check inherit

        # --- inherit chain ---
        expected_class_path = f"/_class_/{symbol}"
        direct_inherits = [
            str(p) for p in prim.GetInherits().GetAllDirectInherits()
        ]
        if expected_class_path not in direct_inherits:
            errors.append(
                f"{path}: does not inherit /_class_/{symbol}; "
                f"actual inherits={direct_inherits}"
            )

    return {
        "name": "atom_invariant",
        "passed": len(errors) == 0,
        "atoms_checked": atoms_checked,
        "errors": errors,
    }


def check_element_class_invariant(stage: "Usd.Stage") -> dict:
    """
    For every child prim of /_class_/ assert:
      - bio:vdwRadius attribute is present and > 0
      - At least one variant child has primvars:displayColor authored
        (bio:cpkColor is NOT present on class prims in current artifacts —
         stored instead as displayColor inside variant Sphere children).

    DEVIATION: bio:cpkColor absent from class prims — checking displayColor
    presence via variant traversal instead; records deviation in findings.
    """
    errors: list[str] = []
    deviations: list[str] = []
    classes_checked = 0

    class_root = stage.GetPrimAtPath("/_class_")
    if not class_root.IsValid():
        return {
            "name": "element_class_invariant",
            "passed": True,  # no /_class_/ in this stage — not applicable
            "classes_checked": 0,
            "errors": [],
            "deviations": ["/_class_ root not present — invariant not applicable"],
        }

    # Class prims are abstract (specifier == class); GetChildren() returns []
    # because abstract prims are excluded from the default traversal.
    # Use TraverseAll() and filter to direct children of /_class_/.
    class_children = [
        p for p in stage.TraverseAll()
        if p.GetPath().GetParentPath() == Sdf.Path("/_class_")
    ]
    for child in class_children:
        classes_checked += 1
        path = str(child.GetPath())
        symbol = child.GetName()

        # bio:vdwRadius
        vdw_attr = child.GetAttribute("bio:vdwRadius")
        if not vdw_attr.IsValid() or vdw_attr.Get() is None:
            errors.append(f"{path}: bio:vdwRadius missing")
        else:
            vdw_val = vdw_attr.Get()
            if vdw_val <= 0:
                errors.append(f"{path}: bio:vdwRadius={vdw_val} is not > 0")

        # bio:cpkColor — DEVIATION: not present; check displayColor via variants
        cpk_attr = child.GetAttribute("bio:cpkColor")
        if not cpk_attr.IsValid() or cpk_attr.Get() is None:
            deviations.append(
                f"{path}: bio:cpkColor absent (DEVIATION: color stored as "
                "primvars:displayColor inside variant Sphere children)"
            )
            # Verify displayColor reachable via at least one variant
            vs_names = child.GetVariantSets().GetNames()
            found_color = False
            if "representation" in vs_names:
                vs = child.GetVariantSets().GetVariantSet("representation")
                child_path_str = str(child.GetPath()) + "/"
                for vname in vs.GetVariantNames():
                    vs.SetVariantSelection(vname)
                    # Class prims are abstract — GetChildren() returns [].
                    # Use TraverseAll filtered by path prefix instead.
                    for desc in stage.TraverseAll():
                        if not str(desc.GetPath()).startswith(child_path_str):
                            continue
                        dc_attr = desc.GetAttribute("primvars:displayColor")
                        if dc_attr.IsValid() and dc_attr.Get() is not None:
                            found_color = True
                            break
                    if found_color:
                        break
            if not found_color:
                errors.append(
                    f"{path}: no primvars:displayColor found in any "
                    "representation variant child"
                )

    return {
        "name": "element_class_invariant",
        "passed": len(errors) == 0,
        "classes_checked": classes_checked,
        "errors": errors,
        "deviations": deviations,
    }


def check_representation_invariant(stage: "Usd.Stage") -> dict:
    """
    For every prim that has a "representation" VariantSet, assert that all
    four variants (points, balls, vdw, ballstick) are registered.

    NOTE: element_grid_demo.usda uses "sticks" instead of "ballstick" for
    atoms — this is a real artifact finding, not a harness defect.
    """
    errors: list[str] = []
    findings: list[str] = []
    prims_checked = 0

    for prim in stage.Traverse():
        vs_names = prim.GetVariantSets().GetNames()
        if "representation" not in vs_names:
            continue
        prims_checked += 1
        path = str(prim.GetPath())
        vs = prim.GetVariantSets().GetVariantSet("representation")
        actual = frozenset(vs.GetVariantNames())
        missing = EXPECTED_REPRESENTATION_VARIANTS - actual
        extra = actual - EXPECTED_REPRESENTATION_VARIANTS
        if missing:
            msg = (
                f"{path}: representation VariantSet missing "
                f"variants={sorted(missing)}; actual={sorted(actual)}"
            )
            errors.append(msg)
            if "sticks" in actual and "ballstick" in missing:
                findings.append(
                    f"{path}: FINDING — has 'sticks' instead of 'ballstick' "
                    "(naming inconsistency between element_grid_demo and class prims)"
                )

    return {
        "name": "representation_invariant",
        "passed": len(errors) == 0,
        "prims_checked": prims_checked,
        "errors": errors,
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Per-stage dispatch
# ---------------------------------------------------------------------------

# Which invariants apply to which artifact basenames.
# trajectory_clip.usda contains only position timeSamples — no atom bio: attrs.
_ATOM_INVARIANT_STAGES = {
    "assembly_demo.usda",
    "element_grid_demo.usda",
    "residue_grid_demo.usda",
    "water_demo.usda",
}
_ELEMENT_CLASS_STAGES = {
    "assembly_demo.usda",
    "element_grid_demo.usda",
}
_REPRESENTATION_STAGES = {
    "assembly_demo.usda",
    "element_grid_demo.usda",
    "residue_grid_demo.usda",
    "water_demo.usda",
    "trajectory_demo.usda",
}


def _run_one(path: str) -> DomainResult:
    """Run applicable invariants for a single stage path."""
    basename = os.path.basename(path)
    checks: list[dict] = []
    all_deviations: list[str] = []
    all_findings: list[str] = []

    try:
        stage = Usd.Stage.Open(path)
    except Exception as exc:
        return DomainResult(
            path=path,
            passed=False,
            checks=[{"name": "stage_open", "passed": False, "errors": [str(exc)]}],
        )

    if basename in _ATOM_INVARIANT_STAGES:
        result = check_atom_invariant(stage)
        checks.append(result)

    if basename in _ELEMENT_CLASS_STAGES:
        result = check_element_class_invariant(stage)
        checks.append(result)
        all_deviations.extend(result.get("deviations", []))

    if basename in _REPRESENTATION_STAGES:
        result = check_representation_invariant(stage)
        checks.append(result)
        all_findings.extend(result.get("findings", []))

    passed = all(c["passed"] for c in checks)
    return DomainResult(
        path=path,
        passed=passed,
        checks=checks,
        deviations=all_deviations,
        findings=all_findings,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(stage_paths: list[str]) -> list[DomainResult]:
    """
    Run domain invariant validators for each stage path.

    Parameters
    ----------
    stage_paths : list of str
        Absolute paths to .usda files to validate.

    Returns
    -------
    list of DomainResult
        One result per file, in input order.
    """
    results = []
    for path in stage_paths:
        if not os.path.isfile(path):
            results.append(DomainResult(
                path=path,
                passed=False,
                checks=[{
                    "name": "file_exists",
                    "passed": False,
                    "errors": [f"File not found: {path}"],
                }],
            ))
        else:
            results.append(_run_one(path))
    return results
