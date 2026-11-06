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

## Verifier verdict

## Continuity notes
