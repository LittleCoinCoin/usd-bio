# p53-MDM2 — Containerized GROMACS on banyan / dgx1 (p1b Step 2 runbook)

**Purpose.** PI-facing runbook for running the project's own p53–MDM2 MD with
**GROMACS** (PI's engine choice, INBOX 2026-07-23) inside a portable container on
the two shared clusters.

> ## ⚠️ NOTHING HAS BEEN BUILT, UPLOADED, OR SUBMITTED
> Everything in this directory is **reviewable scaffolding**. No image has been
> built, no `.sif` exists, no file has been written to any cluster, and no job
> has been submitted. Every cluster-mutating action below is **PI-gated** and
> waits for an explicit "go". This session was unattended and the PI was not
> present (topic Q-003: cluster mutation is PI-gated per step).

## Files here

| File | What it is |
|---|---|
| `gromacs.def` | Singularity/Apptainer definition: GPU-enabled **GROMACS 2025.3** on a **CUDA 12.9** base, built for both V100 (sm_70) and H100 (sm_90). Not built. |
| `smoke_submit.sbatch` | Slurm template for a **1-GPU** smoke test (`gmx --version` on the GPU node + a trivial energy minimization) via `singularity exec --nv`. Not submitted. |
| `README.md` | This runbook. |

## Why this shape (grounded in the live recon)

All cluster facts below are from `__reports__/p53-mdm2/07-cluster_liveverify_v1.md`
(live-verified, cycle-004). The engine choice (GROMACS) is the PI's.

- **One shared NFS home** (`ts2:/export/home`, ~13 TB free) mounted identically on
  both clusters → **stage the `.sif` once, run on either cluster** (no re-upload).
- **Singularity is the only portable, non-root, Slurm-integrated run path** across
  both machines. Docker works interactively on **banyan** (user in `docker` group)
  but does **not** exist for this user on **dgx1**, and a raw `docker run` bypasses
  Slurm GPU isolation. `submit_job` wraps GPU jobs as `singularity exec --nv`.
- **Different GPU generations** drive the CUDA choice:
  - **banyan** — 2× H100 NVL ~94 GB, **sm_90**, driver 595.71.05, singularity-ce 4.2.2, Slurm 22.05.2.
  - **dgx1** — 8× Tesla V100-16GB, **sm_70**, driver 580.159.03, singularity 3.5.2, Slurm 23.11.4.
- **No MD engine is installed on either cluster** — containerizing GROMACS is genuinely required.

### The CUDA-version reasoning (the crux)

`CUDA 13.0` **removes** offline compilation for compute capability < 7.5 —
i.e. it drops **Volta / V100 (sm_70)**. NVIDIA's own guidance is to *"remain on
CUDA Toolkit 12.9 and NVIDIA Driver branch 580"* to keep Volta support
([verified — NVIDIA GPU-architecture-support guide; CUDA 12.8/12.9 release notes]).
**dgx1 is on driver branch 580 exactly.** CUDA 12.x also fully supports **sm_90
(H100)**. So **CUDA 12.9 is the single toolkit that covers BOTH clusters**, and the
image is built with `GMX_CUDA_TARGET_SM="70;90"`. Using CUDA 13 would silently
break the V100 path.
*Runtime note:* with `singularity --nv` the container ships the CUDA runtime and
the **host** driver is bind-mounted in; both host drivers (580, 595) are newer
than the 12.9 runtime, so they are forward-compatible.

**Verified vs assumed:** GROMACS 2025.3 as latest, the CUDA 12.1+ requirement,
the CUDA-13-drops-Volta fact, and the `GMX_*` build-flag names are **verified**
against GROMACS 2025.3 docs and NVIDIA docs. The exact `nvidia/cuda:12.9.1` patch
tag, the GROMACS source tarball URL/sha256, and `GMX_SIMD=AVX2_256` are tagged
`[assumption]` in `gromacs.def` and must be confirmed at build time.

---

## ⛔ PI-gated mutating steps — IN ORDER (none done)

Each step mutates a shared resource (the shared home or the scheduler) and needs
an explicit PI "yes". They are sequential — do not skip ahead.

1. **⛔ Build the image → `.sif`.** *(writes a multi-GB `.sif` to shared home)*
   - **Route A (recommended):** on **banyan** (has singularity-ce 4.2.2 + fakeroot + Docker):
     `singularity build gromacs.sif gromacs.def`
   - **Route B (Docker-first):** build an equivalent Docker image from the same
     base + `%post` steps, `docker save img -o gromacs.tar`, then
     `singularity build gromacs.sif docker-archive://gromacs.tar`.
   - Before building, fill in the `[assumption]`-tagged blanks in `gromacs.def`
     (CUDA patch tag, GROMACS tarball sha256).

2. **⛔ Stage the `.sif` + a tiny test system into shared home.**
   `fs_mkdir /home/eliott/p53mdm2/{,smoke/in,smoke/out}` then `fs_upload` the
   `.sif` (and, if doing Step 2 of the smoke test, a tiny `conf.gro`/`topol.top`/`min.mdp`).
   *(If built on banyan via Route A, the `.sif` is already on shared home and
   visible from dgx1 too — no upload needed, just the smoke-input dir.)*

3. **⛔ Submit the 1-GPU smoke test.** Edit the placeholders in
   `smoke_submit.sbatch` (SIF path, WORKDIR, partition/account if ever needed),
   then `submit_job` / `sbatch smoke_submit.sbatch`. **Recommend banyan first**
   (newer stack; it built the `.sif`), then repeat on dgx1 to prove portability.
   *(mutates shared Slurm + GPU state on a beta node)*

4. **⛔ (Downstream, NOT covered here) Build the real p53-MDM2 decks and run.**
   Solvation, ions, protonation, parameterization, and the production `.mdp`
   files for the actual 1YCR system are a **separate later step**. This directory
   only proves the *container + execution path*, not the science deck.

---

## Open sub-decisions the PI still needs to settle

- **(a) GROMACS exact version.** Scaffolded at **2025.3** (latest stable). Confirm,
  or pin to a specific 2024.x if reproducibility with an existing study is wanted.
- **(b) Build on banyan vs locally.** Recommend **banyan** — it has Docker *and*
  singularity 4.2.2 *and* fakeroot, so `singularity build gromacs.sif gromacs.def`
  runs directly and the output lands on shared home. Local build is possible but
  then needs an upload and a docker→sif conversion.
- **(c) Which cluster to smoke-test first.** Recommend **banyan** (H100, newer
  Slurm/singularity, it built the image). Then dgx1 to confirm portability.
- **(d) Real simulation decks are downstream.** As in gated step 4 — out of scope here.

## Known risks (encoded honestly, not hidden)

- **GPU-generation portability.** Handled by CUDA 12.9 + `GMX_CUDA_TARGET_SM="70;90"`.
  If CUDA 13 is ever used, V100/dgx1 support is silently lost.
- **SIF version skew (flagged in report 07).** The `.sif` is built under
  **singularity-ce 4.2.2** (banyan) but must also run under **singularity 3.5.2**
  (dgx1, a 2019 release). Newer squashfs compression (e.g. zstd) may not open on
  3.5.2. **Mitigation:** smoke-test on dgx1 explicitly (gated step 3); if the
  `.sif` fails to open there, either rebuild with an older-compatible compression
  or maintain a per-cluster build. Building on the older runtime is harder because
  dgx1 lacks Docker + fakeroot for this user — hence banyan-first, dgx1-verify.
- **`docker` group ≈ root on a shared box.** Building with Docker on banyan is
  unscheduled use of a shared node; prefer the `singularity build` route and keep
  any Docker step short and off the GPUs.

---
*Generated as prep scaffolding for p1b Step 2 (cycle-005). Not committed by the
generating agent; left for the orchestrator to review and commit.*
