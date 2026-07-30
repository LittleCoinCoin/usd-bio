"""
Offline gates over the captured container evidence and the two build recipes.

This is the first test module that reads `examples/p53_mdm2/cluster/` artifacts.
Everything here is pure stdlib and runs on a laptop: no network, no cluster, no
docker, no singularity, no pxr. It re-reads what the attended cluster sessions
captured and asserts it against expectations STATED HERE, never re-derived from
the same file by the same parser twice (R02 read-back doctrine).

The highest-value assertion is NOT the SASS list -- it is recipe-versus-recipe
and recipe-versus-evidence consistency. `./Dockerfile` and `./gromacs.def` are
parallel implementations of one image and their own headers concede the sync
obligation between them is only social ("KEEP THE TWO FILES IN SYNC"). These
checks mechanise it, and go red the moment a pin moves without a re-capture.

ZERO-ROWS-WHEN-ABSENT (load-bearing, do not "improve"):
    run_tests.py has no skip concept and reads `passed` as a bool, so a row for
    "evidence not captured yet" would redden the suite permanently. Therefore:
      * `run()` returns [] when cluster/evidence/ does not exist at all;
      * every check family contributes zero rows when the specific evidence
        file it reads is absent -- the dgx1 checks are dark until
        `dgx1_sif_open.txt` lands, then light up on their own.
    Absent file  -> no row (a deferred roadmap leaf).
    Present file that will not parse -> a FAIL row (a real defect).

Checks (row counts are per present-evidence, one row each):
    recipe_twin_agreement       Dockerfile <-> gromacs.def pins agree
    recipe_evidence_agreement   those pins agree with the captured output and
                                with the delivered .sif's inspect labels
    manifest_integrity          every manifest line's sha256/bytes match disk
    required_sass_targets       _REQUIRED_SM present as ELF in every captured
                                SASS summary, and the rebuild summary is
                                identical to the original (build equivalence)
    no_buildstatus_label        the scaffolding label reached neither recipe
                                nor the delivered artifact
    docker_sif_version_parity   docker-path vs sif-path `gmx --version` fields
    docker_sif_energy_parity    the two minimisation energies, relative tol
    dgx1_digest_parity          banyan-computed == dgx1-computed sif digest
    dgx1_sif_opens              inspect + exec succeed under singularity 3.5.2

Deliberately NOT asserted: wall-clock timings and step rates. They vary with
node load; a flaky gate teaches people to ignore failures.
"""

from __future__ import annotations

import hashlib
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)                       # examples/p53_mdm2
_CLUSTER = os.path.join(_PKG, "cluster")
_EVIDENCE = os.path.join(_CLUSTER, "evidence")

_DOCKERFILE = os.path.join(_CLUSTER, "Dockerfile")
_DEFFILE = os.path.join(_CLUSTER, "gromacs.def")
_MANIFEST = os.path.join(_EVIDENCE, "manifest.jsonl")
_SASS_AUDIT = os.path.join(_EVIDENCE, "sass_audit_banyan.txt")
_DOCKER_SMOKE = os.path.join(_EVIDENCE, "docker_gpu_smoke_banyan.txt")
_CONVERT_VERIFY = os.path.join(_EVIDENCE, "convert_verify_banyan.txt")
_DGX1_OPEN = os.path.join(_EVIDENCE, "dgx1_sif_open.txt")

# --- Stated expectations (NOT read back out of the evidence) -----------------
# The cross-cluster portability claim in one line: real SASS for dgx1's V100
# (sm_70) and banyan's H100 (sm_90). JIT-only PTX would not satisfy this.
_REQUIRED_SM = {"sm_70", "sm_90"}

# The delivered artifact's identity, as recorded when it was created
# [source: examples/p53_mdm2/cluster/evidence/convert_verify_banyan.txt
#  "### DELIVERED ARTIFACT" / sif_sha256].
_DELIVERED_SIF_SHA256 = \
    "1fc04f8b48a87f7e0cce4c4b1f3ae7ea5cd640b55c22586c115ce3bed20c81ac"

# One part in a thousand, per the convert_verify leaf. Floating-point reduction
# order is not guaranteed identical across runtimes, so exact equality is the
# wrong gate; the observed delta is ~1.4e-06 relative, so this is not a
# tolerance tuned to pass.
_ENERGY_REL_TOL = 1e-3

# `gmx --version` fields that must survive docker -> singularity conversion.
_GMX_VERSION_FIELDS = (
    "GROMACS version",
    "Precision",
    "GPU support",
    "SIMD instructions",
    "CUDA runtime",
)

# Pins each recipe must declare; a missing one is a malformed recipe.
_RECIPE_PIN_PATTERNS = {
    "base_image": r"^\s*(?:FROM|From:)\s+(\S+)\s*$",
    "gromacs_version": r"GROMACS_VERSION=([^;\s\\]+)",
    "cuda_target_sm": r'-DGMX_CUDA_TARGET_SM="([^"]+)"',
    "cuda_target_compute": r'-DGMX_CUDA_TARGET_COMPUTE="([^"]+)"',
    "gmx_simd": r"-DGMX_SIMD=([^;\s\\]+)",
    "label_gromacs_ver": r'GromacsVer[=\s]+"?([^"\s\\]+)"?',
    "label_target_sm": r'TargetSM[=\s]+"?([^"\s\\]+)"?',
    "label_cuda_toolkit": r'CudaToolkit[=\s]+"?([^"\s\\]+)"?',
}

# The value the removed scaffolding label used to carry. It must never reach a
# recipe or an artifact: a LABEL is baked in and becomes a permanent, wrong
# provenance claim.
_SCAFFOLDING_LABEL_VALUE = "SCAFFOLDING-not-built"


# --- parsers (raise on malformed input; callers guard on absence) ------------

def _read(path):
    with open(path, "r") as fh:
        return fh.read()


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _strip_comments(text):
    """Drop full-line `#` comments and trailing ` # ...`.

    Needed because both recipes discuss their own pins at length in prose --
    e.g. the Dockerfile shows a digest-pinned `FROM` inside a comment -- so a
    naive grep would parse documentation as configuration.
    """
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        out.append(re.split(r"\s+#", line, maxsplit=1)[0])
    return "\n".join(out)


def _load_manifest():
    """Evidence manifest as a list of dicts. Raises on a malformed line."""
    entries = []
    for lineno, line in enumerate(_read(_MANIFEST).splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except ValueError as exc:
            raise ValueError(f"manifest.jsonl:{lineno}: not JSON: {exc}") from exc
        for key in ("body_file", "sha256", "bytes"):
            if key not in obj:
                raise ValueError(f"manifest.jsonl:{lineno}: missing key {key!r}")
        entries.append(obj)
    if not entries:
        raise ValueError("manifest.jsonl is empty")
    return entries


def _parse_summary_block(text):
    """The `--- SUMMARY ---` KEY=VALUE block as a dict.

    The audit script emits this block precisely so a test can assert over it
    without scraping human prose. Exactly one block is expected per file.
    """
    blocks = re.findall(r"^--- SUMMARY ---$\n(.*?)^--- END SUMMARY ---$",
                        text, re.M | re.S)
    if len(blocks) != 1:
        raise ValueError(f"expected exactly 1 SUMMARY block, found {len(blocks)}")
    summary = {}
    for line in blocks[0].splitlines():
        if not line.strip():
            continue
        if "=" not in line:
            raise ValueError(f"malformed SUMMARY line: {line!r}")
        key, _, value = line.partition("=")
        summary[key.strip()] = value.strip()
    if not summary:
        raise ValueError("SUMMARY block carries no keys")
    return summary


def _parse_gmx_version(text):
    """`gmx --version` fields as a dict, from a capture containing one block.

    Patterns are line-anchored on purpose: the evidence files also quote the
    build recipe and shell commands that mention these same field names.
    """
    fields = {}
    for name in _GMX_VERSION_FIELDS:
        found = re.findall(r"^\s*" + re.escape(name) + r":\s*(.+?)\s*$", text, re.M)
        distinct = sorted(set(found))
        if not distinct:
            raise ValueError(f"no {name!r} line in the capture")
        if len(distinct) > 1:
            raise ValueError(f"conflicting {name!r} values: {distinct}")
        fields[name] = distinct[0]
    return fields


def _potential_energy(text):
    """The minimisation potential energy from a capture, as a float."""
    found = re.findall(r"Potential Energy\s*=\s*(\S+)", text)
    if not found:
        raise ValueError("no 'Potential Energy =' line in the capture")
    values = sorted({float(v) for v in found})
    if len(values) > 1:
        raise ValueError(f"conflicting potential energies: {values}")
    return values[0]


def _recipe_pins(path):
    """Pinned values declared by one recipe. Raises if a pin is missing."""
    text = _strip_comments(_read(path))
    pins = {}
    for name, pattern in _RECIPE_PIN_PATTERNS.items():
        found = re.findall(pattern, text, re.M)
        distinct = sorted(set(found))
        if not distinct:
            raise ValueError(f"{os.path.basename(path)}: pin {name!r} not found")
        if len(distinct) > 1:
            raise ValueError(
                f"{os.path.basename(path)}: pin {name!r} declared more than "
                f"once with differing values: {distinct}")
        pins[name] = distinct[0]
    return pins


def _toolkit_from_image(base_image):
    """`nvidia/cuda:12.9.1-devel-ubuntu22.04` -> `12.9.1`."""
    tag = base_image.rsplit(":", 1)[-1]
    return tag.split("-", 1)[0]


def _sm_set(target_sm):
    """`70;90` -> {'sm_70', 'sm_90'}."""
    return {"sm_" + part.strip() for part in target_sm.split(";") if part.strip()}


# --- checks ------------------------------------------------------------------

def _check_recipe_twin_agreement():
    """Every pin must be identical in both parallel implementations."""
    docker = _recipe_pins(_DOCKERFILE)
    definition = _recipe_pins(_DEFFILE)
    errors = []
    for name in sorted(_RECIPE_PIN_PATTERNS):
        if docker[name] != definition[name]:
            errors.append(f"{name}: Dockerfile={docker[name]!r} != "
                          f"gromacs.def={definition[name]!r}")
    # A recipe's own labels are a provenance claim about its own flags, so they
    # must agree with the flags in the same file -- checked per file, not just
    # across the twins.
    for label, path in (("Dockerfile", docker), ("gromacs.def", definition)):
        if path["label_gromacs_ver"] != path["gromacs_version"]:
            errors.append(f"{label}: GromacsVer label "
                          f"{path['label_gromacs_ver']!r} != GROMACS_VERSION "
                          f"{path['gromacs_version']!r}")
        if path["label_target_sm"] != path["cuda_target_sm"]:
            errors.append(f"{label}: TargetSM label {path['label_target_sm']!r} "
                          f"!= GMX_CUDA_TARGET_SM {path['cuda_target_sm']!r}")
        toolkit = _toolkit_from_image(path["base_image"])
        if path["label_cuda_toolkit"] != toolkit:
            errors.append(f"{label}: CudaToolkit label "
                          f"{path['label_cuda_toolkit']!r} != base image "
                          f"toolkit {toolkit!r}")
    return errors, {"pins": docker}


def _check_recipe_evidence_agreement():
    """The recipe pins must match what the built image actually reported."""
    pins = _recipe_pins(_DEFFILE)   # gromacs.def is the stated source of truth
    text = _read(_SASS_AUDIT)
    summary = _parse_summary_block(text)
    version = _parse_gmx_version(text)
    errors = []

    expected_sm = _sm_set(pins["cuda_target_sm"])
    observed_sm = set(summary.get("SM_ELF", "").split(";")) - {""}
    if observed_sm != expected_sm:
        errors.append(f"SM_ELF={sorted(observed_sm)} != recipe "
                      f"GMX_CUDA_TARGET_SM {sorted(expected_sm)}")
    if version["GROMACS version"] != pins["gromacs_version"]:
        errors.append(f"captured GROMACS version "
                      f"{version['GROMACS version']!r} != recipe pin "
                      f"{pins['gromacs_version']!r}")
    if version["SIMD instructions"] != pins["gmx_simd"]:
        errors.append(f"captured SIMD {version['SIMD instructions']!r} != "
                      f"recipe GMX_SIMD {pins['gmx_simd']!r}")
    toolkit = _toolkit_from_image(pins["base_image"])
    if not re.search(r"^CUDA Version " + re.escape(toolkit) + r"\s*$", text, re.M):
        errors.append(f"capture does not report 'CUDA Version {toolkit}' from "
                      f"the pinned base image {pins['base_image']!r}")

    # The delivered .sif's inspect labels are the same claim, made by the
    # artifact rather than the recipe -- assert them too when that capture
    # exists (absent capture contributes no error, only less coverage).
    detail = {"toolkit": toolkit, "sm_elf": sorted(observed_sm)}
    if os.path.isfile(_CONVERT_VERIFY):
        inspect = _read(_CONVERT_VERIFY)
        for key, pin in (("GromacsVer", "label_gromacs_ver"),
                         ("TargetSM", "label_target_sm"),
                         ("CudaToolkit", "label_cuda_toolkit")):
            found = re.findall(r"^" + key + r":\s*(.+?)\s*$", inspect, re.M)
            if not found:
                errors.append(f"singularity inspect output has no {key} label")
            elif found[0] != pins[pin]:
                errors.append(f"inspect {key}={found[0]!r} != recipe "
                              f"{pins[pin]!r}")
        detail["inspect_labels_checked"] = True
    return errors, detail


def _check_manifest_integrity():
    """Recompute every recorded digest and size. A hand-edited copy is this
    evidence class's real failure mode, and only the digest catches it."""
    errors, checked = [], []
    for entry in _load_manifest():
        body = os.path.join(_EVIDENCE, entry["body_file"])
        if not os.path.isfile(body):
            continue    # a manifest line whose body is not (yet) committed here
        checked.append(entry["body_file"])
        actual_bytes = os.path.getsize(body)
        if actual_bytes != entry["bytes"]:
            errors.append(f"{entry['body_file']}: {actual_bytes} bytes on disk "
                          f"!= recorded {entry['bytes']}")
        actual_sha = _sha256(body)
        if actual_sha != entry["sha256"]:
            errors.append(f"{entry['body_file']}: sha256 {actual_sha} != "
                          f"recorded {entry['sha256']}")
    if not checked:
        errors.append("no manifest entry names a file present in evidence/")
    return errors, {"bodies_verified": checked}


def _check_required_sass_targets():
    """Both required architectures must be present as real ELF (SASS).

    Also compares the rebuilt image's summary against the original capture --
    the build-equivalence datum -- recomputed here rather than trusting the
    EQUIVALENCE_SUMMARY verdict the capture states about itself.
    """
    original = _parse_summary_block(_read(_SASS_AUDIT))
    errors = []
    summaries = {"sass_audit_banyan.txt": original}
    if os.path.isfile(_CONVERT_VERIFY):
        summaries["convert_verify_banyan.txt"] = \
            _parse_summary_block(_read(_CONVERT_VERIFY))

    for name, summary in sorted(summaries.items()):
        observed = set(summary.get("SM_ELF", "").split(";")) - {""}
        missing = _REQUIRED_SM - observed
        if missing:
            errors.append(f"{name}: SM_ELF lacks {sorted(missing)} -- the image "
                          f"has no real SASS for those architectures")
    if len(summaries) == 2 and original != summaries["convert_verify_banyan.txt"]:
        errors.append("rebuilt-image SASS summary differs from the original "
                      "capture, so the recipe correction was not "
                      "documentation-only")
    return errors, {"summaries_checked": sorted(summaries)}


def _check_no_buildstatus_label():
    """The scaffolding provenance label must reach neither recipe nor artifact."""
    errors = []
    for path in (_DOCKERFILE, _DEFFILE):
        name = os.path.basename(path)
        raw = _read(path)
        if _SCAFFOLDING_LABEL_VALUE in raw:
            errors.append(f"{name}: carries the scaffolding label value "
                          f"{_SCAFFOLDING_LABEL_VALUE!r}")
        # Prose may discuss the removed key; an active declaration may not
        # exist, so look only outside comments.
        if "BuildStatus" in _strip_comments(raw):
            errors.append(f"{name}: declares a BuildStatus label outside "
                          f"comments")
    inspect = _read(_CONVERT_VERIFY)
    if re.search(r"^BuildStatus\s*:", inspect, re.M):
        errors.append("singularity inspect output carries a BuildStatus label, "
                      "so the recipe correction did not reach the artifact")
    return errors, {}


def _check_docker_sif_version_parity():
    """Conversion must not move any build-configuration field."""
    docker = _parse_gmx_version(_read(_DOCKER_SMOKE))
    sif = _parse_gmx_version(_read(_CONVERT_VERIFY))
    errors = []
    for name in _GMX_VERSION_FIELDS:
        if docker[name] != sif[name]:
            errors.append(f"{name}: docker={docker[name]!r} != "
                          f"sif={sif[name]!r}")
    return errors, {"fields": docker}


def _check_docker_sif_energy_parity():
    """The two minimisations must agree to within a relative tolerance."""
    docker_e = _potential_energy(_read(_DOCKER_SMOKE))
    convert = _read(_CONVERT_VERIFY)
    sif_e = _potential_energy(convert)
    errors = []
    rel = abs(sif_e - docker_e) / abs(docker_e)
    if rel > _ENERGY_REL_TOL:
        errors.append(f"relative energy difference {rel:.6g} exceeds "
                      f"{_ENERGY_REL_TOL:g}: docker={docker_e!r} "
                      f"sif={sif_e!r}")
    # The convert capture also states the pair it compared. Cross-check the
    # docker side against the value parsed from the docker capture itself, so a
    # transcription slip between the two files cannot pass unnoticed.
    for key, expected in (("docker_min_potential_energy", docker_e),
                          ("sif_min_potential_energy", sif_e)):
        found = re.findall(r"^" + key + r":\s*(\S+)\s*$", convert, re.M)
        if not found:
            errors.append(f"convert capture records no {key}")
        elif float(found[0]) != expected:
            errors.append(f"{key}={found[0]} disagrees with the energy parsed "
                          f"from the run capture ({expected!r})")
    return errors, {"docker": docker_e, "sif": sif_e, "relative": rel}


def _check_dgx1_digest_parity():
    """Both clusters must see the same bytes on the shared NFS home."""
    summary = _parse_summary_block(_read(_DGX1_OPEN))
    banyan = summary.get("SIF_SHA256_BANYAN", "")
    dgx1 = summary.get("SIF_SHA256_DGX1", "")
    errors = []
    if not banyan or not dgx1:
        errors.append("SIF_SHA256_BANYAN / SIF_SHA256_DGX1 missing from summary")
    elif banyan != dgx1:
        errors.append(f"shared home does NOT present identical bytes: "
                      f"banyan={banyan} dgx1={dgx1}")
    if banyan and banyan != _DELIVERED_SIF_SHA256:
        errors.append(f"banyan digest {banyan} != the delivered artifact digest "
                      f"recorded at creation ({_DELIVERED_SIF_SHA256})")
    recorded = summary.get("DIGEST_PARITY", "")
    if recorded != "match":
        errors.append(f"DIGEST_PARITY={recorded!r}, expected 'match'")
    return errors, {"digest": banyan}


def _check_dgx1_sif_opens():
    """A 2019 runtime must mount and read a 2024-written squashfs."""
    summary = _parse_summary_block(_read(_DGX1_OPEN))
    errors = []
    if summary.get("DGX1_INSPECT_RC") != "0":
        errors.append(f"singularity inspect exited "
                      f"{summary.get('DGX1_INSPECT_RC')!r}, expected 0")
    if not summary.get("DGX1_INSPECT_GROMACSVER"):
        errors.append("inspect printed no GROMACS version label")
    # exec is the real test: inspect reads metadata, exec must mount squashfs.
    if summary.get("DGX1_EXEC_LS_RC") != "0":
        errors.append(f"singularity exec listing exited "
                      f"{summary.get('DGX1_EXEC_LS_RC')!r}, expected 0")
    if summary.get("DGX1_EXEC_GMX_PRESENT") != "yes":
        errors.append(f"gmx binary not seen inside the mounted image "
                      f"(DGX1_EXEC_GMX_PRESENT="
                      f"{summary.get('DGX1_EXEC_GMX_PRESENT')!r})")
    return errors, {"singularity": summary.get("DGX1_SINGULARITY_VERSION", "")}


# --- harness entry point -----------------------------------------------------

def _row(name, fn):
    """One result row. A parser raise becomes a FAIL, not a harness crash."""
    try:
        errors, detail = fn()
    except Exception as exc:
        errors, detail = [f"{type(exc).__name__}: {exc}"], {}
    return {"check_name": name, "passed": not errors, "errors": errors,
            "detail": detail}


def run() -> list:
    """Harness entry point.

    Returns ZERO rows when cluster/evidence/ is absent, and skips any check
    family whose evidence file has not been captured yet. See the module
    docstring: the harness has no skip concept, so a row is only ever emitted
    for evidence that exists.
    """
    if not os.path.isdir(_EVIDENCE):
        return []

    rows = [_row("recipe_twin_agreement", _check_recipe_twin_agreement)]
    if os.path.isfile(_SASS_AUDIT):
        rows.append(_row("recipe_evidence_agreement",
                         _check_recipe_evidence_agreement))
        rows.append(_row("required_sass_targets", _check_required_sass_targets))
    if os.path.isfile(_MANIFEST):
        rows.append(_row("manifest_integrity", _check_manifest_integrity))
    if os.path.isfile(_CONVERT_VERIFY):
        rows.append(_row("no_buildstatus_label", _check_no_buildstatus_label))
    if os.path.isfile(_CONVERT_VERIFY) and os.path.isfile(_DOCKER_SMOKE):
        rows.append(_row("docker_sif_version_parity",
                         _check_docker_sif_version_parity))
        rows.append(_row("docker_sif_energy_parity",
                         _check_docker_sif_energy_parity))
    if os.path.isfile(_DGX1_OPEN):
        rows.append(_row("dgx1_digest_parity", _check_dgx1_digest_parity))
        rows.append(_row("dgx1_sif_opens", _check_dgx1_sif_opens))
    return rows


if __name__ == "__main__":
    rs = run()
    if not rs:
        print("container-evidence: 0 checks (no cluster/evidence/ captured yet)")
        raise SystemExit(0)
    for r in rs:
        print(f"[{'PASS' if r['passed'] else 'FAIL'}] {r['check_name']}")
        for e in r["errors"]:
            print(f"    - {e}")
        if r["detail"]:
            print(f"    detail: {r['detail']}")
    raise SystemExit(0 if all(r["passed"] for r in rs) else 1)
