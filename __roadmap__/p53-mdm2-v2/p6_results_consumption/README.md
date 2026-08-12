# P6 Results Consumption — Making Simulation Output Legible

## Context
Answers the PI's 2026-07-29 workstream question — "we should also be able to see the visuals from the simulation and not only the numbers" — for the four pipelines that already run end-to-end. It depends on nothing beyond the committed Analysis layer, and it produces the design doc's unauthored fifth department (Review), the campaign's first exercised Payload arc, and a stated, tested boundary between what a simulation consumer may put into USD and what it may not.

## Reference Documents
- [R15 results-consumption boundary](../../../__reports__/p53-mdm2/15-results_consumption_boundary_v0.md) — the architecture analysis this subtree implements: the opacity rule, the three-tier input/observable/rendering split, why plots are not payloads, and the verified pyMaBoSS capability table
- [R02 ΔG↔MaBoSS correlation design](../../../__reports__/p53-mdm2/02-dg_maboss_correlation_v0.md) — the five-node model table the state labels decompose into
- [R00 architecture + reuse map](../../../__reports__/p53-mdm2/00-architecture_v0.md) — the `bio:` sub-namespace conventions and anti-chimera invariants these leaves must preserve

## Goal
Make the p53–MDM2 simulation result legible to a human without loosening what USD is allowed to store, and settle the producer/consumer boundary with a rule a test can enforce.

## Pre-conditions
- [ ] All four pipelines plus the P5 integrated demonstration committed and passing, so there are real results to consume
- [ ] `analysis/p53_mdm2_analysis.usda` carries `bio:maboss:prob:<node>` time samples for four variants over 500 frames
- [ ] R15 reviewed by the PI, since its boundary rule is what these leaves implement and it excludes options the PI raised

## Success Gates
- ⬜ A Review SubLayer exists carrying renderable geometry whose every vertex a read-back check asserts against the Analysis layer's own time samples
- ⬜ The Payload arc is exercised against MaBoSS's raw state-space output, with deferred loading observed under `LoadNone` rather than asserted
- ⬜ MaBoSS's own figures are generated from the committed run directory, and no committed `.usda` carries an image asset path as an attribute value
- ⬜ Every gate in this subtree records what was observed; none predicts a scientific outcome

## Gotchas
- **The permanent design vision governs three things here, and this subtree implements them rather than revises them** (an explicit INTENT scope boundary): [`__design__/openusd_for_research_architecture.md`](../../../__design__/openusd_for_research_architecture.md) §2.1 row **P** (Payloads as *The Raw Data*), §3's Cinematography → publication-visuals row (Hydra rendering, not imported images), and §4.1's fifth department `05_review.usd` (annotations, cameras, PI comments).
- **A plot cannot be a payload.** A payload arc targets scene description — a layer plus a prim path — so it can never point at a PNG. Any leaf phrased as "payload the plots" is malformed; see R15 §Alternatives.
- **The PI's "50k samples" are not in the USD file.** `sample_count = 50000` is the Monte Carlo trajectory count and is carried as a single scalar `bio:maboss:sampleCount`; what the Analysis layer stores is 4 variants × 5 nodes × 500 frames of node marginals, 310 KB of ASCII. Sizing arguments built on the larger number are wrong.
- **MaBoSS's raw output is currently discarded.** `run_maboss.run_cfg` runs into a `tempfile.mkdtemp` and keeps only `get_nodes_probtraj()`; the state-space, fixed-point and stationary-distribution files are written by the binary and lost. Nothing downstream can consume them until Step 1 of `raw_probtraj_payload.md` lands.
- **Evidence files must never end in `.log`** — `.gitignore` swallows the extension silently. Verify with `git check-ignore -v` before trusting any capture.
- **The `run_tests.py` harness has no skip concept** — `_rows_from` reads `passed` as a bool. Every new test module must return zero rows when its artifact is absent, or the suite goes permanently red.
- **Depth here is a real dependency, not a ranking.** `native_plots/` is nested because `StoredResult` cannot read a run directory that does not exist yet; the two depth-0 leaves are genuinely parallel.

## Status
```mermaid
graph TD
    review_layer_plots[Review Layer — In-Stage Result Curves]:::planned
    raw_probtraj_payload[Raw MaBoSS State-Space Output as a Payload]:::planned
    native_plots[Native MaBoSS Plots as Out-of-Stage Byproducts]:::planned
    classDef done       fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned    fill:#374151,color:#e5e7eb
    classDef amendment  fill:#1e3a5f,color:#bfdbfe
    classDef blocked    fill:#7f1d1d,color:#fecaca
```

## Nodes
| Node | Type | Status |
|:-----|:-----|:-------|
| `review_layer_plots.md` | 📄 Leaf Task | ⬜ Planned |
| `raw_probtraj_payload.md` | 📄 Leaf Task | ⬜ Planned |
| `native_plots/` | 📁 Directory | ⬜ Planned |

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
