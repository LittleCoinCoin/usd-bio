#!/usr/bin/env python3
"""
run_tests.py — 4-layer test harness CLI entry point.

Usage
-----
    python3 examples/foundation_demo_v8/tests/run_tests.py [--layer LAYER]

    --layer {compliance,domain,readback,golden}
        Run only the specified layer. Default: run all layers.

Exit codes
----------
    0   All active layers passed
    1   One or more failures

Environment
-----------
    Must be sourced first (or env pre-loaded):
        . ./load_env.sh
    Sets PYTHONPATH to the OpenUSD build; required for pxr imports.

    USDBIO_USDCHECKER  — override path to usdchecker binary (optional)
    USDBIO_DATA_DIR    — path to ShinobuLab data (used by scripts; not
                         required by this test runner directly)

Layers
------
    compliance — Layer 1: usdchecker on all 6 committed .usda files
    domain     — Layer 2: biological invariant validators (bio:element,
                           inherit chain, representation variants)
    readback   — Layer 3: programmatic USD composition read-back assertions
                           (atom composition, variant cascade, clip positions)
    golden     — Layer 4: fixture-based key-attribute diffing
"""

from __future__ import annotations

import argparse
import os
import sys
import time

# ---------------------------------------------------------------------------
# Path setup: make sure sibling test modules and the data package are importable
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_DEMO_ROOT = os.path.dirname(_HERE)
_OUTPUT_DIR = os.path.join(_DEMO_ROOT, "output")
_FIXTURE_DIR = os.path.join(_HERE, "fixtures")

if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if _DEMO_ROOT not in sys.path:
    sys.path.insert(0, _DEMO_ROOT)


# ---------------------------------------------------------------------------
# Public API (importable for testing the runner itself)
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments. Returns a Namespace with .layer attribute."""
    parser = argparse.ArgumentParser(
        prog="run_tests.py",
        description=(
            "usd-bio 4-layer test harness. "
            "Run under the OpenUSD Python interpreter with load_env.sh sourced."
        ),
    )
    parser.add_argument(
        "--layer",
        choices=["compliance", "domain", "readback", "golden"],
        default=None,
        metavar="LAYER",
        help=(
            "Layer to run: compliance | domain | readback | golden. "
            "Default: run all layers."
        ),
    )
    return parser.parse_args(argv)


def _fmt_passed(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def _run_compliance(output_dir: str) -> tuple[bool, list[dict]]:
    """Run layer 1: usdchecker compliance on all .usda artifacts."""
    import layer1_compliance
    results = layer1_compliance.run(output_dir=output_dir)
    rows = []
    for r in results:
        rows.append({
            "layer": "compliance",
            "name": os.path.basename(r.path),
            "passed": r.passed,
            "notes": "; ".join(r.errors[:2]) if r.errors else "",
        })
    all_passed = all(r.passed for r in results)
    return all_passed, rows


def _run_domain(output_dir: str) -> tuple[bool, list[dict]]:
    """Run layer 2: biological domain invariants on all .usda artifacts."""
    import glob
    import layer2_domain
    paths = sorted(glob.glob(os.path.join(output_dir, "**", "*.usda"), recursive=True))
    results = layer2_domain.run(paths)
    rows = []
    for r in results:
        name = os.path.basename(r.path)
        notes_parts = []
        for check in r.checks:
            if not check["passed"]:
                notes_parts.extend(check.get("errors", [])[:1])
        if r.findings:
            notes_parts.extend([f"FINDING: {f[:60]}" for f in r.findings[:1]])
        if r.deviations:
            notes_parts.extend([f"DEV: {d[:40]}" for d in r.deviations[:1]])
        rows.append({
            "layer": "domain",
            "name": name,
            "passed": r.passed,
            "notes": "; ".join(notes_parts)[:120] if notes_parts else "",
        })
    all_passed = all(r.passed for r in results)
    return all_passed, rows


def _run_readback(output_dir: str) -> tuple[bool, list[dict]]:
    """Run layer 3: programmatic USD read-back assertions."""
    import layer3_readback
    results = layer3_readback.run(output_dir=output_dir)
    rows = []
    for r in results:
        notes = "; ".join(r.errors[:2]) if r.errors else ""
        if r.findings:
            notes = (notes + " | " if notes else "") + "; ".join(r.findings[:1])
        rows.append({
            "layer": "readback",
            "name": r.check_name,
            "passed": r.passed,
            "notes": notes[:120],
        })
    all_passed = all(r.passed for r in results)
    return all_passed, rows


def _run_golden(output_dir: str, fixture_dir: str) -> tuple[bool, list[dict]]:
    """Run layer 4: golden fixture comparisons."""
    import layer4_golden
    results = layer4_golden.run(output_dir=output_dir, fixture_dir=fixture_dir)
    rows = []
    for r in results:
        notes_parts = [e[:60] for e in r.errors[:2]]
        if r.findings:
            notes_parts.extend([f"FINDING: {f[:50]}" for f in r.findings[:1]])
        rows.append({
            "layer": "golden",
            "name": r.check_name,
            "passed": r.passed,
            "notes": "; ".join(notes_parts)[:120] if notes_parts else "",
        })
    all_passed = all(r.passed for r in results)
    return all_passed, rows


def run_all_layers(
    layer: str | None,
    output_dir: str,
    fixture_dir: str,
) -> tuple[bool, list[dict]]:
    """
    Dispatch to one or all layers. Returns (all_passed, rows) where rows
    is a flat list of result dicts for the summary table.

    Parameters
    ----------
    layer : str or None
        One of 'compliance', 'domain', 'readback', 'golden', or None for all.
    output_dir : str
        Absolute path to the output/ directory.
    fixture_dir : str
        Absolute path to the tests/fixtures/ directory.

    Returns
    -------
    (all_passed: bool, rows: list of dict)
    """
    dispatch = {
        "compliance": lambda: _run_compliance(output_dir),
        "domain": lambda: _run_domain(output_dir),
        "readback": lambda: _run_readback(output_dir),
        "golden": lambda: _run_golden(output_dir, fixture_dir),
    }

    layers_to_run = [layer] if layer else list(dispatch.keys())
    all_passed = True
    all_rows: list[dict] = []

    for lname in layers_to_run:
        t0 = time.monotonic()
        try:
            layer_passed, rows = dispatch[lname]()
        except Exception as exc:
            layer_passed = False
            rows = [{
                "layer": lname,
                "name": f"EXCEPTION in {lname}",
                "passed": False,
                "notes": str(exc)[:120],
            }]
        elapsed = time.monotonic() - t0
        for row in rows:
            row["elapsed_s"] = f"{elapsed:.1f}s" if len(rows) == 1 else ""
        all_rows.extend(rows)
        if not layer_passed:
            all_passed = False

    return all_passed, all_rows


def _print_summary(rows: list[dict], all_passed: bool) -> None:
    """Print a formatted summary table to stdout."""
    # Column widths
    col_layer = 12
    col_name = 40
    col_status = 8
    col_notes = 60

    sep = (
        "+" + "-" * col_layer
        + "+" + "-" * col_name
        + "+" + "-" * col_status
        + "+" + "-" * col_notes
        + "+"
    )
    header = (
        "|" + "Layer".center(col_layer)
        + "|" + "Check".center(col_name)
        + "|" + "Status".center(col_status)
        + "|" + "Notes".center(col_notes)
        + "|"
    )

    print()
    print(sep)
    print(header)
    print(sep)

    for row in rows:
        status = _fmt_passed(row["passed"])
        layer_str = row.get("layer", "")[:col_layer - 1].ljust(col_layer - 1)
        name_str = row.get("name", "")[:col_name - 1].ljust(col_name - 1)
        notes_str = row.get("notes", "")[:col_notes - 1].ljust(col_notes - 1)
        elapsed = row.get("elapsed_s", "")
        status_str = (status + (f" {elapsed}" if elapsed else "")).center(col_status - 1).ljust(col_status - 1)
        print(f"| {layer_str}| {name_str}| {status_str}| {notes_str}|")

    print(sep)
    total = len(rows)
    passed_count = sum(1 for r in rows if r["passed"])
    failed_count = total - passed_count
    overall = "ALL PASS" if all_passed else f"FAILED ({failed_count}/{total})"
    print(f"  Result: {overall}  ({passed_count}/{total} checks passed)")
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """
    Main CLI entry point.

    Returns
    -------
    int
        0 on all-pass, 1 on any failure.
    """
    args = parse_args(argv)

    # Sanity-check that pxr is importable before dispatching
    try:
        from pxr import Usd  # noqa: F401
    except ImportError:
        print(
            "ERROR: pxr not importable.\n"
            "Run under the OpenUSD Python interpreter with load_env.sh sourced:\n"
            "  . ./load_env.sh\n"
            "  /Users/hacker/.local/share/uv/python/"
            "cpython-3.11.14-macos-aarch64-none/bin/python3 "
            "examples/foundation_demo_v8/tests/run_tests.py",
            file=sys.stderr,
        )
        return 1

    if not os.path.isdir(_OUTPUT_DIR):
        print(
            f"ERROR: output directory not found: {_OUTPUT_DIR}\n"
            "Run from the repo root.",
            file=sys.stderr,
        )
        return 1

    if not os.path.isdir(_FIXTURE_DIR):
        print(
            f"ERROR: fixture directory not found: {_FIXTURE_DIR}\n"
            "Expected: examples/foundation_demo_v8/tests/fixtures/",
            file=sys.stderr,
        )
        return 1

    layer_label = args.layer or "all"
    print(f"usd-bio test harness — layer={layer_label}")
    print(f"  output_dir : {_OUTPUT_DIR}")
    print(f"  fixture_dir: {_FIXTURE_DIR}")

    all_passed, rows = run_all_layers(
        layer=args.layer,
        output_dir=_OUTPUT_DIR,
        fixture_dir=_FIXTURE_DIR,
    )

    _print_summary(rows, all_passed)

    # Print any findings to stderr so they are not lost even on pass
    for row in rows:
        if row.get("notes") and "FINDING" in row.get("notes", ""):
            print(f"FINDING [{row['layer']}] {row['name']}: {row['notes']}", file=sys.stderr)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
