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
read-back test.

Kept runs
---------
By default the binary's own files are discarded with pyMaBoSS's temp dir.
:func:`run_all_kept` (CLI: ``--keep-run``) instead keeps them in
``maboss/output/run_<UTC>/<variant>/`` with a ``provenance.json`` at the run
root, following the ``data/ddmut_ppi_live/run_<UTC>/`` precedent. One such
directory is committed as the evidence of record; ``tests/test_maboss_run_dir``
reads it back. The default path (:func:`run_all`) is unchanged.

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

# ---------------------------------------------------------------------------
# ASSUMED physical unit of MaBoSS model time  [assumption]
# ---------------------------------------------------------------------------
# MaBoSS time is dimensionless: every ``rate_up``/``rate_down`` in the .bnd is
# ``1/$t...`` with the ``$t...`` constants of the reference .cfg (0.3 to 5), so
# ``max_time``/``time_tick`` are in "model time units" and mean nothing physical
# until someone says what one unit is. PI Q-019 (2026-11-04): "at least assume
# one and stick to it". This is that assumption, in ONE place:
#
#     1 MaBoSS model time unit == 1 hour
#
# Why hours [assumption, not verified against the model's source paper]:
#   * the p53-Mdm2 negative-feedback loop this 5-node model abstracts is
#     observed to pulse on an hours scale in single cells (Lahav et al. 2004,
#     Nat Genet 36:147 -- period of a few hours; cited from memory);
#   * under that reading the model's time constants (0.3-5) are 20 min to 5 h,
#     and the wild-type P(p53 up) first peaks near model time 5.7 in the
#     committed Analysis layer -- an hours-scale response, not seconds or days;
#   * nothing in the repo (.bnd/.cfg comments, R02) assigns a unit, so this is
#     a declared choice, recorded on the Analysis layer as
#     ``bio:maboss:timeUnit`` / ``bio:maboss:secondsPerTimeUnit`` with a
#     ``bio:maboss:timeUnitStatus`` that says it is an assumption.
# It does NOT relate the MaBoSS clock to the MD clock: the integrated stage
# keeps the two time axes separate (see demos/run_end_to_end.py).
ASSUMED_TIME_UNIT = "hour"
ASSUMED_SECONDS_PER_TIME_UNIT = 3600.0
ASSUMED_TIME_UNIT_STATUS = (
    "assumption (PI Q-019, 2026-11-04: 'assume one and stick to it'): one "
    "MaBoSS model time unit is taken as one hour, from the hours-scale "
    "p53-Mdm2 feedback; the model itself is dimensionless and assigns no unit")

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
def run_cfg(bnd_path: str, cfg_path: str, *, variant: str = "?",
            keep_dir: Optional[str] = None) -> ProbTraj:
    """Run one MaBoSS model and return its node-probability :class:`ProbTraj`.

    Uses the external-binary path (``maboss.load(...).run()`` without
    ``cmaboss``). Converts the pandas DataFrame to plain Python so no pandas
    dependency leaks to callers/tests.

    *keep_dir* ``None`` (the default, used by every builder and test) keeps the
    historical behaviour: pyMaBoSS runs in its own temp directory and deletes
    it, so only the node marginals survive. Given a path, the binary is pointed
    at that directory instead (``sim.run(workdir=keep_dir, prefix="res")``) and
    everything it writes -- ``res_probtraj.csv``, ``res_fp.csv``,
    ``res_statdist.csv``, ... -- is left on disk, in the flat one-directory
    layout ``maboss.StoredResult(keep_dir)`` reads back. The directory must not
    already hold files: pyMaBoSS silently SKIPS the run when its workdir is
    non-empty, which would return stale output as if fresh.
    """
    ensure_backend()
    import maboss

    for p in (bnd_path, cfg_path):
        if not os.path.isfile(p):
            raise FileNotFoundError(f"MaBoSS model file missing: {p}")
    if keep_dir is not None and os.path.isdir(keep_dir) and os.listdir(keep_dir):
        raise FileExistsError(
            f"refusing to run into non-empty {keep_dir}: pyMaBoSS would skip "
            "the run and hand back whatever is already there")

    tmp = tempfile.mkdtemp(prefix="maboss_run_")
    b = os.path.join(tmp, "model.bnd")
    c = os.path.join(tmp, "model.cfg")
    _sanitise_to_utf8(bnd_path, b)
    _sanitise_to_utf8(cfg_path, c)

    sim = maboss.load(b, c)          # external MaBoSS binary
    if keep_dir is None:
        result = sim.run()
    else:
        os.makedirs(keep_dir, exist_ok=True)
        result = sim.run(workdir=keep_dir, prefix=RUN_PREFIX)
        if getattr(result, "_err", 0):
            raise RuntimeError(
                f"MaBoSS returned non-zero ({result._err}) in {keep_dir}")
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


def run_variant(variant: str, *, keep_dir: Optional[str] = None) -> ProbTraj:
    """Run the model for a genotype *variant* (``WildType``/``F19A``/...).

    *keep_dir* is forwarded to :func:`run_cfg` (``None`` = discard output)."""
    bnd, cfg = variant_model_paths(variant)
    pt = run_cfg(bnd, cfg, variant=variant, keep_dir=keep_dir)
    return pt


# Variants that have emitted mutant models (WT is the reference itself).
EMITTED_VARIANTS = ("F19A", "L26A", "W23A")
ALL_VARIANTS = ("WildType", *EMITTED_VARIANTS)


def run_all() -> Dict[str, ProbTraj]:
    """Run WT + every emitted mutant; {variant: ProbTraj}. Output discarded."""
    return {v: run_variant(v) for v in ALL_VARIANTS}


# ---------------------------------------------------------------------------
# Kept runs: the binary's own output as a committed run directory
# ---------------------------------------------------------------------------
# Layout, mirroring data/ddmut_ppi_live/run_<UTC>/ (one immutable directory per
# run, a provenance record at its root, every byte below it machine-written):
#
#   maboss/output/run_<UTC>/
#       provenance.json            -- written by this module (see below)
#       <variant>/                 -- one flat pyMaBoSS workdir per variant
#           res_probtraj.csv ...   -- written by the MaBoSS binary, verbatim
#           pymaboss_input.bnd/.cfg-- the model text pyMaBoSS handed the binary
#
# The flat per-variant directory is exactly what ``maboss.StoredResult(dir)``
# reads. Only one run directory is committed (the evidence of record); later
# ``run_*`` directories are gitignored so repeated runs do not accrete.
RUN_PREFIX = "res"                      # pyMaBoSS default output prefix
PROVENANCE_NAME = "provenance.json"
PROVENANCE_SCHEMA = "usd-bio/maboss-run-provenance/v1"
# pyMaBoSS writes the re-serialised model under random ``tmpXXXX.bnd/.cfg``
# names; they are renamed (bytes untouched) so two runs list the same files.
PYMABOSS_INPUT_STEM = "pymaboss_input"
# .cfg keys copied into the provenance record (parsed from the SOURCE .cfg).
_CFG_KEYS = ("seed_pseudorandom", "sample_count", "thread_count", "max_time",
             "time_tick", "discrete_time", "use_physrandgen",
             "statdist_traj_count")


def run_output_root() -> str:
    """``examples/p53_mdm2/maboss/output`` -- parent of every ``run_<UTC>/``."""
    return emit_model.output_dir()


def new_run_dir(root: Optional[str] = None) -> str:
    """A FRESH per-run directory ``<root>/run_<UTC timestamp>`` (not created)."""
    from datetime import datetime, timezone
    root = root or run_output_root()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return os.path.join(root, f"run_{stamp}")


def sha256_file(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_cfg_settings(cfg_path: str) -> Dict[str, str]:
    """``key = value;`` simulation settings from a MaBoSS ``.cfg`` (comments
    and ``$param`` lines skipped). Values kept as the literal text."""
    out: Dict[str, str] = {}
    with open(cfg_path, "rb") as fh:
        text = fh.read().decode("latin-1")
    for line in text.splitlines():
        line = line.split("//", 1)[0].strip()
        if not line or line.startswith("$") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key in _CFG_KEYS:
            out[key] = val.strip().rstrip(";").strip()
    return out


def _rel(path: str) -> str:
    """Path relative to ``examples/p53_mdm2`` when inside it, else absolute."""
    pkg = os.path.dirname(_HERE)
    ap = os.path.abspath(path)
    return os.path.relpath(ap, pkg) if ap.startswith(pkg + os.sep) else ap


def _rename_pymaboss_inputs(variant_dir: str) -> Dict[str, str]:
    """Rename pyMaBoSS's ``tmpXXXX.bnd/.cfg`` to a stable name; {new: old}."""
    renamed = {}
    for name in sorted(os.listdir(variant_dir)):
        stem, ext = os.path.splitext(name)
        if stem.startswith("tmp") and ext in (".bnd", ".cfg"):
            new = PYMABOSS_INPUT_STEM + ext
            os.rename(os.path.join(variant_dir, name),
                      os.path.join(variant_dir, new))
            renamed[new] = name
    return renamed


def run_all_kept(run_dir: Optional[str] = None) -> tuple:
    """Run every variant into ``run_dir/<variant>/`` and write the provenance
    record; returns ``(run_dir, {variant: ProbTraj})``.

    Separate from :func:`run_all` so the default demo path cannot change: the
    builders keep calling :func:`run_all`, which discards output as before.
    """
    import json
    import platform
    from datetime import datetime, timezone

    binary = ensure_backend()
    run_dir = run_dir or new_run_dir()
    if os.path.exists(run_dir) and os.listdir(run_dir):
        raise FileExistsError(f"run directory already populated: {run_dir}")
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    probtrajs: Dict[str, ProbTraj] = {}
    variants = {}
    for v in ALL_VARIANTS:
        vdir = os.path.join(run_dir, v)
        probtrajs[v] = run_variant(v, keep_dir=vdir)
        renamed = _rename_pymaboss_inputs(vdir)
        bnd, cfg = variant_model_paths(v)
        files = []
        for name in sorted(os.listdir(vdir)):
            p = os.path.join(vdir, name)
            files.append({
                "path": f"{v}/{name}",
                "bytes": os.path.getsize(p),
                "sha256": sha256_file(p),
                "written_by": ("pyMaBoSS (model text handed to the binary; "
                               f"renamed from {renamed[name]})"
                               if name in renamed else "MaBoSS binary"),
            })
        variants[v] = {
            "input_bnd": {"path": _rel(bnd), "sha256": sha256_file(bnd)},
            "input_cfg": {"path": _rel(cfg), "sha256": sha256_file(cfg)},
            "cfg_settings": parse_cfg_settings(cfg),
            "output_prefix": RUN_PREFIX,
            "files": files,
        }

    try:
        import importlib.metadata as _md
        pymaboss_version = _md.version("maboss")
    except Exception:
        pymaboss_version = "unknown"
    record = {
        "schema": PROVENANCE_SCHEMA,
        "created_utc": started,
        "finished_utc": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "generator": "examples/p53_mdm2/maboss/run_maboss.py run_all_kept()",
        "maboss_binary": {"path": binary, "version": maboss_version()},
        "pymaboss_version": pymaboss_version,
        "backend": "MaBoSS (external binary, colomoto)",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "note": ("Every file listed is machine-written and kept byte-for-byte; "
                 "only the pyMaBoSS model copies were renamed. res_run.txt "
                 "embeds the binary's wall-clock start/end time, so it is the "
                 "one output expected to differ on a deterministic re-run."),
        "variants": variants,
    }
    with open(os.path.join(run_dir, PROVENANCE_NAME), "w",
              encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return run_dir, probtrajs


def _main(argv: Optional[List[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--keep-run", nargs="?", const="", default=None,
                    metavar="DIR",
                    help="keep MaBoSS's own output in a fresh run directory "
                         "(default maboss/output/run_<UTC>/) with a "
                         "provenance.json; without this flag output is "
                         "discarded as before")
    args = ap.parse_args(argv)
    try:
        ensure_backend()
    except MabossUnavailableError as exc:
        print(f"[run_maboss] SKIP: {exc}")
        return 0
    print(f"[run_maboss] backend: {maboss_version()}")
    if args.keep_run is not None:
        run_dir, probtrajs = run_all_kept(args.keep_run or None)
        print(f"[run_maboss] kept run directory: {run_dir}")
    else:
        probtrajs = {v: run_variant(v) for v in ALL_VARIANTS}
    for v in ALL_VARIANTS:
        pt = probtrajs[v]
        p53_avg = pt.time_average(P53_NODE)
        print(f"  {v:<8} nodes={pt.nodes}  "
              f"<P({P53_NODE} up)>={p53_avg:.6f}  "
              f"P@t0={pt.at_frame(P53_NODE, 0):.6f}  "
              f"P@last={pt.series(P53_NODE)[-1]:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
