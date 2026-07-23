"""
Pipeline 4 read-back + directional tests for the MaBoSS analysis SubLayer.

Falsification-resistant / anti-tautology (R02 §Round-trip #3): every expected
value is derived from an INDEPENDENT MaBoSS re-run off the committed
``.bnd``/``.cfg`` (via ``run_maboss``), never from the analysis builder's
in-memory state. MaBoSS is deterministic here (``seed_pseudorandom=100``,
``thread_count=1``), so a fresh re-run is a valid oracle: it catches a wrong
frame mapping, a transcribed/duplicated node, a unit slip, or a stale committed
file -- anything where the USD time samples disagree with what MaBoSS actually
produces.

Checks
------
  #1 readback_probtraj -- open the composed analysis stage FRESH; for every
     variant and node, assert ``bio:maboss:prob:<node>`` at representative USD
     frames equals the independently re-run MaBoSS P(node up) within tolerance.
  #2 directional -- assert time-averaged P(p53 up) for the most-destabilizing
     variant (W23A, S≈0.206) is STRICTLY GREATER than WT (S≈1). The expectation
     is derived independently from the ΔΔG/S ordering (R02: weaker binding →
     p53 released); verified both from an independent re-run AND from the
     committed USD time samples (the committed artifact must itself carry the
     signal).
  #3 departmental_layering -- the analysis SubLayer composes over the topology:
     base atoms still resolve, and the base topology root carries NO
     ``bio:maboss:prob:*`` attribute (base topology untouched).
  #4 provenance_honesty -- the maboss scope self-declares genuine simulation
     provenance and records the backend/engine, so a reader can tell these are
     real runs, not fabricated numbers.

If MaBoSS cannot run in this environment, all substantive checks are reported as
an HONEST SKIP (never a pass on fabricated data), per the R02 honesty contract.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

try:
    from pxr import Usd
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pxr not importable. Run under the OpenUSD interpreter with "
        "load_env.sh sourced.") from exc

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)              # examples/p53_mdm2
_PKG_PARENT = os.path.dirname(_PKG)        # examples/
for _p in (_HERE, _PKG_PARENT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from p53_mdm2.maboss import run_maboss
from p53_mdm2.maboss.run_maboss import MabossUnavailableError
from p53_mdm2.templates.build_analysis_layer import (
    default_output_path, MODEL_NODES, MABOSS_SCOPE, PROB_ATTR_PREFIX,
)

# USD stores prob as float32; independent re-run is float64 -> only rounding.
_PROB_TOL = 1e-4
# Frames to spot-check across the 0..499 grid (start, quarters, end).
_REP_FRAMES = (0, 100, 250, 400, 499)

P53 = run_maboss.P53_NODE
WT = "WildType"
MOST_DESTABILIZING = "W23A"   # S≈0.206, ΔΔG=-3.9 (most negative) -> most p53 up


@dataclass
class Result:
    check_name: str
    passed: bool
    errors: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)


def _analysis_variants(stage, scope_path):
    scope = stage.GetPrimAtPath(scope_path)
    if not scope or not scope.IsValid():
        return {}
    return {c.GetName(): c for c in scope.GetChildren()}


def assert_readback_probtraj(stage_path, probtrajs) -> Result:
    """#1 committed time samples == independent re-run, at representative frames."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    root = stage.GetDefaultPrim()
    scope_path = f"{root.GetPath()}/{MABOSS_SCOPE}"
    variant_prims = _analysis_variants(stage, scope_path)
    if not variant_prims:
        return Result("maboss_readback_probtraj", False,
                      [f"no variant prims under {scope_path}"])

    checked = 0
    for variant, pt in probtrajs.items():
        vprim = variant_prims.get(variant)
        if vprim is None:
            errors.append(f"{variant}: missing analysis prim")
            continue
        for node in MODEL_NODES:
            attr = vprim.GetAttribute(PROB_ATTR_PREFIX + node)
            if not attr.IsValid():
                errors.append(f"{variant}/{node}: prob attr missing")
                continue
            expected = pt.series(node)  # independent re-run, full grid
            for frame in _REP_FRAMES:
                usd_val = attr.Get(Usd.TimeCode(frame))
                exp_val = expected[pt.frames.index(frame)]
                if usd_val is None:
                    errors.append(f"{variant}/{node}@{frame}: no time sample")
                elif abs(float(usd_val) - float(exp_val)) > _PROB_TOL:
                    errors.append(
                        f"{variant}/{node}@{frame}: USD {float(usd_val):.6f} != "
                        f"re-run {float(exp_val):.6f}")
                else:
                    checked += 1
        detail[f"{variant}:p53@250"] = round(
            float(vprim.GetAttribute(PROB_ATTR_PREFIX + P53).Get(Usd.TimeCode(250))), 6)
    detail["samples_checked"] = checked
    if checked == 0:
        errors.append("no time samples verified")
    return Result("maboss_readback_probtraj", not errors, errors, detail)


def _usd_time_average(stage, scope_path, variant, node) -> float:
    vprim = stage.GetPrimAtPath(f"{scope_path}/{variant}")
    attr = vprim.GetAttribute(PROB_ATTR_PREFIX + node)
    ts = attr.GetTimeSamples()
    if not ts:
        return 0.0
    vals = [float(attr.Get(Usd.TimeCode(t))) for t in ts]
    return sum(vals) / len(vals)


def assert_directional(stage_path, probtrajs) -> Result:
    """#2 <P(p53 up)>(W23A) strictly > <P(p53 up)>(WT), independent + from USD."""
    errors, detail = [], {}
    if WT not in probtrajs or MOST_DESTABILIZING not in probtrajs:
        return Result("maboss_directional", False,
                      [f"need both {WT} and {MOST_DESTABILIZING} trajectories"])

    # Independent oracle: re-run averages.
    wt_avg = probtrajs[WT].time_average(P53)
    mut_avg = probtrajs[MOST_DESTABILIZING].time_average(P53)
    detail["rerun_p53_avg_WT"] = round(wt_avg, 6)
    detail[f"rerun_p53_avg_{MOST_DESTABILIZING}"] = round(mut_avg, 6)
    if not (mut_avg > wt_avg):
        errors.append(
            f"re-run: <P(p53 up)> {MOST_DESTABILIZING}={mut_avg:.6f} not > "
            f"WT={wt_avg:.6f} (destabilizing variant should release more p53)")

    # Committed artifact must itself carry the signal (from USD time samples).
    stage = Usd.Stage.Open(stage_path)
    root = stage.GetDefaultPrim()
    scope_path = f"{root.GetPath()}/{MABOSS_SCOPE}"
    wt_usd = _usd_time_average(stage, scope_path, WT, P53)
    mut_usd = _usd_time_average(stage, scope_path, MOST_DESTABILIZING, P53)
    detail["usd_p53_avg_WT"] = round(wt_usd, 6)
    detail[f"usd_p53_avg_{MOST_DESTABILIZING}"] = round(mut_usd, 6)
    if not (mut_usd > wt_usd):
        errors.append(
            f"USD: <P(p53 up)> {MOST_DESTABILIZING}={mut_usd:.6f} not > "
            f"WT={wt_usd:.6f}")

    return Result("maboss_directional", not errors, errors, detail)


def assert_departmental_layering(stage_path) -> Result:
    """#3 analysis composed over topology; base topology untouched."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    root = stage.GetDefaultPrim()
    if not root or not root.IsValid():
        return Result("maboss_departmental_layering", False, ["no default prim"])
    atoms = [p for p in stage.Traverse()
             if p.GetAttribute("bio:element").IsValid()
             and p.GetAttribute("bio:element").Get()]
    detail["composed_atoms"] = len(atoms)
    if not atoms:
        errors.append("no atoms composed from topology SubLayer (layering broken)")
    # Base topology root must NOT carry a prob attribute (analysis is separate).
    if root.GetAttribute(PROB_ATTR_PREFIX + P53).IsValid():
        errors.append("base topology root carries bio:maboss:prob:p53 (mutated!)")
    return Result("maboss_departmental_layering", not errors, errors, detail)


def assert_provenance_honesty(stage_path) -> Result:
    """#4 scope declares genuine simulation provenance + records backend."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    root = stage.GetDefaultPrim()
    scope = stage.GetPrimAtPath(f"{root.GetPath()}/{MABOSS_SCOPE}")
    if not scope or not scope.IsValid():
        return Result("maboss_provenance_honesty", False, ["no maboss scope"])
    prov = scope.GetAttribute("bio:maboss:provenance")
    backend = scope.GetAttribute("bio:maboss:backend")
    pv = str(prov.Get()).lower() if prov.IsValid() and prov.Get() else ""
    if "genuine" not in pv:
        errors.append("provenance does not declare output as genuine")
    if "fabricat" not in pv:
        errors.append("provenance does not disclaim fabrication")
    if not (backend.IsValid() and backend.Get()):
        errors.append("backend not recorded")
    else:
        detail["backend"] = str(backend.Get())
    return Result("maboss_provenance_honesty", not errors, errors, detail)


def _skip(reason: str) -> list:
    return [Result("maboss_readback_SKIPPED", True, [],
                   {"skipped": True, "reason": reason,
                    "note": "non-substantive skip; MaBoSS could not run "
                            "(no fabricated data written)"})]


def run(stage_path: str = None) -> list:
    stage_path = stage_path or default_output_path()
    if not os.path.isfile(stage_path):
        return [Result("maboss_analysis_stage_exists", False,
                       [f"not found: {stage_path}"])]
    # Independent re-run (the oracle). Honest skip if MaBoSS is unavailable.
    try:
        probtrajs = run_maboss.run_all()
    except MabossUnavailableError as exc:
        return _skip(str(exc))
    except Exception as exc:  # pragma: no cover -- surface unexpected failures
        return [Result("maboss_rerun", False, [f"independent re-run failed: {exc}"])]

    return [
        assert_readback_probtraj(stage_path, probtrajs),
        assert_directional(stage_path, probtrajs),
        assert_departmental_layering(stage_path),
        assert_provenance_honesty(stage_path),
    ]


if __name__ == "__main__":
    rs = run()
    ok = all(r.passed for r in rs)
    for r in rs:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.check_name}")
        for e in r.errors:
            print(f"    - {e}")
        if r.detail:
            print(f"    detail: {r.detail}")
    raise SystemExit(0 if ok else 1)
