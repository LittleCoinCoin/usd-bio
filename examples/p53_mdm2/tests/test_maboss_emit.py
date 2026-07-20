"""
Round-trip tests for the USD -> MaBoSS emitter (Pipeline 3, Step 2).

Falsification-resistant / anti-tautology (R02 §Round-trip validation):

  #1 Emit test -- re-parse the emitted ``.cfg`` with an INDEPENDENT reader
     (``_read_cfg_param`` below, not the emitter object) and assert
     ``$KMn_pMCD == S_expected``, where ``S_expected`` is recomputed by a SECOND,
     independent logistic (``_independent_s``) directly from the committed
     ``bio:ddgKcalPerMol`` on the genotype stage -- never from the emitter's
     in-memory S. Also assert each emitted ``.bnd`` is byte-identical to the
     reference (SHA-256) and the companion ``$KMn_pMC`` equals ``$KMn_pMCD``.

  #2 Inverse test -- assert ``m + (1/k)*logit(paramValue)`` recovers the original
     ``bio:ddgKcalPerMol`` within tolerance, reading ``paramValue`` back from the
     emitted ``.cfg`` (full precision) and cross-checking the USD
     ``bio:maboss:paramValue`` write-back. Closes the PI's inverse loop.

  #3 Directional test -- needs a MaBoSS run to compare time-averaged P(p53 up)
     of a destabilizing variant vs. WT. DEFERRED to the Pipeline-4 cycle; a
     documented placeholder is reported here (no MaBoSS installed, by design).

All expected values are re-derived here from the committed genotype stage +
reference files, so a chimeric or self-agreeing emitter cannot pass.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import sys
from dataclasses import dataclass, field

try:
    from pxr import Usd
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pxr not importable. Run under the OpenUSD interpreter with "
        "load_env.sh sourced.") from exc

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from p53_mdm2.maboss import emit_model
from p53_mdm2.maboss.dg_correlation import (
    DEFAULT_MIDPOINT_KCAL_PER_MOL as M,
    DEFAULT_STEEPNESS_PER_KCAL as K,
)

_VALUE_STATUSES = {"success", "fixture"}
_S_TOL = 1e-9      # .cfg stores S at 12 sig-figs; agreement to ~1e-12 expected
_DDG_TOL = 1e-4    # inverse recovery tolerance


@dataclass
class Result:
    check_name: str
    passed: bool
    errors: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)


def _independent_s(ddg, m=M, k=K):
    """Second, independent logistic -- NOT the emitter / dg_correlation module."""
    return 1.0 / (1.0 + math.exp(-k * (ddg - m)))


def _independent_ddg_from_s(s, m=M, k=K):
    """Second, independent logit inverse."""
    return m + (1.0 / k) * math.log(s / (1.0 - s))


def _read_cfg_param(cfg_path, name):
    """Independent single-parameter reader: return float value of $<name>."""
    pat = re.compile(r"^\s*\$" + re.escape(name) + r"\s*=\s*([^;]+);", re.M)
    with open(cfg_path, "r") as fh:
        text = fh.read()
    matches = pat.findall(text)
    if len(matches) != 1:
        raise ValueError(f"expected 1 '${name}' in {cfg_path}, found {len(matches)}")
    return float(matches[0].strip())


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _committed_ddg_by_variant(genotype_path):
    """{variant: (mutation, status, ddg_or_None)} read fresh from the stage."""
    stage = Usd.Stage.Open(genotype_path)
    root = stage.GetDefaultPrim()
    gv = root.GetVariantSets().GetVariantSet("Genotype")
    out = {}
    for v in gv.GetVariantNames():
        gv.SetVariantSelection(v)
        mut = root.GetAttribute("bio:mutation")
        mut = mut.Get() if mut.IsValid() else None
        st = root.GetAttribute("bio:ddgStatus")
        st = str(st.Get()) if st.IsValid() and st.Get() is not None else None
        dd = root.GetAttribute("bio:ddgKcalPerMol")
        dd = float(dd.Get()) if dd.IsValid() and dd.Get() is not None else None
        out[v] = (mut, st, dd)
    return out


def _usd_maboss_paramvalue(genotype_path, variant):
    stage = Usd.Stage.Open(genotype_path)
    root = stage.GetDefaultPrim()
    gv = root.GetVariantSets().GetVariantSet("Genotype")
    gv.SetVariantSelection(variant)
    a = root.GetAttribute("bio:maboss:paramValue")
    return float(a.Get()) if a.IsValid() and a.Get() is not None else None


def assert_emit_roundtrip(genotype_path, out_dir, ref_bnd) -> Result:
    """#1 emit test + #2 inverse test, over every value-bearing variant."""
    errors, detail = [], {}
    ref_sha = _sha256(ref_bnd)
    committed = _committed_ddg_by_variant(genotype_path)

    checked = 0
    for variant, (mutation, status, ddg) in committed.items():
        if not mutation or mutation == "none":
            continue
        if status not in _VALUE_STATUSES or ddg is None:
            continue  # error-model: emitter must have skipped it too
        cfg_path = os.path.join(out_dir, f"p53_Mdm2_{variant}.cfg")
        bnd_path = os.path.join(out_dir, f"p53_Mdm2_{variant}.bnd")
        if not (os.path.isfile(cfg_path) and os.path.isfile(bnd_path)):
            errors.append(f"{variant}: emitted .cfg/.bnd missing")
            continue
        checked += 1

        # --- #1a: .bnd byte-identical to reference (SHA-256) ---
        if _sha256(bnd_path) != ref_sha:
            errors.append(f"{variant}: emitted .bnd not byte-identical to reference")

        # --- #1b: $KMn_pMCD == S recomputed independently from committed ΔΔG ---
        s_cfg = _read_cfg_param(cfg_path, "KMn_pMCD")
        s_companion = _read_cfg_param(cfg_path, "KMn_pMC")
        s_expected = _independent_s(ddg)
        if abs(s_cfg - s_expected) > _S_TOL:
            errors.append(
                f"{variant}: $KMn_pMCD={s_cfg!r} != independent S({ddg})="
                f"{s_expected!r}")
        if abs(s_companion - s_cfg) > _S_TOL:
            errors.append(
                f"{variant}: companion $KMn_pMC={s_companion!r} != "
                f"$KMn_pMCD={s_cfg!r}")

        # --- #1c: emitter must not have touched anything but the two params ---
        # (independent structural guard: exactly two lines differ from reference)
        with open(emit_model.reference_cfg_path()) as fh:
            ref_lines = fh.read().splitlines()
        with open(cfg_path) as fh:
            emit_lines = fh.read().splitlines()
        if len(ref_lines) != len(emit_lines):
            errors.append(f"{variant}: .cfg line count changed vs reference")
        else:
            diffs = [i for i, (a, b) in enumerate(zip(ref_lines, emit_lines)) if a != b]
            if len(diffs) != 2:
                errors.append(
                    f"{variant}: {len(diffs)} lines differ from reference "
                    f"(expected exactly 2: the two $KMn params)")

        # --- #2: inverse recovers the original ΔΔG (from .cfg paramValue) ---
        ddg_rec = _independent_ddg_from_s(s_cfg)
        if abs(ddg_rec - ddg) > _DDG_TOL:
            errors.append(
                f"{variant}: inverse ΔΔG={ddg_rec!r} != committed {ddg!r}")

        # cross-check the USD write-back paramValue recovers ΔΔG too (float32)
        usd_pv = _usd_maboss_paramvalue(genotype_path, variant)
        if usd_pv is None:
            errors.append(f"{variant}: bio:maboss:paramValue not written to USD")
        else:
            ddg_rec_usd = _independent_ddg_from_s(usd_pv)
            if abs(ddg_rec_usd - ddg) > 1e-3:  # looser: USD stores float32
                errors.append(
                    f"{variant}: USD-paramValue inverse ΔΔG={ddg_rec_usd!r} != "
                    f"committed {ddg!r}")
        detail[variant] = {"ddg": ddg, "S_cfg": s_cfg, "ddg_recovered": ddg_rec}

    if checked == 0:
        errors.append("no value-bearing variants emitted to check")
    return Result("emit_inverse_roundtrip", not errors, errors, detail)


def assert_directional_deferred() -> Result:
    """#3 directional test -- requires a MaBoSS run; deferred to Pipeline-4."""
    return Result(
        "directional_test_deferred_to_pipeline4", True, [],
        {"note": "Needs MaBoSS to compare time-averaged P(p53 up) of a "
                 "destabilizing variant vs WT; no MaBoSS installed this cycle "
                 "(R02 §Round-trip #3). Placeholder, not a substantive pass."})


def run() -> list:
    genotype_path = emit_model.default_genotype_path()
    out_dir = emit_model.output_dir()
    ref_bnd = emit_model.reference_bnd_path()
    if not os.path.isfile(genotype_path):
        return [Result("genotype_stage_exists", False,
                       [f"not found: {genotype_path}"])]
    if not os.path.isfile(ref_bnd):
        return [Result("reference_bnd_exists", False,
                       [f"not found: {ref_bnd}"])]
    return [
        assert_emit_roundtrip(genotype_path, out_dir, ref_bnd),
        assert_directional_deferred(),
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
