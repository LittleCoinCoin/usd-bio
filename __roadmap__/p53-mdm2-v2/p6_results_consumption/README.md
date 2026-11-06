# P6 Results Consumption — Making Simulation Output Legible

## Context
Answers the PI's 2026-07-29 workstream question — "we should also be able to see the visuals from the simulation and not only the numbers" — for the four pipelines that already run end-to-end. It depends on nothing beyond the committed Analysis layer. **Amendment of 2026-11-06 (cycle-013)**, following the PI's 2026-09-22 answer to Q-013 and R20 `[source: __threads__/p53-mdm2/QUESTIONS.md Q-013; __reports__/p53-mdm2/20-results_layer_and_texture_assets_v0.md]`: (1) R15's opacity rule is overruled, so rendered MaBoSS PNGs are committed and referenced from USD as texture-like assets with R20's run-digest stale guard; (2) Review is annotations-only, so the result curves move to a separate **Results** SubLayer: `results_layer_curves.md` is added and `review_layer_plots.md` is blocked; (3) one run directory is committed, on the `ddmut_ppi_live` precedent, and `raw_probtraj_payload.md` is trimmed to that step; (4) the state-space payload is deferred, and `state_space_payload.md` is blocked and preserves the design. The Amendment Log row for this change is **not written**, because `dirtree-rdm` 0.1.0 has no command that writes that table and the project forbids hand-editing it; see R20 §What I am uncertain about. The tool-managed Mermaid titles of `raw_probtraj_payload` ("…as a Payload") and `native_plots` ("…Out-of-Stage Byproducts") now under-describe their re-scoped content, because nodes are never renamed. The leaf prose is authoritative.

## Reference Documents
- [R20 results layer + texture assets](../../../__reports__/p53-mdm2/20-results_layer_and_texture_assets_v0.md) — the amendment's source: how OpenUSD handles textures, why "most recent wins" needs a custom resolver, the run-digest stale guard, and the cost of a Results department
- [R15 results-consumption boundary](../../../__reports__/p53-mdm2/15-results_consumption_boundary_v0.md) — the architecture analysis this subtree implements: the opacity rule, the three-tier input/observable/rendering split, why plots are not payloads, and the verified pyMaBoSS capability table
- [R02 ΔG↔MaBoSS correlation design](../../../__reports__/p53-mdm2/02-dg_maboss_correlation_v0.md) — the five-node model table the state labels decompose into
- [R00 architecture + reuse map](../../../__reports__/p53-mdm2/00-architecture_v0.md) — the `bio:` sub-namespace conventions and anti-chimera invariants these leaves must preserve

## Goal
Make the p53–MDM2 simulation result legible to a human, both as in-stage geometry and as MaBoSS's own figures committed as texture assets. Every image the stage references is bound to its source run by a test.

## Pre-conditions
- [ ] All four pipelines plus the P5 integrated demonstration committed and passing, so there are real results to consume
- [ ] `analysis/p53_mdm2_analysis.usda` carries `bio:maboss:prob:<node>` time samples for four variants over 500 frames
- [x] R15 reviewed by the PI: answered 2026-09-22 in Q-013, which overruled the opacity rule and moved results out of Review

## Success Gates
- ⬜ A Results SubLayer exists carrying renderable curve geometry, and a read-back check asserts every vertex against the Analysis layer's own time samples
- ⬜ One MaBoSS run directory is committed with a provenance record listing the files the binary wrote
- ⬜ MaBoSS's own figures are generated from the committed run directory and referenced from the Results layer as texture assets, and a stale-guard check records, per texture, whether its run digest, filename token and image hash match what is on disk
- ⬜ Every gate in this subtree records what was observed; none predicts a scientific outcome

## Gotchas
- **Two design-doc rows are now out of step with this subtree, and neither is edited here** (an explicit INTENT scope boundary): [`__design__/openusd_for_research_architecture.md`](../../../__design__/openusd_for_research_architecture.md) §4.1 lists five departments and has no Results row; §3 maps publication visuals to Hydra rendering only. Changing either is a PI decision raised in R20. Leaves use `results/` and `bio:results:`, which survive any department numbering.
- **"Most recent wins" is not a USD mechanism.** With `ArDefaultResolver` a path has no recency. The stage uses the path the strongest opinion authors. Staleness is prevented by naming each PNG on its source-run digest and testing that, not by recency; see R20.
- **Relative asset paths anchor to the layer holding the strongest opinion**, so a texture path authored in `results/` resolves relative to `results/`. `expressionVariables` do not compose across SubLayers, so do not pin versions with them in the Results layer.
- **A plot cannot be a payload.** A payload arc targets scene description — a layer plus a prim path — so it can never point at a PNG. Any leaf phrased as "payload the plots" is malformed; see R15 §Alternatives.
- **The PI's "50k samples" are not in the USD file.** `sample_count = 50000` is the Monte Carlo trajectory count and is carried as a single scalar `bio:maboss:sampleCount`; what the Analysis layer stores is 4 variants × 5 nodes × 500 frames of node marginals, 310 KB of ASCII. Sizing arguments built on the larger number are wrong.
- **MaBoSS's raw output is currently discarded.** `run_maboss.run_cfg` runs into a `tempfile.mkdtemp` and keeps only `get_nodes_probtraj()`; the state-space, fixed-point and stationary-distribution files are written by the binary and lost. Nothing downstream can consume them until `raw_probtraj_payload.md` lands; cycle-013's agent B is implementing it.
- **Evidence files must never end in `.log`** — `.gitignore` swallows the extension silently. Verify with `git check-ignore -v` before trusting any capture.
- **The `run_tests.py` harness has no skip concept** — `_rows_from` reads `passed` as a bool. Every new test module must return zero rows when its artifact is absent, or the suite goes permanently red.
- **Depth here is a real dependency, not a ranking.** `native_plots/` is nested because `StoredResult` cannot read a run directory that does not exist yet, and because its texture references need the Results layer that `results_layer_curves.md` creates. The live depth-0 leaves, `raw_probtraj_payload` and `results_layer_curves`, are genuinely parallel.

## Status
```mermaid
graph TD
    review_layer_plots[Review Layer — In-Stage Result Curves]:::blocked
    raw_probtraj_payload[Raw MaBoSS State-Space Output as a Payload]:::done
    native_plots[Native MaBoSS Plots as Out-of-Stage Byproducts]:::planned
    results_layer_curves[Results Layer — In-Stage Result Curves]:::amendment
    state_space_payload[State-Space Output as a Payload — Deferred per Q-013.4]:::blocked
    classDef done       fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned    fill:#374151,color:#e5e7eb
    classDef amendment  fill:#1e3a5f,color:#bfdbfe
    classDef blocked    fill:#7f1d1d,color:#fecaca
```

## Nodes
| Node | Type | Status |
|:-----|:-----|:-------|
| `review_layer_plots.md` | 📄 Leaf Task | 🚫 Blocked |
| `raw_probtraj_payload.md` | 📄 Leaf Task | ✅ Done |
| `native_plots/` | 📁 Directory | ⬜ Planned |
| `results_layer_curves.md` | 📄 Leaf Task | 🔵 Amendment |
| `state_space_payload.md` | 📄 Leaf Task | 🚫 Blocked |

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
