#!/usr/bin/env python3
"""
patch_stage_metadata.py — idempotent metersPerUnit + upAxis + defaultPrim patcher.

WHY THIS TOOL EXISTS
--------------------
Two v8 artifacts (trajectory_demo.usda, trajectory_clip.usda) are produced by
converters/xtc_to_clips.py which imports mdtraj.  mdtraj is absent in the uv
CPython 3.11 interpreter that carries the OpenUSD pxr build, so those files
cannot be regenerated from source under the correct interpreter.

This script opens each such file, checks whether metersPerUnit, upAxis, and
defaultPrim are already set, and writes them if missing — then saves.  Running
it twice is safe (idempotency contract: second run is a no-op).

USAGE
-----
    # From repo root, after loading the environment:
    . ./load_env.sh
    /path/to/uv-python3 examples/foundation_demo_v8/tools/patch_stage_metadata.py

    # Or target specific files with optional defaultPrim overrides:
    /path/to/uv-python3 examples/foundation_demo_v8/tools/patch_stage_metadata.py \
        path/to/trajectory_demo.usda path/to/clips/trajectory_clip.usda

DESIGN CONTRACT
---------------
- metersPerUnit = 1e-10  (Ångström: 1 Å = 1e-10 m; matches all other v8 generators)
- upAxis        = "Y"    (USD default; explicit for usdchecker compliance)
- defaultPrim   = first root-level child prim name if absent (usdchecker requires it)
- Only modifies files that are missing one or more values.
- Prints a per-file verdict: PATCHED or ALREADY-SET (no-op).
"""

from __future__ import annotations

import os
import sys

# ---------------------------------------------------------------------------
# Interpreter guard — must run under uv CPython 3.11 with PYTHONPATH set.
# ---------------------------------------------------------------------------
try:
    from pxr import Usd, UsdGeom
except ImportError as exc:
    raise ImportError(
        "pxr not importable. Run under the OpenUSD Python interpreter with "
        "load_env.sh sourced."
    ) from exc

# Canonical values used by all v8 generators.
METERS_PER_UNIT: float = 1e-10   # Ångström
UP_AXIS: str = UsdGeom.Tokens.y  # "Y"


def patch_stage(path: str, default_prim: str | None = None) -> dict:
    """
    Open the stage at *path*, set metersPerUnit, upAxis, and defaultPrim if
    absent or invalid, then save.

    *default_prim*: if provided, use this prim name as the defaultPrim when
    one is missing.  If None, auto-detect from the first root-level prim.

    Returns a dict with keys:
        path                : str
        patched             : bool   (True if any change was written)
        mpu_was_set         : bool
        upaxis_was_set      : bool
        default_prim_was_set: bool
        error               : str | None
    """
    result: dict = {
        "path": path,
        "patched": False,
        "mpu_was_set": False,
        "upaxis_was_set": False,
        "default_prim_was_set": False,
        "error": None,
    }

    if not os.path.isfile(path):
        result["error"] = f"File not found: {path}"
        return result

    try:
        stage = Usd.Stage.Open(path)
    except Exception as exc:
        result["error"] = f"Stage open failed: {exc}"
        return result

    changed = False

    # --- metersPerUnit -------------------------------------------------------
    mpu = UsdGeom.GetStageMetersPerUnit(stage)
    # 0.0 means not set (USD returns 0.01 as the documented default when absent;
    # treat any value != our canonical as "check needed").
    if mpu != METERS_PER_UNIT:
        UsdGeom.SetStageMetersPerUnit(stage, METERS_PER_UNIT)
        result["mpu_was_set"] = True
        changed = True

    # --- upAxis --------------------------------------------------------------
    current_up = UsdGeom.GetStageUpAxis(stage)
    if current_up != UP_AXIS:
        UsdGeom.SetStageUpAxis(stage, UP_AXIS)
        result["upaxis_was_set"] = True
        changed = True

    # --- defaultPrim ---------------------------------------------------------
    dp = stage.GetDefaultPrim()
    if not dp.IsValid():
        # Determine what to use as defaultPrim
        if default_prim is None:
            # Auto-detect: use first direct child of pseudo-root
            root = stage.GetPseudoRoot()
            children = root.GetChildren()
            if children:
                default_prim = children[0].GetName()
        if default_prim:
            prim = stage.GetPrimAtPath("/" + default_prim)
            if prim.IsValid():
                stage.SetDefaultPrim(prim)
                result["default_prim_was_set"] = True
                changed = True

    if changed:
        stage.Save()
        result["patched"] = True

    return result


def main(paths: list[str] | None = None) -> int:
    """
    Patch each USD file in *paths* (or the default trajectory artifact list if
    *paths* is None / empty).

    Returns 0 on success, 1 if any file had an error.
    """
    _here = os.path.dirname(os.path.abspath(__file__))
    _output = os.path.join(os.path.dirname(_here), "output")

    # Default: patch the two trajectory artifacts.
    # trajectory_clip.usda needs defaultPrim="ABLComplex" (its root prim).
    # trajectory_demo.usda already has defaultPrim="World" but may lack metersPerUnit.
    default_targets: list[tuple[str, str | None]] = [
        (os.path.join(_output, "trajectory_demo.usda"), None),
        (os.path.join(_output, "clips", "trajectory_clip.usda"), "ABLComplex"),
    ]

    if paths:
        # When explicit paths are given, auto-detect defaultPrim for each.
        targets = [(p, None) for p in paths]
    else:
        targets = default_targets

    exit_code = 0
    for p, dp_hint in targets:
        r = patch_stage(p, default_prim=dp_hint)
        if r["error"]:
            print(f"  ERROR  {p}: {r['error']}")
            exit_code = 1
        elif r["patched"]:
            details = []
            if r["mpu_was_set"]:
                details.append(f"metersPerUnit={METERS_PER_UNIT}")
            if r["upaxis_was_set"]:
                details.append(f"upAxis={UP_AXIS}")
            if r["default_prim_was_set"]:
                details.append(f"defaultPrim={dp_hint or '(auto)'}")
            print(f"  PATCHED {p}: set {', '.join(details)}")
        else:
            print(f"  ALREADY-SET {p}: no changes needed (idempotent)")

    return exit_code


if __name__ == "__main__":
    # Allow explicit file paths from argv, else use defaults.
    argv_paths = sys.argv[1:] if len(sys.argv) > 1 else []
    sys.exit(main(argv_paths or None))
