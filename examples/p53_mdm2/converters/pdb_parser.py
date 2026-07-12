#!/usr/bin/env python3
"""
Parse PDB files into structured Python data for USD assembly generation.

Generalized from foundation_demo_v8/converters/pdb_parser.py (R00: generalize).
The parsing CORE is unchanged (``_parse_atom_line``, ``infer_element``, the
dataclasses). What is generalized off ABL specifics:

- v8's ``EXCLUDED_RESIDUES`` / ``LIGAND_RESIDUES = {"atp","ATP"}`` module
  constants are GONE. Solvent/ion and ligand residue sets are CALLER-SUPPLIED
  parameters (``exclude_residues``, ``ligand_residues``). ``ligand_residues``
  defaults to empty -- no system carries a baked-in ligand name.
- v8's ``verify_pdb_parse()`` (which asserted the ABL+ATP system's hard-coded
  total and ligand atom counts) is GONE. Dataset counts belong in per-run test
  fixtures, not in library code (R00 anti-chimera invariant).
- Chain labels: when the PDB carries real chain-ID columns (RCSB files), they
  are respected; when the column is blank (AMBER files), chains are segmented
  by TER and labeled sequentially -- so both file styles parse correctly.

No USD imports: this module is a pure parser and stays USD-agnostic.
"""

import os
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional

# ---------------------------------------------------------------------------
# Generic defaults (NOT system-specific). Waters + common monoatomic ions in
# both RCSB (NA, CL) and AMBER (WAT, Na+, Cl-) naming. Callers override with an
# explicit set for their system; nothing here couples to any particular target.
# ---------------------------------------------------------------------------
DEFAULT_SOLVENT_IONS: FrozenSet[str] = frozenset({
    # waters
    "HOH", "WAT", "H2O", "DOD", "TIP", "TIP3", "TIP3P", "TIP4P", "SPC", "SOL",
    # monoatomic ions (RCSB uppercase + AMBER +/- naming)
    "NA", "Na+", "CL", "Cl-", "K", "K+", "MG", "Mg2+", "CA", "Ca2+",
    "ZN", "Zn2+", "MN", "Mn2+", "FE", "CU", "NI", "CO",
})

# AMBER histidine protonation variants (kept for callers that need to map them).
HISTIDINE_VARIANTS: FrozenSet[str] = frozenset({"HID", "HIE", "HIP"})


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
    element: str        # Inferred/parsed element symbol (e.g. "C", "N", "O")


@dataclass
class Residue:
    """A group of atoms forming a single residue."""
    name: str
    seq: int
    chain_id: str
    atoms: List[PDBAtom] = field(default_factory=list)


@dataclass
class Chain:
    """A group of residues forming a single chain."""
    chain_id: str
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
    """Infer an element symbol from a PDB atom name (fallback only).

    Used when the PDB has no element column (e.g. some AMBER files). Returns the
    first alphabetic character upper-cased -- correct for the single-letter
    organic elements (H, C, N, O, S, P) that dominate biomolecules.
    """
    for char in atom_name.strip():
        if char.isalpha():
            return char.upper()
    return "X"


def _parse_atom_line(line: str) -> Optional[dict]:
    """Parse a single ATOM/HETATM line into a dict of fields.

    Fixed-width PDB columns. Short lines (AMBER) are padded to avoid index
    errors. The element column (77-78) is used when present; otherwise the
    element is inferred from the atom name.
    """
    record_type = line[0:6].strip()
    if record_type not in ("ATOM", "HETATM"):
        return None

    padded = line.ljust(80)

    serial = int(padded[6:11].strip())
    atom_name = padded[12:16].strip()
    residue_name = padded[17:20].strip()
    chain_id_raw = padded[21].strip()   # blank in AMBER PDB files
    residue_seq = int(padded[22:26].strip())
    x = float(padded[30:38].strip())
    y = float(padded[38:46].strip())
    z = float(padded[46:54].strip())

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


def parse_pdb(
    pdb_path: str,
    *,
    exclude_residues: FrozenSet[str] = DEFAULT_SOLVENT_IONS,
    ligand_residues: FrozenSet[str] = frozenset(),
) -> PDBStructure:
    """Parse a PDB file into a structured :class:`PDBStructure`.

    Args:
        pdb_path: path to the PDB file.
        exclude_residues: residue names to drop (solvent/ions). Caller-supplied;
            defaults to a generic water+ion set. Pass ``frozenset()`` to keep
            everything.
        ligand_residues: residue names to treat as ligand (chain_type="ligand").
            Caller-supplied; defaults to empty -- no baked-in ligand name.

    Returns:
        PDBStructure with chains, residues, and atoms (positions in Ångström).

    Chain labeling:
        Atoms are segmented on TER records (preserving AMBER behavior). Each
        segment is labeled by its real chain-ID column when non-blank (RCSB
        files) or by a sequential A,B,C... scheme when blank (AMBER files).
        Segments sharing a label are merged into one chain.
    """
    if not os.path.exists(pdb_path):
        raise FileNotFoundError(f"PDB file not found: {pdb_path}")

    structure = PDBStructure(source_file=pdb_path)

    # First pass: TER-separated segments of kept atom records.
    segments: List[List[dict]] = []
    current_segment: List[dict] = []

    with open(pdb_path, "r") as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                parsed = _parse_atom_line(line)
                if parsed is None:
                    continue
                if parsed["residue_name"] in exclude_residues:
                    continue
                current_segment.append(parsed)
            elif line.startswith("TER"):
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []

    if current_segment:
        segments.append(current_segment)

    # Second pass: assign chain labels and build the structure.
    chain_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    blank_protein_idx = 0

    for segment in segments:
        if not segment:
            continue

        first_res_name = segment[0]["residue_name"]
        raw_id = segment[0]["chain_id_raw"]
        is_ligand = first_res_name in ligand_residues

        if raw_id:
            chain_id = raw_id
        elif is_ligand:
            chain_id = "L"
        else:
            if blank_protein_idx < len(chain_labels):
                chain_id = chain_labels[blank_protein_idx]
            else:
                chain_id = f"P{blank_protein_idx}"
            blank_protein_idx += 1

        chain_type = "ligand" if is_ligand else "protein"

        # Merge into an existing chain with the same label, else create one.
        chain = structure.chains.get(chain_id)
        if chain is None:
            chain = Chain(chain_id=chain_id, chain_type=chain_type)

        for atom_dict in segment:
            res_seq = atom_dict["residue_seq"]
            res_name = atom_dict["residue_name"]

            if res_seq not in chain.residues:
                chain.residues[res_seq] = Residue(
                    name=res_name, seq=res_seq, chain_id=chain_id
                )

            chain.residues[res_seq].atoms.append(PDBAtom(
                serial=atom_dict["serial"],
                name=atom_dict["atom_name"],
                residue_name=res_name,
                chain_id=chain_id,
                residue_seq=res_seq,
                x=atom_dict["x"],
                y=atom_dict["y"],
                z=atom_dict["z"],
                element=atom_dict["element"],
            ))

        if chain.residues:
            structure.chains[chain_id] = chain

    return structure


def parse_solvent(
    pdb_path: str,
    solvent_residues: FrozenSet[str] = frozenset({"WAT", "HOH", "TIP3P", "SOL", "H2O"}),
) -> list:
    """Return solvent oxygen coordinates (one point per water molecule).

    A separate, USD-agnostic entry point so callers can choose protein-only vs.
    protein+solvent independently. The solvent residue set is a parameter.

    Returns a plain list of (x, y, z) float tuples in Ångström.
    """
    if not os.path.exists(pdb_path):
        raise FileNotFoundError(f"PDB file not found: {pdb_path}")

    coords: list = []
    with open(pdb_path, "r") as f:
        for line in f:
            if not line.startswith(("ATOM", "HETATM")):
                continue
            parsed = _parse_atom_line(line)
            if parsed is None:
                continue
            if parsed["residue_name"] not in solvent_residues:
                continue
            if parsed["atom_name"] == "O":  # one position per water
                coords.append((parsed["x"], parsed["y"], parsed["z"]))
    return coords
