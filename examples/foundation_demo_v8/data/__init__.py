"""
Foundation Demo v8 - Scientific Data Module

Authoritative physical and chemical data for biochemistry atoms, ions, and residues.
"""

from .element_properties import ELEMENTS, get_scaled_radius, get_element_color
from .ion_properties import IONS, get_ion_radius, get_ion_color
from .residue_definitions import (
    RESIDUES, get_residue, get_all_residues, get_residue_atoms,
    get_residue_bonds, get_residue_type, get_type_color, TYPE_COLORS
)
from .residue_coordinates import RESIDUE_COORDINATES, get_residue_coordinates

__all__ = [
    "ELEMENTS",
    "IONS",
    "RESIDUES",
    "RESIDUE_COORDINATES",
    "TYPE_COLORS",
    "get_scaled_radius",
    "get_element_color",
    "get_ion_radius",
    "get_ion_color",
    "get_residue",
    "get_all_residues",
    "get_residue_atoms",
    "get_residue_bonds",
    "get_residue_type",
    "get_type_color",
    "get_residue_coordinates",
]
