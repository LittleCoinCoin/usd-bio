# Research Report: Atomic Abstraction in OpenUSD for Bioinformatics

**Topic**: Standardizing Atomic and Ionic Representations in USD
**Date**: 2026-01-20
**Status**: Final

---

## 1. Introduction

In the context of the USD-Bio project, atoms are the fundamental primitives of the "Biological Asset." To enable interoperability between molecular dynamics (MD) simulations, structural biology, and high-fidelity visualization, a standardized abstraction layer is required. This report defines the physical and visual parameters for common biochemical elements and ions, and outlines their implementation as OpenUSD classes.

## 2. Physical and Chemical Properties

The following table summarizes the key physical constants used for structural representation. *Van der Waals (vdW) radii* are used for neutral atoms to define space-filling models, while *Ionic radii* are used for charged species to accurately represent their effective volume in a hydrated or crystalline environment.

| Element/Ion | Symbol | vdW Radius (Å) | Ionic Radius (Å) | Common Valence |
| :--- | :--- | :--- | :--- | :--- |
| Hydrogen | H | 1.20 | - | 1 |
| Carbon | C | 1.70 | - | 4 |
| Nitrogen | N | 1.55 | 1.71 (N³⁻) | 3, 4 |
| Oxygen | O | 1.52 | 1.40 (O²⁻) | 2 |
| Phosphorus | P | 1.80 | - | 5 |
| Sulfur | S | 1.80 | 1.84 (S²⁻) | 2, 6 |
| Sodium | Na⁺ | 2.27 | 0.95 - 1.02 | 1 |
| Magnesium | Mg²⁺ | 1.73 | 0.65 - 0.72 | 2 |
| Chlorine | Cl⁻ | 1.75 | 1.81 | 1 |
| Potassium | K⁺ | 2.75 | 1.33 | 1 |
| Calcium | Ca²⁺ | 2.31 | 0.99 | 2 |

*Note: Radii values are approximate and may vary slightly based on the force field (e.g., AMBER vs CHARMM) or coordination state.*

## 3. Visual Representation: CPK Convention

The Corey-Pauling-Koltun (CPK) color scheme is the industry standard for molecular visualization. USD-Bio adopts these colors as default values in the base atom classes to ensure immediate recognizability for researchers.

| Element | Color (RGB) | Hex Code | Rationale |
| :--- | :--- | :--- | :--- |
| Hydrogen | (0.9, 0.9, 0.9) | #E6E6E6 | Light gray/White |
| Carbon | (0.5, 0.5, 0.5) | #808080 | Medium gray (Standard) |
| Nitrogen | (0.0, 0.0, 1.0) | #0000FF | Blue (Nitrogen gas/Sky) |
| Oxygen | (1.0, 0.0, 0.0) | #FF0000 | Red (Blood/Combustion) |
| Sulfur | (1.0, 1.0, 0.0) | #FFFF00 | Yellow (Elemental sulfur) |
| Phosphorus | (1.0, 0.6, 0.0) | #FFA500 | Orange |
| Halogens | (0.0, 1.0, 0.0) | #00FF00 | Green |
| Metals | (0.5, 0.5, 1.0) | #8080FF | Light blue/Silver |

## 4. Proposed USD Class Hierarchy

To implement this in OpenUSD, we utilize the `class` keyword to create non-instantiated "blueprints." These classes reside in the `/_class_` namespace.

### 4.1 Base Classes
*   `_class_Atom`: The root class. Contains common attributes like `mass`, `charge`, and `element`.
*   `_class_Ion`: Inherits from `_class_Atom`. Adds `formalCharge`.

### 4.2 Specific Element Classes
Each element (e.g., `_class_C`, `_class_O`) inherits from `_class_Atom` and sets:
1.  **`primvars:displayColor`**: The CPK color.
2.  **`radius`**: The vdW radius.
3.  **`inputs:element`**: String identifier for the element.

### 4.3 Implementation Strategy
In the `protein.usd` or `complex.usd` files, individual atoms will be defined as follows:

```usda
def sphere "Atom_123" (
    inherits = </_class_/C>
)
{
    double3 xformOp:translate = (12.5, 4.2, -1.0)
    # The color and radius are inherited from the class
}
```

This "Object-Oriented" approach allows for global style updates (e.g., changing all Carbon atoms to black) by modifying a single entry in the template file.

---
**References**:
- *Bondi, A. (1964). "van der Waals Volumes and Radii". J. Phys. Chem. 68 (3): 441–451.*
- *Corey, R. B., Pauling, L. (1953). "Molecular Models of Amino Acids, Peptides, and Proteins". Rev. Sci. Instrum. 24 (8): 621–627.*
