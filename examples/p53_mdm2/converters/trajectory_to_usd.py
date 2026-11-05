#!/usr/bin/env python3
"""
trajectory_to_usd.py -- MD trajectory (GROMACS .xtc + .gro) -> OpenUSD Dynamics layer.

The p53-MDM2 MD -> USD path for one GROMACS production run committed under
``data/md_runs/<run>/`` (default: ``p53_env.DEFAULT_MD_RUN``). Every run-specific
name is derived from the run, never hard-coded: the ``run_id`` is ``--run-id`` if
given, else ``job<job_id>`` from the run's ``manifest.jsonl``. Two layers are
written:

    output/p53_mdm2_dynamics_<run_id>.usda          (light: the Dynamics department)
        /p53_MDM2_complex/dynamics                  Scope, bio:md: run provenance
            trajectory                              Xform, PAYLOAD -> frames layer
    output/p53_mdm2_dynamics_<run_id>_frames.usda   (heavy: loaded on demand)
        /trajectory
            chain_A, chain_B                        Points, time-sampled `points`
            ions                                    Points, time-sampled `points`

Design choices (each is recorded on the stage as a ``bio:md:`` attribute):

- **Payload, not Value Clips.** The P arc is the design doc's "raw data loaded
  on demand"; opening the Dynamics layer with ``Usd.Stage.LoadNone`` costs no
  frame data. Value Clips earn their keep when a trajectory must be chunked
  across many files; 11 frames fit in one modest layer, so clips would add a
  manifest and clip-time bookkeeping for no read-back benefit. They remain the
  growth path for long trajectories.
- **One ``Points`` prim per molecule group**, not one prim per atom (v8 wrote an
  Xform per atom plus per-bond cylinders; that is what makes v8 clips heavy).
  Per-point ``bio:md:atomNames`` / ``bio:md:residueNumbers`` /
  ``bio:md:residueNames`` (raw GROMACS names from the .gro, not mdtraj's
  standardised ones) and a CPK ``primvars:displayColor`` keep each point
  identifiable.
- **Atom selection: protein + ions; waters omitted.** Waters are ~90% of the
  system and carry no biology here. Counts of what was dropped are recorded.
- **Time codes are picoseconds** (the xtc time stamps, t = 0..100 ps), so a time
  code reads directly as simulated time. ``timeCodesPerSecond`` only sets the
  playback rate; it is authored identically on both layers, because USD rescales
  a payloaded layer whose rate differs from the stage's.
- **Angstrom, made whole.** mdtraj returns nm; positions are x10 and rounded to
  0.01 A, which is the xtc's own 0.001 nm precision (lossless up to box-vector
  arithmetic). The raw xtc is PBC-wrapped -- molecules are split across the box
  and atoms jump between frames -- so each chain is unwrapped atom-by-atom
  (minimum image against the previous atom in file order), chain B is imaged
  next to chain A, and every group is made continuous in time. No fitting or
  centering is applied: coordinates stay in the MD box frame, not the 1YCR
  crystal frame. Alignment to the crystal frame is an INTEGRATION concern: the
  integrated stage places this layer under ONE rigid ``xformOp:transform``
  (``composition/dynamics_alignment.py``), so the raw frames are never refitted.

No dataset counts are hard-coded here; everything is read from the run files.
The converter refuses to write if a source file's sha256 disagrees with the
run's ``manifest.jsonl``.

Regenerate (from the repo root):
    PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples" \\
        ~/Documents/src/AOUSD/forOUSD/bin/python3 \\
        examples/p53_mdm2/converters/trajectory_to_usd.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_PKG_PARENT = os.path.dirname(_PKG)
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from p53_mdm2 import p53_env
from p53_mdm2.data import ELEMENTS, IONS

RUN_DIR = p53_env.default_md_run_dir()

TIME_CODES_PER_SECOND = 10.0      # playback only: 10 ps of MD per second
ION_RESNAMES = ("NA", "CL")       # GROMACS ion residue names in this deck
_ION_KEYS = {"NA": "Na+", "CL": "Cl-"}  # -> data.ion_properties keys
POSITION_DECIMALS = 2             # 0.01 A == the xtc's 0.001 nm precision

FORCE_FIELD_STATUS = (
    "plumbing run: AMBER99SB-ILDN/TIP3P accepted to exercise the pipeline, GPU "
    "path and USD read-back, NOT for scientific claims; revisit ff14SB/ff19SB "
    "before any scientific use (PI answer to Q-017, 2026-10-20)")


# --- run identity ------------------------------------------------------------

def run_id_from_manifest(manifest):
    """``job<job_id>`` from the run's manifest (the xtc record's ``job_id``)."""
    return f"job{manifest['md.xtc']['job_id']}"


def output_names(run_id):
    """(dynamics layer, frames layer) file names for *run_id*."""
    return (f"p53_mdm2_dynamics_{run_id}.usda",
            f"p53_mdm2_dynamics_{run_id}_frames.usda")


def default_output_paths(run_dir=RUN_DIR, out_dir=None, run_id=None):
    """{"dynamics": path, "frames": path} the converter writes for *run_dir*."""
    run_id = run_id or run_id_from_manifest(read_manifest(run_dir))
    dyn, frames = output_names(run_id)
    out_dir = out_dir or p53_env.output_dir()
    return {"dynamics": os.path.join(out_dir, dyn),
            "frames": os.path.join(out_dir, frames)}


# --- source files ------------------------------------------------------------

def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(run_dir):
    """{file: record} from the run's manifest.jsonl."""
    out = {}
    with open(os.path.join(run_dir, "manifest.jsonl")) as fh:
        for line in fh:
            if line.strip():
                rec = json.loads(line)
                out[rec["file"]] = rec
    return out


def read_summary(run_dir):
    """KEY=VALUE pairs of the container's summary.txt."""
    out = {}
    with open(os.path.join(run_dir, "summary.txt")) as fh:
        for line in fh:
            k, sep, v = line.strip().partition("=")
            if sep:
                out[k] = v
    return out


def engine_version(run_dir):
    """GROMACS version from the pdb2gmx banner in topol.top (same container)."""
    with open(os.path.join(run_dir, "topol.top")) as fh:
        m = re.search(r"GROMACS - gmx \w+, (\S+)", fh.read())
    return m.group(1) if m else "unknown"


def verify_sources(run_dir, manifest, names=("md.xtc", "md.gro", "topol.top",
                                             "summary.txt")):
    """sha256 of each source vs the manifest; raise on any mismatch."""
    digests = {}
    for name in names:
        actual = _sha256(os.path.join(run_dir, name))
        if manifest.get(name, {}).get("sha256") != actual:
            raise ValueError(f"{name}: sha256 {actual} disagrees with manifest.jsonl")
        digests[name] = actual
    return digests


# --- PBC handling ------------------------------------------------------------

def _min_image(d, box):
    """Minimum-image displacement(s) for a GROMACS triclinic box.

    ``box`` rows are the box vectors a, b, c (lower-triangular, GROMACS
    convention). Reducing along c, then b, then a is exact for displacements
    well under half the shortest box height, which is all this module asks of it.
    """
    a, b, c = box
    d = d - np.outer(np.round(d[..., 2] / c[2]), c).reshape(d.shape)
    d = d - np.outer(np.round(d[..., 1] / b[1]), b).reshape(d.shape)
    d = d - np.outer(np.round(d[..., 0] / a[0]), a).reshape(d.shape)
    return d


def _make_whole(xyz, box):
    """Unwrap one molecule in one frame: each atom min-imaged to its predecessor."""
    steps = _min_image(np.diff(xyz, axis=0), box)
    return np.vstack([xyz[:1], xyz[:1] + np.cumsum(steps, axis=0)])


def unwrap(xyz, boxes, groups):
    """Make chains whole, keep chain B next to chain A, remove time jumps.

    xyz: (n_frames, n_atoms, 3) nm; boxes: (n_frames, 3, 3) nm;
    groups: {"chain_A": idx, "chain_B": idx, "ions": idx} (atom index arrays).
    Returns {group: (n_frames, n_group_atoms, 3)} in nm.
    """
    out = {}
    chains = [g for g in groups if g.startswith("chain_")]
    for g in chains:
        out[g] = np.stack([_make_whole(xyz[f, groups[g]], boxes[f])
                           for f in range(len(xyz))])
    out["ions"] = xyz[:, groups["ions"]].copy()
    for f in range(len(xyz)):
        anchor = out[chains[0]][f].mean(axis=0)
        for g in chains[1:]:
            shift = _min_image(out[g][f].mean(axis=0) - anchor, boxes[f]) \
                - (out[g][f].mean(axis=0) - anchor)
            out[g][f] += shift
        if f == 0:
            continue
        # time continuity: the anchor chain follows its own previous centroid,
        # the other chains move with it, each ion follows its own previous spot
        prev = out[chains[0]][f - 1].mean(axis=0)
        jump = _min_image(anchor - prev, boxes[f]) - (anchor - prev)
        for g in chains:
            out[g][f] += jump
        d = out["ions"][f] - out["ions"][f - 1]
        out["ions"][f] += _min_image(d, boxes[f]) - d
    return out


# --- topology ----------------------------------------------------------------

def gro_names(gro_path):
    """Raw GROMACS (residue name, atom name) per atom, by .gro fixed columns.

    mdtraj standardises names on load (H1 -> H, SOL -> HOH); the stage carries
    the names exactly as the engine wrote them.
    """
    with open(gro_path) as fh:
        fh.readline()
        n = int(fh.readline())
        rows = [fh.readline() for _ in range(n)]
    return [(r[5:10].strip(), r[10:15].strip()) for r in rows]


def select_groups(topology):
    """Atom index arrays per group; chains split where the residue number drops.

    A .gro carries no chain column, so mdtraj reports one chain. The protein
    chains are recovered from the residue numbering restarting (e.g. ...109, 17...).
    """
    protein = topology.select("protein")
    chains, current, last_resseq = [], [], None
    for i in protein:
        rs = topology.atom(int(i)).residue.resSeq
        if last_resseq is not None and rs < last_resseq:
            chains.append(current)
            current = []
        current.append(int(i))
        last_resseq = rs
    chains.append(current)
    groups = {f"chain_{chr(ord('A') + k)}": np.array(c) for k, c in enumerate(chains)}
    sel = " or ".join(f"resname {r}" for r in ION_RESNAMES)
    groups["ions"] = topology.select(sel)
    return groups


def _color(atom):
    rn = atom.residue.name
    if rn in _ION_KEYS and _ION_KEYS[rn] in IONS:
        return IONS[_ION_KEYS[rn]]["cpk_color"]
    sym = atom.element.symbol if atom.element is not None else ""
    return ELEMENTS.get(sym, ELEMENTS["C"])["cpk_color"]


# --- USD authoring -----------------------------------------------------------

def _stage_metadata(stage, start, end, doc):
    from pxr import UsdGeom
    UsdGeom.SetStageMetersPerUnit(stage, p53_env.METERS_PER_UNIT)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.SetStartTimeCode(start)
    stage.SetEndTimeCode(end)
    stage.SetTimeCodesPerSecond(TIME_CODES_PER_SECOND)
    stage.SetFramesPerSecond(TIME_CODES_PER_SECOND)
    stage.GetRootLayer().documentation = doc


def _new_stage(path):
    from pxr import Usd
    if os.path.exists(path):
        os.remove(path)
    return Usd.Stage.CreateNew(path)


def write_frames_layer(path, topology, names, groups, positions_A, times, run_label):
    """Heavy layer: one Points prim per group, `points` time-sampled in ps.

    *run_label* names the run in the layer doc, e.g. ``"<cluster> job <id>"``.
    """
    from pxr import Gf, Sdf, Usd, UsdGeom, Vt
    stage = _new_stage(path)
    _stage_metadata(stage, float(times[0]), float(times[-1]),
                    "Dynamics frames (payload target): protein chains + ions of "
                    f"{run_label}, positions in Angstrom, time codes in ps.")
    root = UsdGeom.Xform.Define(stage, "/trajectory")
    stage.SetDefaultPrim(root.GetPrim())
    for name, idx in groups.items():
        pts = UsdGeom.Points.Define(stage, f"/trajectory/{name}")
        atoms = [topology.atom(int(i)) for i in idx]
        prim = pts.GetPrim()
        prim.CreateAttribute("bio:md:atomNames", Sdf.ValueTypeNames.TokenArray) \
            .Set([names[int(i)][1] for i in idx])
        prim.CreateAttribute("bio:md:residueNames", Sdf.ValueTypeNames.TokenArray) \
            .Set([names[int(i)][0] for i in idx])
        prim.CreateAttribute("bio:md:residueNumbers", Sdf.ValueTypeNames.IntArray) \
            .Set([int(a.residue.resSeq) for a in atoms])
        pts.CreateDisplayColorPrimvar(UsdGeom.Tokens.vertex) \
            .Set([Gf.Vec3f(*_color(a)) for a in atoms])
        attr = pts.CreatePointsAttr()
        for f, t in enumerate(times):
            attr.Set(Vt.Vec3fArray.FromNumpy(
                positions_A[name][f].astype(np.float32)), Usd.TimeCode(float(t)))
    stage.Save()


def write_dynamics_layer(path, frames_name, root_path, times, provenance,
                         run_label):
    """Light Dynamics department layer: provenance + the payload arc.

    *run_label* names the run in the layer doc, e.g. ``"<cluster> job-<id>"``.
    """
    from pxr import Sdf, UsdGeom
    stage = _new_stage(path)
    _stage_metadata(stage, float(times[0]), float(times[-1]),
                    f"Dynamics layer (MD -> USD): the {run_label} GROMACS "
                    "production trajectory of p53-MDM2 (1YCR), protein + ions, "
                    "behind a Payload so frames load on demand. Plumbing run "
                    "(PI Q-017): not for scientific claims.")
    root = UsdGeom.Xform.Define(stage, root_path)
    stage.SetDefaultPrim(root.GetPrim())
    dyn = UsdGeom.Scope.Define(stage, f"{root_path}/dynamics").GetPrim()
    for key, (vtype, value) in provenance.items():
        dyn.CreateAttribute(f"bio:md:{key}", vtype).Set(value)
    traj = UsdGeom.Xform.Define(stage, f"{root_path}/dynamics/trajectory").GetPrim()
    traj.GetPayloads().AddPayload(f"./{frames_name}")
    stage.Save()


def convert(run_dir=RUN_DIR, out_dir=None, root_path=p53_env.DEFAULT_ROOT_PATH,
            run_id=None):
    """Full pipeline. Returns {"dynamics": path, "frames": path}.

    *run_id* defaults to ``job<job_id>`` from the run's manifest and only names
    the output files; the stage content is derived from the run files alone.
    """
    import mdtraj as md
    from pxr import Sdf

    out_dir = out_dir or p53_env.output_dir()
    manifest = read_manifest(run_dir)
    digests = verify_sources(run_dir, manifest)
    summary = read_summary(run_dir)

    gro = os.path.join(run_dir, "md.gro")
    traj = md.load(os.path.join(run_dir, "md.xtc"), top=gro)
    groups = select_groups(traj.topology)
    whole = unwrap(traj.xyz, traj.unitcell_vectors, groups)
    positions_A = {g: np.round(v * 10.0, POSITION_DECIMALS) for g, v in whole.items()}
    times = traj.time
    n_written = sum(len(v) for v in groups.values())
    interval = float(times[1] - times[0]) if len(times) > 1 else 0.0

    S, T, I, F = (Sdf.ValueTypeNames.String, Sdf.ValueTypeNames.Token,
                  Sdf.ValueTypeNames.Int, Sdf.ValueTypeNames.Double)
    job = manifest["md.xtc"]["job_id"]
    cluster = manifest["md.xtc"]["source"].split(":", 1)[0]
    paths = default_output_paths(run_dir, out_dir, run_id)
    frames_name = os.path.basename(paths["frames"])
    provenance = {
        "jobId": (S, job),
        "cluster": (T, cluster),
        "engine": (T, "GROMACS"),
        "engineVersion": (S, engine_version(run_dir)),
        "forceField": (T, summary.get("FORCE_FIELD", "unknown")),
        "waterModel": (T, summary.get("WATER_MODEL", "unknown")),
        "forceFieldStatus": (S, FORCE_FIELD_STATUS),
        "sourceXtc": (S, manifest["md.xtc"]["source"]),
        "sourceXtcSha256": (S, digests["md.xtc"]),
        "sourceGroSha256": (S, digests["md.gro"]),
        "sourceTopolSha256": (S, digests["topol.top"]),
        "sourceSummarySha256": (S, digests["summary.txt"]),
        "timeCodeUnit": (T, "ps"),
        "frameIntervalPs": (F, interval),
        "frameCount": (I, int(traj.n_frames)),
        "atomSelection": (S, "protein + ions (" + ", ".join(ION_RESNAMES)
                          + "); waters omitted"),
        "systemAtomCount": (I, int(traj.n_atoms)),
        "writtenAtomCount": (I, int(n_written)),
        "omittedAtomCount": (I, int(traj.n_atoms - n_written)),
        "positionUnit": (T, "angstrom"),
        "positionPrecisionAngstrom": (F, 10.0 ** -POSITION_DECIMALS),
        "pbcTreatment": (S, "chains made whole (per-atom minimum image), chain B "
                         "imaged to chain A, groups continuous in time; no fit"),
        "framesLayer": (S, frames_name),
    }

    names = gro_names(gro)
    if len(names) != traj.n_atoms:
        raise ValueError(f"md.gro lists {len(names)} atoms, md.xtc {traj.n_atoms}")
    write_frames_layer(paths["frames"], traj.topology, names, groups, positions_A,
                       times, f"{cluster} job {job}")
    write_dynamics_layer(paths["dynamics"], frames_name, root_path, times,
                         provenance, f"{cluster} job-{job}")
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run-dir", default=RUN_DIR)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--run-id", default=None,
                    help="names the output files; default job<job_id> from "
                         "the run's manifest.jsonl")
    args = ap.parse_args(argv)
    paths = convert(args.run_dir, args.out_dir, run_id=args.run_id)
    for k, p in paths.items():
        print(f"  {k:9s} {p} ({os.path.getsize(p)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
