"""
Independent PDB re-derivation for the anti-tautology test guard.

This module intentionally DOES NOT use ``converters.pdb_parser``. It re-derives
atom/chain/element expectations from the raw PDB with a deliberately DIFFERENT
code path -- flat column slicing, chain grouping by the column-21 chain-ID
directly, no TER segmentation, no dataclasses. Read-back tests compare the
composed USD stage against THIS re-derivation, so a bug in the production
parser cannot silently agree with itself (the R00 anti-tautology invariant:
"assert against expectations independently re-derived from source data, never
against generator in-memory state").
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Set, Tuple


@dataclass
class RawExpectations:
    """Expectations re-derived directly from a PDB file (independent path)."""
    total_atoms: int = 0
    chain_atom_counts: Dict[str, int] = field(default_factory=dict)
    elements: Set[str] = field(default_factory=set)
    # (chain_id, residue_seq, atom_name) -> element symbol, for spot checks
    atom_elements: Dict[Tuple[str, int, str], str] = field(default_factory=dict)

    @property
    def chain_ids(self) -> Set[str]:
        return set(self.chain_atom_counts.keys())

    @property
    def chain_count(self) -> int:
        return len(self.chain_atom_counts)


def raw_pdb_expectations(
    pdb_path: str,
    exclude_residues: FrozenSet[str] = frozenset(),
) -> RawExpectations:
    """Re-derive counts/elements from a PDB via flat column parsing.

    Args:
        pdb_path: path to the PDB file.
        exclude_residues: residue names to skip (solvent/ions); should match
            what the generator excluded so the comparison is apples-to-apples.

    Returns:
        RawExpectations. Element per atom uses the PDB element column (77-78)
        when present, else the first alphabetic char of the atom name -- a
        minimal rule, independent of the production ``infer_element``.
    """
    if not os.path.exists(pdb_path):
        raise FileNotFoundError(f"PDB file not found: {pdb_path}")

    exp = RawExpectations()
    with open(pdb_path, "r") as f:
        for line in f:
            rec = line[0:6].strip()
            if rec not in ("ATOM", "HETATM"):
                continue
            padded = line.ljust(80)
            res_name = padded[17:20].strip()
            if res_name in exclude_residues:
                continue
            chain_id = padded[21].strip() or "_"
            atom_name = padded[12:16].strip()
            try:
                res_seq = int(padded[22:26].strip())
            except ValueError:
                continue

            elem_col = padded[76:78].strip()
            if elem_col and elem_col[0].isalpha():
                element = elem_col
            else:
                element = next((c.upper() for c in atom_name if c.isalpha()), "X")

            exp.total_atoms += 1
            exp.chain_atom_counts[chain_id] = exp.chain_atom_counts.get(chain_id, 0) + 1
            exp.elements.add(element)
            exp.atom_elements[(chain_id, res_seq, atom_name)] = element

    return exp
