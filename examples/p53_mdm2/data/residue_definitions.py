"""
Amino acid residue definitions for molecular visualization.

Contains atom compositions, bond connectivity, and classification
for all 20 standard amino acids plus 2 common modifications.
"""

# Residue definitions
# Format: 3-letter code -> {one_letter, type, atoms: [(name, element)], bonds: [(a1, a2)]}
RESIDUES = {
    "ALA": {
        "one_letter": "A",
        "type": "nonpolar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB")],
    },
    "ARG": {
        "one_letter": "R",
        "type": "charged_positive",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("CD", "C"), ("NE", "N"), ("CZ", "C"), ("NH1", "N"), ("NH2", "N")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "CD"), ("CD", "NE"), ("NE", "CZ"), ("CZ", "NH1"), ("CZ", "NH2")],
    },
    "ASN": {
        "one_letter": "N",
        "type": "polar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("OD1", "O"), ("ND2", "N")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "OD1"), ("CG", "ND2")],
    },
    "ASP": {
        "one_letter": "D",
        "type": "charged_negative",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("OD1", "O"), ("OD2", "O")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "OD1"), ("CG", "OD2")],
    },
    "CYS": {
        "one_letter": "C",
        "type": "polar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"), ("SG", "S")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "SG")],
    },
    "GLN": {
        "one_letter": "Q",
        "type": "polar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("CD", "C"), ("OE1", "O"), ("NE2", "N")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "CD"), ("CD", "OE1"), ("CD", "NE2")],
    },
    "GLU": {
        "one_letter": "E",
        "type": "charged_negative",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("CD", "C"), ("OE1", "O"), ("OE2", "O")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "CD"), ("CD", "OE1"), ("CD", "OE2")],
    },
    "GLY": {
        "one_letter": "G",
        "type": "nonpolar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O")],
    },
    "HIS": {
        "one_letter": "H",
        "type": "aromatic",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("ND1", "N"), ("CD2", "C"), ("CE1", "C"), ("NE2", "N")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "ND1"), ("CG", "CD2"), ("ND1", "CE1"), ("CE1", "NE2"), ("NE2", "CD2")],
    },
    "ILE": {
        "one_letter": "I",
        "type": "nonpolar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG1", "C"), ("CG2", "C"), ("CD1", "C")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG1"),
                  ("CB", "CG2"), ("CG1", "CD1")],
    },
    "LEU": {
        "one_letter": "L",
        "type": "nonpolar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("CD1", "C"), ("CD2", "C")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "CD1"), ("CG", "CD2")],
    },
    "LYS": {
        "one_letter": "K",
        "type": "charged_positive",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("CD", "C"), ("CE", "C"), ("NZ", "N")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "CD"), ("CD", "CE"), ("CE", "NZ")],
    },
    "MET": {
        "one_letter": "M",
        "type": "nonpolar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("SD", "S"), ("CE", "C")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "SD"), ("SD", "CE")],
    },
    "PHE": {
        "one_letter": "F",
        "type": "aromatic",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("CD1", "C"), ("CD2", "C"), ("CE1", "C"), ("CE2", "C"), ("CZ", "C")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "CD1"), ("CG", "CD2"), ("CD1", "CE1"), ("CD2", "CE2"), ("CE1", "CZ"), ("CE2", "CZ")],
    },
    "PRO": {
        "one_letter": "P",
        "type": "nonpolar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("CD", "C")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "CD"), ("CD", "N")],
    },
    "SER": {
        "one_letter": "S",
        "type": "polar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"), ("OG", "O")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "OG")],
    },
    "THR": {
        "one_letter": "T",
        "type": "polar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("OG1", "O"), ("CG2", "C")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "OG1"), ("CB", "CG2")],
    },
    "TRP": {
        "one_letter": "W",
        "type": "aromatic",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("CD1", "C"), ("CD2", "C"), ("NE1", "N"), ("CE2", "C"),
                  ("CE3", "C"), ("CZ2", "C"), ("CZ3", "C"), ("CH2", "C")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "CD1"), ("CG", "CD2"), ("CD1", "NE1"), ("NE1", "CE2"), ("CD2", "CE2"),
                  ("CD2", "CE3"), ("CE2", "CZ2"), ("CE3", "CZ3"), ("CZ2", "CH2"), ("CZ3", "CH2")],
    },
    "TYR": {
        "one_letter": "Y",
        "type": "aromatic",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG", "C"), ("CD1", "C"), ("CD2", "C"), ("CE1", "C"), ("CE2", "C"),
                  ("CZ", "C"), ("OH", "O")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG"),
                  ("CG", "CD1"), ("CG", "CD2"), ("CD1", "CE1"), ("CD2", "CE2"),
                  ("CE1", "CZ"), ("CE2", "CZ"), ("CZ", "OH")],
    },
    "VAL": {
        "one_letter": "V",
        "type": "nonpolar",
        "atoms": [("N", "N"), ("CA", "C"), ("C", "C"), ("O", "O"), ("CB", "C"),
                  ("CG1", "C"), ("CG2", "C")],
        "bonds": [("N", "CA"), ("CA", "C"), ("C", "O"), ("CA", "CB"), ("CB", "CG1"), ("CB", "CG2")],
    },
}

# Classification for coloring by type
RESIDUE_TYPES = {
    "nonpolar": ["ALA", "GLY", "ILE", "LEU", "MET", "PRO", "VAL"],
    "polar": ["ASN", "CYS", "GLN", "SER", "THR"],
    "aromatic": ["HIS", "PHE", "TRP", "TYR"],
    "charged_positive": ["ARG", "LYS"],
    "charged_negative": ["ASP", "GLU"],
}

# Type colors for visualization
TYPE_COLORS = {
    "nonpolar": (0.8, 0.8, 0.8),        # Light gray
    "polar": (0.4, 0.8, 0.4),           # Green
    "aromatic": (0.8, 0.6, 0.2),        # Orange
    "charged_positive": (0.2, 0.4, 0.9),  # Blue
    "charged_negative": (0.9, 0.2, 0.2),  # Red
}


def get_residue(code: str) -> dict:
    """Get residue definition by 3-letter code."""
    if code not in RESIDUES:
        raise ValueError(f"Unknown residue: {code}")
    return RESIDUES[code]


def get_all_residues() -> list:
    """Return list of all residue 3-letter codes."""
    return list(RESIDUES.keys())


def get_residue_atoms(code: str) -> list:
    """Return list of (atom_name, element) tuples for a residue."""
    return RESIDUES[code]["atoms"]


def get_residue_bonds(code: str) -> list:
    """Return list of (atom1, atom2) bond tuples for a residue."""
    return RESIDUES[code]["bonds"]


def get_residue_type(code: str) -> str:
    """Return the classification type of a residue."""
    return RESIDUES[code]["type"]


def get_type_color(residue_type: str) -> tuple:
    """Return RGB color for a residue type."""
    return TYPE_COLORS.get(residue_type, (0.5, 0.5, 0.5))
