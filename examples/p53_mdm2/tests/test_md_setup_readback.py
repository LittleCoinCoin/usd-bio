"""
P1b Step 1 -- MD-setup-parameter (``bio:md:``) read-back test.

Falsification-resistant (R00 anti-tautology): opens the committed
``p53_mdm2_md_setup.usda`` FRESH and reconstructs the parameter manifest, then
asserts it against INDEPENDENTLY-stated sources, never against the generator's
in-memory state:

  1. ``templates/fixtures/md_setup_reference.json`` -- a hand-transcribed R01
     manifest maintained SEPARATELY from ``md_parameters.DEFAULT_*`` (the two
     transcriptions must agree; a generator typo diverges from the fixture).
  2. Test-stated R01 quotations (``ANCHOR_*`` below) for a handful of
     load-bearing physical values -- a third, in-test anchor so a shared error
     in fixture + generator cannot pass silently.
  3. A honesty guard on the fixture (must self-declare as NOT generator output).

It additionally verifies the PI Q-003 directive (ionConcentration &
protonationState ARE in CORE), the units + per-field source tags, that CORE is
authored completely with no drift, and that the Protocol layer composed over the
Biology topology (departmental layering works -- atoms still resolve).

Error-model: every ``[assumption: ...]`` value must be tagged as such (never
dressed up as an R01-sourced value), and vice-versa.
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
_PKG = os.path.dirname(_HERE)              # examples/p53_mdm2
_PKG_PARENT = os.path.dirname(_PKG)        # examples/
for _p in (_HERE, _PKG_PARENT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from p53_mdm2 import p53_env
from p53_mdm2.templates.md_parameters import (
    MD_NS, MD_SETUP_PRIM_NAME, MD_SETUP_PRIM_TYPE,
    CORE_FIELDS, OPTIONAL_FIELDS, PI_PROMOTED_CORE, default_output_path,
)

# --- test-stated R01 anchors (third independent oracle; NOT from the generator) ---
# Transcribed here from R01's core table so a shared fixture+generator error trips.
ANCHOR_CORE = {
    "timestep": 0.0035,      # R01: 3.5 fs, HMR-enabled
    "temperature": 310.0,    # R01: temperature=310.0 K
    "cutoff": 8.0,           # R01: cutoffdist=8.0 Angstrom
    "nSteps": 600000,        # R01: 600000 steps per production run
    "engine": "GENESIS",     # R01: ShinobuLab spdyn/GENESIS
    "electrostatics": "PME", # R01: electrostatic=PME
}

_FLOAT_TOL = 1e-9
_CORE_SUFFIXES = {s for s, _t, _u in CORE_FIELDS}
_OPTIONAL_SUFFIXES = {s for s, _t, _u in OPTIONAL_FIELDS}


@dataclass
class ReadbackResult:
    check_name: str
    passed: bool
    errors: list = field(default_factory=list)
    detail: dict = field(default_factory=dict)


def _fixture_path() -> str:
    return os.path.join(_PKG, "templates", "fixtures", "md_setup_reference.json")


def _values_equal(recorded, expected) -> bool:
    if isinstance(expected, bool) or isinstance(recorded, bool):
        return bool(recorded) == bool(expected)
    if isinstance(expected, (int, float)) and isinstance(recorded, (int, float)):
        return abs(float(recorded) - float(expected)) <= _FLOAT_TOL
    return str(recorded) == str(expected)


def assert_fixture_honestly_tagged(fixture_path) -> ReadbackResult:
    """The fixture must self-declare that it is NOT generator output."""
    errors, detail = [], {}
    with open(fixture_path, "r") as fh:
        raw = fh.read().lower()
    if "not generator output" not in raw:
        errors.append("fixture does not disclaim being generator output")
    if "independent" not in raw:
        errors.append("fixture does not self-label as independent")
    detail["fixture"] = os.path.basename(fixture_path)
    return ReadbackResult("md_fixture_honestly_tagged", not errors, errors, detail)


def _md_setup_prim(stage):
    root = stage.GetDefaultPrim()
    if not root or not root.IsValid():
        return None, None
    setup = stage.GetPrimAtPath(f"{root.GetPath()}/{MD_SETUP_PRIM_NAME}")
    return root, (setup if setup and setup.IsValid() else None)


def _grounding_matches(source_tag: str, grounding: str) -> bool:
    s = (source_tag or "").lower()
    if grounding == "R01":
        return "[source: r01" in s
    if grounding == "assumption":
        return "[assumption:" in s
    return False


def assert_core_readback(stage_path, fixture) -> ReadbackResult:
    """Every CORE field reads back with the right value, unit, and source tag,
    matching the independent fixture; CORE is complete with no drift."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    root, setup = _md_setup_prim(stage)
    if setup is None:
        return ReadbackResult("md_core_readback", False,
                              [f"no {MD_SETUP_PRIM_NAME} prim under default prim"])

    detail["setup_path"] = str(setup.GetPath())
    if setup.GetTypeName() != MD_SETUP_PRIM_TYPE:
        errors.append(f"mdSetup typeName={setup.GetTypeName()} != {MD_SETUP_PRIM_TYPE}")

    fx_core = fixture["core"]
    spec_units = {s: u for s, _t, u in CORE_FIELDS}

    # --- value + unit + source per CORE field (vs fixture) ---
    for suffix in _CORE_SUFFIXES:
        attr = setup.GetAttribute(MD_NS + suffix)
        if not attr.IsValid() or attr.Get() is None:
            errors.append(f"CORE {suffix}: attribute missing/unset")
            continue
        recorded = attr.Get()
        fx = fx_core.get(suffix)
        if fx is None:
            errors.append(f"CORE {suffix}: absent from fixture (unexpected core field)")
            continue
        if not _values_equal(recorded, fx["value"]):
            errors.append(f"CORE {suffix}: USD {recorded!r} != fixture {fx['value']!r}")
        cd = attr.GetCustomData()
        # unit
        exp_unit = spec_units.get(suffix)
        if exp_unit != fx.get("unit"):
            errors.append(f"CORE {suffix}: spec unit {exp_unit!r} != fixture unit {fx.get('unit')!r}")
        if exp_unit is not None and cd.get("unit") != exp_unit:
            errors.append(f"CORE {suffix}: USD unit {cd.get('unit')!r} != {exp_unit!r}")
        # source-tag grounding (R01 vs assumption)
        if not _grounding_matches(cd.get("source", ""), fx["grounding"]):
            errors.append(
                f"CORE {suffix}: source tag {cd.get('source')!r} inconsistent "
                f"with fixture grounding {fx['grounding']!r}")

    # --- CORE completeness / no-drift: authored core set == fixture core set ---
    authored_core = set()
    for attr in setup.GetAttributes():
        name = attr.GetName()
        if not name.startswith(MD_NS):
            continue
        suffix = name[len(MD_NS):]
        if suffix in _CORE_SUFFIXES:
            authored_core.add(suffix)
    if authored_core != _CORE_SUFFIXES:
        errors.append(f"authored CORE {sorted(authored_core)} != spec {sorted(_CORE_SUFFIXES)}")
    if set(fx_core.keys()) != _CORE_SUFFIXES:
        errors.append(f"fixture CORE {sorted(fx_core)} != spec {sorted(_CORE_SUFFIXES)}")

    detail["authored_core_count"] = len(authored_core)
    return ReadbackResult("md_core_readback", not errors, errors, detail)


def assert_pi_promoted_in_core(stage_path, fixture) -> ReadbackResult:
    """Q-003 directive: ionConcentration & protonationState ARE in CORE, set."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    _root, setup = _md_setup_prim(stage)
    if setup is None:
        return ReadbackResult("md_pi_promoted_core", False, ["no mdSetup prim"])

    fx_promoted = set(fixture.get("pi_promoted_core", []))
    if fx_promoted != set(PI_PROMOTED_CORE):
        errors.append(f"fixture pi_promoted {sorted(fx_promoted)} != {sorted(PI_PROMOTED_CORE)}")
    for suffix in PI_PROMOTED_CORE:
        if suffix not in _CORE_SUFFIXES:
            errors.append(f"{suffix} not declared in CORE spec")
        attr = setup.GetAttribute(MD_NS + suffix)
        if not attr.IsValid() or attr.Get() is None:
            errors.append(f"PI-promoted {suffix}: missing/unset on mdSetup prim")
    detail["pi_promoted"] = list(PI_PROMOTED_CORE)
    return ReadbackResult("md_pi_promoted_core", not errors, errors, detail)


def assert_test_anchors(stage_path) -> ReadbackResult:
    """USD values match the in-test R01 anchors (third independent oracle)."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    _root, setup = _md_setup_prim(stage)
    if setup is None:
        return ReadbackResult("md_test_anchors", False, ["no mdSetup prim"])
    for suffix, expected in ANCHOR_CORE.items():
        attr = setup.GetAttribute(MD_NS + suffix)
        recorded = attr.Get() if attr.IsValid() else None
        if recorded is None or not _values_equal(recorded, expected):
            errors.append(f"anchor {suffix}: USD {recorded!r} != R01-stated {expected!r}")
        else:
            detail[suffix] = recorded
    return ReadbackResult("md_test_anchors", not errors, errors, detail)


def assert_optional_readback(stage_path, fixture) -> ReadbackResult:
    """Each OPTIONAL field present in the fixture reads back matching."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    _root, setup = _md_setup_prim(stage)
    if setup is None:
        return ReadbackResult("md_optional_readback", False, ["no mdSetup prim"])
    spec_units = {s: u for s, _t, u in OPTIONAL_FIELDS}
    checked = 0
    for suffix, fx in fixture.get("optional", {}).items():
        if suffix not in _OPTIONAL_SUFFIXES:
            errors.append(f"OPTIONAL {suffix}: not in OPTIONAL_FIELDS spec")
            continue
        attr = setup.GetAttribute(MD_NS + suffix)
        if not attr.IsValid() or attr.Get() is None:
            errors.append(f"OPTIONAL {suffix}: missing/unset")
            continue
        checked += 1
        if not _values_equal(attr.Get(), fx["value"]):
            errors.append(f"OPTIONAL {suffix}: USD {attr.Get()!r} != fixture {fx['value']!r}")
        exp_unit = spec_units.get(suffix)
        if exp_unit is not None and attr.GetCustomData().get("unit") != exp_unit:
            errors.append(f"OPTIONAL {suffix}: unit {attr.GetCustomData().get('unit')!r} != {exp_unit!r}")
    detail["optional_checked"] = checked
    if checked == 0:
        errors.append("no optional fields read back")
    return ReadbackResult("md_optional_readback", not errors, errors, detail)


def assert_departmental_layering(stage_path) -> ReadbackResult:
    """The Protocol layer composed over Biology: atoms from the topology
    subLayer still resolve alongside the mdSetup prim on the same root."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    root, setup = _md_setup_prim(stage)
    if setup is None:
        return ReadbackResult("md_departmental_layering", False, ["no mdSetup prim"])
    atom_prims = [p for p in stage.Traverse()
                  if p.GetAttribute("bio:element").IsValid()
                  and p.GetAttribute("bio:element").Get()]
    detail["composed_atom_prims"] = len(atom_prims)
    detail["root"] = str(root.GetPath())
    # mdSetup and atoms must share the same root (Protocol over Biology).
    if atom_prims:
        if not str(atom_prims[0].GetPath()).startswith(str(root.GetPath())):
            errors.append("topology atoms are not under the composed root prim")
    else:
        errors.append("no atoms composed from Biology subLayer (layering broken)")
    return ReadbackResult("md_departmental_layering", not errors, errors, detail)


def run(stage_path: str = None) -> list:
    stage_path = stage_path or default_output_path()
    fixture_path = _fixture_path()
    if not os.path.isfile(stage_path):
        return [ReadbackResult("md_setup_stage_exists", False,
                               [f"not found: {stage_path}"])]
    with open(fixture_path, "r") as fh:
        fixture = json.load(fh)
    return [
        assert_fixture_honestly_tagged(fixture_path),
        assert_core_readback(stage_path, fixture),
        assert_pi_promoted_in_core(stage_path, fixture),
        assert_test_anchors(stage_path),
        assert_optional_readback(stage_path, fixture),
        assert_departmental_layering(stage_path),
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
