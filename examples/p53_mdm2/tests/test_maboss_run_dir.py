"""
Read-back gates for the committed MaBoSS run directory of record.

``run_maboss.run_all_kept()`` keeps the MaBoSS binary's own output under
``maboss/output/run_<UTC>/<variant>/`` with a ``provenance.json`` at the run
root (layout: see ``run_maboss`` "Kept runs"). Exactly one such directory is
committed; this module reads it back WITHOUT running MaBoSS.

Rows
----
  maboss_run_dir_provenance_digests
      every file the record lists exists with the recorded byte count and
      SHA-256, no unlisted file sits in the run dir, and the record names the
      binary version, the .cfg seed / sample_count and the UTC time.
  maboss_run_dir_inputs_match_models
      the record's input ``.bnd``/``.cfg`` digests equal the committed model
      files today (the run is evidence for THESE models, not stale ones).
  maboss_run_dir_marginals_vs_analysis:<variant>
      independent oracle: P(node up) recomputed by summing ``Proba`` over the
      states of the committed ``res_probtraj.csv`` that contain the node (plain
      ``csv`` parse; not pyMaBoSS, not the builder) vs. the Analysis layer's
      ``bio:maboss:prob:<node>`` at the same time code, at every report time.
      The row text carries the max abs difference per node.
  maboss_run_dir_not_gitignored
      ``git check-ignore`` reports no file under the run dir, and none ends in
      ``.log`` (``.gitignore`` swallows that extension silently).
  maboss_run_dir_absent_selftest
      with the path constant redirected IN-PROCESS to a non-existent dir,
      :func:`run` returns zero rows (the harness has no skip concept).

When the run directory is absent the module contributes zero rows.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)              # examples/p53_mdm2
_PKG_PARENT = os.path.dirname(_PKG)        # examples/
for _p in (_HERE, _PKG_PARENT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from p53_mdm2.maboss import run_maboss

# The one committed run directory (must match the .gitignore negation).
COMMITTED_RUN = "run_20261106T004327Z"
RUN_DIR = os.path.join(_PKG, "maboss", "output", COMMITTED_RUN)
ANALYSIS_PATH = os.path.join(_PKG, "analysis", "p53_mdm2_analysis.usda")

MODEL_NODES = ("p53", "p53_h", "Mdm2C", "Mdm2N", "Dam")
PROB_ATTR_PREFIX = "bio:maboss:prob:"
MABOSS_SCOPE = "maboss"
# USD stores float32; the CSV carries 6 decimals and the node marginal is a
# sum of up to 2^5 such values -> worst case ~1.6e-5 of rounding + float32.
_MARGINAL_TOL = 5e-5


@dataclass
class Result:
    check_name: str
    passed: bool
    errors: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)


def _load_record(run_dir):
    with open(os.path.join(run_dir, run_maboss.PROVENANCE_NAME),
              encoding="utf-8") as fh:
        return json.load(fh)


def _files_on_disk(run_dir):
    out = []
    for dp, _dn, fns in os.walk(run_dir):
        for fn in fns:
            out.append(os.path.relpath(os.path.join(dp, fn), run_dir))
    return sorted(out)


def assert_provenance_digests(run_dir, rec) -> Result:
    errors = []
    listed = set()
    for v, entry in sorted(rec.get("variants", {}).items()):
        for f in entry.get("files", []):
            listed.add(f["path"])
            p = os.path.join(run_dir, f["path"])
            if not os.path.isfile(p):
                errors.append(f"missing {f['path']}")
                continue
            if os.path.getsize(p) != f["bytes"]:
                errors.append(f"{f['path']}: size != record")
            if run_maboss.sha256_file(p) != f["sha256"]:
                errors.append(f"{f['path']}: sha256 != record")
        cs = entry.get("cfg_settings", {})
        for key in ("seed_pseudorandom", "sample_count"):
            if key not in cs:
                errors.append(f"{v}: record lacks {key}")
    unlisted = [p for p in _files_on_disk(run_dir)
                if p != run_maboss.PROVENANCE_NAME and p not in listed]
    if unlisted:
        errors.append(f"unlisted files: {unlisted[:3]}")
    if set(rec.get("variants", {})) != set(run_maboss.ALL_VARIANTS):
        errors.append(f"variants {sorted(rec.get('variants', {}))} != "
                      f"{list(run_maboss.ALL_VARIANTS)}")
    version = rec.get("maboss_binary", {}).get("version", "")
    if not version or version == "unknown":
        errors.append("binary version not recorded")
    if not rec.get("created_utc", "").endswith("Z"):
        errors.append("created_utc missing / not UTC")
    if not listed:
        errors.append("record lists no files")
    if errors:
        return Result("maboss_run_dir_provenance_digests", False, errors)
    any_cs = next(iter(rec["variants"].values()))["cfg_settings"]
    note = (f"{len(listed)} files sha256 ok; {version.split(' [')[0]}; "
            f"seed={any_cs['seed_pseudorandom']} "
            f"samples={any_cs['sample_count']}")
    return Result("maboss_run_dir_provenance_digests", True, [note])


def assert_inputs_match_models(rec) -> Result:
    errors = []
    for v, entry in sorted(rec.get("variants", {}).items()):
        bnd, cfg = run_maboss.variant_model_paths(v)
        for key, path in (("input_bnd", bnd), ("input_cfg", cfg)):
            if not os.path.isfile(path):
                errors.append(f"{v}: model file missing {path}")
            elif run_maboss.sha256_file(path) != entry.get(key, {}).get("sha256"):
                errors.append(f"{v}: {os.path.basename(path)} changed since run")
    note = [] if errors else ["8 model digests match committed .bnd/.cfg"]
    return Result("maboss_run_dir_inputs_match_models", not errors,
                  errors or note)


def marginals_from_probtraj_csv(path):
    """{time: {node: P(node up)}} by summing state probabilities.

    Columns: ``Time, TH, ErrorTH, H, HD=0.., `` then repeating
    ``State, Proba, ErrorProba`` triplets. A state label is the ``" -- "``-
    joined list of ON nodes; ``<nil>`` is the all-OFF state.
    """
    out = {}
    with open(path, newline="") as fh:
        rd = csv.reader(fh, delimiter="\t")
        header = next(rd)
        first = header.index("State")
        for row in rd:
            if not row:
                continue
            t = float(row[0])
            acc = {n: 0.0 for n in MODEL_NODES}
            for i in range(first, len(row) - 1, 3):
                label, proba = row[i], row[i + 1]
                if not label:
                    continue
                on = [] if label == "<nil>" else label.split(" -- ")
                for n in on:
                    if n not in acc:
                        raise ValueError(f"unknown node {n!r} in state {label!r}")
                    acc[n] += float(proba)
            out[t] = acc
    return out


def assert_marginals_vs_analysis(run_dir, rec, stage) -> list:
    from pxr import Usd
    rows = []
    root = stage.GetDefaultPrim()
    scope_path = f"{root.GetPath()}/{MABOSS_SCOPE}" if root else ""
    for v in run_maboss.ALL_VARIANTS:
        name = f"maboss_run_dir_marginals_vs_analysis:{v}"
        csv_path = os.path.join(run_dir, v,
                                f"{run_maboss.RUN_PREFIX}_probtraj.csv")
        if not os.path.isfile(csv_path):
            rows.append(Result(name, False, [f"missing {csv_path}"]))
            continue
        vprim = stage.GetPrimAtPath(f"{scope_path}/{v}") if scope_path else None
        if not vprim or not vprim.IsValid():
            rows.append(Result(name, False, [f"no analysis prim for {v}"]))
            continue
        tick = float(rec["variants"][v]["cfg_settings"].get(
            "time_tick", run_maboss.DEFAULT_TIME_TICK))
        marg = marginals_from_probtraj_csv(csv_path)
        errors, maxdiff, n_cmp = [], {}, 0
        for node in MODEL_NODES:
            attr = vprim.GetAttribute(PROB_ATTR_PREFIX + node)
            if not attr.IsValid():
                errors.append(f"{node}: prob attr missing")
                continue
            ts = set(attr.GetTimeSamples())
            md = 0.0
            for t, acc in marg.items():
                frame = int(round(t / tick))
                if frame not in ts:
                    errors.append(f"{node}: no USD sample at frame {frame}")
                    break
                d = abs(float(attr.Get(Usd.TimeCode(frame))) - acc[node])
                md = max(md, d)
                n_cmp += 1
            if len(ts) != len(marg):
                errors.append(f"{node}: {len(ts)} USD samples vs "
                              f"{len(marg)} CSV rows")
            maxdiff[node] = md
            if md > _MARGINAL_TOL:
                errors.append(f"{node}: max|diff|={md:.2e} > {_MARGINAL_TOL}")
        text = " ".join(f"{n}={maxdiff[n]:.1e}" for n in MODEL_NODES
                        if n in maxdiff)
        ok = not errors and n_cmp > 0
        rows.append(Result(name, ok, ([f"max|d| {text}"] if ok
                                      else errors + [f"max|d| {text}"]),
                           {"max_abs_diff": maxdiff, "compared": n_cmp}))
    return rows


def assert_not_gitignored(run_dir) -> Result:
    files = [os.path.join(run_dir, p) for p in _files_on_disk(run_dir)]
    errors = [f"{os.path.relpath(p, run_dir)} ends in .log"
              for p in files if p.endswith(".log")]
    try:
        res = subprocess.run(
            ["git", "-C", run_dir, "check-ignore", "--no-index", "--stdin"],
            input="\n".join(files) + "\n", capture_output=True, text=True,
            timeout=60)
    except Exception as exc:
        return Result("maboss_run_dir_not_gitignored", False,
                      [f"git check-ignore failed: {exc}"])
    if res.returncode not in (0, 1):
        return Result("maboss_run_dir_not_gitignored", False,
                      [f"git check-ignore rc={res.returncode}: "
                       f"{res.stderr.strip()[:80]}"])
    ignored = [ln for ln in res.stdout.splitlines() if ln.strip()]
    if ignored:
        errors.append(f"{len(ignored)} ignored, e.g. "
                      f"{os.path.relpath(ignored[0], run_dir)}")
    return Result("maboss_run_dir_not_gitignored", not errors,
                  errors or [f"{len(files)} files, none ignored, no .log"])


def assert_absent_selftest() -> Result:
    """Redirect RUN_DIR in-process to a path that does not exist."""
    global RUN_DIR
    saved = RUN_DIR
    RUN_DIR = os.path.join(_PKG, "maboss", "output",
                           "run_absent_selftest_does_not_exist")
    try:
        rows = run(_selftest=False)
    finally:
        RUN_DIR = saved
    ok = rows == []
    return Result("maboss_run_dir_absent_selftest", ok,
                  ["absent run dir -> 0 rows"] if ok
                  else [f"absent run dir produced {len(rows)} rows"])


def run(*, _selftest: bool = True) -> list:
    run_dir = RUN_DIR
    if not os.path.isfile(os.path.join(run_dir, run_maboss.PROVENANCE_NAME)):
        return []
    rec = _load_record(run_dir)
    rows = [assert_provenance_digests(run_dir, rec),
            assert_inputs_match_models(rec)]
    if os.path.isfile(ANALYSIS_PATH):
        from pxr import Usd
        stage = Usd.Stage.Open(ANALYSIS_PATH)
        rows += assert_marginals_vs_analysis(run_dir, rec, stage)
    else:
        rows.append(Result("maboss_run_dir_marginals_vs_analysis", False,
                           [f"analysis layer not found: {ANALYSIS_PATH}"]))
    rows.append(assert_not_gitignored(run_dir))
    if _selftest:
        rows.append(assert_absent_selftest())
    return rows


if __name__ == "__main__":
    rs = run()
    for r in rs:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.check_name}  "
              f"{'; '.join(r.errors)}")
    raise SystemExit(0 if rs and all(r.passed for r in rs) else 1)
