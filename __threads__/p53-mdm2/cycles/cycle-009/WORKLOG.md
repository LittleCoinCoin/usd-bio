# WORKLOG — p53-mdm2 cycle-009

## Decision record

- **Scope came from INBOX 2026-09-25 item 4: the first real p53-MDM2 MD run from 1YCR.** I consumed all nine INBOX entries (`30cd1b7`). Item 1 says the 2026-09-22 entry asking for a rebuild reminder is superseded, so no reminder was created for it.
- **Force field: AMBER99SB-ILDN + TIP3P, not the planned ff19SB.** A read-only probe on 2026-10-14 (`ssh dgx1 singularity exec <sif> ls /opt/gromacs/share/gromacs/top`) showed the image bundles no ff14SB/ff19SB. I chose not to download a port, because that would bring an unvetted external input into a shared image path. The divergence is tagged `[assumption:]` in the USD and raised as **Q-017** (soft).
- **New artifact instead of rewriting the old one.** The GENESIS-planned `p53_mdm2_md_setup.usda` (cycle-003) stays untouched and rebuilds byte-identical. The executed run gets its own `p53_mdm2_md_setup_gromacs.usda`. The schema was extended, not forked.
- **The deck is emitted from the composed USD stage.** The mdp files and `prep.env` come from it, and a staleness test guards the committed copies. That is what makes "reproducible from the USD stage alone" (p1b goal) operational rather than declarative.
- **Short protocol (EM / 100 ps NVT / 100 ps NPT / 100 ps NPT production), per INBOX item 4:** "start with a short run and read its md.log GPU block before anything long".
- **Cluster write refused → stopped, no workaround.** The auto-mode classifier refused the staging command (`mkdir` + `scp` to `/home/eliott/p53mdm2/p53_md`, reason "Remote Shell Writes"). Per INBOX item 5 I did not retry through the dgx1 MCP `fs_upload`, which would have served the same intent. I raised **Q-016** (soft) asking for an attended run, with the exact commands. Inputs are staged *in the repo*: everything the job needs is committed under `examples/p53_mdm2/cluster/p53_md/`.
- **Soft rather than hard questions.** Neither blocks other repo work (p6_results_consumption is still open), so neither should halt topic selection.

## Work executed

1. Read-only probes (coordinator):
   - dgx1 reachable;
   - squeue empty, GPUs idle;
   - the image's force-field list (above);
   - 1YCR completeness: 818 ATOM, no REMARK 470, no altlocs, no HETATM, missing residues terminal only.
2. Implementer sub-agent in an isolated worktree, branch `worktree-agent-ac4782e67d2799de8`, five commits:
   - `4bfa36f` GROMACS `bio:md:` instance + schema extension;
   - `ac04900` USD→mdp/prep.env emitter;
   - `0c0d1bc` container script + dgx1 sbatch;
   - `5d5f0e5` read-back tests + independent fixture, plus a mutation probe that turned checks red;
   - `bd7c8c0` docs.
   Merged `--no-ff` onto `topic/p53-mdm2`.
3. Coordinator re-ran the suite after the merge: **63/63 ALL PASS**. The baseline was 53, not 52.
4. Coordinator reviewed `p53_md_submit.sbatch` / `p53_md_run.sh` / `prep.env` by reading them. Real `gmx` has not run them; the implementer checked them with `bash -n`, shellcheck and a mock-gmx dry run only.
5. Staging attempt refused by the classifier (above). Nothing was written to or submitted on either cluster.
6. `umbod ask` Q-016 and Q-017 (`7680773`).
7. Report `__reports__/p53-mdm2/17-cycle009_findings_v0.md` + README index entry (`fb5b57e`).

## Verifier verdict

Verbatim from the verifier sub-agent (fresh context, read-only):

```
verdict: minor-concern
inbox-coverage:
  - 2026-09-22 entry (schedule an attended-rebuild reminder after Oct 1) → no artifact needed: the 2026-09-25 entry, item 1, marks it superseded, and WORKLOG.md:5 records that no reminder was made (__threads__/p53-mdm2/cycles/cycle-009/INBOX-consumed.md)
  - 2026-09-25 item 1 (the 2026-09-22 entry is superseded) → __threads__/p53-mdm2/cycles/cycle-009/WORKLOG.md:5
  - 2026-09-25 item 2 (use gromacs-2025.3-cuda12.9-sm70_90.sif) → examples/p53_mdm2/cluster/p53_md/p53_md_submit.sbatch:43 (SIF default set to that path; sif sha256 written into the SUMMARY block and the sentinel)
  - 2026-09-25 item 3 (cluster state, for information only; the cleanup gate belongs to the PI) → nothing to deliver; the cycle did not touch the cleanup gate (the footprint has no cluster/evidence or roadmap changes)
  - 2026-09-25 item 4 (first real p53-MDM2 MD from 1YCR: topology, solvation, ions, EM/eq/prod, Slurm script with singularity exec --nv, short run, read md.log GPU block) → examples/p53_mdm2/cluster/p53_md/{p53_md_run.sh,p53_md_submit.sbatch,em,nvt,npt,md.mdp,prep.env}, examples/p53_mdm2/output/p53_mdm2_md_setup_gromacs.usda, examples/p53_mdm2/templates/gromacs_deck.py, examples/p53_mdm2/tests/test_md_gromacs_deck.py. The build-and-script part is delivered. The "run it and read the md.log GPU block" part is not, because nothing was executed (see item 5)
  - 2026-09-25 item 5 (if a submit is refused: stop, stage the inputs, raise a question, no workaround) → __threads__/p53-mdm2/QUESTIONS.md Q-016, WORKLOG.md:10. The cycle stopped at the refusal and did not retry through fs_upload. Inputs are staged in the repo, not on the cluster, and the question gives the exact commands
  - 2026-09-25 item 6 (rsync 2.6.9 MCP failure guidance) → nothing to deliver; no MCP failure was recorded (the probes went over ssh, WORKLOG.md:6)
  - 2026-09-25 item 7 (shres image store out of scope) → nothing to deliver; the sbatch reads the image from the home path (p53_md_submit.sbatch:43)
intent-tracking: drift-documented at __threads__/p53-mdm2/cycles/cycle-009/WORKLOG.md:6. The run uses AMBER99SB-ILDN, 2 fs with LINCS, NPT production and 10 Å cutoffs instead of the planned ff19SB/GENESIS deck. This divergence is named there, in __reports__/p53-mdm2/17-cycle009_findings_v0.md:35-45, in Q-017, and as `[assumption:]` tags in the new .usda. Otherwise the work moves the MD → OpenUSD pipeline toward its first real p53-MDM2 input, which is the direction INTENT.md sets.
work-depth: The depth matches what an unattended cycle could deliver under the refusal. The deck is emitted from the composed USD stage (gromacs_deck.py) and is not hand-written. Unit conversion fails on an unknown unit. The 10 new checks run against a fixture that is kept separate from the generator and transcribed by hand (templates/fixtures/md_setup_gromacs_reference.json). A staleness guard and a mutation probe cover them, and the suite went from 53 to 63. The container script records the evidence the next cycle needs (GPU-placement greps, net charge, residue counts, OXT_ADDED, an EM convergence flag). The report says plainly that no gmx has run and calls the run "built, but not run" (17-cycle009_findings_v0.md:7, :49). Three small corners: (1) WORKLOG.md:42 says the `usd-p53-mdm2-NEXT` reminder is "superseded by Q-016/Q-017", but nothing records whether that reminder was completed or updated, so a stale reminder may still be live. (2) WORKLOG.md:41 notes that the roadmap has no leaf for the executed MD run, but the cycle created none and raised no question about it, so the main deliverable has no node in the task graph. (3) The fixture's `_source` cites the same coordinator brief that the generator values come from. It is independent as a transcription, not as a source of values, and the test docstring could say so. One cosmetic issue: the Q-016 and Q-017 headings repeat their own ID ("Q-016 Q-016 --").
recommended-action: self-correct: say in WORKLOG.md what was done to the `usd-p53-mdm2-NEXT` reminder (completed, updated, or still open), and either add a roadmap leaf for the executed p53 MD run or record why it is deferred. Then proceed to finish-cycle with outcome open, since Q-016 and Q-017 are pending.
```

**Coordinator response (self-corrections applied before finish-cycle):**
- (1) Reminder: the review reminders are written *after* finish-cycle (routine step 4), so this WORKLOG cannot record their final state. Planned action: retire `usd-p53-mdm2-NEXT` (complete it with a `retired: superseded by usd-p53-mdm2-Q-016` log line), and create one reminder each for Q-016 and Q-017. The routine's final report records what was actually written.
- (2) Roadmap leaf: deferred on purpose. Its shape depends on Q-017. If the run is plumbing only (option c), it belongs under p1b as an execution gate. If it is the start of scientific production (a/b), it needs its own leaf with trajectory→USD (Value Clips/Payload) gates. Authoring it now would encode an answer the PI has not given. I raise it in the next cycle once Q-017 is answered.
- (3) Fixture independence: I accept the caveat. The fixture is an independent *transcription*, not an independent *source*: its values come from the same brief the generator implements. It catches emitter and unit bugs, not a wrong choice of parameters. That second kind of error is what Q-017 is for.
- Cosmetic "Q-016 Q-016" heading: this is the umbod ID prefix plus my own prefix in the text. Left as is, because hand-editing QUESTIONS.md is forbidden.

## Continuity notes

- **Next cycle, if the PI ran the job:** copy `p53md-short-<jobid>.out` and `run_p53md_<UTC>/p53_md_out.txt` into `cluster/evidence/` as `.txt` and add a manifest line. Then write read-back checks against the SUMMARY block: net charge +3 before ions, 85 + 13 residues, `OXT_ADDED=A109`, nonbonded and PME on GPU for nvt/npt/md, EM converged, NPT density plausible. If the evidence directory is absent, the checks must return zero rows.
- **Most likely failure mode:** grompp at maxwarn 0, if the COM-removal + posres or the net-charge message is a WARNING in 2025.3. Read the text, then rerun with `GROMPP_MAXWARN=1`.
- The roadmap has no leaf for the executed MD run. p1b's gate 3 (round-trip to a runnable MD input) is met at the deck level only. I did not tick it before a real `grompp` accepts the deck.
- The `usd-p53-mdm2-NEXT` reminder is superseded by Q-016/Q-017 (see the verifier response for the planned reminder action).
- A roadmap leaf for the executed MD run is deferred until Q-017 is answered (see the verifier response).
