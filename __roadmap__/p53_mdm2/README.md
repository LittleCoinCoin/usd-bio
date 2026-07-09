# p53_mdm2

## Context
This campaign builds the runnable, multi-scale **p53–MDM2 demonstration** in which OpenUSD is the shared representation tying molecular dynamics to systems-biology (MaBoSS Boolean-network) modelling, across the four pipelines defined in `__threads__/p53-mdm2/INTENT.md`. New work lands under a fresh `examples/p53_mdm2/`; `foundation_demo_v8/` is inspiration, **not** a copy source. The roadmap is driven by the cycle-000 reuse map and reshaped by the PI's cycle-000 review (answers to Q-001/Q-002): MD trajectories are **not** a hard prerequisite — the MD datum the demo needs is **ΔG**; if the project runs its own MD (dgx1/banyan), the MD **setup parameters** become a greenfield USDBio representation concern; and the ΔG→node "threshold" is replaced by a **ΔG↔MaBoSS-parameter correlation** (ΔG as the inverse of the model's tuned parameters).

## Reference Documents
- [R00 cycle-000 architecture + reuse map](../../__reports__/p53-mdm2/00-architecture_v0.md) — v8 asset classification, external-input decisions (1YCR, MaBoSS 5-node model, ddMut-PPI), anti-chimera invariants
- [R01 MD reproducibility survey](../../__reports__/p53-mdm2/01-md_reproducibility_survey_v0.md) — SOTA for sharing MD setup parameters; recommended `bio:md:` schema (cycle-001)
- [R02 ΔG↔MaBoSS correlation design](../../__reports__/p53-mdm2/02-dg_maboss_correlation_v0.md) — governing MaBoSS parameter, correlation function + inverse, round-trip test design (cycle-001)
- [R03 cycle-001 findings synthesis](../../__reports__/p53-mdm2/03-cycle001_findings_v0.md) — decisions, topic-split rationale, open steering questions (cycle-001)
- [design vision](../../__design__/openusd_for_research_architecture.md) — LIVERPS → research mapping (the parity target; implement, don't rewrite)

## Goal
Run the full end-to-end p53–MDM2 demonstration across all four pipelines (MD/ΔG → USD → ddMut-PPI ΔΔG → binarized MaBoSS model → MaBoSS run → results back onto USD), with committed `.usda` artifacts and passing falsification-resistant read-back tests as the unit of "done", built up over multiple cycles.

## Pre-conditions
- [x] cycle-000 reuse map + external-input decisions filed (R00)
- [x] forOUSD venv available (`/Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3` + `PYTHONPATH`) with both `pxr` and `mdtraj`
- [ ] PI decision on the self-run-MD track (governs whether `p1b_md_parameter_representation` is in the critical path — see Q-003)

## Success Gates
- ✅ `examples/p53_mdm2/` package exists with no `/ABLComplex` literal and no dataset atom-count in library code (anti-chimera invariant, R00)
- ✅ Pipeline 1 emits a committed topology `.usda` for 1YCR with passing read-back tests
- ✅ Pipeline 2 writes ddMut-PPI ΔΔG per p53-peptide variant back onto USD as `bio:` attributes, rate-limited and provenance-tagged (never fabricated)
- ✅ Pipeline 3 emits a `.bnd`/`.cfg` pair whose governing parameter is set by the ΔG↔parameter correlation, round-tripping against the PI-provided reference files
- ✅ Pipeline 4 reads MaBoSS node-state/probability time series back as time-sampled `bio:` attributes in an analysis SubLayer
- ✅ Integrated demonstration runs the full chain with committed artifacts + passing read-back tests

## Status
```mermaid
graph TD
    f1_scaffold[F1 Scaffold + Anti-Chimera Contracts]:::planned
    p1_topology[P1 MD→USD — Topology from 1YCR]:::planned
    p1b_mdparams[P1b MD-Parameter Representation greenfield — gated Q-003]:::blocked
    p2_ddg[P2 USD→ddMut-PPI→ΔΔG]:::planned
    p3_maboss[P3 USD→MaBoSS — ΔG↔param correlation]:::planned
    p4_readback[P4 MaBoSS→USD — time-sampled bio: attrs]:::planned
    p5_demo[P5 Integrated Demonstration]:::planned
    f1_scaffold --> p1_topology
    p1_topology --> p1b_mdparams
    p1_topology --> p2_ddg
    p2_ddg --> p3_maboss
    p3_maboss --> p4_readback
    p4_readback --> p5_demo
    p1b_mdparams -.optional feed.-> p2_ddg
    classDef done       fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned    fill:#374151,color:#e5e7eb
    classDef amendment  fill:#1e3a5f,color:#bfdbfe
    classDef blocked    fill:#7f1d1d,color:#fecaca
```

## Nodes
| Node | Type | Status |
|:-----|:-----|:-------|
| `f1_scaffold.md` | 📄 Leaf Task | ⬜ Planned |
| `p1_topology_from_1ycr.md` | 📄 Leaf Task | ⬜ Planned |
| `p1b_md_parameter_representation.md` | 📄 Leaf Task | 🚧 Blocked (Q-003) |
| `p2_ddg_pipeline.md` | 📄 Leaf Task | ⬜ Planned |
| `p3_maboss_emit.md` | 📄 Leaf Task | ⬜ Planned |
| `p4_maboss_readback.md` | 📄 Leaf Task | ⬜ Planned |
| `p5_integrated_demo.md` | 📄 Leaf Task | ⬜ Planned |

## Traversal
BFS execution order (dependency-respecting): `f1_scaffold` → `p1_topology_from_1ycr` → { `p2_ddg_pipeline`, `p1b_md_parameter_representation` (if Q-003 unblocks) } → `p3_maboss_emit` → `p4_maboss_readback` → `p5_integrated_demo`. Each leaf's step-level decomposition is elaborated when the leaf is picked up (kept coarse here deliberately — a planning-cycle roadmap, not premature over-specification).

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|
| — | 2026-07-10 | cycle-001 initial authoring | all | Initial roadmap from R00 reuse map, reshaped by the PI's cycle-000 review (Q-001/Q-002 answers). |

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
| (none yet) | topic/p53-mdm2 | — | Roadmap authored cycle-001; no leaf executed yet. |
