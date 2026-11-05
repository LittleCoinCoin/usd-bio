"""
dynamics_alignment.py -- ONE rigid transform placing an MD Dynamics layer in the
1YCR crystal frame of the Biology (topology) layer.

PI Q-019 (2026-11-04), part 2: offset the Dynamics prim with a SINGLE transform
rather than refitting every frame. So the raw MD frames are never touched (they
stay in the GROMACS box frame, byte-for-byte what ``trajectory_to_usd`` wrote);
the integrated stage authors one ``xformOp:transform`` over them.

The transform is a Kabsch fit (rotation + translation, no scaling, no
reflection) of the MD trajectory's FIRST frame CA atoms onto the matching 1YCR
CA atoms:

    correspondence  CA atoms matched by (chain, residue number). The MD chains
                    are named by order of appearance (``chain_A`` = first block
                    of residues, i.e. MDM2; ``chain_B`` = p53 peptide), the
                    topology chains by the PDB chain ID. Residue names are
                    compared after folding GROMACS protonation-state names
                    (HIE/HID/HIP -> HIS, ...) and any disagreement RAISES -- a
                    renumbered or re-sequenced MD system cannot silently fit.
    fit             X = MD CA (frame 0), Y = 1YCR CA; centre both, SVD of the
                    covariance, sign-corrected so det(R) = +1. y ~ R x + t.
    USD form        USD multiplies ROW vectors (p' = p M), so the authored
                    matrix is M[:3,:3] = R^T and M[3,:3] = t.

Nothing here is dataset-specific: chains, residues and positions are read off
the two committed layers.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

#: Atom used for the fit.
FIT_ATOM = "CA"

#: GROMACS / AMBER residue names that denote a protonation or bonding state of
#: a standard residue; folded before comparing MD and crystal sequences.
_RESNAME_FOLD = {"HIE": "HIS", "HID": "HIS", "HIP": "HIS", "HSD": "HIS",
                 "HSE": "HIS", "HSP": "HIS", "CYX": "CYS", "CYM": "CYS",
                 "LYN": "LYS", "ASH": "ASP", "GLH": "GLU"}

Key = Tuple[str, int]          # (chain letter, residue number)


@dataclass
class Alignment:
    rotation: np.ndarray        # (3, 3), column-vector convention: y = R x + t
    translation: np.ndarray     # (3,)
    rmsd_angstrom: float        # CA RMSD after the fit
    rmsd_before_angstrom: float # CA RMSD of the raw box coordinates
    fit_time_code: float        # the MD frame the fit used
    pairs: List[Key] = field(default_factory=list)

    def usd_matrix(self):
        """The fit as a ``Gf.Matrix4d`` in USD's row-vector convention."""
        from pxr import Gf
        m = np.eye(4)
        m[:3, :3] = self.rotation.T
        m[3, :3] = self.translation
        return Gf.Matrix4d(*[float(v) for v in m.ravel()])

    def mapping_description(self) -> str:
        chains = sorted({c for c, _ in self.pairs})
        parts = []
        for c in chains:
            res = sorted(r for cc, r in self.pairs if cc == c)
            parts.append(f"MD chain_{c} {res[0]}-{res[-1]} -> 1YCR chain {c} "
                         f"{res[0]}-{res[-1]} ({len(res)} CA)")
        return ("CA atoms matched by chain + residue number, identity "
                "numbering, residue names checked: " + "; ".join(parts))


def _fold(resname: str) -> str:
    return _RESNAME_FOLD.get(resname, resname)


def topology_ca(topology_path: str) -> Dict[Key, Tuple[str, np.ndarray]]:
    """{(chain, resSeq): (resname, world xyz)} for every CA of the topology layer."""
    from pxr import Usd, UsdGeom
    stage = Usd.Stage.Open(topology_path, Usd.Stage.LoadNone)
    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    out = {}
    for prim in stage.Traverse():
        if prim.GetAttribute("bio:atomName").Get() != FIT_ATOM:
            continue
        res, chain = prim.GetParent(), prim.GetParent().GetParent()
        key = (str(chain.GetAttribute("bio:chainID").Get()),
               int(res.GetAttribute("bio:residueSeq").Get()))
        xyz = np.array(cache.GetLocalToWorldTransform(prim).ExtractTranslation())
        out[key] = (str(res.GetAttribute("bio:residueName").Get()), xyz)
    return out


def md_ca(frames_path: str, time_code=None) -> Tuple[Dict[Key, Tuple[str, np.ndarray]], float]:
    """CA positions of the frames layer at *time_code* (default: first sample).

    Returns ({(chain, resnr): (resname, xyz)}, time_code). Positions are the raw
    authored ``points`` (no transform exists in the frames layer).
    """
    from pxr import Usd, UsdGeom
    stage = Usd.Stage.Open(frames_path)
    out, used = {}, None
    root = stage.GetDefaultPrim()
    for prim in root.GetChildren():
        name = prim.GetName()
        if not name.startswith("chain_"):
            continue
        chain = name.split("_", 1)[1]
        attr = UsdGeom.Points(prim).GetPointsAttr()
        t = attr.GetTimeSamples()[0] if time_code is None else time_code
        used = float(t)
        xyz = np.array(attr.Get(Usd.TimeCode(t)), dtype=float)
        atoms = prim.GetAttribute("bio:md:atomNames").Get()
        nums = prim.GetAttribute("bio:md:residueNumbers").Get()
        names = prim.GetAttribute("bio:md:residueNames").Get()
        for i, (a, r, n) in enumerate(zip(atoms, nums, names)):
            if a == FIT_ATOM:
                out[(chain, int(r))] = (str(n), xyz[i])
    return out, used


def correspondence(md: dict, topo: dict) -> List[Key]:
    """Matched (chain, resnr) keys; raises on any unmatched or renamed residue."""
    only_md, only_topo = sorted(set(md) - set(topo)), sorted(set(topo) - set(md))
    if only_md or only_topo:
        raise ValueError(f"CA sets differ: MD-only {only_md[:5]}, "
                         f"crystal-only {only_topo[:5]} -- numbering needs an "
                         f"explicit map before fitting")
    keys = sorted(md)
    bad = [(k, md[k][0], topo[k][0]) for k in keys
           if _fold(md[k][0]) != _fold(topo[k][0])]
    if bad:
        raise ValueError(f"residue names disagree at {bad[:5]}")
    return keys


def kabsch(X: np.ndarray, Y: np.ndarray):
    """Rigid (R, t) minimising |R X + t - Y|; det(R) = +1."""
    cx, cy = X.mean(axis=0), Y.mean(axis=0)
    H = (X - cx).T @ (Y - cy)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return R, cy - R @ cx


def _rmsd(A, B) -> float:
    return float(np.sqrt(((A - B) ** 2).sum(axis=1).mean()))


def fit_dynamics_to_topology(topology_path: str, frames_path: str) -> Alignment:
    """Kabsch-fit the frames layer's first frame CA onto the topology's CA."""
    topo = topology_ca(topology_path)
    md, t0 = md_ca(frames_path)
    keys = correspondence(md, topo)
    X = np.array([md[k][1] for k in keys])
    Y = np.array([topo[k][1] for k in keys])
    R, t = kabsch(X, Y)
    return Alignment(rotation=R, translation=t,
                     rmsd_angstrom=_rmsd(X @ R.T + t, Y),
                     rmsd_before_angstrom=_rmsd(X, Y),
                     fit_time_code=t0, pairs=keys)
