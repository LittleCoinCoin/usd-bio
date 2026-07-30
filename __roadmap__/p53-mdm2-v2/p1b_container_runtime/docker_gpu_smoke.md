# Docker GPU Smoke Test on banyan

**Goal**: Prove the image actually executes GROMACS on a real H100 — a non-zero CUDA driver version and nonbonded work on the device — using a generated minimal water box inside a Slurm allocation, with the GPU index passed explicitly to the daemon.
**Pre-conditions**:
- [x] `docker --gpus` is genuinely available: the `nvidia` runtime is registered in `docker info` and `nvidia-container-runtime`, `nvidia-container-cli` and `nvidia-ctk` are all present on `/usr/bin`
- [ ] An `nvidia-smi` check immediately before submission shows a card with more than 80 GB free, since banyan's GPU 0 has repeatedly held another user's unscheduled process
- [x] `/home/eliott/p53mdm2/` staged with `tmp/` and `cache/` so no scratch lands on `/`
- [ ] An attended session, per Q-006
**Success Gates**:
- ✅ `[run]` Captured `gmx --version` reports a **non-zero** `CUDA driver` version, falsifying the build-time `CUDA driver: 0.0`
- ✅ `[run]` The MD log carries the detected-GPU block including compute capability 9.0 and a GPU selected for the run
- ✅ `[run]` The MD log carries a nonbonded GPU kernel timing entry, showing nonbondeds ran on the device rather than falling back to CPU
- ⬜ `[run]` `mdrun` exit status 0 recorded in the manifest
- ✅ `[static]` The submit script resolves the device from `SLURM_JOB_GPUS`, never from `CUDA_VISIBLE_DEVICES` alone
- ✅ `[run]` `docker ps -a` shows no container left behind on the shared node
**References**: [R10 cluster state refresh](../../../__reports__/p53-mdm2/10-cluster_state_refresh_v0.md) — GPU occupancy invisible to Slurm, and why an `nvidia-smi` pre-flight is mandatory; [R07 cluster live verification](../../../__reports__/p53-mdm2/07-cluster_liveverify_v1.md) — Slurm version and GRES conventions on banyan

## Step 1: Build the minimal water-box system
**Goal**: Create a tiny, self-contained GROMACS input set so the smoke test needs no external structure and no p53-MDM2 deck.
**Implementation Logic**:
No mdp, gro or top file exists anywhere in the repo, and the existing smoke template silently skips its own second phase because those inputs are absent — so this closes a pre-existing gap rather than only serving this leaf. GROMACS ships the SPC water coordinate file and the OPLS-AA force field inside its own share tree, so a box can be solvated with no network access and no external asset. Write two mdp files, not one: a steepest-descent minimisation as a grompp warm-up, and a short leap-frog MD run, because minimisation with GPU nonbondeds does not reliably emit the detected-GPU block and has documented GPU feature restrictions — the MD run is the one whose log actually proves device execution. Keep the box small enough that the whole thing runs in seconds on a shared node.
**Deliverables**: `examples/p53_mdm2/cluster/smoke_system/topol.top`, `min.mdp` (steep integrator, Verlet, PME), `md.mdp` (md integrator, short nsteps, PME) and `make_box.sh` (solvates from the bundled SPC coordinates, updates the molecule count)
**Consistency Checks**: `sh -n examples/p53_mdm2/cluster/smoke_system/make_box.sh` (expected: PASS)
**Commit**: `feat(p53-mdm2): minimal SPC water-box smoke system for GROMACS`

## Step 2: Write the Slurm-wrapped GPU job
**Goal**: Run the container against exactly the GPU Slurm allocated, and record honestly what that wrapping does and does not guarantee.
**Implementation Logic**:
Request one GPU through the GRES interface, since the TRES interface does not allocate GPUs on this cluster. Resolve the device index from the Slurm job GPU variable first, falling back to the step variable and only then to the CUDA visibility variable: Slurm can rewrite the visibility variable to allocation-relative indices, so a zero there means the first allocated card rather than global card zero, and passing that to the daemon risks landing on the contended GPU. The daemon executes the container outside the job's cgroup, so the wrapper buys reservation and courtesy but not isolation, and cancelling the job will not stop a running container — state that in the script's header rather than implying containment. Run the version query, then generate the box, then grompp and mdrun for minimisation, then for MD.
**Deliverables**: `examples/p53_mdm2/cluster/docker_gpu_smoke.sbatch` — GRES GPU request, `DEV` resolution chain from `SLURM_JOB_GPUS` through `SLURM_STEP_GPUS` to `CUDA_VISIBLE_DEVICES`, explicit device passthrough, and a header stating the no-isolation caveat
**Consistency Checks**: `grep -c SLURM_JOB_GPUS examples/p53_mdm2/cluster/docker_gpu_smoke.sbatch` (expected: PASS)
**Commit**: `feat(p53-mdm2): Slurm-wrapped docker GPU smoke job for banyan`

## Step 3: Submit and capture the evidence
**Goal**: Execute the job attended and commit its output as tracked, provenance-carrying evidence.
**Implementation Logic**:
Run the mandatory pre-flight first — free space and GPU occupancy are point-in-time and have already changed once within a week. Submit through the cluster job-submission tooling rather than the generic command runner, which is the sanctioned route and the one that worked for the build. Capture the version block and both run logs verbatim under the evidence directory, using a text extension because the ignore file swallows the log extension and would silently drop them. Append manifest lines carrying digest, timestamp, cluster, job id and command. Confirm no container is left running on the shared node afterwards.
**Deliverables**: `examples/p53_mdm2/cluster/evidence/docker_gpu_smoke_banyan.txt` and `docker_md.log.txt` — verbatim version block, grompp output and both run logs; plus appended `manifest.jsonl` entries carrying job id
**Consistency Checks**: `grep -c 'CUDA driver' examples/p53_mdm2/cluster/evidence/docker_gpu_smoke_banyan.txt` (expected: PASS)
**Commit**: `docs(p53-mdm2): captured GROMACS GPU execution on a banyan H100`

## Step 4: Extend the evidence gates to the GPU run
**Goal**: Make the GPU claims machine-checked rather than narrated.
**Implementation Logic**:
Add assertions to the existing container-evidence module for the facts that distinguish a real device run from a CPU fallback: a non-zero CUDA driver version, the detected-GPU block with the expected compute capability, a nonbonded GPU kernel timing entry, and a zero exit status in the manifest. The zero-rows-when-absent rule still applies, so these assertions must activate only when the GPU evidence files exist. Avoid asserting on wall-clock timings or energies here — those are not stable across runs and belong to the parity comparison later.
**Deliverables**: `examples/p53_mdm2/tests/test_container_evidence.py` — added checks `gpu_driver_nonzero`, `gpu_detected_block`, `gpu_nonbonded_kernel`, `mdrun_exit_zero`
**Consistency Checks**: `PYTHONPATH="$PYTHONPATH:$(pwd)/examples" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/tests/run_tests.py` (expected: PASS)
**Commit**: `test(p53-mdm2): gates over the docker GPU smoke evidence`

## Step 5: Point the existing smoke template at the real inputs
**Goal**: Remove the template's placeholder assumption now that a real minimal system exists, so its second phase stops silently skipping.
**Implementation Logic**:
The existing submit template conditions its GROMACS phase on three input files existing and otherwise prints a skip, with a note explaining that preparing even a tiny system is its own task. That task is now done, so name the real files, drop the placeholder note, and fill the image and workdir placeholders. Also record the device-variable finding in its pre-flight comments so the next operator does not repeat the relative-index mistake. This step deliberately does not run the template — it is the Singularity-side path and is exercised in the delivery leaf.
**Deliverables**: `examples/p53_mdm2/cluster/smoke_submit.sbatch` — status header updated, real `smoke_system/` filenames substituted for placeholders, image and workdir paths filled, device-variable caveat recorded
**Consistency Checks**: `grep -c PLACEHOLDER examples/p53_mdm2/cluster/smoke_submit.sbatch` (expected: FAIL)
**Commit**: `docs(p53-mdm2): smoke template names the real staged water box`
