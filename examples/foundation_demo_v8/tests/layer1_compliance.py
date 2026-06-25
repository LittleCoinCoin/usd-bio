"""
Layer 1 — usdchecker compliance gate.

Shells out to the USD build's usdchecker binary for each committed .usda
artifact and collects pass/fail results. Lowest-overhead gate: if a file
fails usdchecker, none of the higher layers are meaningful.

usdchecker binary: prefer /Users/hacker/Documents/bin/OpenUSD/bin/usdchecker
(matches the linked libraries); override via USDBIO_USDCHECKER env var.
"""

from __future__ import annotations

import glob
import os
import subprocess
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

class ComplianceResult(NamedTuple):
    """Result of running usdchecker on a single .usda file."""
    path: str
    passed: bool
    errors: list[str]


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------

_DEFAULT_USDCHECKER = "/Users/hacker/Documents/bin/OpenUSD/bin/usdchecker"


def _find_usdchecker() -> str:
    """Return the usdchecker binary path; configurable via USDBIO_USDCHECKER."""
    override = os.environ.get("USDBIO_USDCHECKER", "")
    if override and os.path.isfile(override):
        return override
    if os.path.isfile(_DEFAULT_USDCHECKER):
        return _DEFAULT_USDCHECKER
    # Fall back to whatever is on PATH
    import shutil
    found = shutil.which("usdchecker")
    if found:
        return found
    raise FileNotFoundError(
        "usdchecker not found. Set USDBIO_USDCHECKER env var or install OpenUSD."
    )


def _check_one(path: str, usdchecker: str) -> ComplianceResult:
    """Run usdchecker on a single file and return a ComplianceResult."""
    try:
        result = subprocess.run(
            [usdchecker, path],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return ComplianceResult(
            path=path,
            passed=False,
            errors=["usdchecker timed out after 60s"],
        )
    except FileNotFoundError as exc:
        return ComplianceResult(
            path=path,
            passed=False,
            errors=[f"usdchecker binary not found: {exc}"],
        )

    output = result.stdout + result.stderr
    # Collect lines containing "Error:" (usdchecker error format)
    error_lines = [
        line.strip()
        for line in output.splitlines()
        if "Error:" in line or "error:" in line.lower()
    ]
    # usdchecker exits 0 on success; non-zero or any Error line = failure
    passed = result.returncode == 0 and not error_lines
    return ComplianceResult(path=path, passed=passed, errors=error_lines)


def _discover_usda_paths(output_dir: str) -> list[str]:
    """Discover all .usda artifacts under output_dir (recursive)."""
    pattern = os.path.join(output_dir, "**", "*.usda")
    paths = sorted(glob.glob(pattern, recursive=True))
    return paths


def run(usda_paths: list[str] | None = None, output_dir: str | None = None) -> list[ComplianceResult]:
    """
    Run usdchecker on each path in usda_paths (or discover from output_dir).

    Parameters
    ----------
    usda_paths : list of str, optional
        Explicit list of .usda file paths to check. If None, output_dir is used.
    output_dir : str, optional
        Directory to glob for *.usda files. Used when usda_paths is None.

    Returns
    -------
    list of ComplianceResult
        One result per file, ordered by path.
    """
    if usda_paths is None:
        if output_dir is None:
            raise ValueError("Either usda_paths or output_dir must be provided.")
        usda_paths = _discover_usda_paths(output_dir)

    usdchecker = _find_usdchecker()
    results = []
    for path in usda_paths:
        if not os.path.isfile(path):
            results.append(ComplianceResult(
                path=path,
                passed=False,
                errors=[f"File not found: {path}"],
            ))
        else:
            results.append(_check_one(path, usdchecker))
    return results
