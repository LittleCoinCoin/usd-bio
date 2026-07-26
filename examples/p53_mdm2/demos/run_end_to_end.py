#!/usr/bin/env python3
"""
run_end_to_end.py -- Pipeline 5: the integrated p53-MDM2 demonstration.

ONE entry point that drives the four pipelines in order for the wild type plus
every destabilizing p53-peptide variant, and then composes their four committed
departmental layers into a SINGLE USD stage -- the topic's whole thesis: an MD
free-energy signal steering a systems-biology Boolean model, with OpenUSD as the
shared representation on both ends.

The four hops (each DELEGATES to the pipeline module that owns it -- nothing is
reimplemented here; this script is orchestration + the P5 composition only):

    hop 1  P1  topology     builders.build_assembly       1ycr.pdb -> topology .usda
           P1b protocol     templates.md_parameters       bio:md: setup deck (Protocol layer)
    hop 2  P2  ΔΔG          composition.build_genotype    Genotype (Perturbation) VariantSet
                            converters.ddmut_client       ΔΔG -> bio:ddgKcalPerMol per variant
    hop 3  P3  correlation  maboss.dg_correlation         S = 1/(1+exp(-k(ΔΔG-m)))
                            maboss.emit_model             S -> $KMn_pMC*/.cfg + bio:maboss:*
    hop 4  P4  read-back    maboss.run_maboss             real MaBoSS run -> node probtraj
                            templates.build_analysis_layer probtraj -> time-sampled bio:maboss:prob:<node>
    hop 5  P5  integration  THIS module                   the four layers -> one composed stage

The integrated artifact (:func:`default_integrated_path`) is a thin ROOT LAYER.
It contains no copy of any pipeline's data; it contains only

  * the ``subLayers`` list that composes the four departmental layers,
  * the stage-level metadata USD reads from the root layer ONLY (``defaultPrim``,
    ``metersPerUnit``, ``upAxis``, start/end time codes) -- sublayers cannot
    supply these, which is why a dedicated integration root layer is needed,
  * a Local-arc ``Genotype`` variant selection (the "which hypothesis am I
    consulting" switch), and
  * an ``integration`` Scope: the cross-pipeline JOIN, one prim per variant
    carrying (ΔΔG, S, <P(p53 up)>) side by side.

Why the join exists (and is not redundant): the ΔΔG and S of a variant live
INSIDE that variant's edit context, so only ONE variant's values resolve on the
stage at a time; the MaBoSS trajectories live on per-variant analysis prims,
which are all resolvable at once. The join is the one place where the whole
variant sweep -- input ΔΔG, correlated parameter, and simulated outcome -- can be
read in a single traversal. That IS the "integrated MD + systems-biology
consultation" the INTENT names as the done definition.

Honesty (R02 honesty contract):
  * ``<P(p53 up)>`` in the join is computed from the composed analysis layer's
    own time samples -- i.e. from the committed genuine MaBoSS output, not from
    this script's in-memory run.
  * ΔΔG/S status + source tokens are PROPAGATED into the join, so the fixture
    lineage of the ΔΔG inputs (see composition/fixtures/ddmut_ppi_fixture.json --
    synthetic, literature-informed placeholders, NOT DDMut-PPI server output)
    remains visible from the integrated stage alone. The join never launders
    fixture inputs into "measured".
  * The wild type has no ΔΔG and no correlated S by construction (the reference
    ``.cfg`` IS the WT model, $KMn_pMC* = 1); it is tagged ``baseline`` rather
    than given a fabricated 0.0.
  * If MaBoSS cannot run, hop 4 raises and the demo ABORTS -- it never composes a
    stage with fabricated dynamics.

Departmental layering: the integrated stage is a pure composition. The base
Biology topology is never mutated by any downstream hop -- the Analysis layer
brings the root in as an ``over``, and so does this integration layer. Verified
by ``tests/test_integrated.py``.

Usage (from the repo root, OpenUSD env sourced):
    . ./load_env.sh
    PYTHONPATH="$PYTHONPATH:$(pwd)/examples" \
        ~/Documents/src/AOUSD/forOUSD/bin/python3 \
        examples/p53_mdm2/demos/run_end_to_end.py

    # only recompose the integrated stage from the already-committed layers
    #   (skips hops 1-3; hop 4 still runs MaBoSS for real)
    ... run_end_to_end.py --from-committed

    # re-query the live DDMut-PPI API instead of replaying the committed capture
    ... run_end_to_end.py --ddg-source live

Note on the ΔΔG source: hop 2 defaults to ``--ddg-source captured`` -- it replays
the REAL DDMut-PPI server predictions Pipeline 2 committed verbatim under
``data/ddmut_ppi_live/``. That keeps the demo reproducible and network-free while
still standing on genuine server output, and it means a demo run never issues a
fresh live capture that would renumber Pipeline 2's committed evidence. Pass
``--ddg-source live`` to re-query. Whichever source is used, the resulting
``bio:ddgStatus``/``bio:ddgSource`` tokens travel all the way into the integration
join, so the artifact always states its own provenance and
``tests/test_integrated.py`` picks the matching oracle (the verbatim captured
response body vs. the synthetic fixture JSON) from those tokens.

Design source: __roadmap__/p53_mdm2/p5_integrated_demo.md;
__design__/openusd_for_research_architecture.md §4.1 (departmental layering),
§4.2 (Perturbation Variant); __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)              # examples/p53_mdm2
_PKG_PARENT = os.path.dirname(_PKG)        # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from p53_mdm2 import p53_env
from p53_mdm2.maboss import run_maboss
from p53_mdm2.templates import build_analysis_layer

# ---------------------------------------------------------------------------
# Integrated-stage contract (imported by tests -- single source of truth)
# ---------------------------------------------------------------------------
#: Scope holding the cross-pipeline join, one child prim per genotype variant.
INTEGRATION_SCOPE = "integration"

#: Attributes on each join prim. The ``bio:`` names REUSE the spellings the
#: owning pipelines already author (no new vocabulary except the two below).
JOIN_DDG_ATTR = "bio:ddgKcalPerMol"          # P2 (mutants only)
JOIN_DDG_STATUS_ATTR = "bio:ddgStatus"       # P2
JOIN_DDG_SOURCE_ATTR = "bio:ddgSource"       # P2
JOIN_S_ATTR = "bio:maboss:paramValue"        # P3
JOIN_S_STATUS_ATTR = "bio:maboss:paramValueStatus"   # P3
#: NEW in P5: the time-averaged read-out of the P4 trajectory, and its frame count.
JOIN_P53_AVG_ATTR = "bio:maboss:p53TimeAverage"
JOIN_FRAME_COUNT_ATTR = "bio:maboss:frameCount"

#: Provenance attributes on the integration scope itself.
DEMO_HOPS_ATTR = "bio:demo:hops"
DEMO_LAYERS_ATTR = "bio:demo:sourceLayers"
DEMO_READOUT_ATTR = "bio:demo:readoutNode"

#: Token written for the wild-type baseline, which has no ΔΔG by construction.
BASELINE_STATUS = "baseline"
BASELINE_SOURCE = "wild-type-reference"

#: The four hops, recorded onto the stage so the artifact is self-describing.
HOP_DESCRIPTIONS = (
    "1: MD/structure -> USD topology (1YCR -> bio: atoms, elements, bonds)",
    "2: USD -> ΔΔG (Genotype VariantSet -> DDMut-PPI -> bio:ddgKcalPerMol)",
    "3: ΔΔG -> MaBoSS model (logistic correlation -> $KMn_pMC*, bio:maboss:*)",
    "4: MaBoSS run -> USD (node probtraj -> time-sampled bio:maboss:prob:<node>)",
)

WILDTYPE = "WildType"


def demos_dir() -> str:
    return _HERE


def default_integrated_path() -> str:
    """Canonical committed location for the integrated (P5) stage."""
    return os.path.join(_HERE, "p53_mdm2_integrated.usda")


def topology_path() -> str:
    return os.path.join(p53_env.output_dir(), "p53_mdm2_topology.usda")


def md_setup_path() -> str:
    from p53_mdm2.templates.md_parameters import default_output_path
    return default_output_path()


def genotype_path() -> str:
    from p53_mdm2.composition.build_genotype import default_output_path
    return default_output_path()


def analysis_path() -> str:
    return build_analysis_layer.default_output_path()


def source_layers() -> List[str]:
    """The departmental layers the integrated stage composes, STRONGEST FIRST.

    LIVERPS 'L' (Local + SubLayers): an earlier sublayer wins over a later one.
    Analysis is strongest because a re-analysis must be able to override an
    earlier opinion without touching Biology; Biology (topology) is weakest
    because it is the shared ground truth every other layer annotates.
    """
    return [analysis_path(), genotype_path(), md_setup_path()]


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------
@dataclass
class VariantSummary:
    """One row of the cross-pipeline join."""
    variant: str
    ddg: Optional[float] = None          # P2, kcal/mol (None for WT)
    ddg_status: str = BASELINE_STATUS    # P2
    ddg_source: str = BASELINE_SOURCE    # P2
    s: Optional[float] = None            # P3 correlated parameter (None for WT)
    s_status: str = BASELINE_STATUS      # P3
    p53_time_average: float = 0.0        # P4 read-out, from the USD time samples
    frame_count: int = 0                 # P4


@dataclass
class DemoResult:
    integrated_path: str
    root_path: str
    source_layers: List[str] = field(default_factory=list)
    summaries: Dict[str, VariantSummary] = field(default_factory=dict)
    backend: str = ""
    engine_version: str = ""


# ---------------------------------------------------------------------------
# Hops 1-4: delegate to the pipeline modules that own them
# ---------------------------------------------------------------------------
def hop1_topology_and_protocol(*, verbose: bool = True) -> None:
    """P1 + P1b: Biology topology and the Protocol MD-setup deck."""
    from p53_mdm2.builders.build_assembly import build_assembly
    from p53_mdm2.templates.md_parameters import build_md_setup_artifact

    if verbose:
        print("\n=== hop 1/5 -- P1 Biology topology + P1b Protocol deck ===")
    os.makedirs(p53_env.output_dir(), exist_ok=True)
    build_assembly(topology_path(), p53_env.get_structure_path("1ycr.pdb"),
                   system_name="p53-MDM2 complex (1YCR)")
    build_md_setup_artifact(md_setup_path())


def hop2_genotype_and_ddg(*, ddg_source: str = "captured",
                          verbose: bool = True) -> dict:
    """P2: Genotype (Perturbation) VariantSet + the ΔΔG write-back.

    *ddg_source* is passed straight through to
    :func:`converters.ddmut_client.write_back_ddg` -- this demo treats the ΔΔG
    provenance as a PARAMETER and does not second-guess Pipeline 2's error model.
    """
    from p53_mdm2.composition.build_genotype import build_genotype_assembly
    from p53_mdm2.converters.ddmut_client import write_back_ddg

    if verbose:
        print(f"\n=== hop 2/5 -- P2 Genotype VariantSet + ΔΔG "
              f"(source={ddg_source}) ===")
    build_genotype_assembly(genotype_path(),
                            p53_env.get_structure_path("1ycr.pdb"))
    return write_back_ddg(genotype_path(), source=ddg_source, verbose=verbose)


def hop3_emit_maboss(*, verbose: bool = True) -> list:
    """P3: ΔΔG -> S -> MaBoSS ``.bnd``/``.cfg`` + the ``bio:maboss:*`` contract."""
    from p53_mdm2.maboss.emit_model import emit_from_stage, output_dir

    if verbose:
        print("\n=== hop 3/5 -- P3 ΔΔG<->parameter correlation -> MaBoSS model ===")
    emitted = emit_from_stage(genotype_path())
    if verbose:
        print(f"  emitted {len(emitted)} model(s) into {output_dir()}")
        for r in emitted:
            print(f"    {r.variant:<8} ΔΔG={r.ddg:+.3f}  S={r.s:.6f}  "
                  f"[{r.status}/{r.source}]")
    if not emitted:
        raise RuntimeError(
            "hop 3 emitted no MaBoSS models -- no variant carried a "
            "value-bearing ΔΔG. Refusing to continue with an empty sweep.")
    return emitted


def hop4_run_and_read_back(*, verbose: bool = True):
    """P4: run MaBoSS for real and write the Analysis SubLayer.

    Raises :class:`run_maboss.MabossUnavailableError` when no MaBoSS backend
    exists -- the demo ABORTS rather than composing fabricated dynamics.
    """
    if verbose:
        print("\n=== hop 4/5 -- P4 real MaBoSS run -> time-sampled USD ===")
    run_maboss.ensure_backend()          # raises MabossUnavailableError, honestly
    probtrajs = run_maboss.run_all()
    result = build_analysis_layer.build_analysis_layer(probtrajs=probtrajs)
    if verbose:
        print(f"  backend={result.backend} ({result.engine_version})")
        print(f"  wrote {result.path}  variants={result.variants} "
              f"frames={result.frame_count}")
    return result


# ---------------------------------------------------------------------------
# Hop 5: the P5 composition
# ---------------------------------------------------------------------------
def _relative_sublayer(from_file: str, target: str) -> str:
    rel = os.path.relpath(target, os.path.dirname(from_file))
    return rel if rel.startswith((".", "/")) else "./" + rel


def _read_variant_ddg_and_s(stage, root, variant) -> VariantSummary:
    """Read (ΔΔG, S, status tokens) for *variant* off the COMPOSED stage.

    The values are resolved through the Genotype VariantSet, i.e. they are read
    exactly the way a downstream consumer of the integrated stage would read
    them -- not copied out of any builder's return value.
    """
    genotype = root.GetVariantSets().GetVariantSet("Genotype")
    previous = genotype.GetVariantSelection()
    genotype.SetVariantSelection(variant)
    try:
        def _get(name):
            a = root.GetAttribute(name)
            return a.Get() if a.IsValid() else None

        ddg = _get(JOIN_DDG_ATTR)
        s = _get(JOIN_S_ATTR)
        return VariantSummary(
            variant=variant,
            ddg=float(ddg) if ddg is not None else None,
            ddg_status=str(_get(JOIN_DDG_STATUS_ATTR) or BASELINE_STATUS),
            ddg_source=str(_get(JOIN_DDG_SOURCE_ATTR) or BASELINE_SOURCE),
            s=float(s) if s is not None else None,
            s_status=str(_get(JOIN_S_STATUS_ATTR) or BASELINE_STATUS),
        )
    finally:
        genotype.SetVariantSelection(previous)


def _usd_time_average(stage, scope_path: str, variant: str, node: str):
    """(mean, n) of a time-sampled ``bio:maboss:prob:<node>`` on the composed stage."""
    from pxr import Usd

    prim = stage.GetPrimAtPath(f"{scope_path}/{variant}")
    if not prim or not prim.IsValid():
        return None, 0
    attr = prim.GetAttribute(build_analysis_layer.PROB_ATTR_PREFIX + node)
    if not attr.IsValid():
        return None, 0
    samples = attr.GetTimeSamples()
    if not samples:
        return None, 0
    vals = [float(attr.Get(Usd.TimeCode(t))) for t in samples]
    return sum(vals) / len(vals), len(vals)


def build_integrated_stage(
    output_path: Optional[str] = None,
    *,
    layers: Optional[List[str]] = None,
    default_variant: str = WILDTYPE,
    verbose: bool = True,
) -> DemoResult:
    """Compose the committed departmental layers into the single P5 stage.

    Two passes, deliberately:

      pass A  author the ``subLayers`` list + the root-layer-only stage metadata,
              save, and REOPEN. Everything after this point reads the COMPOSED
              stage, so the join is built from resolved composition -- never from
              a builder's in-memory state.
      pass B  read (ΔΔG, S) per variant through the Genotype VariantSet and
              <P(p53 up)> from the Analysis layer's time samples, then author the
              ``integration`` join + provenance into the same root layer.
    """
    from pxr import Usd, UsdGeom, Sdf

    output_path = output_path or default_integrated_path()
    layers = layers or source_layers()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    missing = [p for p in (*layers, topology_path()) if not os.path.isfile(p)]
    if missing:
        raise FileNotFoundError(
            "hop 5 cannot compose -- missing upstream layer(s): "
            + ", ".join(missing))

    if verbose:
        print("\n=== hop 5/5 -- P5 compose the integrated stage ===")

    # ---- pass A: the compositional root layer -----------------------------
    if os.path.exists(output_path):
        os.remove(output_path)
    stage = Usd.Stage.CreateNew(output_path)
    layer = stage.GetRootLayer()
    for src in layers:
        layer.subLayerPaths.append(_relative_sublayer(output_path, src))

    # The topology default prim path is READ, never hard-coded.
    topo_stage = Usd.Stage.Open(topology_path())
    topo_root = topo_stage.GetDefaultPrim()
    if not topo_root or not topo_root.IsValid():
        raise ValueError(f"topology stage has no default prim: {topology_path()}")
    root_path = topo_root.GetPath().pathString

    # Bring the complex root in as an OVER: this integration layer contributes
    # no topology of its own and must not redefine the Biology layer's root.
    root_over = stage.OverridePrim(root_path)
    stage.SetDefaultPrim(root_over)

    # Stage metadata USD resolves from the ROOT LAYER ONLY -- a sublayered
    # analysis layer's own start/end time codes and defaultPrim do NOT propagate
    # up, which is precisely why P5 needs its own root layer.
    stage.SetMetadata("metersPerUnit", p53_env.METERS_PER_UNIT)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    analysis_stage = Usd.Stage.Open(analysis_path())
    stage.SetStartTimeCode(analysis_stage.GetStartTimeCode())
    stage.SetEndTimeCode(analysis_stage.GetEndTimeCode())
    stage.SetTimeCodesPerSecond(analysis_stage.GetTimeCodesPerSecond())
    stage.SetFramesPerSecond(analysis_stage.GetFramesPerSecond())
    layer.Save()

    # ---- pass B: read the COMPOSED stage, then author the join ------------
    stage = Usd.Stage.Open(output_path)
    root = stage.GetDefaultPrim()
    # HasVariantSet is the real existence check -- GetVariantSet(name).IsValid()
    # returns a valid handle for ANY name and would never catch a failed compose.
    if not root.GetVariantSets().HasVariantSet("Genotype"):
        raise ValueError(
            "integrated stage has no Genotype VariantSet -- the Perturbation "
            "layer did not compose")
    genotype = root.GetVariantSets().GetVariantSet("Genotype")

    maboss_scope_path = f"{root_path}/{build_analysis_layer.MABOSS_SCOPE}"
    maboss_scope = stage.GetPrimAtPath(maboss_scope_path)
    if not maboss_scope or not maboss_scope.IsValid():
        raise ValueError(
            "integrated stage has no maboss analysis scope -- the Analysis "
            "layer did not compose")

    def _scope_attr(name):
        a = maboss_scope.GetAttribute(name)
        return a.Get() if a.IsValid() else None

    backend = str(_scope_attr("bio:maboss:backend") or "unknown")
    engine_version = str(_scope_attr("bio:maboss:engineVersion") or "unknown")

    # Variants to join = those the Analysis layer actually simulated.
    simulated = [c.GetName() for c in maboss_scope.GetChildren()]
    summaries: Dict[str, VariantSummary] = {}
    for variant in simulated:
        summary = (_read_variant_ddg_and_s(stage, root, variant)
                   if variant in genotype.GetVariantNames()
                   else VariantSummary(variant=variant))
        avg, n = _usd_time_average(stage, maboss_scope_path, variant,
                                  run_maboss.P53_NODE)
        if avg is None:
            raise ValueError(
                f"no {run_maboss.P53_NODE} time samples for {variant} on the "
                f"composed stage -- refusing to author an empty join row")
        summary.p53_time_average = avg
        summary.frame_count = n
        summaries[variant] = summary

    # Author the join into the integration root layer (LIVERPS 'L': a Local
    # opinion, the consultation view over the composed departmental layers).
    scope = stage.DefinePrim(f"{root_path}/{INTEGRATION_SCOPE}", "Scope")
    scope.CreateAttribute(DEMO_HOPS_ATTR, Sdf.ValueTypeNames.StringArray,
                          custom=True).Set(list(HOP_DESCRIPTIONS))
    scope.CreateAttribute(
        DEMO_LAYERS_ATTR, Sdf.ValueTypeNames.StringArray, custom=True).Set(
        [_relative_sublayer(output_path, p) for p in layers]
        + [_relative_sublayer(output_path, topology_path())])
    scope.CreateAttribute(DEMO_READOUT_ATTR, Sdf.ValueTypeNames.Token,
                          custom=True).Set(run_maboss.P53_NODE)
    scope.CreateAttribute("bio:maboss:backend", Sdf.ValueTypeNames.String,
                          custom=True).Set(backend)
    scope.CreateAttribute("bio:maboss:engineVersion", Sdf.ValueTypeNames.String,
                          custom=True).Set(engine_version)
    scope.CreateAttribute(
        "bio:demo:provenance", Sdf.ValueTypeNames.String, custom=True).Set(
        "Cross-pipeline join derived from the composed departmental layers "
        "(ΔΔG + S read through the Genotype VariantSet; <P(node up)> averaged "
        "over the Analysis layer's committed MaBoSS time samples). The ΔΔG "
        "status/source tokens below carry the input lineage unchanged -- a "
        "'fixture' ΔΔG is never presented as measured or predicted.")

    for variant in sorted(summaries):
        s = summaries[variant]
        prim = stage.DefinePrim(f"{scope.GetPath()}/{variant}", "Scope")
        prim.CreateAttribute("bio:maboss:variant", Sdf.ValueTypeNames.Token,
                             custom=True).Set(variant)
        prim.CreateAttribute(JOIN_DDG_STATUS_ATTR, Sdf.ValueTypeNames.Token,
                             custom=True).Set(s.ddg_status)
        prim.CreateAttribute(JOIN_DDG_SOURCE_ATTR, Sdf.ValueTypeNames.Token,
                             custom=True).Set(s.ddg_source)
        # Numerics authored ONLY where a real value exists (WT has no ΔΔG/S).
        if s.ddg is not None:
            prim.CreateAttribute(JOIN_DDG_ATTR, Sdf.ValueTypeNames.Float,
                                 custom=True).Set(float(s.ddg))
            prim.CreateAttribute("bio:ddgUnits", Sdf.ValueTypeNames.Token,
                                 custom=True).Set("kcal/mol")
        if s.s is not None:
            prim.CreateAttribute(JOIN_S_ATTR, Sdf.ValueTypeNames.Float,
                                 custom=True).Set(float(s.s))
            prim.CreateAttribute(JOIN_S_STATUS_ATTR, Sdf.ValueTypeNames.Token,
                                 custom=True).Set(s.s_status)
        prim.CreateAttribute(JOIN_P53_AVG_ATTR, Sdf.ValueTypeNames.Float,
                             custom=True).Set(float(s.p53_time_average))
        prim.CreateAttribute(JOIN_FRAME_COUNT_ATTR, Sdf.ValueTypeNames.Int,
                             custom=True).Set(int(s.frame_count))

    # Local-arc hypothesis switch: which genotype this stage opens on.
    if default_variant in genotype.GetVariantNames():
        genotype.SetVariantSelection(default_variant)

    layer.documentation = (
        "Integrated demonstration (Pipeline 5): a single composed stage carrying "
        "the 1YCR Biology topology, the Protocol bio:md: setup deck, the "
        "Perturbation Genotype VariantSet with its DDMut-PPI ΔΔG and correlated "
        "MaBoSS parameter S, and the time-sampled MaBoSS node probabilities -- "
        "across four departmental SubLayers. This root layer adds ONLY the "
        "subLayers list, the root-layer-only stage metadata, a Local Genotype "
        "selection, and the integration/ cross-pipeline join. "
        f"MaBoSS backend: {backend} ({engine_version})."
    )
    layer.Save()

    if verbose:
        print(f"  wrote {output_path}")
        print(f"  root={root_path}  subLayers="
              f"{[os.path.basename(p) for p in layers]}")
        print(f"  {'variant':<9} {'ΔΔG':>7} {'S':>9} {'<P(p53 up)>':>12}  lineage")
        for variant in sorted(summaries, key=lambda v: summaries[v].p53_time_average):
            s = summaries[variant]
            ddg = f"{s.ddg:+.2f}" if s.ddg is not None else "   --"
            sval = f"{s.s:.6f}" if s.s is not None else "      --"
            print(f"  {variant:<9} {ddg:>7} {sval:>9} "
                  f"{s.p53_time_average:>12.6f}  [{s.ddg_status}/{s.ddg_source}]")

    return DemoResult(integrated_path=output_path, root_path=root_path,
                      source_layers=list(layers), summaries=summaries,
                      backend=backend, engine_version=engine_version)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def run_end_to_end(*, ddg_source: str = "captured",
                   from_committed: bool = False,
                   verbose: bool = True) -> DemoResult:
    """Drive all four pipelines, then compose the integrated stage.

    Args:
        ddg_source: forwarded verbatim to Pipeline 2's ``write_back_ddg``.
            ``captured`` (the default) replays the committed REAL DDMut-PPI
            server output with no network; ``live`` re-queries the API;
            ``fixture`` is the synthetic offline fallback; ``auto`` tries live
            then degrades. Pipeline 2 owns this vocabulary -- the demo only
            passes it through and records whatever lineage comes back.
        from_committed: skip hops 1-3 and reuse the committed topology/protocol/
            genotype artifacts. Hop 4 (the real MaBoSS run) always executes.
    """
    if verbose:
        print("p53-MDM2 end-to-end integrated demonstration (Pipeline 5)")
        print("  MD/structure -> USD -> ΔΔG -> MaBoSS -> USD")
    if not from_committed:
        hop1_topology_and_protocol(verbose=verbose)
        hop2_genotype_and_ddg(ddg_source=ddg_source, verbose=verbose)
        hop3_emit_maboss(verbose=verbose)
    elif verbose:
        print("\n=== hops 1-3 SKIPPED (--from-committed): reusing committed "
              "topology / protocol / genotype / MaBoSS models ===")
    hop4_run_and_read_back(verbose=verbose)
    return build_integrated_stage(verbose=verbose)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="p53-MDM2 end-to-end integrated demonstration (P5)")
    ap.add_argument("--ddg-source",
                    choices=("captured", "live", "fixture", "auto"),
                    default="captured",
                    help="ΔΔG provenance for hop 2, forwarded to Pipeline 2 "
                         "(default: 'captured' -- replay the committed REAL "
                         "DDMut-PPI server values offline). Use 'live' to "
                         "re-query the API, 'fixture' for the synthetic "
                         "offline fallback.")
    ap.add_argument("--from-committed", action="store_true",
                    help="skip hops 1-3 and recompose from the committed "
                         "artifacts (hop 4 still runs MaBoSS for real)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    try:
        result = run_end_to_end(ddg_source=args.ddg_source,
                                from_committed=args.from_committed,
                                verbose=not args.quiet)
    except run_maboss.MabossUnavailableError as exc:
        print(f"\n[run_end_to_end] ABORT: MaBoSS unavailable -- {exc}")
        print("  No integrated stage was written. The demo refuses to compose "
              "a stage with fabricated dynamics.")
        return 2

    if not args.quiet:
        print(f"\nDone. Inspect with:  usdcat --flatten {result.integrated_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
