# Cycle-011 findings — the first p53-MDM2 trajectory is in USD, behind a Payload

**Date:** 2026-11-03 · **Topic:** p53-mdm2 · **Cycle:** 011 (unattended) · **Type:** findings

## Headline

The production trajectory of banyan job 119 (100 ps NPT, amber99sb-ildn/TIP3P, a plumbing run per Q-017) is now a USD **Dynamics** layer. Its frames sit behind a **Payload**, so a stage opened with `LoadNone` shows the run's provenance and no coordinates, and `Load()` brings in the 11 time-sampled frames. This is the first use of the Payload arc in p53-mdm2, which the README's LIVERPS table had listed as "not used yet". **Suite: 87/87** (76 before, plus 11 new `readback-traj` rows), re-run by the coordinator after the merge. **The Dynamics layer is NOT in the integrated stage yet.** That needs two PI decisions (Q-019).

## What landed

| Piece | Path | Size | What it does |
|---|---|---|---|
| Source data | `examples/p53_mdm2/data/md_runs/banyan_job119/` | ~1.9 MB | `md.xtc`, `md.gro`, `topol.top`, `summary.txt` from `run_p53md_20261020T043135Z`, fetched read-only with SHA-256-verified `fs_download`. `manifest.jsonl` records each digest |
| Converter | `examples/p53_mdm2/converters/trajectory_to_usd.py` | — | Uses mdtraj to read xtc+gro and writes both layers. It refuses to write if a source digest disagrees with the manifest |
| Light layer | `examples/p53_mdm2/output/p53_mdm2_dynamics_job119.usda` | 2 471 B | `/p53_MDM2_complex/dynamics`: 23 `bio:md:` provenance attributes, plus the Payload on `trajectory` |
| Payload target | `examples/p53_mdm2/output/p53_mdm2_dynamics_job119_frames.usda` | 480 921 B | `/trajectory/{chain_A, chain_B, ions}` as `Points`, in Å, time codes in ps (0…100 every 10) |
| Tests | `examples/p53_mdm2/tests/test_trajectory_readback.py` | — | 11 rows, registered in `run_tests.py` |

## Design choices

| Choice | Why |
|---|---|
| Protein and ions only (1449 + 221 + 35 = 1705 atoms). The 15 858 water atoms are omitted, and the stage records the count | Waters are about 90% of the bytes and carry no biology at this scale |
| One `Points` prim per molecule group, not one prim per atom | Per-atom prims are what made the foundation demo's clips heavy |
| A Payload, not Value Clips | 11 frames fit in a single 481 kB layer. Clips remain the path for long trajectories |
| Time codes in ps, `timeCodesPerSecond = 10` on both layers (a test asserts they match) | A time code reads directly as simulated time. A rate mismatch would make USD rescale the payload |
| Molecules made whole across the periodic box, with no fitting or centring | The raw xtc had 45 protein/ion atoms wrapped one box vector away in the last frame |

## Evidence: oracles independent of the converter

- **Frame grid** comes from `md.mdp`: `nsteps 50000 × dt 0.002 / nstxout-compressed 5000` gives 11 frames at 10 ps spacing.
- **Atom and residue counts** come from `summary.txt` and the `md.gro` header. The chain split is A 25–109 (85 residues) and B 17–29 (13 residues).
- **Final frame** is compared with a separate plain-text parse of `md.gro`. Measured agreement is 0.01 Å against a 0.02 Å tolerance.
- **Whole chains:** the largest consecutive CA–CA distance is 4.08 Å. `md.gro` shows the same 4.08 Å at Lys31–Pro32.
- **Staleness:** both layers are regenerated into a temp directory and byte-compared with the committed files.
- **Self-test:** 8 in-memory mutations, all 8 caught.

## Uncertainty

- `[assumption]` The bound-complex check (chain-centre distance ≤ 20 Å) assumes the peptide stays in the MDM2 cleft. The observed maximum is 12.8 Å.
- `[assumption]` The engine version (2025.3) comes from the pdb2gmx banner in `topol.top`. It was not cross-checked against `md.log`, which was not fetched.
- Not verified: how the layers render in usdview.
- 100 ps is a smoke-length run. Nothing scientific is claimed from it (Q-017).

## Steering

**Q-019 (soft)** asks how the Dynamics layer should join the integrated stage. There are two blockers:

- **Time axes.** The integrated stage counts MaBoSS frames (0–499), while Dynamics counts ps (0–100).
- **Reference frames.** MD coordinates are in the GROMACS box, not the 1YCR crystal frame of hop 1.

## Appendix — verifier verdict (recorded here because the sealed WORKLOG lacks it)

The cycle-011 WORKLOG was sealed by `finish-cycle` **without** its `## Verifier verdict` section. The coordinator's scripted insert failed, and `finish-cycle` ran in the same command anyway. A sealed WORKLOG is immutable, so the verifier's verdict is reproduced here verbatim:

```
verdict: aligned
inbox-coverage: INBOX empty (vacuous); cycle-010 HANDOFF commitments met — job-119 gro/xtc fetched (8be37e3, shasums recomputed and matching the manifest for all 4 files); MD->USD read-back built (converter, two layers, 11 rows registered); Q-018 needed no action.
intent-tracking: drift-documented — Dynamics layer deliberately not joined to the integrated stage, deferred to soft Q-019 (report 18). Otherwise advances INTENT's MD -> OpenUSD pipeline on the real run.
work-depth: matches commitment; verifier re-ran suite 87/87; oracles independent (md.mdp frame grid, summary.txt/md.gro header counts, plain-text md.gro final-frame parse at 0.02 A, staleness byte-compare, 8-mutation self-test); Payload LoadNone tested; gaps owned (engineVersion source, no usdview check, no scientific claim). Corners cut: (a) Q-019 heading duplicates its id, cosmetic (same as all prior umbod-asked Qs); (b) converter takes --run-dir/--out-dir but output filenames/docstrings hard-code job 119, short of INTENT's "generalize"; (c) no roadmap node records this MD->USD trajectory leaf, roadmap_refs empty.
recommended-action: proceed
```

Next-cycle follow-ups from the verifier: parameterise the converter's output names by run (b), and add a `__roadmap__/p53-mdm2-v2/` leaf for the trajectory work (c).
