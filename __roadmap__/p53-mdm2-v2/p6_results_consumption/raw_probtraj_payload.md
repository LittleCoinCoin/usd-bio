# Raw MaBoSS State-Space Output as a Payload

**Goal**: Stop discarding MaBoSS's own output files and commit one run directory as the evidence of record, following the `ddmut_ppi_live` precedent the PI endorsed in Q-013.3. Re-scoped on 2026-11-06 from the PI's 2026-09-22 Q-013 answer: the Payload half (former Steps 2–3) is deferred per Q-013.4 and preserved in the blocked sibling `state_space_payload.md`. The file stem and Mermaid title are kept, because nodes are never renamed.
**Pre-conditions**:
- [ ] `run_maboss.run_cfg()` runs into a `tempfile.mkdtemp` and keeps only `get_nodes_probtraj()`, so MaBoSS's `*_probtraj.csv`, `*_fp.csv` and `*_statdist.csv` are written and then lost [source: `examples/p53_mdm2/maboss/run_maboss.py`, as read for R15]
- [ ] The reference `.cfg` sets `sample_count = 50000`, `statdist_traj_count = 100`, `max_time = 50`, `time_tick = 0.1`, `seed_pseudorandom = 100`, `thread_count = 1` [source: `examples/p53_mdm2/maboss/reference/p53_Mdm2_runcfg.cfg`]
- [ ] PI Q-013.3 answer: one committed run directory, on the `ddmut_ppi_live` precedent [source: `__threads__/p53-mdm2/QUESTIONS.md` Q-013]
**Success Gates**:
- ⬜ `[static]` One MaBoSS run directory, holding one subdirectory per variant, is committed verbatim under `examples/p53_mdm2/maboss/output/`. It contains the files the binary itself wrote, plus a provenance record naming the binary version, seed, sample count and time grid. No file in it ends in `.log`, since `.gitignore` swallows that extension
- ⬜ `[static]` The provenance record lists the binary-written files, so that a run digest over exactly those files can be recomputed. R20's stale guard for the native plots keys on this digest
- ⬜ `[run]` `tests/run_tests.py` reports zero failures, and the committed layers rebuild byte-identical
**References**: [R20 §stale guard](../../../__reports__/p53-mdm2/20-results_layer_and_texture_assets_v0.md) — why the run directory's file list must be digestible; [R15 §Current State](../../../__reports__/p53-mdm2/15-results_consumption_boundary_v0.md) — the discarded-output finding this leaf fixes

## Step 1: Persist MaBoSS run output instead of discarding it
**Goal**: Make the binary's own output a durable artifact, since the native plots and any future re-analysis need files that today exist only inside a temporary directory.
**Implementation Logic**:
`run_cfg` sanitises the model into a temp directory, runs it, reads one DataFrame and lets the rest evaporate. Redirect the run into `maboss/output/run_<UTC>/<variant>/` instead, per the project's rule that per-run directories keep concurrent runs from overwriting each other's evidence. Keep the pyMaBoSS default `res` prefix and the flat one-directory layout, because that is the layout `maboss.StoredResult` expects.
Commit exactly one run directory as the evidence of record, following `data/ddmut_ppi_live/`. Ignore later `run_*` directories so repeated runs do not accrete in the history.
Write the provenance record outside the set of binary-written files, so a digest over those files never includes itself.
Implemented in parallel by cycle-013's agent B. This leaf records the scope, not the outcome.
**Deliverables**: `examples/p53_mdm2/maboss/run_maboss.py` — `run_dir()`, `run_cfg(..., keep_dir=)`; `examples/p53_mdm2/maboss/output/run_<UTC>/` — the committed reference run, one subdirectory per variant plus a provenance record naming binary version, seed, sample count, time grid and the binary-written file list; `.gitignore` — rule keeping only the committed reference run
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import glob, os; d = sorted(glob.glob('examples/p53_mdm2/maboss/output/run_*')); assert d, 'no committed run dir'; f = glob.glob(os.path.join(d[-1], '*', '*_probtraj.csv')); assert len(f) == 4, f; assert not glob.glob(os.path.join(d[-1], '*', '*.log'))"` (expected: PASS)
**Commit**: `feat(p53-mdm2): persist MaBoSS run output as a committed reference run directory`
