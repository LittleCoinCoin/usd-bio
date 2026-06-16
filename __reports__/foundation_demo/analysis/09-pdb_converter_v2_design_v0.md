# Report: PDB Converter v2 Architecture (v0)

**Topic**: Refactoring PDB Conversion for Departmental Layering
**Source**: Analysis of ShinobuLab Data (`atp-complex-solv35.pdb`)
**Date**: 2026-01-20
**Status**: Design

---

## Executive Summary

The initial PDB converter (v1) created a monolithic USD file. To support the **Departmental Architecture** (Biology vs. Chemistry vs. Physics layers), Version 2 will deconstruct the PDB into semantic components. This allows independent versioning of the protein topology, the ligand position, and the solvent box.

---

## 1. Input Analysis

The source file `atp-complex-solv35.pdb` contains mixed data types identified by Residue Name:

| Component | Residue Names | Target USD Asset | USD Type |
| :--- | :--- | :--- | :--- |
| **Protein** | `ACE`, `ALA`, `ARG` ... `TYR` | `assets/protein.usd` | `UsdGeomPoints` (with Chain hierarchy) |
| **Ligand** | `atp` | `assets/ligand.usd` | `UsdGeomMesh` (Spheres) or `Points` |
| **Ions** | `Na+`, `Cl-`, `MG` | `assets/ions.usd` | `UsdGeomPointInstancer` |
| **Solvent** | `WAT` | `assets/solvent.usd` | `UsdGeomPointInstancer` |

---

## 2. Output Architecture

The converter will produce a set of files and a composition root.

### File Structure
```
examples/foundation_demo_v2/
├── assets/
│   ├── protein.usd      # The static biological machinery
│   ├── ligand.usd       # The active site molecule
│   ├── solvent.usd      # The environmental context (Water + Ions)
│   └── complex.usd      # Composition: References protein + ligand + solvent
```

### Hierarchy (Internal)
Instead of a flat list, `protein.usd` will structure data by Chain:
```
/Protein
    /Chain_A  (Points: 2450 atoms)
    /Chain_B  (Points: 2340 atoms)
```

This granular structure enables:
*   **Selective Visualization**: "Hide Chain B"
*   **Rigid Body Dynamics**: Treating domains as separate rigid bodies in future physics layers.

---

## 3. Implementation Plan

The script `pdb_to_usd_v2.py` will:
1.  **Multi-Pass Parse**: Read the PDB once, binning atoms into dictionaries based on `res_name`.
2.  **Batch Write**:
    *   Write `protein.usd` (iterating over protein bins).
    *   Write `ligand.usd` (iterating over `atp`).
    *   Write `solvent.usd` (iterating over `WAT`, `Na+`, `Cl-`).
3.  **Compose**: Write `complex.usd` which uses `References` to assemble the scene.

This separates the *definition* of data from its *assembly*, a core OpenUSD principle.
