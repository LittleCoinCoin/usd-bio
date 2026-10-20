"""
Offline read-back checks over the first executed p53-MDM2 MD run (banyan job 119).

Pure stdlib, no pxr, no network, no cluster. Re-reads
`cluster/evidence/p53_md_banyan_job119.txt` (and the job-118 captures for the
manifest check) and asserts against expectations STATED HERE, hand-derived from
the structure and the committed deck -- never re-derived from the same file by
the same parser (R02 / R00 anti-tautology doctrine). Pattern follows
test_container_evidence.py.

ZERO-ROWS-WHEN-ABSENT: absent evidence file -> no rows (run_tests.py has no
skip concept). Present but unparseable -> a FAIL row.

Hand-derived expectations (see the constants below):
    1YCR chain A 85 residues / 706 atoms, chain B 13 residues / 113 atoms,
    so 98 residues, 819 heavy+H atoms after OXT insertion (818 + 1 OXT on A109);
    pdb2gmx -ignh rebuilds hydrogens, giving 1670 protein atoms.
    Topology charge +5 (A) and -2 (B) = +3 before ions.
    Ion bookkeeping: 3 CL neutralise the +3, then 0.15 M adds 16 NA/CL pairs:
        NA = 16, CL = 3 + 16 = 19, net ion charge 16 - 19 = -3, total 0.
    TIP3P is 3 atoms/water: TOTAL_ATOMS = 1670 + 3*5286 + 16 + 19 = 17563.

SELF-TEST ROW (`falsification_selftest`): every other family is re-run on an
in-memory mutated copy of the capture and must go red. This proves the checks
can fail without touching evidence on disk.

Deliberately NOT asserted: ns/day throughput (node-load dependent).
"""

from __future__ import annotations

import hashlib
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_CLUSTER = os.path.join(_PKG, "cluster")
_EVIDENCE = os.path.join(_CLUSTER, "evidence")
_DECK = os.path.join(_CLUSTER, "p53_md")
_USDA = os.path.join(_PKG, "output", "p53_mdm2_md_setup_gromacs.usda")

_JOB119 = os.path.join(_EVIDENCE, "p53_md_banyan_job119.txt")
_JOB118_FAIL = os.path.join(_EVIDENCE, "p53_md_banyan_job118_grompp_ions_fail.txt")
_JOB118_OK = os.path.join(_EVIDENCE, "p53_md_banyan_job118_grompp_ions.txt")
_MANIFEST = os.path.join(_EVIDENCE, "manifest.jsonl")
_COLD_VERIFY = os.path.join(_EVIDENCE, "convert_verify_cold_banyan.txt")

# --- Stated expectations (NOT read back out of the evidence) -----------------
_EXPECT = {
    "PDB_ATOM_RECORDS_IN": "818",
    "PDB_ATOM_RECORDS_CLEAN": "819",
    "OXT_ADDED": "A109",
    "PROTEIN_RESIDUES_CHAIN_A": "85",
    "PROTEIN_RESIDUES_CHAIN_B": "13",
    "PROTEIN_CHAINS": "2",
    "PROTEIN_ATOMS": "1670",
    "IONS_NA": "16",
    "IONS_CL": "19",
    "WATERS": "5286",
    "TOTAL_ATOMS": "17563",
    "CONTAINER_EXIT": "0",
    "VERSION_EXIT": "0",
    "GROMPP_MAXWARN": "0",
    "STAGES": "em nvt npt md",
}
_CHARGE_A, _CHARGE_B, _NET_CHARGE = 5.0, -2.0, 3.0
_ATOMS_PER_WATER = 3          # TIP3P
_RESIDUES_TOTAL = 85 + 13     # "98 residues" in the pdb2gmx banner
_T_TARGET_K = 310.0
_T_TOL_K = 3.0                # observed 309.70-309.88; V-rescale, short runs
_DENSITY_RANGE = (1000.0, 1020.0)   # kg/m3, aqueous 0.15 M system at 310 K
_EMTOL_STATED = 1000.0        # em.mdp as committed
_DYNAMICS = ("NVT", "NPT", "MD")

# Digest of the delivered sif for this run: the cold-rebuilt one-image sif
# recorded in convert_verify_cold_banyan.txt (NOT the older 1fc7... sif that
# test_container_evidence._DELIVERED_SIF_SHA256 pins; see report).
_SIF_SHA256 = "221d748ec44c531fb4d9442624f13ae5693c3d3389b4f4d4a698bf5b01de95fa"

# Stated manifest values for the three p53 MD captures (seq 16-18).
_MANIFEST_EXPECT = {
    "p53_md_banyan_job119.txt":
        ("f617dfe82efdb9424adc876946bd889a2a820f3fee0efb11b0392443f866de91", 7060),
    "p53_md_banyan_job118_grompp_ions.txt":
        ("ec00977d804282963409d9767e07ec9ce0a4c1f436771320c1a6b45e260d45be", 2637),
    "p53_md_banyan_job118_grompp_ions_fail.txt":
        ("cffead7886a947c96d717b2cc8bb8af3b75466ae9ec8ea32d36adfc32a5ca7fa", 5472),
}

_DECK_FILES = ("prep.env", "em.mdp", "nvt.mdp", "npt.mdp", "md.mdp",
               "p53_md_run.sh")


# --- helpers -----------------------------------------------------------------

def _read(path):
    with open(path, "r") as fh:
        return fh.read()


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _summary(text):
    blocks = re.findall(r"^--- SUMMARY ---$\n(.*?)^--- END SUMMARY ---$",
                        text, re.M | re.S)
    if len(blocks) != 1:
        raise ValueError(f"expected exactly 1 SUMMARY block, found {len(blocks)}")
    out = {}
    for line in blocks[0].splitlines():
        if not line.strip():
            continue
        if "=" not in line:
            raise ValueError(f"malformed SUMMARY line: {line!r}")
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    if not out:
        raise ValueError("SUMMARY block carries no keys")
    return out


def _body(text):
    """KEY=VALUE lines from the container-side log, i.e. everything before the
    SUMMARY block. The SUMMARY is a re-emission of these; comparing the two
    catches a hand-edited summary."""
    head = text.split("======== SUMMARY ========", 1)[0]
    out = {}
    for k, v in re.findall(r"^([A-Z][A-Z0-9_]+)=(\S.*?)\s*$", head, re.M):
        # the prep.env echo in STEP 3 is shell-quoted ('x'); the SUMMARY is not
        out.setdefault(k, set()).add(v.strip("'"))
    return out


def _f(summary, key, errors):
    try:
        return float(summary[key])
    except (KeyError, ValueError):
        errors.append(f"{key}={summary.get(key)!r} is not a number")
        return None


# --- checks over the capture text --------------------------------------------

def _check_run_completed(text):
    errors = []
    s = _summary(text)
    if not re.search(r"^======== RESULT: rc=0 ========\s*$", text, re.M):
        errors.append("no 'RESULT: rc=0' trailer")
    for key in ("CONTAINER_EXIT", "VERSION_EXIT", "GROMPP_MAXWARN", "STAGES"):
        if s.get(key) != _EXPECT[key]:
            errors.append(f"{key}={s.get(key)!r} != {_EXPECT[key]!r}")
    if not re.search(r"^container_exit: 0\s*$", text, re.M):
        errors.append("no 'container_exit: 0' line")
    return errors, {"stages": s.get("STAGES")}


def _check_system_counts(text):
    s = _summary(text)
    errors = []
    for key in ("PDB_ATOM_RECORDS_IN", "PDB_ATOM_RECORDS_CLEAN", "OXT_ADDED",
                "PROTEIN_RESIDUES_CHAIN_A", "PROTEIN_RESIDUES_CHAIN_B",
                "PROTEIN_CHAINS", "PROTEIN_ATOMS"):
        if s.get(key) != _EXPECT[key]:
            errors.append(f"{key}={s.get(key)!r} != hand-counted {_EXPECT[key]!r}")
    # one OXT inserted: clean = in + 1, stated independently of the strings above
    try:
        if int(s["PDB_ATOM_RECORDS_CLEAN"]) != int(s["PDB_ATOM_RECORDS_IN"]) + 1:
            errors.append("clean records != input records + 1 OXT")
    except (KeyError, ValueError) as exc:
        errors.append(f"record counts unusable: {exc}")
    if not re.search(r"There are 2 chains and 0 blocks of water and "
                     rf"{_RESIDUES_TOTAL} residues with 819 atoms", text):
        errors.append(f"pdb2gmx banner is not '2 chains ... {_RESIDUES_TOTAL} "
                      f"residues with 819 atoms'")
    for key, want in (("CHARGE_CHAIN_A", _CHARGE_A), ("CHARGE_CHAIN_B", _CHARGE_B),
                      ("NET_CHARGE_TOPOLOGY", _NET_CHARGE),
                      ("NET_CHARGE_PRE_IONS_GROMPP", _NET_CHARGE)):
        got = _f(s, key, errors)
        if got is not None and abs(got - want) > 1e-6:
            errors.append(f"{key}={got} != {want}")
    if _CHARGE_A + _CHARGE_B != _NET_CHARGE:      # the stated constants agree
        errors.append("internal: stated chain charges do not sum to stated net")
    return errors, {"atoms": s.get("PROTEIN_ATOMS")}


def _check_ion_bookkeeping(text):
    s = _summary(text)
    errors = []
    try:
        na, cl = int(s["IONS_NA"]), int(s["IONS_CL"])
        wat, tot = int(s["WATERS"]), int(s["TOTAL_ATOMS"])
        prot = int(s["PROTEIN_ATOMS"])
    except (KeyError, ValueError) as exc:
        return [f"unusable counts: {exc}"], {}
    for key in ("IONS_NA", "IONS_CL", "WATERS", "TOTAL_ATOMS"):
        if s[key] != _EXPECT[key]:
            errors.append(f"{key}={s[key]} != stated {_EXPECT[key]}")
    # system charge after ions: protein +3, NA +1, CL -1  -> must be zero
    total_charge = _NET_CHARGE + na - cl
    if total_charge != 0:
        errors.append(f"net charge after ions = {total_charge:+g}, expected 0")
    # neutralisation needs exactly 3 CL; the rest are matched concentration pairs
    if cl - int(_NET_CHARGE) != na:
        errors.append(f"CL - 3 neutralising = {cl - int(_NET_CHARGE)} != NA {na}: "
                      f"concentration ions are not matched pairs")
    # atom arithmetic, from solvent count, not from the file's own total
    expected_total = prot + _ATOMS_PER_WATER * wat + na + cl
    if tot != expected_total:
        errors.append(f"TOTAL_ATOMS={tot} != {prot} + {_ATOMS_PER_WATER}*{wat} "
                      f"+ {na} + {cl} = {expected_total}")
    return errors, {"na": na, "cl": cl, "waters": wat, "total": tot}


def _check_em_converged(text, emtol=None):
    s = _summary(text)
    errors = []
    if emtol is None:
        emtol = _emtol_from_deck()
    if emtol != _EMTOL_STATED:
        errors.append(f"committed em.mdp emtol={emtol} != stated {_EMTOL_STATED}")
    fmax = _f(s, "EM_MAX_FORCE", errors)
    epot = _f(s, "EM_POTENTIAL_ENERGY", errors)
    if s.get("EM_CONVERGED") != "yes":
        errors.append(f"EM_CONVERGED={s.get('EM_CONVERGED')!r} != 'yes'")
    if fmax is not None and not fmax < emtol:
        errors.append(f"Fmax={fmax} is not below emtol={emtol}")
    if epot is not None and not epot < 0:
        errors.append(f"EM potential energy {epot} is not negative")
    return errors, {"fmax": fmax, "emtol": emtol, "epot": epot}


def _check_stage_thermo(text):
    s = _summary(text)
    errors = []
    detail = {}
    for st in _DYNAMICS:
        t = _f(s, f"{st}_AVG_TEMPERATURE", errors)
        if t is not None:
            detail[st] = t
            if abs(t - _T_TARGET_K) > _T_TOL_K:
                errors.append(f"{st} <T>={t} K is more than {_T_TOL_K} K from "
                              f"{_T_TARGET_K}")
    for st in ("NPT", "MD"):        # NVT is constant volume: no density claim
        d = _f(s, f"{st}_AVG_DENSITY", errors)
        if d is not None:
            detail[st + "_rho"] = d
            lo, hi = _DENSITY_RANGE
            if not lo <= d <= hi:
                errors.append(f"{st} density {d} kg/m3 outside [{lo}, {hi}]")
    return errors, detail


def _check_gpu_execution(text):
    s = _summary(text)
    errors = []
    for st in _DYNAMICS:
        for what in ("NONBONDED", "PME"):
            key = f"{st}_{what}_ON_GPU"
            if s.get(key) != "yes":
                errors.append(f"{key}={s.get(key)!r} != 'yes'")
    # md.log GPU lines, per dynamics stage (a bare 'yes' flag is the script's
    # own claim; the quoted md.log lines are GROMACS's)
    for st in ("nvt", "npt", "md"):
        m = re.search(rf"^--- {st}\.log ---$\n(.*?)(?=^--- \w+\.log ---$|^=+ )",
                      text, re.M | re.S)
        if not m:
            errors.append(f"no '--- {st}.log ---' section")
            continue
        sec = m.group(1)
        for needle in ("Number of GPUs detected: 1",
                       "compute cap.: 9.0",
                       "PP tasks will do (non-perturbed) short-ranged "
                       "interactions on the GPU",
                       "PME tasks will do all aspects on the GPU",
                       "Using GPU 8x4 nonbonded short-range kernels"):
            if needle not in sec:
                errors.append(f"{st}.log lacks {needle!r}")
    if s.get("GPU_NAME") != "NVIDIA H100 NVL":
        errors.append(f"GPU_NAME={s.get('GPU_NAME')!r}")
    for key in ("GPU_COMPUTE_CAP_NVIDIASMI", "GPU_COMPUTE_CAP_MDLOG",
                "REQUIRED_COMPUTE_CAP"):
        if s.get(key) != "9.0":
            errors.append(f"{key}={s.get(key)!r} != '9.0'")
    # device actually did PME work: a non-zero GPU-mesh counter in the timing table
    m = re.search(r"^\s*PME GPU mesh\s+\d+\s+\d+\s+(\d+)\s", text, re.M)
    if not m or int(m.group(1)) <= 0:
        errors.append("production timing table shows no PME GPU mesh calls")
    return errors, {"gpu": s.get("GPU_NAME")}


def _check_summary_matches_body(text):
    """The SUMMARY is a re-emission; every key the body also carries must agree."""
    s = _summary(text)
    body = _body(text)
    errors = []
    compared = 0
    for key, vals in sorted(body.items()):
        if key not in s:
            continue
        compared += 1
        if len(vals) > 1:
            errors.append(f"{key}: body carries conflicting values {sorted(vals)}")
        elif s[key] not in vals:
            errors.append(f"{key}: SUMMARY={s[key]!r} != body {sorted(vals)}")
    if compared < 20:
        errors.append(f"only {compared} keys comparable between body and SUMMARY")
    return errors, {"keys_compared": compared}


def _check_provenance_text(text):
    s = _summary(text)
    errors = []
    if s.get("PDB_SHA256") != "d8f23749da9ec22da2e17bb31c33803e3db6123233cd0404bdc005111196e7a3":
        errors.append(f"PDB_SHA256={s.get('PDB_SHA256')!r} is not the stated 1ycr.pdb digest")
    if s.get("SIF_SHA256") != _SIF_SHA256:
        errors.append(f"SIF_SHA256={s.get('SIF_SHA256')!r} != stated {_SIF_SHA256}")
    return errors, {}


# --- checks against files on disk --------------------------------------------

def _emtol_from_deck(deck=None):
    path = os.path.join(deck or _DECK, "em.mdp")
    m = re.search(r"^emtol\s*=\s*([0-9.eE+-]+)", _read(path), re.M)
    if not m:
        raise ValueError("em.mdp declares no emtol")
    return float(m.group(1))


def _check_deck_digests(text, deck=None):
    deck = deck or _DECK
    errors, seen = [], {}
    for name, digest in re.findall(r"^deck_sha256 (\S+): ([0-9a-f]{64})\s*$",
                                   text, re.M):
        seen[name] = digest
    if sorted(seen) != sorted(_DECK_FILES):
        errors.append(f"evidence deck files {sorted(seen)} != {sorted(_DECK_FILES)}")
    for name in _DECK_FILES:
        path = os.path.join(deck, name)
        if not os.path.isfile(path):
            errors.append(f"committed deck file {name} missing")
        elif name in seen and _sha256(path) != seen[name]:
            errors.append(f"{name}: committed sha256 {_sha256(path)} != "
                          f"evidence {seen[name]} (deck changed since the run)")
    return errors, {"files": sorted(seen)}


def _check_force_field_vs_usda(text, usda=None):
    s = _summary(text)
    usda_text = _read(usda or _USDA)
    errors = []
    # the assumption tags in the usda carry the names; compare case-insensitively
    # on the bare token (usda: "AMBER99SB-ILDN" / "TIP3P"; run: lower-case)
    ff = re.search(r'custom string bio:md:forceField = "([^"]+)"', usda_text)
    wm = re.search(r'custom string bio:md:waterModel = "([^"]+)"', usda_text)
    if not ff or not wm:
        return ["usda lacks bio:md:forceField / bio:md:waterModel"], {}
    if s.get("FORCE_FIELD") != "amber99sb-ildn":
        errors.append(f"FORCE_FIELD={s.get('FORCE_FIELD')!r} != 'amber99sb-ildn'")
    if s.get("WATER_MODEL") != "tip3p":
        errors.append(f"WATER_MODEL={s.get('WATER_MODEL')!r} != 'tip3p'")
    if ff.group(1).lower() != s.get("FORCE_FIELD", "").lower():
        errors.append(f"usda forceField {ff.group(1)!r} != run {s.get('FORCE_FIELD')!r}")
    if wm.group(1).lower() != s.get("WATER_MODEL", "").lower():
        errors.append(f"usda waterModel {wm.group(1)!r} != run {s.get('WATER_MODEL')!r}")
    # the usda must still flag the ff19SB divergence: the run is evidence for
    # amber99sb-ildn, not for the planned ff19SB
    if "DIVERGES from the planned AMBER ff19SB" not in usda_text:
        errors.append("usda lost its 'DIVERGES from the planned AMBER ff19SB' tag")
    return errors, {"usda_ff": ff.group(1), "usda_water": wm.group(1)}


def _check_sif_digest_recorded():
    """The run's SIF digest must equal the one recorded when that sif was built
    and verified (cold rebuild capture) -- a second file, not the job file."""
    errors = []
    found = re.findall(r"^sif_sha256[=:]\s*(\S+)\s*$", _read(_COLD_VERIFY), re.M)
    if not found:
        return ["convert_verify_cold_banyan.txt records no sif_sha256"], {}
    if set(found) != {_SIF_SHA256}:
        errors.append(f"container evidence digests {sorted(set(found))} != "
                      f"stated {_SIF_SHA256}")
    return errors, {"digest": found[0]}


def _check_manifest_p53_md(manifest=None, evidence=None):
    manifest = manifest or _MANIFEST
    evidence = evidence or _EVIDENCE
    errors = []
    entries = {}
    for lineno, line in enumerate(_read(manifest).splitlines(), 1):
        if line.strip():
            obj = json.loads(line)
            entries[obj.get("body_file")] = obj
    for name, (want_sha, want_bytes) in sorted(_MANIFEST_EXPECT.items()):
        path = os.path.join(evidence, name)
        e = entries.get(name)
        if e is None:
            errors.append(f"{name}: no manifest line")
            continue
        if e.get("sha256") != want_sha or e.get("bytes") != want_bytes:
            errors.append(f"{name}: manifest says {e.get('sha256')}/{e.get('bytes')}"
                          f" != stated {want_sha}/{want_bytes}")
        if not os.path.isfile(path):
            errors.append(f"{name}: not on disk")
            continue
        if _sha256(path) != e.get("sha256"):
            errors.append(f"{name}: disk sha256 {_sha256(path)} != manifest")
        if os.path.getsize(path) != e.get("bytes"):
            errors.append(f"{name}: disk bytes {os.path.getsize(path)} != manifest "
                          f"{e.get('bytes')}")
    return errors, {"verified": sorted(_MANIFEST_EXPECT)}


# --- falsification self-test -------------------------------------------------

def _mutations(text):
    """(label, family check fn, mutated text). Each must make its check fail."""
    def sub(old, new, count=1):
        assert old in text, f"selftest anchor missing: {old!r}"
        return text.replace(old, new, count)

    # Replace only inside the SUMMARY (the last occurrence) where one is parsed.
    def sub_summary(old, new):
        head, sep, tail = text.rpartition("--- SUMMARY ---")
        assert old in tail, f"selftest anchor missing in summary: {old!r}"
        return head + sep + tail.replace(old, new, 1)

    return [
        ("charge: IONS_NA 16->13", _check_ion_bookkeeping, sub_summary("IONS_NA=16", "IONS_NA=13")),
        ("atoms: TOTAL_ATOMS off by one", _check_ion_bookkeeping, sub_summary("TOTAL_ATOMS=17563", "TOTAL_ATOMS=17564")),
        ("count: OXT residue moved", _check_system_counts, sub_summary("OXT_ADDED=A109", "OXT_ADDED=A108")),
        ("em: Fmax above emtol", _check_em_converged, sub_summary("EM_MAX_FORCE=9.5286469e+02", "EM_MAX_FORCE=1.5286469e+03")),
        ("thermo: NPT 20 K hot", _check_stage_thermo, sub_summary("NPT_AVG_TEMPERATURE=309.81", "NPT_AVG_TEMPERATURE=329.81")),
        ("thermo: MD density 800", _check_stage_thermo, sub_summary("MD_AVG_DENSITY=1010.04", "MD_AVG_DENSITY=800.04")),
        ("gpu: MD PME on CPU", _check_gpu_execution, sub_summary("MD_PME_ON_GPU=yes", "MD_PME_ON_GPU=no")),
        ("gpu: md.log lost PME line", _check_gpu_execution,
         text.replace("PME tasks will do all aspects on the GPU", "PME tasks will run on the CPU")),
        ("exit: container nonzero", _check_run_completed, sub_summary("CONTAINER_EXIT=0", "CONTAINER_EXIT=1")),
        ("summary edited vs body", _check_summary_matches_body, sub_summary("NVT_AVG_TEMPERATURE=309.698", "NVT_AVG_TEMPERATURE=310.000")),
        ("provenance: sif digest", _check_provenance_text, sub_summary("SIF_SHA256=221d", "SIF_SHA256=221e")),
        ("deck: em.mdp digest flipped", _check_deck_digests, sub("deck_sha256 em.mdp: cb2a", "deck_sha256 em.mdp: cb2b")),
        ("ff: usda disagreement", _check_force_field_vs_usda, sub_summary("FORCE_FIELD=amber99sb-ildn", "FORCE_FIELD=amber99sb")),
    ]


def _check_falsification_selftest(text):
    """Each mutation applied in memory (nothing on disk is touched) must turn its
    family red, and the unmutated text must be green for that same family --
    otherwise a red result proves nothing."""
    errors = []
    killed = 0
    for label, fn, mutated in _mutations(text):
        base_errors, _ = fn(text)
        if base_errors:
            errors.append(f"[{label}] family already red on the real capture: "
                          f"{base_errors[0]}")
            continue
        mut_errors, _ = fn(mutated)
        if mut_errors:
            killed += 1
        else:
            errors.append(f"[{label}] mutation went UNDETECTED")
    return errors, {"mutations_detected": killed}


# --- harness entry point -----------------------------------------------------

def _row(name, fn):
    try:
        errors, detail = fn()
    except Exception as exc:
        errors, detail = [f"{type(exc).__name__}: {exc}"], {}
    return {"check_name": name, "passed": not errors, "errors": errors,
            "detail": detail}


def run() -> list:
    if not os.path.isdir(_EVIDENCE) or not os.path.isfile(_JOB119):
        return []
    try:
        text = _read(_JOB119)
    except Exception as exc:            # unreadable present file -> FAIL row
        return [_row("md_run_readable", lambda: ([f"{type(exc).__name__}: {exc}"], {}))]

    rows = [
        _row("md_run_completed", lambda: _check_run_completed(text)),
        _row("md_system_counts", lambda: _check_system_counts(text)),
        _row("md_ion_bookkeeping", lambda: _check_ion_bookkeeping(text)),
        _row("md_em_converged", lambda: _check_em_converged(text)),
        _row("md_stage_thermo", lambda: _check_stage_thermo(text)),
        _row("md_gpu_execution", lambda: _check_gpu_execution(text)),
        _row("md_summary_matches_body", lambda: _check_summary_matches_body(text)),
        _row("md_provenance", lambda: _check_provenance_text(text)),
    ]
    if os.path.isdir(_DECK):
        rows.append(_row("md_deck_digests", lambda: _check_deck_digests(text)))
    if os.path.isfile(_USDA):
        rows.append(_row("md_force_field_vs_usda",
                         lambda: _check_force_field_vs_usda(text)))
    if os.path.isfile(_COLD_VERIFY):
        rows.append(_row("md_sif_digest_recorded", _check_sif_digest_recorded))
    if os.path.isfile(_MANIFEST):
        rows.append(_row("md_manifest_p53_md", _check_manifest_p53_md))
    rows.append(_row("md_falsification_selftest",
                     lambda: _check_falsification_selftest(text)))
    return rows


if __name__ == "__main__":
    rs = run()
    if not rs:
        print("md-run-evidence: 0 checks (p53_md_banyan_job119.txt not captured)")
        raise SystemExit(0)
    for r in rs:
        print(f"[{'PASS' if r['passed'] else 'FAIL'}] {r['check_name']}")
        for e in r["errors"]:
            print(f"    - {e}")
        if r["detail"]:
            print(f"    detail: {r['detail']}")
    raise SystemExit(0 if all(r["passed"] for r in rs) else 1)
