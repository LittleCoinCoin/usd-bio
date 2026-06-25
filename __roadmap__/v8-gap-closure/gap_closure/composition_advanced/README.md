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
    parameter_variantset[Parameter VariantSet (ForceField)]:::planned
    specializes_arc[Specializes Arc Demonstration]:::planned
    analysis_attributes[Analysis Data as USD Attributes (PMF/RMSD/contacts)]:::planned
    provenance_metadata[Structured Provenance Metadata (§3.4)]:::planned
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
| `parameter_variantset.md` | 📄 Leaf Task | ⬜ Planned |
| `specializes_arc.md` | 📄 Leaf Task | ⬜ Planned |
| `analysis_attributes.md` | 📄 Leaf Task | ⬜ Planned |
| `provenance_metadata.md` | 📄 Leaf Task | ⬜ Planned |

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
| `perturbation_variantset.md` | topic/v8-gap-closure | 5f5dc22, 636f023, 2fbfcf4 | Done (cycle-002): `/ABLKinase` with `Genotype` VariantSet (WildType/T315I), each variant Referencing a distinct mutation-site geometry stub (THR Oγ1 vs ILE Cγ1). Read-back proves composed `bio:residueName` swaps THR↔ILE and sentinel atom positions change per variant; 9/9 tests; harness 30/30. |
| `ensemble_payload.md` | topic/v8-gap-closure | 1e22238, bc21e85, 082cf2c | Exp 4 done (cycle-002): `/ABLEnsemble` with `ReplicaID` VariantSet (rep_01/02/03), each variant authoring a Payload to a distinct clip stub. Read-back proves payload swap resolves at composition level: sentinel points (1,0,0)/(2,0,0)/(3,0,0) per variant; 6/6 tests; harness 30/30. DEVIATION: self-contained base rather than sublayering departmental_demo (avoids /ABLComplex root ambiguity in sentinel assertions); payload-swap mechanics fully demonstrated. |
