"""test_provenance_metadata.py — Step 4 of provenance_metadata leaf.

Read-back tests for structured bio: provenance attributes in
assembly_with_provenance.usda. Opens the stage FRESH (no generator state in
scope) and asserts each of the six lineage fields is present, non-empty, and
declared as type ``string``. Also asserts the legacy ``bio:source`` attribute
is absent, and that ``bio:simSettings`` parses as valid JSON with the required
keys.

No tautologies: the stage is opened independently of the build script; the
assertions are falsifiable (each would fail if the attribute were missing,
empty, wrongly typed, or if bio:source were present).

[source: examples/composition_advanced/provenance_metadata/assembly_with_provenance.usda]
[source: __roadmap__/v8-gap-closure/gap_closure/composition_advanced/provenance_metadata.md — Step 4]

Attribute confirmed via context7 /websites/openusd_release:
  - prim.GetAttribute(name).IsValid()   — attribute presence check
  - attr.Get()                          — retrieve authored value
  - attr.GetTypeName()                  — returns Sdf.ValueTypeName; str() gives "string"
    [source: context7 /websites/openusd_release — UsdAttribute.GetTypeName]

Usage (from repo root):
    . ./load_env.sh
    /path/to/forOUSD/bin/python3 tests/composition_advanced/test_provenance_metadata.py
"""

import json
import os
import sys

from pxr import Usd, UsdGeom

# ---------------------------------------------------------------------------
# Locate the USDA output — path relative to repo root
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_STAGE_PATH = os.path.join(
    _REPO_ROOT,
    "examples", "composition_advanced", "provenance_metadata",
    "assembly_with_provenance.usda",
)

# The six provenance attribute names that must be present
_PROVENANCE_ATTRS = [
    "bio:sourcePdb",
    "bio:forceField",
    "bio:softwareName",
    "bio:softwareVersion",
    "bio:simSettings",
    "bio:timestamp",
]

# The legacy flat attribute that must NOT exist
_LEGACY_ATTR = "bio:source"

# Required JSON keys in bio:simSettings
_SIM_SETTINGS_KEYS = {"timestep_fs", "temp_K", "pressure_bar"}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _open_fresh_stage() -> Usd.Stage:
    """Open assembly_with_provenance.usda with a fresh, isolated stage."""
    assert os.path.isfile(_STAGE_PATH), (
        f"Stage not found: {_STAGE_PATH}\n"
        "Run build_provenance.py first."
    )
    stage = Usd.Stage.Open(_STAGE_PATH)
    errors = stage.GetCompositionErrors()
    assert not errors, f"Composition errors on open: {errors}"
    return stage


def _get_complex_prim(stage: Usd.Stage) -> Usd.Prim:
    """Retrieve /ABLComplex prim; assert it is valid."""
    prim = stage.GetPrimAtPath("/ABLComplex")
    assert prim.IsValid(), "/ABLComplex prim not found in stage"
    return prim


# ---------------------------------------------------------------------------
# Test 1: all six provenance attributes present and non-empty
# ---------------------------------------------------------------------------

def test_all_provenance_fields_present() -> None:
    """Each of the six bio: provenance attributes must exist and be non-empty.

    Falsifiable: would fail if any attribute were absent or had an empty value.
    """
    stage = _open_fresh_stage()
    prim = _get_complex_prim(stage)

    for attr_name in _PROVENANCE_ATTRS:
        attr = prim.GetAttribute(attr_name)
        assert attr.IsValid(), (
            f"Attribute '{attr_name}' is missing from /ABLComplex"
        )
        value = attr.Get()
        assert value is not None, (
            f"Attribute '{attr_name}' returns None (no authored value)"
        )
        assert isinstance(value, str), (
            f"Attribute '{attr_name}' value is not a str: {type(value)}"
        )
        assert value.strip(), (
            f"Attribute '{attr_name}' value is empty or whitespace-only: {value!r}"
        )

    print(f"  PASS: all {len(_PROVENANCE_ATTRS)} provenance attributes present and non-empty")


# ---------------------------------------------------------------------------
# Test 2: all six attributes declared as type 'string'
# ---------------------------------------------------------------------------

def test_provenance_field_types() -> None:
    """Each bio: provenance attribute must have declared type 'string'.

    Uses attr.GetTypeName() — returns an Sdf.ValueTypeName whose str()
    representation is 'string' for Sdf.ValueTypeNames.String.
    [source: context7 /websites/openusd_release — UsdAttribute.GetTypeName]

    Falsifiable: would fail if any attribute were authored with a non-string
    type (e.g., token, int, float).
    """
    stage = _open_fresh_stage()
    prim = _get_complex_prim(stage)

    for attr_name in _PROVENANCE_ATTRS:
        attr = prim.GetAttribute(attr_name)
        assert attr.IsValid(), f"Attribute '{attr_name}' not found"
        type_name = attr.GetTypeName()
        type_str = str(type_name)
        assert type_str == "string", (
            f"Attribute '{attr_name}' has type '{type_str}', expected 'string'"
        )

    print(f"  PASS: all {len(_PROVENANCE_ATTRS)} provenance attributes have declared type 'string'")


# ---------------------------------------------------------------------------
# Test 3: legacy bio:source attribute is ABSENT
# ---------------------------------------------------------------------------

def test_legacy_source_absent() -> None:
    """bio:source must NOT exist on /ABLComplex.

    The structured schema fully replaces the legacy flat string.
    Falsifiable: would fail if the old attribute were still authored.
    """
    stage = _open_fresh_stage()
    prim = _get_complex_prim(stage)

    legacy_attr = prim.GetAttribute(_LEGACY_ATTR)
    assert not legacy_attr.IsValid(), (
        f"Legacy attribute '{_LEGACY_ATTR}' is still present on /ABLComplex — "
        "it must be removed when using the structured provenance schema"
    )

    print(f"  PASS: legacy '{_LEGACY_ATTR}' attribute is absent (correctly replaced)")


# ---------------------------------------------------------------------------
# Test 4: bio:simSettings parses as JSON with required keys
# ---------------------------------------------------------------------------

def test_sim_settings_parseable_json() -> None:
    """bio:simSettings must be a valid JSON string with timestep_fs, temp_K,
    and pressure_bar keys, each with numeric values.

    Falsifiable: would fail if the value is not valid JSON, if any required
    key is absent, or if the values are not numeric.
    """
    stage = _open_fresh_stage()
    prim = _get_complex_prim(stage)

    attr = prim.GetAttribute("bio:simSettings")
    assert attr.IsValid(), "bio:simSettings attribute not found"

    raw = attr.Get()
    assert raw is not None, "bio:simSettings returns None"

    # Must be parseable as JSON
    try:
        settings = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"bio:simSettings is not valid JSON: {exc}\nValue: {raw!r}"
        ) from exc

    assert isinstance(settings, dict), (
        f"bio:simSettings JSON must be a dict, got {type(settings)}: {settings}"
    )

    # All three required keys must be present
    for key in _SIM_SETTINGS_KEYS:
        assert key in settings, (
            f"bio:simSettings JSON missing required key '{key}'. "
            f"Present keys: {list(settings.keys())}"
        )

    # Values must be numeric (int or float)
    for key in _SIM_SETTINGS_KEYS:
        val = settings[key]
        assert isinstance(val, (int, float)), (
            f"bio:simSettings['{key}'] must be numeric, got {type(val)}: {val!r}"
        )

    print(
        f"  PASS: bio:simSettings parses as JSON with keys "
        f"timestep_fs={settings['timestep_fs']}, "
        f"temp_K={settings['temp_K']}, "
        f"pressure_bar={settings['pressure_bar']}"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_all_provenance_fields_present,
        test_provenance_field_types,
        test_legacy_source_absent,
        test_sim_settings_parseable_json,
    ]

    passed = 0
    failed = 0
    for fn in tests:
        print(f"Running {fn.__name__} ...")
        try:
            fn()
            passed += 1
        except AssertionError as exc:
            print(f"  FAIL: {exc}")
            failed += 1
        except Exception as exc:
            print(f"  ERROR: {type(exc).__name__}: {exc}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
    print("All tests PASSED.")
