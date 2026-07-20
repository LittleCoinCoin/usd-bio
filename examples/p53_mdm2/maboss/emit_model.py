"""
emit_model.py -- Pipeline 3 Step 2: emit MaBoSS ``.bnd``/``.cfg`` from the USD
genotype stage via the ΔΔG<->parameter correlation.

For each genotype variant that carries a value-bearing ΔΔG, this:

  1. reads ``bio:ddgKcalPerMol`` (+ ``bio:ddgStatus`` / ``bio:ddgSource``) off the
     composed stage;
  2. computes ``S = s_from_ddg(ΔΔG; m, k)`` (dg_correlation);
  3. emits ``p53_Mdm2_<variant>.cfg`` -- the reference ``.cfg`` text with ONLY
     ``$KMn_pMCD`` and ``$KMn_pMC`` reset to ``S`` (optionally a continuous
     ``Mdm2N.istate = [1-S, S]``); everything else byte-for-byte unchanged;
  4. emits ``p53_Mdm2_<variant>.bnd`` -- a VERBATIM copy of the reference
     topology (byte-identical);
  5. writes the ``bio:maboss:*`` correlation contract (R02 §Contracts) back onto
     the variant prim, PROPAGATING the ΔΔG status/source so the S value's
     fixture-vs-real lineage is inspectable from USD alone.

Error model (R02): a variant whose ``bio:ddgStatus`` is not value-bearing
(``unknown``/``unavailable``/absent) is SKIPPED -- never emit a fabricated S.

The ``.cfg`` templating (:func:`emit_cfg_text`) is pure text (no ``pxr``) so it is
independently testable; only the stage read/write path needs OpenUSD.

Design source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md
Reference model: examples/p53_mdm2/maboss/reference/p53_Mdm2{.bnd,_runcfg.cfg}
  (fetched verbatim from https://maboss.curie.fr/files/p53Dam/).

NOTE ON ATTRIBUTE NAMES: the committed genotype stage carries the ΔΔG as
``bio:ddgKcalPerMol`` / ``bio:ddgStatus`` / ``bio:ddgSource`` (Pipeline 2's actual
write-back), NOT the ``bio:mutation:ddgKcalPerMol`` / ``bio:ddg:status`` spelling
sketched in the R02 contract table. Reality is followed here; the discrepancy is
flagged in the cycle return.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from dataclasses import dataclass
from typing import List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from p53_mdm2.maboss.dg_correlation import (
    s_from_ddg,
    CORRELATION_FORM,
    DEFAULT_MIDPOINT_KCAL_PER_MOL,
    DEFAULT_STEEPNESS_PER_KCAL,
)

# The two hill parameters the correlation drives (R02: primary + companion,
# both WT=1). $KMn_p / $KMn_pD stay at WT 0; non-p53 contexts untouched.
CORRELATED_PARAMS = ("KMn_pMCD", "KMn_pMC")
TARGET_NODE = "Mdm2N"

# ΔΔG statuses that carry a real numeric to correlate from (mirrors the
# Pipeline-2 read-back test's _VALUE_STATUSES).
_VALUE_STATUSES = {"success", "fixture"}

# Value format: 12 significant figures -- enough precision that the logit
# inverse recovers ΔΔG well within test tolerance.
_VALUE_FMT = ".12g"


@dataclass
class EmitResult:
    variant: str
    mutation: str
    ddg: float
    s: float
    status: str
    source: str
    cfg_path: str
    bnd_path: str


def _fmt(value: float) -> str:
    return format(value, _VALUE_FMT)


def _replace_param(cfg_text: str, name: str, value: float) -> str:
    """Reset exactly one ``$<name> = <...>;`` assignment, preserving surrounding
    whitespace/formatting; raise unless it matches exactly once."""
    pat = re.compile(r"(\$" + re.escape(name) + r"\s*=\s*)([^;]*)(;)")
    new_text, n = pat.subn(lambda mm: mm.group(1) + _fmt(value) + mm.group(3),
                           cfg_text)
    if n != 1:
        raise ValueError(
            f"expected exactly one '${name}' assignment in .cfg, found {n}")
    return new_text


def _replace_istate(cfg_text: str, node: str, s: float) -> str:
    """Set ``<node>.istate = <1-s> [0] , <s> [1];`` (continuous initial cond.)."""
    pat = re.compile(r"(" + re.escape(node) + r"\.istate\s*=\s*)([^;]*)(;)")
    repl = f"{_fmt(1.0 - s)} [0] , {_fmt(s)} [1]"
    new_text, n = pat.subn(lambda mm: mm.group(1) + repl + mm.group(3), cfg_text)
    if n != 1:
        raise ValueError(
            f"expected exactly one '{node}.istate' assignment, found {n}")
    return new_text


def emit_cfg_text(reference_cfg_text: str, s: float,
                  *, set_istate: bool = False) -> str:
    """Return the reference ``.cfg`` with only the correlated params (and,
    optionally, ``Mdm2N.istate``) reset to *s*. Pure text; no ``pxr``.
    """
    out = reference_cfg_text
    for name in CORRELATED_PARAMS:
        out = _replace_param(out, name, s)
    if set_istate:
        out = _replace_istate(out, TARGET_NODE, s)
    return out


def reference_dir() -> str:
    return os.path.join(_HERE, "reference")


def output_dir() -> str:
    return os.path.join(_HERE, "output")


def reference_bnd_path() -> str:
    return os.path.join(reference_dir(), "p53_Mdm2.bnd")


def reference_cfg_path() -> str:
    return os.path.join(reference_dir(), "p53_Mdm2_runcfg.cfg")


def default_genotype_path() -> str:
    """The committed ΔΔG-bearing genotype stage this emitter consumes."""
    from p53_mdm2.composition.build_genotype import default_output_path
    return default_output_path()


def _write_maboss_attrs(root_prim, s: float, m: float, k: float,
                        ddg_status: str, ddg_source: str) -> None:
    """Author the R02 ``bio:maboss:*`` contract on *root_prim* (inside the active
    variant edit context). Propagates the ΔΔG status/source so the S value's
    lineage is inspectable from USD alone."""
    from pxr import Sdf
    root_prim.CreateAttribute("bio:maboss:targetNode",
                              Sdf.ValueTypeNames.Token).Set(TARGET_NODE)
    root_prim.CreateAttribute("bio:maboss:paramNames",
                              Sdf.ValueTypeNames.TokenArray).Set(list(CORRELATED_PARAMS))
    root_prim.CreateAttribute("bio:maboss:paramValue",
                              Sdf.ValueTypeNames.Float).Set(float(s))
    root_prim.CreateAttribute("bio:maboss:correlationForm",
                              Sdf.ValueTypeNames.Token).Set(CORRELATION_FORM)
    root_prim.CreateAttribute("bio:maboss:correlationMidpointKcalPerMol",
                              Sdf.ValueTypeNames.Float).Set(float(m))
    root_prim.CreateAttribute("bio:maboss:correlationSteepnessPerKcal",
                              Sdf.ValueTypeNames.Float).Set(float(k))
    # Provenance propagation: S is only as real as the ΔΔG it came from.
    root_prim.CreateAttribute("bio:maboss:paramValueStatus",
                              Sdf.ValueTypeNames.Token).Set(str(ddg_status))
    root_prim.CreateAttribute("bio:maboss:paramValueSource",
                              Sdf.ValueTypeNames.Token).Set(str(ddg_source))


def emit_from_stage(
    genotype_path: Optional[str] = None,
    out_dir: Optional[str] = None,
    *,
    m: float = DEFAULT_MIDPOINT_KCAL_PER_MOL,
    k: float = DEFAULT_STEEPNESS_PER_KCAL,
    set_istate: bool = False,
    write_back_usd: bool = True,
) -> List[EmitResult]:
    """Emit ``.bnd``/``.cfg`` for every value-bearing variant on the genotype
    stage and (optionally) write the ``bio:maboss:*`` contract back into USD.

    Returns the list of :class:`EmitResult` for the variants actually emitted
    (skipped variants -- WT with no ΔΔG, or non-value ΔΔG status -- are omitted).
    """
    from pxr import Usd

    genotype_path = genotype_path or default_genotype_path()
    out_dir = out_dir or output_dir()
    os.makedirs(out_dir, exist_ok=True)

    with open(reference_cfg_path(), "r") as fh:
        reference_cfg = fh.read()

    stage = Usd.Stage.Open(genotype_path)
    root = stage.GetDefaultPrim()
    genotype = root.GetVariantSets().GetVariantSet("Genotype")
    if not genotype.IsValid():
        raise ValueError(f"no Genotype VariantSet on {root.GetPath()}")

    original_selection = genotype.GetVariantSelection()
    emitted: List[EmitResult] = []

    for variant in genotype.GetVariantNames():
        genotype.SetVariantSelection(variant)
        mutation_attr = root.GetAttribute("bio:mutation")
        mutation = mutation_attr.Get() if mutation_attr.IsValid() else None
        # WT baseline has no ΔΔG -> the reference .cfg already IS its model.
        if not mutation or mutation == "none":
            continue

        status_attr = root.GetAttribute("bio:ddgStatus")
        ddg_attr = root.GetAttribute("bio:ddgKcalPerMol")
        source_attr = root.GetAttribute("bio:ddgSource")
        status = str(status_attr.Get()) if status_attr.IsValid() and status_attr.Get() is not None else None
        source = str(source_attr.Get()) if source_attr.IsValid() and source_attr.Get() is not None else "unknown"
        has_numeric = ddg_attr.IsValid() and ddg_attr.Get() is not None

        # Error model: skip anything without a value-bearing ΔΔG.
        if status not in _VALUE_STATUSES or not has_numeric:
            continue

        ddg = float(ddg_attr.Get())
        s = s_from_ddg(ddg, m=m, k=k)

        cfg_text = emit_cfg_text(reference_cfg, s, set_istate=set_istate)
        cfg_path = os.path.join(out_dir, f"p53_Mdm2_{variant}.cfg")
        bnd_path = os.path.join(out_dir, f"p53_Mdm2_{variant}.bnd")
        with open(cfg_path, "w") as fh:
            fh.write(cfg_text)
        # .bnd is topology-invariant: byte-identical verbatim copy.
        shutil.copyfile(reference_bnd_path(), bnd_path)

        if write_back_usd:
            with genotype.GetVariantEditContext():
                _write_maboss_attrs(root, s, m, k, status, source)

        emitted.append(EmitResult(
            variant=variant, mutation=str(mutation), ddg=ddg, s=s,
            status=status, source=source,
            cfg_path=cfg_path, bnd_path=bnd_path))

    genotype.SetVariantSelection(original_selection)
    if write_back_usd:
        stage.GetRootLayer().Save()

    return emitted


if __name__ == "__main__":
    results = emit_from_stage()
    print(f"[emit_model] emitted {len(results)} MaBoSS model(s) into {output_dir()}")
    for r in results:
        print(f"  {r.variant:<8} ΔΔG={r.ddg:+.3f}  S={r.s:.6f}  "
              f"[{r.status}/{r.source}]  -> {os.path.basename(r.cfg_path)}, "
              f"{os.path.basename(r.bnd_path)}")
