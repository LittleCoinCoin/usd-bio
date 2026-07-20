"""
Unit tests for the ΔΔG <-> MaBoSS-parameter correlation (Pipeline 3, Step 1).

Falsification-resistant: the expected S values are either hand-computed fixtures
(R02 §Behaviour) or recomputed by a SECOND, independent logistic implementation
here (``_independent_s``) -- never read back from the module under test. So a
correlation that silently changed form or constants cannot pass by agreeing with
itself.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from p53_mdm2.maboss.dg_correlation import (
    s_from_ddg,
    ddg_from_s,
    DEFAULT_MIDPOINT_KCAL_PER_MOL as M,
    DEFAULT_STEEPNESS_PER_KCAL as K,
    EPS,
)


@dataclass
class Result:
    check_name: str
    passed: bool
    errors: list = field(default_factory=list)


def _independent_s(ddg, m=M, k=K):
    """Second, independent logistic (direct exp of the R02 formula)."""
    return 1.0 / (1.0 + math.exp(-k * (ddg - m)))


def _check(name, cond, msg):
    return Result(name, bool(cond), [] if cond else [msg])


def run() -> list:
    results = []

    # --- Hand-computed fixture anchors (R02 §Behaviour, m=-3, k=1.5) ---
    s0 = s_from_ddg(0.0)
    results.append(_check(
        "wt_ddg0_S_approx_0p989", abs(s0 - 0.98901306) < 1e-6,
        f"S(0)={s0!r} != ~0.98901306"))

    s_mid = s_from_ddg(-3.0)
    results.append(_check(
        "ddg_minus3_S_is_0p5", abs(s_mid - 0.5) < 1e-9,
        f"S(-3)={s_mid!r} != 0.5"))

    s_lo = s_from_ddg(-6.0)
    results.append(_check(
        "ddg_minus6_S_approx_0p011", abs(s_lo - 0.01098694) < 1e-6,
        f"S(-6)={s_lo!r} != ~0.01098694"))

    # --- Agreement with an independent implementation across a range ---
    indep_err = []
    for ddg in (-8.0, -5.0, -3.0, -1.0, 0.0, 2.0, 5.0):
        got = s_from_ddg(ddg)
        exp = _independent_s(ddg)
        if abs(got - exp) > 1e-9:
            indep_err.append(f"ddg={ddg}: {got!r} != independent {exp!r}")
    results.append(Result("matches_independent_logistic", not indep_err, indep_err))

    # --- Round-trip: ddg_from_s(s_from_ddg(x)) ~= x (unclamped middle range) ---
    rt_err = []
    for ddg in (-7.0, -4.5, -3.0, -2.0, 0.0, 1.5, 4.0):
        rec = ddg_from_s(s_from_ddg(ddg))
        if abs(rec - ddg) > 1e-6:
            rt_err.append(f"round-trip ddg={ddg}: recovered {rec!r}")
    results.append(Result("roundtrip_ddg_s_ddg", not rt_err, rt_err))

    # --- Monotonicity: S strictly increasing in ΔΔG (unclamped region) ---
    # Range chosen so |k*(ΔΔG-m)| <= 15, i.e. S stays inside (EPS, 1-EPS) and
    # the clamp never flattens two neighbours (the clamp is exercised
    # separately below).
    xs = [-13.0 + i * 0.5 for i in range(41)]  # -13 .. +7 (offset from m: ±10)
    ss = [s_from_ddg(x) for x in xs]
    mono = all(b > a for a, b in zip(ss, ss[1:]))
    results.append(_check("strictly_increasing", mono,
                          "S is not strictly increasing in ΔΔG"))

    # --- Clamp behaviour at the saturating tails ---
    s_hi = s_from_ddg(1000.0)   # ΔΔG -> +inf, S -> 1
    s_low = s_from_ddg(-1000.0)  # ΔΔG -> -inf, S -> 0
    clamp_ok = (s_hi <= 1.0 - EPS + 1e-18) and (s_low >= EPS - 1e-18) \
        and (s_hi < 1.0) and (s_low > 0.0)
    results.append(_check("clamped_to_open_interval", clamp_ok,
                          f"tails not clamped: S(+1000)={s_hi!r}, S(-1000)={s_low!r}"))

    # inverse must stay finite at the clamped extremes (no divide-by-zero)
    try:
        d_hi = ddg_from_s(1.0)
        d_low = ddg_from_s(0.0)
        inv_finite = math.isfinite(d_hi) and math.isfinite(d_low)
        err = [] if inv_finite else [f"inverse not finite at S in {{0,1}}: {d_low}, {d_hi}"]
    except Exception as exc:  # pragma: no cover
        inv_finite, err = False, [f"inverse raised at S in {{0,1}}: {exc}"]
    results.append(Result("inverse_finite_at_boundaries", inv_finite, err))

    # --- k <= 0 rejected (guards monotonicity precondition) ---
    bad_k = False
    try:
        s_from_ddg(0.0, k=0.0)
    except ValueError:
        bad_k = True
    results.append(_check("rejects_nonpositive_k", bad_k,
                          "s_from_ddg did not reject k=0"))

    return results


if __name__ == "__main__":
    rs = run()
    ok = all(r.passed for r in rs)
    for r in rs:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.check_name}")
        for e in r.errors:
            print(f"    - {e}")
    raise SystemExit(0 if ok else 1)
