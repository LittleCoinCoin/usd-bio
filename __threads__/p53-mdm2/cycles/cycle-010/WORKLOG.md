# WORKLOG — p53-mdm2 cycle-010

## Decision record

- Cycle scope taken from PI answers Q-016/Q-017 (2026-10-20): write read-back checks against job 119 evidence (p53_md_banyan_job119.txt). No cluster work this cycle: the run already completed (attended), nothing further to submit.
- Q-017 accepted (amber99sb-ildn/TIP3P, plumbing run); the force-field divergence tag is asserted, not removed.

## Work executed

- Sub-agent (isolated worktree) wrote examples/p53_mdm2/tests/test_md_run_evidence.py (13 rows) and registered it in run_tests.py; merged. Suite 63 -> 76/76 (re-run by coordinator after merge).
- Findings: the +3 charge is neutralised by 3 CL, NA=16/CL=19 (log shows only `head -3` of genion lines); job 119 SIF digest 221d...95fa differs from the stale constant in test_container_evidence.py -> raised as Q-018 (soft).
- Docstring corrected per verifier: expectations are hand-counted or pinned, not all hand-derived.

## Verifier verdict

minor-concern. Matches intent, no scope creep; the only issue was a docstring overstating independence of pinned expectations (PROTEIN_ATOMS, WATERS, ion counts, GPU strings, digests) -- fixed. Self-test falsification judged genuine (13 mutations). Optional improvement not done: independent 0.15 M x 178.4 nm^3 ~ 16 ion-pair check.

## Continuity notes

- Next: read the produced trajectory/outputs back into USD (MD -> USD for p53-mdm2) once the run artifacts (xtc/gro) are retrieved; not yet fetched locally. Optionally add the ion-pair independent check.
