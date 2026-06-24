# v8-gap-closure

## Context
This campaign brings `examples/foundation_demo_v8/` to **architecture-doc parity**: every pattern that `__design__/openusd_for_research_architecture.md` specifies, demonstrated in Python with runnable demos + committed `.usda` (or equivalent evidence) + falsification-resistant tests. It executes the in-scope backlog of `__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md` (§3 gaps + §5 experiments), refreshed against current code in cycle-000 (`__reports__/v8-gap-closure/r0-audit-and-roadmap_v1.md`). It depends on nothing outside the repo; it produces the demos/tests/`.usda` that retire each gap. C++/schema authoring and the p53-mdm2 application are explicitly **out of scope**.

## Reference Documents
- [R01 cycle-000 audit + roadmap rationale](../../__reports__/v8-gap-closure/r0-audit-and-roadmap_v1.md) — refreshed gap status, sequencing rationale
- [R02 v8→production perspective](../../__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md) — authoritative §3 gaps + §5 experiments
- [R03 architecture vision](../../__design__/openusd_for_research_architecture.md) — the parity target (LIVERPS → research)

## Goal
Demonstrate every in-scope architecture pattern (§3 gaps + §5 experiments) in v8 Python, each with a runnable demo, committed artifact, and read-back tests that pass.

## Pre-conditions
- [ ] cycle-000 refreshed audit confirms each gap still open (done — see R01)
- [ ] OpenUSD `pxr` Python environment available via `load_env.sh` for any cycle that runs demos/tests

## Success Gates
- ✅ Foundation wave complete: hard-coded paths removed, falsification-resistant test harness exists and passes against existing v8 artifacts, v8 `ROADMAP/` statuses truthful
- ✅ Every §5 experiment (1–6) closed with a runnable demo + committed artifact + read-back tests
- ✅ Every §3.3 arc (References, Payloads, Ensemble/Perturbation/Parameter VariantSets, Specializes, departmental layering, analysis-as-attributes) and §3.4 provenance demonstrated
- ✅ Each closed gap carries integrity + intent-conformance tests that read the artifact back as a downstream consumer

## Status
```mermaid
graph TD
    portability_fix[Portability Fix — De-hardcode ShinobuLab Paths]:::planned
    test_harness[Falsification-Resistant Test Harness]:::planned
    roadmap_status_correction[Correct Stale v8 ROADMAP Statuses]:::planned
    gap_closure[Gap Closure — §5 Experiments + §3 Arcs]:::planned
    classDef done       fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned    fill:#374151,color:#e5e7eb
    classDef amendment  fill:#1e3a5f,color:#bfdbfe
    classDef blocked    fill:#7f1d1d,color:#fecaca
```

## Nodes
| Node | Type | Status |
|:-----|:-----|:-------|
| `portability_fix.md` | 📄 Leaf Task | ⬜ Planned |
| `test_harness.md` | 📄 Leaf Task | ⬜ Planned |
| `roadmap_status_correction.md` | 📄 Leaf Task | ⬜ Planned |
| `gap_closure/` | 📁 Directory | ⬜ Planned |

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
