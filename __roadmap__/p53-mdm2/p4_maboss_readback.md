# P4 — MaBoSS → OpenUSD: node-state time series → time-sampled `bio:` attrs

**Goal**: Run the MaBoSS model emitted by Pipeline 3 (via pyMaBoSS), read its output — node-state/probability trajectories over time — and write it back onto USD prims as **time-sampled `bio:` attributes** in a separate analysis SubLayer, enabling joint MD + systems-biology consultation on one stage.

**Pre-conditions**:
- [ ] Pipeline 3 emits a runnable `.bnd`/`.cfg`
- [ ] pyMaBoSS load/override/run/read-output call shape confirmed in R02 [source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md]
- [ ] v8 analysis-layer pattern to generalize: `_create_analysis_layer` writes time-sampled `bio:rmsd` via `Usd.TimeCode(frame)` on an `OverridePrim` in a separate SubLayer [source: __reports__/p53-mdm2/00-architecture_v0.md §Pipeline 4]

**Success Gates**:
- ⬜ MaBoSS runs from the emitted files and produces node probabilities over time
- ⬜ Node-state/probability series written as time-sampled `bio:` attributes in an analysis SubLayer (departmental layering preserved; base topology untouched)
- ⬜ Read-back test opens the composed stage FRESH and asserts the time samples against the MaBoSS output parsed **independently** (not from generator state)
- ⬜ Value at representative time codes matches MaBoSS's own reported probabilities within tolerance

## Step 1: pyMaBoSS run wrapper + output parser
**Deliverables**: `examples/p53_mdm2/maboss/run_maboss.py`
**Commit**: `feat(p53-mdm2): pyMaBoSS run wrapper + node-probability parser`

## Step 2: Write time-sampled node states into an analysis SubLayer
**Deliverables**: `examples/p53_mdm2/templates/build_analysis_layer.py`, committed analysis `.usda`, read-back test
**Commit**: `feat(p53-mdm2): MaBoSS node states as time-sampled bio: attrs (analysis layer)`

**References**: [R00 §Pipeline 4](../../__reports__/p53-mdm2/00-architecture_v0.md), [R02](../../__reports__/p53-mdm2/02-dg_maboss_correlation_v0.md)
