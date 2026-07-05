# OpenUSD for Research: Architectural Vision

**Type:** Permanent Design Document
**Status:** Verified against official Pixar and NVIDIA documentation (Feb 2026)
**Supersedes:** Brainstorming reports `__reports__/foundation_demo/analysis/02` through `10`

---

## 1. Core Thesis

OpenUSD is not just a 3D file format -- it is a **composition engine** that resolves conflicting opinions from multiple data sources using a deterministic strength ordering. This makes it a natural fit for scientific data management, where research workflows involve layered protocols, parallel experiments, and multi-scale representations of the same physical system.

**usd-bio treats OpenUSD as a Scientific Knowledge Management System**, not merely a visualization tool.

The fundamental insight: the problems USD solves for film production (heterogeneous data, collaborative iteration, massive instancing, non-destructive editing, departmental separation) are structurally identical to the problems facing computational biology research.

---

## 2. LIVERPS: Composition Arc Strength Ordering

When USD composes a scene, it resolves conflicting opinions (e.g., two different values for an atom's position) using a strict strength ordering called **LIVERPS**. The first opinion found wins.

> **Note:** Older documentation uses "LIVRPS" (6 letters). The current official acronym is **LIVERPS** (7 letters), reflecting the addition of the Relocates arc.

### 2.1 The LIVERPS Table

| Strength | Letter | Arc Type | Research Equivalent | Verification |
|:---------|:-------|:---------|:-------------------|:-------------|
| 1 (Strongest) | **L** | **Local** (and SubLayers) | **The Lab Notebook** -- the active experiment. Direct opinions and sublayered protocol steps override everything below. | Confirmed. Pixar Glossary: "Consults all layers in the local LayerStack for opinions. Recursively applies LIVERPS evaluation on SubLayers." |
| 2 | **I** | **Inherits** | **The Taxonomy** -- classification rules. "All Carbons are gray spheres with radius 1.7 A." Class prims under `/_class_/` define shared properties. | Confirmed. Pixar Glossary documents the `class _class_Tree` pattern as standard. |
| 3 | **V** | **VariantSets** | **The Hypothesis** -- toggling discrete experimental conditions. "What if we use CHARMM instead of Amber?" "What if residue 315 is mutated?" | Confirmed. Within a variant edit context, any composition arc (including Payloads) can be authored. |
| 4 | **E** | r**E**locates | **Path Reorganization** -- moving prims to different locations in the hierarchy without breaking references. Rarely used directly. | Confirmed. Added to PcpArcType enum; NVIDIA docs note LIVRPS -> LIVERPS transition. |
| 5 | **R** | **References** | **The Literature** -- importing standard assets. A canonical amino acid library, a validated water model, a published crystal structure. | Confirmed. Standard arc per Pixar Glossary. |
| 6 | **P** | **Payloads** | **The Raw Data** -- massive datasets (trajectories, volumetric data) loaded only on demand. Identical to References but deferred. | Confirmed. Standard arc per Pixar Glossary. |
| 7 (Weakest) | **S** | **Specializes** | **Specialized Refinements** -- a derived prim is continuously refined from a base prim: the derived (specialized) prim's own opinions always override the base's, and the base stays weaker than References too. Useful for base-class *defaults* that any specialization -- or a reference on the specialized prim -- can override. | Confirmed as weakest arc. **Correction (2026-07-06, verified via context7 OpenUSD glossary + PcpArcType enum):** the specialized/derived prim's opinions override the *base* source; the base is the *weakest* fallback -- it does **not** override instance/local opinions. The distinction from Inherits is that a specializes base stays weaker than *referenced* opinions on the specialized prim regardless of referencing context. Empirically demonstrated + tested in `examples/composition_advanced/specializes_arc/` (`tests/composition_advanced/test_specializes_arc.py`). |

### 2.2 Research Mapping Detail

#### Local + SubLayers: The Experimental Protocol

SubLayers within the Local arc model sequential protocol steps. Opinions in later steps override earlier ones.

```
root.usda
  subLayers = [
    @step3_production.usd@,   # Strongest: production trajectory
    @step2_heating.usd@,      # Overlays thermal velocities
    @step1_minimization.usd@  # Weakest sublayer: minimized positions
  ]
```

Disabling `step3` instantly reveals the state after `step2`. This maps directly to the ShinobuLab equilibration protocol (minimization -> heating -> equilibration -> production).

**Verification:** Confirmed. NVIDIA docs: "A local opinion is authored directly, without any other composition operations, in a layer or any of its recursive sublayers."

#### Inherits: Biological Taxonomy via Class Prims

Class prims define non-instantiated templates. Concrete prims inherit from them.

```usda
class "_class_" {
    class "C" {
        float bio:vdwRadius = 1.70
        color3f[] primvars:displayColor = [(0.5, 0.5, 0.5)]
    }
}

def Xform "Atom_CA" (
    prepend inherits = </_class_/C>
) {
    double3 xformOp:translate = (12.5, 4.2, -1.0)
    # Color and radius inherited from class
}
```

This provides a semantic ontology directly in the scene graph. Changing the Carbon class globally updates every Carbon atom.

**Verification:** Confirmed. Pixar Glossary: "class prims...contribute opinions via Inherits arcs."

#### VariantSets: Hypothesis Testing

VariantSets toggle discrete states without duplicating data. Three patterns identified for research:

**Pattern A -- Ensemble Variant (Statistical Power):**
- VariantSet: `ReplicaID` with values `rep_01`...`rep_50`
- Each variant swaps the Payload pointer to a different trajectory file
- Use case: REUS umbrella sampling with 50 replicas

**Pattern B -- Perturbation Variant (In Silico Mutagenesis):**
- VariantSet: `Genotype` with values `WildType`, `T315I`
- Swaps residue geometry for the mutated position
- Use case: ABL kinase drug resistance studies

**Pattern C -- Parameter Variant (Force Field Comparison):**
- VariantSet: `ForceField` with values `Amber99`, `Charmm36`
- Overrides charge and mass attributes on atoms
- Use case: Methodological validation

**Verification:** Confirmed. Standard pattern -- within a variant edit context, any composition arc can be authored.

#### Value Clips: Trajectory Data

MD trajectories are structurally identical to animation clips: topology is constant, positions change per frame.

- **Topology file:** Static PDB data (bonds, residues, element types) -- loads in milliseconds
- **Clip files:** Only `points` attribute time samples -- streamed on demand
- **Manifest:** Stitches clips together via `UsdClipsAPI`

**Verification:** Confirmed. Pixar docs: "The USD Value Clips feature allows users to decompose time-varying data across many layers that can then be sequenced and re-sequenced back together in flexible ways." `UsdClipsAPI` docs: "the asset reference will provide the topology and unvarying data for the model, while the clips will provide the time-sampled animation."

---

## 3. The Research-as-Movie Analogy

The central conceptual framework mapping film production to research workflows. **This mapping is an original interpretation built on confirmed USD mechanisms.** The USD mechanisms themselves are standard; applying them to research domains is novel.

| Film Production Concept | Research Equivalent | USD Mechanism |
|:------------------------|:-------------------|:-------------|
| **Character Rig / Asset** | The Biological System (e.g., ABL kinase + ATP) | Schema + `PointInstancer` for solvent |
| **The Screenplay** | Simulation Protocol (Minimization -> Heating -> Production) | SubLayers (opinion strength ordering) |
| **Takes / Alternate Cuts** | Replicas & Ensembles (REUS runs) | VariantSets swapping Payloads |
| **Departments** (Layout, Anim, Lighting, FX) | Research concerns (Biology, Protocol, Dynamics, Analysis, Review) | SubLayer separation by concern |
| **Clip Stitching** (non-linear editing) | Trajectory data: static topology + streamed frames | Value Clips (`UsdClipsAPI`) |
| **Dailies / Director Review** | PI feedback: 3D annotations, cameras, comments on the data | Non-destructive Review layer |
| **LOD / Proxies** | Cross-scale: MD = 50,000-atom mesh; Systems Bio = single point with `rate_constant` | Class inheritance + `Representation` VariantSet |
| **Cinematography** | Publication visuals | Hydra rendering (Storm/RTX) |

### Why This Analogy Works

Both domains share the same structural requirements:
- **Heterogeneous data** that must compose into a single coherent scene
- **Collaborative iteration** where multiple people edit without destroying each other's work
- **Massive instancing** (30,000+ water molecules = crowd simulation)
- **Non-destructive editing** (toggle protocol steps, swap experimental conditions)
- **Departmental separation** with clear ownership boundaries

---

## 4. Three Architectural Pillars

### 4.1 Departmental Layering (SubLayers for Concern Separation)

Adapted from film studio department separation (Layout, Animation, Lighting, FX) and NVIDIA Digital Twin patterns (Layout Layer, Geometry Layer, Simulation Layer).

| Film Department | Research Concern | Layer | Content |
|:----------------|:----------------|:------|:--------|
| Assets | **Biology** | `01_biology.usd` | Topology, mass, charge, bonds |
| Layout | **Protocol** | `02_protocol.usd` | Solvent box, ion placement, restraints |
| Animation | **Dynamics** | `03_dynamics.usd` | Time-sampled positions (trajectory) |
| FX | **Analysis** | `04_analysis.usd` | Derived data (PMF, distances, angles) |
| Lighting | **Review** | `05_review.usd` | Annotations, cameras, PI comments |

**Benefits:**
- Parallel work: the analysis student edits `04_analysis.usd` while the simulation student reruns `03_dynamics.usd`
- Non-destructive: replacing the dynamics layer preserves review comments
- Selective loading: load only the layers needed for the current task
- Independent versioning: each layer version-controlled separately

**Verification:** SubLayer-based separation is standard practice. Pixar's own examples show `@shotFX.usd@, @shotAnimationBake.usd@, @sequence.usd@` layer stacks. The mapping to research domains is an original application.

### 4.2 Variant-Based Hypothesis Testing

Three patterns for scientific VariantSets (detailed in Section 2.2 above):

1. **Ensemble Variant** (`ReplicaID`) -- statistical power through replica comparison
2. **Perturbation Variant** (`Genotype`) -- in silico mutagenesis and A/B testing
3. **Parameter Variant** (`ForceField`) -- methodological comparison

All three patterns use confirmed USD mechanisms (VariantSets swapping Payloads/References). The specific application to research workflows is original.

### 4.3 Value Clips for Trajectory Data

Topology/clip separation maps directly to the MD simulation data model:
- **Topology** = PDB file (atom types, bonds, residues) -- static
- **Clips** = Trajectory frames (XTC/DCD) -- time-varying positions only

This enables:
- Instant loading of the molecular structure
- On-demand streaming of trajectory frames
- Random access to any frame without loading the full dataset
- Memory-efficient playback of large simulations

**Verification:** Confirmed as structurally identical to USD's crowd animation workflow. Pixar: "decompose time-varying data across many layers that can then be sequenced and re-sequenced back together."

---

## 5. Hierarchical Data Model

The usd-bio asset hierarchy builds biological structures compositionally, from atoms up:

### Level 1: Elements (Atoms)

Class prims for each chemical element under `/_class_/`. Each defines:
- Van der Waals radius (Bondi 1964)
- Covalent radius (Cordero 2008)
- CPK display color (Corey-Pauling-Koltun / Jmol conventions)
- Atomic mass (IUPAC 2021)
- Electronegativity (Pauling scale)
- `representation` VariantSet with modes: `points`, `balls`, `vdw`, `ballstick`

### Level 2: Molecules

Small molecule templates (e.g., water). SubLayer the element templates to access `/_class_/` definitions. Atoms within the molecule inherit from their element class.

### Level 3: Residues

Amino acid and nucleotide templates. Each residue:
- SubLayers element_templates to access `/_class_/` definitions
- Uses `over "_class_"` to extend the class namespace where needed
- Each atom inherits from its element class (e.g., `inherits = </_class_/N>`)
- Atom 3D positions are Local opinions (strongest in LIVERPS, overriding inherited defaults)
- Custom attributes in the `bio:` namespace: `bio:residueName`, `bio:oneLetterCode`, `bio:residueType`, `bio:atomCount`, `bio:bondCount`
- `representation` VariantSet cascades from residue level to individual atoms and bonds

### Level 4: Assemblies (planned)

Protein chains, complexes, solvated systems. Will compose residue templates via References, apply experimental conditions via VariantSets, and attach trajectory data via Value Clips.

### Composition Pattern Summary

This hierarchy demonstrates LIVERPS in action:
- **Inherits (I):** Atoms inherit element properties (radius, color, mass) from `/_class_/` templates
- **Local (L):** Atom 3D positions are local opinions that override inherited defaults
- **VariantSets (V):** `representation` variants cascade through the hierarchy
- **SubLayers (L):** Residue templates sublayer element templates to share class definitions

---

## 6. Concrete Example: ShinobuLab ABL Kinase Workflow

The architecture maps to the ShinobuLab MD simulation data for the ABL kinase system:

### The System
- ABL kinase with ATP ligand, solvated (~35,000+ atoms)
- GENESIS simulation suite with Amber force fields

### The Protocol (SubLayers)
Sequential equilibration steps, each a SubLayer:
1. `1-min/` & `2-min/` -- Energy minimization
2. `3-heat/` -- Thermalization to 310K
3. `4-eq1/` & `5-eq2/` -- NPT/NVT equilibration
4. `md-simulations/production/` -- 350 sequential production runs

### The Ensembles (VariantSets)
- REUS umbrella sampling: 50 replicas with harmonic restraints on COM distances/angles
- Maps to `ReplicaID` VariantSet with Payload swapping

### The Analysis Pipeline (Departmental Layers)
- `0_traj/` -> Trajectory processing
- `1_comdist/` -> COM distance calculations
- `2_angle/` -> Angular distributions
- `3_mbar/` -> MBAR free energy (PyMBAR)
- `4_pmf/` -> PMF generation
- `5_kmeans/` -> K-means clustering (16 cluster centers)

Each analysis step can be modeled as a layer or as custom attributes on analysis prims, maintaining provenance from raw data through derived results.

---

## 7. What's Confirmed vs. What's Original

### Confirmed USD Behavior (verified against official docs)

| Claim | Source |
|:------|:-------|
| LIVERPS strength ordering (7 arcs) | Pixar Glossary, PcpArcType enum |
| SubLayers are part of the Local arc | Pixar Glossary, NVIDIA Learn OpenUSD |
| VariantSets can author any composition arc (including Payloads) | Standard API behavior |
| Value Clips decompose time-sampled data across files | Pixar Value Clips docs, UsdClipsAPI |
| Class prims + Inherits = taxonomy | Pixar Glossary `_class_Tree` example |
| Specializes = weakest arc; the specialized (derived) prim's opinions override the base source (the base is the weakest fallback, not stronger than instance/local opinions) | PcpArcType enum, Pixar Glossary (context7-verified 2026-07-06) |
| Topology + Clips = standard crowd/animation pattern | Pixar docs, UsdClipsAPI docs |
| SubLayer-based departmental separation | Pixar layer stack examples |

### Original Interpretations (novel research-domain mappings)

| Interpretation | Builds On |
|:---------------|:----------|
| LIVERPS arcs mapped to research equivalents (Lab Notebook, Taxonomy, Hypothesis, Literature, Raw Data) | Confirmed LIVERPS ordering |
| Research-as-Movie analogy (full mapping table) | Confirmed departmental/layer patterns |
| Departmental layering for research (Biology, Protocol, Dynamics, Analysis, Review) | Confirmed SubLayer separation |
| Three Scientific VariantSet patterns (Ensemble, Perturbation, Parameter) | Confirmed VariantSet mechanics |
| MD trajectories as animation clips | Confirmed Value Clips API |
| Cross-scale representation (atom mesh vs. abstract point, same class) | Confirmed Inherits + VariantSet |
| `bio:` namespace conventions for research metadata | Standard USD namespace pattern |

---

## 8. References

### Official Pixar Documentation
- [OpenUSD Glossary](https://openusd.org/release/glossary.html) -- LIVERPS definitions, class prims, composition arcs
- [Value Clips](https://openusd.org/dev/api/_usd__page__value_clips.html) -- Sequencable, re-timable animated value clips
- [UsdClipsAPI](https://openusd.org/release/api/class_usd_clips_a_p_i.html) -- Clips API reference
- [UsdUtilsStitchClips](https://openusd.org/docs/api/stitch_clips_8h.html) -- Clip stitching utilities
- [PcpArcType source](https://openusd.org/release/api/usd_2pcp_2types_8h_source.html) -- Composition arc enum in C++

### NVIDIA Documentation
- [What Is LIVERPS?](https://docs.nvidia.com/learn-openusd/latest/creating-composition-arcs/strength-ordering/what-is-liverps.html) -- LIVRPS -> LIVERPS transition, strength ordering
- [Composition Basics: Strength Ordering](https://docs.nvidia.com/learn-openusd/latest/composition-basics/strength-ordering.html) -- Detailed walkthrough

### Scientific References
- Bondi, A. (1964). "van der Waals Volumes and Radii." *J. Phys. Chem.* 68(3): 441-451.
- Cordero, B. et al. (2008). "Covalent radii revisited." *Dalton Trans.* (21): 2832-2838.
- Corey, R.B., Pauling, L. (1953). "Molecular Models of Amino Acids, Peptides, and Proteins." *Rev. Sci. Instrum.* 24(8): 621-627.
