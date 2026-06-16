# Report: Encapsulated Department Architecture (v0)

**Topic**: Recursive Composition of Scientific Domains
**Source**: Synthesis of Film Patterns & Digital Twin Layering
**Date**: 2026-01-19
**Status**: Draft

---

## Executive Summary

To manage the complexity of a Multi-Scale Research Project, we propose the **Encapsulated Department Architecture**. This pattern treats each scientific domain (MD Simulation, Systems Biology, Microscopy) as an independent "Production Department" with its own internal logic (Shots, Replicas, Stitched Clips). These departments are then composed into a **Project Root** via SubLayers, creating a unified yet modular research environment.

---

## 1. The Recursive Composition Model

We reject the idea of a "Flat" file structure. Instead, we use a recursive hierarchy where each level encapsulates its own complexity.

### Level 0: The Project Container (The "Digital Twin")
The PI interacts here. They see the "Whole Picture."
*   **File**: `project_root.usda`
*   **Composition**:
    *   `subLayers`:
        *   `@./layers/05_review.usd@` (Global Comments)
        *   `@./layers/04_analysis_dashboard.usd@` (Cross-Scale Correlation)
        *   `@./layers/03_microscopy_dept.usd@` (Tissue Scale)
        *   `@./layers/02_systems_bio_dept.usd@` (Cell Scale)
        *   `@./layers/01_md_simulations_dept.usd@` (Molecular Scale)

### Level 1: The Department (The "Film Sequence")
The PhD Student interacts here. They see their specific domain in high fidelity.
*   **Example**: `01_md_simulations_dept.usd`
*   **Internal Pattern**: **Sequence/Shot Organization**.
    *   Defines the "Binding Affinity Experiment" Sequence.
    *   Contains 50 "Shots" (Replicas).
    *   Manages **Scientific Variant Sets** (ForceFields, Mutations).
*   **Encapsulation**: The Project Root does *not* need to know about "Replica #42". It just references the Department Layer.

### Level 2: The Asset (The "Clip Stitching")
The Algorithm interacts here. It manages raw data.
*   **Example**: `atp_complex.usd`
*   **Internal Pattern**: **Value Clips**.
    *   Stitches `topology.usd` (Static PDB) with `trajectory.usd` (Dynamic XTC).
    *   Optimizes memory by loading data only on demand.

---

## 2. The Cross-Scale Interface (LOD & Proxies)

A critical challenge is relating data across scales. A "Protein" means different things to different departments.

### The "Proxy" Pattern
*   **MD Department**: Represents "ATP Synthase" as a 50,000-atom Mesh (`UsdGeomMesh`).
*   **Systems Bio Department**: Represents "ATP Synthase" as a Single Point (`UsdGeomPoint`) with attributes like `rate_constant`.

### The Integration Strategy
We use **USD Classes (`inherits`)** to link them semantically.
1.  Define a global class `class "_ATP_Synthase_"`.
2.  **MD Layer**: Defines the `Mesh` representation *inheriting* from `_ATP_Synthase_`.
3.  **Systems Layer**: Defines the `Point` representation *inheriting* from `_ATP_Synthase_`.
4.  **Project Root**: Can use a **VariantSet** named `Representation` to switch between `Atomic` (MD view) and `Abstract` (Systems view) globally.

---

## 3. The "Live" Connection (Data Connectors)

Scientific data is not static; it grows.

### The "Live Layer" Pattern
*   **Concept**: A layer that is updated by an external process (e.g., a microscope or a running simulation).
*   **Mechanism**:
    *   **File-Based**: The simulation appends frames to `trajectory.usd` on disk. USD's "Reload" feature picks up changes.
    *   **Delegate-Based**: A Hydra Delegate streams data directly into memory (advanced, future scope).
*   **Usage**: The `04_analysis_dashboard.usd` layer is "Live". A Python script watches the `md_simulations` folder. When a new simulation finishes, it calculates the Binding Energy and writes it to a `timeSample` on the dashboard prim. The PI sees the graph update in real-time.

---

## 4. Implementation Specification for Demo

The `examples/demo_research_workflow` will generate:

1.  **`assets/atp.usd`** (Level 2): Uses Value Clips to mock a trajectory.
2.  **`layers/md_dept.usd`** (Level 1): Arranges 3 Replicas of ATP in a grid.
3.  **`layers/sys_dept.usd`** (Level 1): Arranges 100 Points representing the cell context.
4.  **`root.usda`** (Level 0): Composes them. Defines a `Global_View` variant to toggle between "Show Molecules" and "Show Systems".

This structure provides the "Simplicity vs. Power" demonstration required for the Flash Intro.
