# Report: Foundation Demo Plan - Visualizing the Experimental Setup (v1)

**Topic**: Implementation Plan for the Friday Deadline
**Source**: Analysis of ShinobuLab Data (ASCII PDB + ASCII Inputs vs Binary Trajectories)
**Date**: 2026-01-20
**Status**: Plan

---

## Executive Summary

Given the urgent 4-day deadline and the binary nature of the simulation *outputs* (Trajectory/Restart files), we will pivot the demo to focus on the **Simulation Inputs**.

We will build a "Visual Debugger for HPC Inputs." Instead of showing atoms moving (which requires complex binary parsing), we will show **what the supercomputer was told to do**. We will map the `reus-tune` input files to USD Variants, visualizing the "Target Restraints" overlaid on the static PDB structure.

**The Narrative**: "Why wait for the simulation to fail? Use OpenUSD to verify your 50-replica configuration *visually* before submitting to Fugaku."

---

## 1. The Asset: `atp_complex.usd`
**Source**: `files/atp-complex-solv35.pdb` (ASCII)

We will write a robust PDB-to-USD converter (`pdb_to_usd.py`) that generates a high-quality asset.
*   **Geometry**:
    *   **Protein**: `UsdGeomPoints` (High performance) or `UsdGeomMesh` (Spheres).
    *   **Solvent**: `UsdGeomPointInstancer`. We will extract the 30,000+ water molecules and instance a single cube/pyramid prototype. This demonstrates the "Massive Instancing" capability.
*   **Metadata**:
    *   Embed `ResidueID`, `ResidueName`, and `ChainID` as `primvars`. This is critical for the next step (visualizing restraints).

## 2. The Variants: `reus_experiment.usd`
**Source**: `pull/reus-tune-50rep-*.inp` (ASCII)

These input files contain the "Screenplay" for the 50 replicas. We will write a parser (`parse_genesis_inputs.py`) to extract:
*   **Restraint Groups**: Which residues are being pulled? (e.g., `group1 = atom:1-100`, `group2 = atom:200-300`).
*   **Target Values**: The target distance/angle for that specific replica (e.g., `dist = 10.5` Angstroms).

**The USD Structure**:
*   **Root Prim**: `REUS_Experiment`
*   **VariantSet**: `ReplicaID` (Values: `rep01` ... `rep50`)
*   **Visuals**:
    *   When you switch to `rep10`, a **Dasbed Line** (UsdGeomBasisCurves) appears between Group 1 and Group 2.
    *   The line length matches the *Target Distance* defined in the input file.
    *   **Visual Validation**: If `rep49` has a typo in the input file (e.g., target=1000 instead of 10.0), the user will see a massive line shooting off-screen. This is the "Visual Debugging" value prop.

## 3. The Workflow: Departmental Layering

We will structure the output to match the "Departmental" pattern:

*   `layer_01_biology.usd`: The static PDB asset (Atoms + Water).
*   `layer_02_layout.usd`: The experimental setup (The Box).
*   `layer_03_inputs.usd`: The REUS Variants (The Restraint Lines).
*   `foundation_demo.usda`: The entry point.

---

## Step-by-Step Implementation Plan

### Day 1: The PDB Converter (Biology Layer)
*   **Task**: Write `pdb_to_usd.py`.
*   **Success Criteria**: Load `atp_complex.usd` in `usdview`. See protein (colored by element) and solvent (instanced).

### Day 2: The Input Parser (Input Layer)
*   **Task**: Analyze the text format of `reus-tune-50rep-10.3.inp`.
*   **Task**: Write `parse_inputs.py` to extract `{ReplicaID: TargetDistance}`.
*   **Success Criteria**: A JSON dump of the experimental parameters.

### Day 3: The Restraint Visualizer (Composition)
*   **Task**: Write `generate_reus_stage.py`.
*   **Logic**:
    *   Reference `atp_complex.usd`.
    *   Create `ReplicaID` VariantSet.
    *   For each variant, add a `UsdGeomBasisCurves` representing the restraint.
*   **Success Criteria**: Open `foundation_demo.usda`, flip through variants, watch the "Target Line" grow/shrink.

### Day 4: Polish & Documentation
*   **Task**: Add 3D Text labels ("Restraint: 10.5 A").
*   **Task**: Capture screenshots.

## Why this works for Friday
1.  **No Binary Parsing**: We avoid the risk of decoding `.rst`/`.xtc` files.
2.  **Real Data**: We are using the *actual* input files from ShinobuLab, so the demo is scientifically grounded.
3.  **Unique Value**: "Visual Input Validation" is a fresh angle that appeals to PIs who worry about wasted supercomputer time.
