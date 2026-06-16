# Perspective: From v8 Prototypes to UsdBio Production

**Date:** 2026-02-15
**Context:** foundation_demo_v8 complete through Level 4 (assemblies) + trajectory playback
**Purpose:** Assess what the prototyping phase has proven, identify gaps, and define what remains before writing a multi-phase production roadmap for the UsdBio schema extension.

---

## Table of Contents

1. What We Have Proven
2. The Schema Question: When Does `bio:` Become `UsdBio`?
3. Gap Analysis
4. Open Questions
5. Prototyping Experiments Still Needed
6. On the GUI Question
7. On the Pipeline Automation Question
8. Toward a Production Roadmap Structure

---

## 1. What We Have Proven

The v8 prototyping phase set out to answer: can OpenUSD's composition engine represent the full data lifecycle of a computational biology research project using only built-in types? The answer is **yes, with qualifications**.

### Proven with working code against real data

| Claim | Evidence | Files |
|-------|----------|-------|
| Class prims model biological taxonomy | 23 elements as `/_class_/` templates; 4,676 atoms inherit properties (radius, color, mass) from 6 element classes | `01_create_element_templates.py`, `04_create_assembly.py` |
| PDB hierarchy maps to USD hierarchy | Chain -> Residue -> Atom encoded as nested Xform prims with `bio:` metadata at every level | `pdb_parser.py`, `04_create_assembly.py` |
| VariantSet cascade scales to real structures | Single variant selection at `/ABLComplex` toggles 4,676 atom + 2,428 bond representations through a 4-level cascade (complex -> chain -> residue -> atom) | `04_create_assembly.py` |
| Value Clips map to MD trajectories | 20 frames from a 70,000-frame XTC trajectory, with both atom positions and bond geometry animated, playable in usdview | `xtc_to_clips.py`, `trajectory_demo.py` |
| Topology/clip separation works for biology | Static assembly (hierarchy, colors, variants, metadata) composes with dynamic clip (positions only) exactly as designed | `assembly_demo.py` vs `trajectory_demo.py` |
| SubLayers separate concerns | Element templates sublayered by assemblies; assembly sublayered by demos. Each layer independently editable. | All template and demo scripts |

### What this means for UsdBio

The architectural thesis from `openusd_for_research_architecture.md` is **validated at the pattern level**. Every LIVERPS arc we mapped to a research concept has a working prototype demonstrating the mapping with real ShinobuLab data. The composition engine handles biology data naturally -- no hacks, no workarounds, no custom types needed for the core representation.

This is the strongest possible foundation for a schema extension: we know exactly which patterns work because we've built them by hand. The schema's job is to formalize and optimize what we've already proven.

---

## 2. The Schema Question: When Does `bio:` Become `UsdBio`?

Right now, every biological attribute is a custom attribute with a `bio:` namespace prefix (`bio:vdwRadius`, `bio:residueName`, `bio:element`). This works, but it's convention-enforced, not schema-enforced. The difference matters for production:

| Aspect | Convention (`bio:` attributes) | Schema (`UsdBio` typed prims) |
|--------|-------------------------------|-------------------------------|
| Validation | None -- any string goes into `bio:element` | Type-checked at authoring time |
| Discovery | Grep for `bio:` across files | `stage.GetPrimAtPath(...).IsA(UsdBioAtom)` |
| Documentation | CLAUDE.md and tribal knowledge | Auto-generated from schema definition |
| Interop | Other tools must know the convention | Other tools query the schema registry |
| Defaults | Must be set explicitly every time | Schema provides fallback values |
| Codegen | Manual Python for everything | C++ classes with Python bindings auto-generated |

**The prototyping phase has produced the schema's input specification.** We now know which attributes exist, what types they need, which prims carry them, and how they compose. Concretely:

- **UsdBioAtom**: `bio:atomName` (Token), `bio:element` (Token), `bio:serial` (Int). Applied to Xform prims that inherit from element classes.
- **UsdBioResidue**: `bio:residueName` (Token), `bio:residueSeq` (Int), `bio:atomCount` (Int). Applied to Xform prims containing atom children.
- **UsdBioChain**: `bio:chainID` (Token), `bio:chainType` (Token), `bio:residueCount` (Int), `bio:atomCount` (Int).
- **UsdBioAssembly**: `bio:systemName` (String), `bio:source` (String), `bio:atomCount` (Int), `bio:chainCount` (Int).
- **UsdBioElement** (class prim schema): `bio:symbol` (Token), `bio:atomicNumber` (Int), `bio:vdwRadius` (Float), `bio:covalentRadius` (Float), `bio:cpkColor` (Color3f), `bio:electronegativity` (Float).

The question of *when* to formalize into C++ schemas is a roadmap decision, not a technical one. The schemas can be written any time; the question is whether enough of the composition patterns are settled to avoid schema churn. Based on what v8 has demonstrated, the element/atom/residue/chain hierarchy is stable. What's *not* stable yet is how analysis data, ensemble variants, and cross-scale representations should be schematized -- those need more prototyping.

---

## 3. Gap Analysis

### 3.1 Scale (Critical)

The v8 assembly uses per-atom Xform prims. This worked for 4,676 protein+ligand atoms and produced a 12 MB `.usda` text file. It will not work for the full 188,609-atom solvated system, nor for production trajectories with thousands of frames.

| Gap | Current State | Production Need |
|-----|--------------|-----------------|
| Solvent representation | Excluded (183K atoms deferred) | PointInstancer for 61K water molecules |
| File format | `.usda` text (12 MB assembly, 18 MB clip) | `.usdc` binary (Crate format, 5-10x smaller) |
| Trajectory frames | 20 frames from 1 of 10 XTC files | 700K+ frames across all files, lazy-loaded |
| Clip architecture | Single clip file, all frames in memory | Clip template pattern, one clip per source file |
| Bond representation | Per-bond Xform + Cylinder (2,428 prims) | Needs scaling strategy (see 3.2) |

### 3.2 Bond Geometry at Scale

Bonds are currently explicit cylinder prims, each requiring translate + orient + height computation. This tripled the clip file size (8 MB atoms-only -> 18 MB with bonds). At production scale (thousands of frames, potentially tens of thousands of bonds including solvent), this is untenable.

Alternatives not yet prototyped:
- **Implicit bonds**: Render-time bond inference from atom positions + connectivity table. No bond prims in the stage at all. Requires custom Hydra delegate or render plugin.
- **UsdGeomBasisCurves**: Encode bonds as curve primitives (two points per curve). Much lighter than cylinders. Supported natively by Hydra/Storm.
- **Shader-based bonds**: Geometry shader that generates cylinders from line segments at render time. GPU-efficient but requires custom rendering code.

### 3.3 Composition Arcs Not Yet Exercised

| Arc / Pattern | Architectural Vision | Prototype Status |
|--------------|---------------------|------------------|
| References for asset libraries | Canonical residue/element libraries as referenced assets | Not demonstrated -- SubLayers used instead |
| Payloads for deferred loading | Heavy trajectory data loaded on demand | Not demonstrated -- Value Clips used (related but distinct) |
| Ensemble VariantSet (`ReplicaID`) | Toggle between REUS replicas | Not demonstrated |
| Perturbation VariantSet (`Genotype`) | In silico mutagenesis | Not demonstrated |
| Parameter VariantSet (`ForceField`) | Force field comparison | Not demonstrated |
| Specializes arc | Base-class corrections propagate forcefully | Not demonstrated |
| Departmental layering | Biology/Protocol/Dynamics/Analysis/Review as separate SubLayers | Only Biology+Dynamics separation shown |
| Analysis data as USD attributes | PMF, RMSD, contacts as attributes or prims | Not demonstrated |

### 3.4 Data Provenance and Metadata

The assembly records `bio:source = "ShinobuLab MD simulation"` but there's no structured provenance chain: which PDB file, which force field parameters, which software version, which simulation settings produced the data. Film pipelines solve this with asset management systems that track every revision. Biology needs equivalent lineage tracking, either within USD metadata or via an external system that USD references.

---

## 4. Open Questions

### 4.1 References vs. SubLayers for asset composition

We used SubLayers everywhere: element templates sublayered into residue templates, assembly sublayered into demos. The architectural vision maps References to "the literature" (standard asset libraries). In film, a character rig is *referenced* into a shot, not sublayered -- because referencing encapsulates the asset under a namespace, while sublayering merges it into the root.

For biology: should a canonical alanine residue be a *reference* (encapsulated, version-pinned, replaceable) or a *sublayer* (merged into the stage, editable in place)? The answer likely depends on whether the residue is a shared library asset or an active part of the experiment. This distinction needs prototyping with both approaches to feel the ergonomic difference.

### 4.2 Where do bonds live architecturally?

Bonds are currently sibling prims to atoms within a residue. This works but raises questions:
- Inter-residue peptide bonds live at the chain level, breaking the residue encapsulation
- Bond geometry (cylinders) is heavy and couples visualization to data representation
- Molecular viewers like VMD and PyMOL infer bonds from distance at load time rather than storing them

Should bonds be: (a) explicit geometry prims as now, (b) relationship arcs between atom prims (`rel bio:bondedTo`), (c) a connectivity table attribute on the assembly root, or (d) inferred at render time? Each choice has different implications for the schema, for composition, and for performance.

### 4.3 Cross-scale representation

The architecture envisions a single class prim representing a molecule at multiple scales: all-atom mesh at the MD level, a single sphere with `rate_constant` at the systems biology level. This is the `representation` VariantSet taken to its logical extreme. But it hasn't been prototyped beyond the four visual modes (points/balls/vdw/ballstick). A coarse-grained variant that collapses thousands of atoms into a single bead, or an abstract variant that replaces geometry with a data-carrying point, would test whether the composition model holds across scales.

### 4.4 Multi-system composition

All prototyping has been within a single molecular system (ABL kinase + ATP). Production biology involves composing multiple systems: a protein binding to a membrane, a cell containing thousands of molecules, a tissue containing millions of cells. How does the hierarchy extend beyond a single assembly? USD's namespace isolation via References should handle this, but it hasn't been tested.

---

## 5. Prototyping Experiments Still Needed

These are ordered by information value -- which experiments most reduce uncertainty about production architecture.

### Experiment 1: PointInstancer for Solvent (High Priority)

**Question:** Can 61,273 water molecules (183K atoms) be rendered interactively using PointInstancer with prototype variants?

**Why it matters:** This is the single largest scaling bottleneck. If PointInstancer handles solvent well, the hybrid approach (individual prims for protein, PointInstancer for solvent) covers the full solvated system. If it doesn't, we need UsdGeomPoints or a custom solution.

**Deliverable:** Solvated assembly demo with protein (per-atom Xforms) + water (PointInstancer) composing in one scene. Measure load time, mode-switch latency, memory.

### Experiment 2: Binary Format + Clip Templates (High Priority)

**Question:** What's the size and performance difference between `.usda` and `.usdc` for assemblies and clips? Does the clip template pattern (`clipTemplateAssetPath`) work for mapping multiple XTC files?

**Why it matters:** Directly determines whether the current architecture is viable at production scale or needs fundamental restructuring. The answer might be "just use `.usdc` and it's fine" -- or it might reveal that per-atom clips are inherently too slow regardless of format.

**Deliverable:** Same assembly + trajectory in `.usdc` format. Benchmark load time, scrub latency, file size. Test clip template pattern with 2-3 XTC source files stitched together.

### Experiment 3: Departmental Layering with Real Workflow (Medium Priority)

**Question:** Does the Biology/Protocol/Dynamics/Analysis/Review layer separation work in practice when multiple people edit different layers?

**Why it matters:** This is the collaboration architecture. If layers compose cleanly (disable the dynamics layer, the analysis layer still loads with stale but valid data), it validates the departmental model. If layers have implicit dependencies that break composition, the model needs revision.

**Deliverable:** A 5-layer stage for the ABL kinase system: biology (topology), protocol (solvation box, ions), dynamics (trajectory clip), analysis (RMSD as time-sampled attribute), review (camera positions, annotations). Test toggling layers on/off.

### Experiment 4: Ensemble VariantSet with Payload Swapping (Medium Priority)

**Question:** Can REUS replicas be modeled as a `ReplicaID` VariantSet that swaps Payload references to different trajectory clip files?

**Why it matters:** This is the most novel architectural claim -- that USD's VariantSet + Payload mechanism maps to statistical ensembles. The ShinobuLab data has 50 REUS replicas with pull directories. If variant switching between replicas works smoothly, it validates the core hypothesis-testing architecture.

**Deliverable:** Assembly with `ReplicaID` VariantSet containing 3-5 replicas, each pointing to different clip files. Verify that switching replicas in usdview swaps the trajectory seamlessly.

### Experiment 5: BasisCurves for Bonds (Medium Priority)

**Question:** Can UsdGeomBasisCurves replace cylinder prims for bonds, and how does this affect file size and render performance?

**Why it matters:** The current per-bond cylinder approach added 50% to assembly size and doubled clip size. BasisCurves would be a single prim with point arrays -- dramatically lighter. But the visual quality and Hydra/Storm compatibility need testing.

**Deliverable:** Alternative assembly using BasisCurves for bonds. Compare file size, render quality, and trajectory clip size against the cylinder approach.

### Experiment 6: References vs. SubLayers (Low Priority)

**Question:** What's the practical difference between referencing a residue library and sublayering it?

**Why it matters:** Determines the asset composition model for the schema. Low priority because both work; the question is which is more ergonomic for the biology domain.

**Deliverable:** Same assembly built with References instead of SubLayers for element templates. Compare editability, encapsulation, and file organization.

---

## 6. On the GUI Question

**Short answer:** Yes, a custom viewer is eventually necessary. But the investment is smaller than it appears, and the timing matters.

### What usdview gives us (and where it falls short)

usdview is a developer inspection tool. It provides prim hierarchy browsing, variant switching, attribute inspection, timeline scrubbing, and Hydra/Storm rendering. For prototyping, this is sufficient. For a scientist, it is not, because:

- **No molecular selection semantics.** usdview selects prims, not atoms-in-context. A scientist wants to select "all residues within 5A of the ligand" or "the backbone of chain A." This requires domain-aware selection that understands `bio:` attributes.
- **No measurement tools.** Distance between two atoms, angle between three atoms, dihedral between four -- these are fundamental operations in molecular analysis. usdview has none.
- **No analysis integration.** A scientist wants to plot RMSD vs. frame alongside the 3D view, color atoms by B-factor or charge, overlay distance distributions. This requires a split-pane application with linked data views.
- **No workflow awareness.** usdview doesn't know about the departmental layer model. A scientist should see toggles for "show/hide solvent", "enable analysis overlay", "switch to replica 3" -- not raw variant and layer controls.

### What we should NOT build

A molecular viewer from scratch. VMD, PyMOL, ChimeraX, and SAMSON have decades of development in molecular interaction, selection languages, and analysis tools. Building a competitor is not the goal.

### What we should build

A **thin domain layer** on top of Hydra rendering, providing:

1. **Molecular selection language** that queries `bio:` attributes and translates to USD prim selections
2. **Measurement overlays** (distances, angles) as USD prims themselves (composable, saveable)
3. **Layer/variant control panel** with biology-aware labels ("Representation", "Replica", "Force Field" instead of raw VariantSet names)
4. **Analysis side panel** that reads time-sampled `bio:` attributes and plots them synchronized to the timeline

### The platform question

Three viable approaches, in order of increasing investment:

**Option A: usdview plugin.** usdview supports custom plugins (Python). Lowest effort. Limited by usdview's Qt-based architecture and its assumption of a developer audience. Good for near-term prototyping.

**Option B: Omniverse extension.** NVIDIA's Kit/Omniverse SDK provides a full application framework with Hydra rendering, UI toolkit, and extension system. Higher effort but production-grade. Requires NVIDIA ecosystem buy-in.

**Option C: Standalone app with Hydra.** Build a custom application using Hydra as the render engine (via `UsdImagingGLEngine` or the Hydra standalone API), with a custom UI framework (Qt, Dear ImGui, or web-based). Maximum flexibility, maximum effort. This is what film studios do for proprietary tools.

**Recommendation:** Start with **Option A** (usdview plugin) to prototype the molecular selection and measurement UX. If the concept proves out, migrate to **Option C** for production -- by then the schema will be stable enough to justify the investment. Option B is worth evaluating if Omniverse's ecosystem aligns with the target user base.

### Film production comparison

Film studios do not typically use usdview for production work. They use proprietary viewers built on Hydra (Disney's Presto, Pixar's usdview-derived internal tools, DreamWorks' MoonRay viewer) or commercial DCCs with USD integration (Maya, Houdini, Katana). The common pattern: **USD provides the data model and composition engine; the viewer is domain-specific.** UsdBio should follow the same pattern.

---

## 7. On the Pipeline Automation Question

This is the right question to ask early, because the pipeline architecture constrains everything else.

### The current state: manual scripts

Today, generating the assembly requires running a sequence of Python scripts in order:

```
python3 templates/01_create_element_templates.py
python3 templates/04_create_assembly.py
python3 converters/xtc_to_clips.py
python3 demos/trajectory_demo.py
```

This is appropriate for prototyping. It is not appropriate for a lab where a graduate student finishes a 100ns simulation run and wants to see it immediately.

### How film production solves this

Film studios operate **asset pipeline systems** -- software that watches for new data, runs conversion/validation, publishes assets to a database, and notifies downstream consumers. Key components:

1. **Asset database** (ShotGrid/Flow, Prism Pipeline, ftrack): Tracks every asset version, who created it, what it depends on. Every USD file has a database entry with metadata.

2. **Publish system**: When an artist saves a Maya scene, a publish hook converts it to USD, validates it against the schema, registers it in the database, and places it in the correct filesystem location with a versioned path.

3. **Asset resolver** (`ArResolver`): USD's pluggable asset resolution system. Instead of `@/path/to/file.usd@`, references can be `@asset:protein/abl_kinase/v3@` and the resolver translates this to the actual file path at composition time. This is how studios decouple scene description from filesystem layout.

4. **Watch/trigger system**: Filesystem watchers or CI-like triggers that detect new data and run conversion pipelines automatically.

### What a biology pipeline needs

The film model maps directly, with domain-specific adaptations:

| Film Component | Biology Equivalent |
|---------------|-------------------|
| Asset database (ShotGrid) | Experiment database tracking PDB files, topologies, trajectory runs, analysis results |
| Publish hook (Maya -> USD) | Converter hooks: new PDB drops -> `pdb_parser.py` + `04_create_assembly.py` run automatically |
| Trajectory ingest | New XTC appears -> `xtc_to_clips.py` generates clips, registers with clip template |
| Asset resolver | `@bio:experiment/abl_kinase/run_042/trajectory@` resolves to the correct `.usdc` clip file |
| Validation | Schema validation on publish: does the USD file conform to UsdBio schema? Are required attributes present? |

### The ArResolver is the key infrastructure piece

USD's `ArResolver` is the mechanism that makes "drop data, it just appears" possible. A custom `ArResolver` for biology would:

- Resolve `@bio:element_library/v1@` to the current element templates
- Resolve `@bio:experiment/abl_kinase/trajectory/replica_03@` to the correct clip file
- Support versioning: `@bio:experiment/abl_kinase/assembly/v2@` vs `v3`
- Optionally resolve remote URIs for data stored on lab servers or cloud storage

This is a C++ plugin (USD's resolver is C++-only) that would ship as part of UsdBio. It's a modest implementation but a critical one -- it's the difference between "run these 4 scripts" and "data just appears when you open the stage."

### Incremental path

The pipeline doesn't need to be built all at once:

1. **Now (prototyping):** Manual scripts. Fine.
2. **Next:** Single `make`/`invoke` command that runs the full conversion pipeline. Detects what's changed and only rebuilds what's needed.
3. **Then:** Filesystem watcher (Python `watchdog` or similar) that triggers conversion when new PDB/XTC files appear in designated directories.
4. **Later:** Custom `ArResolver` that abstracts filesystem paths into semantic asset identifiers.
5. **Production:** Full asset database with web UI for browsing experiments, tracking provenance, and managing pipeline runs.

---

## 8. Toward a Production Roadmap Structure

We are not ready to write the multi-phase production roadmap yet. What's missing is the output of Experiments 1-4 from Section 5. Those experiments will answer:

- **Can the per-atom model scale?** (Experiment 1: PointInstancer, Experiment 2: binary format)
- **Does composition hold for real workflows?** (Experiment 3: departmental layering, Experiment 4: ensemble variants)
- **What's the bond strategy?** (Experiment 5: BasisCurves)

Once those answers are in, the production roadmap would likely have this shape:

### Phase 0: Scaling Validation (where we are after v8 + experiments)
- All composition patterns validated with real data
- Performance characteristics known for target scale
- Bond representation strategy chosen

### Phase 1: Schema Definition
- `UsdBioElement`, `UsdBioAtom`, `UsdBioResidue`, `UsdBioChain`, `UsdBioAssembly` as C++ IsA schemas
- Schema generation from `usdGenSchema` with proper fallback values
- Python bindings auto-generated
- Validation plugin for `usdchecker`

### Phase 2: Converter Library
- Production-grade PDB/mmCIF/PDBx parser (C++ for performance, Python bindings)
- XTC/DCD/TRR trajectory converter with clip template output
- AMBER prmtop / GROMACS topology parser for force field metadata
- Analysis format converters (MBAR, PMF -> USD attributes)

### Phase 3: Pipeline Infrastructure
- Custom `ArResolver` for biology asset resolution
- Build system (CMake-based, matching USD's own build)
- Filesystem watcher for automated ingest
- Provenance tracking metadata schema

### Phase 4: Viewer / Application Layer
- Molecular selection language (query `bio:` attributes)
- Measurement tools as USD prims
- Domain-aware layer/variant control panel
- Analysis visualization synchronized with timeline

### Phase 5: Community and Ecosystem
- Open-source release with documentation
- Example datasets and tutorials
- Integration guides for existing tools (VMD, PyMOL, ChimeraX)
- Schema registry submission to OpenUSD Alliance

---

## Summary

The v8 prototyping phase has answered the fundamental viability question: **yes, OpenUSD's composition engine can represent the full data lifecycle of computational biology research using built-in types.** The remaining work is not about proving the concept -- it's about scaling it, formalizing it, and making it usable.

The six experiments in Section 5 are the bridge between prototyping and production planning. They're scoped to answer specific architectural questions whose answers determine the shape of the production roadmap. Until they're done, any production roadmap would be speculative.

What we should *not* do is rush to C++ schemas or a custom GUI before the composition patterns are fully settled. The prototyping phase exists precisely to make the expensive investments (schema definitions, C++ infrastructure, application development) go right the first time.
