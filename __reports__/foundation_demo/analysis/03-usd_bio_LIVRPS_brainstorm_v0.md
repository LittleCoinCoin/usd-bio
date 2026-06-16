# Report: LIVRPS - The DNA of OpenUSD for Research (v0)

**Topic**: Mapping OpenUSD Composition Arcs (LIVRPS) to Scientific Workflows
**Source**: ShinobuLab Data & OpenUSD Documentation
**Date**: 2026-01-19
**Status**: Draft

---

## Executive Summary

The power of OpenUSD lies not in its file format, but in its **Composition Engine**. This engine resolves conflicts between data sources using a strict strength ordering known as **LIVRPS**. By mapping scientific data operations to these specific composition arcs, we can create a "Research Container" that is robust, version-controlled, and collaborative by design.

---

## The LIVRPS Principle

When OpenUSD composes a scene, it looks for opinions on a Prim (e.g., an Atom's position) in this specific order. The first opinion found **wins**.

| Strength | Mnemonic | Arc Type | Research Equivalent | Usage in USD-Bio |
| :--- | :--- | :--- | :--- | :--- |
| **1 (Strongest)** | **L** | **Local** | **The Lab Notebook** | The active experiment. Overrides everything below it. Includes **SubLayers** (Protocol steps). |
| **2** | **I** | **Inherits** | **The Taxonomy** | "All Proteins represent atoms as spheres." Global classification rules. |
| **3** | **V** | **VariantSets** | **The Hypothesis** | "What if we use CHARMM instead of Amber?" Toggling discrete states. |
| **4** | **R** | **References** | **The Literature** | Importing standard assets (e.g., a standard Amino Acid library). |
| **5** | **P** | **Payloads** | **The Raw Data** | Massive datasets (Trajectories) that are loaded only on demand. |
| **6 (Weakest)** | **S** | **Specialize** | *(Rarely Used)* | Specialized refinements of base definitions. |

---

## Application to ShinobuLab Workflow

### 1. **P**ayloads: Handling "Heavy" Data
*   **Problem**: MD trajectories (`.xtc`) are gigabytes in size. Loading them freezes the UI.
*   **USD Solution**: Wrap the trajectory in a **Payload**.
    *   The `ATP_Complex` prim exists in the scene hierarchy instantly.
    *   The *actual atoms* are only loaded when the user explicitly requesting them (or clicks "Play").
    *   **Code**: `prim.GetPayloads().AddPayload("./heavy_trajectory.usd")`

### 2. **R**eferences: Standard Parts
*   **Problem**: Every simulation re-defines what "Water" is.
*   **USD Solution**: Create a single `solvent_library.usd`.
    *   The simulation references `WaterMolecule` from the library.
    *   If we update the visualization of Water (e.g., improved shading), *every* simulation updates instantly.
    *   **Code**: `prim.GetReferences().AddReference("./assets/solvent.usd")`

### 3. **V**ariants: Managing Ensembles
*   **Problem**: `pull/` directory has 50 replicas (`rep01`...`rep50`). To compare them, you open 50 windows.
*   **USD Solution**: A **VariantSet** named `ReplicaID` on the Root Prim.
    *   Switching the Variant changes the **Payload** pointer to a different trajectory file.
    *   The camera, lighting, and analysis tools remain constant; only the *data* creates the context.
    *   **Code**: `vset = prim.GetVariantSets().AddVariantSet("ReplicaID"); vset.AddVariant("rep01"); ...`

### 4. **I**nherits: Semantic Classification
*   **Problem**: How do we tell the renderer that "Residue 278" is a "Tyrosine"?
*   **USD Solution**: Create a class `_Tyrosine_` that defines default bonds and mass.
    *   `def "Residue_278" (inherits = </Classes/AminoAcids/Tyrosine>)`
    *   This provides a **Semantic Ontology** directly in the scene graph.
    *   **Code**: `prim.GetInherits().AddInherit("/Classes/AminoAcids/Tyrosine")`

### 5. **L**ocal (SubLayers): The Experimental Protocol
*   **Problem**: Tracking the history of a system (Minimization -> Heating -> Production).
*   **USD Solution**: **SubLayers** within the Local arc.
    *   `root.usda` has `subLayers = [@step3_prod.usd@, @step2_heat.usd@, @step1_min.usd@]`.
    *   Opinions in `step3` override `step2`.
    *   Disabling `step3` instantly reveals the state of `step2`.
    *   **Code**: `stage.GetRootLayer().subLayerPaths.append("./step1_min.usd")`

---

## The "Flash Demo" Architecture

We will implement this hierarchy in `examples/demo_research_workflow`:

```mermaid
graph TD
    ROOT[Experiment.usda] -->|SubLayer (L)| PROTOCOL[Protocol Layer]
    ROOT -->|SubLayer (L)| REVIEW[Review Layer]
    
    PROTOCOL -->|Reference (R)| ASSET[ATP_Complex.usd]
    
    ASSET -->|Inherit (I)| CLASS[Ontology.usd]
    ASSET -->|Variant (V)| STATE{State Variant}
    
    STATE -- Minimized --> PAYLOAD1[Minimization.usd]
    STATE -- Production --> PAYLOAD2[Trajectory_Payload.usd]
```

### Implementation Plan
1.  **Script 1**: `generate_ontology.usd` (Defines the `_Protein_` class).
2.  **Script 2**: `generate_asset.usd` (The ATP structure, referencing Ontology, Payload for atoms).
3.  **Script 3**: `generate_experiment.usd` (Composes the SubLayers for review and protocol).

This structure proves that USD is capable of handling the *logic* of science, not just the pixels.
