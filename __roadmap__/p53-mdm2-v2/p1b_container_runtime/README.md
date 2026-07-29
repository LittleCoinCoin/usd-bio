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
- ⬜ `[run]` `gromacs.sif` exists on `ts2:/export/home` (never on `/`) and `singularity inspect` reports `GromacsVer 2025.3` and `TargetSM 70;90` with **no** `BuildStatus` key
- ⬜ `[run]` GROMACS is observed executing on a real H100 — a non-zero `CUDA driver` version and a GPU-selection block in an `mdrun` log, captured verbatim
- ⬜ `[run]` `cuobjdump` output names **both** `sm_70` and `sm_90`, so the cross-cluster portability claim is observed rather than asserted
- ⬜ `[run]` the `.sif` and the Docker image agree on the GROMACS version, SIMD, CUDA runtime and GPU-support lines, and on minimisation energy to ≤ 1e-3 relative
- ⬜ `[static]` nothing in `examples/p53_mdm2/cluster/` still claims the container was never built, and no `BuildStatus` label survives in either recipe
- ⬜ `[run]` banyan's `/` returns to its pre-work free space; no `gromacs.tar` and no `gromacs-p53mdm2` image remain
- ⬜ `[static]` `Dockerfile`↔`gromacs.def` pin agreement is enforced by a test in `run_tests.py`, not by convention

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
    recipe_evidence_corrections[Recipe + Runbook Corrections]:::planned
    sass_portability_audit[CUDA SASS Portability Audit]:::planned
    docker_gpu_smoke[Docker GPU Smoke Test on banyan]:::planned
    sif_delivery[SIF Delivery]:::planned
    classDef done       fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned    fill:#374151,color:#e5e7eb
    classDef amendment  fill:#1e3a5f,color:#bfdbfe
    classDef blocked    fill:#7f1d1d,color:#fecaca
```

## Nodes
| Node | Type | Status |
|:-----|:-----|:-------|
| `recipe_evidence_corrections.md` | 📄 Leaf Task | ⬜ Planned |
| `sass_portability_audit.md` | 📄 Leaf Task | ⬜ Planned |
| `docker_gpu_smoke.md` | 📄 Leaf Task | ⬜ Planned |
| `sif_delivery/` | 📁 Directory | ⬜ Planned |

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
