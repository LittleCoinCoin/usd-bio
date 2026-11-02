# WORKLOG — p53-mdm2 cycle-011

## Decision record

- Scope from cycle-010 HANDOFF next-decision: fetch job 119 output (gro/xtc) and build the MD->USD read-back of the actual run. PI answered Q-018 (leave the old-sif digest constant as a record of the first build) -> no action. INBOX empty; INTENT unchanged.
- Cluster access was read-only this cycle (fs_ls + SHA-256-verified fs_download on banyan); nothing staged or submitted, so the Q-016 submission authorization was not exercised.
- Committed the source trajectory into the repo (`examples/p53_mdm2/data/md_runs/banyan_job119/`, ~1.9 MB) rather than fetching at test time, following the `ddmut_ppi_live` precedent (PI Q-013.3): read-back tests need a fixed, checksummed source.

## Work executed

- Fetched from banyan `run_p53md_20261020T043135Z/work/`: md.xtc (702768 B), md.gro (1211961 B), topol.top, summary.txt; all transfers `verified: true` via rsync. mdtraj probe: 11 frames, t = 0..100 ps, 17563 atoms, box 6.32 nm. Committed with a sha256 manifest.jsonl at 8be37e3.
- Sub-agent (isolated worktree) built `converters/trajectory_to_usd.py`, two layers `output/p53_mdm2_dynamics_job119.usda` (2471 B, provenance + Payload) and `_frames.usda` (480921 B, 1705 protein+ion atoms as Points, 11 frames, ps time codes, Å), 11 `readback-traj` test rows, and a README LIVERPS P-row update (1640598, c1a6256, eca54f9). The coordinator merged it at ffde1d6 and re-ran the suite: **87/87**.
- Report `__reports__/p53-mdm2/18-cycle011_findings_v0.md`, plus an index update.
- Raised **Q-019** (soft): how Dynamics joins the integrated stage (time axis ps vs MaBoSS frames; GROMACS box vs 1YCR frame). The integrated stage is deliberately untouched.
