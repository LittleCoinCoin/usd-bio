# P7 MD Trajectory to USD + Integration

**Goal**: Bring the project's own GROMACS production trajectory (banyan job 119) into USD as a payloaded Dynamics layer, then join that layer to the integrated stage without inventing a relation between the MD and MaBoSS clocks, placing it in the 1YCR crystal frame with one rigid transform.
**Pre-conditions**:
- [x] Banyan job 119 (100 ps NPT production, GROMACS 2025.3) fetched with its manifest under `examples/p53_mdm2/data/md_runs/banyan_job119/` (commit 8be37e3)
- [x] PI Q-017: AMBER99SB-ILDN/TIP3P accepted for pipeline plumbing only
- [x] PI Q-019 (2026-11-04): Dynamics joins by reference with its own ps clock; the stage clock stays MaBoSS-only; no layer offset or scale relates them; an assumed MaBoSS time unit is recorded once, as data, tagged as an assumption; one Kabsch transform fitted on frame-0 CA onto 1YCR CA, raw frames untouched
**Success Gates**:
- ✅ `[run]` `output/p53_mdm2_dynamics_job119.usda` carries `bio:md:` run provenance and a Payload to a frames layer of time-sampled `Points` in Å with time codes in ps; `readback-traj` rows pass against `md.mdp`, `summary.txt`, `md.gro` and `manifest.jsonl`
- ✅ `[static]` `converters/trajectory_to_usd.py` derives output names and labels from the run manifest; library code names no job number; the committed layers rebuild byte-identical
- ✅ `[run]` `demos/p53_mdm2_integrated.usda` References the Dynamics `dynamics` subtree with an identity layer offset; the stage clock stays MaBoSS frames 0–499 at 10 TCPS; composed MD samples read back at ps 0–100, equal to the raw frames layer
- ✅ `[run]` Exactly one `xformOp:transform` on `dynamics/trajectory`; applying it to frame-0 CA gives ≤ 0.35 Å CA RMSD against 1YCR over a correspondence re-derived from `1ycr.pdb` and `md.gro`, within 1e-3 Å of an independent Horn optimum
- ✅ `[static]` `bio:maboss:timeUnit`, `bio:maboss:secondsPerTimeUnit` and `bio:maboss:timeUnitStatus` exist on the Analysis layer, documented as an assumption; `bio:md:timeCodeUnit = ps` composes through the reference
- ✅ `[run]` `tests/run_tests.py` reports 96/96, including the `integrated-dyn` staleness and self-falsification rows
**References**: [design vision §2.1 rows R and P](../../__design__/openusd_for_research_architecture.md) — References as standard assets, Payloads as raw data; [p53_mdm2 README](../../examples/p53_mdm2/README.md) — hop 1c and hop 5 rows, *Not yet done*

## Step 1: Payloaded Dynamics layer from the job-119 trajectory (cycle-011)
**Goal**: Give the campaign a real MD trajectory in USD, with the frames behind a Payload so the provenance opens without loading them.
**Implementation Logic**:
Read `md.xtc` against `md.gro` with mdtraj, keep the protein chains and ions, drop waters, and write positions in Å as time-sampled `Points` per chain, with time codes in ps. The run provenance lives in a light root layer and the frames in a separate layer brought in by a Payload, so `LoadNone` shows provenance and no frames. Value Clips are not used: 11 frames fit in one layer. The read-back oracles are the `.mdp` time grid, the `summary.txt` and `md.gro` counts, a separate fixed-column parse of `md.gro` for the final frame, and the manifest digests.
**Deliverables**: `examples/p53_mdm2/converters/trajectory_to_usd.py` — `convert()`, `write_frames_layer()`, `write_dynamics_layer()`; `examples/p53_mdm2/output/p53_mdm2_dynamics_job119.usda`, `examples/p53_mdm2/output/p53_mdm2_dynamics_job119_frames.usda`; `examples/p53_mdm2/tests/test_trajectory_readback.py` — `readback-traj` rows
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/tests/run_tests.py` (expected: PASS)
**Commit**: `feat(p53-mdm2): convert job-119 trajectory to a payloaded Dynamics layer` (1640598), `test(p53-mdm2): read back the Dynamics layer against independent oracles` (c1a6256)

## Step 2: Join Dynamics to the integrated stage (cycle-012)
**Goal**: Compose the Dynamics layer into the integrated stage per Q-019, with two independent clocks and one rigid transform into the crystal frame.
**Implementation Logic**:
Parameterise the converter by run (output names from the manifest job id, `--run-id`) so the library names no job. Record the assumed MaBoSS time unit (1 unit = 1 hour) once in `run_maboss` and author it on the Analysis layer as data tagged `[assumption]`. Join Dynamics through a Reference rather than a sublayer: a reference grafts one subtree, keeps the Dynamics root opinions and its ps range out of the layer stack, and puts the clock relation on a single arc whose layer offset is deliberately identity. Fail the build if the timeCodesPerSecond values differ, because USD would otherwise fold the ratio into the reference and silently rescale ps samples. Fit frame-0 CA onto 1YCR CA by chain and residue number, then author the fit as a single `xformOp:transform` on `dynamics/trajectory`.
**Deliverables**: `examples/p53_mdm2/composition/dynamics_alignment.py` — `fit_dynamics_to_topology()`, `kabsch()`, `correspondence()`, `Alignment.usd_matrix()`; `examples/p53_mdm2/demos/run_end_to_end.py` — `hop1c_dynamics()`, `dynamics_paths()`, `CLOCK_RELATION_ATTR`, `ALIGN_*_ATTR`; `examples/p53_mdm2/maboss/run_maboss.py` — `ASSUMED_TIME_UNIT`, `ASSUMED_SECONDS_PER_TIME_UNIT`, `ASSUMED_TIME_UNIT_STATUS`; `examples/p53_mdm2/tests/test_dynamics_integration.py` — `integrated-dyn` rows
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/tests/run_tests.py` (expected: PASS)
**Commit**: `refactor(p53-mdm2): derive trajectory output names from the run, not job119` (32bc626), `feat(p53-mdm2): record an assumed physical unit for MaBoSS model time` (3938500), `feat(p53-mdm2): join the Dynamics layer to the integrated stage by reference` (2360335), `test(p53-mdm2): read back the Dynamics join against independent oracles` (806a114)
