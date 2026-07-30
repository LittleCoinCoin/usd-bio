# P1b Container Runtime Validation

## Context
This node is the decomposition of `p1b_md_parameter_representation` **Step 2** — the containerized MD execution half of the MD-parameter track. It consumes the GROMACS Docker image built on banyan on 2026-07-29 (Slurm job 30, exit 0, 5m27s, 10.6 GB, image id `70659e395c53`) and produces the `gromacs.sif` that every later MD run on either cluster will execute, together with the observed evidence that the image actually computes on a GPU and carries CUDA code for both cluster architectures. It is the first work in this campaign to put a real artifact on a shared cluster; everything before it was representation and scaffolding.

## Reference Documents
- [R07 cluster live verification](../../../__reports__/p53-mdm2/07-cluster_liveverify_v1.md) — first live recon; superseded on fakeroot and disk by R10
- [R10 cluster state refresh](../../../__reports__/p53-mdm2/10-cluster_state_refresh_v0.md) — CPU models behind `GMX_SIMD`, GPU occupancy, the missing subuid mapping that killed Route A

## Goal
Turn the built-but-unproven GROMACS Docker image into a verified, portable `gromacs.sif` on the shared NFS home, with every claim about it observed rather than asserted, and leave the shared node no dirtier than we found it.

## Pre-conditions
- [x] Q-006 answered: container builds stay PI-attended; read-only cluster work is unattended-safe
- [x] Q-007 answered: Route B confirmed by observation — Route A dead (no `/etc/subuid` mapping, `proot` absent)
- [x] Docker image `gromacs-p53mdm2:latest` exists on banyan and reports `GROMACS 2025.3`, `GPU support: CUDA`, `SIMD: AVX2_256`, CUDA runtime 12.90
- [x] `docker run --gpus` is actually available on banyan: `nvidia` runtime registered in `docker info`; `nvidia-container-runtime`, `nvidia-container-cli`, `nvidia-ctk` all present on `/usr/bin`
- [x] `gromacs.def` and `Dockerfile` staged on banyan at `/home/eliott/p53mdm2/`, sha256-matched against the repo
- [ ] An attended session is available for every cluster-mutating step

## Success Gates
- ✅ `[run]` `gromacs.sif` exists on `ts2:/export/home` (never on `/`) and `singularity inspect` reports `GromacsVer 2025.3` and `TargetSM 70;90` with **no** `BuildStatus` key — job 33, sha256 `1fc04f8b…81ac`, 5750255616 bytes
- ✅ `[run]` GROMACS is observed executing on a real H100 — `CUDA driver: 13.20` (was `0.0` at build) plus `Number of GPUs detected: 1` / `compute cap.: 9.0` / `1 GPU selected for this run`, captured verbatim in job 32 and again under `--nv` in job 33
- ✅ `[run]` `cuobjdump` output names **both** `sm_70` and `sm_90` — `SM_ELF=sm_70;sm_90`, real SASS not PTX-only, so cross-cluster portability is observed
- ✅ `[run]` the `.sif` and the Docker image agree on version/SIMD/CUDA-runtime/GPU-support and on minimisation energy — relative difference **1.39e-06**, three orders inside the 1e-3 tolerance
- ✅ `[static]` nothing in `examples/p53_mdm2/cluster/` still claims the container was never built, and the `SCAFFOLDING-not-built` value survives in neither recipe
- ⬜ `[run]` **Reworded, and the original is recorded as NOT met.** The original gate demanded that banyan's `/` return to its pre-work free space. It did not: `/` held at 430 G. Deleting the image moved ~10 GB from active to *reclaimable* (169.7 → 179.9 GB), but releasing it needs `docker image prune`, which would delete other users' dangling images across a store holding 52 of them — out of scope for this project. What IS achieved and verifiable: `gromacs.tar` deleted (9.9 GB off shared home), no `gromacs-p53mdm2` image rows remain, build cache pruned. Reclaiming the dangling layers is an admin/owner action.
- ✅ `[static]` `Dockerfile`↔`gromacs.def` pin agreement is enforced by a test in `run_tests.py`, not by convention

## Gotchas
- **`docker build` and `docker run` are executed by the daemon, outside the job's cgroup.** Wrapping them in Slurm buys reservation and courtesy — it does **not** buy resource isolation, and `cancel_job` will not stop a running build. Say so plainly in any leaf that uses this pattern rather than implying containment.
- **Resolve the GPU index from `SLURM_JOB_GPUS`, not `CUDA_VISIBLE_DEVICES`.** Slurm can rewrite `CUDA_VISIBLE_DEVICES` to allocation-relative indices, so `0` means "your first GPU", not global GPU 0. banyan's GPU 0 has repeatedly held another user's ~86 GB process that Slurm cannot see, so passing a relative index to `docker --gpus device=N` risks landing on exactly the contended card.
- **Energy minimisation is a weak GPU proof.** `integrator = steep` with `-nb gpu` will not reliably emit the GPU-selection block. Gate GPU claims on a short `integrator = md` run, whose log prints the detected-GPU block and per-kernel GPU timings.
- **Order is load-bearing, twice.** The SASS audit must precede conversion, because a wrong-SASS image has to be rebuilt and that would discard any GPU evidence captured first. And the recipe corrections must land before the rebuild, because deleting the `BuildStatus` label edits the `Dockerfile` above every expensive `RUN` — forcing a rebuild anyway, which is then worth turning into a build-reproducibility datum.
- **The last step of `convert_verify_cleanup` is irreversible.** Once the tar is deleted and the image pruned, its earlier steps cannot be re-run. The step ordering *is* the safety mechanism.
- **Why the three depth-1 leaves are siblings, not a chain.** `recipe_evidence_corrections` is repo-only, `sass_portability_audit` is CPU-only in a plain container, `docker_gpu_smoke` needs Slurm and a GPU. They share no files, need different permissions, and fail in unrelated ways — genuine parallelism. `sif_delivery/` is the gate that consumes all three, which is why it is nested rather than a fourth sibling.

## Status
```mermaid
graph TD
    recipe_evidence_corrections[Recipe + Runbook Corrections]:::done
    sass_portability_audit[CUDA SASS Portability Audit]:::inprogress
    docker_gpu_smoke[Docker GPU Smoke Test on banyan]:::inprogress
    sif_delivery[SIF Delivery]:::inprogress
    classDef done       fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned    fill:#374151,color:#e5e7eb
    classDef amendment  fill:#1e3a5f,color:#bfdbfe
    classDef blocked    fill:#7f1d1d,color:#fecaca
```

## Nodes
| Node | Type | Status |
|:-----|:-----|:-------|
| `recipe_evidence_corrections.md` | 📄 Leaf Task | ✅ Done |
| `sass_portability_audit.md` | 📄 Leaf Task | 🔄 In Progress |
| `docker_gpu_smoke.md` | 📄 Leaf Task | 🔄 In Progress |
| `sif_delivery/` | 📁 Directory | 🔄 In Progress |

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
| `recipe_evidence_corrections.md` | task/p53-mdm2-container-runtime | 3 | `2e20cbf` R13 observation, `6a4407c` runbook, `34595c9` recipe twins; merged `--no-ff` at `4df8da3` after rebase. `BuildStatus` label deleted from both recipes so it cannot reach the `.sif`. Also corrected the false PTX-for-90-only claim, resolved the `libcuda.so.1` DT_NEEDED assumption against real `readelf` output, and recorded banyan's `Default Runtime: nvidia`. 39/39 suite. |
| `sass_portability_audit.md` | task/p53-mdm2-container-runtime | 2 | `d828f9c` audit script, `56536f2` captured evidence. Steps 1–2 done: `SM_ELF=sm_70;sm_90` both present as real SASS, `LIBCUDA_DT_NEEDED=no`, evidence byte-verified against the cluster (`ca3902cf`). Step 3 (the `container-evidence` test layer) still open. |
| `docker_gpu_smoke.md` | task/p53-mdm2-container-runtime | 3 | `3247a9b` smoke system, `33641d4` Slurm-wrapped job, `77b4d71` captured evidence. Steps 1–3 done: job 32 exit 0, `CUDA driver: 13.20`, H100 detected at compute cap 9.0, ~76% of wall time in GPU activities. Job **31 failed first** — a `SOL 0` placeholder made `solvate` append a second molecule block, `grompp` segfaulted and dumped 1.4 GB of core onto shared home; four fixes landed. Steps 4–5 (test gates, smoke_submit update) still open. |
