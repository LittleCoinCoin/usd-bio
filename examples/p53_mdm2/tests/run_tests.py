#!/usr/bin/env python3
"""
run_tests.py -- read-back + anti-chimera test harness for the 1YCR topology.

Usage (from the repo root, OpenUSD env sourced):
    . ./load_env.sh
    PYTHONPATH="$PYTHONPATH:$(pwd)/examples" \
        /path/to/forOUSD/python3 examples/p53_mdm2/tests/run_tests.py

Layers (mirrors the v8 4-layer ladder; rebuilt for 1YCR topology-only):
    compliance   -- usdchecker on the committed topology .usda
    domain       -- biological invariants (bio:element, inherits, variants)
    readback     -- fresh-open assertions vs. INDEPENDENT 1YCR re-derivation
    anti-chimera -- static grep-gate for the ABL root literal / dataset counts

Exit code: 0 all pass, 1 any failure.
"""

from __future__ import annotations

import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_PKG_PARENT = os.path.dirname(_PKG)  # examples/
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from p53_mdm2 import p53_env

STAGE_PATH = os.path.join(p53_env.output_dir(), "p53_mdm2_topology.usda")
PDB_PATH = p53_env.get_structure_path("1ycr.pdb")

_DEFAULT_USDCHECKER = "/Users/hacker/Documents/bin/OpenUSD/bin/usdchecker"


def _run_compliance() -> list:
    checker = os.environ.get("USDBIO_USDCHECKER", "") or _DEFAULT_USDCHECKER
    if not os.path.isfile(checker):
        import shutil
        checker = shutil.which("usdchecker") or ""
    if not checker:
        return [{"check_name": "usdchecker(missing)", "passed": False,
                 "errors": ["usdchecker binary not found"]}]
    try:
        res = subprocess.run([checker, "--skipVariants", STAGE_PATH],
                             capture_output=True, text=True, timeout=120)
    except Exception as exc:  # pragma: no cover
        return [{"check_name": "usdchecker", "passed": False, "errors": [str(exc)]}]
    out = res.stdout + res.stderr
    errs = [ln.strip() for ln in out.splitlines() if "error" in ln.lower()]
    passed = res.returncode == 0 and not errs
    return [{"check_name": "usdchecker", "passed": passed, "errors": errs}]


def _rows_from(layer, results):
    rows = []
    for r in results:
        if isinstance(r, dict):
            name, passed, errors = r["check_name"], r["passed"], r.get("errors", [])
        else:
            name, passed, errors = r.check_name, r.passed, r.errors
        rows.append({"layer": layer, "name": name, "passed": passed,
                     "notes": "; ".join(errors[:2])[:110]})
    return rows


def main() -> int:
    all_rows = []

    all_rows += _rows_from("compliance", _run_compliance())

    import layer2_domain
    all_rows += _rows_from("domain", layer2_domain.run(STAGE_PATH))

    import layer3_readback
    all_rows += _rows_from("readback", layer3_readback.run(STAGE_PATH, PDB_PATH))

    import test_dg_correlation
    all_rows += _rows_from("unit-correlation", test_dg_correlation.run())

    import test_ddg_readback
    all_rows += _rows_from("readback-ddg", test_ddg_readback.run())

    import test_md_setup_readback
    all_rows += _rows_from("readback-md", test_md_setup_readback.run())

    import test_anti_chimera
    all_rows += _rows_from("anti-chimera", test_anti_chimera.run())

    # summary table
    print(f"\np53_mdm2 topology test harness")
    print(f"  stage: {STAGE_PATH}")
    print(f"  pdb:   {PDB_PATH}\n")
    width = max(len(r["name"]) for r in all_rows) + 2
    for r in all_rows:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['layer']:<12} {r['name']:<{width}} {r['notes']}")
    passed = sum(1 for r in all_rows if r["passed"])
    total = len(all_rows)
    ok = passed == total
    print(f"\n  Result: {'ALL PASS' if ok else 'FAILED'} ({passed}/{total} checks)\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
