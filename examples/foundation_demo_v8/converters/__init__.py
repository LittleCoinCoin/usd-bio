"""
Converters for importing external data formats into USD-compatible structures.
"""

from .pdb_parser import parse_pdb, PDBAtom
from .xtc_to_clips import generate_clips
