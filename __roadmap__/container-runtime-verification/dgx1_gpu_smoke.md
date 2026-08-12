# dgx1 GPU Smoke Test

**Goal**: Observe a dgx1 V100 actually executing `gromacs.sif`, closing the gap between "the image opens and reads under dgx1's runtime" and "a dgx1 GPU has run it" — two facts cycle-007 warned must not be allowed to read as one.
**Pre-conditions**:
- [x] `gromacs.sif` on the shared home, digest `1fc04f8b…d20c81ac`, reachable from dgx1
- [x] The smoke system (`topol.top`, `min.mdp`, `md.mdp`, `make_box.sh`) staged under the shared home
- [x] dgx1 exposes GPUs through Slurm — GRES `gpu:nvidiav100sxm2:8`, partition `all`
- [x] An attended session, per Q-006, since this requests a device
**Success Gates**:
- ✅ `[run]` Captured `gmx --version` under `--nv` reports a **non-zero** `CUDA driver`, falsifying the driverless `0.0` that cycle-007 recorded without a device — observed `13.0`
- ✅ `[run]` The MD log carries the detected-GPU block naming a **compute capability 7.0** device as `compatible`, and a GPU selected for the run
- ✅ `[run]` The MD log carries a nonbonded GPU kernel line, showing nonbondeds ran on the device rather than falling back to CPU — `Using GPU 8x4 nonbonded short-range kernels`
- ✅ `[run]` `mdrun` exit status 0 recorded in the committed evidence
- ✅ `[run]` Minimisation potential energy agrees with the banyan H100 run of the **same** image to within one part in a thousand — observed relative difference `2.62e-06`
**References**: [R14 cycle-007 findings](../../__reports__/p53-mdm2/14-cycle007_findings_v0.md) — the proof-frontier ladder placing this at rung 5, and the warning that `inspect`/`exec` success is not GPU evidence; [R10 cluster state refresh](../../__reports__/p53-mdm2/10-cluster_state_refresh_v0.md) — the dgx1 GPU inventory the `sm_70` target must cover

## Step 1: Write the dgx1 smoke script
**Goal**: A repeatable single-GPU run of the identical smoke system, so any difference from the banyan result is attributable to the GPU architecture alone.
**Implementation Logic**:
Reuse the proven `convert_verify.sh` step-3 pattern rather than inventing one: resolve the device from `SLURM_JOB_GPUS` before falling back to `CUDA_VISIBLE_DEVICES`, which Slurm may rewrite to allocation-relative indices. Pin the OpenMP thread count to 8 rather than reading `SLURM_CPUS_PER_TASK`, because a 2652-atom system on 64 threads would be a different run from the banyan baseline it is compared against — like-for-like is the whole point. Emit a machine-parseable `--- SUMMARY ---` block with explicit keys so a test can assert over it without scraping prose. Capture the `md.log` GPU block verbatim, because a zero exit status is compatible with a silent CPU fallback.
**Deliverables**: `examples/p53_mdm2/cluster/dgx1_gpu_smoke.sh` — device resolution chain from `SLURM_JOB_GPUS`, `singularity exec --nv` with read-only template bind, pinned `SMOKE_NTOMP=8`, and a SUMMARY block carrying keys `CLUSTER`, `GPU_NAME`, `GPU_COMPUTE_CAP_NVIDIASMI`, `GPU_COMPUTE_CAP_MDLOG`, `SM_ARCH_EXERCISED`, `CUDA_DRIVER`, `CUDA_RUNTIME`, `GPUS_DETECTED`, `NONBONDED_ON_GPU`, `MDRUN_EXIT`, `DGX1_MIN_POTENTIAL_ENERGY`, `BANYAN_MIN_POTENTIAL_ENERGY`, `CROSSCLUSTER_ENERGY_REL`, `SIF_SHA256`
**Consistency Checks**: `bash -n examples/p53_mdm2/cluster/dgx1_gpu_smoke.sh` (expected: PASS)
**Commit**: `feat(p53-mdm2): dgx1 single-GPU smoke script for gromacs.sif`

## Step 2: Execute on dgx1 and capture verbatim
**Goal**: Run the script inside a real Slurm allocation and commit its output as evidence carrying provenance.
**Implementation Logic**:
Submit through the sanctioned `submit_job` route rather than a generic command runner, requesting one GPU via `gpus_per_node` so the agent emits `--gres=gpu:N` — dgx1 has no GPU-as-TRES, so `--gpus-per-node` would allocate nothing. Unlike the banyan docker path this genuinely runs inside the job's cgroup, so the allocation is real and worth recording as the pattern future MD runs should follow. Record a manifest line carrying the file digest, capture timestamp, cluster, command and the artifact digest read, so this capture can be distinguished from an edited copy later. Verify the evidence digest across the transfer rather than trusting the copy, since `fs_view` is known not to be byte-faithful.
**Deliverables**: `examples/p53_mdm2/cluster/evidence/dgx1_gpu_smoke.txt` — verbatim version block, GPU block, kernel timing rows, cross-cluster parity and the SUMMARY block; plus an appended `manifest.jsonl` entry
**Consistency Checks**: `git check-ignore -q examples/p53_mdm2/cluster/evidence/dgx1_gpu_smoke.txt` (expected: FAIL)
**Commit**: `docs(p53-mdm2): observed GROMACS executing on a dgx1 V100`

## Step 3: Gate the dgx1 GPU evidence in the test suite
**Goal**: Make the dgx1 GPU claims machine-checked offline so they cannot rot when a version or a device changes.
**Implementation Logic**:
Extend the existing `container-evidence` layer rather than adding a second one, keeping the harness contract intact: the module must return zero rows when `cluster/evidence/` is absent, and each family must go dark independently when only its own capture is missing. Assert the things that would actually break — a non-zero CUDA driver, the compute capability matching the architecture this cluster is supposed to exercise, nonbondeds on the device, and cross-cluster energy parity recomputed from the two recorded values rather than trusting the script's own verdict string. Deliberately do not assert wall-clock timings or step rates: they vary with node load and a flaky gate teaches people to ignore failures.
**Deliverables**: `examples/p53_mdm2/tests/test_container_evidence.py` — constant `_DGX1_GPU_SMOKE`, check `dgx1_gpu_executes` asserting driver, compute capability, nonbonded placement and `mdrun` exit; check `crosscluster_energy_parity` recomputing the relative difference against `_ENERGY_REL_TOL`
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/tests/run_tests.py` (expected: PASS)
**Commit**: `test(p53-mdm2): gate the observed dgx1 GPU execution`
