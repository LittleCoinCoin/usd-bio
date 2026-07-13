"""
provenance.py -- six-field ``bio:`` provenance schema for the p53_mdm2 package.

Generalized (reuse) from foundation_demo_v8/composition_advanced/
provenance_metadata/{provenance_schema,provenance_source}.py. What is carried:

- The SIX-FIELD lineage schema (``apply_provenance_metadata``) authored as
  typed ``bio:`` string attributes -- the same field names v8 uses, so this is
  a genuine reuse of the pattern rather than a fork.
- The "unknown, never fabricated" philosophy: any field a caller cannot resolve
  from a real source is recorded as the literal string ``"unknown"``. A
  failed/absent value is an explicit ``unknown`` tag, NEVER an invented value.

What is generalized off v8 specifics:

- v8's ``provenance_source.py`` hard-wires GENESIS ``.inp``/``.log`` parsing for
  the ShinobuLab MD run. That is MD-provenance; Pipeline 2's provenance records
  a *predictor query* (DDMut-PPI). ``ddmut_provenance_record`` builds the six
  fields for a ddMut ddG query -- reusing the schema, not the MD parser.

No ``pxr`` import at module import time except inside ``apply_provenance_metadata``
(which needs ``Sdf``); the record builders are pure Python and import-safe
before the OpenUSD environment is loaded.
"""

from __future__ import annotations

import json

# Canonical field names in the bio: namespace (identical to v8's schema so the
# provenance vocabulary stays consistent across the codebase).
PROVENANCE_FIELDS = (
    "bio:sourcePdb",
    "bio:forceField",
    "bio:softwareName",
    "bio:softwareVersion",
    "bio:simSettings",
    "bio:timestamp",
)

_ATTR_TO_KEY = {
    "bio:sourcePdb":       "sourcePdb",
    "bio:forceField":      "forceField",
    "bio:softwareName":    "softwareName",
    "bio:softwareVersion": "softwareVersion",
    "bio:simSettings":     "simSettings",
    "bio:timestamp":       "timestamp",
}

# The single honest sentinel for an unresolved field (never a fabricated value).
UNKNOWN = "unknown"


def apply_provenance_metadata(prim, record: dict) -> None:
    """Author all six structured provenance attributes onto *prim*.

    Reused from v8 ``provenance_schema.apply_provenance_metadata``. Every field
    must be a non-empty string; unresolved fields must be the literal
    :data:`UNKNOWN` string, never omitted and never fabricated.

    Args:
        prim: a valid ``Usd.Prim`` to receive the six ``bio:`` attributes.
        record: dict with the six string keys (``sourcePdb``, ``forceField``,
            ``softwareName``, ``softwareVersion``, ``simSettings``,
            ``timestamp``).

    Raises:
        ValueError: if the prim is invalid, a key is missing, or a value is not
            a non-empty string.
    """
    from pxr import Sdf  # local import: keep module import-safe without pxr

    if not prim.IsValid():
        raise ValueError(f"apply_provenance_metadata: prim is not valid: {prim}")

    for attr_name, key in _ATTR_TO_KEY.items():
        if key not in record:
            raise ValueError(
                f"apply_provenance_metadata: missing required key '{key}'")
        value = record[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"apply_provenance_metadata: value for '{key}' must be a "
                f"non-empty string, got {value!r}")
        prim.CreateAttribute(attr_name, Sdf.ValueTypeNames.String).Set(value)


def ddmut_provenance_record(
    *,
    source_pdb: str,
    mutation: str,
    chain: str,
    endpoint: str,
    timestamp: str,
    software_version: str = UNKNOWN,
    reverse: bool = False,
) -> dict:
    """Build a six-field provenance record for a DDMut-PPI ddG query.

    Reuses the MD schema field names, mapping each to its ddMut analogue and
    honestly marking non-applicable fields:

    - ``sourcePdb``       -> the structure the mutation was applied to (1YCR).
    - ``forceField``      -> ``"n/a (DDMut-PPI graph-based ML predictor)"``:
      ddMut is not a force-field method, so a force field would be fabricated;
      the field is filled with an explicit not-applicable note, never a made-up
      force-field name.
    - ``softwareName``    -> ``"DDMut-PPI"``.
    - ``softwareVersion`` -> the API does not report a version, so this defaults
      to :data:`UNKNOWN` unless the caller resolves one.
    - ``simSettings``     -> JSON of the query parameters (mutation, chain,
      endpoint, reverse) -- the reproducible "settings" of this prediction.
    - ``timestamp``       -> ISO-8601 time the query/record was made.

    All fields are always non-empty strings so the record is directly usable by
    :func:`apply_provenance_metadata`.
    """
    settings = {
        "mutation": mutation,
        "chain": chain,
        "endpoint": endpoint,
        "reverse": bool(reverse),
    }
    return {
        "sourcePdb": source_pdb or UNKNOWN,
        "forceField": "n/a (DDMut-PPI graph-based ML predictor)",
        "softwareName": "DDMut-PPI",
        "softwareVersion": software_version or UNKNOWN,
        "simSettings": json.dumps(settings, sort_keys=True),
        "timestamp": timestamp or UNKNOWN,
    }
