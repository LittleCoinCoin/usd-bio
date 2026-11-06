"""Fast checks for toy_benchmark.py. Plain asserts: runs under pytest or as a script.

    /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 examples/cross_scale_time/tests/test_toy_benchmark.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.linalg import expm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import toy_benchmark as tb  # noqa: E402


def _joint_mc_waiting_times(low_h: tb.Telegraph, lam: float, n: int, rng) -> np.ndarray:
    """Direct Gillespie of the composed (L, H) system, independent of the PH formula."""
    out = np.empty(n)
    for i in range(n):
        s = int(rng.random() < low_h.p1)
        t = 0.0
        while True:
            if s == 0:
                t += rng.exponential(1.0 / low_h.a)
                s = 1
            else:
                tot = low_h.b + lam
                t += rng.exponential(1.0 / tot)
                if rng.random() < lam / tot:
                    break
                s = 0
        out[i] = t
    return out


def test_reference_matches_monte_carlo():
    lh = tb.base_h()
    lam = 1.0 * lh.k  # eps = 1, where the waiting time is far from exponential
    ref = tb.reference(lh, lam)
    w = _joint_mc_waiting_times(lh, lam, 20000, np.random.default_rng(7))
    se = w.std() / np.sqrt(w.size)
    assert abs(w.mean() - ref.mean()) < 4 * se, (w.mean(), ref.mean(), se)
    ts = np.sort(w)
    emp = np.arange(1, ts.size + 1) / ts.size
    ks = np.max(np.abs((1 - ref.survival(ts)) - emp))
    assert ks < 1.63 / np.sqrt(ts.size), ks  # ~1% KS critical value


def test_survival_and_mean_closed_forms():
    lh = tb.base_h()
    lam = 0.3 * lh.k
    ref = tb.reference(lh, lam)
    t = np.linspace(0, 5 * ref.mean(), 7)
    via_expm = np.array([ref.alpha @ expm(ref.S * x) @ np.ones(2) for x in t])
    assert np.allclose(ref.survival(t), via_expm, rtol=1e-10, atol=1e-12)
    assert np.isclose(ref.mean(), tb.mfpt(lh.a, lh.b, lam), rtol=1e-12)


def test_m1_matches_reference_as_eps_to_zero():
    lh = tb.base_h()
    errs = []
    for eps in (1e-1, 1e-2, 1e-3, 1e-4):
        lam = eps * lh.k
        s = tb.score(tb.fit_infinite_data(lh, lam)["M1"], tb.reference(lh, lam))
        errs.append(abs(s["mean_rel"]))
        assert s["ks"] < 2 * eps  # KS also vanishes linearly in eps
        # analytic: |mean error| = eps*pi0 / (1 + eps*pi0)
        assert np.isclose(abs(s["mean_rel"]), eps * (1 - lh.p1) / (1 + eps * (1 - lh.p1)), rtol=1e-9)
    assert errs == sorted(errs, reverse=True) and errs[-1] < 1e-4


def test_unit_invariance():
    tr = tb.trajectories(tb.BASE, 1, 11, t_end=2000.0)[0]
    rows = tb.unit_invariance(tr)
    good = [r for r in rows if not r["case"].startswith("NEGATIVE")]
    bad = [r for r in rows if r["case"].startswith("NEGATIVE")]
    assert good and bad
    for r in good:
        assert r["max_rel_dev_mean"] < 1e-9 and r["max_abs_dev_survival"] < 1e-9, r
    # the control (window declared in L units) must visibly break invariance for a dynamic method
    assert max(r["max_rel_dev_mean"] for r in bad if r["method"] == "M2ph") > 1e-3


def test_m1_is_window_neutral_under_mean_aggregation():
    tr = tb.trajectories(tb.BASE, 1, 3, t_end=2000.0)[0]
    lam = tb.base_h().k
    thetas = [tb.fit_all(tb.project(tr, tb.default_tmap(kd=kd)), tb.default_tmap(kd=kd), lam)["M1"].theta
              for kd in (0.01, 0.3, 3.0)]
    assert np.ptp(thetas) / np.mean(thetas) < 2e-3, thetas  # only the truncated last window differs


def test_lag_generator_recovers_rates_on_snapshots():
    tr = tb.trajectories(tb.BASE, 1, 5, t_end=5000.0)[0]
    lh = tb.base_h()
    tm = tb.default_tmap(kd=0.3, mode="snapshot")
    a, b = tb.lag_generator(tb.project(tr, tm).astype(np.int8), tm.window)
    assert abs(a / lh.a - 1) < 0.05 and abs(b / lh.b - 1) < 0.05, (a / lh.a, b / lh.b)


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_") and callable(v)]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"{len(tests)} passed")
