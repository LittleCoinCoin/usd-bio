# Cycle-012 findings — Dynamics joins the integrated stage on its own clock

**Date:** 2026-11-05 · **Topic:** p53-mdm2 · **Cycle:** 012 (unattended) · **Type:** findings

## Headline

This cycle implements the PI's Q-019 answer (2026-11-04).

- **Join.** The job-119 Dynamics layer now enters `demos/p53_mdm2_integrated.usda` through a **reference with an identity layer offset**. The stage clock stays MaBoSS-only (frames 0–499), and the MD samples keep their own picosecond time codes (0–100). No relation between the two clocks is invented.
- **Alignment.** A **single rigid transform** places the trajectory in the 1YCR crystal frame. It is a Kabsch fit of frame 0 onto 98 CA atoms: RMSD **71.91 Å → 0.348 Å**. Raw frame coordinates are untouched.
- **Time units.** MaBoSS model time now carries an explicit, `[assumption]`-tagged unit: **1 unit = 1 hour**.
- **Literature.** A survey finds no reliable, accepted method for integrating MD time directly into a Boolean or MaBoSS network as of 2026. The accepted practice is sequential **parameter passing**.

**Suite: 96/96**, re-run by the coordinator after the merge (87 before, plus 9 new `integrated-dyn` rows).

## What landed

| Piece | Path | What it does |
|---|---|---|
| Reference arc | `demos/p53_mdm2_integrated.usda` | `prepend references = @../output/p53_mdm2_dynamics_job119.usda@</p53_MDM2_complex/dynamics>`, identity offset |
| Alignment | `composition/dynamics_alignment.py` (new) | Kabsch fit of frame-0 CA onto 1YCR CA. It authors one `xformOp:transform` on `dynamics/trajectory` and records the fit as `bio:md:alignment*` attributes |
| MaBoSS time unit | `maboss/run_maboss.py`, `analysis/p53_mdm2_analysis.usda` | One constant, written as `bio:maboss:timeUnit = hour`, `bio:maboss:secondsPerTimeUnit = 3600` and `bio:maboss:timeUnitStatus` (assumption) |
| MD time unit | Dynamics layer | `bio:md:timeCodeUnit = ps` composes through the reference |
| Converter by run | `converters/trajectory_to_usd.py` | Output names come from the run manifest or `--run-id`, and the library code no longer contains "119". Both layers rebuild byte-identical. This was cycle-011 verifier follow-up (b) |
| Roadmap leaf | `__roadmap__/p53-mdm2-v2/p7_md_trajectory_integration.md` | Added through `dirtree-rdm add` and `update … inprogress`; `validate` OK. This was follow-up (c) |
| Tests | `tests/test_dynamics_integration.py` (new) | 9 rows, described in the Evidence section |

## Design choices

| Choice | Why |
|---|---|
| A reference rather than a sublayer | A reference grafts one subtree, so the Dynamics root opinions and its time range stay out of the stage's layer stack. The clock relation then sits on a single arc you can inspect, with a deliberately identity offset |
| No scaling offset | The PI did not endorse making the clocks play together. MD time in ps and MaBoSS time in hours are about 15 orders of magnitude apart (1 h = 3.6 × 10¹⁵ ps), so any shared playback would be a visual convenience with no physical meaning |
| A guard on `timeCodesPerSecond` | The build refuses when the Dynamics layer and the stage disagree on `timeCodesPerSecond`. A probe shows USD silently rescales a referenced layer when they differ: doubling the rate moved the last sample from 100 to 200 |
| One transform on the frame-0 fit | This follows the PI's lean (Q-019.2). Later frames are not refitted, so internal motion stays visible relative to the crystal pose |
| 1 h per MaBoSS unit | The cfg time constants (0.3–5) read as 20 min to 5 h. The wild-type P(p53↑) first peaks at model time 5.7, and single-cell p53 pulses recur every 5–6 h (Geva-Zatorsky et al. 2006, doi:10.1038/msb4100068). The PhysiBoSS tutorial uses the same hour convention (doi:10.1093/bib/bbae509) |

## Evidence: oracles independent of the generator

- **CA correspondence.** The test rebuilds it from `1ycr.pdb` and `md.gro` with its own fixed-column parse. MD A 25–109 maps to 1YCR A 25–109, and MD B 17–29 maps to 1YCR B 17–29. Protonation names are folded (HIE→HIS).
- **Fit quality.** The authored matrix, applied to the composed frame-0 CA positions, gives RMSD ≤ 0.35 Å. It also matches an **independent Horn-quaternion optimum** to within 1e-3 Å (both 0.3482).
- **Clocks.** The stage reads frames 0–499. Composed MD samples read at ps 0…100 and equal the raw frames layer.
- **Untouched sources.** No other prim in the subtree carries an xformOp, and the Dynamics and frames layers are byte-unchanged.
- **Staleness and self-test.** Regenerated Analysis and integrated layers byte-compare with their committed copies. A falsification self-test checks that the new rows catch mutations.

## What the literature says (Q-019.1 (i))

A read-only sub-agent ran the survey with web search. Its answers to the PI's three points follow.

1. **No accepted direct method.** As of 2026 there is no reliable, accepted way to integrate all-atom MD time into a Boolean network. The established approach is **sequential coupling (parameter passing)**: the fast scale is condensed into an equilibrium or rate parameter and passed to the slow model. Its theory is set out in the heterogeneous multiscale method (E et al., Commun Comput Phys 2007). The closest applied analogue found feeds rates from a coarse-grained simulation into a small EGFR/SOS/Ras ODE model (bioRxiv 2024, doi:10.1101/2024.12.04.626844). It is not all-atom and not Boolean. `[unverified]` No paper was found that feeds all-atom MD or ΔΔG into MaBoSS. This absence comes from searches, not from a systematic review.
2. **Assigning time to MaBoSS.** MaBoSS itself names no unit; rates are "the inverse of the mean time" (Stoll et al. 2012, doi:10.1186/1752-0509-6-116). The modeller assigns one, and the PhysiBoSS tutorial uses hours. That supports the choice above.
3. **Your discrete-event intuition has a name.** It is **on-the-fly kinetic Monte Carlo**: a coarse event scheduler whose rates come from fine-scale simulation (Henkelman & Jónsson, JCP 2001, doi:10.1063/1.1415500). The catch is the separation of timescales. Binding and unbinding happen far faster than a MaBoSS step, so the coarse model only sees their equilibrium occupancy (a quasi-steady-state assumption). Our 100 ps run also cannot yield kon/koff. An MDM2–peptide Markov state model needed sampling on the sub-millisecond scale for that (Paul et al., Nat Commun 2017, doi:10.1038/s41467-017-01163-6). The defensible quantity to pass up is thermodynamic: ΔΔG → Kd fold change exp(ΔΔG/RT) → fraction bound → rate scaling. This is the shape the Pipeline 3 correlation already has.

**Defensible stance for the demo.** Present the link as one-way parameter passing (ΔΔG → MaBoSS rate), not as time integration. Use the MD run for structure and provenance only, and state the hour unit openly. All three are established practice.

## Uncertainty

- `[assumption]` The hour unit is a convention, not a calibration. The 5–6 h pulse period is a sanity anchor only: the population-level MaBoSS model is not fitted to it.
- `[assumption]` MD chain_A/B are matched to PDB chains A/B by order of appearance, confirmed by identical residue numbers and names.
- The 1:1 time mapping through the reference holds because the offset is identity and both layers use the same `timeCodesPerSecond`. It is a mechanical fact, not a scientific relation, and the guard enforces it.
- Not verified: how the result renders in usdview. Coordinates are stored to 0.01 Å.
- The P7 roadmap leaf is `inprogress`. Its Amendment Log and Progress rows are not updated, because dirtree-rdm has no command for them and they must not be hand-edited.
- The survey's references were checked by the sub-agent; the coordinator did not open each one.

## Steering

- **Q-020 (soft):** should cross-scale time integration become a **dedicated umbod topic**, separate from this technology demonstration? My recommendation is yes, and the question carries the proposed first research question.
