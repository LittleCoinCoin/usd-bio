# State-Space Output as a Payload — Deferred per Q-013.4

**Goal**: BLOCKED by PI decision. The PI's Q-013.4 answer (2026-09-22) reads "Let's ignore storing the 50k state space run as payload for now". This leaf preserves the Payload half split out of `raw_probtraj_payload.md` (its former Steps 2–3), so the design is not lost. Reviving it needs a new amendment node, because `blocked` is terminal. R20 also notes that job-119's Dynamics layer has been the campaign's first exercised Payload since cycle-011, which removes one of R15's two reasons for this leaf.
**Pre-conditions**:
- [ ] PI lifts Q-013.4 [source: `__threads__/p53-mdm2/QUESTIONS.md` Q-013 answer item 4]
- [ ] `raw_probtraj_payload.md` landed: one committed MaBoSS run directory containing `*_probtraj.csv` per variant
**Success Gates**:
- ⬜ `[static]` The Analysis layer authors a `payload` arc on each `maboss/<variant>` prim. The payloaded layers contain state-space data and no atom, `mdSetup`, `integration/` or `bio:maboss:prob:<node>` opinion
- ⬜ `[run]` Under `Usd.Stage.LoadNone` the Local `bio:maboss:prob:<node>` samples resolve and no `bio:maboss:stateProb` does; after `Load()` it resolves. Both observations and each payload layer's on-disk size are recorded
- ⬜ `[run]` Marginalising payloaded state probabilities over the states in which a node is ON is compared with `bio:maboss:prob:<node>`, and the per-node maximum absolute difference is recorded
**References**: [R15 §Proposed State](../../../__reports__/p53-mdm2/15-results_consumption_boundary_v0.md) — the original payload design; [R20 §Current state](../../../__reports__/p53-mdm2/20-results_layer_and_texture_assets_v0.md) — why the "first Payload arc" rationale is out of date

## Step 1: State-space payload layers, deferred-load and marginalisation checks
**Goal**: Preserved for a future revival only. Put the state-space trajectory behind a Payload arc and cross-check it against the stored node marginals.
**Implementation Logic**:
Emit one layer per variant with a uniform `token[]` of state labels and a time-sampled `float[]` of per-state probabilities on the Analysis frame grid. Attach each layer to `maboss/<variant>` with a payload arc, authored by the Analysis builder in the same pass.
Then observe deferred loading under `LoadNone`, and run the marginalisation oracle by splitting the `" -- "`-joined labels. Return zero rows when the payload layers are absent.
Not to be executed while Q-013.4 stands.
**Deliverables**: `examples/p53_mdm2/templates/build_analysis_layer.py` — `build_state_payloads()`, `STATE_LABELS_ATTR`, `STATE_PROB_ATTR`; `examples/p53_mdm2/analysis/payloads/p53_mdm2_states_<variant>.usda`; `examples/p53_mdm2/tests/test_state_payload.py` — `run()` with rows `payload_arc_authored`, `payload_deferred_under_loadnone`, `payload_resolves_after_load`, `payload_marginals_match_node_probs`
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$(pwd)/examples/p53_mdm2/tests:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import test_state_payload as t; rows = t.run(); assert rows; import sys; sys.exit(0 if all(r.passed for r in rows) else 1)"` (expected: PASS)
**Commit**: `feat(p53-mdm2): state-space probtraj behind a Payload arc on the analysis layer`
