"""test_specializes_arc.py — Step 3 of specializes_arc leaf.

Read-back tests for the cross-reference specializes_arc demonstration.
Opens specializes_demo.usda (outer/root layer, which references
asset_specializes.usda) fresh — no generator state in scope — and asserts
the TRUE observed resolved values demonstrating the real contrast between
Specializes and Inherits arcs.

## Scene construction (two-layer, cross-reference)

INNER ASSET (asset_specializes.usda):
  /_class_/AtomBase       — base class: bio:vdwRadius=1.70, bio:charge=0.0
  /World/Atom_Specializes — specializes AtomBase, local bio:vdwRadius=9.99
  /World/Atom_Inherits    — inherits AtomBase,    local bio:vdwRadius=9.99
  (neither child has a local opinion on bio:charge)

OUTER ROOT (specializes_demo.usda):
  References asset at /World
  Overrides /_class_/AtomBase: bio:vdwRadius=2.00, bio:charge=-1.0

## Flat single-file finding (documented from prior pass: commits cd7b1ea/a117222/f0832f7)

In a single-file context, Local (L) is the strongest LIVERPS arc, so BOTH
Inherits and Specializes prims resolve to the local opinion (9.99). There is
NO observable contrast between the two arc types in a flat single-layer file.
The cross-reference boundary is what reveals the difference.
[source: context7 /websites/openusd_release — LIVERPS glossary]
[assumption: confirmed empirically in prior pass build_specializes_demo.py run]

## The REAL contrast (cross-reference context, empirically verified)

bio:vdwRadius (both child prims have LOCAL opinion 9.99 in inner asset):

  Atom_Specializes -> 9.99  LOCAL WINS
    The specialized prim's own local opinions ALWAYS override the base prim.
    Specializes is the WEAKEST arc in LIVERPS. The referenced-layer local
    opinion is stronger than the Specializes arc resolving from the outer base.
    [source: context7 /websites/openusd_release — Specializes glossary:
     'opinions expressed directly on the specialized prim always override
      those on the base prim, regardless of the referencing context.']

  Atom_Inherits -> 2.00  BASE OVERRIDE WINS
    Inherits (I) is STRONGER than References (R) in LIVERPS (I > R > S).
    The outer-layer opinion on the inherited class propagates through the
    reference boundary, overriding the referenced-layer local opinion (9.99).
    [source: context7 /websites/openusd_release — LIVERPS glossary,
     PcpArcType enum (PcpArcTypeInherit < PcpArcTypeReference in strength order)]

bio:charge (neither child has a local opinion):
  Both -> -1.0  (outer base override propagates to both; no local opinion to block it)

## Does this meet the leaf goal?

YES, with an important clarification:
  The leaf spec originally expected Specializes to show base-wins and Inherits to
  show local-wins. The empirically correct behavior is the REVERSE:
    - Inherits shows "outer base override wins over referenced-layer local" (I > R)
    - Specializes shows "local always wins over base" (L > S regardless of referencing)
  This IS the correct Specializes vs Inherits contrast — it is just the opposite of
  the original spec's assumption. The honest demonstration is documented here.
  [assumption: the leaf spec's predicted direction was incorrect; empirical behavior
   documented above is the ground truth]

## API confirmed via context7 /websites/openusd_release
  - Usd.Stage.Open(path) — open stage fresh
  - prim.GetAttribute(name).Get() — sample composed attribute value
  - stage.GetCompositionErrors() — check for composition faults

Usage (from repo root):
    . ./load_env.sh
    /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 \\
        tests/composition_advanced/test_specializes_arc.py
"""

import math
import os
import sys

from pxr import Usd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Inner asset (single-file flat context tests)
_ASSET = os.path.join(
    _REPO_ROOT,
    "examples", "composition_advanced", "specializes_arc", "asset_specializes.usda",
)

# Outer demo (cross-reference contrast tests)
_DEMO = os.path.join(
    _REPO_ROOT,
    "examples", "composition_advanced", "specializes_arc", "specializes_demo.usda",
)

# Prim paths
_BASE_PATH = "/_class_/AtomBase"
_SPECIALIZES_PATH = "/World/Atom_Specializes"
_INHERITS_PATH = "/World/Atom_Inherits"

# Float tolerance
_TOL = 1e-2


def _approx_eq(a: float, b: float) -> bool:
    return math.isclose(a, b, abs_tol=_TOL)


# ---------------------------------------------------------------------------
# Test 1: Flat single-file — both prims resolve local opinion (no contrast)
# ---------------------------------------------------------------------------

def test_flat_both_local_wins() -> None:
    """In the inner asset alone (single-file), both prims resolve local 9.99.

    Flat single-file finding (prior pass, commits cd7b1ea/a117222/f0832f7):
    Local (L) is the strongest LIVERPS arc, so BOTH Inherits and Specializes
    resolve to the local opinion. No observable contrast in this context.

    TRUE OBSERVED VALUES (single-file): both 9.99.
    [source: context7 /websites/openusd_release — LIVERPS: Local is strongest]
    [assumption: confirmed empirically in prior pass]
    """
    stage = Usd.Stage.Open(_ASSET)
    errors = stage.GetCompositionErrors()
    assert not errors, f"Unexpected composition errors in asset: {errors}"

    spe = stage.GetPrimAtPath(_SPECIALIZES_PATH)
    inh = stage.GetPrimAtPath(_INHERITS_PATH)
    assert spe.IsValid(), f"Prim not found: {_SPECIALIZES_PATH}"
    assert inh.IsValid(), f"Prim not found: {_INHERITS_PATH}"

    spe_r = spe.GetAttribute("bio:vdwRadius").Get()
    inh_r = inh.GetAttribute("bio:vdwRadius").Get()

    assert spe_r is not None, f"{_SPECIALIZES_PATH} bio:vdwRadius returned None"
    assert inh_r is not None, f"{_INHERITS_PATH} bio:vdwRadius returned None"

    # Both local opinions win in single-file context.
    # [source: context7 LIVERPS — Local is strongest arc]
    assert _approx_eq(spe_r, 9.99), (
        f"FAIL test_flat_both_local_wins: Specializes expected ~9.99 (local), got {spe_r}"
    )
    assert _approx_eq(inh_r, 9.99), (
        f"FAIL test_flat_both_local_wins: Inherits expected ~9.99 (local), got {inh_r}"
    )
    print(
        f"[PASS] test_flat_both_local_wins: "
        f"Specializes={spe_r:.4f}, Inherits={inh_r:.4f} (both local 9.99 in single-file)"
    )


# ---------------------------------------------------------------------------
# Test 2: Cross-reference — Specializes local wins (9.99)
# ---------------------------------------------------------------------------

def test_xref_specializes_local_wins() -> None:
    """In the cross-reference context (demo references asset), Specializes prim
    resolves its LOCAL opinion (9.99), NOT the outer base override (2.00).

    The specialized prim's own local opinions ALWAYS override the base prim.
    Specializes is the WEAKEST arc (S is last in LIVERPS). The referenced-layer
    local opinion is stronger than the outer Specializes-arc base override.

    TRUE OBSERVED VALUE: 9.99 (local wins).
    [source: context7 /websites/openusd_release — Specializes glossary:
     'opinions expressed directly on the specialized prim always override
      those on the base prim, regardless of the referencing context.']
    [source: empirical — build_specializes_demo.py run output]
    """
    stage = Usd.Stage.Open(_DEMO)
    errors = stage.GetCompositionErrors()
    assert not errors, f"Unexpected composition errors in demo: {errors}"

    prim = stage.GetPrimAtPath(_SPECIALIZES_PATH)
    assert prim.IsValid(), f"Prim not found: {_SPECIALIZES_PATH}"

    val = prim.GetAttribute("bio:vdwRadius").Get()
    assert val is not None, f"{_SPECIALIZES_PATH} bio:vdwRadius returned None"

    # Specialized prim's local (9.99) wins over outer base override (2.00).
    # This is the fundamental property of the Specializes arc.
    assert _approx_eq(val, 9.99), (
        f"FAIL test_xref_specializes_local_wins: "
        f"expected ~9.99 (local), got {val}. "
        f"Specialized prim's local opinion should always override base."
    )
    print(
        f"[PASS] test_xref_specializes_local_wins: "
        f"{_SPECIALIZES_PATH} bio:vdwRadius = {val:.4f} "
        f"(local 9.99 wins over outer base 2.00)"
    )


# ---------------------------------------------------------------------------
# Test 3: Cross-reference — Inherits base override wins (2.00)
# ---------------------------------------------------------------------------

def test_xref_inherits_base_wins() -> None:
    """In the cross-reference context (demo references asset), Inherits prim
    resolves the OUTER BASE OVERRIDE (2.00), NOT its local opinion (9.99).

    Inherits (I) is STRONGER than References (R) in LIVERPS (I > R > S).
    The outer-layer opinion on the inherited class propagates through the
    reference boundary and overrides the referenced-layer local opinion (9.99).

    TRUE OBSERVED VALUE: 2.00 (outer base override wins via Inherits arc).
    [source: context7 /websites/openusd_release — LIVERPS: Inherits > References]
    [source: context7 /websites/openusd_release — PcpArcType enum:
     PcpArcTypeInherit listed before PcpArcTypeReference (stronger first)]
    [source: empirical — build_specializes_demo.py run output]
    """
    stage = Usd.Stage.Open(_DEMO)
    errors = stage.GetCompositionErrors()
    assert not errors, f"Unexpected composition errors in demo: {errors}"

    prim = stage.GetPrimAtPath(_INHERITS_PATH)
    assert prim.IsValid(), f"Prim not found: {_INHERITS_PATH}"

    val = prim.GetAttribute("bio:vdwRadius").Get()
    assert val is not None, f"{_INHERITS_PATH} bio:vdwRadius returned None"

    # Outer-layer base class override (2.00) wins via Inherits arc (I > R in LIVERPS).
    # This contrasts with Specializes where the local always wins.
    assert _approx_eq(val, 2.00), (
        f"FAIL test_xref_inherits_base_wins: "
        f"expected ~2.00 (outer base override via Inherits), got {val}. "
        f"Inherits > References in LIVERPS — outer class opinion should propagate."
    )
    print(
        f"[PASS] test_xref_inherits_base_wins: "
        f"{_INHERITS_PATH} bio:vdwRadius = {val:.4f} "
        f"(outer base override 2.00 wins over referenced-layer local 9.99)"
    )


# ---------------------------------------------------------------------------
# Test 4: Cross-reference — charge (no local opinion) propagates to both
# ---------------------------------------------------------------------------

def test_xref_no_local_propagates_to_both() -> None:
    """For bio:charge (no local opinion on either child), the outer base
    override (-1.0) propagates to BOTH Specializes and Inherits prims.

    When neither child prim has a local opinion, both arc types allow the
    base class value to propagate freely.

    TRUE OBSERVED VALUE: both -1.0.
    [source: context7 /websites/openusd_release — Specializes glossary:
     local opinions override base; absence of local opinion means base wins]
    [source: empirical — build_specializes_demo.py run output]
    """
    stage = Usd.Stage.Open(_DEMO)
    errors = stage.GetCompositionErrors()
    assert not errors, f"Unexpected composition errors in demo: {errors}"

    spe = stage.GetPrimAtPath(_SPECIALIZES_PATH)
    inh = stage.GetPrimAtPath(_INHERITS_PATH)

    spe_c = spe.GetAttribute("bio:charge").Get()
    inh_c = inh.GetAttribute("bio:charge").Get()

    assert spe_c is not None, f"{_SPECIALIZES_PATH} bio:charge returned None"
    assert inh_c is not None, f"{_INHERITS_PATH} bio:charge returned None"

    # No local opinion -> outer base override propagates to both.
    assert _approx_eq(spe_c, -1.0), (
        f"FAIL test_xref_no_local_propagates_to_both: "
        f"Specializes bio:charge expected ~-1.00, got {spe_c}"
    )
    assert _approx_eq(inh_c, -1.0), (
        f"FAIL test_xref_no_local_propagates_to_both: "
        f"Inherits bio:charge expected ~-1.00, got {inh_c}"
    )
    print(
        f"[PASS] test_xref_no_local_propagates_to_both: "
        f"Specializes bio:charge={spe_c:.4f}, Inherits bio:charge={inh_c:.4f} "
        f"(both -1.0; no local to block base override)"
    )


# ---------------------------------------------------------------------------
# Test 5: Base class reads correctly in root layer
# ---------------------------------------------------------------------------

def test_xref_base_class_values() -> None:
    """Assert /_class_/AtomBase resolves the root-layer override values.

    The root layer (specializes_demo.usda) authors an 'over' on /_class_/AtomBase:
      bio:vdwRadius = 2.00
      bio:charge    = -1.0

    TRUE OBSERVED VALUES: 2.00, -1.0.
    [source: empirical — build_specializes_demo.py]
    """
    stage = Usd.Stage.Open(_DEMO)

    base = stage.GetPrimAtPath(_BASE_PATH)
    assert base.IsValid(), f"Prim not found: {_BASE_PATH}"

    r = base.GetAttribute("bio:vdwRadius").Get()
    c = base.GetAttribute("bio:charge").Get()

    assert _approx_eq(r, 2.00), (
        f"FAIL test_xref_base_class_values: bio:vdwRadius expected ~2.00, got {r}"
    )
    assert _approx_eq(c, -1.0), (
        f"FAIL test_xref_base_class_values: bio:charge expected ~-1.00, got {c}"
    )
    print(
        f"[PASS] test_xref_base_class_values: "
        f"AtomBase bio:vdwRadius={r:.4f}, bio:charge={c:.4f} "
        f"(root-layer override: 2.00, -1.0)"
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Inner asset: {_ASSET}")
    print(f"Outer demo:  {_DEMO}")
    print()

    tests = [
        test_flat_both_local_wins,
        test_xref_specializes_local_wins,
        test_xref_inherits_base_wins,
        test_xref_no_local_propagates_to_both,
        test_xref_base_class_values,
    ]

    failures = []
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            print(f"[FAIL] {t.__name__}: {exc}")
            failures.append(t.__name__)
        except Exception as exc:
            print(f"[ERROR] {t.__name__}: {exc}")
            failures.append(t.__name__)

    print()
    if failures:
        print(f"FAILED: {len(failures)}/{len(tests)} — {failures}")
        sys.exit(1)
    else:
        print(f"PASSED: {len(tests)}/{len(tests)}")
        sys.exit(0)


if __name__ == "__main__":
    main()
