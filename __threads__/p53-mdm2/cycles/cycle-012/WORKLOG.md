# WORKLOG — p53-mdm2 cycle-012

## Decision record

- Scope from the cycle-011 HANDOFF: integrate Dynamics per Q-019, parameterise the converter by run, add a roadmap leaf. INBOX empty; INTENT unchanged. `umbod diff` shows the PI answer to Q-019 (2026-11-04) as the only substantive change.
- Q-019.1 (time axis): the PI did not endorse aligning the two clocks. They asked for (i) a literature check that no reliable cross-scale time-integration method exists, (ii) one assumed physical unit for MaBoSS time that we then keep, and (iii) asked whether a dedicated topic should take on the research question. Plan: implement option (c): Dynamics joins the integrated stage with its own ps clock, the stage clock stays MaBoSS-only, no scaling layer offset. Both time units go into the data as explicit `[assumption]`-tagged attributes. A read-only sub-agent runs the literature survey. My view on the dedicated topic goes to the PI as a soft question, since only the PI can `umbod init`.
- Q-019.2 (reference frame): the PI leans toward a single transform on the Dynamics prim. Plan: one rigid Kabsch fit of frame-0 CA onto 1YCR CA, authored as one xformOp. Raw coordinates stay untouched.
- Delegation: an implementation sub-agent in an isolated worktree, and a read-only literature-survey sub-agent running in parallel.

## Work executed

- **Implementation sub-agent** (isolated worktree). Six commits, 32bc626 to 3b9bf0f, merged at 5a66914:
  - `trajectory_to_usd.py` parameterised by run. Byte-identical rebuild confirmed.
  - MaBoSS time unit recorded as `bio:maboss:timeUnit/secondsPerTimeUnit/timeUnitStatus`: 1 h, `[assumption]`, one constant in `run_maboss.py`.
  - Dynamics joined to `demos/p53_mdm2_integrated.usda` by reference with an identity offset. The stage clock stays MaBoSS 0–499, and the build guards against a `timeCodesPerSecond` mismatch (a probe shows USD would rescale).
  - Single Kabsch `xformOp:transform` on `dynamics/trajectory`, fitted on frame-0 CA (98 atoms, chain and residue number identical on both sides): RMSD 71.91 → 0.348 Å.
  - 9 `integrated-dyn` test rows against independent oracles: own PDB/GRO parse, a Horn-quaternion optimum, byte staleness, and a self-test.
  - Roadmap leaf `__roadmap__/p53-mdm2-v2/p7_md_trajectory_integration.md`, added with `dirtree-rdm add` and `update inprogress`; `validate` OK.
- **Coordinator re-ran the suite after the merge: 96/96 PASS.**
- **Literature-survey sub-agent** (read-only, web). Found no accepted direct method for integrating MD time into a Boolean or MaBoSS network as of 2026; the accepted practice is sequential parameter passing. It recommended the 1 h MaBoSS unit (PhysiBoSS convention, 5–6 h p53 pulses) and named the PI's discrete-event idea as on-the-fly kinetic Monte Carlo.
- Report `__reports__/p53-mdm2/19-cycle012_findings_v0.md` plus the index update (e0233ba).
- Raised **Q-020** (soft): should cross-scale time integration get its own topic? It records my recommendation (yes) and asks the PI to accept the 1 h unit.

## Verifier verdict

```
verdict: aligned
inbox-coverage:
  - INBOX.md is empty, and the WORKLOG records "INBOX empty". No inbox-ack item to pair.
  - In place of an INBOX item, the cycle's input was the PI answer to Q-019 (6149dcf, 2026-11-04) plus three cycle-011 HANDOFF promises:
  - Q-019.1(i), literature check for a cross-scale time-integration method → __reports__/p53-mdm2/19-cycle012_findings_v0.md §"What the literature says" (survey is recorded only there, with no raw survey notes)
  - Q-019.1(ii), assume one MaBoSS time unit and keep it → examples/p53_mdm2/maboss/run_maboss.py (ASSUMED_TIME_UNIT*) and examples/p53_mdm2/analysis/p53_mdm2_analysis.usda (bio:maboss:timeUnit/secondsPerTimeUnit/timeUnitStatus)
  - Q-019.1(iii), the PI's "dedicated topic? what do you think?" → __threads__/p53-mdm2/QUESTIONS.md Q-020
  - Q-019.2, single transform on the Dynamics prim → examples/p53_mdm2/composition/dynamics_alignment.py and examples/p53_mdm2/demos/p53_mdm2_integrated.usda (one xformOp:transform on dynamics/trajectory)
  - HANDOFF "integrate per Q-019" → examples/p53_mdm2/demos/p53_mdm2_integrated.usda (reference arc, identity offset) and examples/p53_mdm2/demos/run_end_to_end.py
  - HANDOFF "parameterise converter by run" → examples/p53_mdm2/converters/trajectory_to_usd.py
  - HANDOFF "add roadmap leaf" → __roadmap__/p53-mdm2-v2/p7_md_trajectory_integration.md and __roadmap__/p53-mdm2-v2/README.md
intent-tracking: aligned
work-depth: The depth matches what the cycle committed to.

- **Tests:** The join is backed by 9 new rows in examples/p53_mdm2/tests/test_dynamics_integration.py. They use oracles that do not come from the generator, which is what INTENT's falsification-resistant rule asks for: their own fixed-column parses of 1ycr.pdb and md.gro (_pdb_ca, _gro_chain_atoms), a separate Horn-quaternion optimum (_horn_min_rmsd), a probe of USD's timeCodesPerSecond rescaling, byte checks that the source layers are untouched and not stale, and a mutation self-test.
- **Re-run:** I ran the suite myself and got 96/96 PASS. The working tree was unchanged afterwards apart from the WORKLOG modification that was already there.
- **Report 19:** It backs its claims with numbers: RMSD 71.91 → 0.348 Å over 98 CA atoms, the guard against clock rescaling, and DOIs supporting the 1 h unit. It also states what is not verified: usdview rendering, survey references the coordinator did not open, and the P7 Amendment Log and Progress rows left unedited because they are BNF-managed.
- **Small gaps, none blocking:**
  - The literature survey exists only as a report section. No raw survey notes are kept as an artifact.
  - The 1 h unit is written into the data before the PI accepts it in Q-020. It is tagged `[assumption]`, which is what the PI asked for.
  - The WORKLOG's "Verifier verdict" and "Continuity notes" sections are still empty. That is expected before finish-cycle.
recommended-action: proceed
```

## Continuity notes

- Outcome `open`: the topic is not complete. Value Clips are still unused (they wait for a longer run), and the scientific production MD run is still pending (Q-017).
- P7 roadmap leaf is `inprogress`. Next cycle may mark Step 2 done via `dirtree-rdm update` if the PI accepts the cycle.
- If the PI answers Q-020 with (a), the new topic needs `umbod init` by the PI. If the PI rejects the 1 h unit, change the single constant in `run_maboss.py` and regenerate the analysis and integrated layers.
- A dedicated topic would start from the survey's first question: Kd-only vs kinetics-dependent MaBoSS outcome at equal ΔΔG. The references are in report 19.
