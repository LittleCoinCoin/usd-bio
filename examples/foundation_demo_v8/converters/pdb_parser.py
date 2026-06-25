#!/usr/bin/env python3
"""
Parse PDB files into structured Python data for USD assembly generation.

Handles AMBER-format PDB files (no chain ID column, no element column).
Chain boundaries are detected via TER records. Elements are inferred
from atom names.

Filters out solvent (WAT), ions (Na+, Cl-), and cofactors (MG) to
extract only protein + ligand atoms.
"""

import os
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# Residue names to exclude (solvent, ions, cofactors)
EXCLUDED_RESIDUES = {"WAT", "Na+", "Cl-", "MG"}

# AMBER histidine protonation variants -> standard HIS
HISTIDINE_VARIANTS = {"HID", "HIE", "HIP"}

# Known ligand residue names (lowercase in AMBER)
LIGAND_RESIDUES = {"atp", "ATP"}


@dataclass
class PDBAtom:
    """A single atom parsed from a PDB ATOM/HETATM record."""
    serial: int
    name: str           # Atom name (stripped, e.g. "CA", "HH31")
    residue_name: str   # Residue name (e.g. "SER", "atp")
    chain_id: str       # Assigned chain label (e.g. "A", "B", "L")
    residue_seq: int    # Residue sequence number
    x: float
    y: float
    z: float
    element: str        # Inferred element symbol (e.g. "C", "N", "O")


@dataclass
class Residue:
    """A group of atoms forming a single residue."""
    name: str           # Residue name (e.g. "SER", "atp")
    seq: int            # Sequence number
    chain_id: str       # Parent chain ID
    atoms: List[PDBAtom] = field(default_factory=list)


@dataclass
class Chain:
    """A group of residues forming a single chain."""
    chain_id: str       # Chain label (e.g. "A", "B", "L")
    residues: "OrderedDict[int, Residue]" = field(default_factory=OrderedDict)
    chain_type: str = "protein"  # "protein" or "ligand"


@dataclass
class PDBStructure:
    """Complete parsed PDB structure with chains, residues, and atoms."""
    chains: "OrderedDict[str, Chain]" = field(default_factory=OrderedDict)
    source_file: str = ""

    @property
    def atom_count(self) -> int:
        return sum(
            len(res.atoms)
            for chain in self.chains.values()
            for res in chain.residues.values()
        )

    @property
    def residue_count(self) -> int:
        return sum(len(chain.residues) for chain in self.chains.values())

    @property
    def chain_ids(self) -> List[str]:
        return list(self.chains.keys())

    @property
    def elements(self) -> set:
        return {
            atom.element
            for chain in self.chains.values()
            for res in chain.residues.values()
            for atom in res.atoms
        }


def infer_element(atom_name: str) -> str:
    """Infer element symbol from PDB atom name.

    AMBER atom names follow the convention where the first alphabetic
    character indicates the element for single-letter elements (H, C, N, O, S, P).
    """
    stripped = atom_name.strip()
    for char in stripped:
        if char.isalpha():
            return char.upper()
    return "X"  # Unknown


def _parse_atom_line(line: str) -> Optional[dict]:
    """Parse a single ATOM/HETATM line into a dict of fields.

    Uses fixed-width column positions per PDB format specification.
    Handles AMBER-format files (shorter lines, blank chain ID).
    """
    record_type = line[0:6].strip()
    if record_type not in ("ATOM", "HETATM"):
        return None

    # Pad short lines to avoid index errors
    padded = line.ljust(80)

    serial = int(padded[6:11].strip())
    atom_name = padded[12:16].strip()
    residue_name = padded[17:20].strip()
    # Column 21 is chain ID (blank in AMBER PDB files)
    chain_id_raw = padded[21].strip()
    residue_seq = int(padded[22:26].strip())
    x = float(padded[30:38].strip())
    y = float(padded[38:46].strip())
    z = float(padded[46:54].strip())

    # Try element column (76-77) first, fall back to inference
    element_col = padded[76:78].strip()
    if element_col and element_col[0].isalpha():
        element = element_col
    else:
        element = infer_element(atom_name)

    return {
        "serial": serial,
        "atom_name": atom_name,
        "residue_name": residue_name,
        "chain_id_raw": chain_id_raw,
        "residue_seq": residue_seq,
        "x": x,
        "y": y,
        "z": z,
        "element": element,
    }


def parse_pdb(pdb_path: str, exclude_solvent: bool = True) -> PDBStructure:
    """Parse a PDB file into a structured PDBStructure.

    Reads ATOM/HETATM records, detects chain boundaries from TER records,
    assigns chain labels (A, B, C... for protein chains, L for ligand),
    and groups atoms by chain and residue.

    Args:
        pdb_path: Path to the PDB file.
        exclude_solvent: If True, exclude WAT, Na+, Cl-, MG residues.

    Returns:
        PDBStructure with chains, residues, and atoms.
    """
    if not os.path.exists(pdb_path):
        raise FileNotFoundError(f"PDB file not found: {pdb_path}")

    structure = PDBStructure(source_file=pdb_path)

    # First pass: collect all atom records grouped by TER-separated segments
    segments = []       # List of lists of atom dicts
    current_segment = []

    with open(pdb_path, 'r') as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                parsed = _parse_atom_line(line)
                if parsed is None:
                    continue

                res_name = parsed["residue_name"]

                # Filter excluded residues
                if exclude_solvent and res_name in EXCLUDED_RESIDUES:
                    continue

                current_segment.append(parsed)

            elif line.startswith("TER"):
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []

    # Don't forget the last segment if file doesn't end with TER
    if current_segment:
        segments.append(current_segment)

    # Second pass: assign chain IDs and build structure
    protein_chain_idx = 0
    chain_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for segment in segments:
        if not segment:
            continue

        # Determine chain type from first residue
        first_res_name = segment[0]["residue_name"]
        is_ligand = first_res_name in LIGAND_RESIDUES

        if is_ligand:
            chain_id = "L"
            chain_type = "ligand"
        else:
            if protein_chain_idx < len(chain_labels):
                chain_id = chain_labels[protein_chain_idx]
            else:
                chain_id = f"P{protein_chain_idx}"
            protein_chain_idx += 1
            chain_type = "protein"

        chain = Chain(chain_id=chain_id, chain_type=chain_type)

        for atom_dict in segment:
            res_seq = atom_dict["residue_seq"]
            res_name = atom_dict["residue_name"]

            if res_seq not in chain.residues:
                chain.residues[res_seq] = Residue(
                    name=res_name,
                    seq=res_seq,
                    chain_id=chain_id,
                )

            atom = PDBAtom(
                serial=atom_dict["serial"],
                name=atom_dict["atom_name"],
                residue_name=res_name,
                chain_id=chain_id,
                residue_seq=res_seq,
                x=atom_dict["x"],
                y=atom_dict["y"],
                z=atom_dict["z"],
                element=atom_dict["element"],
            )
            chain.residues[res_seq].atoms.append(atom)

        if chain.residues:
            structure.chains[chain_id] = chain

    return structure


def parse_solvent(pdb_path: str) -> list:
    """Parse solvent residue oxygen-atom coordinates from a PDB file.

    Reads ATOM/HETATM records for residues named WAT, HOH, TIP3P, or SOL and
    returns the (x, y, z) coordinate of each oxygen atom — one point per water
    molecule.  Returns a plain list of (float, float, float) tuples with no USD
    types, keeping the parser USD-agnostic.

    This is a separate entry point from parse_pdb() so callers can choose
    protein-only vs. protein+solvent independently without breaking existing callers
    that expect only protein/ligand records.

    Args:
        pdb_path: Path to the PDB file.

    Returns:
        List of (x, y, z) float tuples, one per solvent oxygen atom (Ångstroms).
    """
    if not os.path.exists(pdb_path):
        raise FileNotFoundError(f"PDB file not found: {pdb_path}")

    SOLVENT_RESIDUES = {"WAT", "HOH", "TIP3P", "SOL"}
    coords: list = []

    with open(pdb_path, "r") as f:
        for line in f:
            if not line.startswith(("ATOM", "HETATM")):
                continue
            parsed = _parse_atom_line(line)
            if parsed is None:
                continue
            if parsed["residue_name"] not in SOLVENT_RESIDUES:
                continue
            # Collect only the oxygen atom — one position per water molecule
            if parsed["atom_name"] == "O":
                coords.append((parsed["x"], parsed["y"], parsed["z"]))

    return coords


def verify_pdb_parse(structure: PDBStructure):
    """Verify the parsed PDB structure meets expected criteria.

    Prints diagnostic information and asserts correctness for the
    ABL kinase + ATP system.
    """
    print("\n--- PDB Parser Verification ---")
    print(f"Source: {structure.source_file}")

    # Chain summary
    print(f"\nChains: {structure.chain_ids}")
    for cid, chain in structure.chains.items():
        res_names = [r.name for r in chain.residues.values()]
        atom_count = sum(len(r.atoms) for r in chain.residues.values())
        print(f"  Chain {cid} ({chain.chain_type}): "
              f"{len(chain.residues)} residues, {atom_count} atoms "
              f"[{res_names[0]}..{res_names[-1]}]")

    # Total counts
    total_atoms = structure.atom_count
    total_residues = structure.residue_count
    print(f"\nTotal atoms: {total_atoms}")
    print(f"Total residues: {total_residues}")
    print(f"Elements: {sorted(structure.elements)}")

    # Assertions for ABL kinase + ATP
    assert total_atoms == 4676, f"Expected 4676 atoms, got {total_atoms}"
    print(f"  PASS: atom count = {total_atoms}")

    assert len(structure.chains) >= 2, f"Expected >= 2 chains, got {len(structure.chains)}"
    print(f"  PASS: chain count = {len(structure.chains)}")

    assert "L" in structure.chains, "Expected ligand chain 'L'"
    ligand_chain = structure.chains["L"]
    ligand_atoms = sum(len(r.atoms) for r in ligand_chain.residues.values())
    assert ligand_atoms == 43, f"Expected 43 ligand atoms, got {ligand_atoms}"
    print(f"  PASS: ligand (ATP) atoms = {ligand_atoms}")

    expected_elements = {"H", "C", "N", "O", "S", "P"}
    assert expected_elements.issubset(structure.elements), \
        f"Missing elements: {expected_elements - structure.elements}"
    print(f"  PASS: all expected elements present")

    # Check histidine variants are preserved
    all_res_names = {
        res.name
        for chain in structure.chains.values()
        for res in chain.residues.values()
    }
    his_variants = all_res_names & HISTIDINE_VARIANTS
    assert len(his_variants) > 0, "Expected at least one histidine variant (HID/HIE/HIP)"
    print(f"  PASS: histidine variants found: {sorted(his_variants)}")

    # Check caps are present
    assert "ACE" in all_res_names, "Expected ACE cap residue"
    assert "NME" in all_res_names, "Expected NME cap residue"
    print(f"  PASS: terminal caps (ACE, NME) present")

    print("\n  ALL VERIFICATIONS PASSED")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from usdbio_env import get_data_dir

    # Default path — root from environment; fails loudly if USDBIO_DATA_DIR is unset
    default_pdb = os.path.join(get_data_dir(), "files", "atp-complex-solv35.pdb")

    pdb_path = sys.argv[1] if len(sys.argv) > 1 else default_pdb

    print(f"Parsing: {pdb_path}")
    structure = parse_pdb(pdb_path)
    verify_pdb_parse(structure)
