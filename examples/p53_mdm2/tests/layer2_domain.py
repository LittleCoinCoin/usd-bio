"""
Layer 2 -- biological domain-invariant validators.

Encodes biology-specific structural invariants as programmatic checks against
the committed topology artifact, catching USD-valid-but-biologically-malformed
stages that usdchecker cannot detect. Source-of-truth for element symbols is
imported from ``p53_mdm2.data`` -- NOT from any generator's in-memory state
(anti-tautology).

Invariants:
  1. atom_invariant     -- every atom prim carries a non-empty bio:element that
                           names a known element symbol AND inherits
                           /_class_/<symbol>.
  2. element_class      -- every /_class_/<symbol> prim has bio:vdwRadius > 0
                           and an authored bio:cpkColor.
  3. representation     -- every prim with a "representation" VariantSet has all
                           four canonical variants.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

try:
    from pxr import Usd, Sdf
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pxr not importable. Run under the OpenUSD Python interpreter "
        "with load_env.sh sourced."
    ) from exc

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from p53_mdm2.data import ELEMENTS  # source of truth
from p53_mdm2 import p53_env

EXPECTED_REPRESENTATION_VARIANTS = frozenset(p53_env.DEFAULT_REPRESENTATIONS)
_KNOWN_SYMBOLS = frozenset(ELEMENTS.keys())


@dataclass
class DomainResult:
    check_name: str
    passed: bool
    errors: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)


def _is_atom_prim(prim) -> bool:
    if not prim.IsValid() or prim.GetTypeName() not in ("Xform", ""):
        return False
    attr = prim.GetAttribute("bio:element")
    return attr.IsValid() and attr.Get() is not None


def check_atom_invariant(stage) -> DomainResult:
    errors, checked = [], 0
    for prim in stage.Traverse():
        if not _is_atom_prim(prim):
            continue
        checked += 1
        path = str(prim.GetPath())
        symbol = prim.GetAttribute("bio:element").Get()
        if not symbol:
            errors.append(f"{path}: bio:element empty")
            continue
        symbol = str(symbol)
        if symbol not in _KNOWN_SYMBOLS:
            errors.append(f"{path}: bio:element='{symbol}' not a known symbol")
        inherits = [str(p) for p in prim.GetInherits().GetAllDirectInherits()]
        if f"/_class_/{symbol}" not in inherits:
            errors.append(f"{path}: missing inherit /_class_/{symbol}; got {inherits}")
    return DomainResult("atom_invariant", not errors, errors, {"atoms_checked": checked})


def check_element_class_invariant(stage) -> DomainResult:
    errors, checked = [], 0
    class_children = [
        p for p in stage.TraverseAll()
        if p.GetPath().GetParentPath() == Sdf.Path("/_class_")
    ]
    for child in class_children:
        checked += 1
        path = str(child.GetPath())
        vdw = child.GetAttribute("bio:vdwRadius")
        if not vdw.IsValid() or vdw.Get() is None:
            errors.append(f"{path}: bio:vdwRadius missing")
        elif vdw.Get() <= 0:
            errors.append(f"{path}: bio:vdwRadius={vdw.Get()} not > 0")
        cpk = child.GetAttribute("bio:cpkColor")
        if not cpk.IsValid() or cpk.Get() is None:
            errors.append(f"{path}: bio:cpkColor not authored")
    return DomainResult(
        "element_class_invariant", not errors, errors, {"classes_checked": checked})


def check_representation_invariant(stage) -> DomainResult:
    errors, checked = [], 0
    for prim in stage.Traverse():
        if "representation" not in prim.GetVariantSets().GetNames():
            continue
        checked += 1
        vs = prim.GetVariantSets().GetVariantSet("representation")
        actual = frozenset(vs.GetVariantNames())
        missing = EXPECTED_REPRESENTATION_VARIANTS - actual
        if missing:
            errors.append(
                f"{prim.GetPath()}: representation missing {sorted(missing)}; "
                f"got {sorted(actual)}")
    return DomainResult(
        "representation_invariant", not errors, errors, {"prims_checked": checked})


def run(stage_path: str) -> list:
    """Run all domain invariants against a single stage path."""
    if not os.path.isfile(stage_path):
        return [DomainResult("file_exists", False, [f"File not found: {stage_path}"])]
    stage = Usd.Stage.Open(stage_path)
    return [
        check_atom_invariant(stage),
        check_element_class_invariant(stage),
        check_representation_invariant(stage),
    ]
