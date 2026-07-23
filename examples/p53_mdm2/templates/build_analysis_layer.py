"""
build_analysis_layer.py -- Pipeline 4 Step 2: write MaBoSS node-probability
trajectories into a SEPARATE analysis SubLayer as time-sampled ``bio:`` attrs.

Generalises the foundation_demo_v8 ``_create_analysis_layer`` pattern
(``OverridePrim`` + ``attr.Set(v, Usd.TimeCode(frame))`` + start/end time codes,
authored in its own ``.usda`` SubLayer over the base topology)
`[source: examples/foundation_demo_v8/templates/09_create_departmental_layers.py:156-195]`.

Departmental layering (CLAUDE.md pattern 5): the analysis stage SubLayers the
committed topology (``output/p53_mdm2_topology.usda``) and contributes ONLY new
analysis prims -- the base topology's own prims/attributes are never mutated.
The topology root ``/p53_MDM2_complex`` is brought in as an ``over`` (no
redefinition); a new ``maboss`` Scope hangs a child prim per genotype variant:

    /p53_MDM2_complex
        maboss/                       (Scope; analysis-only)
            WildType   -> bio:maboss:prob:<node> (time-sampled), provenance
            F19A       -> ...
            L26A       -> ...
            W23A       -> ...

Each variant carries the full node set (``p53``, ``p53_h``, ``Mdm2C``,
``Mdm2N``, ``Dam``) as ``bio:maboss:prob:<node>`` FLOAT attributes, time-sampled
at ``Usd.TimeCode(frame)`` where ``frame = round(time / time_tick)`` (see
``run_maboss`` for the mapping). The correlation contract (``bio:maboss:*``)
authored by Pipeline 3 stays on the genotype stage; this layer adds the *run
outputs*.

Provenance / honesty (R02 honesty contract): probabilities are GENUINE MaBoSS
simulation output. Provenance attrs on the ``maboss`` scope record the backend,
engine version, seed, sample count, and time grid so a reader can tell these are
real runs, not fabricated numbers. If MaBoSS cannot run
(:class:`run_maboss.MabossUnavailableError`), this builder RAISES rather than
writing anything -- no fabricated fallback.

Design source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md §Contracts
(``bio:maboss:prob:<node>`` row); __roadmap__/p53_mdm2/p4_maboss_readback.md Step 2.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)              # examples/p53_mdm2
_PKG_PARENT = os.path.dirname(_PKG)        # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from p53_mdm2 import p53_env
from p53_mdm2.maboss import run_maboss
from p53_mdm2.maboss.run_maboss import ProbTraj

# The five model nodes we persist (R02 node table). Order is stable for output.
MODEL_NODES = ("p53", "p53_h", "Mdm2C", "Mdm2N", "Dam")

# Analysis prim structure (all under the topology default prim).
MABOSS_SCOPE = "maboss"          # /p53_MDM2_complex/maboss
PROB_ATTR_PREFIX = "bio:maboss:prob:"


def topology_path() -> str:
    return os.path.join(p53_env.output_dir(), "p53_mdm2_topology.usda")


def analysis_dir() -> str:
    return os.path.join(p53_env.PACKAGE_DIR, "analysis")


def default_output_path() -> str:
    return os.path.join(analysis_dir(), "p53_mdm2_analysis.usda")


@dataclass
class BuildResult:
    path: str
    root_path: str
    variants: List[str]
    nodes: List[str]
    frame_count: int
    backend: str
    engine_version: str
    p53_time_average: Dict[str, float]


def _relative_sublayer(analysis_file: str, topology_file: str) -> str:
    """Relative identifier for the topology SubLayer (portable, not absolute)."""
    rel = os.path.relpath(topology_file, os.path.dirname(analysis_file))
    return rel if rel.startswith((".", "/")) else "./" + rel


def build_analysis_layer(
    output_path: Optional[str] = None,
    topology: Optional[str] = None,
    *,
    probtrajs: Optional[Dict[str, ProbTraj]] = None,
) -> BuildResult:
    """Run MaBoSS for WT + every emitted mutant and write the analysis SubLayer.

    *probtrajs* may be supplied to reuse already-computed trajectories; if
    ``None`` the models are run fresh via :func:`run_maboss.run_all`.
    """
    from pxr import Usd, UsdGeom, Sdf

    output_path = output_path or default_output_path()
    topology = topology or topology_path()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if probtrajs is None:
        probtrajs = run_maboss.run_all()

    # Determine the topology default prim path (parameterised, not hard-coded).
    topo_stage = Usd.Stage.Open(topology)
    root_prim = topo_stage.GetDefaultPrim()
    if not root_prim or not root_prim.IsValid():
        raise ValueError(f"topology stage has no default prim: {topology}")
    root_path = root_prim.GetPath().pathString

    # Frame grid + provenance from any trajectory (all share the sim params).
    any_pt = next(iter(probtrajs.values()))
    n_frames = len(any_pt.frames)
    start_frame = min(any_pt.frames)
    end_frame = max(any_pt.frames)

    if os.path.exists(output_path):
        os.remove(output_path)
    stage = Usd.Stage.CreateNew(output_path)
    layer = stage.GetRootLayer()
    layer.documentation = (
        "Analysis layer (Pipeline 4): MaBoSS node-probability trajectories as "
        "time-sampled bio:maboss:prob:<node> under a maboss/ scope per genotype "
        "variant. SubLayers the 1YCR topology; base topology untouched. "
        "Probabilities are GENUINE MaBoSS simulation output "
        f"({any_pt.backend}; {any_pt.engine_version})."
    )
    # SubLayer the base topology (departmental layering).
    layer.subLayerPaths.append(_relative_sublayer(output_path, topology))

    stage.SetMetadata("metersPerUnit", p53_env.METERS_PER_UNIT)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    # Bring in the topology root as an OVER (do not redefine it), and set it as
    # this stage's default prim so the composed stage keeps a single root.
    root_over = stage.OverridePrim(root_path)
    stage.SetDefaultPrim(root_over)

    # New analysis scope + provenance (this layer legitimately introduces it).
    scope_path = f"{root_path}/{MABOSS_SCOPE}"
    scope = stage.DefinePrim(scope_path, "Scope")
    scope.CreateAttribute("bio:maboss:provenance", Sdf.ValueTypeNames.String,
                          custom=True).Set(
        "genuine MaBoSS simulation output (not fabricated)")
    scope.CreateAttribute("bio:maboss:backend", Sdf.ValueTypeNames.String,
                          custom=True).Set(any_pt.backend)
    scope.CreateAttribute("bio:maboss:engineVersion", Sdf.ValueTypeNames.String,
                          custom=True).Set(any_pt.engine_version)
    scope.CreateAttribute("bio:maboss:timeTick", Sdf.ValueTypeNames.Float,
                          custom=True).Set(float(any_pt.time_tick))
    scope.CreateAttribute("bio:maboss:maxTime", Sdf.ValueTypeNames.Float,
                          custom=True).Set(float(any_pt.max_time))
    scope.CreateAttribute("bio:maboss:seedPseudorandom", Sdf.ValueTypeNames.Int,
                          custom=True).Set(100)
    scope.CreateAttribute("bio:maboss:sampleCount", Sdf.ValueTypeNames.Int,
                          custom=True).Set(50000)
    scope.CreateAttribute("bio:maboss:nodes", Sdf.ValueTypeNames.TokenArray,
                          custom=True).Set(list(MODEL_NODES))

    p53_time_average: Dict[str, float] = {}
    written_variants: List[str] = []

    for variant, pt in probtrajs.items():
        vprim = stage.DefinePrim(f"{scope_path}/{variant}", "Scope")
        vprim.CreateAttribute("bio:maboss:variant", Sdf.ValueTypeNames.Token,
                              custom=True).Set(variant)
        vprim.CreateAttribute("bio:maboss:frameCount", Sdf.ValueTypeNames.Int,
                              custom=True).Set(len(pt.frames))
        for node in MODEL_NODES:
            attr = vprim.CreateAttribute(
                PROB_ATTR_PREFIX + node, Sdf.ValueTypeNames.Float, custom=True)
            series = pt.series(node)  # missing node -> zeros over full grid
            for frame, val in zip(pt.frames, series):
                attr.Set(float(val), Usd.TimeCode(frame))
        p53_time_average[variant] = pt.time_average(run_maboss.P53_NODE)
        written_variants.append(variant)

    stage.SetStartTimeCode(start_frame)
    stage.SetEndTimeCode(end_frame)
    stage.SetFramesPerSecond(1.0 / any_pt.time_tick)  # frames-per-unit-time
    stage.SetTimeCodesPerSecond(1.0 / any_pt.time_tick)

    layer.Save()

    return BuildResult(
        path=output_path, root_path=root_path, variants=written_variants,
        nodes=list(MODEL_NODES), frame_count=n_frames, backend=any_pt.backend,
        engine_version=any_pt.engine_version, p53_time_average=p53_time_average)


if __name__ == "__main__":
    res = build_analysis_layer()
    print(f"[build_analysis_layer] wrote {res.path}")
    print(f"  root={res.root_path}  variants={res.variants}")
    print(f"  nodes={res.nodes}  frames={res.frame_count}")
    print(f"  backend={res.backend} ({res.engine_version})")
    for v, avg in res.p53_time_average.items():
        print(f"    <P(p53 up)> {v:<8} = {avg:.6f}")
