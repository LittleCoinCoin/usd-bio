"""Toy benchmark for cross-scale dynamics fitting (topic ``cross-scale-time``, Q-A).

Vocabulary follows ``__threads__/cross-scale-time/INTENT.md``.

Low model L
    Two-state telegraph process, states {0, 1}, rates ``a`` (0->1) and ``b`` (1->0),
    simulated exactly (event-driven) on its OWN clock, in its own unit.
Reference (ground truth)
    Composed fast-slow CTMC on (L, H): H fires 0->1 at rate ``lam`` only while L = 1.
    H's waiting time T, from L in its stationary state, is phase-type with
    sub-generator S = [[-a, a], [b, -(b + lam)]] and initial vector (pi0, pi1), so its
    survival P(T > t) = alpha . expm(S t) . 1 is exact; no Monte Carlo is needed.
Projection pi
    The L state itself (0/1).
Time map tau
    Unit conversion ``c`` (H units per L unit) plus an aggregation window ``window``
    (declared in H units) and an aggregation operator (``mean`` = fraction of the window
    spent in L = 1, then thresholded at 1/2 for the dynamic estimators; ``snapshot`` =
    L state at the window's left edge).
Fitted H
    Either memoryless (single rate theta: the MaBoSS-like form) or two-phase phase-type.
Methods (input: the projected series + tau + H's declared coupling rate ``lam``)
    M1     stationary: theta = lam * mean occupancy.
    M2exp  dynamic, dwell times: a, b from run lengths; theta = 1 / MFPT(a, b, lam).
    M2ph   dynamic, dwell times: phase-type H with the estimated a, b.
    M3ph   lag-time generator: a, b from the lag-1 transition matrix via the exact
           two-state matrix logarithm (embedding); phase-type H.
    M1c    control for the perturbation test only: a single rate calibrated to the
           REFERENCE base-state mean, then scaled by occupancy for a mutant.

Run: ``python examples/cross_scale_time/toy_benchmark.py`` from the repo root; it writes
``examples/cross_scale_time/outputs/run_<UTC>/`` and never overwrites a previous run.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import platform
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import scipy

HERE = Path(__file__).resolve().parent

# ----------------------------------------------------------------------------- model


@dataclass(frozen=True)
class Telegraph:
    """Two-state L. Rates are per unit of whatever clock they are expressed in."""

    a: float
    b: float

    @property
    def k(self) -> float:
        """Relaxation rate a + b (inverse correlation time of L)."""
        return self.a + self.b

    @property
    def p1(self) -> float:
        return self.a / self.k

    def in_unit(self, f: float) -> "Telegraph":
        """Same process expressed in a unit f times LONGER than the current one."""
        return Telegraph(self.a * f, self.b * f)


@dataclass(frozen=True)
class TimeMap:
    """tau: c = H units per L unit; window in H units; mode = aggregation operator."""

    c: float
    window: float
    mode: str = "mean"


@dataclass
class Trajectory:
    """Piecewise-constant L path: states[i] holds on [times[i], times[i+1]), last up to t_end."""

    times: np.ndarray
    states: np.ndarray
    t_end: float

    def in_unit(self, f: float) -> "Trajectory":
        return Trajectory(self.times / f, self.states, self.t_end / f)


def simulate_telegraph(m: Telegraph, t_end: float, rng: np.random.Generator) -> Trajectory:
    """Exact event-driven simulation, started from the stationary distribution."""
    s0 = int(rng.random() < m.p1)
    leave = np.array([m.a, m.b])
    dwells: list[np.ndarray] = []
    total, state = 0.0, s0
    chunk = int(t_end * m.k) + 64
    while total < t_end:
        seq = (state + np.arange(chunk)) % 2
        d = rng.exponential(1.0, chunk) / leave[seq]
        dwells.append(d)
        total += d.sum()
        state = int((state + chunk) % 2)
    d = np.concatenate(dwells)
    starts = np.concatenate([[0.0], np.cumsum(d)[:-1]])
    keep = starts < t_end
    states = ((s0 + np.arange(d.size)) % 2)[keep]
    return Trajectory(starts[keep], states.astype(np.int8), float(t_end))


def project(traj: Trajectory, tmap: TimeMap) -> np.ndarray:
    """Apply tau: place L on H's axis and aggregate over windows. Returns x_k in [0, 1]."""
    t_h = traj.times * tmap.c
    t_end_h = traj.t_end * tmap.c
    n = int(np.floor(t_end_h / tmap.window + 1e-9))
    edges = np.arange(n + 1) * tmap.window
    if tmap.mode == "snapshot":
        idx = np.searchsorted(t_h, edges[:-1], side="right") - 1
        return traj.states[idx].astype(float)
    if tmap.mode == "mean":
        knots = np.append(t_h, t_end_h)
        cum = np.concatenate([[0.0], np.cumsum(np.diff(knots) * traj.states)])
        return np.diff(np.interp(edges, knots, cum)) / tmap.window
    raise ValueError(f"unknown aggregation mode {tmap.mode!r}")


def binarize(x: np.ndarray) -> np.ndarray:
    return (x > 0.5).astype(np.int8)


# ------------------------------------------------------------------------ fitted H


@dataclass
class FittedH:
    """Either a single-rate (memoryless) H or a phase-type H; all in H's time unit."""

    kind: str
    theta: float = float("nan")
    alpha: np.ndarray | None = None
    S: np.ndarray | None = None

    @property
    def ok(self) -> bool:
        if self.kind == "exp":
            return bool(np.isfinite(self.theta) and self.theta > 0)
        return self.S is not None and bool(np.all(np.isfinite(self.S)))

    def mean(self) -> float:
        if not self.ok:
            return float("nan")
        if self.kind == "exp":
            return 1.0 / self.theta
        return float(-self.alpha @ np.linalg.solve(self.S, np.ones(2)))

    def survival(self, t: np.ndarray) -> np.ndarray:
        t = np.asarray(t, dtype=float)
        if not self.ok:
            return np.full_like(t, np.nan)
        if self.kind == "exp":
            return np.exp(-self.theta * t)
        mu, V = np.linalg.eig(self.S)
        w = (self.alpha @ V) * np.linalg.solve(V, np.ones(2))
        return np.real(np.exp(np.outer(t, mu)) @ w)


def phase_type(a: float, b: float, lam: float) -> FittedH:
    if not (np.isfinite(a) and np.isfinite(b) and a > 0 and b > 0):
        return FittedH("ph")
    S = np.array([[-a, a], [b, -(b + lam)]])
    return FittedH("ph", alpha=np.array([b, a]) / (a + b), S=S)


def mfpt(a: float, b: float, lam: float) -> float:
    """Mean waiting time of H from stationary L (closed form; checked against PH in tests)."""
    return (a + b) / (a * lam) + b / (a * (a + b))


def reference(low_h: Telegraph, lam: float) -> FittedH:
    """Exact ground truth: L rates already in H units."""
    return phase_type(low_h.a, low_h.b, lam)


# ------------------------------------------------------------------------- methods


def dwell_rates(xb: np.ndarray, window: float) -> tuple[float, float]:
    """a, b from mean complete run lengths of a binary series (first/last runs censored)."""
    cut = np.flatnonzero(np.diff(xb)) + 1
    bounds = np.concatenate([[0], cut, [xb.size]])
    lengths = np.diff(bounds)[1:-1]
    values = xb[bounds[1:-2]] if lengths.size else np.array([], dtype=np.int8)
    out = []
    for v in (0, 1):
        sel = lengths[values == v]
        out.append(1.0 / (sel.mean() * window) if sel.size else float("nan"))
    return out[0], out[1]


def lag_generator(xb: np.ndarray, window: float) -> tuple[float, float]:
    """a, b from the lag-1 transition matrix via the exact 2-state matrix log.

    Returns NaNs when the estimated matrix is not embeddable (1 - p - q <= 0).
    """
    s, t = xb[:-1], xb[1:]
    n0, n1 = np.sum(s == 0), np.sum(s == 1)
    if n0 == 0 or n1 == 0:
        return float("nan"), float("nan")
    p = np.sum((s == 0) & (t == 1)) / n0
    q = np.sum((s == 1) & (t == 0)) / n1
    r = 1.0 - p - q
    if r <= 0 or p + q == 0:
        return float("nan"), float("nan")
    kk = -np.log(r) / window
    return kk * p / (p + q), kk * q / (p + q)


def fit_all(x: np.ndarray, tmap: TimeMap, lam: float) -> dict[str, FittedH]:
    """Every method, from the projected series x (H axis) and tau alone."""
    xb = x.astype(np.int8) if tmap.mode == "snapshot" else binarize(x)
    a2, b2 = dwell_rates(xb, tmap.window)
    a3, b3 = lag_generator(xb, tmap.window)
    return {
        "M1": FittedH("exp", theta=lam * float(x.mean())),
        "M2exp": FittedH("exp", theta=1.0 / mfpt(a2, b2, lam)) if np.isfinite(a2 + b2) else FittedH("exp"),
        "M2ph": phase_type(a2, b2, lam),
        "M3ph": phase_type(a3, b3, lam),
    }


def fit_infinite_data(low_h: Telegraph, lam: float) -> dict[str, FittedH]:
    """Each method's functional form with its summary at its exact (infinite-data) value."""
    return {
        "M1": FittedH("exp", theta=lam * low_h.p1),
        "M2exp": FittedH("exp", theta=1.0 / mfpt(low_h.a, low_h.b, lam)),
        "M2ph": reference(low_h, lam),
        "M3ph": reference(low_h, lam),
    }


METHODS = ("M1", "M2exp", "M2ph", "M3ph")


def score(fit: FittedH, ref: FittedH) -> dict[str, float]:
    """KS distance on the waiting-time CDF and relative error of the mean, vs reference."""
    t = np.linspace(0.0, 8.0 * ref.mean(), 4001)
    ks = float(np.max(np.abs(fit.survival(t) - ref.survival(t)))) if fit.ok else float("nan")
    return {"ks": ks, "mean_rel": fit.mean() / ref.mean() - 1.0}


# ------------------------------------------------------------------------- config

BASE = Telegraph(a=1.0, b=2.0)  # in L's own unit (u_L); p1 = 1/3, k = 3 / u_L
C_BASE = 1.0e-3                 # 1 u_L = 1e-3 u_H (any value works: that is the point)
T_L = 10_000.0                  # L trajectory length in u_L (~6,700 L cycles)
K_DELTA = 0.01                  # default window: k_H * window
N_REP = 20
SEED = 20261106
EPS_GRID = (1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1, 1.0, 3.0, 10.0, 30.0, 100.0)
KD_GRID = (0.01, 0.03, 0.1, 0.3, 1.0, 3.0)
TOLS = (0.01, 0.05)


def base_h(low: Telegraph = BASE, c: float = C_BASE) -> Telegraph:
    """L's rates expressed in H units (1 u_H = 1/c u_L)."""
    return low.in_unit(1.0 / c)


def default_tmap(low: Telegraph = BASE, c: float = C_BASE, kd: float = K_DELTA, mode: str = "mean") -> TimeMap:
    return TimeMap(c=c, window=kd / base_h(low, c).k, mode=mode)


def trajectories(low: Telegraph, n_rep: int, seed: int, t_end: float = T_L) -> list[Trajectory]:
    return [simulate_telegraph(low, t_end, np.random.default_rng([seed, r])) for r in range(n_rep)]


# -------------------------------------------------------------------------- sweeps


def sweep_eps(trajs: list[Trajectory]) -> list[dict]:
    lh = base_h()
    tmap = default_tmap()
    xs = [project(tr, tmap) for tr in trajs]
    rows = []
    for eps in EPS_GRID:
        lam = eps * lh.k
        ref = reference(lh, lam)
        for m, f in fit_infinite_data(lh, lam).items():
            rows.append({"eps": eps, "method": m, "rep": "inf", **score(f, ref)})
        for r, x in enumerate(xs):
            for m, f in fit_all(x, tmap, lam).items():
                rows.append({"eps": eps, "method": m, "rep": r, **score(f, ref)})
    return rows


def m1_thresholds(p1_values=(0.1, 1 / 3, 0.5, 0.9)) -> list[dict]:
    """Smallest eps at which an infinite-data memoryless fit exceeds a tolerance.

    M1 on the mean (numeric and analytic) and on the CDF (KS); M2exp on the CDF (its mean
    is exact by construction). Grid step is 0.5% in eps.
    """
    out = []
    eps_fine = np.logspace(-4, 2, 1201)
    for p1 in p1_values:
        lh = Telegraph(a=p1, b=1 - p1)  # k = 1, units irrelevant
        mean_err = np.empty_like(eps_fine)
        ks = np.empty_like(eps_fine)
        ks2 = np.empty_like(eps_fine)
        for i, e in enumerate(eps_fine):
            ref = reference(lh, e)
            s = score(FittedH("exp", theta=e * p1), ref)
            mean_err[i], ks[i] = abs(s["mean_rel"]), s["ks"]
            ks2[i] = score(FittedH("exp", theta=1.0 / mfpt(lh.a, lh.b, e)), ref)["ks"]
        for tol in TOLS:
            first = lambda arr: float(eps_fine[np.argmax(arr > tol)]) if np.any(arr > tol) else float("nan")
            out.append({
                "p1": p1, "tol": tol,
                "M1_eps_star_mean_numeric": first(mean_err),
                "M1_eps_star_mean_analytic": tol / ((1 - tol) * (1 - p1)),
                "M1_eps_star_ks_numeric": first(ks),
                "M2exp_eps_star_ks_numeric": first(ks2),
                "M2exp_max_ks": float(ks2.max()),
            })
    return out


def sweep_window(trajs: list[Trajectory], eps_values=(0.1, 1.0)) -> list[dict]:
    lh = base_h()
    rows = []
    for mode in ("snapshot", "mean"):
        for kd in KD_GRID:
            tmap = default_tmap(kd=kd, mode=mode)
            xs = [project(tr, tmap) for tr in trajs]
            for eps in eps_values:
                lam = eps * lh.k
                ref = reference(lh, lam)
                for r, x in enumerate(xs):
                    for m, f in fit_all(x, tmap, lam).items():
                        rows.append({"mode": mode, "k_delta": kd, "eps": eps, "method": m, "rep": r, **score(f, ref)})
    return rows


def unit_invariance(traj: Trajectory, eps: float = 1.0) -> list[dict]:
    """Rescale L's clock (and tau's conversion consistently); then H's clock.

    Also a negative control: the window declared in L's units instead of H's.
    """
    lh = base_h()
    lam = eps * lh.k
    tmap0 = default_tmap()
    t_grid = np.linspace(0.0, 5.0 / (lh.p1 * lam), 501)
    base = {m: (f.mean(), f.survival(t_grid)) for m, f in fit_all(project(traj, tmap0), tmap0, lam).items()}
    w_l_declared = tmap0.window / tmap0.c  # window as a NUMBER of L units (negative control)
    rows = []

    def compare(label, factor, fits, h_scale=1.0):
        for m, f in fits.items():
            mu0, s0 = base[m]
            mu = f.mean() * h_scale
            s = f.survival(t_grid / h_scale)
            rows.append({"case": label, "factor": factor, "method": m,
                         "max_rel_dev_mean": abs(mu / mu0 - 1.0),
                         "max_abs_dev_survival": float(np.max(np.abs(s - s0)))})

    for f in (1e-12, 1e-6, 1e-3, 10.0, 1e3, 1e6):
        tr = traj.in_unit(f)                       # L timestamps in a unit f x longer
        tm = TimeMap(c=tmap0.c * f, window=tmap0.window, mode=tmap0.mode)
        compare("L clock rescaled, window declared in H units", f, fit_all(project(tr, tm), tm, lam))
        tm_bad = TimeMap(c=tmap0.c * f, window=w_l_declared * tmap0.c * f, mode=tmap0.mode)
        if tm_bad.window < 0.5 * tmap0.window or tm_bad.window > 0.2 * traj.t_end * tmap0.c:
            continue  # window outside the trajectory's usable range: control not computable
        compare("NEGATIVE CONTROL: window declared in L units", f, fit_all(project(tr, tm_bad), tm_bad, lam))
    for h in (1 / 3600, 1 / 60, 60.0, 3600.0):   # H unit h x longer
        tm = TimeMap(c=tmap0.c / h, window=tmap0.window / h, mode=tmap0.mode)
        compare("H clock rescaled", h, fit_all(project(traj, tm), tm, lam * h), h_scale=h)
    return rows


MUTANTS = {
    "b x4 (occupancy 1/3 -> 1/9)": lambda m: Telegraph(m.a, 4 * m.b),
    "a,b x0.1 (same occupancy, 10x slower switching)": lambda m: Telegraph(0.1 * m.a, 0.1 * m.b),
    "a,b x10 (same occupancy, 10x faster switching)": lambda m: Telegraph(10 * m.a, 10 * m.b),
}


def perturbation(n_rep: int, seed: int, eps_values=(0.01, 0.1, 1.0, 10.0)) -> list[dict]:
    """Fit on base and on mutant L with the same rule; compare mean-waiting-time fold changes."""
    lh0 = base_h()
    tmap = default_tmap()  # same declared tau for base and mutants
    base_x = [project(tr, tmap) for tr in trajectories(BASE, n_rep, seed)]
    rows = []
    for mi, (name, mut) in enumerate(MUTANTS.items()):
        low_m = mut(BASE)
        lhm = base_h(low_m)
        mut_x = [project(tr, tmap) for tr in trajectories(low_m, n_rep, seed + 1 + mi)]
        for eps in eps_values:
            lam = eps * lh0.k
            ref0, refm = reference(lh0, lam), reference(lhm, lam)
            fc_ref = refm.mean() / ref0.mean()
            for r in range(n_rep):
                f0, fm = fit_all(base_x[r], tmap, lam), fit_all(mut_x[r], tmap, lam)
                for m in METHODS:
                    fc = fm[m].mean() / f0[m].mean()
                    rows.append({"mutant": name, "eps_base": eps, "method": m, "rep": r, "fc_ref": fc_ref,
                                 "fc_fit": fc, "fc_rel_err": fc / fc_ref - 1.0,
                                 "base_mean_rel": score(f0[m], ref0)["mean_rel"],
                                 "mut_ks": score(fm[m], refm)["ks"]})
                # M1c: single rate calibrated to the REFERENCE base mean, scaled by occupancy
                theta0 = 1.0 / ref0.mean()
                thetam = theta0 * mut_x[r].mean() / base_x[r].mean()
                fc = theta0 / thetam
                rows.append({"mutant": name, "eps_base": eps, "method": "M1c", "rep": r, "fc_ref": fc_ref,
                             "fc_fit": fc, "fc_rel_err": fc / fc_ref - 1.0, "base_mean_rel": 0.0,
                             "mut_ks": score(FittedH("exp", theta=thetam), refm)["ks"]})
    return rows


# ------------------------------------------------------------------------ summaries


def _stats(vals) -> dict[str, float]:
    v = np.asarray([x for x in vals if np.isfinite(x)], dtype=float)
    n_fail = len(vals) - v.size
    if v.size == 0:
        return {"median": float("nan"), "p05": float("nan"), "p95": float("nan"), "n_fail": n_fail}
    return {"median": float(np.median(v)), "p05": float(np.percentile(v, 5)),
            "p95": float(np.percentile(v, 95)), "n_fail": n_fail}


def summarize(rows: list[dict], keys: tuple[str, ...], metrics: tuple[str, ...]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        if r.get("rep") == "inf":
            continue
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    out = []
    for g, rs in groups.items():
        row = dict(zip(keys, g))
        for m in metrics:
            for s, v in _stats([x[m] for x in rs]).items():
                row[f"{m}_{s}"] = v
        out.append(row)
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


# -------------------------------------------------------------------------- figures


def make_figures(out: Path, eps_rows, win_rows, pert_rows) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"M1": "#c2410c", "M2exp": "#7c3aed", "M2ph": "#0f766e", "M3ph": "#2563eb", "M1c": "#6b7280"}
    labels = {"M1": "M1 stationary (exp)", "M2exp": "M2exp dwell-time, mean-matched (exp)",
              "M2ph": "M2ph dwell-time (phase-type)", "M3ph": "M3ph lag-time generator (phase-type)",
              "M1c": "M1c calibrated on base, occupancy-scaled"}
    files = []

    # Fig 1: eps sweep
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    for ax, metric, title in ((axes[0], "mean_rel", "|relative error| of mean waiting time"),
                              (axes[1], "ks", "KS distance on waiting-time CDF")):
        for m in METHODS:
            eps = np.array(EPS_GRID)
            fin = [[abs(r[metric]) for r in eps_rows if r["method"] == m and r["eps"] == e and r["rep"] != "inf"]
                   for e in eps]
            med = np.array([np.median(v) for v in fin])
            lo = np.array([np.percentile(v, 5) for v in fin])
            hi = np.array([np.percentile(v, 95) for v in fin])
            inf = np.array([abs(r[metric]) for e in eps for r in eps_rows
                            if r["method"] == m and r["eps"] == e and r["rep"] == "inf"])
            ax.fill_between(eps, np.maximum(lo, 1e-6), np.maximum(hi, 1e-6), color=colors[m], alpha=0.15, lw=0)
            ax.plot(eps, np.maximum(med, 1e-6), "o-", color=colors[m], ms=3.5, lw=1.5, label=labels[m])
            if m in ("M1", "M2exp"):
                ax.plot(eps, np.maximum(inf, 1e-6), "--", color=colors[m], lw=1, alpha=0.8)
        ax.axhline(0.05, color="#111827", lw=0.8, ls=":")
        ax.text(1.2e-3, 0.058, "tolerance 5%", fontsize=8)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(1e-4, 2)
        ax.set_xlabel(r"$\varepsilon = \lambda / (a+b)$ (dimensionless)")
        ax.set_title(title, fontsize=10)
        ax.grid(True, which="major", color="#e5e7eb", lw=0.6)
    axes[0].legend(fontsize=7.5, loc="upper left", frameon=False)
    fig.suptitle("Fit vs exact reference across time-scale ratio: median of 20 seeds, 5-95% band; dashed = infinite data",
                 fontsize=9)
    p = out / "fig1_eps_sweep.png"; fig.savefig(p, dpi=150); plt.close(fig); files.append(p.name)

    # Fig 2: window sweep at eps = 1
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True, constrained_layout=True)
    for ax, mode in zip(axes, ("snapshot", "mean")):
        for m in METHODS:
            kd = np.array(KD_GRID)
            med = []
            for k in kd:
                v = [r["mean_rel"] for r in win_rows if r["mode"] == mode and r["k_delta"] == k
                     and r["eps"] == 1.0 and r["method"] == m and np.isfinite(r["mean_rel"])]
                med.append(np.median(v) if v else np.nan)
            ax.plot(kd, med, "o-", color=colors[m], ms=3.5, lw=1.5, label=labels[m])
        ax.axhline(0, color="#111827", lw=0.8)
        ax.axhspan(-0.05, 0.05, color="#9ca3af", alpha=0.15, lw=0)
        ax.set_xscale("log")
        ax.set_xlabel(r"aggregation window $(a+b)\,\Delta$ (dimensionless)")
        ax.set_title(f"aggregation operator: {mode}", fontsize=10)
        ax.grid(True, color="#e5e7eb", lw=0.6)
    axes[0].set_ylabel("relative error of mean waiting time (signed)")
    axes[0].legend(fontsize=7.5, frameon=False, loc="upper left")
    fig.suptitle(r"The window in $\tau$ is not neutral ($\varepsilon=1$, median of 20 seeds; grey band = $\pm$5%; M2exp and M2ph share a mean, so their lines overlap)", fontsize=9)
    p = out / "fig2_window_sweep.png"; fig.savefig(p, dpi=150); plt.close(fig); files.append(p.name)

    # Fig 3: perturbation fold change error
    mutants = list(MUTANTS)
    fig, axes = plt.subplots(1, len(mutants), figsize=(12, 3.8), sharey=True, constrained_layout=True)
    eps_b = sorted({r["eps_base"] for r in pert_rows})
    styles = {"M1": ("o", "-", 6), "M1c": ("x", "--", 7), "M2exp": ("s", "-", 4),
              "M2ph": ("^", "-", 4), "M3ph": ("v", "-", 4)}
    for ax, mu in zip(axes, mutants):
        ref_fc = [np.median([r["fc_ref"] for r in pert_rows if r["mutant"] == mu and r["eps_base"] == e])
                  for e in eps_b]
        ax.plot(eps_b, ref_fc, "-", color="#111827", lw=3, alpha=0.35, label="exact reference")
        for m in (*METHODS, "M1c"):
            med = [np.median([r["fc_fit"] for r in pert_rows if r["mutant"] == mu and r["eps_base"] == e
                              and r["method"] == m]) for e in eps_b]
            mk, ls, ms = styles[m]
            ax.plot(eps_b, med, marker=mk, ls=ls, color=colors[m], ms=ms, lw=1.2, label=labels[m])
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel(r"base $\varepsilon$")
        ax.set_title(mu, fontsize=9)
        ax.grid(True, which="both", color="#e5e7eb", lw=0.6)
    axes[0].set_ylabel("fold change of mean waiting time\n(mutant / base)")
    axes[0].legend(fontsize=7, frameon=False, loc="upper left")
    fig.suptitle("Perturbation response, median of 20 seeds. M1 and M1c coincide: calibrating the base state "
                 "exactly does not fix the response", fontsize=9)
    p = out / "fig3_perturbation.png"; fig.savefig(p, dpi=150); plt.close(fig); files.append(p.name)
    return files


# ----------------------------------------------------------------------------- main


def main(argv=None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n-rep", type=int, default=N_REP)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--outputs", type=Path, default=HERE / "outputs")
    args = ap.parse_args(argv)

    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = args.outputs / f"run_{stamp}"
    out.mkdir(parents=True, exist_ok=False)  # never overwrite a previous run

    trajs = trajectories(BASE, args.n_rep, args.seed)
    eps_rows = sweep_eps(trajs)
    thr_rows = m1_thresholds()
    win_rows = sweep_window(trajs)
    inv_rows = unit_invariance(trajs[0])
    pert_rows = perturbation(args.n_rep, args.seed)

    write_csv(out / "eps_sweep_raw.csv", eps_rows)
    write_csv(out / "eps_sweep_summary.csv", summarize(eps_rows, ("eps", "method"), ("mean_rel", "ks")))
    write_csv(out / "eps_sweep_infinite_data.csv", [r for r in eps_rows if r["rep"] == "inf"])
    write_csv(out / "m1_thresholds.csv", thr_rows)
    write_csv(out / "window_sweep_raw.csv", win_rows)
    write_csv(out / "window_sweep_summary.csv",
              summarize(win_rows, ("mode", "k_delta", "eps", "method"), ("mean_rel", "ks")))
    write_csv(out / "unit_invariance.csv", inv_rows)
    write_csv(out / "perturbation_raw.csv", pert_rows)
    write_csv(out / "perturbation_summary.csv",
              summarize(pert_rows, ("mutant", "eps_base", "method"), ("fc_ref", "fc_fit", "fc_rel_err", "mut_ks")))
    figs = [] if args.no_figures else make_figures(out, eps_rows, win_rows, pert_rows)

    lh = base_h()
    manifest = {
        "script": "examples/cross_scale_time/toy_benchmark.py",
        "utc": stamp, "seed": args.seed, "n_rep": args.n_rep,
        "L_base_rates_per_uL": {"a": BASE.a, "b": BASE.b},
        "c_uH_per_uL": C_BASE, "L_rates_per_uH": {"a": lh.a, "b": lh.b},
        "T_L_uL": T_L, "default_tau": {"k_delta": K_DELTA, "window_uH": default_tmap().window, "mode": "mean"},
        "eps_grid": EPS_GRID, "k_delta_grid": KD_GRID, "tolerances": TOLS,
        "mutants": list(MUTANTS), "figures": figs,
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(out)
    return out


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
