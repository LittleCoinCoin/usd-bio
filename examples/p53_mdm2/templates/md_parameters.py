#!/usr/bin/env python3
"""
md_parameters.py -- USDBio MD-setup-parameter representation (``bio:md:``).

P1b Step 1 deliverable. Instantiates the R01-recommended reproducible MD-setup
parameter set as typed USD attributes on a dedicated ``mdSetup`` prim, so a
simulation is reproducible from the USD stage alone and serialises losslessly to
an MDDB (EU Molecular Dynamics Data Bank) YAML key-value tree.
[source: __reports__/p53-mdm2/01-md_reproducibility_survey_v0.md]

Design (kept minimal-core + optional-extensions -- useful, reusable, NOT an
exhaustive parameter dump):

- **Carrying prim.** A single dedicated ``Scope`` prim at ``<root>/mdSetup``,
  authored in a **Protocol departmental layer** that ``subLayers`` the Biology
  topology. Rationale: R01 recommends one dedicated ``MDSetup``/``Scope`` prim in
  the Protocol SubLayer so setup metadata is queryable per-attribute, unit-typed,
  and independently versionable/loadable -- which stage-level metadata (a flat,
  untyped, unit-less blob) cannot provide. This matches CLAUDE.md departmental
  layering ("Protocol/setup"). [source: R01 "Recommended bio:md: Attribute Schema"]

- **CORE set (17 attributes).** R01's ~15-field "conceptual-reproducibility"
  core (MDDB D1.1 §1 intersected with the LiveCoMS reporting checklist) PLUS the
  two fields the PI promoted to core in Q-003 because they are NOT derivable from
  geometry: ``ionConcentration`` and ``protonationState``.
  [source: __threads__/p53-mdm2/QUESTIONS.md Q-003 answer, PI 2026-07-12]

- **OPTIONAL extension block.** A clearly-separated set of methodology fields
  (box/PBC, pairlist, dispersion correction, hydrogen-mass repartitioning,
  Langevin friction, ion species) authored under the same namespace but only
  when a value is available.

- **REMD growth path.** R01 designs a nested ``bio:md:remd:`` block for
  replica-exchange runs (the ShinobuLab workflow is 2D gREST/REUS). Its field
  list is published here (:data:`REMD_FIELDS`) and documented in README.md, but
  it is NOT authored into the conventional-production p53-MDM2 artifact this
  cycle -- copying ShinobuLab's ABL-specific 288-replica ladder onto p53-MDM2
  would be fabrication. It is authored only when a caller supplies a real
  ``remd`` spec.

- **Units.** MDDB mandates a unit on every value; USD has no per-attribute unit
  primitive (except length). Each non-string attribute therefore carries its
  unit in ``customData["unit"]`` (lossless to the MDDB YAML tree). Every
  attribute also carries ``customData["source"]`` so the artifact is
  self-documenting and each value's provenance (R01 vs assumption) is inline.

- **Provenance.** Reuses the six-field ``bio:`` provenance schema from
  :mod:`p53_mdm2.composition.provenance` (no re-invention) to record where the
  parameter deck came from, satisfying MDDB's provenance-record intent.

Import-safe before the OpenUSD environment is loaded: no ``pxr`` at module
import time (only inside the authoring functions). The field specs and reference
values are plain Python.
"""

from __future__ import annotations

import os
import sys
from typing import Dict, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from p53_mdm2 import p53_env

# ---------------------------------------------------------------------------
# Namespace + field specifications (pxr-free constants)
# ---------------------------------------------------------------------------
#: Attribute namespace prefix for every MD-setup parameter.
MD_NS = "bio:md:"

#: Prim (relative to root) that carries the parameters, and its USD type.
MD_SETUP_PRIM_NAME = "mdSetup"
MD_SETUP_PRIM_TYPE = "Scope"

# Each field: (suffix, sdf_type_name, unit_or_None). The sdf_type_name is a key
# into the local Sdf.ValueTypeNames lookup built inside the authoring function,
# so this constant stays free of any pxr import.
#
# CORE -- the minimum defensible reproducible set. The final two entries are the
# PI-promoted (Q-003) fields, kept last and flagged so the "promoted to core"
# decision is visible in the schema itself.
CORE_FIELDS = (
    ("engine",              "String", None),
    ("engineVersion",       "String", None),
    ("forceField",          "String", None),
    ("waterModel",          "String", None),
    ("ensemble",            "Token",  None),      # {NVE, NVT, NPT}
    ("integrator",          "String", None),
    ("timestep",            "Double", "ps"),
    ("nSteps",              "Int64",  "steps"),
    ("temperature",         "Double", "K"),
    ("thermostat",          "String", None),
    ("barostat",            "String", None),
    ("pressure",            "Double", "atm"),
    ("electrostatics",      "Token",  None),      # {PME, CUTOFF, ...}
    ("cutoff",              "Double", "angstrom"),
    ("constraintAlgorithm", "String", None),
    # --- PI-promoted to CORE in Q-003 (not derivable from geometry) ---
    ("ionConcentration",    "Double", "mol/L"),
    ("protonationState",    "String", None),
)

#: Suffixes the PI explicitly promoted into CORE (Q-003) -- asserted by the test.
PI_PROMOTED_CORE = ("ionConcentration", "protonationState")

# OPTIONAL extension -- authored only when a value is supplied. Methodology
# detail that sharpens reproducibility but is not part of the minimal core.
OPTIONAL_FIELDS = (
    ("ionSpecies",                 "String", None),
    ("boxType",                    "Token",  None),      # {PBC, ...}
    ("pairlistDist",               "Double", "angstrom"),
    ("dispersionCorrection",       "String", None),
    ("hydrogenMassRepartitioning", "Bool",   None),
    ("hmrRatio",                   "Double", None),
    ("gammaT",                     "Double", "1/ps"),    # Langevin friction
)

#: R01's nested replica-exchange block (documented growth path; not authored in
#: the default conventional-production artifact). namespace ``bio:md:remd:``.
REMD_FIELDS = (
    ("remd:method",         "String",   None),
    ("remd:dimensions",     "Int",      None),
    ("remd:nReplicas",      "Int",      None),
    ("remd:exchangePeriod", "Int",      "steps"),
)

_ALL_SPECS = {suffix: (t, u) for suffix, t, u in
              (*CORE_FIELDS, *OPTIONAL_FIELDS, *REMD_FIELDS)}


# ---------------------------------------------------------------------------
# Reference values -- the project's planned p53-MDM2 production run, adopting
# the ShinobuLab GENESIS protocol that R01 extracted from the real decks.
#
# This is the GENERATOR's own default state. The read-back test does NOT assert
# against it; it asserts the authored USD against an INDEPENDENTLY-transcribed
# fixture (templates/fixtures/md_setup_reference.json). Every value carries a
# "source" tag: "[source: R01 ...]" for a value grounded in the survey, or
# "[assumption: ...]" for a value the survey does not fix.
# ---------------------------------------------------------------------------
DEFAULT_STARTING_STRUCTURE = "1YCR"  # p53-MDM2 crystal complex (committed 1ycr.pdb)

# value + per-field source tag. Units come from the field spec above.
DEFAULT_CORE: Dict[str, dict] = {
    "engine":              {"value": "GENESIS",
                            "source": "[source: R01 grounding -- ShinobuLab spdyn/GENESIS]"},
    "engineVersion":       {"value": "unknown",
                            "source": "[source: R01 -- version not in .inp decks; capture from job env]"},
    "forceField":          {"value": "AMBER ff19SB",
                            "source": "[source: R01 core table -- forcefield=AMBER]"},
    "waterModel":          {"value": "TIP3P",
                            "source": "[source: R01 core table -- Amber WAT residue => TIP3P]"},
    "ensemble":            {"value": "NVT",
                            "source": "[source: R01 -- production & REUS ensemble=NVT]"},
    "integrator":          {"value": "VRES",
                            "source": "[source: R01 -- RESPA multiple-timestep integrator]"},
    "timestep":            {"value": 0.0035,
                            "source": "[source: R01 -- 3.5 fs, HMR-enabled]"},
    "nSteps":              {"value": 600000,
                            "source": "[source: R01 -- 600000 steps per production run]"},
    "temperature":         {"value": 310.0,
                            "source": "[source: R01 -- temperature=310.0 K]"},
    "thermostat":          {"value": "Bussi",
                            "source": "[source: R01 -- tpcontrol=BUSSI]"},
    "barostat":            {"value": "Bussi",
                            "source": "[source: R01 -- BUSSI barostat (NPT equilibration)]"},
    "pressure":            {"value": 1.0,
                            "source": "[source: R01 -- pressure=1.0 atm]"},
    "electrostatics":      {"value": "PME",
                            "source": "[source: R01 -- electrostatic=PME]"},
    "cutoff":              {"value": 8.0,
                            "source": "[source: R01 -- cutoffdist=8.0 Angstrom]"},
    "constraintAlgorithm": {"value": "SHAKE",
                            "source": "[source: R01 -- rigid_bond=YES (SHAKE)]"},
    # --- PI-promoted to CORE (Q-003) ---
    "ionConcentration":    {"value": 0.15,
                            "source": "[assumption: physiological 0.15 mol/L NaCl for a solvated "
                                      "p53-MDM2 setup; not fixed by R01/ShinobuLab decks]"},
    "protonationState":    {"value": "standard states at pH 7.0 (Amber default protonation)",
                            "source": "[assumption: standard-state protonation at physiological pH; "
                                      "not specified in R01 decks]"},
}

DEFAULT_OPTIONAL: Dict[str, dict] = {
    "ionSpecies":                 {"value": "NaCl",
                                   "source": "[assumption: NaCl neutralisation, companion to ionConcentration]"},
    "boxType":                    {"value": "PBC",
                                   "source": "[source: R01 -- type=PBC]"},
    "pairlistDist":               {"value": 10.0,
                                   "source": "[source: R01 -- pairlistdist=10.0 Angstrom]"},
    "dispersionCorrection":       {"value": "EPRESS",
                                   "source": "[source: R01 -- dispersion_corr=EPRESS]"},
    "hydrogenMassRepartitioning": {"value": True,
                                   "source": "[source: R01 -- hydrogen_mr=YES]"},
    "hmrRatio":                   {"value": 3.0,
                                   "source": "[source: R01 -- hmr_ratio=3.0]"},
    "gammaT":                     {"value": 1.0,
                                   "source": "[source: R01 -- gamma_t=1.0 ps^-1]"},
}


# ---------------------------------------------------------------------------
# Authoring
# ---------------------------------------------------------------------------
def _value_type_names():
    """Return the {spec-name: Sdf.ValueTypeName} map (local pxr import)."""
    from pxr import Sdf
    return {
        "String": Sdf.ValueTypeNames.String,
        "Token":  Sdf.ValueTypeNames.Token,
        "Double": Sdf.ValueTypeNames.Double,
        "Int":    Sdf.ValueTypeNames.Int,
        "Int64":  Sdf.ValueTypeNames.Int64,
        "Bool":   Sdf.ValueTypeNames.Bool,
    }


def _author_field(prim, suffix: str, entry: dict) -> None:
    """Author one ``bio:md:<suffix>`` attribute with unit + source customData."""
    type_name, unit = _ALL_SPECS[suffix]
    vtypes = _value_type_names()
    attr = prim.CreateAttribute(MD_NS + suffix, vtypes[type_name])
    attr.Set(entry["value"])
    custom = {"source": entry["source"]}
    if unit is not None:
        custom["unit"] = unit
    attr.SetCustomData(custom)


def author_md_setup(
    stage,
    *,
    root_path: Optional[str] = None,
    core: Optional[Dict[str, dict]] = None,
    optional: Optional[Dict[str, dict]] = None,
    starting_structure: str = DEFAULT_STARTING_STRUCTURE,
    provenance_record: Optional[dict] = None,
    remd: Optional[Dict[str, dict]] = None,
):
    """Author the ``mdSetup`` prim and its ``bio:md:`` parameters onto *stage*.

    Args:
        stage: an open ``Usd.Stage`` (the Protocol layer).
        root_path: complex root prim path (PARAMETER; default
            :data:`p53_env.DEFAULT_ROOT_PATH`).
        core: {suffix: {"value", "source"}} for the CORE set. Every CORE suffix
            in :data:`CORE_FIELDS` must be present (the core is mandatory by
            definition). Defaults to :data:`DEFAULT_CORE`.
        optional: {suffix: {...}} for OPTIONAL fields to author (subset of
            :data:`OPTIONAL_FIELDS`). Defaults to :data:`DEFAULT_OPTIONAL`.
        starting_structure: value for ``bio:md:startingStructure`` (the anchor
            back to the source structure, per R01).
        provenance_record: optional six-field dict for
            :func:`composition.provenance.apply_provenance_metadata`.
        remd: optional {suffix: {...}} nested replica-exchange block. Authored
            only when supplied (no fabricated ladder in the default artifact).

    Returns:
        the ``mdSetup`` ``Usd.Prim``.

    Raises:
        ValueError: if a mandatory CORE field is missing, or an unknown suffix
            is supplied.
    """
    from pxr import Sdf  # noqa: F401  (ensures pxr is importable early)

    if root_path is None:
        root_path = p53_env.DEFAULT_ROOT_PATH
    core = DEFAULT_CORE if core is None else core
    optional = DEFAULT_OPTIONAL if optional is None else optional

    missing = [s for s, _t, _u in CORE_FIELDS if s not in core]
    if missing:
        raise ValueError(f"author_md_setup: missing mandatory CORE fields: {missing}")

    setup_path = f"{root_path}/{MD_SETUP_PRIM_NAME}"
    setup_prim = stage.DefinePrim(setup_path, MD_SETUP_PRIM_TYPE)

    # startingStructure anchor (R01: the provenance carry-over back to the PDB).
    from pxr import Sdf as _Sdf
    setup_prim.CreateAttribute(
        MD_NS + "startingStructure", _Sdf.ValueTypeNames.String
    ).Set(starting_structure)

    # CORE (mandatory) -- authored in the fixed CORE_FIELDS order.
    for suffix, _t, _u in CORE_FIELDS:
        _author_field(setup_prim, suffix, core[suffix])

    # OPTIONAL -- only the supplied subset.
    for suffix, _t, _u in OPTIONAL_FIELDS:
        if suffix in optional:
            _author_field(setup_prim, suffix, optional[suffix])

    # REMD nested block -- only when a real spec is supplied.
    if remd:
        for suffix, entry in remd.items():
            if suffix not in _ALL_SPECS:
                raise ValueError(f"author_md_setup: unknown remd suffix {suffix!r}")
            _author_field(setup_prim, suffix, entry)

    # Provenance (reuse -- do not re-invent).
    if provenance_record is not None:
        from p53_mdm2.composition.provenance import apply_provenance_metadata
        apply_provenance_metadata(setup_prim, provenance_record)

    return setup_prim


def default_provenance_record(timestamp: str = "unknown") -> dict:
    """A six-field provenance record for the default parameter deck.

    Records that the parameters were adopted from the ShinobuLab GENESIS
    protocol (via R01), honestly marking the un-fixed software version.
    """
    return {
        "sourcePdb": DEFAULT_STARTING_STRUCTURE,
        "forceField": DEFAULT_CORE["forceField"]["value"],
        "softwareName": DEFAULT_CORE["engine"]["value"],
        "softwareVersion": DEFAULT_CORE["engineVersion"]["value"],
        "simSettings": "R01 ShinobuLab GENESIS reference protocol "
                       "(NVT production, VRES, PME, SHAKE, BUSSI 310K)",
        "timestamp": timestamp,
    }


def build_md_setup_artifact(
    output_path: Optional[str] = None,
    *,
    root_path: Optional[str] = None,
    topology_sublayer: Optional[str] = "p53_mdm2_topology.usda",
) -> str:
    """Build the committed ``bio:md:`` Protocol-layer artifact.

    The layer ``subLayers`` the Biology topology (when present next to it), so
    the ``mdSetup`` prim composes onto the same complex root -- a working
    demonstration of the departmental-layering pattern (Protocol over Biology).

    Args:
        output_path: destination .usda (default: output/p53_mdm2_md_setup.usda).
        root_path: complex root path (default :data:`p53_env.DEFAULT_ROOT_PATH`).
        topology_sublayer: relative path to the Biology topology layer to
            subLayer, or ``None`` to author a standalone Protocol layer.

    Returns:
        ``output_path``.
    """
    from pxr import Usd, UsdGeom, Sdf

    if output_path is None:
        output_path = os.path.join(p53_env.output_dir(), "p53_mdm2_md_setup.usda")
    if root_path is None:
        root_path = p53_env.DEFAULT_ROOT_PATH

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, p53_env.METERS_PER_UNIT)
    stage.SetMetadata(
        "comment",
        "p53-MDM2 MD-setup parameters (bio:md:) -- Protocol departmental layer. "
        "CORE = R01 reproducible set + PI-promoted ionConcentration & "
        "protonationState (Q-003). Values tagged [source: R01] or [assumption:].")

    # SubLayer the Biology topology so mdSetup composes onto the same root.
    if topology_sublayer:
        topo_abs = os.path.join(os.path.dirname(os.path.abspath(output_path)),
                                topology_sublayer)
        if os.path.isfile(topo_abs):
            stage.GetRootLayer().subLayerPaths.append("./" + topology_sublayer)

    # Root prim (Xform, matches the topology's root type) + defaultPrim.
    root_prim = UsdGeom.Xform.Define(stage, root_path).GetPrim()
    stage.SetDefaultPrim(root_prim)

    author_md_setup(
        stage,
        root_path=root_path,
        provenance_record=default_provenance_record(),
    )

    stage.GetRootLayer().Save()
    print(f"[md_parameters] Written: {output_path}")
    print(f"  root: {root_path}  prim: {root_path}/{MD_SETUP_PRIM_NAME} ({MD_SETUP_PRIM_TYPE})")
    print(f"  core fields: {len(CORE_FIELDS)}  optional: {len(DEFAULT_OPTIONAL)}")
    if topology_sublayer:
        print(f"  subLayer: ./{topology_sublayer}")
    return output_path


def default_output_path() -> str:
    """Canonical committed location for the MD-setup artifact."""
    return os.path.join(p53_env.output_dir(), "p53_mdm2_md_setup.usda")


if __name__ == "__main__":
    path = build_md_setup_artifact()
    print(f"[md_parameters] Done. Inspect with:  usdcat --flatten {path}")
