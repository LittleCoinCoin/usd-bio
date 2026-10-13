# Cycle-009 findings — the first p53-MDM2 MD run is built, but not run

**Date:** 2026-10-14 · **Topic:** p53-mdm2 · **Cycle:** 009 (unattended) · **Type:** findings

## Headline

The first real p53-MDM2 MD run from 1YCR is built, committed and tested: system build, four-stage protocol, the dgx1 job script, and read-back tests. **It has not executed.** The auto-mode classifier refused the cycle's first cluster write (`mkdir` + `scp` to the shared home, reason "Remote Shell Writes"), so nothing reached dgx1 and no job was submitted. Per INBOX 2026-09-25 item 5, the cycle stopped there and raised **Q-016**, which asks for an attended run and gives the exact commands. **Every execution to date is still the 2652-atom smoke box.**

## What landed

| Piece | Path | What it does |
|---|---|---|
| GROMACS `bio:md:` instance | `examples/p53_mdm2/output/p53_mdm2_md_setup_gromacs.usda` | The parameters of the run that will actually execute. It sublayers the topology, sets `metersPerUnit = 1e-10`, and puts per-stage overrides on `mdSetup/protocol/{em,nvt,npt,md}` |
| Schema extension | `examples/p53_mdm2/templates/md_parameters.py` | Adds 10 optional fields and 3 stage-only fields. The schema is extended, not forked, and the GENESIS-planned artifact rebuilds byte-identical |
| USD → deck emitter | `examples/p53_mdm2/templates/gromacs_deck.py` | Reads the **composed stage**, not the Python defaults, and writes `{em,nvt,npt,md}.mdp` + `prep.env`. Units are converted from each attribute's declared unit (Å→nm, atm→bar); an unknown unit is an error |
| Container script | `examples/p53_mdm2/cluster/p53_md/p53_md_run.sh` | Runs clean PDB → pdb2gmx → editconf → solvate → genion → stages. It holds no physics parameters of its own |
| Job script | `examples/p53_mdm2/cluster/p53_md/p53_md_submit.sbatch` | dgx1, 1 GPU, 8 threads, 30 min cap. Follows the `dgx1_gpu_smoke.sh` pattern: device from `SLURM_JOB_GPUS`, inputs bound read-only, `run_p53md_<UTC>/`, a sentinel, a `--- SUMMARY ---` block, and the GPU block for each stage |
| Tests | `tests/test_md_gromacs_deck.py` + fixture `templates/fixtures/md_setup_gromacs_reference.json` | 10 checks against a hand-written fixture. They cover the unit conversions (recomputed in the test), a staleness guard (committed mdp files byte-identical to a fresh emission), and that the scripts read the deck instead of inlining parameters. A mutation probe turned the relevant checks red |

**Suite: 63/63 pass** after the merge onto `topic/p53-mdm2` (re-run by the coordinator). The baseline was 53, not the 52 the 2026-08-12 INBOX recorded.

This closes the substance of p1b gate 3 (USD read-back reconstructs a runnable MD input) **at the deck level**: the mdp files are generated from the stage. It is not closed at the execution level, because no `gmx grompp` has accepted them yet.

## Protocol

| Stage | Setup | Length |
|---|---|---|
| EM | steepest descent to Fmax < 1000 kJ/mol/nm; `-nb gpu` only, because GPU PME does not support minimisers | ≤ 50 000 steps |
| NVT | heavy atoms restrained; velocities generated with seed 20261014 | 100 ps |
| NPT | restrained; C-rescale at 1.01325 bar; `refcoord-scaling = com` | 100 ps |
| Production | NPT, unrestrained | 100 ps |

All stages share: AMBER99SB-ILDN with TIP3P water; 310 K V-rescale; 2 fs timestep with LINCS on h-bonds; PME with 1.0 nm cutoffs; a dodecahedron box with 1.0 nm clearance; 0.15 M NaCl, neutralised. The expected wall time on one V100 is 3–5 min. That estimate assumes roughly 20 k atoms and has not been measured.

## Divergences from the planned deck (Q-017)

The container's GROMACS bundles **no ff14SB or ff19SB**. A read-only probe on 2026-10-14 found amber03/94/96/99, amber99sb, amber99sb-ildn, amberGS, charmm27, gromos* and oplsaa. The executed deck therefore departs from the cycle-003 GENESIS plan on:

- the force field: AMBER99SB-ILDN, not ff19SB;
- integration: 2 fs with no HMR, where the plan had 3.5 fs VRES with HMR;
- constraints: LINCS, not SHAKE;
- the production ensemble: NPT, not NVT;
- cutoffs: 10 Å, not 8 Å.

Every divergent value is tagged `[assumption: …]` in the USD. No force-field port was downloaded. **Q-017** puts the choice to the PI.

## Things the real run will settle (not yet known)

- **Untested against real `gmx`.** The pipeline was checked only by `bash -n`, shellcheck and a mock-`gmx` dry run. The most likely first failure is grompp at `maxwarn 0`, if "COM removal with position restraints" or the +3 net-charge message is a WARNING rather than a NOTE in 2025.3. The run would then stop cleanly at `grompp_<stage>`, and `GROMPP_MAXWARN=1` overrides it.
- **OXT on VAL A109 is placed by the script.** 1YCR lacks it. The script reflects C→O through the CA→C axis; checked locally, C–O comes out at 1.25 Å with angles near 120°. It is unknown whether the force field's C-terminus database would have rebuilt it.
- **Hand-counted expectations, not yet asserted:** net charge +3 before ions (chain A +5, chain B −2), 85 + 13 residues. The next cycle turns these into read-back checks against the captured evidence.

## Tooling observation

This is the third unattended cycle in which the classifier refused a cluster mutation (cycle-006 twice, now cycle-009). PI-authorisation text in INBOX or project files does not change its decision. Either every cluster step stays attended, or the PI adds a permission rule. Q-016 says so.

## Open questions this cycle

- **Q-016** (soft): run the job attended, and decide whether unattended staging and submission should be permitted.
- **Q-017** (soft): accept AMBER99SB-ILDN, add a vetted ff19SB/ff14SB, or treat this run as plumbing only.
