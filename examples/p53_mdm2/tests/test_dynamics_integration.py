"""
Read-back checks for the Dynamics layer's join to the INTEGRATED stage (PI Q-019).

Opens the COMMITTED ``demos/p53_mdm2_integrated.usda`` fresh and asserts what
the join claims, against oracles that do not go through
``demos/run_end_to_end.py`` or ``composition/dynamics_alignment.py``:

    stage clock       <- maboss/reference/p53_Mdm2_runcfg.cfg (max_time,
                         time_tick): frames 0 .. max_time/time_tick - 1
    MD time grid      <- cluster/p53_md/md.mdp (nsteps, dt, nstxout-compressed)
    raw MD samples    <- the frames layer opened as a bare Sdf.Layer
    CA correspondence <- 1ycr.pdb CA rows by flat column slicing (chain col 22,
                         resSeq cols 23-26) and md.gro rows by fixed columns,
                         chains split where the residue number drops --
                         re-derived here, not taken from the aligner
    fit optimum       <- Horn's quaternion closed form for the minimum RMSD
                         (a different algorithm from the aligner's SVD Kabsch)
    time-unit values  <- stated below: MaBoSS 1 model unit = 1 hour (3600 s),
                         an ASSUMPTION per Q-019; MD time codes in ps

How USD maps the referenced clock (verified by ``dynint_ps_samples_via_reference``
with an in-memory probe): a reference with no layer offset maps time codes 1:1,
so at integrated time t the Dynamics sample authored at t is read. USD ALSO
folds the timeCodesPerSecond ratio of the two layers into that mapping, so a
TCPS mismatch would silently rescale the ps samples; the probe composes the
same layer under a root with doubled TCPS and asserts the samples move, which
proves the equality check is the right guard.

CA tolerance: the aligner's fit on frame 0 gave 0.3482 A CA RMSD over 98 pairs
(recorded as bio:md:alignmentRmsdAngstrom in the committed integrated stage). The stage stores positions to 0.01 A, so re-reading them cannot
move the RMSD by more than ~0.005 A; the stated bound is 0.35 A, and the
authored fit must also be within 1e-3 A of the Horn optimum.

SELF-TEST ROW (``dynint_falsification_selftest``): each pure family is re-run
on an in-memory mutated copy of its inputs and must go red.
"""

from __future__ import annotations

import copy
import os
import sys
import tempfile

import numpy as np

try:
    from pxr import Gf, Sdf, Usd, UsdGeom
except ImportError:  # pragma: no cover
    Usd = None

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_INTEGRATED = os.path.join(_PKG, "demos", "p53_mdm2_integrated.usda")
_ANALYSIS = os.path.join(_PKG, "analysis", "p53_mdm2_analysis.usda")
_DYN = os.path.join(_PKG, "output", "p53_mdm2_dynamics_job119.usda")
_FRAMES = os.path.join(_PKG, "output", "p53_mdm2_dynamics_job119_frames.usda")
_TOPO = os.path.join(_PKG, "output", "p53_mdm2_topology.usda")
_PDB = os.path.join(_PKG, "data", "structures", "1ycr.pdb")
_GRO = os.path.join(_PKG, "data", "md_runs", "banyan_job119", "md.gro")
_MDP = os.path.join(_PKG, "cluster", "p53_md", "md.mdp")
_CFG = os.path.join(_PKG, "maboss", "reference", "p53_Mdm2_runcfg.cfg")

_ROOT = "/p53_MDM2_complex"
_DYN_PRIM = f"{_ROOT}/dynamics"
_TRAJ = f"{_DYN_PRIM}/trajectory"
_MABOSS = f"{_ROOT}/maboss"
_CHAINS = ("chain_A", "chain_B")

# --- stated expectations ------------------------------------------------------
_DYN_LAYER_NAME = "p53_mdm2_dynamics_job119.usda"
_JOB_ID = "119"
_MABOSS_UNIT, _MABOSS_SECONDS = "hour", 3600.0     # [assumption] PI Q-019
_MD_UNIT = "ps"
_CA_RMSD_MAX_A = 0.35          # fit gave 0.3482 A; see module docstring
_OPTIMUM_TOL_A = 1e-3
_ORTHO_TOL = 1e-9


# --- independent oracles ------------------------------------------------------

def _kv(path, comment):
    out = {}
    with open(path, encoding="latin-1") as fh:
        for line in fh:
            line = line.split(comment, 1)[0].strip().rstrip(";")
            k, s, v = line.partition("=")
            if s:
                out[k.strip()] = v.strip()
    return out


def _pdb_ca():
    out = {}
    with open(_PDB) as fh:
        for ln in fh:
            if ln.startswith("ATOM") and ln[12:16].strip() == "CA":
                out[(ln[21], int(ln[22:26]))] = np.array(
                    [float(ln[30:38]), float(ln[38:46]), float(ln[46:54])])
    return out


def _gro_chain_atoms():
    """{chain letter: [(atom name, resnr), ...]} in file order; no mdtraj."""
    with open(_GRO) as fh:
        lines = fh.read().splitlines()
    n = int(lines[1])
    chains, ci, last = {}, 0, None
    for ln in lines[2:2 + n]:
        resnr, resname, atom = int(ln[0:5]), ln[5:10].strip(), ln[10:15].strip()
        if resname in ("SOL", "NA", "CL"):
            continue
        if last is not None and resnr < last:
            ci += 1
        last = resnr
        chains.setdefault("AB"[ci], []).append((atom, resnr))
    return chains


def _load_oracle():
    cfg, mdp = _kv(_CFG, "//"), _kv(_MDP, ";")
    tick, tmax = float(cfg["time_tick"]), float(cfg["max_time"])
    nsteps, dt, nout = int(mdp["nsteps"]), float(mdp["dt"]), int(mdp["nstxout-compressed"])
    return {
        "maboss_frames": (0.0, float(round(tmax / tick) - 1)),
        "maboss_tcps": 1.0 / tick,
        "md_grid": [float(round(k * nout * dt, 6)) for k in range(nsteps // nout + 1)],
        "pdb_ca": _pdb_ca(),
        "gro": _gro_chain_atoms(),
    }


# --- stage read-back ----------------------------------------------------------

def _mat(m):
    return np.array([[m[i][j] for j in range(4)] for i in range(4)])


def _attr(prim, name):
    a = prim.GetAttribute(name)
    return a.Get() if a.IsValid() else None


def _load_stage():
    stage = Usd.Stage.Open(_INTEGRATED, Usd.Stage.LoadAll)
    root_layer = stage.GetRootLayer()
    spec = root_layer.GetPrimAtPath(_DYN_PRIM)
    refs = []
    if spec is not None:
        for r in spec.referenceList.GetAddedOrExplicitItems():
            refs.append({"asset": r.assetPath, "prim": str(r.primPath),
                         "offset": r.layerOffset.offset,
                         "scale": r.layerOffset.scale})
    dyn, traj = stage.GetPrimAtPath(_DYN_PRIM), stage.GetPrimAtPath(_TRAJ)
    frames_layer = Sdf.Layer.FindOrOpen(_FRAMES)
    chains = {}
    for c in _CHAINS:
        prim = stage.GetPrimAtPath(f"{_TRAJ}/{c}")
        if not prim.IsValid():
            continue
        pts = UsdGeom.Points(prim).GetPointsAttr()
        times = list(pts.GetTimeSamples())
        raw_path = Sdf.Path(f"/trajectory/{c}.points")
        chains[c] = {
            "times": times,
            "composed": {t: np.array(pts.Get(Usd.TimeCode(t))) for t in times},
            "raw": {t: np.array(frames_layer.QueryTimeSample(raw_path, t))
                    for t in frames_layer.ListTimeSamplesForPath(raw_path)},
            "world": _mat(UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(
                Usd.TimeCode(times[0]))) if times else None,
            "atoms": list(_attr(prim, "bio:md:atomNames") or []),
            "resnrs": list(_attr(prim, "bio:md:residueNumbers") or []),
        }
    xf_prims = sorted(str(p.GetPath()) for p in Usd.PrimRange(dyn)
                      if p.GetAttribute("xformOpOrder").HasAuthoredValue()) \
        if dyn.IsValid() else []
    maboss = stage.GetPrimAtPath(_MABOSS)
    unit_attr = maboss.GetAttribute("bio:maboss:timeUnit")
    secs_attr = maboss.GetAttribute("bio:maboss:secondsPerTimeUnit")
    traj_op = list(_attr(traj, "xformOpOrder") or []) if traj.IsValid() else []
    local = _mat(_attr(traj, "xformOp:transform")) \
        if traj.IsValid() and _attr(traj, "xformOp:transform") is not None else None
    return {
        "refs": refs,
        "layer_stack": [os.path.basename(l.identifier) for l in stage.GetLayerStack()],
        "used_layers": [os.path.basename(l.identifier) for l in stage.GetUsedLayers()],
        "start": stage.GetStartTimeCode(), "end": stage.GetEndTimeCode(),
        "tcps": {"integrated": stage.GetTimeCodesPerSecond(),
                 "dynamics": Sdf.Layer.FindOrOpen(_DYN).timeCodesPerSecond,
                 "frames": frames_layer.timeCodesPerSecond},
        "dyn_type": dyn.GetTypeName() if dyn.IsValid() else None,
        "job_id": _attr(dyn, "bio:md:jobId") if dyn.IsValid() else None,
        "md_unit": _attr(dyn, "bio:md:timeCodeUnit") if dyn.IsValid() else None,
        "clock_relation": str(_attr(dyn, "bio:demo:clockRelation") or "") if dyn.IsValid() else "",
        "chains": chains,
        "xform_prims": xf_prims,
        "traj_op_order": traj_op,
        "traj_local": local,
        "align": {k: _attr(traj, f"bio:md:{k}") for k in
                  ("alignmentRmsdAngstrom", "alignmentAtomCount", "alignmentMethod")}
        if traj.IsValid() else {},
        "maboss_unit": _attr(maboss, "bio:maboss:timeUnit"),
        "maboss_secs": _attr(maboss, "bio:maboss:secondsPerTimeUnit"),
        "maboss_status": str(_attr(maboss, "bio:maboss:timeUnitStatus") or ""),
        "maboss_docs": (unit_attr.GetDocumentation() if unit_attr.IsValid() else "",
                        secs_attr.GetDocumentation() if secs_attr.IsValid() else ""),
    }


# --- pure checks: (st, orc) -> (errors, detail) ---------------------------------

def _check_reference(st, orc):
    errs = []
    if len(st["refs"]) != 1:
        return [f"{_DYN_PRIM} carries {len(st['refs'])} references, expected 1"], {}
    r = st["refs"][0]
    if os.path.basename(r["asset"]) != _DYN_LAYER_NAME:
        errs.append(f"reference asset {r['asset']} is not {_DYN_LAYER_NAME}")
    if r["prim"] != _DYN_PRIM:
        errs.append(f"reference targets {r['prim']}, expected {_DYN_PRIM}")
    if (r["offset"], r["scale"]) != (0.0, 1.0):
        errs.append(f"reference layer offset ({r['offset']}, x{r['scale']}) is "
                    "not identity -- a clock relation was invented")
    if _DYN_LAYER_NAME in st["layer_stack"]:
        errs.append("Dynamics layer is in the sublayer stack, not referenced")
    if _DYN_LAYER_NAME not in st["used_layers"]:
        errs.append("Dynamics layer is not used by the composed stage")
    if st["dyn_type"] != "Scope" or st["job_id"] != _JOB_ID:
        errs.append(f"composed dynamics prim type={st['dyn_type']} "
                    f"jobId={st['job_id']!r}")
    if set(st["chains"]) != set(_CHAINS):
        errs.append(f"payload frames not composed: {sorted(st['chains'])}")
    return errs, {"asset": r["asset"], "prim": r["prim"]}


def _check_clock(st, orc):
    errs = []
    lo, hi = orc["maboss_frames"]
    if (st["start"], st["end"]) != (lo, hi):
        errs.append(f"stage clock {st['start']}..{st['end']} != MaBoSS frames {lo}..{hi}")
    if st["tcps"]["integrated"] != orc["maboss_tcps"]:
        errs.append(f"stage timeCodesPerSecond {st['tcps']['integrated']} != "
                    f"1/time_tick {orc['maboss_tcps']}")
    if (st["start"], st["end"]) == (orc["md_grid"][0], orc["md_grid"][-1]):
        errs.append("stage clock was taken from the Dynamics layer")
    return errs, {"frames": f"{lo:g}..{hi:g}"}


def _check_ps_samples(st, orc):
    errs = []
    if len(set(st["tcps"].values())) != 1:
        errs.append(f"timeCodesPerSecond differ {st['tcps']} -- USD rescales")
    for c, d in st["chains"].items():
        if d["times"] != orc["md_grid"]:
            errs.append(f"{c}: composed samples {d['times']} != mdp grid (ps)")
        if sorted(d["raw"]) != orc["md_grid"]:
            errs.append(f"{c}: raw frames-layer samples != mdp grid")
        for t in d["times"]:
            if t not in d["raw"] or not np.array_equal(d["composed"][t], d["raw"][t]):
                errs.append(f"{c}: composed sample at t={t} != raw sample at t")
                break
    return errs, {"ps_grid": f"{orc['md_grid'][0]:g}..{orc['md_grid'][-1]:g}"}


def _check_units(st, orc):
    errs = []
    if st["maboss_unit"] != _MABOSS_UNIT:
        errs.append(f"bio:maboss:timeUnit {st['maboss_unit']!r} != {_MABOSS_UNIT!r}")
    if st["maboss_secs"] != _MABOSS_SECONDS:
        errs.append(f"bio:maboss:secondsPerTimeUnit {st['maboss_secs']} != {_MABOSS_SECONDS}")
    if "assumption" not in st["maboss_status"].lower():
        errs.append("bio:maboss:timeUnitStatus does not declare an assumption")
    if not all("[assumption]" in d for d in st["maboss_docs"]):
        errs.append("time-unit attribute docs lack the [assumption] tag")
    if st["md_unit"] != _MD_UNIT:
        errs.append(f"composed bio:md:timeCodeUnit {st['md_unit']!r} != {_MD_UNIT!r}")
    rel = st["clock_relation"]
    if "independent" not in rel or "NO layer offset" not in rel:
        errs.append("bio:demo:clockRelation does not state independent clocks")
    return errs, {"maboss": f"1 unit = {st['maboss_secs']} s [assumption]",
                  "md": st["md_unit"]}


def _horn_min_rmsd(X, Y):
    """Minimum RMSD over rigid motions, Horn (1987) quaternion closed form."""
    X, Y = X - X.mean(axis=0), Y - Y.mean(axis=0)
    S = X.T @ Y
    (xx, xy, xz), (yx, yy, yz), (zx, zy, zz) = S
    N = np.array([
        [xx + yy + zz, yz - zy, zx - xz, xy - yx],
        [yz - zy, xx - yy - zz, xy + yx, zx + xz],
        [zx - xz, xy + yx, -xx + yy - zz, yz + zy],
        [xy - yx, zx + xz, yz + zy, -xx - yy + zz]])
    lam = np.linalg.eigvalsh(N)[-1]
    e = (X ** 2).sum() + (Y ** 2).sum() - 2.0 * lam
    return float(np.sqrt(max(e, 0.0) / len(X)))


def _ca_pairs(st, orc):
    """(MD CA local positions at t0, world matrices, crystal CA, keys)."""
    X, W, Y, keys = [], [], [], []
    for c in _CHAINS:
        letter = c.split("_")[1]
        d = st["chains"].get(c)
        gro = orc["gro"].get(letter, [])
        if d is None or [a for a, _ in gro] != d["atoms"] \
                or [r for _, r in gro] != d["resnrs"]:
            raise ValueError(f"{c}: stage atom order differs from md.gro")
        p0 = d["composed"][d["times"][0]]
        for i, (atom, resnr) in enumerate(gro):
            if atom == "CA" and (letter, resnr) in orc["pdb_ca"]:
                X.append(p0[i]); W.append(d["world"])
                Y.append(orc["pdb_ca"][(letter, resnr)]); keys.append((letter, resnr))
    return np.array(X, dtype=float), W, np.array(Y), keys


def _check_alignment(st, orc):
    errs = []
    if st["traj_op_order"] != ["xformOp:transform"]:
        errs.append(f"trajectory xformOpOrder {st['traj_op_order']} != one transform")
    if st["xform_prims"] != [_TRAJ]:
        errs.append(f"xformOps authored on {st['xform_prims']}, expected only {_TRAJ}")
    M = st["traj_local"]
    if M is None:
        return errs + ["no xformOp:transform on the trajectory prim"], {}
    R = M[:3, :3]
    if np.abs(R @ R.T - np.eye(3)).max() > _ORTHO_TOL or abs(np.linalg.det(R) - 1) > _ORTHO_TOL \
            or np.abs(M[:3, 3]).max() != 0.0 or M[3, 3] != 1.0:
        errs.append("authored transform is not a proper rigid motion")
    try:
        X, W, Y, keys = _ca_pairs(st, orc)
    except ValueError as exc:
        return errs + [str(exc)], {}
    md_keys = {(c.split("_")[1], r) for c in _CHAINS
               for (a, r) in orc["gro"].get(c.split("_")[1], []) if a == "CA"}
    if md_keys != set(orc["pdb_ca"]):
        errs.append(f"CA sets differ: MD-only {sorted(md_keys - set(orc['pdb_ca']))[:3]} "
                    f"crystal-only {sorted(set(orc['pdb_ca']) - md_keys)[:3]}")
    world = np.array([(np.append(x, 1.0) @ w)[:3] for x, w in zip(X, W)])
    rmsd = float(np.sqrt(((world - Y) ** 2).sum(axis=1).mean()))
    best = _horn_min_rmsd(X, Y)
    if rmsd > _CA_RMSD_MAX_A:
        errs.append(f"CA RMSD after transform {rmsd:.4f} A > {_CA_RMSD_MAX_A}")
    if rmsd - best > _OPTIMUM_TOL_A:
        errs.append(f"transform is not the optimal fit: {rmsd:.4f} vs Horn {best:.4f}")
    a = st["align"]
    if a.get("alignmentAtomCount") != len(orc["pdb_ca"]) or len(keys) != len(orc["pdb_ca"]):
        errs.append(f"{len(keys)} pairs / recorded {a.get('alignmentAtomCount')} "
                    f"!= {len(orc['pdb_ca'])} crystal CA")
    if a.get("alignmentRmsdAngstrom") is None \
            or abs(a["alignmentRmsdAngstrom"] - rmsd) > _OPTIMUM_TOL_A:
        errs.append(f"recorded RMSD {a.get('alignmentRmsdAngstrom')} != measured {rmsd:.4f}")
    return errs, {"pairs": len(keys), "ca_rmsd_A": round(rmsd, 4),
                  "horn_opt_A": round(best, 4)}


# --- stage-structural checks ----------------------------------------------------

def _check_rescale_probe():
    """USD folds the TCPS ratio into a reference: prove the guard is needed."""
    dyn = Sdf.Layer.FindOrOpen(_DYN)
    out = {}
    for label, tcps in (("same", dyn.timeCodesPerSecond),
                        ("doubled", 2.0 * dyn.timeCodesPerSecond)):
        s = Usd.Stage.CreateInMemory()
        s.SetTimeCodesPerSecond(tcps)
        p = s.OverridePrim("/probe")
        p.GetReferences().AddReference(_DYN, Sdf.Path(_DYN_PRIM))
        pts = UsdGeom.Points(s.GetPrimAtPath("/probe/trajectory/chain_A"))
        out[label] = list(pts.GetPointsAttr().GetTimeSamples())
    raw = list(Sdf.Layer.FindOrOpen(_FRAMES).ListTimeSamplesForPath(
        Sdf.Path("/trajectory/chain_A.points")))
    errs = []
    if out["same"] != raw:
        errs.append(f"identity reference remapped samples: {out['same'][:3]} vs {raw[:3]}")
    if out["doubled"] == raw:
        errs.append("doubled TCPS did NOT rescale -- the guard rests on a false premise")
    return errs, {"same_tcps_last": out["same"][-1], "doubled_tcps_last": out["doubled"][-1]}


def _check_layers_untouched():
    errs = []
    for path in (_DYN, _FRAMES):
        layer, found = Sdf.Layer.FindOrOpen(path), []
        layer.Traverse(layer.pseudoRoot.path,
                       lambda p: found.append(str(p)) if p.IsPropertyPath()
                       and (p.name.startswith("xformOp") or p.name.startswith("bio:demo:")
                            or "alignment" in p.name) else None)
        if found:
            errs.append(f"{os.path.basename(path)} carries integration opinions {found[:2]}")
    topo = Usd.Stage.Open(_TOPO, Usd.Stage.LoadNone)
    if topo.GetPrimAtPath(_DYN_PRIM).IsValid():
        errs.append("Biology topology layer contains the dynamics prim")
    return errs, {}


def _check_not_stale():
    """Regenerate the analysis + integrated layers next to the committed ones
    (same directory, so relative asset paths agree) and byte-compare."""
    sys.path.insert(0, os.path.dirname(_PKG))
    from p53_mdm2.demos import run_end_to_end
    from p53_mdm2.maboss import run_maboss
    from p53_mdm2.templates import build_analysis_layer
    errs, tmps = [], []
    try:
        run_maboss.ensure_backend()
        for committed, build in (
                (_ANALYSIS, lambda out: build_analysis_layer.build_analysis_layer(
                    out, probtrajs=run_maboss.run_all())),
                (_INTEGRATED, lambda out: run_end_to_end.build_integrated_stage(
                    out, verbose=False))):
            fd, tmp = tempfile.mkstemp(suffix=".usda", prefix=".stale_",
                                       dir=os.path.dirname(committed))
            os.close(fd)
            tmps.append(tmp)
            build(tmp)
            with open(committed, "rb") as a, open(tmp, "rb") as b:
                if a.read() != b.read():
                    errs.append(f"{os.path.basename(committed)} is stale vs a rebuild")
    finally:
        for t in tmps:
            if os.path.exists(t):
                os.remove(t)
    return errs, {"rebuilt": 2}


# --- self-falsification ---------------------------------------------------------

def _mutations(st, orc):
    def m_st(fn):
        s = copy.deepcopy(st); fn(s); return s

    def m_orc(fn):
        o = copy.deepcopy(orc); fn(o); return o

    def scale_ref(s):
        s["refs"][0]["scale"] = 0.01

    def rescale_samples(s):
        d = s["chains"]["chain_A"]
        d["composed"] = {t * 2: v for t, v in d["composed"].items()}
        d["times"] = [t * 2 for t in d["times"]]

    def shift_transform(s):
        for d in s["chains"].values():
            d["world"] = d["world"].copy(); d["world"][3, 0] += 1.0

    def renumber_pdb(o):
        o["pdb_ca"] = {(c, r + 1): v for (c, r), v in o["pdb_ca"].items()}

    def per_frame_ops(s):
        s["xform_prims"] = s["xform_prims"] + [f"{_TRAJ}/chain_A"]

    return [
        ("reference offset scale 0.01", _check_reference, m_st(scale_ref), orc),
        ("stage clock = Dynamics ps", _check_clock,
         m_st(lambda s: s.update(start=0.0, end=100.0)), orc),
        ("composed samples rescaled x2", _check_ps_samples, m_st(rescale_samples), orc),
        ("MaBoSS unit relabelled seconds", _check_units,
         m_st(lambda s: s.update(maboss_unit="second", maboss_secs=1.0)), orc),
        ("transform translated +1 A", _check_alignment, m_st(shift_transform), orc),
        ("1YCR residues renumbered +1", _check_alignment, st, m_orc(renumber_pdb)),
        ("extra xformOp on a chain", _check_alignment, m_st(per_frame_ops), orc),
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
        return [_row("dynint_pxr_available", lambda: (["pxr not importable"], {}))]
    for p in (_INTEGRATED, _DYN, _FRAMES, _ANALYSIS):
        if not os.path.isfile(p):
            return [_row("dynint_stage_exists", lambda p=p: ([f"not found: {p}"], {}))]
    try:
        st, orc = _load_stage(), _load_oracle()
    except Exception as exc:
        return [_row("dynint_readable", lambda: ([f"{type(exc).__name__}: {exc}"], {}))]
    pure = [
        ("dynint_reference_arc", _check_reference),
        ("dynint_stage_clock_maboss_only", _check_clock),
        ("dynint_ps_samples_via_reference", _check_ps_samples),
        ("dynint_time_unit_assumptions", _check_units),
        ("dynint_single_transform_ca_fit", _check_alignment),
    ]
    rows = [_row(n, lambda f=f: f(st, orc)) for n, f in pure]
    rows += [
        _row("dynint_tcps_rescale_probe", _check_rescale_probe),
        _row("dynint_source_layers_untouched", _check_layers_untouched),
        _row("dynint_committed_not_stale", _check_not_stale),
        _row("dynint_falsification_selftest", lambda: _check_selftest(st, orc)),
    ]
    return rows


if __name__ == "__main__":
    for r in run():
        print("PASS" if r["passed"] else "FAIL", r["check_name"], r["errors"][:2], r["detail"])
