"""test_specializes_arc.py — Step 3 of specializes_arc leaf.

Read-back tests for specializes_demo.usda: opens the stage fresh (no
generator state in scope) and asserts the TRUE observed resolved values
for the Inherits vs Specializes arc contrast.

## FINDING: single-file context — both prims resolve local opinion

The leaf spec and architecture doc claim that Specializes prim should resolve
the base-class value (1.70), not the local override (9.99). This claim is
WRONG for a single-file context.

Context7 /websites/openusd_release (PcpArcType enum + Specializes glossary)
confirms:
  LIVERPS = Local > Inherits > VariantSets > Relocates > References >
            Payload > Specializes
  Specializes glossary: "opinions expressed directly on the specialized prim
  always override those on the base prim, regardless of the referencing
  context."

This means in a single-file (flat, one layer) context:
  - /World/Atom_Inherits: local 9.99 wins over inherited 1.70 -> 9.99
  - /World/Atom_Specializes: local 9.99 wins over specialized 1.70 -> 9.99

The Specializes arc's distinctive "base overrides instance" behavior only
manifests when the specialized prim is REFERENCED INTO another layer from
a third layer that also specializes from the base. In the single-file demo
the specialized prim IS the instance — so local opinions always dominate.

For the base-update propagation test (leaf spec step 4): after setting
/_class_/AtomBase.bio:vdwRadius = 2.00 in-session, BOTH prims still
resolve 9.99. Their local opinions override the base whether the arc is
Inherits or Specializes (in single-file context). Calling stage.Reload()
afterwards discards the in-memory edit (reverting base to 1.70) — prims
stay at 9.99.

These tests assert the TRUE observed behavior. They do NOT match the leaf
spec's predicted values (which assumed cross-reference boundary semantics).
Falsification note: if any assertion below fails it is a real failure; do
not weaken them to pass.

[source: context7 /websites/openusd_release — PcpArcType enum,
 Specializes glossary entry, LIVERPS glossary entry]
[source: empirical observation — build_specializes_demo.py run output,
 plus direct in-process test below]

API confirmed via context7 /websites/openusd_release:
  - Usd.Stage.Open(path) — open stage fresh
  - prim.GetAttribute(name).Get() — sample composed attribute
  - stage.GetCompositionErrors() — check for composition faults

Usage (from repo root):
    . ./load_env.sh
    /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 \\
        tests/composition_advanced/test_specializes_arc.py
"""

import math
import os
import sys

from pxr import Sdf, Usd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_USDA = os.path.join(
    _REPO_ROOT,
    "examples", "composition_advanced", "specializes_arc", "specializes_demo.usda",
)

_BASE_PATH = "/_class_/AtomBase"
_INHERITS_PATH = "/World/Atom_Inherits"
_SPECIALIZES_PATH = "/World/Atom_Specializes"

# ---------------------------------------------------------------------------
# Float tolerance
# ---------------------------------------------------------------------------
_TOL = 1e-3


def _approx_eq(a: float, b: float) -> bool:
    return math.isclose(a, b, abs_tol=_TOL)


# ---------------------------------------------------------------------------
# Test 1: Inherits prim — local opinion wins
# ---------------------------------------------------------------------------

def test_inherits_local_wins() -> None:
    """Assert /World/Atom_Inherits resolves the local override (9.99), not the base (1.70).

    Under LIVERPS, Local (L) is stronger than Inherits (I). The atom prim has
    a local opinion bio:vdwRadius = 9.99, so 9.99 wins.
    [source: context7 /websites/openusd_release — LIVERPS glossary entry]
    """
    stage = Usd.Stage.Open(_USDA)
    errors = stage.GetCompositionErrors()
    assert not errors, f"Unexpected composition errors: {errors}"

    prim = stage.GetPrimAtPath(_INHERITS_PATH)
    assert prim.IsValid(), f"Prim not found: {_INHERITS_PATH}"

    val = prim.GetAttribute("bio:vdwRadius").Get()
    assert val is not None, f"{_INHERITS_PATH} bio:vdwRadius returned None"
    # TRUE OBSERVED VALUE: local 9.99 wins over inherited 1.70.
    # [source: context7 LIVERPS — Local > Inherits; empirical run]
    assert _approx_eq(val, 9.99), (
        f"FAIL test_inherits_local_wins: expected ~9.99, got {val}. "
        f"Local opinion should win over Inherits in LIVERPS."
    )
    print(f"[PASS] test_inherits_local_wins: {_INHERITS_PATH} bio:vdwRadius = {val:.4f} (~9.99)")


# ---------------------------------------------------------------------------
# Test 2: Specializes prim — local opinion wins (single-file context)
# ---------------------------------------------------------------------------

def test_specializes_local_wins_single_file() -> None:
    """Assert /World/Atom_Specializes resolves 9.99, NOT 1.70, in single-file context.

    FINDING: this contradicts the leaf spec's prediction (1.70).

    The leaf spec claimed Specializes prim should resolve 1.70 (base wins).
    This is incorrect for a single-file context. The official USD docs state:
    "opinions expressed directly on the specialized prim always override those
    on the base prim, regardless of the referencing context."
    [source: context7 /websites/openusd_release — Specializes glossary entry]

    In a flat single-layer file the prim's own local attribute IS the direct
    opinion on the specialized prim, so it always overrides the base.
    The base-wins behaviour only manifests when the scene is embedded inside
    a referencing layer and a third layer inherits from the base — at that
    point Specializes causes the base update to propagate THROUGH the
    reference boundary, overriding the inner-layer local opinion seen from
    the outer layer's perspective.

    TRUE OBSERVED VALUE: 9.99 (local wins, identical to Inherits in single-file).
    """
    stage = Usd.Stage.Open(_USDA)
    errors = stage.GetCompositionErrors()
    assert not errors, f"Unexpected composition errors: {errors}"

    prim = stage.GetPrimAtPath(_SPECIALIZES_PATH)
    assert prim.IsValid(), f"Prim not found: {_SPECIALIZES_PATH}"

    val = prim.GetAttribute("bio:vdwRadius").Get()
    assert val is not None, f"{_SPECIALIZES_PATH} bio:vdwRadius returned None"
    # TRUE OBSERVED VALUE (single-file): local 9.99 wins — NOT the base 1.70.
    # [source: context7 Specializes glossary; empirical build_specializes_demo.py run]
    assert _approx_eq(val, 9.99), (
        f"FAIL test_specializes_local_wins_single_file: expected ~9.99 (local wins), got {val}. "
        f"In single-file context the Specializes prim's local opinion wins over the base."
    )
    print(
        f"[PASS] test_specializes_local_wins_single_file: "
        f"{_SPECIALIZES_PATH} bio:vdwRadius = {val:.4f} (~9.99, local wins)"
    )


# ---------------------------------------------------------------------------
# Test 3: Base-update propagation — both prims retain local opinion
# ---------------------------------------------------------------------------

def test_base_update_propagation() -> None:
    """Assert that updating /_class_/AtomBase.bio:vdwRadius to 2.00 in-session
    does NOT change the resolved value for either prim (both stay at 9.99).

    FINDING: this contradicts the leaf spec's prediction for Specializes.

    The leaf spec predicted:
      - /Atom_Inherits stays 9.99 (correct — local wins over Inherits)
      - /Atom_Specializes changes to 2.00 (INCORRECT for single-file context)

    In a single-file flat stage, setting the base-class attribute to 2.00 has
    NO effect on either prim because both prims' local opinions (9.99) override
    the base class regardless of arc type.

    The in-session edit (no stage.Reload() needed for in-memory edits) is
    immediately reflected in base_prim.Get() = 2.00, but the composed value
    for the child prims remains 9.99 because local opinions dominate.

    stage.Reload() after the edit DISCARDS the in-memory base modification
    (reverting the base to 1.70 from disk) — prims still resolve 9.99.

    [source: context7 /websites/openusd_release — Specializes glossary;
     empirical: direct in-process measurement in this test suite]
    """
    stage = Usd.Stage.Open(_USDA)

    inh_prim = stage.GetPrimAtPath(_INHERITS_PATH)
    spe_prim = stage.GetPrimAtPath(_SPECIALIZES_PATH)
    base_prim = stage.GetPrimAtPath(_BASE_PATH)

    # Verify baseline
    assert _approx_eq(inh_prim.GetAttribute("bio:vdwRadius").Get(), 9.99), "Baseline Inherits != 9.99"
    assert _approx_eq(spe_prim.GetAttribute("bio:vdwRadius").Get(), 9.99), "Baseline Specializes != 9.99"
    assert _approx_eq(base_prim.GetAttribute("bio:vdwRadius").Get(), 1.70), "Baseline base != 1.70"

    # Modify base class attribute in-session (in-memory edit, no reload needed).
    base_prim.GetAttribute("bio:vdwRadius").Set(2.00)
    assert _approx_eq(base_prim.GetAttribute("bio:vdwRadius").Get(), 2.00), \
        "Base class did not update to 2.00 after Set()"

    # Assert composed values UNCHANGED — local opinions still dominate.
    inh_after = inh_prim.GetAttribute("bio:vdwRadius").Get()
    spe_after = spe_prim.GetAttribute("bio:vdwRadius").Get()

    # TRUE OBSERVED: Inherits prim stays 9.99 (local > Inherits, base irrelevant).
    assert _approx_eq(inh_after, 9.99), (
        f"FAIL: Inherits prim should stay 9.99 after base update, got {inh_after}"
    )
    # TRUE OBSERVED: Specializes prim ALSO stays 9.99 (local wins in single-file context).
    # The leaf spec predicted 2.00 here — that prediction is wrong for single-file.
    assert _approx_eq(spe_after, 9.99), (
        f"FAIL: Specializes prim should stay 9.99 in single-file context after base update, "
        f"got {spe_after}. "
        f"NOTE: leaf spec predicted 2.00, but that only applies across referencing boundaries."
    )

    print(
        f"[PASS] test_base_update_propagation: after base -> 2.00: "
        f"Inherits={inh_after:.4f}, Specializes={spe_after:.4f} (both retain local 9.99)"
    )
    print(
        "       FINDING: Specializes prim does NOT propagate base update in single-file context."
        " Leaf spec prediction (2.00) only holds across referencing boundaries."
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Opening stage: {_USDA}")
    tests = [
        test_inherits_local_wins,
        test_specializes_local_wins_single_file,
        test_base_update_propagation,
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
