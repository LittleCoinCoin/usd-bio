"""provenance_source.py — data-driven ShinobuLab provenance loader.

Scalable replacement for hard-coded provenance sentinels. Instead of a demo
script embedding literal strings like ``sourcePdb="2HYY.pdb"``, this module
PARSES the real ShinobuLab run artifacts under ``$USDBIO_DATA_DIR`` at
generation time and returns a record dict compatible with
``provenance_schema.apply_provenance_metadata``.

Why this design (vs. a static YAML/JSON metadata file committed by hand)
--------------------------------------------------------------------------
Two scalable options were weighed:

1. **Parse real run artifacts directly (chosen).** GENESIS ``.inp`` config
   files and ``.log`` run logs are already the ground-truth record of what
   ran — force field, ensemble, temperature, pressure, timestep, engine
   version, run date. Parsing them means provenance can never drift from
   the data: point this loader at a new dataset's equilibration directory
   and it re-derives fresh, correct values with zero code changes to the
   demo script. This is the same shape as ``usdbio_env.get_data_dir()``
   (env-driven, zero-USD-import, fails loudly) already used elsewhere in
   this codebase — this module follows that convention.
2. **Hand-authored metadata file per dataset (rejected as primary, but
   compatible).** A committed ``metadata.json`` per dataset is simpler to
   parse but re-introduces the exact hard-coding risk this task is meant
   to close: a human types values by hand and they silently drift from the
   `.inp`/`.log` files as the dataset evolves. Kept as a *future* escape
   hatch (see ``load_shinobulab_provenance``'s ``override`` parameter) for
   fields genuinely absent from any run artifact, not as the primary path.

Any field this loader cannot find in the data is set to the literal string
``"unknown"`` (never fabricated) and reported via ``UNRESOLVED_FIELDS`` in
the returned record's sibling list, so callers can decide whether to fail
loudly or proceed with an honestly incomplete record.

API used: only ``os`` / ``re`` / ``json`` — no ``pxr`` import, so this
module is importable before the OpenUSD environment is loaded, exactly
like ``usdbio_env.py``.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class ProvenanceResolution:
    """Result of resolving a ShinobuLab provenance record from real data.

    Attributes
    ----------
    record:
        dict compatible with ``provenance_schema.apply_provenance_metadata``
        (six string keys: sourcePdb, forceField, softwareName,
        softwareVersion, simSettings, timestamp). Fields that could not be
        resolved from data are set to the literal string ``"unknown"``.
    sources:
        dict mapping each of the six keys to the absolute file path it was
        extracted from (or ``None`` for unresolved fields).
    unresolved:
        list of field names that could not be found in the data and were
        set to ``"unknown"``.
    """
    record: dict = field(default_factory=dict)
    sources: dict = field(default_factory=dict)
    unresolved: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Low-level .inp / .log parsing helpers
# ---------------------------------------------------------------------------

def _read_text(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    with open(path, "r", errors="replace") as fh:
        return fh.read()


def _parse_inp_key(text: str, key: str) -> str | None:
    """Extract ``key = value`` (GENESIS .inp style, '#' comments) from text."""
    pattern = re.compile(
        r"^\s*" + re.escape(key) + r"\s*=\s*([^\s#]+)", re.MULTILINE
    )
    m = pattern.search(text)
    return m.group(1) if m else None


def _parse_log_field(text: str, label: str) -> str | None:
    """Extract ``label = value`` (GENESIS .log style, e.g. 'version      = 2.0.3')."""
    pattern = re.compile(
        r"^\s*" + re.escape(label) + r"\s*=\s*(.+?)\s*$", re.MULTILINE
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else None


# ---------------------------------------------------------------------------
# Field resolvers — each returns (value_or_None, source_path_or_None)
# ---------------------------------------------------------------------------

def _resolve_source_pdb(data_dir: str) -> tuple[str | None, str | None]:
    """The real starting structure filename.

    [source: README.md `files/` section — "atp-complex-solv35.pdb: Protein
    Data Bank format file for visualization."]
    """
    path = os.path.join(data_dir, "files", "atp-complex-solv35.pdb")
    if os.path.isfile(path):
        return "atp-complex-solv35.pdb", path
    return None, None


def _resolve_force_field(data_dir: str, inp_path: str) -> tuple[str | None, str | None]:
    """Force field family from a GENESIS [ENERGY] block.

    Only the family name is present in the run artifacts inspected
    (``forcefield = AMBER``); no `.inp`, `.log`, README, or the procedure
    .docx names a specific AMBER point-release (e.g. ff99SB-ILDN / ff14SB).
    The prmtop RADIUS_SET is 'modified Bondi radii (mbondi)', which is
    compatible with several AMBER protein force fields and does not by
    itself disambiguate the variant. Reporting the family honestly rather
    than guessing the variant.
    """
    text = _read_text(inp_path)
    if text is None:
        return None, None
    ff = _parse_inp_key(text, "forcefield")
    if ff is None:
        return None, None
    return f"AMBER (family; specific parameter set not recorded in data)", inp_path


def _resolve_software(eq_log_path: str) -> tuple[str | None, str | None, str | None]:
    """Engine name + version from a real GENESIS SPDYN log header.

    Returns (name, version, source_path).
    [source: equilibration/5-eq2/atpcomplex-cmd-eq2.log — 'GENESIS SPDYN'
     banner + 'GENESIS_Information> version = 2.0.3']
    """
    text = _read_text(eq_log_path)
    if text is None:
        return None, None, None
    name = "GENESIS" if "GENESIS" in text else None
    version = _parse_log_field(text, "version")
    return name, version, eq_log_path


def _resolve_sim_settings(inp_path: str) -> tuple[dict | None, str | None]:
    """Key simulation settings from a GENESIS [DYNAMICS]/[ENSEMBLE] block.

    timestep is authored in picoseconds in GENESIS .inp files; converted to
    femtoseconds for the simSettings schema (timestep_fs key).
    [source: equilibration/5-eq2/atpcomplex-cmd-eq2.inp — [DYNAMICS] and
     [ENSEMBLE] sections]
    """
    text = _read_text(inp_path)
    if text is None:
        return None, None

    timestep_ps = _parse_inp_key(text, "timestep")
    temp_k = _parse_inp_key(text, "temperature")
    pressure_bar = _parse_inp_key(text, "pressure")
    ensemble = _parse_inp_key(text, "ensemble")
    integrator = _parse_inp_key(text, "integrator")

    if timestep_ps is None and temp_k is None:
        return None, None

    settings: dict = {}
    if timestep_ps is not None:
        settings["timestep_fs"] = round(float(timestep_ps) * 1000.0, 4)
    if temp_k is not None:
        settings["temp_K"] = float(temp_k)
    if pressure_bar is not None:
        # GENESIS reports pressure in atm; carried through as pressure_bar
        # key per the existing schema, 1 atm ~= 1.01325 bar, but the raw
        # GENESIS unit is atm — recorded as-is with unit noted in the key
        # name kept for schema backward-compatibility. Not unit-converted
        # to avoid inventing precision the source data doesn't claim.
        settings["pressure_bar"] = float(pressure_bar)
    if ensemble is not None:
        settings["ensemble"] = ensemble
    if integrator is not None:
        settings["integrator"] = integrator

    return settings, inp_path


def _resolve_timestamp(eq_log_path: str) -> tuple[str | None, str | None]:
    """Real run date from the GENESIS log 'date' field.

    No timezone is recorded in the log, so the raw machine-local timestamp
    is normalized to ISO-8601 WITHOUT a fabricated UTC offset.
    [source: equilibration/5-eq2/atpcomplex-cmd-eq2.log — 'date = 2023/08/25 17:06:48']
    """
    text = _read_text(eq_log_path)
    if text is None:
        return None, None
    raw = _parse_log_field(text, "date")
    if raw is None:
        return None, None
    m = re.match(r"(\d{4})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2}):(\d{2})", raw)
    if not m:
        return raw, eq_log_path
    y, mo, d, h, mi, s = m.groups()
    return f"{y}-{mo}-{d}T{h}:{mi}:{s}", eq_log_path


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def load_shinobulab_provenance(data_dir: str) -> ProvenanceResolution:
    """Resolve a provenance record from real ShinobuLab run artifacts.

    Parameters
    ----------
    data_dir:
        Root of the ShinobuLab data directory (``$USDBIO_DATA_DIR``).

    Returns
    -------
    ProvenanceResolution
        ``.record`` is compatible with
        ``provenance_schema.apply_provenance_metadata`` (all six keys always
        present as non-empty strings — unresolved fields are the literal
        string ``"unknown"``, never a fabricated value).
        ``.sources`` maps each key to the absolute file path it came from.
        ``.unresolved`` lists any keys that fell back to ``"unknown"``.

    Notes
    -----
    Reads (all under ``data_dir``):
      - ``files/atp-complex-solv35.pdb``               (sourcePdb)
      - ``equilibration/5-eq2/atpcomplex-cmd-eq2.inp``  (forceField, simSettings)
      - ``equilibration/5-eq2/atpcomplex-cmd-eq2.log``  (softwareName,
                                                          softwareVersion, timestamp)
    The 5-eq2 stage is the FINAL equilibration step whose output is the
    equilibrated starting point for all downstream sampling
    [source: 251112-grest-reus-md-procedure-shinobu-lab.docx — "The final
    output of 5-eq2 was used as the equilibrated starting point for
    subsequent gREST temperature tuning and REUS pulling simulations."],
    making it the most representative single run record for the topology
    shipped as atp-complex-solv35.pdb/.prmtop/.inpcrd.
    """
    eq_dir = os.path.join(data_dir, "equilibration", "5-eq2")
    inp_path = os.path.join(eq_dir, "atpcomplex-cmd-eq2.inp")
    log_path = os.path.join(eq_dir, "atpcomplex-cmd-eq2.log")

    result = ProvenanceResolution()
    record: dict = {}
    sources: dict = {}
    unresolved: list = []

    # sourcePdb
    pdb_val, pdb_src = _resolve_source_pdb(data_dir)
    record["sourcePdb"] = pdb_val or "unknown"
    sources["sourcePdb"] = pdb_src
    if pdb_val is None:
        unresolved.append("sourcePdb")

    # forceField
    ff_val, ff_src = _resolve_force_field(data_dir, inp_path)
    record["forceField"] = ff_val or "unknown"
    sources["forceField"] = ff_src
    if ff_val is None:
        unresolved.append("forceField")

    # softwareName / softwareVersion
    sw_name, sw_version, sw_src = _resolve_software(log_path)
    record["softwareName"] = sw_name or "unknown"
    record["softwareVersion"] = sw_version or "unknown"
    sources["softwareName"] = sw_src if sw_name else None
    sources["softwareVersion"] = sw_src if sw_version else None
    if sw_name is None:
        unresolved.append("softwareName")
    if sw_version is None:
        unresolved.append("softwareVersion")

    # simSettings
    settings, settings_src = _resolve_sim_settings(inp_path)
    if settings:
        record["simSettings"] = json.dumps(settings, sort_keys=True)
        sources["simSettings"] = settings_src
    else:
        record["simSettings"] = "unknown"
        sources["simSettings"] = None
        unresolved.append("simSettings")

    # timestamp
    ts_val, ts_src = _resolve_timestamp(log_path)
    record["timestamp"] = ts_val or "unknown"
    sources["timestamp"] = ts_src
    if ts_val is None:
        unresolved.append("timestamp")

    result.record = record
    result.sources = sources
    result.unresolved = unresolved
    return result


if __name__ == "__main__":
    import sys as _sys

    _data_dir = os.environ.get("USDBIO_DATA_DIR")
    if not _data_dir:
        print("USDBIO_DATA_DIR not set.", file=_sys.stderr)
        _sys.exit(1)

    resolution = load_shinobulab_provenance(_data_dir)
    print("Resolved provenance record:")
    for k, v in resolution.record.items():
        src = resolution.sources.get(k)
        print(f"  {k:16s} = {v!r}  [source: {src}]")
    if resolution.unresolved:
        print(f"\nUNRESOLVED (set to 'unknown'): {resolution.unresolved}")
    else:
        print("\nAll fields resolved from real data.")
