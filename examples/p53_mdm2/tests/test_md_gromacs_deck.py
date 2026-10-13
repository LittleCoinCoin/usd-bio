"""
GROMACS deck read-back + USD -> .mdp round-trip (p1b gate 3).

Falsification-resistant (R00 anti-tautology). Every check opens the committed
``output/p53_mdm2_md_setup_gromacs.usda`` FRESH and compares against oracles
that are NOT the generator's in-memory state:

  1. ``templates/fixtures/md_setup_gromacs_reference.json`` -- hand-transcribed
     USD values, per-stage overrides, and the expected ``.mdp`` / ``prep.env``
     contents with the unit conversions worked by hand.
  2. In-test conversion anchors: rcoulomb / ref-p / fourierspacing are
     recomputed HERE from the raw USD Angstrom/atm values with the physical
     constants written in this file, so a wrong factor in the emitter and a
     matching typo in the fixture cannot both slip through.
  3. An independent ``.mdp`` reader (``_parse_mdp``) -- the emitter's own
     pair list is never consulted.

Also: the committed deck under ``cluster/p53_md/`` must be byte-identical to a
fresh emission (staleness guard), the job scripts must consume that deck
rather than carry parameters of their own, and the GROMACS force-field
divergence from the planned ff19SB must stay tagged as an assumption.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    from pxr import Usd
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pxr not importable. Run under the OpenUSD interpreter with the "
        "OpenUSD lib/python on PYTHONPATH.") from exc

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_PKG_PARENT = os.path.dirname(_PKG)
for _p in (_HERE, _PKG_PARENT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from p53_mdm2.templates.md_parameters import (  # noqa: E402
    MD_NS, MD_SETUP_PRIM_NAME, MD_PROTOCOL_PRIM_NAME, CORE_FIELDS, OPTIONAL_FIELDS,
    STAGE_FIELDS, gromacs_output_path,
)
from p53_mdm2.templates import gromacs_deck  # noqa: E402
from test_md_setup_readback import (  # noqa: E402
    ReadbackResult, assert_fixture_honestly_tagged, assert_departmental_layering,
    _values_equal,
)

_DECK_DIR = os.path.join(_PKG, "cluster", "p53_md")
_RUN_SH = os.path.join(_DECK_DIR, "p53_md_run.sh")
_SUBMIT = os.path.join(_DECK_DIR, "p53_md_submit.sbatch")

# --- in-test physical constants (third oracle; not imported) ---
ANGSTROM_PER_NM = 10.0
BAR_PER_ATM = 1.01325
_TOL = 1e-9

_SPEC_UNITS = {s: u for s, _t, u in (*CORE_FIELDS, *OPTIONAL_FIELDS, *STAGE_FIELDS)}


def _fixture_path() -> str:
    return os.path.join(_PKG, "templates", "fixtures", "md_setup_gromacs_reference.json")


def _setup(stage):
    root = stage.GetDefaultPrim()
    if not root or not root.IsValid():
        return None
    p = root.GetChild(MD_SETUP_PRIM_NAME)
    return p if p and p.IsValid() else None


def _grounding_ok(tag: str, grounding: str) -> bool:
    t = (tag or "").lower()
    return {"source": "[source:", "assumption": "[assumption:"}.get(grounding, "\0") in t


def _authored(prim) -> dict:
    return {a.GetName()[len(MD_NS):]: a for a in prim.GetAttributes()
            if a.GetName().startswith(MD_NS) and a.HasAuthoredValue()}


def _parse_mdp(text: str) -> dict:
    """Independent .mdp reader: ``key = value``, ';' comments, last wins."""
    out = {}
    for line in text.splitlines():
        line = line.split(";", 1)[0].strip()
        if not line:
            continue
        key, sep, val = line.partition("=")
        if sep:
            out[key.strip()] = val.strip()
    return out


def _parse_env(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z_]+)='([^']*)'$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def _mdp_value_equal(text: str, expected) -> bool:
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        try:
            return abs(float(text) - float(expected)) <= _TOL * max(1.0, abs(expected))
        except ValueError:
            return False
    return text == str(expected)


# ---------------------------------------------------------------------------
def assert_values_readback(stage_path, fixture) -> ReadbackResult:
    """CORE + OPTIONAL read back with fixture value, spec unit, and grounding."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    setup = _setup(stage)
    if setup is None:
        return ReadbackResult("gmx_values_readback", False, ["no mdSetup prim"])
    authored = _authored(setup)
    expected = {**fixture["core"], **fixture["optional"]}
    for suffix, fx in expected.items():
        attr = authored.get(suffix)
        if attr is None:
            errors.append(f"{suffix}: not authored")
            continue
        if not _values_equal(attr.Get(), fx["value"]):
            errors.append(f"{suffix}: USD {attr.Get()!r} != fixture {fx['value']!r}")
        cd = attr.GetCustomData()
        if _SPEC_UNITS.get(suffix) != fx["unit"] or cd.get("unit") != fx["unit"]:
            errors.append(f"{suffix}: unit spec={_SPEC_UNITS.get(suffix)!r} "
                          f"usd={cd.get('unit')!r} fixture={fx['unit']!r}")
        if not _grounding_ok(cd.get("source", ""), fx["grounding"]):
            errors.append(f"{suffix}: source tag {cd.get('source')!r} is not "
                          f"[{fx['grounding']}:]")
    extra = sorted(set(authored) - set(expected) - {"startingStructure"})
    if extra:
        errors.append(f"authored but not in fixture: {extra}")
    start = authored.get("startingStructure")
    if start is None or start.Get() != fixture["starting_structure"]:
        errors.append("startingStructure missing or wrong")
    detail["checked"] = len(expected)
    return ReadbackResult("gmx_values_readback", not errors, errors, detail)


def assert_stages_readback(stage_path, fixture) -> ReadbackResult:
    """Ordered protocol stages carry exactly the fixture's overrides."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    setup = _setup(stage)
    protocol = setup.GetChild(MD_PROTOCOL_PRIM_NAME) if setup else None
    if not protocol or not protocol.IsValid():
        return ReadbackResult("gmx_stages_readback", False, ["no mdSetup/protocol prim"])
    names = [c.GetName() for c in protocol.GetChildren()]
    want = [n for n, _f in fixture["stages"]]
    if names != want:
        errors.append(f"stage order {names} != {want}")
    for name, fields in fixture["stages"]:
        prim = protocol.GetChild(name)
        if not prim or not prim.IsValid():
            errors.append(f"stage {name}: missing")
            continue
        got = {k: a.Get() for k, a in _authored(prim).items()}
        if set(got) != set(fields):
            errors.append(f"stage {name}: authored {sorted(got)} != {sorted(fields)}")
        for k, v in fields.items():
            if k in got and not _values_equal(got[k], v):
                errors.append(f"stage {name}.{k}: {got[k]!r} != {v!r}")
    detail["stages"] = names
    return ReadbackResult("gmx_stages_readback", not errors, errors, detail)


def assert_divergence_tagged(stage_path) -> ReadbackResult:
    """The force field departs from the planned ff19SB; that must stay visible."""
    errors = []
    stage = Usd.Stage.Open(stage_path)
    setup = _setup(stage)
    if setup is None:
        return ReadbackResult("gmx_ff_divergence_tagged", False, ["no mdSetup prim"])
    ff = setup.GetAttribute(MD_NS + "forceField")
    tag = ff.GetCustomData().get("source", "") if ff.IsValid() else ""
    if not tag.startswith("[assumption:") or "ff19SB" not in tag:
        errors.append(f"forceField tag does not record the ff19SB divergence: {tag!r}")
    if setup.GetAttribute(MD_NS + "engine").Get() != "GROMACS":
        errors.append("engine is not GROMACS")
    return ReadbackResult("gmx_ff_divergence_tagged", not errors, errors, {})


def _emit_fresh(stage_path):
    tmp = tempfile.mkdtemp(prefix="p53md_deck_")
    try:
        gromacs_deck.emit_deck(stage_path, tmp)
        return {fn: open(os.path.join(tmp, fn)).read() for fn in sorted(os.listdir(tmp))}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def assert_mdp_roundtrip(fresh, fixture) -> ReadbackResult:
    """Emitted .mdp == fixture's hand-written expectation, key set and values."""
    errors, detail = [], {}
    for stage_name, want in fixture["expected_mdp"].items():
        text = fresh.get(f"{stage_name}.mdp")
        if text is None:
            errors.append(f"{stage_name}.mdp not emitted")
            continue
        got = _parse_mdp(text)
        if set(got) != set(want):
            errors.append(f"{stage_name}.mdp keys: extra {sorted(set(got) - set(want))} "
                          f"missing {sorted(set(want) - set(got))}")
        for k, v in want.items():
            if k in got and not _mdp_value_equal(got[k], v):
                errors.append(f"{stage_name}.mdp {k} = {got[k]!r}, expected {v!r}")
    emitted = sorted(fn[:-4] for fn in fresh if fn.endswith(".mdp"))
    if emitted != sorted(fixture["expected_mdp"]):
        errors.append(f"emitted stages {emitted} != fixture {sorted(fixture['expected_mdp'])}")
    detail["stages"] = emitted
    return ReadbackResult("gmx_mdp_roundtrip", not errors, errors, detail)


def assert_unit_conversions(stage_path, fresh) -> ReadbackResult:
    """rcoulomb/rvdw/fourierspacing/ref-p recomputed here from raw USD values."""
    errors, detail = [], {}
    stage = Usd.Stage.Open(stage_path)
    setup = _setup(stage)
    a = lambda s: setup.GetAttribute(MD_NS + s)  # noqa: E731
    if a("cutoff").GetCustomData().get("unit") != "angstrom" \
            or a("pmeGridSpacing").GetCustomData().get("unit") != "angstrom" \
            or a("pressure").GetCustomData().get("unit") != "atm":
        errors.append("USD length/pressure not stored in angstrom/atm")
    want = {
        "rcoulomb": a("cutoff").Get() / ANGSTROM_PER_NM,
        "rvdw": a("cutoff").Get() / ANGSTROM_PER_NM,
        "fourierspacing": a("pmeGridSpacing").Get() / ANGSTROM_PER_NM,
    }
    md = _parse_mdp(fresh.get("md.mdp", ""))
    npt = _parse_mdp(fresh.get("npt.mdp", ""))
    for k, v in want.items():
        if not _mdp_value_equal(md.get(k, "nan"), v):
            errors.append(f"md.mdp {k}={md.get(k)!r} != {v} (Angstrom/10)")
    ref_p = a("pressure").Get() * BAR_PER_ATM
    for name, d in (("md", md), ("npt", npt)):
        if not _mdp_value_equal(d.get("ref-p", "nan"), ref_p):
            errors.append(f"{name}.mdp ref-p={d.get('ref-p')!r} != {ref_p} bar")
    env = _parse_env(fresh.get("prep.env", ""))
    box = a("soluteBoxDistance").Get() / ANGSTROM_PER_NM
    if not _mdp_value_equal(env.get("BOX_DISTANCE_NM", "nan"), box):
        errors.append(f"prep.env BOX_DISTANCE_NM={env.get('BOX_DISTANCE_NM')!r} != {box}")
    detail.update({k: v for k, v in want.items()}, ref_p_bar=ref_p, box_nm=box)
    return ReadbackResult("gmx_unit_conversions", not errors, errors, detail)


def assert_prep_env_roundtrip(fresh, fixture) -> ReadbackResult:
    errors = []
    got = _parse_env(fresh.get("prep.env", ""))
    want = fixture["expected_prep_env"]
    if got != want:
        for k in sorted(set(got) | set(want)):
            if got.get(k) != want.get(k):
                errors.append(f"prep.env {k}: {got.get(k)!r} != {want.get(k)!r}")
    return ReadbackResult("gmx_prep_env_roundtrip", not errors, errors, {"keys": len(got)})


def assert_committed_deck_fresh(fresh) -> ReadbackResult:
    """The deck the job will read is exactly what the USD stage emits now."""
    errors = []
    for fn, text in fresh.items():
        path = os.path.join(_DECK_DIR, fn)
        if not os.path.isfile(path):
            errors.append(f"cluster/p53_md/{fn} not committed")
        elif open(path).read() != text:
            errors.append(f"cluster/p53_md/{fn} is STALE -- re-run templates/gromacs_deck.py")
    stray = sorted(fn for fn in os.listdir(_DECK_DIR)
                   if (fn.endswith(".mdp") or fn == "prep.env") and fn not in fresh)
    if stray:
        errors.append(f"committed deck files the stage no longer emits: {stray}")
    return ReadbackResult("gmx_committed_deck_fresh", not errors, errors, {"files": len(fresh)})


def assert_scripts_consume_deck(fixture) -> ReadbackResult:
    """The job scripts read the emitted deck and carry no mdp parameters."""
    errors = []
    mdp_keys = {k for stage in fixture["expected_mdp"].values() for k in stage}
    for path in (_RUN_SH, _SUBMIT):
        if not os.path.isfile(path):
            errors.append(f"missing {os.path.basename(path)}")
            continue
        text = open(path).read()
        for k in sorted(mdp_keys):
            if re.search(rf"^\s*{re.escape(k)}\s*=", text, re.M):
                errors.append(f"{os.path.basename(path)} inlines mdp key {k!r}")
        bash = shutil.which("bash")
        if bash:
            res = subprocess.run([bash, "-n", path], capture_output=True, text=True)
            if res.returncode != 0:
                errors.append(f"bash -n {os.path.basename(path)}: {res.stderr.strip()[:80]}")
    run_sh = open(_RUN_SH).read() if os.path.isfile(_RUN_SH) else ""
    for needle in ('. "$DECK/prep.env"', 'mdp="$DECK/$s.mdp"', "for s in $STAGES"):
        if needle not in run_sh:
            errors.append(f"p53_md_run.sh does not contain {needle!r}")
    return ReadbackResult("gmx_scripts_consume_deck", not errors, errors, {})


def run(stage_path: str = None) -> list:
    stage_path = stage_path or gromacs_output_path()
    if not os.path.isfile(stage_path):
        return [ReadbackResult("gmx_stage_exists", False, [f"not found: {stage_path}"])]
    with open(_fixture_path()) as fh:
        fixture = json.load(fh)
    fresh = _emit_fresh(stage_path)
    # Reused checks are renamed so their rows are distinguishable from the
    # GENESIS-deck rows of test_md_setup_readback in the harness table.
    honest = assert_fixture_honestly_tagged(_fixture_path())
    honest.check_name = "gmx_fixture_honestly_tagged"
    layering = assert_departmental_layering(stage_path)
    layering.check_name = "gmx_departmental_layering"
    return [
        honest,
        assert_values_readback(stage_path, fixture),
        assert_stages_readback(stage_path, fixture),
        assert_divergence_tagged(stage_path),
        assert_mdp_roundtrip(fresh, fixture),
        assert_unit_conversions(stage_path, fresh),
        assert_prep_env_roundtrip(fresh, fixture),
        assert_committed_deck_fresh(fresh),
        assert_scripts_consume_deck(fixture),
        layering,
    ]


if __name__ == "__main__":
    results = run()
    for r in results:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.check_name}")
        for e in r.errors:
            print(f"    - {e}")
    raise SystemExit(0 if all(r.passed for r in results) else 1)
