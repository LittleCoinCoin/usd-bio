#!/usr/bin/env python3
"""
Test suite for element and ion data validation.

Verifies:
1. All required fields are present
2. Values are within physically reasonable ranges
3. Helper functions work correctly
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data import ELEMENTS, IONS, get_scaled_radius, get_element_color, get_ion_radius


def test_element_completeness():
    """Verify all elements have required fields."""
    required_fields = [
        "name",
        "atomic_number",
        "atomic_mass",
        "vdw_radius",
        "covalent_radius",
        "cpk_color",
        "electronegativity",
        "common_oxidation_states",
        "bio_notes",
    ]

    print("Testing element completeness...")
    for symbol, data in ELEMENTS.items():
        for field in required_fields:
            assert field in data, f"{symbol} missing field: {field}"
    print(f"  ✓ All {len(ELEMENTS)} elements have required fields")


def test_element_value_ranges():
    """Verify element values are physically reasonable."""
    print("Testing element value ranges...")

    for symbol, data in ELEMENTS.items():
        # Atomic number: 1-118
        assert 1 <= data["atomic_number"] <= 118, f"{symbol}: invalid atomic_number"

        # Atomic mass: 1-300 Da
        assert 1 <= data["atomic_mass"] <= 300, f"{symbol}: invalid atomic_mass"

        # VDW radius: 1.0-3.0 Å
        assert 1.0 <= data["vdw_radius"] <= 3.0, f"{symbol}: invalid vdw_radius"

        # Covalent radius: 0.2-2.5 Å
        assert 0.2 <= data["covalent_radius"] <= 2.5, f"{symbol}: invalid covalent_radius"

        # CPK color: RGB tuple with values 0-1
        assert len(data["cpk_color"]) == 3, f"{symbol}: cpk_color not RGB tuple"
        for c in data["cpk_color"]:
            assert 0.0 <= c <= 1.0, f"{symbol}: cpk_color value out of range"

        # Electronegativity: 0.7-4.0 (Pauling)
        assert 0.7 <= data["electronegativity"] <= 4.0, f"{symbol}: invalid electronegativity"

    print(f"  ✓ All {len(ELEMENTS)} elements have valid value ranges")


def test_ion_completeness():
    """Verify all ions have required fields."""
    required_fields = [
        "element",
        "charge",
        "ionic_radius",
        "cpk_color",
        "bio_role",
    ]

    print("Testing ion completeness...")
    for ion_name, data in IONS.items():
        for field in required_fields:
            assert field in data, f"{ion_name} missing field: {field}"
        # Verify element reference is valid
        assert data["element"] in ELEMENTS, f"{ion_name}: unknown element {data['element']}"

    print(f"  ✓ All {len(IONS)} ions have required fields")


def test_ion_value_ranges():
    """Verify ion values are physically reasonable."""
    print("Testing ion value ranges...")

    for ion_name, data in IONS.items():
        # Ionic radius: 0.3-2.5 Å
        assert 0.3 <= data["ionic_radius"] <= 2.5, f"{ion_name}: invalid ionic_radius"

        # Charge: -3 to +4
        assert -3 <= data["charge"] <= 4, f"{ion_name}: invalid charge"

        # CPK color: RGB tuple
        assert len(data["cpk_color"]) == 3, f"{ion_name}: cpk_color not RGB tuple"

    print(f"  ✓ All {len(IONS)} ions have valid value ranges")


def test_helper_functions():
    """Test helper functions work correctly."""
    print("Testing helper functions...")

    # Test get_scaled_radius
    for mode in ["points", "balls", "vdw", "sticks"]:
        radius = get_scaled_radius("C", mode)
        assert radius > 0, f"Invalid radius for C in {mode} mode"

    # Test get_element_color
    color = get_element_color("O")
    assert len(color) == 3
    assert color[0] > 0.9  # Red should be high for oxygen

    # Test get_ion_radius
    radius = get_ion_radius("Ca2+", "balls")
    assert radius > 0

    print("  ✓ All helper functions work correctly")


def test_biochemistry_coverage():
    """Verify all biochemistry-essential elements are present."""
    print("Testing biochemistry coverage...")

    # Essential organic elements (CHONPS)
    organic = ["H", "C", "N", "O", "P", "S"]
    for elem in organic:
        assert elem in ELEMENTS, f"Missing organic element: {elem}"

    # Common metal cofactors
    metals = ["Fe", "Zn", "Cu", "Mn", "Mg", "Ca"]
    for elem in metals:
        assert elem in ELEMENTS, f"Missing metal: {elem}"

    # Common ions
    common_ions = ["Na+", "K+", "Ca2+", "Mg2+", "Cl-", "Zn2+", "Fe2+", "Fe3+"]
    for ion in common_ions:
        assert ion in IONS, f"Missing ion: {ion}"

    print("  ✓ All biochemistry-essential elements/ions present")


def print_summary():
    """Print a summary of the data."""
    print("\n" + "=" * 60)
    print("ELEMENT AND ION DATA SUMMARY")
    print("=" * 60)

    print(f"\nElements: {len(ELEMENTS)}")
    print("  " + ", ".join(sorted(ELEMENTS.keys())))

    print(f"\nIons: {len(IONS)}")
    print("  " + ", ".join(sorted(IONS.keys())))

    print("\nVisualization modes:")
    from data.element_properties import RADIUS_SCALES
    for mode, scale in RADIUS_SCALES.items():
        print(f"  {mode}: {scale:.2f}x VDW radius")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_element_completeness()
    test_element_value_ranges()
    test_ion_completeness()
    test_ion_value_ranges()
    test_helper_functions()
    test_biochemistry_coverage()
    print_summary()
    print("\n✓ ALL TESTS PASSED")
