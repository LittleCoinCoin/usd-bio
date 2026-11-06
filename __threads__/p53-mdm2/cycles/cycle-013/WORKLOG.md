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

## Continuity notes
