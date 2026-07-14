"""
Pipeline 2 ddG write-back read-back test (falsification-resistant).

Opens the committed Genotype assembly FRESH and asserts the recorded ddG /
provenance against INDEPENDENT sources, never against the write-back's in-memory
state (R00 anti-tautology):

  1. The committed fixture JSON, read directly here -- the "committed fixture"
     arm the leaf allows ("recorded ddG vs an independent re-query OR a
     committed fixture").
  2. An INDEPENDENT flat-column re-parse of 1ycr.pdb: the wild-type residue at
     each mutated chain-B position is re-derived here (not via the production
     parser) and cross-checked against each mutation code's WT letter+position.
     A chimera that mislabelled a site therefore cannot pass.
  3. A honesty guard on the fixture file itself: it must be self-labelled as
     synthetic / not-server-output, so fixture values can never masquerade as
     real DDMut-PPI predictions.

Error-model assertion: any variant whose status is NOT a value-bearing status
('success'/'fixture') must carry NO numeric bio:ddgKcalPerMol -- a failed query
surfaces as an explicit status tag, never a fabricated ddG.
"""

from __future__ import annotations

import json
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
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
for _p in (_HERE, _PKG_PARENT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from p53_mdm2 import p53_env
from p53_mdm2.data import RESIDUES
from p53_mdm2.composition.build_genotype import default_output_path

_VALUE_STATUSES = {"success", "fixture"}
_PROVENANCE_FIELDS = (
    "bio:sourcePdb", "bio:forceField", "bio:softwareName",
    "bio:softwareVersion", "bio:simSettings", "bio:timestamp")
_THREE_TO_ONE = {k: v["one_letter"] for k, v in RESIDUES.items()}


@dataclass
class ReadbackResult:
    check_name: str
    passed: bool
    errors: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)


def _fixture_path() -> str:
    return os.path.join(
        _PKG_PARENT, "p53_mdm2", "composition", "fixtures",
        "ddmut_ppi_fixture.json")


def _independent_chainB_resnames(pdb_path: str) -> dict:
    """{res_seq: 3-letter residue name} for chain B, via a flat column parse
    INDEPENDENT of the production pdb_parser."""
    out = {}
    with open(pdb_path, "r") as fh:
        for line in fh:
            if line[0:6].strip() not in ("ATOM", "HETATM"):
                continue
            padded = line.ljust(80)
            if padded[21].strip() != "B":
                continue
            try:
                seq = int(padded[22:26].strip())
            except ValueError:
                continue
            out.setdefault(seq, padded[17:20].strip())
    return out


def assert_fixture_is_honestly_tagged(fixture_path) -> ReadbackResult:
    """The fixture must self-declare as synthetic / not server output."""
    errors, detail = [], {}
    with open(fixture_path, "r") as fh:
        raw = fh.read()
    doc = json.loads(raw)
    blob = (raw + json.dumps(doc)).lower()
    if "synthetic" not in blob:
        errors.append("fixture does not self-label as 'synthetic'")
    if "not" not in blob or "server output" not in blob:
        errors.append("fixture does not disclaim being server output")
    detail["source_field"] = doc.get("source")
    return ReadbackResult("fixture_honestly_tagged", not errors, errors, detail)


def assert_ddg_written_back(stage_path, pdb_path, fixture_path) -> ReadbackResult:
    """Recorded ddG + provenance vs. committed fixture + independent PDB."""
    errors, detail = [], {}

    with open(fixture_path, "r") as fh:
        fixture_doc = json.load(fh)
    fixture_pred = {m: float(v["prediction"])
                    for m, v in fixture_doc.get("predictions", {}).items()}
    indep_resnames = _independent_chainB_resnames(pdb_path)

    stage = Usd.Stage.Open(stage_path)
    root = stage.GetDefaultPrim()
    genotype = root.GetVariantSets().GetVariantSet("Genotype")
    if not genotype.IsValid():
        return ReadbackResult("ddg_written_back", False,
                              ["no Genotype VariantSet on root"])

    per_variant = {}
    checked_mutants = 0
    for variant in genotype.GetVariantNames():
        genotype.SetVariantSelection(variant)
        mutation = root.GetAttribute("bio:mutation").Get()
        status_attr = root.GetAttribute("bio:ddgStatus")
        ddg_attr = root.GetAttribute("bio:ddgKcalPerMol")
        status = status_attr.Get() if status_attr.IsValid() else None
        has_numeric = ddg_attr.IsValid() and ddg_attr.Get() is not None

        # --- WildType baseline: no mutation, no ddG numeric ---
        if not mutation or mutation == "none":
            if has_numeric:
                errors.append(f"{variant}: wild-type carries a ddG numeric")
            continue

        checked_mutants += 1
        per_variant[variant] = {"mutation": mutation, "status": str(status),
                                "numeric": ddg_attr.Get() if has_numeric else None}

        # bio:mutation must equal the variant name (round-trip identity)
        if mutation != variant:
            errors.append(f"{variant}: bio:mutation={mutation} != variant name")

        # --- independent PDB cross-check of WT letter + position ---
        wt_letter, pos_str, mut_letter = mutation[0], mutation[1:-1], mutation[-1]
        try:
            pos = int(pos_str)
        except ValueError:
            errors.append(f"{variant}: malformed mutation code {mutation!r}")
            pos = None
        if pos is not None:
            indep_three = indep_resnames.get(pos)
            indep_one = _THREE_TO_ONE.get(indep_three) if indep_three else None
            if indep_one is None:
                errors.append(f"{variant}: residue {pos} not found on chain B "
                              f"in independent PDB parse")
            elif indep_one != wt_letter:
                errors.append(
                    f"{variant}: mutation WT letter {wt_letter} != independent "
                    f"PDB residue {indep_three}({indep_one}) at position {pos}")

        # --- status / value / provenance ---
        if str(status) in _VALUE_STATUSES:
            if not has_numeric:
                errors.append(f"{variant}: status={status} but no ddG numeric")
            else:
                recorded = float(ddg_attr.Get())
                if str(status) == "fixture":
                    exp = fixture_pred.get(mutation)
                    if exp is None:
                        errors.append(f"{variant}: no fixture entry for {mutation}")
                    elif abs(recorded - exp) > 1e-4:
                        errors.append(
                            f"{variant}: recorded ddG {recorded} != fixture {exp}")
            # provenance completeness
            for pf in _PROVENANCE_FIELDS:
                a = root.GetAttribute(pf)
                if not (a.IsValid() and a.Get() and str(a.Get()).strip()):
                    errors.append(f"{variant}: missing/empty provenance {pf}")
            swn = root.GetAttribute("bio:softwareName")
            if swn.IsValid() and str(swn.Get()) != "DDMut-PPI":
                errors.append(f"{variant}: softwareName={swn.Get()} != DDMut-PPI")
        else:
            # ERROR-MODEL: non-value status must have NO fabricated numeric
            if has_numeric:
                errors.append(
                    f"{variant}: status={status} but a ddG numeric "
                    f"{ddg_attr.Get()} was written (fabrication!)")

    detail["mutant_variants_checked"] = checked_mutants
    detail["per_variant"] = per_variant
    if checked_mutants == 0:
        errors.append("no mutant variants found to check")
    return ReadbackResult("ddg_written_back", not errors, errors, detail)


def run(stage_path: str = None, pdb_path: str = None) -> list:
    stage_path = stage_path or default_output_path()
    pdb_path = pdb_path or p53_env.get_structure_path("1ycr.pdb")
    fixture_path = _fixture_path()
    if not os.path.isfile(stage_path):
        return [ReadbackResult("genotype_stage_exists", False,
                               [f"not found: {stage_path}"])]
    return [
        assert_fixture_is_honestly_tagged(fixture_path),
        assert_ddg_written_back(stage_path, pdb_path, fixture_path),
    ]


if __name__ == "__main__":
    results = run()
    ok = all(r.passed for r in results)
    for r in results:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.check_name}")
        for e in r.errors:
            print(f"    - {e}")
        if r.detail:
            print(f"    detail: {r.detail}")
    raise SystemExit(0 if ok else 1)
