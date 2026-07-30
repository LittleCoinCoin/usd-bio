# WORKLOG — p53-mdm2 cycle-007

## Decision record

Entered on `pi-reviewed` after the PI acked cycle-006 and ran an **attended session
2026-07-29 → 2026-07-31** that changed the situation substantially: `gromacs.sif` was
delivered to the shared NFS home via Route B, Route A was killed by observation rather
than inference, and the roadmap was re-founded as `__roadmap__/p53-mdm2-v2/` with the v1
campaign retired behind a blocked banner. `umbod diff` showed edits to **INBOX and
QUESTIONS only** — INTENT unchanged, so no scope renegotiation was required this cycle.

The PI's INBOX brief named the resume point precisely, and the plan followed it rather
than re-deriving one: three leaves under `p1b_container_runtime/` all converge on **one**
missing artifact (`tests/test_container_evidence.py` plus a `container-evidence` layer in
`run_tests.py`), which is repo-only and therefore unattended-safe; and
`dgx1_sif_open_check` is read-only by construction and therefore also unattended-safe
under the Q-006 policy. Everything else in p1b — any container build, the dgx1 GPU smoke
test, a cold-cache rebuild, the cleanup prune — is **PI-attended by standing policy** and
was deliberately not attempted.

Four work units were dispatched to sub-agents; three ran concurrently, the fourth was
serialised because it depended on their outcomes:

| Unit | Scope | Attended? |
|---|---|---|
| A | container-evidence test module + harness registration | no — repo-only, fully offline |
| B | `dgx1_sif_open_check` steps 1–2, read-only cluster capture | no — read-only by construction |
| C | success-gate audit across four container-runtime leaves | no — observation-only |
| D | runbook risk-register rewrite + documentation truth repair | no — repo-only |

Q-006 note, recorded because it is the direct answer to the question that blocked
cycle-006: **no permission classifier refused anything this cycle.** The unattended
read-only cluster path worked. The one tool failure (`fs_checksum` on dgx1) was an
endpoint fault, not a refusal.

## Work executed

**Unit A — container-evidence test module.** `58223d8`. `test_container_evidence.py`
(513 lines) + layer `container-evidence` in `run_tests.py`. 9 rows, all PASS; suite went
**39/39 → 48/48 ALL PASS**. The PI's hard constraint was honoured *and proven*: with
`cluster/evidence/` moved aside the suite still returns `ALL PASS (39/39)` and the layer
contributes **0** rows — `run_tests.py` has no skip concept and reads `passed` as a bool,
so any other behaviour would make the suite permanently red. Per-family darkness was also
demonstrated against synthetic fixtures (good → 2 PASS, corrupted → 2 FAIL, malformed →
`ValueError`, absent → 0 rows). The highest-value assertion is recipe↔evidence
consistency, not the SASS list: pins parsed out of **both** `Dockerfile` and `gromacs.def`,
asserted to agree with each other and then with the captured output — mechanising a sync
obligation the runbook itself concedes is only social.

**Unit B — dgx1 read-only open check.** `a46515b`. `evidence/dgx1_sif_open.txt` +
`manifest.jsonl` seq 4/5. First genuine test of the stage-once-run-anywhere claim, which
until now rested only on matching `df` output.

- Identical sha256 `1fc04f8b…d20c81ac` and identical `5750255616` bytes computed from
  **banyan** and from **dgx1**; both hosts mount the same NFSv4 export `ts2:/export/home`
  from `10.5.1.206`. **Byte parity is now observed, not asserted.**
- Under dgx1 `singularity 3.5.2` (image built by banyan `singularity-ce 4.2.2`):
  `inspect` rc **0** with `GromacsVer: 2025.3`, `TargetSM: 70;90`, no `BuildStatus`;
  `exec … ls` rc **0** showing `gmx` at `/opt/gromacs/bin/gmx`. `exec` is the decisive
  half — `inspect` reads metadata, `exec` must actually mount the squashfs. **The
  version-skew risk did not materialise.**
- Mechanism rather than luck: squashfs 4.0, **gzip**, 128 KiB blocks — the most portable
  compressor, so 4.2.2 never reached for zstd/lz4. **Caveat carried into the register:
  gzip is a builder default, not a contracted guarantee.**
- The leaf predicted `gmx --version` would fail on `libcuda.so.1`; it exited 0 with
  `CUDA driver: 0.0`, consistent with `LIBCUDA_DT_NEEDED=no` (lazy driver resolution).
  That is the expected reading of a driverless run and says **nothing** about skew — and
  is **not** evidence the image can drive a dgx1 GPU.
- Beta-tooling feedback (Q-003 mandate): `mcp__plugin_dgx1_dgx1-hpc__fs_checksum` returned
  `could not communicate with process` — a dgx1-side endpoint failure, **not** a permission
  refusal; the banyan equivalent succeeded on the same 5.75 GB path. Fell back to
  `sha256sum`, recorded in the evidence and in the manifest's `digest_method`.

**Unit C — success-gate audit.** `14a4272`. 20 gates across four leaves; **15 met and
ticked** (glyph-only, no gate text altered; `dirtree-rdm validate` rc=0 on all seven files
before and after), **5 left unticked** — one falsified prediction, one over-claiming
interpretive clause, one leaf/parent honesty divergence, one misplaced-but-true record, and
`dgx1_sif_open_check` gate 4 which Unit D then met. All three defect classes were escalated
as **Q-008** and **Q-010** rather than silently repaired, because each is a question of what
the campaign should promise. Confirmed in passing: R13 exists with `type: observation` and is
indexed; the retired v1 campaign carries its blocked banner plus `MIGRATION.md`.

**Unit D — runbook truth repair.** `d5707ff`, `56ba79b`. The runbook was never updated
after Slurm jobs 32/33, so `cluster/README.md` still asserted in the present tense — in its
**top banner** and six further places — that `gromacs.sif` does not exist, that no GPU has
executed the container, and that the SASS audit is pending. All three false. The
SIF-version-skew entry was rewritten from speculative open risk to observation with citation
and the gzip caveat (`dgx1_sif_open_check` gate 4); the docker-group≈root risk was left
byte-identical, per the leaf. Dated-changelog idiom preserved — cycle-006 entries untouched,
the 2026-07-30 entry's clauses labelled superseded rather than deleted, a new 2026-07-31
entry added. The assertion grep now returns zero hits; the one surviving broader-sweep hit
sits inside an explicitly-superseded dated quote, which `recipe_evidence_corrections` gate 1
expressly allows. Suite re-verified `ALL PASS (48/48)`.

**Orchestrator.** Ticked all four `dgx1_sif_open_check` gates and its `gromacs.sif` exists
pre-condition; filed Q-008/Q-009/Q-010; consumed 12 INBOX entries (`4ece883`).

## Process finding — concurrent sub-agents in one worktree

Units A, B and C ran concurrently in a single git working tree and collided twice. Unit B's
first commit swept in Unit A's staged files, because Unit A staged them in the window
between Unit B's verify and its commit; Unit B repaired it by soft-reset and explicit
pathspec (`71bb6dd` discarded, `a46515b` is the real commit; no files were touched on disk).
Separately, Unit A's zero-rows test renamed `evidence/` aside while Units B and C were
reading it, briefly showing four tracked files as deleted, and one restore nested
`evidence.aside/` inside `evidence/` before being repaired. Final history is correctly
split; the orchestrator verified the tree clean with all five evidence files tracked at
HEAD and no stray `.aside` directories. **Lesson for future cycles: concurrent sub-agents
that share a working tree need `isolation: worktree`, or must be serialised.** Unit D was
serialised for exactly this reason and hit no collision.

## Verifier verdict

**`minor-concern`** — full block is in `HANDOFF.md` verbatim. `intent-tracking:
drift-documented`; `inbox-coverage`: every one of the 12 acked entries paired with an
artifact, none `no artifact found`. The verifier independently re-ran the suite
(`ALL PASS 48/48`), confirmed byte-identity and the older-runtime open are backed by
verbatim captures rather than prose, and confirmed the roadmap diff is glyph-only.

**Self-corrected before close** (`recommended-action: self-correct`, applied): the
truth-repair grep in Unit D was scoped to `cluster/`, so `examples/p53_mdm2/README.md` —
the file a reader opens first — still asserted in the present tense that nothing in
`cluster/` had been built, staged, or submitted. Corrected in `4dc3a0f`; the sweep now
returns **zero** assertions of that class across all of `examples/p53_mdm2/`. Two further
gates that the report agent flagged as substantively met were ticked in the same commit:
`recipe_evidence_corrections` gate 1 and the parent's pin-agreement gate. The cleanup gate
stays **unticked** — it is not met, and the PI recorded it as such.

**Accepted without correction**, recorded here because the PI should see it: the verifier
notes that `dgx1_digest_parity` / `dgx1_sif_opens` read the human-authored `SUMMARY` block
at the head of `dgx1_sif_open.txt` rather than the verbatim shell captures below it, so
their expectation source is the capturing agent's transcription — corroborated by the raw
lines but not independent of them, a notch below the falsification-resistance standard
INTENT §22 sets. `_DELIVERED_SIF_SHA256` supplies one independently-stated anchor. Left as
a known limitation rather than rebuilt this cycle.

## Continuity notes

- **p1b's unattended-safe surface is now exhausted.** What remains is PI-attended by
  policy: the dgx1 GPU smoke test, a cold-cache rebuild, the cleanup prune. This is the
  substance of **Q-009**.
- **Three things not to overstate**, all recorded in-repo and repeated here because this
  topic has been burned on each: build equivalence was measured against a **cached** compile
  layer and is **not** a cold-cache reproduction; the cleanup gate demanding `/` return to
  its pre-work free space is **not met**; and **nothing has ever run on a dgx1 GPU**, nor has
  any p53-MDM2 **MD simulation** ever run on any cluster — only smoke-test water boxes.
- Two new PI workstreams are queued with no roadmap leaves yet: the MaBoSS
  producer/consumer payload boundary, and the communication/graphics deliverables for a
  talk. Both are in **Q-009**; the second may carry a deadline the agent does not know.
