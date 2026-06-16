#!/usr/bin/env python3
"""
Authoritative physical properties for biochemistry-relevant ions.

Sources:
- Ionic radii: Shannon (1976) Acta Cryst. A32, 751-767
- Coordination numbers noted where relevant
"""

from .element_properties import ELEMENTS

# Ion data with Shannon ionic radii (coordination number VI unless noted)
IONS = {
    # =========================================================================
    # MONOVALENT CATIONS
    # =========================================================================
    "Na+": {
        "element": "Na",
        "charge": +1,
        "ionic_radius": 1.02,      # Shannon, VI coordination
        "ionic_radius_iv": 0.99,   # Shannon, IV coordination
        "hydrated_radius": 3.58,
        "cpk_color": (0.671, 0.361, 0.949),
        "bio_role": "Osmotic balance, nerve impulse, Na+/K+-ATPase",
    },
    "K+": {
        "element": "K",
        "charge": +1,
        "ionic_radius": 1.38,      # Shannon, VI
        "ionic_radius_iv": 1.37,   # Shannon, IV
        "hydrated_radius": 3.31,
        "cpk_color": (0.561, 0.251, 0.831),
        "bio_role": "Membrane potential, enzyme activation",
    },
    # =========================================================================
    # DIVALENT CATIONS
    # =========================================================================
    "Ca2+": {
        "element": "Ca",
        "charge": +2,
        "ionic_radius": 1.00,       # Shannon, VI
        "ionic_radius_viii": 1.12,  # Shannon, VIII (common in proteins)
        "hydrated_radius": 4.12,
        "cpk_color": (0.239, 1.000, 0.000),
        "bio_role": "Signaling, muscle contraction, bone",
    },
    "Mg2+": {
        "element": "Mg",
        "charge": +2,
        "ionic_radius": 0.72,      # Shannon, VI
        "ionic_radius_iv": 0.57,   # Shannon, IV
        "hydrated_radius": 4.28,
        "cpk_color": (0.541, 1.000, 0.000),
        "bio_role": "ATP binding, chlorophyll, enzyme cofactor",
    },
    "Zn2+": {
        "element": "Zn",
        "charge": +2,
        "ionic_radius": 0.74,      # Shannon, VI
        "ionic_radius_iv": 0.60,   # Shannon, IV (common in enzymes)
        "hydrated_radius": 4.30,
        "cpk_color": (0.490, 0.502, 0.690),
        "bio_role": "Zinc fingers, metalloenzymes, structural",
    },
    "Fe2+": {
        "element": "Fe",
        "charge": +2,
        "ionic_radius": 0.78,      # Shannon, VI, high spin
        "ionic_radius_ls": 0.61,   # Shannon, VI, low spin
        "hydrated_radius": 4.28,
        "cpk_color": (0.878, 0.400, 0.200),
        "bio_role": "Hemoglobin (deoxy), Fe-S clusters",
    },
    "Cu2+": {
        "element": "Cu",
        "charge": +2,
        "ionic_radius": 0.73,      # Shannon, VI
        "hydrated_radius": 4.19,
        "cpk_color": (0.784, 0.502, 0.200),
        "bio_role": "Plastocyanin, ceruloplasmin",
    },
    "Mn2+": {
        "element": "Mn",
        "charge": +2,
        "ionic_radius": 0.83,      # Shannon, VI, high spin
        "hydrated_radius": 4.38,
        "cpk_color": (0.612, 0.478, 0.780),
        "bio_role": "Photosystem II, arginase",
    },
    # =========================================================================
    # TRIVALENT CATIONS
    # =========================================================================
    "Fe3+": {
        "element": "Fe",
        "charge": +3,
        "ionic_radius": 0.65,      # Shannon, VI, high spin
        "ionic_radius_ls": 0.55,   # Shannon, VI, low spin
        "hydrated_radius": 4.57,
        "cpk_color": (0.878, 0.400, 0.200),
        "bio_role": "Hemoglobin (met), cytochromes, ferritin",
    },
    # =========================================================================
    # ANIONS
    # =========================================================================
    "Cl-": {
        "element": "Cl",
        "charge": -1,
        "ionic_radius": 1.81,      # Shannon, VI
        "hydrated_radius": 3.32,
        "cpk_color": (0.122, 0.941, 0.122),
        "bio_role": "Major biological anion, GABA receptors, HCl",
    },
}

# Radius scaling for ion visualization
ION_RADIUS_SCALES = {
    "points": 0.20,
    "balls": 0.40,
    "vdw": 1.00,     # Uses ionic radius
    "sticks": 0.25,
}


def get_ion_radius(ion_name: str, mode: str = "balls") -> float:
    """Get visualization radius for an ion."""
    if ion_name not in IONS:
        raise ValueError(f"Unknown ion: {ion_name}")
    if mode not in ION_RADIUS_SCALES:
        raise ValueError(f"Unknown mode: {mode}")

    ionic_radius = IONS[ion_name]["ionic_radius"]
    return ionic_radius * ION_RADIUS_SCALES[mode]


def get_ion_color(ion_name: str) -> tuple:
    """Get CPK color for an ion as RGB tuple (0-1 range)."""
    if ion_name not in IONS:
        raise ValueError(f"Unknown ion: {ion_name}")
    return IONS[ion_name]["cpk_color"]
