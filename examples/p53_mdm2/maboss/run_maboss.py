"""
run_maboss.py -- Pipeline 4 Step 1: run the MaBoSS model emitted by Pipeline 3
(via pyMaBoSS) and parse its node-probability trajectories over time.

This is the *run* boundary R02 deferred to Pipeline 4: Pipeline 3 emits ``.bnd``/
``.cfg`` as pure text; here we finally load and run them and read the
node-probability probtraj (``get_nodes_probtraj``: P(node up) over time).

Backend (honest account of what actually runs here)
---------------------------------------------------
The ``maboss`` PyPI package ships two run paths:

  * ``cmaboss`` -- a compiled in-process backend (``maboss.load(..., cmaboss=True)``);
  * the default path, which shells out to a standalone ``MaBoSS`` executable.

On this machine the ``cmaboss`` beta (1.0.0b32) returns an EMPTY / flaky node-name
set from ``get_nodes_probtraj()`` (and empty state labels), so it is NOT trusted
for node probabilities. The standalone ``MaBoSS 2.6.6`` binary (installed via
``python -c "import maboss_setup"`` into ``~/.local/share/colomoto``) is reliable
and deterministic, so this module drives the DEFAULT (external-binary) path and
merely ensures that binary is discoverable on ``PATH`` / ``DYLD_LIBRARY_PATH``.

If no ``MaBoSS`` binary can be found, :func:`ensure_backend` raises
:class:`MabossUnavailableError` -- a clear, catchable signal so downstream
callers (analysis-layer build, read-back test) SKIP honestly instead of
fabricating probabilities.

Encoding note
-------------
The reference ``p53_Mdm2.bnd`` (copied byte-identical into every emitted model)
contains two non-UTF-8 bytes (``0xC9``) inside code comments. ``maboss.load``
opens files as UTF-8 and would choke, so we read the ``.bnd``/``.cfg`` as
Latin-1 and re-serialise UTF-8 into a transient temp copy for the run ONLY -- the
committed model files are never touched (their byte-identical-to-reference
invariant, R02, is preserved).

Determinism
-----------
The emitted ``.cfg`` sets ``seed_pseudorandom=100`` and ``thread_count=1``; runs
are reproducible, so a fresh re-run is a valid INDEPENDENT oracle for the
read-back test (no need to persist raw MaBoSS output).

Time -> frame mapping
---------------------
MaBoSS reports at times ``0.0, time_tick, 2*time_tick, ... < max_time`` (here
``time_tick=0.1``, ``max_time=50`` -> 500 points ``0.0 .. 49.9``). We map each
report to an integer USD frame ``frame = round(time / time_tick)`` (so
``frame = 0, 1, ..., 499`` and ``time = frame * time_tick``). The mapping is
carried into the analysis layer as ``bio:maboss:timeTick`` so wall-clock time is
recoverable from the USD frame alone.

Design source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md (pyMaBoSS
call shape, node table, sim params); __roadmap__/p53_mdm2/p4_maboss_readback.md.
"""

from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from p53_mdm2.maboss import emit_model

# The MaBoSS node whose P(up) is the biological read-out (R02 node table:
# ``p53.logic = NOT Mdm2N``). ``p53_h`` is a companion "helper" p53 node.
P53_NODE = "p53"

# Sim params baked into the reference/emitted .cfg (R02 §Every tunable parameter).
DEFAULT_TIME_TICK = 0.1
DEFAULT_MAX_TIME = 50.0

# Candidate directories that may hold the standalone MaBoSS binary + its libs.
# colomoto's maboss_setup installs into ~/.local/share/colomoto/{bin,lib}.
_HOME = os.path.expanduser("~")
_BINARY_DIRS = (
    os.path.join(_HOME, ".local", "share", "colomoto", "bin"),
    os.path.join(_HOME, ".local", "share", "maboss", "bin"),
)
_LIB_DIRS = (
    os.path.join(_HOME, ".local", "share", "colomoto", "lib"),
    os.path.join(_HOME, ".local", "share", "maboss", "lib"),
)


class MabossUnavailableError(RuntimeError):
    """Raised when neither the ``maboss`` package nor a usable ``MaBoSS`` binary
    can be found. Callers should catch this and SKIP (never fabricate)."""


@dataclass
class ProbTraj:
    """Plain-Python node-probability trajectory (no pandas dependency leaks out).

    ``times[i]`` is the MaBoSS report time (float); ``prob[node][i]`` is
    P(node up) at that time; ``frames[i]`` is the integer USD frame. Nodes that
    never leave 0 may be absent from ``prob`` -- use :meth:`series` which treats
    a missing node as an all-zero series over the full time grid.
    """
    variant: str
    times: List[float]
    frames: List[int]
    prob: Dict[str, List[float]]
    nodes: List[str]
    time_tick: float
    max_time: float
    backend: str
    engine_version: str

    def series(self, node: str) -> List[float]:
        """P(node up) over the full time grid; missing node -> zeros."""
        if node in self.prob:
            return self.prob[node]
        return [0.0] * len(self.times)

    def at_frame(self, node: str, frame: int) -> float:
        return self.series(node)[self.frames.index(frame)]

    def time_average(self, node: str) -> float:
        """Simple mean of P(node up) over reported times (uniform grid)."""
        s = self.series(node)
        return sum(s) / len(s) if s else 0.0


# ---------------------------------------------------------------------------
# Backend discovery / environment
# ---------------------------------------------------------------------------
def _prepend_env(var: str, path: str) -> None:
    if not os.path.isdir(path):
        return
    cur = os.environ.get(var, "")
    parts = cur.split(os.pathsep) if cur else []
    if path not in parts:
        os.environ[var] = os.pathsep.join([path, *parts]) if parts else path


def find_maboss_binary() -> Optional[str]:
    """Return the path to a runnable ``MaBoSS`` executable, or ``None``."""
    import shutil
    for d in _BINARY_DIRS:
        cand = os.path.join(d, "MaBoSS")
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return shutil.which("MaBoSS")


def ensure_backend() -> str:
    """Make the external ``MaBoSS`` binary discoverable and return its path.

    Prepends the binary dir to ``PATH`` and the lib dir to
    ``DYLD_LIBRARY_PATH`` / ``LD_LIBRARY_PATH`` (the colomoto build links
    ``@rpath/libsbml.5.dylib``). Raises :class:`MabossUnavailableError` if the
    ``maboss`` package or the binary is missing.
    """
    try:
        import maboss  # noqa: F401
    except ImportError as exc:
        raise MabossUnavailableError(
            "the 'maboss' Python package is not installed "
            "(pip install maboss)") from exc

    binary = find_maboss_binary()
    if binary is None:
        raise MabossUnavailableError(
            "no standalone 'MaBoSS' executable found. Install it with "
            "`python -c \"import maboss_setup\"` (fetches colomoto/maboss) or "
            "put a MaBoSS binary on PATH.")

    _prepend_env("PATH", os.path.dirname(binary))
    for lib in _LIB_DIRS:
        _prepend_env("DYLD_LIBRARY_PATH", lib)
        _prepend_env("LD_LIBRARY_PATH", lib)
    return binary


def maboss_version() -> str:
    binary = find_maboss_binary()
    if binary is None:
        return "unknown"
    import subprocess
    try:
        out = subprocess.run([binary, "--version"], capture_output=True,
                             text=True, timeout=30)
        first = (out.stdout + out.stderr).splitlines()
        return first[0].strip() if first else "unknown"
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Model file resolution + sanitising
# ---------------------------------------------------------------------------
def variant_model_paths(variant: str) -> tuple:
    """(bnd_path, cfg_path) for *variant*. WT -> the verbatim reference model;
    a mutant -> the Pipeline-3 emitted model under maboss/output/."""
    if variant in ("WildType", "WT", "wildtype"):
        return emit_model.reference_bnd_path(), emit_model.reference_cfg_path()
    out = emit_model.output_dir()
    return (os.path.join(out, f"p53_Mdm2_{variant}.bnd"),
            os.path.join(out, f"p53_Mdm2_{variant}.cfg"))


def _sanitise_to_utf8(src: str, dst: str) -> None:
    """Copy *src* -> *dst* re-encoded UTF-8 (Latin-1 in). The reference .bnd
    carries two 0xC9 bytes in comments; this makes maboss.load's UTF-8 open
    succeed without altering any model semantics (comments are ignored)."""
    with open(src, "rb") as fh:
        raw = fh.read()
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(raw.decode("latin-1"))


# ---------------------------------------------------------------------------
# Run + parse
# ---------------------------------------------------------------------------
def run_cfg(bnd_path: str, cfg_path: str, *, variant: str = "?") -> ProbTraj:
    """Run one MaBoSS model and return its node-probability :class:`ProbTraj`.

    Uses the external-binary path (``maboss.load(...).run()`` without
    ``cmaboss``). Converts the pandas DataFrame to plain Python so no pandas
    dependency leaks to callers/tests.
    """
    ensure_backend()
    import maboss

    for p in (bnd_path, cfg_path):
        if not os.path.isfile(p):
            raise FileNotFoundError(f"MaBoSS model file missing: {p}")

    tmp = tempfile.mkdtemp(prefix="maboss_run_")
    b = os.path.join(tmp, "model.bnd")
    c = os.path.join(tmp, "model.cfg")
    _sanitise_to_utf8(bnd_path, b)
    _sanitise_to_utf8(cfg_path, c)

    sim = maboss.load(b, c)          # external MaBoSS binary
    result = sim.run()
    df = result.get_nodes_probtraj()  # index=Time, cols=node, val=P(node up)

    times = [float(t) for t in df.index]
    tick = DEFAULT_TIME_TICK
    frames = [int(round(t / tick)) for t in times]
    prob = {str(node): [float(v) for v in df[node].tolist()]
            for node in df.columns}
    return ProbTraj(
        variant=variant, times=times, frames=frames, prob=prob,
        nodes=list(prob.keys()), time_tick=tick, max_time=DEFAULT_MAX_TIME,
        backend="MaBoSS (external binary, colomoto)",
        engine_version=maboss_version())


def run_variant(variant: str) -> ProbTraj:
    """Run the model for a genotype *variant* (``WildType``/``F19A``/...)."""
    bnd, cfg = variant_model_paths(variant)
    pt = run_cfg(bnd, cfg, variant=variant)
    return pt


# Variants that have emitted mutant models (WT is the reference itself).
EMITTED_VARIANTS = ("F19A", "L26A", "W23A")
ALL_VARIANTS = ("WildType", *EMITTED_VARIANTS)


def run_all() -> Dict[str, ProbTraj]:
    """Run WT + every emitted mutant; {variant: ProbTraj}."""
    return {v: run_variant(v) for v in ALL_VARIANTS}


if __name__ == "__main__":
    try:
        ensure_backend()
    except MabossUnavailableError as exc:
        print(f"[run_maboss] SKIP: {exc}")
        raise SystemExit(0)
    print(f"[run_maboss] backend: {maboss_version()}")
    for v in ALL_VARIANTS:
        pt = run_variant(v)
        p53_avg = pt.time_average(P53_NODE)
        print(f"  {v:<8} nodes={pt.nodes}  "
              f"<P({P53_NODE} up)>={p53_avg:.6f}  "
              f"P@t0={pt.at_frame(P53_NODE, 0):.6f}  "
              f"P@last={pt.series(P53_NODE)[-1]:.6f}")
