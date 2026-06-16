# Report: OpenUSD Architectural Patterns for Research (v0)

**Topic**: Adapting Film & Digital Twin Patterns to Scientific Workflows
**Source**: OpenUSD & Omniverse Documentation Analysis
**Date**: 2026-01-19
**Status**: Draft

---

## Executive Summary

This report synthesizes architectural patterns from high-end Film Production (Pixar) and Digital Twin (Nvidia) pipelines to design a robust "Research Container" for biological data. The core finding is that **MD Trajectories are mathematically equivalent to Animation Clips**, and **Research Protocols are equivalent to Shot Composition**.

---

## 1. The "Shot-Based" Workflow Pattern

In film, a **Sequence** (e.g., "The Chase") contains multiple **Shots** (e.g., "Car jumps", "Hero looks back"). All shots reference the same **Assets** (Car, Hero) but apply unique animation and lighting.

### Mapping to Science
*   **Sequence** = **Experiment Series** (e.g., "Binding Affinity Study")
*   **Shot** = **Simulation Run** (e.g., "Replica 1", "Replica 2")
*   **Asset** = **Biological System** (e.g., "ATP Complex")

### Implementation Strategy
We will use the **"Reference with Overrides"** pattern.
1.  **`assets/atp_complex.usd`**: Defines the topology and default state.
2.  **`experiments/affinity_study/base.usd`**: Defines the common environment (solvent box, temperature).
3.  **`experiments/affinity_study/run_01.usd`**:
    *   Inherits from `base.usd`.
    *   Applies a specific **Random Seed**.
    *   References the unique trajectory cache.

---

## 2. The "Clip Stitching" Pattern (Topology vs. Animation)

MD simulations produce massive datasets (`.xtc` files) where topology is constant, but positions change per frame. This mirrors the **Value Clips** pattern in OpenUSD.

### The Problem
Storing a full mesh for every frame is impossible (file bloat).

### The Solution: `usdstitchclips`
*   **Topology File**: `topology.usd` (Contains the mesh definition, no time samples).
*   **Clip Files**: `clip.101.usd`, `clip.102.usd`... (Contain *only* the `points` attribute time samples).
*   **Manifest**: `result.usda` (Stitches them together).

### Usage in USD-Bio
We will not just "convert" XTC to USD. We will implement **Value Clips**:
*   `atp_topology.usd`: The static PDB data.
*   `atp_trajectory.usd`: A lightweight file that *only* contains the `timeSamples` for the `points` attribute.
*   **Benefit**: Users can load the topology instantly (milliseconds) and stream the trajectory data only when scrubbing the timeline.

---

## 3. The "Digital Twin" Composition Pattern

Nvidia's Factory Twins use a rigorous layering scheme to separate concerns.
1.  **Layout Layer**: Where things are.
2.  **Geometry Layer**: What things look like.
3.  **Simulation Layer**: How things move.

### Usage in USD-Bio
We will enforce this separation in our `examples/demo_research_workflow`:
*   **`01_layout.usd`**: The "Petri Dish" arrangement (Solvent box dimensions).
*   **`02_geometry.usd`**: The Molecular Surface representations.
*   **`03_physics.usd`**: The Force Field parameters (Mass, Charge, Bonds).
*   **`04_data.usd`**: The Trajectory clips.

---

## 4. The "Data Connector" Pattern

Digital Twins often pull live data from sensors. In research, "live data" is the analysis results (e.g., a Python script calculating energy).

### Usage in USD-Bio
We will treat **Analysis as a Live Layer**.
*   Instead of baking a graph into a texture, we create a **Custom Prim** `AnalysisGraph`.
*   A Python script running in the background (or a Hydra Delegate) updates the `data` attribute of this prim.
*   The visualization updates in real-time as the simulation progresses (or as the trajectory is scrubbed).

---

## Recommendation for Demo Implementation

To meet the Friday deadline, we should focus on implementing **Pattern 2 (Value Clips)** and **Pattern 3 (Layer Separation)**. These offer the highest "ROI" for demonstrating workflow superiority over legacy formats.

### Planned Directory Structure for `examples/demo_research_workflow`
```
demo/
├── assets/
│   ├── atp_topology.usd       (Pattern 2: Topology)
│   └── solvent.usd            (Pattern 3: Geometry)
├── data/
│   └── run_01_trajectory.usd  (Pattern 2: Value Clips)
├── layers/
│   ├── 01_biology.usd         (Pattern 3: Physics/Bio Metadata)
│   └── 02_protocol.usd        (Pattern 1: The "Shot" setup)
└── root.usda                  (The Composition)
```
