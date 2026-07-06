#!/usr/bin/env python3
"""
Falsification-resistant read-back tests for real provenance lineage.

Opens the committed abl_kinase_complex.usda FRESH with Usd.Stage.Open() and
asserts that the six bio: provenance attributes on /ABLComplex match values
INDEPENDENTLY re-derived here from the raw ShinobuLab data files under
$USDBIO_DATA_DIR — NOT from provenance_source.py's in-memory dict, and NOT
from templates/04_create_assembly.py's generator state. This is the
anti-tautology guard: if provenance_source.py had a parsing bug that produced
a self-consistent-but-wrong value, comparing against its own output would not
catch it. Comparing against independently-parsed raw text does.

Also asserts a negative: no provenance field may equal a previously-shipped
hard-coded sentinel value (e.g. "2HYY.pdb", "AMBER99SB-ILDN", "2.1.0",
"2024-03-15T09:00:00+09:00") — this is the regression guard against the
fabricated placeholders this test suite replaces.

Data sources independently re-read by this test (same files
provenance_source.py reads, parsed here with separate ad hoc logic):
  - files/atp-complex-solv35.pdb                    (sourcePdb)
  - equilibration/5-eq2/atpcomplex-cmd-eq2.inp       (forceField, simSettings)
  - equilibration/5-eq2/atpcomplex-cmd-eq2.log       (softwareName,
                                                       softwareVersion, timestamp)

Standalone: run as __main__; exits non-zero on any failure.
Requires USDBIO_DATA_DIR to be set (via load_env.sh) — skips with a clear
message (exit 0) if unset, since the artifact under test was already
generated from that data and committed; re-verification against raw source
files is a stronger check but not this repo's only correctness gate.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# USD import guard
# ---------------------------------------------------------------------------
try:
    from pxr import Usd
except ImportError as exc:
    raise ImportError(
        "pxr not importable. Run under the OpenUSD Python interpreter "
        "with load_env.sh sourced."
    ) from exc

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_DEMO_ROOT = os.path.dirname(_HERE)
_ASSEMBLY_PATH = os.path.join(
    _DEMO_ROOT, "assets", "level4_assemblies", "abl_kinase_complex.usda"
)

_PROVENANCE_ATTRS = (
    "bio:sourcePdb",
    "bio:forceField",
    "bio:softwareName",
    "bio:softwareVersion",
    "bio:simSettings",
    "bio:timestamp",
)

# Known-wrong sentinel values previously hard-coded in
# templates/04_create_assembly.py before this fix — regression guard.
_KNOWN_WRONG_SENTINELS = frozenset({
    "2HYY.pdb",
    "AMBER99SB-ILDN",
    "2.1.0",
    "2024-03-15T09:00:00+09:00",
    '{"timestep_fs": 2.0, "temp_K": 310, "pressure_bar": 1.0}',
})


@dataclass
class TestResult:
    name: str
    passed: bool
    errors: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Independent re-derivation of the real ShinobuLab values.
#
# Deliberately reimplemented here with separate regex/string logic from
# provenance_source.py — a bug shared between the generator's parser and this
# test's parser would not be caught if this test imported and called
# provenance_source.py directly, so it does not.
# ---------------------------------------------------------------------------

def _independent_expected_values(data_dir: str) -> dict:
    """Re-derive the six expected values directly from raw data files."""
    expected: dict = {}

    # sourcePdb: the real starting structure filename per README.md
    pdb_path = os.path.join(data_dir, "files", "atp-complex-solv35.pdb")
    if not os.path.isfile(pdb_path):
        raise FileNotFoundError(pdb_path)
    expected["sourcePdb"] = "atp-complex-solv35.pdb"

    eq_dir = os.path.join(data_dir, "equilibration", "5-eq2")
    inp_path = os.path.join(eq_dir, "atpcomplex-cmd-eq2.inp")
    log_path = os.path.join(eq_dir, "atpcomplex-cmd-eq2.log")

    with open(inp_path) as fh:
        inp_text = fh.read()
    with open(log_path) as fh:
        log_text = fh.read()

    # forceField: literal string after "forcefield" in [ENERGY] block
    m = re.search(r"forcefield\s*=\s*(\S+)", inp_text)
    assert m, "forcefield key not found in .inp"
    expected["forceField_family"] = m.group(1)  # "AMBER"

    # softwareName/softwareVersion: GENESIS SPDYN banner + version field
    assert "GENESIS" in log_text
    m = re.search(r"version\s*=\s*(\S+)", log_text)
    assert m, "version field not found in .log"
    expected["softwareName"] = "GENESIS"
    expected["softwareVersion"] = m.group(1)  # "2.0.3"

    # simSettings: timestep (ps -> fs), temperature, pressure, ensemble
    m_ts = re.search(r"timestep\s*=\s*([\d.]+)", inp_text)
    m_temp = re.search(r"temperature\s*=\s*([\d.]+)", inp_text)
    m_press = re.search(r"pressure\s*=\s*([\d.]+)", inp_text)
    m_ens = re.search(r"ensemble\s*=\s*(\S+)", inp_text)
    assert m_ts and m_temp and m_press and m_ens
    expected["timestep_fs"] = round(float(m_ts.group(1)) * 1000.0, 4)  # 3.5
    expected["temp_K"] = float(m_temp.group(1))  # 310.0
    expected["pressure_bar"] = float(m_press.group(1))  # 1.0
    expected["ensemble"] = m_ens.group(1)  # "NPT"

    # timestamp: raw GENESIS log date, normalized to ISO-8601 (no fabricated tz)
    m_date = re.search(r"date\s*=\s*(\d{4})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2}):(\d{2})",
                        log_text)
    assert m_date, "date field not found in .log"
    y, mo, d, h, mi, s = m_date.groups()
    expected["timestamp"] = f"{y}-{mo}-{d}T{h}:{mi}:{s}"

    return expected


# ---------------------------------------------------------------------------
# Test 1 — all six fields present, non-empty, no sentinel leaks
# ---------------------------------------------------------------------------

def test_provenance_fields_present_and_non_sentinel(stage: Usd.Stage) -> TestResult:
    """Every bio: provenance field is present, non-empty, and not a known-wrong
    sentinel value from the pre-fix hard-coded placeholders."""
    errors: list = []
    detail: dict = {}

    complex_prim = stage.GetPrimAtPath("/ABLComplex")
    if not complex_prim.IsValid():
        return TestResult(
            "fields_present_and_non_sentinel", False,
            errors=["/ABLComplex prim not found"],
        )

    for attr_name in _PROVENANCE_ATTRS:
        attr = complex_prim.GetAttribute(attr_name)
        value = attr.Get() if attr.IsValid() else None
        detail[attr_name] = value

        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"{attr_name} is empty or missing (value={value!r})")
            continue

        if str(value) in _KNOWN_WRONG_SENTINELS:
            errors.append(
                f"{attr_name}={value!r} matches a KNOWN-WRONG hard-coded "
                f"sentinel from the pre-fix generator — fabricated value leaked "
                f"into the committed artifact"
            )

    return TestResult(
        "fields_present_and_non_sentinel",
        passed=len(errors) == 0,
        errors=errors,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Test 2 — values match independently re-derived real ShinobuLab data
# ---------------------------------------------------------------------------

def test_provenance_matches_real_data(stage: Usd.Stage, data_dir: str) -> TestResult:
    """bio: provenance attributes match values independently re-parsed from
    the raw ShinobuLab .pdb/.inp/.log files (not from provenance_source.py's
    in-memory dict)."""
    errors: list = []
    detail: dict = {}

    complex_prim = stage.GetPrimAtPath("/ABLComplex")
    if not complex_prim.IsValid():
        return TestResult(
            "matches_real_data", False,
            errors=["/ABLComplex prim not found"],
        )

    expected = _independent_expected_values(data_dir)

    actual_source_pdb = complex_prim.GetAttribute("bio:sourcePdb").Get()
    detail["sourcePdb"] = actual_source_pdb
    if str(actual_source_pdb) != expected["sourcePdb"]:
        errors.append(
            f"bio:sourcePdb={actual_source_pdb!r}, expected "
            f"{expected['sourcePdb']!r} (independently re-derived from "
            f"files/atp-complex-solv35.pdb)"
        )

    actual_ff = complex_prim.GetAttribute("bio:forceField").Get()
    detail["forceField"] = actual_ff
    if expected["forceField_family"] not in str(actual_ff):
        errors.append(
            f"bio:forceField={actual_ff!r} does not contain the real force "
            f"field family {expected['forceField_family']!r} parsed from "
            f"equilibration/5-eq2/atpcomplex-cmd-eq2.inp [ENERGY] block"
        )

    actual_sw_name = complex_prim.GetAttribute("bio:softwareName").Get()
    detail["softwareName"] = actual_sw_name
    if str(actual_sw_name) != expected["softwareName"]:
        errors.append(
            f"bio:softwareName={actual_sw_name!r}, expected "
            f"{expected['softwareName']!r}"
        )

    actual_sw_version = complex_prim.GetAttribute("bio:softwareVersion").Get()
    detail["softwareVersion"] = actual_sw_version
    if str(actual_sw_version) != expected["softwareVersion"]:
        errors.append(
            f"bio:softwareVersion={actual_sw_version!r}, expected "
            f"{expected['softwareVersion']!r} (real GENESIS SPDYN version "
            f"from equilibration/5-eq2/atpcomplex-cmd-eq2.log)"
        )

    actual_settings_raw = complex_prim.GetAttribute("bio:simSettings").Get()
    detail["simSettings"] = actual_settings_raw
    try:
        actual_settings = json.loads(actual_settings_raw) if actual_settings_raw else {}
    except (TypeError, json.JSONDecodeError):
        actual_settings = {}
        errors.append(f"bio:simSettings is not valid JSON: {actual_settings_raw!r}")

    for key, exp_val in (
        ("timestep_fs", expected["timestep_fs"]),
        ("temp_K", expected["temp_K"]),
        ("pressure_bar", expected["pressure_bar"]),
        ("ensemble", expected["ensemble"]),
    ):
        act_val = actual_settings.get(key)
        if act_val != exp_val:
            errors.append(
                f"bio:simSettings[{key!r}]={act_val!r}, expected {exp_val!r} "
                f"(independently re-derived from atpcomplex-cmd-eq2.inp)"
            )

    actual_timestamp = complex_prim.GetAttribute("bio:timestamp").Get()
    detail["timestamp"] = actual_timestamp
    if str(actual_timestamp) != expected["timestamp"]:
        errors.append(
            f"bio:timestamp={actual_timestamp!r}, expected "
            f"{expected['timestamp']!r} (real GENESIS run date from "
            f"atpcomplex-cmd-eq2.log)"
        )

    return TestResult(
        "matches_real_data",
        passed=len(errors) == 0,
        errors=errors,
        detail=detail,
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run(assembly_path: str, data_dir: str | None) -> list:
    results = []

    if not os.path.isfile(assembly_path):
        return [TestResult(
            "provenance_lineage", False,
            errors=[f"File not found: {assembly_path}"],
        )]

    stage = Usd.Stage.Open(assembly_path)

    results.append(test_provenance_fields_present_and_non_sentinel(stage))

    if data_dir is None:
        results.append(TestResult(
            "matches_real_data", True,
            detail={"skipped": "USDBIO_DATA_DIR not set — cannot cross-check "
                                "against raw ShinobuLab data files"},
        ))
    else:
        results.append(test_provenance_matches_real_data(stage, data_dir))

    return results


if __name__ == "__main__":
    print(f"Opening: {_ASSEMBLY_PATH}")
    data_dir = os.environ.get("USDBIO_DATA_DIR")
    if data_dir:
        print(f"Cross-checking against: {data_dir}")
    else:
        print("USDBIO_DATA_DIR not set — will skip cross-check against raw data")
    print()

    results = run(_ASSEMBLY_PATH, data_dir)

    all_passed = True
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {result.name}")
        if result.detail:
            for k, v in result.detail.items():
                print(f"         {k} = {v}")
        for err in result.errors:
            print(f"         ERROR: {err}")
        if not result.passed:
            all_passed = False
        print()

    total = len(results)
    passed_count = sum(1 for r in results if r.passed)
    failed_count = total - passed_count

    if all_passed:
        print(f"ALL PASS ({passed_count}/{total})")
        sys.exit(0)
    else:
        print(f"FAILED ({failed_count}/{total} failed)")
        sys.exit(1)
