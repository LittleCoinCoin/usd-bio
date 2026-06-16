#!/usr/bin/env python3
"""
Authoritative physical properties for biochemistry-relevant elements.

Sources:
- Van der Waals radii: Bondi (1964) J. Phys. Chem. 68, 441-451
- Covalent radii: Cordero et al. (2008) Dalton Trans. 2832-2838
- Atomic masses: IUPAC Standard Atomic Weights (2021)
- CPK colors: Corey-Pauling-Koltun / Jmol conventions
- Electronegativity: Pauling scale
"""

# RGB colors normalized to 0-1 range
ELEMENTS = {
    # =========================================================================
    # ORGANIC ELEMENTS (CHONPS)
    # =========================================================================
    "H": {
        "name": "Hydrogen",
        "atomic_number": 1,
        "atomic_mass": 1.008,
        "vdw_radius": 1.20,
        "covalent_radius": 0.31,
        "cpk_color": (1.000, 1.000, 1.000),  # White
        "electronegativity": 2.20,
        "common_oxidation_states": [+1, -1],
        "bio_notes": "Most abundant, hydrogen bonds, proton transfer",
    },
    "C": {
        "name": "Carbon",
        "atomic_number": 6,
        "atomic_mass": 12.011,
        "vdw_radius": 1.70,
        "covalent_radius": 0.76,
        "cpk_color": (0.200, 0.200, 0.200),  # Dark gray
        "electronegativity": 2.55,
        "common_oxidation_states": [-4, +4],
        "bio_notes": "Backbone of organic molecules",
    },
    "N": {
        "name": "Nitrogen",
        "atomic_number": 7,
        "atomic_mass": 14.007,
        "vdw_radius": 1.55,
        "covalent_radius": 0.71,
        "cpk_color": (0.188, 0.314, 0.973),  # Blue
        "electronegativity": 3.04,
        "common_oxidation_states": [-3, +3, +5],
        "bio_notes": "Amino acids, nucleotides, proteins",
    },
    "O": {
        "name": "Oxygen",
        "atomic_number": 8,
        "atomic_mass": 15.999,
        "vdw_radius": 1.52,
        "covalent_radius": 0.66,
        "cpk_color": (1.000, 0.051, 0.051),  # Red
        "electronegativity": 3.44,
        "common_oxidation_states": [-2],
        "bio_notes": "Water, carbohydrates, phosphates",
    },
    "P": {
        "name": "Phosphorus",
        "atomic_number": 15,
        "atomic_mass": 30.974,
        "vdw_radius": 1.80,
        "covalent_radius": 1.07,
        "cpk_color": (1.000, 0.502, 0.000),  # Orange
        "electronegativity": 2.19,
        "common_oxidation_states": [-3, +3, +5],
        "bio_notes": "ATP, DNA/RNA backbone, phospholipids",
    },
    "S": {
        "name": "Sulfur",
        "atomic_number": 16,
        "atomic_mass": 32.06,
        "vdw_radius": 1.80,
        "covalent_radius": 1.05,
        "cpk_color": (1.000, 1.000, 0.188),  # Yellow
        "electronegativity": 2.58,
        "common_oxidation_states": [-2, +4, +6],
        "bio_notes": "Cysteine, methionine, disulfide bonds",
    },
    # =========================================================================
    # TRANSITION METALS (biologically relevant)
    # =========================================================================
    "Fe": {
        "name": "Iron",
        "atomic_number": 26,
        "atomic_mass": 55.845,
        "vdw_radius": 2.05,
        "covalent_radius": 1.32,
        "cpk_color": (0.878, 0.400, 0.200),  # Orange-brown
        "electronegativity": 1.83,
        "common_oxidation_states": [+2, +3],
        "bio_notes": "Hemoglobin, cytochromes, Fe-S clusters",
    },
    "Zn": {
        "name": "Zinc",
        "atomic_number": 30,
        "atomic_mass": 65.38,
        "vdw_radius": 2.10,
        "covalent_radius": 1.22,
        "cpk_color": (0.490, 0.502, 0.690),  # Slate blue
        "electronegativity": 1.65,
        "common_oxidation_states": [+2],
        "bio_notes": "Zinc fingers, carbonic anhydrase, structural",
    },
    "Cu": {
        "name": "Copper",
        "atomic_number": 29,
        "atomic_mass": 63.546,
        "vdw_radius": 1.96,
        "covalent_radius": 1.32,
        "cpk_color": (0.784, 0.502, 0.200),  # Copper
        "electronegativity": 1.90,
        "common_oxidation_states": [+1, +2],
        "bio_notes": "Cytochrome c oxidase, plastocyanin",
    },
    "Mn": {
        "name": "Manganese",
        "atomic_number": 25,
        "atomic_mass": 54.938,
        "vdw_radius": 2.05,
        "covalent_radius": 1.39,
        "cpk_color": (0.612, 0.478, 0.780),  # Purple
        "electronegativity": 1.55,
        "common_oxidation_states": [+2, +3, +4],
        "bio_notes": "Photosystem II, superoxide dismutase",
    },
    "Co": {
        "name": "Cobalt",
        "atomic_number": 27,
        "atomic_mass": 58.933,
        "vdw_radius": 2.00,
        "covalent_radius": 1.26,
        "cpk_color": (0.941, 0.565, 0.627),  # Pink
        "electronegativity": 1.88,
        "common_oxidation_states": [+2, +3],
        "bio_notes": "Vitamin B12 (cobalamin)",
    },
    "Mo": {
        "name": "Molybdenum",
        "atomic_number": 42,
        "atomic_mass": 95.95,
        "vdw_radius": 2.17,
        "covalent_radius": 1.54,
        "cpk_color": (0.329, 0.710, 0.710),  # Teal
        "electronegativity": 2.16,
        "common_oxidation_states": [+4, +6],
        "bio_notes": "Nitrogenase, xanthine oxidase",
    },
    "Se": {
        "name": "Selenium",
        "atomic_number": 34,
        "atomic_mass": 78.971,
        "vdw_radius": 1.90,
        "covalent_radius": 1.20,
        "cpk_color": (1.000, 0.631, 0.000),  # Orange
        "electronegativity": 2.55,
        "common_oxidation_states": [-2, +4, +6],
        "bio_notes": "Selenocysteine (21st amino acid)",
    },
    # =========================================================================
    # ALKALI AND ALKALINE EARTH METALS
    # =========================================================================
    "Na": {
        "name": "Sodium",
        "atomic_number": 11,
        "atomic_mass": 22.990,
        "vdw_radius": 2.27,
        "covalent_radius": 1.66,
        "cpk_color": (0.671, 0.361, 0.949),  # Purple
        "electronegativity": 0.93,
        "common_oxidation_states": [+1],
        "bio_notes": "Na+/K+ pump, nerve impulses",
    },
    "K": {
        "name": "Potassium",
        "atomic_number": 19,
        "atomic_mass": 39.098,
        "vdw_radius": 2.75,
        "covalent_radius": 2.03,
        "cpk_color": (0.561, 0.251, 0.831),  # Purple
        "electronegativity": 0.82,
        "common_oxidation_states": [+1],
        "bio_notes": "Membrane potential, enzyme cofactor",
    },
    "Ca": {
        "name": "Calcium",
        "atomic_number": 20,
        "atomic_mass": 40.078,
        "vdw_radius": 2.31,
        "covalent_radius": 1.76,
        "cpk_color": (0.239, 1.000, 0.000),  # Green
        "electronegativity": 1.00,
        "common_oxidation_states": [+2],
        "bio_notes": "Bone, signaling, muscle contraction",
    },
    "Mg": {
        "name": "Magnesium",
        "atomic_number": 12,
        "atomic_mass": 24.305,
        "vdw_radius": 1.73,
        "covalent_radius": 1.41,
        "cpk_color": (0.541, 1.000, 0.000),  # Bright green
        "electronegativity": 1.31,
        "common_oxidation_states": [+2],
        "bio_notes": "ATP binding, chlorophyll, DNA stabilization",
    },
    # =========================================================================
    # HALOGENS
    # =========================================================================
    "Cl": {
        "name": "Chlorine",
        "atomic_number": 17,
        "atomic_mass": 35.45,
        "vdw_radius": 1.75,
        "covalent_radius": 1.02,
        "cpk_color": (0.122, 0.941, 0.122),  # Green
        "electronegativity": 3.16,
        "common_oxidation_states": [-1],
        "bio_notes": "Major anion, Cl- channels, gastric HCl",
    },
    "I": {
        "name": "Iodine",
        "atomic_number": 53,
        "atomic_mass": 126.904,
        "vdw_radius": 1.98,
        "covalent_radius": 1.39,
        "cpk_color": (0.580, 0.000, 0.580),  # Dark violet
        "electronegativity": 2.66,
        "common_oxidation_states": [-1],
        "bio_notes": "Thyroid hormones (T3, T4)",
    },
}

# Radius scaling factors for different visualization modes
RADIUS_SCALES = {
    "points": 0.15,    # Small dots for overview
    "balls": 0.30,     # Medium spheres
    "vdw": 1.00,       # Full van der Waals radii (space-filling)
    "ballstick": 0.25, # Smaller spheres for ball-and-stick with bonds
}


def get_scaled_radius(symbol: str, mode: str) -> float:
    """Get radius for an element in a specific visualization mode."""
    if symbol not in ELEMENTS:
        raise ValueError(f"Unknown element: {symbol}")
    if mode not in RADIUS_SCALES:
        raise ValueError(f"Unknown mode: {mode}. Use: {list(RADIUS_SCALES.keys())}")

    vdw_radius = ELEMENTS[symbol]["vdw_radius"]
    return vdw_radius * RADIUS_SCALES[mode]


def get_element_color(symbol: str) -> tuple:
    """Get CPK color for an element as RGB tuple (0-1 range)."""
    if symbol not in ELEMENTS:
        raise ValueError(f"Unknown element: {symbol}")
    return ELEMENTS[symbol]["cpk_color"]
