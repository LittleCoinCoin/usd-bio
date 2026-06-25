#!/usr/bin/env python3
"""
Convert XTC trajectory frames into USD Value Clip files.

Reads MD trajectory data via mdtraj, selects protein+ligand atoms,
and writes clip .usda files containing time-sampled xformOp:translate
values matching the assembly prim paths.

Pattern applied (from docs):
- 05_payloads_arc.md: Heavy data loaded on demand
- Value Clips: static topology + time-varying positions
"""

import os
import sys
import math

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from usdbio_env import get_data_dir

import mdtraj as md
import numpy as np
from pxr import Usd, UsdGeom, Sdf, Gf

from converters.pdb_parser import parse_pdb, PDBStructure
from data import RESIDUES

# Bond connectivity for residues not in RESIDUES (heavy atoms only)
EXTRA_BONDS = {
    "ACE": [("CH3", "C"), ("C", "O")],
    "NME": [("N", "CH3")],
    "HID": RESIDUES["HIS"]["bonds"],
    "HIE": RESIDUES["HIS"]["bonds"],
    "HIP": RESIDUES["HIS"]["bonds"],
    "atp": [
        ("PG", "O1G"), ("PG", "O2G"), ("PG", "O3G"), ("PG", "O3B"),
        ("O3B", "PB"), ("PB", "O1B"), ("PB", "O2B"), ("PB", "O3A"),
        ("O3A", "PA"), ("PA", "O1A"), ("PA", "O2A"), ("PA", "O5*"),
        ("O5*", "C5*"), ("C5*", "C4*"), ("C4*", "O4*"), ("C4*", "C3*"),
        ("O4*", "C1*"), ("C1*", "N9"), ("C1*", "C2*"),
        ("C2*", "O2*"), ("C2*", "C3*"), ("C3*", "O3*"),
        ("N9", "C8"), ("N9", "C4"), ("C8", "N7"), ("N7", "C5"),
        ("C5", "C6"), ("C5", "C4"), ("C6", "N6"), ("C6", "N1"),
        ("N1", "C2"), ("C2", "N3"), ("N3", "C4"),
    ],
}


def _get_bond_pairs(residue_name: str) -> list:
    """Get bond pairs for a residue."""
    if residue_name in RESIDUES:
        return RESIDUES[residue_name]["bonds"]
    if residue_name in EXTRA_BONDS:
        return EXTRA_BONDS[residue_name]
    return []


# Default paths — root from environment; fails loudly if USDBIO_DATA_DIR is unset
DEFAULT_PDB = os.path.join(get_data_dir(), "files", "atp-complex-solv35.pdb")
DEFAULT_XTC = os.path.join(get_data_dir(), "analysis", "0_traj", "sort_traj_1.xtc")


def sanitize_name(name: str) -> str:
    """Make a string safe for use as a USD prim name."""
    result = name.replace("+", "plus").replace("-", "minus")
    result = result.replace("*", "s").replace("'", "p")
    if result and result[0].isdigit():
        result = "_" + result
    return result


def build_prim_paths(structure: PDBStructure) -> list:
    """Build ordered list of USD prim paths matching PDB atom order.

    Returns paths in the same order atoms appear in the PDB file,
    which matches mdtraj's atom ordering after selection.
    """
    paths = []
    for chain_id, chain in structure.chains.items():
        chain_label = f"Chain_{chain_id}"
        for res_seq, residue in chain.residues.items():
            res_label = f"{sanitize_name(residue.name)}_{res_seq}"
            for atom in residue.atoms:
                atom_label = sanitize_name(atom.name)
                path = f"/ABLComplex/{chain_label}/{res_label}/{atom_label}"
                paths.append(path)
    return paths


def build_bond_info(structure: PDBStructure, atom_paths: list) -> list:
    """Build bond info mapping bond prims to their two atom indices.

    Returns list of dicts: {bond_path, cyl_path, atom1_idx, atom2_idx}
    where atom indices point into the flat positions array.
    """
    # Build lookup: atom prim path -> index in flat array
    path_to_idx = {p: i for i, p in enumerate(atom_paths)}

    bonds = []

    for chain_id, chain in structure.chains.items():
        chain_label = f"Chain_{chain_id}"
        res_seq_list = list(chain.residues.keys())

        for res_seq, residue in chain.residues.items():
            res_label = f"{sanitize_name(residue.name)}_{res_seq}"
            res_prefix = f"/ABLComplex/{chain_label}/{res_label}"

            # Build atom name -> path for this residue
            atom_name_to_path = {}
            for atom in residue.atoms:
                atom_label = sanitize_name(atom.name)
                atom_name_to_path[atom.name] = f"{res_prefix}/{atom_label}"

            # Intra-residue bonds
            for a1_name, a2_name in _get_bond_pairs(residue.name):
                p1 = atom_name_to_path.get(a1_name)
                p2 = atom_name_to_path.get(a2_name)
                if p1 is None or p2 is None:
                    continue
                if p1 not in path_to_idx or p2 not in path_to_idx:
                    continue
                bond_label = f"Bond_{sanitize_name(a1_name)}_{sanitize_name(a2_name)}"
                bond_path = f"{res_prefix}/{bond_label}"
                bonds.append({
                    "bond_path": bond_path,
                    "cyl_path": f"{bond_path}/Cylinder",
                    "atom1_idx": path_to_idx[p1],
                    "atom2_idx": path_to_idx[p2],
                })

        # Inter-residue peptide bonds
        for idx in range(len(res_seq_list) - 1):
            seq_i = res_seq_list[idx]
            seq_j = res_seq_list[idx + 1]
            res_i = chain.residues[seq_i]
            res_j = chain.residues[seq_j]

            res_i_label = f"{sanitize_name(res_i.name)}_{seq_i}"
            res_j_label = f"{sanitize_name(res_j.name)}_{seq_j}"
            prefix_i = f"/ABLComplex/{chain_label}/{res_i_label}"
            prefix_j = f"/ABLComplex/{chain_label}/{res_j_label}"

            c_path = f"{prefix_i}/C"
            n_path = f"{prefix_j}/N"
            if c_path not in path_to_idx or n_path not in path_to_idx:
                continue

            bond_label = f"PeptideBond_{res_i_label}__{res_j_label}"
            bond_path = f"/ABLComplex/{chain_label}/{bond_label}"
            bonds.append({
                "bond_path": bond_path,
                "cyl_path": f"{bond_path}/Cylinder",
                "atom1_idx": path_to_idx[c_path],
                "atom2_idx": path_to_idx[n_path],
            })

    return bonds


def compute_bond_xform(pos1, pos2):
    """Compute bond midpoint, orientation quaternion, and length.

    Returns (midpoint_Vec3d, quat_Quatf, length_float).
    """
    p1 = Gf.Vec3d(float(pos1[0]), float(pos1[1]), float(pos1[2]))
    p2 = Gf.Vec3d(float(pos2[0]), float(pos2[1]), float(pos2[2]))
    midpoint = (p1 + p2) / 2
    bond_vec = p2 - p1
    bond_length = bond_vec.GetLength()

    y_axis = Gf.Vec3d(0, 1, 0)
    bond_dir = bond_vec.GetNormalized()
    rot_axis = y_axis ^ bond_dir

    if rot_axis.GetLength() > 0.001:
        rot_axis = rot_axis.GetNormalized()
        cos_angle = y_axis * bond_dir
        angle_deg = math.degrees(math.acos(max(-1, min(1, cos_angle))))
        rotation = Gf.Rotation(Gf.Vec3d(rot_axis), angle_deg)
        quat = Gf.Quatf(rotation.GetQuat())
    else:
        if (y_axis * bond_dir) > 0:
            quat = Gf.Quatf(1, 0, 0, 0)
        else:
            quat = Gf.Quatf(0, 1, 0, 0)

    return midpoint, quat, bond_length


def extract_frames(pdb_path: str, xtc_path: str,
                   num_frames: int = 20, stride: int = None) -> tuple:
    """Extract trajectory frames for protein+ligand atoms.

    Args:
        pdb_path: Path to PDB topology file.
        xtc_path: Path to XTC trajectory file.
        num_frames: Target number of frames to extract.
        stride: Frame stride. If None, computed from num_frames.

    Returns:
        (positions, n_frames) where positions is (n_frames, n_atoms, 3)
        in Angstroms.
    """
    # Load topology to determine atom count and compute stride
    topo = md.load_pdb(pdb_path)
    protein_idx = topo.topology.select("protein")
    atp_idx = topo.topology.select("resname atp or resname ATP")
    combined = np.sort(np.concatenate([protein_idx, atp_idx]))

    if stride is None:
        # Estimate total frames from a quick scan
        test_traj = md.load(xtc_path, top=pdb_path,
                            atom_indices=combined[:1], stride=1000)
        estimated_total = test_traj.n_frames * 1000
        stride = max(1, estimated_total // num_frames)
        print(f"  Estimated total frames: ~{estimated_total}, using stride={stride}")

    # Load frames
    print(f"  Loading XTC with stride={stride}...")
    traj = md.load(xtc_path, top=pdb_path,
                   atom_indices=combined, stride=stride)

    # Convert nm -> Angstroms
    positions = traj.xyz * 10.0

    print(f"  Loaded {traj.n_frames} frames, {traj.n_atoms} atoms")
    return positions, traj.n_frames


def write_clip_file(output_path: str, prim_paths: list,
                    positions: np.ndarray, bond_info: list):
    """Write a USD clip file with time-sampled atom and bond transforms.

    Args:
        output_path: Path for the output .usda clip file.
        prim_paths: Ordered list of atom prim paths.
        positions: Array of shape (n_frames, n_atoms, 3) in Angstroms.
        bond_info: List of bond dicts from build_bond_info().
    """
    n_frames, n_atoms, _ = positions.shape
    assert len(prim_paths) == n_atoms, \
        f"Path count ({len(prim_paths)}) != atom count ({n_atoms})"

    if os.path.exists(output_path):
        os.remove(output_path)

    stage = Usd.Stage.CreateNew(output_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1e-10)  # coordinates in Ångström (1 Å = 1e-10 m)
    stage.SetMetadata("comment",
        f"Trajectory clip: {n_frames} frames, {n_atoms} atoms, "
        f"{len(bond_info)} bonds")

    # Write time-sampled translate ops for each atom
    for atom_idx, prim_path in enumerate(prim_paths):
        xform = UsdGeom.Xform.Define(stage, prim_path)
        translate_op = xform.AddTranslateOp()

        for frame_idx in range(n_frames):
            pos = positions[frame_idx, atom_idx]
            translate_op.Set(
                Gf.Vec3d(float(pos[0]), float(pos[1]), float(pos[2])),
                Usd.TimeCode(frame_idx)
            )

        if atom_idx % 500 == 0:
            print(f"    Atoms: {atom_idx}/{n_atoms}...")

    # Write time-sampled bond transforms (translate, orient, height)
    for bond_idx, bond in enumerate(bond_info):
        bond_xform = UsdGeom.Xform.Define(stage, bond["bond_path"])
        translate_op = bond_xform.AddTranslateOp()
        orient_op = bond_xform.AddOrientOp()

        cyl = UsdGeom.Cylinder.Define(stage, bond["cyl_path"])
        height_attr = cyl.CreateHeightAttr()

        a1 = bond["atom1_idx"]
        a2 = bond["atom2_idx"]

        for frame_idx in range(n_frames):
            midpoint, quat, length = compute_bond_xform(
                positions[frame_idx, a1], positions[frame_idx, a2]
            )
            tc = Usd.TimeCode(frame_idx)
            translate_op.Set(midpoint, tc)
            orient_op.Set(quat, tc)
            height_attr.Set(length, tc)

        if bond_idx % 500 == 0:
            print(f"    Bonds: {bond_idx}/{len(bond_info)}...")

    stage.Save()
    print(f"  Created clip: {output_path}")
    print(f"    Frames: {n_frames}, Atoms: {n_atoms}, Bonds: {len(bond_info)}")


def generate_clips(pdb_path: str, xtc_path: str, output_dir: str,
                   num_frames: int = 20) -> dict:
    """Full pipeline: PDB parse -> XTC extract -> clip file.

    Returns dict with clip metadata for UsdClipsAPI configuration.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Parse PDB for prim path and bond mapping
    print("Parsing PDB for prim paths and bond info...")
    structure = parse_pdb(pdb_path)
    prim_paths = build_prim_paths(structure)
    bond_info = build_bond_info(structure, prim_paths)
    print(f"  {len(prim_paths)} atom prim paths, {len(bond_info)} bonds")

    # Extract frames
    print("Extracting trajectory frames...")
    positions, n_frames = extract_frames(pdb_path, xtc_path,
                                         num_frames=num_frames)

    # Write clip file
    clip_filename = "trajectory_clip.usda"
    clip_path = os.path.join(output_dir, clip_filename)
    print("Writing clip file...")
    write_clip_file(clip_path, prim_paths, positions, bond_info)

    return {
        "clip_path": clip_path,
        "clip_filename": clip_filename,
        "n_frames": n_frames,
        "n_atoms": len(prim_paths),
        "start_frame": 0,
        "end_frame": n_frames - 1,
    }


def verify_clips(clip_path: str, n_expected_atoms: int = 4676):
    """Verify clip file structure."""
    stage = Usd.Stage.Open(clip_path)

    print("\n--- Clip Verification ---")

    # Check a sample atom has time samples
    sample_path = "/ABLComplex/Chain_A/ACE_1/HH31"
    sample = stage.GetPrimAtPath(sample_path)
    assert sample.IsValid(), f"Sample prim not found: {sample_path}"

    xformable = UsdGeom.Xformable(sample)
    ops = xformable.GetOrderedXformOps()
    assert len(ops) > 0, "No xform ops on sample atom"

    translate_op = ops[0]
    time_samples = translate_op.GetTimeSamples()
    assert len(time_samples) > 1, f"Expected multiple time samples, got {len(time_samples)}"
    print(f"  PASS: sample atom has {len(time_samples)} time samples")

    # Check positions differ between frames
    pos0 = translate_op.Get(Usd.TimeCode(time_samples[0]))
    pos1 = translate_op.Get(Usd.TimeCode(time_samples[-1]))
    diff = (Gf.Vec3d(pos0) - Gf.Vec3d(pos1)).GetLength()
    assert diff > 0.1, f"First/last frame positions are too similar (diff={diff})"
    print(f"  PASS: positions change between frames (diff={diff:.2f} A)")

    # Check ATP atom exists
    atp_path = "/ABLComplex/Chain_L/atp_293/PG"
    atp = stage.GetPrimAtPath(atp_path)
    assert atp.IsValid(), f"ATP atom not found: {atp_path}"
    print(f"  PASS: ATP atom present in clip")

    # Check a bond has time-sampled translate and orient
    bond_path = "/ABLComplex/Chain_A/SER_2/Bond_N_CA"
    bond = stage.GetPrimAtPath(bond_path)
    assert bond.IsValid(), f"Sample bond not found: {bond_path}"
    bond_xformable = UsdGeom.Xformable(bond)
    bond_ops = bond_xformable.GetOrderedXformOps()
    op_names = [op.GetOpName() for op in bond_ops]
    assert "xformOp:translate" in op_names, f"Bond missing translate op: {op_names}"
    assert "xformOp:orient" in op_names, f"Bond missing orient op: {op_names}"
    bond_ts = bond_ops[0].GetTimeSamples()
    assert len(bond_ts) > 1, f"Bond should have time samples, got {len(bond_ts)}"
    print(f"  PASS: sample bond has {len(bond_ts)} time samples (translate + orient)")

    # Check bond cylinder has time-sampled height
    cyl_path = f"{bond_path}/Cylinder"
    cyl = stage.GetPrimAtPath(cyl_path)
    assert cyl.IsValid(), f"Bond cylinder not found: {cyl_path}"
    height_attr = cyl.GetAttribute("height")
    height_ts = height_attr.GetTimeSamples()
    assert len(height_ts) > 1, f"Cylinder height should have time samples"
    print(f"  PASS: bond cylinder height animated ({len(height_ts)} samples)")

    print("\n  ALL VERIFICATIONS PASSED")


if __name__ == "__main__":
    pdb_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDB
    xtc_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_XTC

    output_dir = os.path.join(root_dir, "output", "clips")

    print(f"PDB: {pdb_path}")
    print(f"XTC: {xtc_path}")
    print(f"Output: {output_dir}")

    clip_info = generate_clips(pdb_path, xtc_path, output_dir, num_frames=20)
    verify_clips(clip_info["clip_path"])
