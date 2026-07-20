"""
Anti-chimera grep-gate.

Statically scans the package LIBRARY code (converters/, builders/, data/, and
the top-level config/init modules -- NOT the tests, whose fixtures legitimately
name these tokens) to enforce the R00 anti-chimera invariants:

  - The v8 ABL root prim literal must never appear.
  - The v8 ABL dataset atom counts (total + ligand) must never appear as
    standalone tokens -- dataset counts belong in per-run test fixtures only.

This is a source-text gate, not a USD read-back, so it runs without pxr.

NOTE: the forbidden tokens are assembled from fragments below so that THIS
file's own source text never contains them verbatim -- otherwise the very gate
that forbids them would trip on itself (and on the repo-level grep gate).
"""

from __future__ import annotations

import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)  # examples/p53_mdm2

# Library code directories/files to scan (tests/ deliberately excluded).
_LIBRARY_DIRS = ["converters", "builders", "data", "composition", "templates", "maboss"]
_LIBRARY_FILES = ["__init__.py", "p53_env.py"]

# Assembled from fragments (see NOTE) -> the ABL root prim literal at runtime.
_FORBIDDEN_LITERALS = ["ABL" + "Complex"]
# v8 ABL dataset counts as standalone tokens (word-boundary) -- must not appear.
_FORBIDDEN_COUNT_RE = re.compile(
    r"\b" + "46" + "76" + r"\b|\b" + "4" + "3" + r"\b")


def _library_py_files() -> list:
    files = []
    for name in _LIBRARY_FILES:
        p = os.path.join(_PKG, name)
        if os.path.isfile(p):
            files.append(p)
    for d in _LIBRARY_DIRS:
        for root, _dirs, fnames in os.walk(os.path.join(_PKG, d)):
            if "__pycache__" in root:
                continue
            for fn in fnames:
                if fn.endswith(".py"):
                    files.append(os.path.join(root, fn))
    return sorted(files)


def scan() -> list:
    """Return a list of violation strings; empty means the gate passes."""
    violations = []
    for path in _library_py_files():
        with open(path, "r") as f:
            for lineno, line in enumerate(f, 1):
                for lit in _FORBIDDEN_LITERALS:
                    if lit in line:
                        violations.append(f"{path}:{lineno}: forbidden literal '{lit}'")
                if _FORBIDDEN_COUNT_RE.search(line):
                    violations.append(
                        f"{path}:{lineno}: forbidden ABL dataset count token "
                        f"-> {line.strip()!r}")
    return violations


def run() -> list:
    """Harness entry point. Returns a list of one result-shaped dict."""
    violations = scan()
    return [{
        "check_name": "anti_chimera_grep_gate",
        "passed": not violations,
        "errors": violations,
        "detail": {"library_files_scanned": len(_library_py_files())},
    }]


if __name__ == "__main__":
    v = scan()
    if v:
        print("ANTI-CHIMERA GATE FAILED:")
        for line in v:
            print("  " + line)
        raise SystemExit(1)
    print(f"anti-chimera gate PASS ({len(_library_py_files())} library files clean)")
