"""provenance_schema.py — Structured provenance attribute schema helper.

Defines the six-field lineage schema for usd-bio provenance metadata and
provides a reusable helper function ``apply_provenance_metadata`` that authors
all six typed ``bio:`` attributes onto a USD prim.

The six fields replace the legacy flat ``bio:source`` string:

  bio:sourcePdb       (string) — source PDB accession or filename
  bio:forceField      (string) — force field identifier
  bio:softwareName    (string) — simulation software name
  bio:softwareVersion (string) — simulation software version
  bio:simSettings     (string) — JSON-encoded dict of key simulation settings
                                 (must include keys: timestep_fs, temp_K, pressure_bar)
  bio:timestamp       (string) — ISO-8601 datetime of when the simulation ran

API used: ``prim.CreateAttribute(name, Sdf.ValueTypeNames.String).Set(value)``
[source: context7 /websites/openusd_release — UsdPrim.CreateAttribute,
 Sdf.ValueTypeNames.String for custom string attributes on USD prims]

Usage::

    from provenance_schema import apply_provenance_metadata
    record = {
        "sourcePdb":       "2HYY.pdb",
        "forceField":      "AMBER99SB-ILDN",
        "softwareName":    "GENESIS",
        "softwareVersion": "2.1.0",
        "simSettings":     '{"timestep_fs": 2.0, "temp_K": 310, "pressure_bar": 1.0}',
        "timestamp":       "2024-03-15T09:00:00+09:00",
    }
    apply_provenance_metadata(prim, record)
"""

from pxr import Sdf

# Canonical field names in the bio: namespace.
# Each field maps to a required key in the record dict.
PROVENANCE_FIELDS = (
    "bio:sourcePdb",
    "bio:forceField",
    "bio:softwareName",
    "bio:softwareVersion",
    "bio:simSettings",
    "bio:timestamp",
)

# Mapping from bio: attribute name to the record dict key.
_ATTR_TO_KEY = {
    "bio:sourcePdb":       "sourcePdb",
    "bio:forceField":      "forceField",
    "bio:softwareName":    "softwareName",
    "bio:softwareVersion": "softwareVersion",
    "bio:simSettings":     "simSettings",
    "bio:timestamp":       "timestamp",
}


def apply_provenance_metadata(prim, record: dict) -> None:
    """Author all six structured provenance attributes onto *prim*.

    Parameters
    ----------
    prim:
        A valid ``Usd.Prim`` to receive the provenance attributes.
    record:
        Dict with required keys: ``sourcePdb``, ``forceField``,
        ``softwareName``, ``softwareVersion``, ``simSettings``, ``timestamp``.
        All values must be non-empty strings.

    Raises
    ------
    ValueError
        If any required key is missing or its value is empty.

    Notes
    -----
    Uses ``prim.CreateAttribute(name, Sdf.ValueTypeNames.String).Set(value)``
    for each field — the canonical USD Python API for custom string attributes.
    [source: context7 /websites/openusd_release — UsdPrim.CreateAttribute]
    """
    if not prim.IsValid():
        raise ValueError(f"apply_provenance_metadata: prim is not valid: {prim}")

    for attr_name, key in _ATTR_TO_KEY.items():
        if key not in record:
            raise ValueError(
                f"apply_provenance_metadata: missing required key '{key}' in record"
            )
        value = record[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"apply_provenance_metadata: value for '{key}' must be a non-empty string, "
                f"got {value!r}"
            )
        prim.CreateAttribute(attr_name, Sdf.ValueTypeNames.String).Set(value)
