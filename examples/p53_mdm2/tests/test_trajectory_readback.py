"""
Read-back checks for the MD -> USD Dynamics layer (banyan job 119).

Opens the COMMITTED `output/p53_mdm2_dynamics_job119.usda` (and its payload
`..._frames.usda`) fresh, and asserts it against oracles that do not go through
`converters/trajectory_to_usd.py` or mdtraj:

    frame grid      <- cluster/p53_md/md.mdp (nsteps, dt, nstxout-compressed)
    atom counts     <- summary.txt (own KEY=VALUE parse) and the md.gro header
    chain split     <- stated here: chain A MDM2 25-109 (85 res), chain B p53
                       17-29 (13 res) -- the 1YCR construct
    final frame     <- an independent fixed-column parse of md.gro (nm, x10)
    whole chains    <- physics: consecutive CA-CA <= 4.2 A (trans peptide 3.8 A)
    digests         <- hashlib over the files, and manifest.jsonl via json
    on-demand load  <- Usd.Stage.LoadNone vs LoadAll on the composed stage

Final-frame tolerance: gro is written to 0.001 nm, the xtc is quantised to
0.001 nm, and the stage rounds to 0.01 A after adding box vectors, so the
budget is ~3 x 0.005 A plus box-vector float error -> 0.02 A per component.
The xtc frame and md.gro may differ by a whole box vector per molecule
(GROMACS writes confout.gro with molecules made whole in its own image), so
the comparison is "same coordinates up to one lattice vector per chain/atom".

SELF-TEST ROW (`traj_falsification_selftest`): each pure-data family is re-run
on an in-memory mutated copy of its inputs and must go red; nothing on disk is
touched.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile

import numpy as np

try:
    from pxr import Sdf, Usd, UsdGeom
except ImportError:  # pragma: no cover
    Usd = None

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_RUN = os.path.join(_PKG, "data", "md_runs", "banyan_job119")
_MDP = os.path.join(_PKG, "cluster", "p53_md", "md.mdp")
_OUT = os.path.join(_PKG, "output")
_DYN = os.path.join(_OUT, "p53_mdm2_dynamics_job119.usda")
_FRAMES = os.path.join(_OUT, "p53_mdm2_dynamics_job119_frames.usda")

_ROOT = "/p53_MDM2_complex"
_SCOPE = f"{_ROOT}/dynamics"
_TRAJ = f"{_SCOPE}/trajectory"
_GROUPS = ("chain_A", "chain_B", "ions")

# --- stated expectations ------------------------------------------------------
_JOB_ID = "119"
_FORCE_FIELD, _WATER = "amber99sb-ildn", "tip3p"
_ENGINE_VERSION = "2025.3"            # topol.top pdb2gmx banner
_CHAIN_RESIDUES = {"chain_A": (25, 109), "chain_B": (17, 29)}   # 1YCR construct
_ATOMS_PER_WATER = 3                  # TIP3P
_TOL_A = 0.02                         # see module docstring
_CA_CA_MAX_A = 4.2
_BOUND_CENTROID_MAX_A = 20.0          # [assumption: peptide sits in the MDM2 cleft]
_MAX_STEP_A = 15.0                    # per 10 ps; a PBC jump is >= ~44 A here
_SOURCES = ("md.xtc", "md.gro", "topol.top", "summary.txt")
_SHA_ATTR = {"md.xtc": "sourceXtcSha256", "md.gro": "sourceGroSha256",
             "topol.top": "sourceTopolSha256", "summary.txt": "sourceSummarySha256"}


# --- independent oracles ------------------------------------------------------

def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_gro(path):
    """Plain fixed-column .gro parse: rows + box (nm). No mdtraj."""
    with open(path) as fh:
        lines = fh.read().splitlines()
    n = int(lines[1])
    rows = []
    for ln in lines[2:2 + n]:
        rows.append({"resnr": int(ln[0:5]), "resname": ln[5:10].strip(),
                     "atom": ln[10:15].strip(),
                     "xyz": (float(ln[20:28]), float(ln[28:36]), float(ln[36:44]))})
    v = [float(x) for x in lines[2 + n].split()]
    v += [0.0] * (9 - len(v))
    box = np.array([[v[0], v[3], v[4]], [v[5], v[1], v[6]], [v[7], v[8], v[2]]])
    return {"n_header": n, "rows": rows, "box": box}


def _gro_groups(gro):
    """Split gro rows: ions by resname, the rest (non-SOL) into chains wherever
    the residue number drops. Returns {group: [row, ...]}."""
    groups = {"ions": []}
    chain, last = 0, None
    for r in gro["rows"]:
        if r["resname"] == "SOL":
            continue
        if r["resname"] in ("NA", "CL"):
            groups["ions"].append(r)
            continue
        if last is not None and r["resnr"] < last:
            chain += 1
        last = r["resnr"]
        groups.setdefault(f"chain_{'AB'[chain]}", []).append(r)
    return groups


def _parse_kv(path, sep="="):
    out = {}
    with open(path) as fh:
        for line in fh:
            line = line.split(";", 1)[0].strip()
            k, s, v = line.partition(sep)
            if s:
                out[k.strip()] = v.strip()
    return out


def _load_oracle():
    manifest = {}
    with open(os.path.join(_RUN, "manifest.jsonl")) as fh:
        for line in fh:
            if line.strip():
                rec = json.loads(line)
                manifest[rec["file"]] = rec
    return {
        "gro": _parse_gro(os.path.join(_RUN, "md.gro")),
        "summary": _parse_kv(os.path.join(_RUN, "summary.txt")),
        "mdp": _parse_kv(_MDP),
        "manifest": manifest,
        "hashes": {f: _sha256(os.path.join(_RUN, f)) for f in _SOURCES},
    }


# --- stage read-back ----------------------------------------------------------

def _load_stage():
    """Composed stage, LoadAll. Returns plain data so checks stay pure."""
    stage = Usd.Stage.Open(_DYN, Usd.Stage.LoadAll)
    scope = stage.GetPrimAtPath(_SCOPE)
    attrs = {a.GetName().split("bio:md:", 1)[1]: a.Get()
             for a in scope.GetAttributes() if a.GetName().startswith("bio:md:")}
    groups = {}
    for g in _GROUPS:
        prim = stage.GetPrimAtPath(f"{_TRAJ}/{g}")
        if not prim.IsValid():
            continue
        pts = UsdGeom.Points(prim).GetPointsAttr()
        times = pts.GetTimeSamples()
        groups[g] = {
            "times": list(times),
            "xyz": np.array([np.array(pts.Get(t)) for t in times]),
            "atoms": list(prim.GetAttribute("bio:md:atomNames").Get()),
            "resnames": list(prim.GetAttribute("bio:md:residueNames").Get()),
            "resnrs": list(prim.GetAttribute("bio:md:residueNumbers").Get()),
        }
    return {"attrs": attrs, "groups": groups,
            "start": stage.GetStartTimeCode(), "end": stage.GetEndTimeCode()}


# --- pure checks: (stage_data, oracle) -> (errors, detail) ---------------------

def _check_sources(st, orc):
    errs = []
    for f in _SOURCES:
        h = orc["hashes"][f]
        if orc["manifest"].get(f, {}).get("sha256") != h:
            errs.append(f"{f}: file sha256 != manifest.jsonl")
        if st["attrs"].get(_SHA_ATTR[f]) != h:
            errs.append(f"{f}: stage {_SHA_ATTR[f]} != file sha256")
    return errs, {"files": len(_SOURCES)}


def _expected_times(mdp):
    nsteps, dt = int(mdp["nsteps"]), float(mdp["dt"])
    nout = int(mdp["nstxout-compressed"])
    return [float(round(k * nout * dt, 6)) for k in range(nsteps // nout + 1)]


def _check_time_grid(st, orc):
    exp = _expected_times(orc["mdp"])
    errs = []
    for g in _GROUPS:
        got = st["groups"].get(g, {}).get("times")
        if got != exp:
            errs.append(f"{g}: time samples {got} != mdp grid {exp}")
    if (st["start"], st["end"]) != (exp[0], exp[-1]):
        errs.append(f"stage range {st['start']}..{st['end']} != {exp[0]}..{exp[-1]}")
    a = st["attrs"]
    if a.get("frameCount") != len(exp):
        errs.append(f"bio:md:frameCount {a.get('frameCount')} != {len(exp)}")
    if a.get("frameIntervalPs") != exp[1] - exp[0]:
        errs.append(f"bio:md:frameIntervalPs {a.get('frameIntervalPs')} != {exp[1]-exp[0]}")
    if a.get("timeCodeUnit") != "ps":
        errs.append(f"bio:md:timeCodeUnit {a.get('timeCodeUnit')!r} != 'ps'")
    return errs, {"frames": len(exp), "interval_ps": exp[1] - exp[0]}


def _check_counts(st, orc):
    s, gr, a = orc["summary"], st["groups"], st["attrs"]
    errs = []
    n = {g: len(gr.get(g, {}).get("atoms", [])) for g in _GROUPS}
    if n["chain_A"] + n["chain_B"] != int(s["PROTEIN_ATOMS"]):
        errs.append(f"protein atoms {n['chain_A']}+{n['chain_B']} != {s['PROTEIN_ATOMS']}")
    ions = gr.get("ions", {}).get("resnames", [])
    for ion, key in (("NA", "IONS_NA"), ("CL", "IONS_CL")):
        if ions.count(ion) != int(s[key]):
            errs.append(f"{ion}: {ions.count(ion)} != summary {s[key]}")
    total = int(s["TOTAL_ATOMS"])
    if orc["gro"]["n_header"] != total or a.get("systemAtomCount") != total:
        errs.append(f"system atoms gro={orc['gro']['n_header']} "
                    f"stage={a.get('systemAtomCount')} summary={total}")
    if a.get("writtenAtomCount") != sum(n.values()):
        errs.append(f"writtenAtomCount {a.get('writtenAtomCount')} != {sum(n.values())}")
    if a.get("omittedAtomCount") != _ATOMS_PER_WATER * int(s["WATERS"]):
        errs.append(f"omittedAtomCount {a.get('omittedAtomCount')} != 3 x {s['WATERS']}")
    for g in _GROUPS:
        sizes = {len(gr.get(g, {}).get(k, [])) for k in ("atoms", "resnames", "resnrs")}
        if g in gr:
            sizes.add(gr[g]["xyz"].shape[1])
        if len(sizes) != 1:
            errs.append(f"{g}: per-point array lengths disagree {sorted(sizes)}")
    return errs, n


def _check_chain_split(st, orc):
    s, errs = orc["summary"], []
    for g, key in (("chain_A", "PROTEIN_RESIDUES_CHAIN_A"),
                   ("chain_B", "PROTEIN_RESIDUES_CHAIN_B")):
        res = sorted(set(st["groups"].get(g, {}).get("resnrs", [])))
        lo, hi = _CHAIN_RESIDUES[g]
        if res != list(range(lo, hi + 1)):
            errs.append(f"{g}: residues {res[:1]}..{res[-1:]} != {lo}..{hi}")
        if len(res) != int(s[key]):
            errs.append(f"{g}: {len(res)} residues != summary {s[key]}")
    return errs, {}


def _lattice_residual(d, box):
    """d minus its nearest lattice vector of `box` (rows a, b, c)."""
    n = np.round(np.linalg.solve(box.T, d.T).T)
    return d - n @ box


def _check_final_frame(st, orc):
    gro = orc["gro"]
    box_A = gro["box"] * 10.0
    ref = _gro_groups(gro)
    errs, worst = [], 0.0
    for g in _GROUPS:
        rows, got = ref.get(g, []), st["groups"].get(g)
        if got is None or len(rows) != got["xyz"].shape[1]:
            errs.append(f"{g}: {len(rows)} gro atoms vs "
                        f"{None if got is None else got['xyz'].shape[1]} on stage")
            continue
        if [r["atom"] for r in rows] != got["atoms"] \
                or [r["resname"] for r in rows] != got["resnames"] \
                or [r["resnr"] for r in rows] != got["resnrs"]:
            errs.append(f"{g}: atom/residue names or numbers differ from md.gro")
        exp = np.array([r["xyz"] for r in rows]) * 10.0
        d = got["xyz"][-1] - exp
        if g.startswith("chain_"):
            # one lattice shift for the whole chain
            d = d - (d[0] - _lattice_residual(d[:1], box_A)[0])
        else:
            d = _lattice_residual(d, box_A)
        m = float(np.abs(d).max())
        worst = max(worst, m)
        if m > _TOL_A:
            errs.append(f"{g}: final frame deviates from md.gro by {m:.4f} A (> {_TOL_A})")
    return errs, {"max_dev_A": round(worst, 4)}


def _check_whole(st, orc):
    errs, worst_caca, worst_step, worst_cent = [], 0.0, 0.0, 0.0
    gr = st["groups"]
    for g in ("chain_A", "chain_B"):
        if g not in gr:
            errs.append(f"{g} missing")
            continue
        ca = [i for i, a in enumerate(gr[g]["atoms"]) if a == "CA"]
        dca = np.linalg.norm(np.diff(gr[g]["xyz"][:, ca], axis=1), axis=2)
        worst_caca = max(worst_caca, float(dca.max()))
        if dca.max() > _CA_CA_MAX_A:
            errs.append(f"{g}: CA-CA {dca.max():.2f} A > {_CA_CA_MAX_A} (chain broken)")
    if "chain_A" in gr and "chain_B" in gr:
        cent = np.linalg.norm(gr["chain_A"]["xyz"].mean(axis=1)
                              - gr["chain_B"]["xyz"].mean(axis=1), axis=1)
        worst_cent = float(cent.max())
        if cent.max() > _BOUND_CENTROID_MAX_A:
            errs.append(f"chain B centroid {cent.max():.1f} A from chain A")
    for g in _GROUPS:
        if g in gr:
            step = np.linalg.norm(np.diff(gr[g]["xyz"], axis=0), axis=2)
            worst_step = max(worst_step, float(step.max()))
            if step.max() > _MAX_STEP_A:
                errs.append(f"{g}: {step.max():.1f} A jump between frames")
    return errs, {"max_CA_CA_A": round(worst_caca, 2),
                  "max_step_A": round(worst_step, 2),
                  "max_centroid_A": round(worst_cent, 2)}


def _check_provenance(st, orc):
    a, errs = st["attrs"], []
    want = {"jobId": _JOB_ID, "forceField": _FORCE_FIELD, "waterModel": _WATER,
            "engine": "GROMACS", "engineVersion": _ENGINE_VERSION,
            "cluster": "banyan", "positionUnit": "angstrom"}
    for k, v in want.items():
        if a.get(k) != v:
            errs.append(f"bio:md:{k} {a.get(k)!r} != {v!r}")
    if orc["manifest"].get("md.xtc", {}).get("job_id") != _JOB_ID:
        errs.append("manifest md.xtc job_id != 119")
    if (orc["summary"].get("FORCE_FIELD"), orc["summary"].get("WATER_MODEL")) \
            != (_FORCE_FIELD, _WATER):
        errs.append("summary.txt force field / water model differ from stated")
    status = a.get("forceFieldStatus") or ""
    if "Q-017" not in status or "plumbing" not in status:
        errs.append("forceFieldStatus lacks the Q-017 plumbing-run tag")
    if "waters omitted" not in (a.get("atomSelection") or ""):
        errs.append("atomSelection does not record that waters were omitted")
    return errs, {}


# --- stage-structural checks ----------------------------------------------------

def _check_payload_on_demand():
    errs = []
    lazy = Usd.Stage.Open(_DYN, Usd.Stage.LoadNone)
    traj = lazy.GetPrimAtPath(_TRAJ)
    if not traj.IsValid() or not traj.HasAuthoredPayloads():
        errs.append("trajectory prim missing or carries no payload")
    if traj.IsValid() and traj.IsLoaded():
        errs.append("LoadNone: trajectory reports loaded")
    if lazy.GetPrimAtPath(f"{_TRAJ}/chain_A").IsValid():
        errs.append("LoadNone: frame data (chain_A) visible without loading")
    if lazy.GetPrimAtPath(_SCOPE).GetAttribute("bio:md:jobId").Get() != _JOB_ID:
        errs.append("LoadNone: provenance not readable without the payload")
    lazy.Load(_TRAJ)
    pts = lazy.GetPrimAtPath(f"{_TRAJ}/chain_A")
    if not pts.IsValid() or not UsdGeom.Points(pts).GetPointsAttr().GetNumTimeSamples():
        errs.append("after Load(): chain_A has no time-sampled points")
    # the light layer itself carries no frame data
    layer = Sdf.Layer.FindOrOpen(_DYN)
    heavy = []
    layer.Traverse(layer.pseudoRoot.path,
                   lambda p: heavy.append(p) if p.IsPropertyPath()
                   and p.name == "points" else None)
    if heavy:
        errs.append(f"Dynamics layer itself authors points: {heavy[:1]}")
    return errs, {"dynamics_bytes": os.path.getsize(_DYN),
                  "frames_bytes": os.path.getsize(_FRAMES)}


def _check_metadata():
    errs = []
    for path in (_DYN, _FRAMES):
        s = Usd.Stage.Open(path, Usd.Stage.LoadNone)
        name = os.path.basename(path)
        if UsdGeom.GetStageMetersPerUnit(s) != 1e-10:
            errs.append(f"{name}: metersPerUnit {UsdGeom.GetStageMetersPerUnit(s)}")
        if UsdGeom.GetStageUpAxis(s) != UsdGeom.Tokens.y:
            errs.append(f"{name}: upAxis {UsdGeom.GetStageUpAxis(s)}")
        if not s.GetDefaultPrim().IsValid():
            errs.append(f"{name}: no defaultPrim")
    tcps = {Sdf.Layer.FindOrOpen(p).timeCodesPerSecond for p in (_DYN, _FRAMES)}
    if len(tcps) != 1:
        errs.append(f"timeCodesPerSecond differs across layers {tcps} "
                    "(USD would rescale the payload's time samples)")
    return errs, {}


def _check_not_stale():
    sys.path.insert(0, os.path.dirname(_PKG))
    from p53_mdm2.converters import trajectory_to_usd
    tmp = tempfile.mkdtemp(prefix="p53_traj_")
    try:
        trajectory_to_usd.convert(out_dir=tmp)
        errs = []
        for p in (_DYN, _FRAMES):
            with open(p, "rb") as a, open(os.path.join(tmp, os.path.basename(p)), "rb") as b:
                if a.read() != b.read():
                    errs.append(f"{os.path.basename(p)} is stale vs a fresh conversion")
        return errs, {}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- self-falsification ---------------------------------------------------------

def _mutations(st, orc):
    def m_orc(fn):
        o = copy.deepcopy(orc); fn(o); return o

    def m_st(fn):
        s = copy.deepcopy(st); fn(s); return s

    def nudge_gro(o):
        r = next(r for r in o["gro"]["rows"] if r["resname"] == "CL")
        r["xyz"] = (r["xyz"][0] + 0.005, r["xyz"][1], r["xyz"][2])   # 0.05 A

    def nm_units(s):
        s["groups"]["chain_B"]["xyz"] = s["groups"]["chain_B"]["xyz"] / 10.0

    def pbc_jump(s):
        s["groups"]["chain_A"]["xyz"][5, :40, 0] += orc["gro"]["box"][0, 0] * 10.0

    def bad_sha(o):
        o["hashes"]["md.xtc"] = "0" * 64

    return [
        ("gro coordinate +0.05 A", _check_final_frame, st, m_orc(nudge_gro)),
        ("chain B left in nm", _check_final_frame, m_st(nm_units), orc),
        ("mdp nsteps 60000", _check_time_grid, st,
         m_orc(lambda o: o["mdp"].__setitem__("nsteps", "60000"))),
        ("summary PROTEIN_ATOMS +1", _check_counts, st,
         m_orc(lambda o: o["summary"].__setitem__("PROTEIN_ATOMS", "1671"))),
        ("summary chain A residues 86", _check_chain_split, st,
         m_orc(lambda o: o["summary"].__setitem__("PROTEIN_RESIDUES_CHAIN_A", "86"))),
        ("xtc sha flipped", _check_sources, st, m_orc(bad_sha)),
        ("PBC jump in frame 5", _check_whole, m_st(pbc_jump), orc),
        ("force field relabelled", _check_provenance,
         m_st(lambda s: s["attrs"].__setitem__("forceField", "amber14sb")), orc),
    ]


def _check_selftest(st, orc):
    errs, killed = [], 0
    for label, fn, s_m, o_m in _mutations(st, orc):
        if fn(st, orc)[0]:
            errs.append(f"[{label}] family already red on the real data")
            continue
        if fn(s_m, o_m)[0]:
            killed += 1
        else:
            errs.append(f"[{label}] mutation went UNDETECTED")
    return errs, {"mutations_detected": killed}


# --- harness entry point --------------------------------------------------------

def _row(name, fn):
    try:
        errors, detail = fn()
    except Exception as exc:
        errors, detail = [f"{type(exc).__name__}: {exc}"], {}
    return {"check_name": name, "passed": not errors, "errors": errors,
            "detail": detail}


def run() -> list:
    if Usd is None:
        return [_row("traj_pxr_available", lambda: (["pxr not importable"], {}))]
    for p in (_DYN, _FRAMES):
        if not os.path.isfile(p):
            return [_row("traj_stage_exists", lambda: ([f"not found: {p}"], {}))]
    try:
        st, orc = _load_stage(), _load_oracle()
    except Exception as exc:
        return [_row("traj_readable", lambda: ([f"{type(exc).__name__}: {exc}"], {}))]
    pure = [
        ("traj_sources_vs_manifest", _check_sources),
        ("traj_time_grid_vs_mdp", _check_time_grid),
        ("traj_atom_counts_vs_summary", _check_counts),
        ("traj_chain_split", _check_chain_split),
        ("traj_final_frame_vs_gro", _check_final_frame),
        ("traj_chains_whole_no_jumps", _check_whole),
        ("traj_provenance", _check_provenance),
    ]
    rows = [_row(n, lambda f=f: f(st, orc)) for n, f in pure]
    rows += [
        _row("traj_payload_on_demand", _check_payload_on_demand),
        _row("traj_units_metadata", _check_metadata),
        _row("traj_committed_not_stale", _check_not_stale),
        _row("traj_falsification_selftest", lambda: _check_selftest(st, orc)),
    ]
    return rows


if __name__ == "__main__":
    for r in run():
        print("PASS" if r["passed"] else "FAIL", r["check_name"], r["errors"][:2], r["detail"])
