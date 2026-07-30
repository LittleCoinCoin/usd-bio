# P4 MaBoSS to USD — Time-Sampled Attrs

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

**References**: [R00 §Pipeline 4](../../__reports__/p53-mdm2/00-architecture_v0.md), [R02](../../__reports__/p53-mdm2/02-dg_maboss_correlation_v0.md)

## Step 1: pyMaBoSS run wrapper + output parser
**Goal**: Wrap pyMaBoSS's load/override/run/read-output call shape so any emitted `.bnd`/`.cfg` pair can be run and its node-probability trajectories recovered programmatically.
**Implementation Logic**:
Follows the pyMaBoSS call shape confirmed in R02 (load → override → run → read output). Exposes a per-variant run entry point plus a run-all-variants convenience wrapper, returning node-probability trajectories rather than raw pyMaBoSS objects so callers do not need to know the pyMaBoSS API.
**Deliverables**: `examples/p53_mdm2/maboss/run_maboss.py`
**Consistency Checks**: `. ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "from p53_mdm2.maboss import run_maboss; probs = run_maboss.run_all(); assert probs"` (expected: PASS)
**Commit**: `feat(p53-mdm2): pyMaBoSS run wrapper + node-probability parser`

## Step 2: Write time-sampled node states into an analysis SubLayer
**Goal**: Generalize v8's `_create_analysis_layer` pattern to write MaBoSS node-state/probability series as time-sampled `bio:` attributes in a separate analysis SubLayer, leaving the base topology untouched.
**Implementation Logic**:
Mirrors v8's departmental-layering pattern: an `OverridePrim` in its own SubLayer carries `Usd.TimeCode(frame)`-keyed `bio:` attributes, generalized from `bio:rmsd` to MaBoSS node probabilities. A fresh-open read-back test asserts sampled values against an independent parse of the MaBoSS output, not against the writer's in-memory state.
**Deliverables**: `examples/p53_mdm2/templates/build_analysis_layer.py`, committed analysis `.usda`, read-back test
**Consistency Checks**: `. ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples:$(pwd)/examples/p53_mdm2/tests" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import test_maboss_readback as t; rows = t.run(); import sys; sys.exit(0 if all(r.passed for r in rows) else 1)"` (expected: PASS)
**Commit**: `feat(p53-mdm2): MaBoSS node states as time-sampled bio: attrs (analysis layer)`
