# WORKLOG — p53-mdm2 cycle-013

## Decision record

- Manifest: INBOX is empty and INTENT is unchanged. The PI answered Q-020 on 2026-11-05/06: (a) cross-scale-time is opened as its own topic, and the 1 h MaBoSS unit is accepted as the working value. That retires the time-integration thread here; it now lives in `cross-scale-time`. `umbod diff` renders QUESTIONS.md as wholly removed and re-added. On disk the file is intact (20 `## Q-` entries), so this is a diff-rendering artefact, not data loss.
- The cycle-012 continuity notes say to close P7 if the PI accepts the cycle. The PI acked, and all six P7 gates are ✅, so P7 → done.
- **Unacted PI input found.** The PI's 2026-09-22 answer to Q-013 (the opacity rule) has never been acted on, and cycles 009–012 all worked the MD track. The P6 subtree still encodes the rejected design. The answer had four parts:
  1. Overrule the opacity rule: commit rendered PNGs the way artists' textures are tracked in OpenUSD. The PI asks how to avoid stale ones, how textures are usually handled, and whether "rename the asset, most recent wins" is the pattern.
  2. The Review layer is meant for annotations only. The PI asks what results as their own layer would cost.
  3. One committed run directory, following the ddmut_ppi_live precedent.
  4. Skip the 50k state-space payload for now.
- Plan, two parallel sub-agents in isolated worktrees:
  - **A — research, report and roadmap amendment.** Using context7 OpenUSD docs, find how USD handles texture and asset versioning (asset paths, resolver, versioned or content-addressed paths, `assetInfo`) and answer the PI's three Q-013 follow-ups. Cost a separate Results department layer against Review. Write report 20. Then re-scope the P6 subtree with `dirtree-rdm` to match the PI's decisions, and mark P7 done.
  - **B — implementation.** Stop discarding MaBoSS's run output. Commit one run directory per the ddmut precedent, with provenance. This is needed under every option, and it is the precondition for the native plots. The payload half is dropped per Q-013.4. The suite must stay green and the committed layers must rebuild byte-identical.
- Deferred: the Results-layer curves and the PNG asset implementation wait for report 20's recommendation, and the PI may want to weigh in on the stale-PNG guard.

## Work executed

- **Agent B, implementation** (isolated worktree): `813809a`, `ef81790`, `3732922`, merged at the `merge: p53-mdm2 committed MaBoSS run directory` commit.
  - `run_maboss.run_cfg(..., keep_dir=)` plus `run_all_kept()` and a `--keep-run` CLI. The default demo path is unchanged. The function refuses a non-empty directory, because pyMaBoSS silently skips the run there.
  - Committed `examples/p53_mdm2/maboss/output/run_20261106T004327Z/`: 4 variants, 41 files, 1.48 MB, no `.log`, nothing gitignored. `provenance.json` records the binary (MaBoSS 2.6.6), pyMaBoSS 0.8.15, seed, sample count, time grid, input digests, and every file's SHA-256 and the program that wrote it.
  - A `.gitignore` rule keeps only this run.
  - Re-run determinism: every CSV is byte-identical. Only the clock lines in `res_run.txt` differ.
  - Rebuild: `--from-committed` gives `git diff --exit-code` 0. The default demo differs only in hop-2's pre-existing `bio:timestamp`, which the agent reproduced on the untouched base.
  - New `maboss-run-dir` test layer, 8 rows. Node marginals recomputed from the CSV match `bio:maboss:prob:<node>` to ≤3.0e-08 for every variant and node.
- **Agent A, research, report and roadmap** (isolated worktree): `a09e1b5`, `4b70440`, `a08cf20`, merged at `97e842e`.
  - Report `__reports__/p53-mdm2/20-results_layer_and_texture_assets_v0.md` answers the PI's three Q-013 follow-ups from context7 OpenUSD docs. USD stores only asset paths, and "most recent wins" is not a default-resolver mechanism. It recommends a run-digest-versioned filename with a deterministic stale-guard test, and costs a Results SubLayer as small, apart from the design-doc decision.
  - PNG determinism probe in `__reports__/p53-mdm2/evidence/20-png_determinism_probe.{py,txt}`.
  - P7 → done.
  - P6 re-scoped to the PI's decisions: `results_layer_curves` added; `review_layer_plots` blocked; `raw_probtraj_payload` trimmed to the run directory; `state_space_payload` split out and blocked; native plots now commit PNGs with the guard. `dirtree-rdm validate` passes on all P6 files.
- **Coordinator:**
  - Re-ran the suite on `topic/p53-mdm2` after the merges: **104/104 PASS** (was 96/96).
  - Marked `raw_probtraj_payload` done and `p6_results_consumption` in progress with `dirtree-rdm update`, because B's work meets all three gates of the trimmed leaf. Root and P6 READMEs validate OK.
  - Registered soft Q-021 (Results as a sixth department, and its strength order), Q-022 (stale-guard choices) and Q-023 (Amendment Log row, state-space payload future).
- **Not done:** the Results-layer curves and the PNG textures. Both wait on Q-021/Q-022, since they touch the design doc's department list.

## Verifier verdict

```
verdict: minor-concern
inbox-coverage:
  - INBOX.md is empty, and no `umbod inbox-ack` items were consumed this cycle. The begin-cycle commit 266f44c only consumes `pi-reviewed`. Recorded at __threads__/p53-mdm2/cycles/cycle-013/WORKLOG.md:5. There are no ack'd items to pair.
  - PI answer to Q-020 (open cross-scale-time, accept the 1 h unit) → __threads__/p53-mdm2/cycles/cycle-013/WORKLOG.md:5 routes it to the `cross-scale-time` topic. Nothing in p53-mdm2 needed to change. Adequate.
  - Cycle-012 HANDOFF "close P7 if the PI acks" → __roadmap__/p53-mdm2-v2/README.md (P7 → done) and __roadmap__/p53-mdm2-v2/p7_md_trajectory_integration.md
  - PI answer to Q-013.1 (commit PNGs as textures, stale guard, "rename / most recent wins") → __reports__/p53-mdm2/20-results_layer_and_texture_assets_v0.md, __reports__/p53-mdm2/evidence/20-png_determinism_probe.{py,txt}, __roadmap__/p53-mdm2-v2/p6_results_consumption/native_plots/pymaboss_stored_result_plots.md. The PNGs themselves are not built. That is owned at WORKLOG.md:35 and Q-022.
  - PI answer to Q-013.2 (Review is for annotations only; cost of a separate results layer) → R20 §"Results as its own layer — the cost", __roadmap__/p53-mdm2-v2/p6_results_consumption/results_layer_curves.md (new), review_layer_plots.md (blocked), and Q-021 in __threads__/p53-mdm2/QUESTIONS.md
  - PI answer to Q-013.3 (one committed run directory, ddmut precedent) → examples/p53_mdm2/maboss/output/run_20261106T004327Z/ (with provenance.json), examples/p53_mdm2/maboss/run_maboss.py (keep_dir / --keep-run), .gitignore, examples/p53_mdm2/tests/test_maboss_run_dir.py
  - PI answer to Q-013.4 (skip the 50k state-space payload) → __roadmap__/p53-mdm2-v2/p6_results_consumption/state_space_payload.md (split out, blocked) and Q-023(2)
intent-tracking: drift-documented at __threads__/p53-mdm2/cycles/cycle-013/WORKLOG.md:7. The cycle turns from the MD track back to the long-unacted Q-013 answer and names why. That is a return to the INTENT's "MaBoSS → OpenUSD" pipeline (results legible in USD), not a move away from it. No design-doc edits were made: R20 sends the §4.1/§3 department change to the PI through Q-021, which is consistent with INTENT's "don't alter the architecture doc's decisions". Deferring the curves and textures is owned at WORKLOG.md:15 and :35.
work-depth: The depth matches what the cycle committed to. R20 (__reports__/p53-mdm2/20-results_layer_and_texture_assets_v0.md) answers every Q-013 follow-up with tagged context7 citations (UsdUVTexture, ArDefaultResolver, assetInfo, variable expressions not composing across sublayers, UsdUtilsComputeAllDependencies). It backs the run-digest naming choice with an observed byte-determinism probe. It also gives an alternatives table, a risk register and an explicit uncertainty list, and it catches that R15's "first Payload arc" argument is out of date. The implementation is falsification-resistant in the INTENT's sense. examples/p53_mdm2/tests/test_maboss_run_dir.py recomputes node marginals with a plain csv parse over the committed res_probtraj.csv and checks them against bio:maboss:prob:<node>. It verifies SHA-256s against provenance.json and checks that the input digests match today's models. It runs an in-process absent-dir selftest, following the CLAUDE.md rule against renaming files on disk. One corner was cut, in bookkeeping. __roadmap__/p53-mdm2-v2/p6_results_consumption/raw_probtraj_payload.md is marked ✅ Done in p6_results_consumption/README.md:56, but all three of its Success Gates still read ⬜, and its Step 1 prose still says "records the scope, not the outcome". The leaf therefore claims done without recording what was observed against each gate. That clashes with P6 README.md:24 ("Every gate in this subtree records what was observed"). Two claims rest on the coordinator's word: the 104/104 suite result and the byte-identical rebuild. They are consistent with the README count change but are recorded only in the WORKLOG, not as an evidence file. The missing Amendment Log row is honestly surfaced as Q-023 and is not a cut corner.
recommended-action: self-correct: flip the three Success Gates in __roadmap__/p53-mdm2-v2/p6_results_consumption/raw_probtraj_payload.md to ✅, each with what was observed (the run-dir path and file count, provenance.json listing the binary-written files, and the suite at 104/104 with `--from-committed` git diff exit 0), through dirtree-rdm if it supports this, otherwise as the leaf's prose allows. Replace the "records the scope, not the outcome" line with a pointer to commits 813809a/ef81790/3732922. Then finish-cycle with outcome open, pending Q-021..Q-023.
```

**Coordinator response:** self-correct applied in `9732875`. All three gates of `raw_probtraj_payload.md` are now ✅, each with its observation, and the Step 1 line points at `813809a`/`ef81790`/`3732922`. dirtree-rdm has no gate verb, so the leaf was edited directly; the leaf still passes `dirtree-rdm validate`. The suite and rebuild claims stay the coordinator's observations, recorded here and on the gate, with no separate evidence file. Outcome `open`, pending Q-021…Q-023.

## Continuity notes

- P6 state: `raw_probtraj_payload` and P7 are done; `p6_results_consumption` is in progress. The next buildable P6 work waits on the PI. `results_layer_curves` needs Q-021 (Results as a sixth department and its strength order). The native-plot PNGs need Q-022 (the stale-guard choice). `review_layer_plots` and `state_space_payload` are blocked by design.
- If Q-021/Q-022 stay unanswered next cycle, the default is R20's recommendation: a Results SubLayer above Review, and run-digest-versioned PNG names with a deterministic stale-guard test. Build both with no design-doc edit until the PI rules on Q-021.
- Q-023: the root Amendment Log row for the P6 re-scope is BNF-managed and still missing; record it once the PI decides how.
- Leftover from before this cycle: `p7_md_trajectory_integration.md` fails `dirtree-rdm validate` on the missing `**Commit**` fields in Steps 1–2.
- MaBoSS run directory: `run_maboss.py --keep-run` writes a new `run_<UTC>/` that is gitignored. Only `run_20261106T004327Z` is committed.
- dirtree-rdm is not on PATH. This session used a chmod'd copy of the managing-roadmaps skill's `dirtree-rdm-darwin-arm64`.
