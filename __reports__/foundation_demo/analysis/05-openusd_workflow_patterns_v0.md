# Report: Workflow Patterns for Scientific OpenUSD (v0)

**Topic**: Deep Architectural Patterns for Research Data
**Source**: Industry Analysis (Film/Digital Twin) + ShinobuLab Brainstorming
**Date**: 2026-01-19
**Status**: Draft

---

## Executive Summary

This report defines the specific OpenUSD patterns that transform a "File Folder" workflow into a "Connected Research Database." We identify three core pillars: **Departmental Layering** (Organization), **Scientific Variant Sets** (Hypothesis Testing), and **Contextual Review** (Collaboration).

---

## 1. Departmental Layering (The "Digital Lab Bench")

Film studios separate "Layout" from "Animation." Research labs should separate "Setup" from "Simulation."

### The "Concern-Separation" Pattern

| Film Department | Research Concern | Layer Name | Content |
| :--- | :--- | :--- | :--- |
| **Assets** | **Biology** | `01_biology.usd` | Topology, Mass, Charge, Bounds. |
| **Layout** | **Protocol** | `02_protocol.usd` | Solvent Box size, Ion placement, Restraints. |
| **Animation** | **Dynamics** | `03_dynamics.usd` | Time-sampled positions (Trajectory). |
| **FX** | **Analysis** | `04_analysis.usd` | Derived data (PMF plots, bond distances). |
| **Lighting** | **Review** | `05_review.usd` | Annotations, Cameras, Comments. |

### Workflow Benefit
*   **Parallel Work**: The "Analysis Student" can work on `04_analysis.usd` while the "Simulation Student" is still re-running `03_dynamics.usd`.
*   **Non-Destructive**: If the simulation fails, you just replace layer 03. You don't lose the Review comments (05) or the Protocol setup (02).

---

## 2. Scientific Variant Sets (The "Hypothesis Engine")

Variants are not just for colors; they are for **Experimental Conditions**.

### Pattern A: The "Ensemble" Variant (Statistical Power)
*   **Context**: Umbrella Sampling (50 replicas).
*   **VariantSet**: `ReplicaID`
*   **Variants**: `rep_00`, `rep_01`, ... `rep_50`.
*   **Mechanism**: Swaps the **Payload** pointer to different `.xtc` caches.
*   **Value**: Instantly browse the statistical distribution of the experiment.

### Pattern B: The "Perturbation" Variant (In Silico Mutagenesis)
*   **Context**: Drug Resistance studies (ABL Kinase T315I mutation).
*   **VariantSet**: `Genotype`
*   **Variants**:
    *   `WildType`: Standard topology.
    *   `T315I`: Swaps Residue 315 geometry for Isoleucine.
*   **Value**: Visual A/B testing of steric clashes with drugs.

### Pattern C: The "Parameter" Variant (Force Fields)
*   **Context**: Methodological comparison.
*   **VariantSet**: `ForceField`
*   **Variants**: `Amber99`, `Charmm36`.
*   **Mechanism**: Overrides `primvars:charge` and `primvars:mass` on all atoms.
*   **Value**: Verify how parameterization affects the model structure.

---

## 3. Contextual Review (The "3D Google Doc")

Research collaboration is often asynchronous and disconnected (emailing static screenshots).

### The "Dailies" Pattern
*   **Mechanism**: A dedicated `Review` layer stack.
*   **Tools**:
    *   **Cameras**: `Camera_Frame145_LoopCheck` (Forces the view to the critical moment).
    *   **3D Text**: `UsdGeomText` placed at the exact 3D coordinate of an event.
    *   **Screen Drawing**: "Grease Pencil" annotations projected onto the protein surface.
*   **Value**: The feedback is attached to the *data*, not an email. It persists through version updates.

---

## Implementation Plan for `examples/demo_research_workflow`

We will implement a Python generator that builds this exact structure for the ABL Kinase system.

### Phase 1: The Asset Generator (`01_build_assets.py`)
*   Builds `atp_complex.usd` with `ForceField` variants (Pattern 2C).
*   Builds `mutant_complex.usd` with `Genotype` variants (Pattern 2B).

### Phase 2: The Simulation Composer (`02_compose_experiment.py`)
*   Creates the **Layer Stack** (Pattern 1).
*   Generates a mock trajectory and stitches it via Value Clips.
*   Adds `ReplicaID` variants (Pattern 2A) pointing to mock trajectory files.

### Phase 3: The Review Simulator (`03_simulate_review.py`)
*   Creates a `review.usd` layer.
*   Injects a Camera and 3D Text annotation ("Check bond length here").
*   Sublayers it on top of the Experiment.

This suite will powerfully demonstrate OpenUSD as a **Scientific Knowledge Management System**.
