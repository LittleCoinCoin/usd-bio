#!/usr/bin/env python3
"""
gromacs_deck.py -- USD stage -> GROMACS deck (``.mdp`` per stage + ``prep.env``).

Closes the p1b round-trip gate ("parameters written to USD read back and
reconstruct a runnable MD input"): every value in the emitted deck is read from
the COMPOSED USD stage, never from the Python defaults in
:mod:`p53_mdm2.templates.md_parameters`. A deck is reproducible from the stage
plus this file, and nothing else.

What it reads:
    ``<defaultPrim>/mdSetup``                 the production deck (CORE + OPTIONAL)
    ``<defaultPrim>/mdSetup/protocol/<name>`` ordered stages; an attribute the
                                              stage does not author falls back to
                                              ``mdSetup`` (the resolution rule)

What it writes (into one directory):
    ``<name>.mdp`` per stage                  grompp input
    ``prep.env``                              shell assignments for system prep
                                              (pdb2gmx/editconf/solvate/genion),
                                              sourced by cluster/p53_md/p53_md_run.sh

Units are converted from the unit each attribute DECLARES in
``customData["unit"]`` -- never assumed. USD carries Angstrom (stage
``metersPerUnit = 1e-10``) and atm; GROMACS wants nm and bar. An attribute with
an unexpected unit is a hard error, not a silent pass-through.

Engine-mapping constants (the only values this file contributes, all
structural rather than physical): ``cutoff-scheme = Verlet`` (required for GPU
nonbondeds), ``tc-grps = System``, ``pcoupltype = isotropic``,
``refcoord-scaling = com`` under restrained pressure coupling, and the
force-field / water / ion name tables below.
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)                  # examples/p53_mdm2
_PKG_PARENT = os.path.dirname(_PKG)            # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from p53_mdm2.templates.md_parameters import (  # noqa: E402
    MD_NS, MD_SETUP_PRIM_NAME, MD_PROTOCOL_PRIM_NAME, gromacs_output_path,
)

#: Committed location of the emitted deck (consumed by the Slurm job).
DEFAULT_DECK_DIR = os.path.join(_PKG, "cluster", "p53_md")

# --- explicit unit conversions ---------------------------------------------
_TO_NM = {"angstrom": 0.1, "nm": 1.0}
_TO_BAR = {"atm": 1.01325, "bar": 1.0}          # 1 atm = 1.01325 bar (exact)
_TO_PS = {"ps": 1.0, "fs": 0.001}

# --- name tables: USD value -> GROMACS token --------------------------------
_FORCE_FIELDS = {"AMBER99SB-ILDN": "amber99sb-ildn"}
_WATER_MODELS = {"TIP3P": ("tip3p", "spc216.gro")}   # 3-site box for 3-site water
_ION_SPECIES = {"NaCl": ("NA", "CL")}                 # amber99sb-ildn ions.itp names
_THERMOSTATS = {"V-rescale", "Nose-Hoover", "Berendsen"}
_BAROSTATS = {"C-rescale", "Parrinello-Rahman", "Berendsen"}
_MINIMISERS = {"steep", "cg", "l-bfgs"}
_BOX_SHAPES = {"cubic", "triclinic", "dodecahedron", "octahedron"}


class DeckError(ValueError):
    """The stage does not describe a deck this emitter can write faithfully."""


# ---------------------------------------------------------------------------
# Read the composed stage
# ---------------------------------------------------------------------------
def _read_prim(prim) -> Dict[str, Tuple[object, object]]:
    """{suffix: (value, unit)} for every authored ``bio:md:`` attribute."""
    out = {}
    for attr in prim.GetAttributes():
        name = attr.GetName()
        if name.startswith(MD_NS) and attr.HasAuthoredValue():
            out[name[len(MD_NS):]] = (attr.Get(), attr.GetCustomData().get("unit"))
    return out


def read_md_deck(stage_path: str) -> dict:
    """Read ``mdSetup`` and its ordered stages from the composed stage.

    Returns ``{"stage_path", "setup_path", "base": {...}, "stages": [(name, {...})]}``
    with every field as ``(value, unit)``.
    """
    from pxr import Usd
    stage = Usd.Stage.Open(stage_path)
    if stage is None:
        raise DeckError(f"cannot open {stage_path}")
    root = stage.GetDefaultPrim()
    if not root or not root.IsValid():
        raise DeckError(f"{stage_path}: no defaultPrim")
    setup = root.GetChild(MD_SETUP_PRIM_NAME)
    if not setup or not setup.IsValid():
        raise DeckError(f"{stage_path}: no {MD_SETUP_PRIM_NAME} under {root.GetPath()}")
    protocol = setup.GetChild(MD_PROTOCOL_PRIM_NAME)
    if not protocol or not protocol.IsValid():
        raise DeckError(f"{setup.GetPath()}: no {MD_PROTOCOL_PRIM_NAME} stages")
    stages = [(child.GetName(), _read_prim(child)) for child in protocol.GetChildren()]
    if not stages:
        raise DeckError(f"{protocol.GetPath()}: no stages")
    return {"stage_path": stage_path, "setup_path": str(setup.GetPath()),
            "base": _read_prim(setup), "stages": stages}


def resolve_stage(deck: dict, stage_name: str) -> Dict[str, Tuple[object, object]]:
    """Stage fields over ``mdSetup`` fields (the documented fallback rule)."""
    for name, fields in deck["stages"]:
        if name == stage_name:
            merged = dict(deck["base"])
            merged.update(fields)
            return merged
    raise DeckError(f"no stage {stage_name!r}")


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------
def _need(fields, suffix):
    if suffix not in fields:
        raise DeckError(f"missing bio:md:{suffix}")
    return fields[suffix]


def _convert(fields, suffix, table, what):
    value, unit = _need(fields, suffix)
    if unit not in table:
        raise DeckError(f"bio:md:{suffix}: unit {unit!r} is not a {what} unit {sorted(table)}")
    return float(value) * table[unit]


def _num(x) -> str:
    """Deterministic mdp number text (10 significant digits, no float noise)."""
    if isinstance(x, bool):
        raise DeckError("boolean where a number was expected")
    if isinstance(x, int):
        return str(x)
    return format(float(x), ".10g")


def _choice(fields, suffix, allowed):
    value = str(_need(fields, suffix)[0])
    if value not in allowed:
        raise DeckError(f"bio:md:{suffix}={value!r} not in {sorted(allowed)}")
    return value


def _flag(fields, suffix) -> bool:
    return bool(fields.get(suffix, (False, None))[0])


# ---------------------------------------------------------------------------
# Emit
# ---------------------------------------------------------------------------
def mdp_pairs(fields: dict) -> List[Tuple[str, str]]:
    """Ordered ``(mdp-key, value-text)`` pairs for one resolved stage."""
    if str(_need(fields, "engine")[0]) != "GROMACS":
        raise DeckError(f"bio:md:engine={fields['engine'][0]!r}; this emitter writes GROMACS")
    if str(_need(fields, "boxType")[0]) != "PBC":
        raise DeckError("only boxType=PBC is supported")
    if str(_need(fields, "electrostatics")[0]) != "PME":
        raise DeckError("only electrostatics=PME is supported")

    integrator = str(_need(fields, "integrator")[0])
    minimise = integrator in _MINIMISERS
    restrained = _flag(fields, "positionRestraints")
    pairs: List[Tuple[str, str]] = []
    add = lambda k, v: pairs.append((k, v))  # noqa: E731

    if restrained:
        add("define", "-DPOSRES")
    add("integrator", integrator)
    add("nsteps", _num(int(_need(fields, "nSteps")[0])))
    if minimise:
        tol, unit = _need(fields, "emTolerance")
        if unit != "kJ/mol/nm":
            raise DeckError(f"bio:md:emTolerance unit {unit!r} != 'kJ/mol/nm'")
        add("emtol", _num(float(tol)))
    else:
        if integrator != "md":
            raise DeckError(f"integrator {integrator!r} not supported")
        add("dt", _num(_convert(fields, "timestep", _TO_PS, "time")))

    # non-bonded
    add("cutoff-scheme", "Verlet")
    add("pbc", "xyz")
    add("coulombtype", "PME")
    rc = _num(_convert(fields, "cutoff", _TO_NM, "length"))
    add("rcoulomb", rc)
    add("rvdw", rc)
    add("fourierspacing", _num(_convert(fields, "pmeGridSpacing", _TO_NM, "length")))
    add("DispCorr", str(_need(fields, "dispersionCorrection")[0]))

    # constraints
    bonds = _choice(fields, "constrainedBonds", {"none", "h-bonds", "all-bonds"})
    add("constraints", bonds)
    if bonds != "none":
        add("constraint-algorithm", str(_need(fields, "constraintAlgorithm")[0]).lower())

    if not minimise:
        seed = _num(int(_need(fields, "randomSeed")[0]))
        temp = _num(float(_need(fields, "temperature")[0]))
        gen = _flag(fields, "generateVelocities")
        add("continuation", "no" if gen else "yes")
        add("gen-vel", "yes" if gen else "no")
        if gen:
            add("gen-temp", temp)
            add("gen-seed", seed)
        add("tcoupl", _choice(fields, "thermostat", _THERMOSTATS))
        add("tc-grps", "System")
        add("tau-t", _num(_convert(fields, "thermostatTau", _TO_PS, "time")))
        add("ref-t", temp)
        add("ld-seed", seed)
        ensemble = _choice(fields, "ensemble", {"NVT", "NPT"})
        if ensemble == "NPT":
            add("pcoupl", _choice(fields, "barostat", _BAROSTATS))
            add("pcoupltype", "isotropic")
            add("tau-p", _num(_convert(fields, "barostatTau", _TO_PS, "time")))
            add("ref-p", _num(_convert(fields, "pressure", _TO_BAR, "pressure")))
            comp, unit = _need(fields, "compressibility")
            if unit != "1/bar":
                raise DeckError(f"bio:md:compressibility unit {unit!r} != '1/bar'")
            add("compressibility", _num(float(comp)))
            if restrained:
                add("refcoord-scaling", "com")
        else:
            add("pcoupl", "no")

    out = _num(int(_need(fields, "outputInterval")[0]))
    add("nstenergy", out)
    add("nstlog", out)
    if not minimise:
        add("nstxout-compressed", _num(int(_need(fields, "trajectoryInterval")[0])))
    return pairs


def _header(deck: dict, what: str, c: str = ";") -> str:
    src = os.path.basename(deck["stage_path"])
    return (f"{c} GENERATED by examples/p53_mdm2/templates/gromacs_deck.py -- DO NOT EDIT.\n"
            f"{c} {what}\n"
            f"{c} source: {src} {deck['setup_path']} (bio:md:, composed stage)\n"
            f"{c} regenerate: python examples/p53_mdm2/templates/gromacs_deck.py\n")


def mdp_text(deck: dict, stage_name: str) -> str:
    pairs = mdp_pairs(resolve_stage(deck, stage_name))
    width = max(len(k) for k, _v in pairs)
    body = "".join(f"{k:<{width}} = {v}\n" for k, v in pairs)
    return (_header(deck, f"stage '{stage_name}' = {deck['setup_path']}/"
                          f"{MD_PROTOCOL_PRIM_NAME}/{stage_name} over mdSetup")
            + "\n" + body)


def prep_env_text(deck: dict) -> str:
    """Shell assignments for system preparation, from the production deck."""
    base = deck["base"]
    ff = str(_need(base, "forceField")[0])
    water = str(_need(base, "waterModel")[0])
    ions = str(_need(base, "ionSpecies")[0])
    if ff not in _FORCE_FIELDS:
        raise DeckError(f"forceField {ff!r} has no GROMACS mapping {sorted(_FORCE_FIELDS)}")
    if water not in _WATER_MODELS:
        raise DeckError(f"waterModel {water!r} has no GROMACS mapping")
    if ions not in _ION_SPECIES:
        raise DeckError(f"ionSpecies {ions!r} has no GROMACS mapping")
    conc, unit = _need(base, "ionConcentration")
    if unit != "mol/L":
        raise DeckError(f"ionConcentration unit {unit!r} != 'mol/L'")
    water_tok, solvent_box = _WATER_MODELS[water]
    pname, nname = _ION_SPECIES[ions]
    lines = [
        ("FORCE_FIELD", _FORCE_FIELDS[ff]),
        ("WATER_MODEL", water_tok),
        ("SOLVENT_BOX", solvent_box),
        ("BOX_SHAPE", _choice(base, "boxShape", _BOX_SHAPES)),
        ("BOX_DISTANCE_NM", _num(_convert(base, "soluteBoxDistance", _TO_NM, "length"))),
        ("ION_POSITIVE", pname),
        ("ION_NEGATIVE", nname),
        ("ION_CONCENTRATION_MOLAR", _num(float(conc))),
        ("STAGES", " ".join(name for name, _f in deck["stages"])),
    ]
    body = "".join(f"{k}='{v}'\n" for k, v in lines)
    return _header(deck, "system preparation, sourced by p53_md_run.sh", c="#") + "\n" + body


def emit_deck(stage_path: str = None, out_dir: str = None) -> List[str]:
    """Write ``<stage>.mdp`` for every stage plus ``prep.env``; return paths."""
    stage_path = stage_path or gromacs_output_path()
    out_dir = out_dir or DEFAULT_DECK_DIR
    deck = read_md_deck(stage_path)
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for name, _fields in deck["stages"]:
        path = os.path.join(out_dir, f"{name}.mdp")
        with open(path, "w") as fh:
            fh.write(mdp_text(deck, name))
        written.append(path)
    path = os.path.join(out_dir, "prep.env")
    with open(path, "w") as fh:
        fh.write(prep_env_text(deck))
    written.append(path)
    return written


if __name__ == "__main__":
    for p in emit_deck(*sys.argv[1:3]):
        print(f"[gromacs_deck] Written: {p}")
