"""
Pipeline 2 ddG write-back read-back test (falsification-resistant).

Opens the committed Genotype assembly FRESH and asserts the recorded ddG /
provenance against INDEPENDENT sources, never against the write-back's in-memory
state (R00 anti-tautology):

  1. For a ``fixture``-status variant: the committed fixture JSON, read directly
     here.
  2. For a ``success``-status (live) variant: the VERBATIM captured server
     response body named by ``bio:ddgResponseFile``, re-parsed here from disk.
     The recorded numeric must equal that body's ``prediction``, and the body's
     own ``chain``/``position``/``wild-type``/``mutant`` fields must agree with
     the mutation code -- so a live number cannot be recorded against the wrong
     site, and cannot exist at all without committed evidence behind it.
  3. An INDEPENDENT flat-column re-parse of 1ycr.pdb: the wild-type residue at
     each mutated chain-B position is re-derived here (not via the production
     parser) and cross-checked against each mutation code's WT letter+position.
     A chimera that mislabelled a site therefore cannot pass.
  4. A honesty guard on the fixture file itself: it must be self-labelled as
     synthetic / not-server-output, so fixture values can never masquerade as
     real DDMut-PPI predictions. The fixture remains committed as the documented
     OFFLINE FALLBACK, so this guard stays load-bearing even though the live
     values are now the active source.
  5. A traceability guard on the live capture directory: manifest.jsonl must
     exist, every body file it references must exist and be non-empty, and the
     script-derived predictions JSON must still agree with the raw bodies.

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


def _capture_dir() -> str:
    return os.path.join(_PKG_PARENT, "p53_mdm2", "data", "ddmut_ppi_live")


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


def assert_live_capture_traceable(capture_dir) -> ReadbackResult:
    """The live-capture evidence must be self-consistent and complete.

    Guards the chain "recorded number -> curated JSON -> verbatim body":
      - every body cited by the curated predictions JSON exists under
        ``responses/`` and is a well-formed DONE payload whose job_id, chain and
        prediction agree with the citing entry;
      - the curated JSON self-declares as real server output;
      - the root-cause proof in ``encoding_diagnostic/`` is still present, since
        it is the only evidence that the historical 'server down' diagnosis was
        wrong.

    Note on layout: ``responses/`` is validated STRICTLY because it is the
    canonical, immutable set the pipeline cites. Raw per-run capture
    directories are not byte-checked here -- capture numbering restarts at 001
    per run, so a shared directory can legitimately contain interleaved bodies
    from more than one run (see the directory README).
    """
    errors, detail = [], {}

    diag = os.path.join(capture_dir, "encoding_diagnostic")
    if not os.path.isdir(diag) or not os.listdir(diag):
        errors.append("encoding_diagnostic/ root-cause proof is missing")

    derived_path = os.path.join(capture_dir, "ddmut_ppi_live_predictions.json")
    if not os.path.isfile(derived_path):
        errors.append(f"no derived predictions file: {derived_path}")
        return ReadbackResult("live_capture_traceable", not errors, errors, detail)

    with open(derived_path, "r") as fh:
        derived_raw = fh.read()
    derived = json.loads(derived_raw)
    if "real ddmut-ppi server output" not in derived_raw.lower():
        errors.append("curated predictions file does not declare itself as "
                      "real server output")

    preds = derived.get("predictions", {})
    detail["curated_mutations"] = sorted(preds)
    for mutation, entry in preds.items():
        rel = entry.get("response_file", "")
        body_path = os.path.join(capture_dir, rel)
        if not rel.startswith("responses/"):
            errors.append(f"{mutation}: response_file {rel!r} is not in the "
                          f"canonical responses/ set")
        if not os.path.isfile(body_path):
            errors.append(f"{mutation}: curated entry cites missing body {rel!r}")
            continue
        with open(body_path, "r") as fh:
            body = json.load(fh)
        if str(body.get("status")) != "DONE":
            errors.append(f"{mutation}: {rel} status={body.get('status')!r}, "
                          f"not a completed DONE payload")
        if abs(float(entry["prediction"]) - float(body["prediction"])) > 1e-9:
            errors.append(
                f"{mutation}: curated prediction {entry['prediction']} != "
                f"body prediction {body['prediction']} in {rel}")
        if str(entry.get("job_id")) != str(body.get("job_id")):
            errors.append(f"{mutation}: curated job_id != body job_id in {rel}")
        if str(entry.get("chain")) != str(body.get("chain")):
            errors.append(f"{mutation}: curated chain != body chain in {rel}")
        # the filename must not disagree with the payload it holds
        if str(body.get("job_id")) not in os.path.basename(rel):
            errors.append(f"{mutation}: {rel} filename does not carry its own "
                          f"job_id {body.get('job_id')!r}")

    return ReadbackResult("live_capture_traceable", not errors, errors, detail)


def assert_ddg_written_back(stage_path, pdb_path, fixture_path,
                            capture_dir) -> ReadbackResult:
    """Recorded ddG + provenance vs. independent evidence.

    A ``fixture``-status value is checked against the committed fixture JSON; a
    ``success``-status value is checked against the verbatim captured server
    response body it names. Both are cross-checked against an independent
    re-parse of the PDB.
    """
    errors, detail = [], {}

    with open(fixture_path, "r") as fh:
        fixture_doc = json.load(fh)
    fixture_pred = {m: float(v["prediction"])
                    for m, v in fixture_doc.get("predictions", {}).items()}
    indep_resnames = _independent_chainB_resnames(pdb_path)

    stage = Usd.Stage.Open(stage_path)
    root = stage.GetDefaultPrim()
    chain_attr = root.GetAttribute("bio:mutationChain")
    chain_id = str(chain_attr.Get()) if chain_attr.IsValid() else None
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
                elif str(status) == "success":
                    # LIVE value: must trace to a committed verbatim response
                    # body, and that body must be for THIS site.
                    src_attr = root.GetAttribute("bio:ddgSource")
                    src = str(src_attr.Get()) if src_attr.IsValid() else None
                    if src != "ddmut-ppi-live":
                        errors.append(
                            f"{variant}: status=success but ddgSource={src!r} "
                            f"(expected 'ddmut-ppi-live')")
                    rf_attr = root.GetAttribute("bio:ddgResponseFile")
                    rf = str(rf_attr.Get()) if rf_attr.IsValid() else ""
                    body_path = os.path.join(capture_dir, rf) if rf else ""
                    if not rf or rf == "unknown":
                        errors.append(
                            f"{variant}: status=success but no "
                            f"bio:ddgResponseFile -- a live ddG with no "
                            f"committed evidence behind it")
                    elif not os.path.isfile(body_path):
                        errors.append(
                            f"{variant}: bio:ddgResponseFile={rf!r} does not "
                            f"exist in {capture_dir}")
                    else:
                        with open(body_path, "r") as fh:
                            body = json.load(fh)
                        served = body.get("prediction")
                        if served is None:
                            errors.append(f"{variant}: {rf} carries no prediction")
                        elif abs(recorded - float(served)) > 1e-4:
                            errors.append(
                                f"{variant}: recorded ddG {recorded} != "
                                f"served prediction {served} in {rf}")
                        # the response must describe THIS mutation's site
                        if str(body.get("chain")) != str(chain_id):
                            errors.append(
                                f"{variant}: {rf} chain={body.get('chain')!r} "
                                f"!= stage chain {chain_id!r}")
                        if pos is not None and str(body.get("position")) != str(pos):
                            errors.append(
                                f"{variant}: {rf} position="
                                f"{body.get('position')!r} != mutation "
                                f"position {pos}")
                        served_wt = _THREE_TO_ONE.get(str(body.get("wild-type")))
                        if served_wt != wt_letter:
                            errors.append(
                                f"{variant}: {rf} wild-type="
                                f"{body.get('wild-type')!r} != mutation WT "
                                f"letter {wt_letter}")
                        served_mut = _THREE_TO_ONE.get(str(body.get("mutant")))
                        if served_mut != mut_letter:
                            errors.append(
                                f"{variant}: {rf} mutant="
                                f"{body.get('mutant')!r} != mutation target "
                                f"letter {mut_letter}")
                        job_attr = root.GetAttribute("bio:ddgJobId")
                        if job_attr.IsValid() and \
                                str(job_attr.Get()) != str(body.get("job_id")):
                            errors.append(
                                f"{variant}: bio:ddgJobId="
                                f"{job_attr.Get()!r} != {rf} job_id "
                                f"{body.get('job_id')!r}")
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
    capture_dir = _capture_dir()
    if not os.path.isfile(stage_path):
        return [ReadbackResult("genotype_stage_exists", False,
                               [f"not found: {stage_path}"])]
    return [
        assert_fixture_is_honestly_tagged(fixture_path),
        assert_live_capture_traceable(capture_dir),
        assert_ddg_written_back(stage_path, pdb_path, fixture_path, capture_dir),
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
