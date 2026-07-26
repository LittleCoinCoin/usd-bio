"""
Pipeline 5 read-back suite -- the INTEGRATED end-to-end stage.

Every check opens the COMMITTED integrated ``.usda`` FRESH from disk and asserts
composed values against an oracle built INDEPENDENTLY of the demo builder. The
demo's ``DemoResult`` is never imported, passed in, or consulted: the only things
imported from ``demos.run_end_to_end`` are attribute-NAME constants (the contract
under test), not values.

The four independent oracles, one per hop:

  hop 1  Biology topology   ``independent_pdb.raw_pdb_expectations`` re-derives
                            atom/chain/element counts from 1ycr.pdb by flat
                            column slicing (a different code path from
                            ``converters.pdb_parser``).
  hop 2  ΔΔG                dispatched on the lineage the STAGE declares, and
                            read with plain ``json.load`` (never via
                            ``ddmut_client``): ``bio:ddgSource ==
                            "ddmut-ppi-live"`` is checked against the VERBATIM
                            captured response body named by
                            ``bio:ddgResponseFile`` under
                            ``data/ddmut_ppi_live/`` -- the actual server bytes;
                            ``"fixture"`` is checked against the committed
                            fixture JSON. The live-vs-fixture choice is Pipeline
                            2's to make, so this test follows it and reports
                            which ground truth it used instead of pinning one.
  hop 3  correlation        the logistic ``1/(1+exp(-k(ΔΔG-m)))`` recomputed
                            inline here with ``math.exp`` -- ``dg_correlation``
                            is deliberately NOT called -- from the ΔΔG and the
                            (m, k) BOTH read off the composed stage.
  hop 4  MaBoSS dynamics    a FRESH ``run_maboss.run_all()``. MaBoSS is
                            deterministic here (``seed_pseudorandom=100``,
                            ``thread_count=1``), so a re-run is a valid oracle.

Checks
------
  #1 integrated_composition   -- one composed stage carries all four pipelines:
     topology atoms (vs. the independent PDB re-derivation), the Protocol
     ``bio:md:`` deck, the Genotype VariantSet with its ΔΔG, and the
     time-sampled ``bio:maboss:prob:<node>`` analysis prims. This is the P5
     pre-condition.
  #2 integrated_ddg_lineage   -- ΔΔG resolved through the Genotype VariantSet on
     the fresh stage == the independently-read fixture value, and the join row
     agrees with the variant context (no transcription drift between the two
     places the same number appears).
  #3 integrated_correlation   -- S in the join == the logistic recomputed here
     from the composed ΔΔG and the composed (m, k).
  #4 integrated_maboss_readout -- the join's ``bio:maboss:p53TimeAverage`` and the
     Analysis layer's own composed time samples both == a fresh independent
     MaBoSS re-run's time average.
  #5 integrated_destabilization_ordering -- THE THESIS. Order the variants by
     destabilization (WT baseline, then ΔΔG most negative last) -- an ordering
     stated from the ΔΔG INPUTS alone -- and assert ``<P(p53 up)>`` is STRICTLY
     increasing along it. A destabilized p53:MDM2 interface must release more
     p53, and it must do so through the ΔΔG -> S -> MaBoSS chain.
  #6 integrated_departmental_layering -- the base Biology layer is untouched by
     every downstream hop: opened ALONE it has no analysis, no join, no Protocol
     deck and no ΔΔG; the Analysis and Integration layers both bring the root in
     as an ``over``; and the composed stage still resolves the atoms.
  #7 integrated_honesty_lineage -- the join propagates the ΔΔG status/source
     tokens, the wild type carries NO fabricated ΔΔG/S numeric (only a
     ``baseline`` tag), and a fixture-derived sweep says so on the stage.

If MaBoSS cannot run, checks #4 and #5 are reported as an HONEST SKIP (never a
pass on fabricated data); the purely-compositional checks still run.

Design source: __roadmap__/p53_mdm2/p5_integrated_demo.md Step 2;
__threads__/p53-mdm2/INTENT.md (codebase philosophy: falsification-resistant
read-back testing).
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    from pxr import Sdf, Usd
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

import independent_pdb

from p53_mdm2 import p53_env
from p53_mdm2.maboss import run_maboss
from p53_mdm2.maboss.run_maboss import MabossUnavailableError
from p53_mdm2.templates.build_analysis_layer import (
    MABOSS_SCOPE, MODEL_NODES, PROB_ATTR_PREFIX,
)
# NAMES ONLY -- the contract under test. No builder values cross this import.
from p53_mdm2.demos.run_end_to_end import (
    BASELINE_STATUS, DEMO_HOPS_ATTR, DEMO_LAYERS_ATTR, HOP_DESCRIPTIONS,
    INTEGRATION_SCOPE, JOIN_DDG_ATTR, JOIN_DDG_SOURCE_ATTR,
    JOIN_DDG_STATUS_ATTR, JOIN_FRAME_COUNT_ATTR, JOIN_P53_AVG_ATTR,
    JOIN_S_ATTR, WILDTYPE, default_integrated_path,
)

P53 = run_maboss.P53_NODE

#: ΔΔG is stored float32; the fixture is exact decimal -> rounding only.
_DDG_TOL = 1e-5
#: S is stored float32 (~7 significant digits).
_S_TOL = 1e-6
#: Node probabilities are float32 and averaged over 500 samples.
_PROB_TOL = 1e-4
#: ``bio:ddgSource`` tokens and the oracle each one authorises.
_FIXTURE_SOURCES = {"fixture"}
_LIVE_SOURCES = {"ddmut-ppi-live"}
#: Committed directory of VERBATIM DDMut-PPI response bodies (Pipeline 2's
#: live-capture evidence). Resolved by path, not by importing the client, so this
#: oracle shares no code with the pipeline that authored the stage.
_LIVE_CAPTURE_DIR = os.path.join(_PKG, "data", "ddmut_ppi_live")


@dataclass
class Result:
    check_name: str
    passed: bool
    errors: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Independent oracles
# ---------------------------------------------------------------------------
def _fixture_ddg() -> Dict[str, float]:
    """{mutation: ΔΔG} read straight from the committed fixture JSON.

    Deliberately does NOT call ``ddmut_client.load_fixture`` -- the oracle must
    not share a code path with the pipeline that authored the stage.
    """
    path = os.path.join(_PKG, "composition", "fixtures", "ddmut_ppi_fixture.json")
    with open(path, "r") as fh:
        doc = json.load(fh)
    return {mut: float(rec["prediction"])
            for mut, rec in doc["predictions"].items()}


def _captured_live_ddg(response_file: str) -> Optional[float]:
    """ΔΔG parsed from the VERBATIM captured DDMut-PPI response body.

    The strongest available oracle for a live-sourced value: the actual server
    bytes Pipeline 2 committed as evidence, read with plain ``json.load``.
    Returns ``None`` when the named body is absent or carries no prediction.
    """
    if not response_file or response_file in ("unknown", ""):
        return None
    path = os.path.join(_LIVE_CAPTURE_DIR, response_file)
    if not os.path.isfile(path):
        # Pipeline 2 scopes each live run to its own run_<UTC>/ subdirectory, so
        # fall back to a basename search under the capture root.
        base = os.path.basename(response_file)
        found = [os.path.join(d, base)
                 for d, _sub, files in os.walk(_LIVE_CAPTURE_DIR)
                 if base in files]
        if not found:
            return None
        path = found[0]
    try:
        with open(path, "r") as fh:
            payload = json.load(fh)
        return float(payload["prediction"])
    except (ValueError, KeyError, TypeError):
        return None


def _logistic(ddg: float, m: float, k: float) -> float:
    """Independent re-implementation of the R02 logistic (no dg_correlation)."""
    return 1.0 / (1.0 + math.exp(-k * (ddg - m)))


# ---------------------------------------------------------------------------
# Stage helpers
# ---------------------------------------------------------------------------
def _open(stage_path: str):
    stage = Usd.Stage.Open(stage_path)
    root = stage.GetDefaultPrim()
    if not root or not root.IsValid():
        raise ValueError(f"integrated stage has no default prim: {stage_path}")
    return stage, root


def _join_prims(stage, root) -> Dict[str, Usd.Prim]:
    scope = stage.GetPrimAtPath(f"{root.GetPath()}/{INTEGRATION_SCOPE}")
    if not scope or not scope.IsValid():
        return {}
    return {c.GetName(): c for c in scope.GetChildren()}


def _get(prim, name):
    attr = prim.GetAttribute(name)
    return attr.Get() if attr.IsValid() else None


def _variant_values(root, variant: str, names: List[str]) -> dict:
    """Resolve *names* on the root prim under the *variant* Genotype selection."""
    vset = root.GetVariantSets().GetVariantSet("Genotype")
    previous = vset.GetVariantSelection()
    vset.SetVariantSelection(variant)
    try:
        return {n: _get(root, n) for n in names}
    finally:
        vset.SetVariantSelection(previous)


def _usd_time_average(stage, root, variant: str, node: str):
    prim = stage.GetPrimAtPath(f"{root.GetPath()}/{MABOSS_SCOPE}/{variant}")
    if not prim or not prim.IsValid():
        return None, 0
    attr = prim.GetAttribute(PROB_ATTR_PREFIX + node)
    if not attr.IsValid():
        return None, 0
    samples = attr.GetTimeSamples()
    if not samples:
        return None, 0
    vals = [float(attr.Get(Usd.TimeCode(t))) for t in samples]
    return sum(vals) / len(vals), len(vals)


# ---------------------------------------------------------------------------
# #1 the P5 pre-condition: one stage, four pipelines
# ---------------------------------------------------------------------------
def assert_composition(stage_path: str, pdb_path: str) -> Result:
    errors, detail = [], {}
    stage, root = _open(stage_path)

    # -- hop 1 Biology: atoms composed, cross-checked against a raw PDB re-derivation
    expected = independent_pdb.raw_pdb_expectations(pdb_path)
    topo_atoms = 0
    for chain_id in sorted(expected.chain_atom_counts):
        chain_prim = stage.GetPrimAtPath(f"{root.GetPath()}/Chain_{chain_id}")
        if not chain_prim or not chain_prim.IsValid():
            errors.append(f"topology chain {chain_id} did not compose")
            continue
        n = sum(1 for p in Usd.PrimRange(chain_prim)
                if p.GetAttribute("bio:element").IsValid()
                and p.GetAttribute("bio:element").Get())
        topo_atoms += n
        if n != expected.chain_atom_counts[chain_id]:
            errors.append(
                f"chain {chain_id}: composed {n} atoms != "
                f"{expected.chain_atom_counts[chain_id]} in the raw PDB")
    detail["topology_atoms"] = topo_atoms
    detail["independent_pdb_atoms"] = expected.total_atoms

    # -- hop 1b Protocol: the bio:md: deck composed onto the same root
    md = stage.GetPrimAtPath(f"{root.GetPath()}/mdSetup")
    if not md or not md.IsValid():
        errors.append("Protocol layer did not compose (no mdSetup prim)")
    else:
        ff = _get(md, "bio:md:forceField")
        detail["md_forceField"] = str(ff)
        if not ff:
            errors.append("mdSetup carries no bio:md:forceField")

    # -- hop 2/3 Perturbation: the Genotype VariantSet with ΔΔG + correlation
    # HasVariantSet is the existence check; GetVariantSet(...).IsValid() is not.
    if not root.GetVariantSets().HasVariantSet("Genotype"):
        errors.append("Genotype VariantSet did not compose")
        variant_names = []
    else:
        vset = root.GetVariantSets().GetVariantSet("Genotype")
        variant_names = list(vset.GetVariantNames())
        detail["genotype_variants"] = sorted(variant_names)
        if WILDTYPE not in variant_names:
            errors.append(f"Genotype VariantSet has no {WILDTYPE} baseline")
        mutants = [v for v in variant_names if v != WILDTYPE]
        if not mutants:
            errors.append("Genotype VariantSet carries no mutant variant")
        for variant in mutants:
            vals = _variant_values(root, variant,
                                   [JOIN_DDG_ATTR, JOIN_S_ATTR])
            if vals[JOIN_DDG_ATTR] is None:
                errors.append(f"{variant}: no {JOIN_DDG_ATTR} on the composed stage")
            if vals[JOIN_S_ATTR] is None:
                errors.append(f"{variant}: no {JOIN_S_ATTR} (correlation) composed")

    # -- hop 4 Analysis: time-sampled node probabilities
    scope = stage.GetPrimAtPath(f"{root.GetPath()}/{MABOSS_SCOPE}")
    if not scope or not scope.IsValid():
        errors.append("Analysis layer did not compose (no maboss scope)")
    else:
        simulated = [c.GetName() for c in scope.GetChildren()]
        detail["simulated_variants"] = sorted(simulated)
        if not simulated:
            errors.append("maboss scope has no variant prims")
        for variant in simulated:
            prim = stage.GetPrimAtPath(f"{scope.GetPath()}/{variant}")
            for node in MODEL_NODES:
                attr = prim.GetAttribute(PROB_ATTR_PREFIX + node)
                if not attr.IsValid() or not attr.GetTimeSamples():
                    errors.append(f"{variant}/{node}: no time samples composed")
        missing = [v for v in variant_names if v not in simulated]
        if missing:
            errors.append(f"genotype variants never simulated: {missing}")

    # -- hop 5 the join itself
    joins = _join_prims(stage, root)
    detail["join_rows"] = sorted(joins)
    if not joins:
        errors.append(f"no {INTEGRATION_SCOPE}/ join prims")

    # -- the stage must be time-navigable from its own root-layer metadata
    detail["time_range"] = (stage.GetStartTimeCode(), stage.GetEndTimeCode())
    if stage.GetEndTimeCode() <= stage.GetStartTimeCode():
        errors.append("integrated stage carries no usable time range "
                      "(start/end time codes not authored on the root layer)")

    return Result("integrated_composition", not errors, errors, detail)


# ---------------------------------------------------------------------------
# #2 hop-2 oracle: ΔΔG vs the independently-read fixture
# ---------------------------------------------------------------------------
def assert_ddg_lineage(stage_path: str) -> Result:
    errors, detail = [], {}
    stage, root = _open(stage_path)
    fixture = _fixture_ddg()
    joins = _join_prims(stage, root)
    checked, skipped = 0, []

    for variant, prim in sorted(joins.items()):
        if variant == WILDTYPE:
            continue
        join_ddg = _get(prim, JOIN_DDG_ATTR)
        source = str(_get(prim, JOIN_DDG_SOURCE_ATTR) or "")
        if join_ddg is None:
            errors.append(f"{variant}: join row carries no {JOIN_DDG_ATTR}")
            continue

        # The same number must appear identically in the variant edit context.
        ctx = _variant_values(root, variant, [JOIN_DDG_ATTR])[JOIN_DDG_ATTR]
        if ctx is None:
            errors.append(f"{variant}: variant context carries no {JOIN_DDG_ATTR}")
        elif abs(float(ctx) - float(join_ddg)) > _DDG_TOL:
            errors.append(
                f"{variant}: join ΔΔG {float(join_ddg):.6f} != variant-context "
                f"ΔΔG {float(ctx):.6f} (transcription drift)")

        # Dispatch the oracle on the lineage the STAGE declares -- Pipeline 2
        # owns the live-vs-fixture choice; this test follows it and names which
        # ground truth it used, rather than pinning one source.
        if source in _LIVE_SOURCES:
            response_file = str(
                _variant_values(root, variant,
                                ["bio:ddgResponseFile"])["bio:ddgResponseFile"]
                or "")
            expected = _captured_live_ddg(response_file)
            oracle = f"captured:{response_file}"
        elif source in _FIXTURE_SOURCES:
            expected = fixture.get(variant)
            oracle = "fixture-json"
        else:
            skipped.append(f"{variant}({source or 'no-source'})")
            continue

        if expected is None:
            skipped.append(f"{variant}({oracle}: no oracle value available)")
            continue
        if abs(float(join_ddg) - expected) > _DDG_TOL:
            errors.append(
                f"{variant}: composed ΔΔG {float(join_ddg):.6f} != "
                f"{oracle} {expected:.6f}")
        else:
            checked += 1
            detail[f"ddg_{variant}"] = (round(float(join_ddg), 6), oracle)

    detail["oracle_checked"] = checked
    if skipped:
        detail["unoracled"] = skipped
    if checked == 0:
        errors.append(
            "no ΔΔG verified against an independent oracle -- neither the "
            "fixture JSON nor a captured live response body matched any "
            "variant's declared bio:ddgSource")
    return Result("integrated_ddg_lineage", not errors, errors, detail)


# ---------------------------------------------------------------------------
# #3 hop-3 oracle: the correlation, recomputed here
# ---------------------------------------------------------------------------
def assert_correlation(stage_path: str) -> Result:
    errors, detail = [], {}
    stage, root = _open(stage_path)
    joins = _join_prims(stage, root)
    checked = 0

    for variant, prim in sorted(joins.items()):
        if variant == WILDTYPE:
            continue
        ddg = _get(prim, JOIN_DDG_ATTR)
        s = _get(prim, JOIN_S_ATTR)
        if ddg is None or s is None:
            errors.append(f"{variant}: join row missing ΔΔG or S")
            continue
        # (m, k) are read off the stage too -- a re-fit is a data change, and
        # this test must follow it rather than hard-code R02's placeholders.
        params = _variant_values(root, variant, [
            "bio:maboss:correlationMidpointKcalPerMol",
            "bio:maboss:correlationSteepnessPerKcal",
            "bio:maboss:correlationForm"])
        m = params["bio:maboss:correlationMidpointKcalPerMol"]
        k = params["bio:maboss:correlationSteepnessPerKcal"]
        form = str(params["bio:maboss:correlationForm"] or "")
        if m is None or k is None:
            errors.append(f"{variant}: correlation (m, k) not on the composed stage")
            continue
        if form != "logistic":
            errors.append(f"{variant}: correlationForm is {form!r}, not "
                          f"'logistic' -- this oracle no longer applies")
            continue
        expected = _logistic(float(ddg), float(m), float(k))
        if abs(float(s) - expected) > _S_TOL:
            errors.append(
                f"{variant}: composed S {float(s):.8f} != independently "
                f"recomputed logistic {expected:.8f} "
                f"(ΔΔG={float(ddg):.3f}, m={float(m)}, k={float(k)})")
        else:
            checked += 1
            detail[f"S_{variant}"] = round(float(s), 8)

    detail["recomputed_checked"] = checked
    if checked == 0:
        errors.append("no S verified against the independent logistic")
    return Result("integrated_correlation", not errors, errors, detail)


# ---------------------------------------------------------------------------
# #4 hop-4 oracle: a fresh MaBoSS re-run
# ---------------------------------------------------------------------------
def assert_maboss_readout(stage_path: str, probtrajs) -> Result:
    errors, detail = [], {}
    stage, root = _open(stage_path)
    joins = _join_prims(stage, root)
    checked = 0

    for variant, pt in sorted(probtrajs.items()):
        rerun_avg = pt.time_average(P53)
        detail[f"rerun_{variant}"] = round(rerun_avg, 6)

        # (a) the Analysis layer's composed time samples
        usd_avg, n = _usd_time_average(stage, root, variant, P53)
        if usd_avg is None:
            errors.append(f"{variant}: no composed {P53} time samples")
        else:
            detail[f"usd_{variant}"] = round(usd_avg, 6)
            if abs(usd_avg - rerun_avg) > _PROB_TOL:
                errors.append(
                    f"{variant}: composed <P({P53} up)> {usd_avg:.6f} != fresh "
                    f"MaBoSS re-run {rerun_avg:.6f}")
            else:
                checked += 1

        # (b) the join's precomputed read-out must agree with both
        prim = joins.get(variant)
        if prim is None:
            errors.append(f"{variant}: no join row")
            continue
        join_avg = _get(prim, JOIN_P53_AVG_ATTR)
        if join_avg is None:
            errors.append(f"{variant}: join row carries no {JOIN_P53_AVG_ATTR}")
        elif abs(float(join_avg) - rerun_avg) > _PROB_TOL:
            errors.append(
                f"{variant}: join <P({P53} up)> {float(join_avg):.6f} != fresh "
                f"MaBoSS re-run {rerun_avg:.6f}")
        frames = _get(prim, JOIN_FRAME_COUNT_ATTR)
        if frames is None or int(frames) != len(pt.frames):
            errors.append(
                f"{variant}: join frameCount {frames} != re-run "
                f"{len(pt.frames)}")

    detail["variants_checked"] = checked
    if checked == 0:
        errors.append("no variant read-out verified against a fresh re-run")
    return Result("integrated_maboss_readout", not errors, errors, detail)


# ---------------------------------------------------------------------------
# #5 THE THESIS: destabilization shifts the p53 dynamics
# ---------------------------------------------------------------------------
def assert_destabilization_ordering(stage_path: str, probtrajs) -> Result:
    """Expectation stated from the ΔΔG INPUTS, then tested on the outputs.

    A more destabilizing variant (more negative ΔΔG) weakens the p53:MDM2
    interface, which the logistic maps to a SMALLER antagonism parameter S,
    which in the Boolean model means less Mdm2N activity and therefore MORE p53
    up. So ordering the variants by descending ΔΔG (WT baseline first, most
    negative last) must give a STRICTLY INCREASING ``<P(p53 up)>``.

    Nothing in this ordering comes from the simulation: it is fixed by the ΔΔG
    inputs alone, so the check is falsifiable by a broken chain at any hop.
    """
    errors, detail = [], {}
    stage, root = _open(stage_path)
    joins = _join_prims(stage, root)

    # Rank from the INPUTS: WT (no ΔΔG) is the least-perturbed baseline.
    ranked = []
    for variant, prim in joins.items():
        ddg = _get(prim, JOIN_DDG_ATTR)
        ranked.append((0.0 if ddg is None else float(ddg), variant))
    ranked.sort(key=lambda t: -t[0])   # descending ΔΔG == increasing destabilization
    order = [v for _d, v in ranked]
    detail["expected_order"] = order
    if len(order) < 2:
        return Result("integrated_destabilization_ordering", False,
                      ["need at least a WT + one mutant to test the thesis"],
                      detail)

    # Read-out from the composed Analysis time samples (the committed artifact
    # must itself carry the signal), cross-checked against the fresh re-run.
    # Three independent read-out sources must ALL carry the ordering: the
    # Analysis layer's raw time samples, the join row a consumer actually reads,
    # and a fresh MaBoSS re-run.
    for label, getter in (
        ("usd", lambda v: _usd_time_average(stage, root, v, P53)[0]),
        ("join", lambda v: (lambda x: None if x is None else float(x))(
            _get(joins[v], JOIN_P53_AVG_ATTR))),
        ("rerun", lambda v: probtrajs[v].time_average(P53)
                  if v in probtrajs else None),
    ):
        avgs = [(v, getter(v)) for v in order]
        if any(a is None for _v, a in avgs):
            errors.append(f"{label}: missing <P({P53} up)> for "
                          f"{[v for v, a in avgs if a is None]}")
            continue
        detail[f"{label}_avgs"] = [(v, round(a, 6)) for v, a in avgs]
        for (v_lo, a_lo), (v_hi, a_hi) in zip(avgs, avgs[1:]):
            if not (a_hi > a_lo):
                errors.append(
                    f"{label}: <P({P53} up)> {v_hi}={a_hi:.6f} not strictly > "
                    f"{v_lo}={a_lo:.6f} -- destabilization ordering broken")

    # And S must move the opposite way (more destabilizing -> smaller S).
    s_vals = [(v, _get(joins[v], JOIN_S_ATTR)) for v in order]
    s_known = [(v, float(s)) for v, s in s_vals if s is not None]
    detail["S_by_order"] = [(v, round(s, 6)) for v, s in s_known]
    for (v_lo, s_lo), (v_hi, s_hi) in zip(s_known, s_known[1:]):
        if not (s_hi < s_lo):
            errors.append(
                f"S {v_hi}={s_hi:.6f} not strictly < {v_lo}={s_lo:.6f} -- the "
                f"ΔΔG->parameter correlation is not monotone along the sweep")

    return Result("integrated_destabilization_ordering", not errors, errors, detail)


# ---------------------------------------------------------------------------
# #6 departmental layering: the base Biology layer stays clean
# ---------------------------------------------------------------------------
def assert_departmental_layering(stage_path: str) -> Result:
    errors, detail = [], {}
    stage, root = _open(stage_path)
    root_path = root.GetPath().pathString

    # (a) the integration root layer contributes an OVER, not a def, and no
    #     topology of its own.
    layer = stage.GetRootLayer()
    spec = layer.GetPrimAtPath(root_path)
    if spec is None:
        errors.append("integration root layer has no spec for the complex root")
    else:
        detail["integration_root_specifier"] = str(spec.specifier)
        if spec.specifier != Sdf.SpecifierOver:
            errors.append(
                f"integration root layer redefines the complex root "
                f"({spec.specifier}) instead of over-ing it")
        stray = [p.name for p in spec.properties]
        if stray:
            errors.append(f"integration layer authors attributes directly on "
                          f"the complex root: {stray}")

    # (b) the Analysis layer likewise only over-s the root.
    analysis = Sdf.Layer.FindOrOpen(
        os.path.join(_PKG, "analysis", "p53_mdm2_analysis.usda"))
    if analysis is None:
        errors.append("analysis layer not found")
    else:
        aspec = analysis.GetPrimAtPath(root_path)
        detail["analysis_root_specifier"] = (
            str(aspec.specifier) if aspec else "missing")
        if aspec is None or aspec.specifier != Sdf.SpecifierOver:
            errors.append("analysis layer does not bring the complex root in "
                          "as an over")

    # (c) the base Biology layer, OPENED ALONE, carries none of the downstream
    #     departments' data. This is the non-destructiveness claim.
    topo_path = os.path.join(p53_env.output_dir(), "p53_mdm2_topology.usda")
    topo_stage = Usd.Stage.Open(topo_path)
    topo_root = topo_stage.GetDefaultPrim()
    for child, owner in ((MABOSS_SCOPE, "Analysis"),
                         (INTEGRATION_SCOPE, "Integration"),
                         ("mdSetup", "Protocol")):
        if topo_stage.GetPrimAtPath(f"{topo_root.GetPath()}/{child}").IsValid():
            errors.append(f"base topology layer contains {owner} data "
                          f"({child}) -- Biology was mutated")
    polluted = []
    for prim in topo_stage.Traverse():
        for attr in prim.GetAttributes():
            name = attr.GetName()
            if name.startswith("bio:ddg") or name.startswith("bio:maboss:") \
                    or name.startswith("bio:md:") or name.startswith("bio:demo:"):
                polluted.append(f"{prim.GetPath()}.{name}")
    detail["base_topology_pollution"] = polluted[:5]
    if polluted:
        errors.append(f"base topology carries {len(polluted)} downstream "
                      f"attribute(s), e.g. {polluted[:3]}")
    # NB: HasVariantSet, not GetVariantSet(...).IsValid() -- the latter returns a
    # valid handle for ANY name and would never fire.
    topo_vsets = topo_root.GetVariantSets()
    detail["base_topology_variantsets"] = sorted(topo_vsets.GetNames())
    if topo_vsets.HasVariantSet("Genotype"):
        errors.append("base topology layer carries the Genotype VariantSet")

    # (d) and yet the composed stage resolves the atoms.
    atoms = [p for p in stage.Traverse()
             if p.GetAttribute("bio:element").IsValid()
             and p.GetAttribute("bio:element").Get()]
    detail["composed_atoms"] = len(atoms)
    if len(atoms) < 800:
        errors.append(f"only {len(atoms)} atoms composed -- layering broken")

    detail["layer_stack"] = [os.path.basename(l.identifier)
                             for l in stage.GetLayerStack()
                             if not l.anonymous]
    return Result("integrated_departmental_layering", not errors, errors, detail)


# ---------------------------------------------------------------------------
# #7 honesty: lineage propagated, nothing fabricated
# ---------------------------------------------------------------------------
def assert_honesty_lineage(stage_path: str) -> Result:
    errors, detail = [], {}
    stage, root = _open(stage_path)
    scope = stage.GetPrimAtPath(f"{root.GetPath()}/{INTEGRATION_SCOPE}")
    if not scope or not scope.IsValid():
        return Result("integrated_honesty_lineage", False,
                      [f"no {INTEGRATION_SCOPE} scope"])

    # The stage documents its own four hops and source layers.
    hops = _get(scope, DEMO_HOPS_ATTR) or []
    if len(list(hops)) != len(HOP_DESCRIPTIONS):
        errors.append(f"{DEMO_HOPS_ATTR} records {len(list(hops))} hops, "
                      f"expected {len(HOP_DESCRIPTIONS)}")
    layers = [str(x) for x in (_get(scope, DEMO_LAYERS_ATTR) or [])]
    detail["source_layers"] = [os.path.basename(x) for x in layers]
    for needed in ("p53_mdm2_topology.usda", "p53_mdm2_genotype.usda",
                   "p53_mdm2_analysis.usda"):
        if not any(needed in x for x in layers):
            errors.append(f"{DEMO_LAYERS_ATTR} does not name {needed}")

    sources = set()
    for variant, prim in sorted(_join_prims(stage, root).items()):
        status = str(_get(prim, JOIN_DDG_STATUS_ATTR) or "")
        source = str(_get(prim, JOIN_DDG_SOURCE_ATTR) or "")
        if not status or not source:
            errors.append(f"{variant}: join row does not carry the ΔΔG "
                          f"status/source lineage")
        sources.add(source)
        if variant != WILDTYPE:
            # The join must PROPAGATE the lineage unchanged, not restate it.
            ctx = _variant_values(root, variant,
                                  [JOIN_DDG_STATUS_ATTR, JOIN_DDG_SOURCE_ATTR])
            for name, join_val in ((JOIN_DDG_STATUS_ATTR, status),
                                   (JOIN_DDG_SOURCE_ATTR, source)):
                ctx_val = str(ctx[name] or "")
                if ctx_val != join_val:
                    errors.append(
                        f"{variant}: join {name}={join_val!r} != variant-context "
                        f"{ctx_val!r} -- lineage rewritten, not propagated")
        if variant == WILDTYPE:
            # No fabricated baseline numerics: the reference .cfg IS the WT model.
            if status != BASELINE_STATUS:
                errors.append(f"{WILDTYPE}: ΔΔG status is {status!r}, expected "
                              f"{BASELINE_STATUS!r}")
            if _get(prim, JOIN_DDG_ATTR) is not None:
                errors.append(f"{WILDTYPE}: carries a ΔΔG numeric -- the wild "
                              f"type has no ΔΔG by construction")
            if _get(prim, JOIN_S_ATTR) is not None:
                errors.append(f"{WILDTYPE}: carries a correlated S -- none is "
                              f"derivable without a ΔΔG")
    detail["ddg_sources"] = sorted(sources)

    prov = str(_get(scope, "bio:demo:provenance") or "").lower()
    if "fixture" in sources and "fixture" not in prov:
        errors.append("the sweep is fixture-derived but the integration "
                      "provenance does not say so")
    return Result("integrated_honesty_lineage", not errors, errors, detail)


# ---------------------------------------------------------------------------
# Harness entry point
# ---------------------------------------------------------------------------
def _skip(reason: str) -> Result:
    return Result("integrated_maboss_SKIPPED", True, [],
                  {"skipped": True, "reason": reason,
                   "note": "non-substantive skip; MaBoSS could not run "
                           "(no fabricated data asserted)"})


def run(stage_path: Optional[str] = None) -> list:
    stage_path = stage_path or default_integrated_path()
    if not os.path.isfile(stage_path):
        return [Result("integrated_stage_exists", False,
                       [f"not found: {stage_path} -- run "
                        f"demos/run_end_to_end.py"])]
    pdb_path = p53_env.get_structure_path("1ycr.pdb")

    results = [
        assert_composition(stage_path, pdb_path),
        assert_ddg_lineage(stage_path),
        assert_correlation(stage_path),
    ]

    # Hops 4-5 need the independent MaBoSS oracle.
    try:
        probtrajs = run_maboss.run_all()
    except MabossUnavailableError as exc:
        results.append(_skip(str(exc)))
    except Exception as exc:  # pragma: no cover -- surface unexpected failures
        results.append(Result("integrated_maboss_rerun", False,
                              [f"independent re-run failed: {exc}"]))
    else:
        results.append(assert_maboss_readout(stage_path, probtrajs))
        results.append(assert_destabilization_ordering(stage_path, probtrajs))

    results.append(assert_departmental_layering(stage_path))
    results.append(assert_honesty_lineage(stage_path))
    return results


if __name__ == "__main__":
    rs = run()
    ok = all(r.passed for r in rs)
    for r in rs:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.check_name}")
        for e in r.errors:
            print(f"    - {e}")
        if r.detail:
            for key, val in r.detail.items():
                print(f"    {key}: {val}")
    raise SystemExit(0 if ok else 1)
