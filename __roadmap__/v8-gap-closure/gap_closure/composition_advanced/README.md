# Advanced Composition Arcs (depend on layering + clip templates)

## Context
The advanced composition arcs, nested one level below `gap_closure/` because they consume its outputs: `ensemble_payload` needs the clip-template pattern (Exp 2) and a layered stage (Exp 3); `analysis_attributes` needs the Analysis layer from the 5-layer stage (Exp 3). The remaining leaves (`perturbation_variantset`, `parameter_variantset`, `specializes_arc`, `provenance_metadata`) are independent §3.3/§3.4 arcs grouped here as the campaign's final wave. All six are mutually independent and parallel-executable once the prior wave lands.

## Reference Documents
- [R01 cycle-000 audit + roadmap](../../../../__reports__/v8-gap-closure/00-audit_and_roadmap_v0.md) — §3.3/§3.4 arc status
- [R03 architecture vision](../../../../__design__/openusd_for_research_architecture.md) — Ensemble/Perturbation/Parameter variant semantics, Specializes

## Goal
Demonstrate the remaining §3.3 composition arcs and §3.4 provenance, completing architecture-doc parity.

## Pre-conditions
- [ ] `gap_closure/` wave done: clip-template pattern (Exp 2) and 5-layer stage (Exp 3) exist as consumable inputs
- [ ] `pxr` environment available for demos/tests

## Success Gates
- ✅ Ensemble VariantSet (ReplicaID) swaps Payload-referenced trajectories; Perturbation (Genotype) and Parameter (ForceField) VariantSets resolve; Specializes arc demonstrated; analysis data (PMF/RMSD/contacts) carried as time-sampled USD attributes; structured provenance metadata present
- ✅ Each arc has read-back tests asserting the composed result, not generator in-memory state

## Status
```mermaid
graph TD
    ensemble_payload[Exp 4 — Ensemble VariantSet + Payload Swapping]:::done
    perturbation_variantset[Perturbation VariantSet (Genotype)]:::done
    parameter_variantset[Parameter VariantSet (ForceField)]:::done
    specializes_arc[Specializes Arc Demonstration]:::done
    analysis_attributes[Analysis Data as USD Attributes (PMF/RMSD/contacts)]:::done
    provenance_metadata[Structured Provenance Metadata (§3.4)]:::done
    classDef done       fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned    fill:#374151,color:#e5e7eb
    classDef amendment  fill:#1e3a5f,color:#bfdbfe
    classDef blocked    fill:#7f1d1d,color:#fecaca
```

## Nodes
| Node | Type | Status |
|:-----|:-----|:-------|
| `ensemble_payload.md` | 📄 Leaf Task | ✅ Done |
| `perturbation_variantset.md` | 📄 Leaf Task | ✅ Done |
| `parameter_variantset.md` | 📄 Leaf Task | ✅ Done |
| `specializes_arc.md` | 📄 Leaf Task | ✅ Done |
| `analysis_attributes.md` | 📄 Leaf Task | ✅ Done |
| `provenance_metadata.md` | 📄 Leaf Task | ✅ Done |

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
| `provenance_metadata.md` | topic/v8-gap-closure | 6125f0d, c6d02bc, a907436, 71e6d68 | Done (cycle-002): structured 6-field lineage (`bio:sourcePdb`/`forceField`/`softwareName`/`softwareVersion`/`simSettings`(JSON)/`timestamp`) via reusable `apply_provenance_metadata()` helper; `assembly_with_provenance.usda` authored; `04_create_assembly.py` refactored to drop flat `bio:source` for the structured schema; read-back asserts all 6 present+typed, legacy bio:source absent, simSettings JSON parses; 4/4 tests; harness 30/30. Sentinel provenance values (2HYY.pdb, AMBER99SB-ILDN, GENESIS 2.1.0) flagged as representative assumptions. |
| `analysis_attributes.md` | topic/v8-gap-closure | 348c7f4, fe22e07, 6e2e9e6 | Done (cycle-002): time-sampled `bio:rmsd` (10 samples, 1.2→3.8 Å) on /ABLComplex, `bio:pmf` (21-sample Gaussian well) on /ABLComplex/Analysis/PMFProfile, `bio:contactCount` (int, 10 samples) on Lig_ATP; read-back samples at multiple timecodes + held-boundary; 4/4 tests; harness 30/30. DEVIATION: leaf's @4≈2.7 rmsd hint contradicted its own ramp formula (2.3556) — tested the formula value. |
| `specializes_arc.md` | topic/v8-gap-closure | cd7b1ea, a117222, f0832f7, 776fab8 | Done (cycle-002): demonstrates the true Inherits-vs-Specializes LIVERPS contrast across a reference boundary (flat single-file shows no contrast — both local-win — recorded as a finding). Observed (verified vs LIVERPS strength): Inherits instance → root base 2.00 wins over referenced local 9.99 (Inherits>References); Specializes instance → referenced local 9.99 wins over root base 2.00 (Specializes is weakest — base always weaker than instance, even across refs); no-local case → both pick up base. 5/5 tests; harness 30/30. **MAJOR FINDING: the architecture doc §2.1 row S / §7 claim "Specializes source overrides instance" is BACKWARDS** — real USD: with Specializes the base/source is always WEAKER than instance opinions. Flagged for PI; doc not altered (out of scope). |
| `parameter_variantset.md` | topic/v8-gap-closure | 30712a0, 8e4dc8b, 0dca328 | Done (cycle-002): `/ABLFragment` with `ForceField` VariantSet (Amber99/Charmm36) swapping force-field params; composed `bio:partialCharge` on Atom_CA resolves −0.0518 (AMBER) vs −0.02 (CHARMM), `bio:forceFieldName` differs; 9/9 tests; harness 30/30. FINDING: SubLayer-in-variant does NOT compose (sublayers are layer-stack-level, per USD glossary) — switched to Reference-in-variant (primPath-mapped overs); also removed local partialCharge opinions that beat the reference (LIVERPS: Local>Reference). No test weakening. |
| `perturbation_variantset.md` | topic/v8-gap-closure | 5f5dc22, 636f023, 2fbfcf4 | Done (cycle-002): `/ABLKinase` with `Genotype` VariantSet (WildType/T315I), each variant Referencing a distinct mutation-site geometry stub (THR Oγ1 vs ILE Cγ1). Read-back proves composed `bio:residueName` swaps THR↔ILE and sentinel atom positions change per variant; 9/9 tests; harness 30/30. |
| `ensemble_payload.md` | topic/v8-gap-closure | 1e22238, bc21e85, 082cf2c | Exp 4 done (cycle-002): `/ABLEnsemble` with `ReplicaID` VariantSet (rep_01/02/03), each variant authoring a Payload to a distinct clip stub. Read-back proves payload swap resolves at composition level: sentinel points (1,0,0)/(2,0,0)/(3,0,0) per variant; 6/6 tests; harness 30/30. DEVIATION: self-contained base rather than sublayering departmental_demo (avoids /ABLComplex root ambiguity in sentinel assertions); payload-swap mechanics fully demonstrated. |
