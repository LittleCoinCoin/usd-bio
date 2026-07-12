"""
p53_mdm2.data -- authoritative physical/chemical biochemistry reference data.

Reuse-as-is from foundation_demo_v8 (R00 classifies these modules as
reuse-as-is: no ABL coupling). Pure-Python constant tables and lookup
helpers -- no USD, no mdtraj imports -- so this package is safe to import
anywhere, including inside read-back tests as the source-of-truth against
which composed artifacts are checked (the anti-tautology guard).

Sources:
- Van der Waals radii: Bondi (1964) J. Phys. Chem. 68, 441-451
- Covalent radii: Cordero et al. (2008) Dalton Trans. 2832-2838
- Ionic radii: Shannon (1976) Acta Cryst. A32, 751-767
- CPK colors: Corey-Pauling-Koltun / Jmol conventions
"""

from .element_properties import ELEMENTS, get_scaled_radius, get_element_color
from .ion_properties import IONS, get_ion_radius, get_ion_color
from .residue_definitions import (
    RESIDUES,
    get_residue,
    get_all_residues,
    get_residue_atoms,
    get_residue_bonds,
    get_residue_type,
    get_type_color,
    TYPE_COLORS,
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
