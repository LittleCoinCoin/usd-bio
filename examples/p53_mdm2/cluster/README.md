# p53-MDM2 — Containerized GROMACS on banyan / dgx1 (p1b Step 2 runbook)

**Purpose.** PI-facing runbook for running the project's own p53–MDM2 MD with
**GROMACS** (PI's engine choice, INBOX 2026-07-23) inside a portable container on
the two shared clusters.

> ## ✅ THE DOCKER IMAGE IS BUILT — THE `.sif` IS NOT
> **Slurm job 30 on banyan COMPLETED, exit 0, in 5m27s (2026-07-29).** It
> produced `gromacs-p53mdm2:latest` (image id `70659e395c53`, 10.6 GB),
> independently corroborated by the `/home/eliott/p53mdm2/BUILD_STATUS`
> sentinel (`stage=docker_build exit=0 finished=2026-07-29T23:31:29+09:00`).
> Full evidence: `__reports__/p53-mdm2/13-route_b_build_observed_v0.md` (R13).
>
> **Still true — do not read past this line as "done":** no `gromacs.sif`
> exists yet, no GPU has executed the container (the build-time gate reported
> `CUDA driver: 0.0` — no NVIDIA driver was present in the CPU-only build
> sandbox, which is expected there and proves nothing about GPU execution),
> the `sm_70`/`sm_90` SASS targets are independently under audit, and the
> build's own layers have not been cleaned up on banyan yet. Those four gaps
> are exactly the four sibling nodes under
> `__roadmap__/p53-mdm2-v2/p1b_container_runtime/`
> (`recipe_evidence_corrections` — this leaf; `sass_portability_audit`;
> `docker_gpu_smoke`; `sif_delivery`). Every remaining cluster-mutating action
> stays **PI-gated** and attended.
>
> ### The gate was tooling; it is resolved for attended sessions
> **Q-006 is answered.** Container builds — the mutating, shared-node-costly
> half — stay PI-attended by policy; other clean, engineering-justified work
> may be *attempted* unattended and escalated through the umbod question path
> rather than stalled; no blanket pre-allow rule was added. The build above is
> the proof the attended path works: two earlier unattended dispatches were
> **refused by Claude Code's auto-mode permission classifier**, which blocks
> cluster-mutating actions regardless of an authorization written into project
> files; the attended session that followed built the image on the first
> attempt. See topic **Q-006** (`__threads__/p53-mdm2/QUESTIONS.md`) for the
> full resolution.

## Files here

| File | What it is |
|---|---|
| `gromacs.def` | Singularity/Apptainer definition: GPU-enabled **GROMACS 2025.3** on a **CUDA 12.9.1 / Ubuntu 22.04** base, built for both V100 (sm_70) and H100 (sm_90). Every pin carries an inline source URL. Drives **Route A**, which is dead by observation (see below) — this file's `%post` has never itself been executed by `singularity build`, though its Docker twin has. |
| `Dockerfile` | **Route B** (the path that was actually used) build recipe — a *faithful translation* of `gromacs.def`: same base tag, same tarball URL, same md5 **and** sha256, same pinned CMake 4.0.3, same `GMX_*` flags. Single-stage, no `ENTRYPOINT`. ⚠️ **Parallel implementation of `gromacs.def` — the two must be kept in sync.** **Built 2026-07-29** — Slurm job 30, exit 0, `gromacs-p53mdm2:latest` (`70659e395c53`, 10.6 GB). See gated step 1 and R13. |
| `smoke_submit.sbatch` | Slurm template for a **1-GPU** smoke test (`gmx --version` on the GPU node + a trivial energy minimization) via `singularity exec --nv`. Not yet submitted — depends on `sif_delivery` producing a `.sif` first. |
| `README.md` | This runbook. |

## Why this shape (grounded in the live recon)

Cluster facts below are live-verified. The baseline is
`__reports__/p53-mdm2/07-cluster_liveverify_v1.md` (cycle-004), **refreshed and
partly corrected** by `__reports__/p53-mdm2/10-cluster_state_refresh_v0.md`
(cycle-006, commit `c8f2cc2`) — report 10 wins where they disagree. The engine
choice (GROMACS) is the PI's.

- **One shared NFS home** (`ts2:/export/home`, ~13 TB free) mounted identically on
  both clusters → **stage the `.sif` once, run on either cluster** (no re-upload).
  Confirmed still 13 TB free `[source: report 10 §5]`.
- **Singularity is the only portable, non-root, Slurm-integrated *run* path** across
  both machines. Docker works interactively on **banyan** (user in `docker` group,
  daemon 29.4.3 answering `[source: report 10 §3]`) but does **not** exist for this
  user on **dgx1**, and a raw `docker run` bypasses Slurm GPU isolation.
  `submit_job` wraps GPU jobs as `singularity exec --nv`. **Note the split:
  singularity is the run path; the *build* path is now Docker-on-banyan — see the
  fakeroot finding below.**
- **Different GPU generations** drive the CUDA choice:
  - **banyan** — 2× H100 NVL ~94 GB, **sm_90** (`compute_cap 9.0`), driver 595.71.05, singularity-ce 4.2.2, Slurm 22.05.2, CPU Xeon Gold 6530.
  - **dgx1** — 8× Tesla V100-16GB, **sm_70** (`compute_cap 7.0`), driver 580.159.03, singularity 3.5.2, Slurm 23.11.4, CPU Xeon Gold 6130.
  - Both `compute_cap` values are now read directly off `nvidia-smi` rather than
    inferred, confirming `GMX_CUDA_TARGET_SM="70;90"` `[source: report 10 §7]`.
- **No MD engine is installed on either cluster** — containerizing GROMACS is
  genuinely required. Still true: `gmx` is NOT FOUND on either host
  `[source: report 10 §8]`.
- **Outbound internet works from both clusters, no proxy** — the base-image pull
  and the GROMACS tarball fetch will succeed *on-cluster* (registry manifest and
  tarball URL both answer) `[source: report 10 §10]`.

### 🚫 `--fakeroot` is NOT available to this user — OBSERVED, not inferred

Report 07 asserted banyan "has singularity-ce 4.2.2 + fakeroot". The version half
is right; **the fakeroot half is wrong, and this is now settled by an attended
probe, not by inference.** `/etc/subuid` and `/etc/subgid` contain **no mapping
for this user on either cluster** — banyan has only `user` and `test`, dgx1 only
`lxd` and `root` `[source: report 10 §3]`. Unprivileged user namespaces are
otherwise enabled on banyan (`kernel.unprivileged_userns_clone = 1`), so the
constraint is specifically the **missing subuid/subgid range**, not a kernel
lockdown. This was a capability-vs-entitlement conflation: singularity 4.2.2
*supports* fakeroot; this *user* is not entitled to it.

`gromacs.def`'s `%post` runs `apt-get install` and compiles, i.e. it needs
root-in-container, i.e. `--fakeroot`. **`singularity build gromacs.sif
gromacs.def` (Route A) was run, attended, on 2026-07-29, and it failed in
seconds:**

```
$ singularity build gromacs.sif gromacs.def
FATAL:   --remote, --fakeroot, or the proot command are required to build
         this source as a non-root user
(exit 255)
```

That error names three ways out, and this session closed all three:
`--fakeroot` has no subuid range (above); `proot` is **absent** from banyan's
`PATH` (`command -v proot` found nothing); and `--remote` is declined on
principle — it would ship the recipe to a third-party cloud builder, a
different decision than a technical gap. **Route A is dead by observation.**
`[source: __reports__/p53-mdm2/13-route_b_build_observed_v0.md §7-8]`

**Route B is the live path, and it already succeeded** — see gated step 1,
now marked done.

*Podman is a lead, not a route.* banyan has `podman 3.4.4` reporting
`Rootless: true` `[source: report 10 §3]`, but **rootless podman builds normally
consume subuid ranges too**, and no build was attempted with it. Do not plan
around it until someone tries it.

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

### Verified vs assumed (upstream verification pass, cycle-006)

Every pinned value in `gromacs.def` now carries an inline source URL. **No
`[assumption]` remains** — the last one (`GMX_SIMD`) was resolved later in
cycle-006 and is written up below.

**Verified against upstream sources** (URLs are in `gromacs.def` next to each value):

| Item | Resolved value | Source |
|---|---|---|
| GROMACS version + tarball URL | `2025.3`, `https://ftp.gromacs.org/gromacs/gromacs-2025.3.tar.gz` (42 MB, 2025-08-29) | GROMACS 2025.3 download page + ftp index |
| Tarball checksum (official) | **md5** `5a2315b6f6e13b091bbbbfddee9eb62b` | GROMACS 2025.3 download page — GROMACS publishes **only** an md5, no sha256 anywhere |
| Tarball checksum (corroborated) | **sha256** `8bdfca02…c65` | Spack *and* EasyBuild recipes agree byte-for-byte; **not** vendor-published — flagged as such in the def. Both checks are active in `%post`. |
| Minimum CUDA for GROMACS 2025.3 | "CUDA toolkit version 12.1 or newer" | GROMACS 2025.3 install guide (12.9.1 clears it; note GROMACS' own CI only tests 12.1/12.5.1/12.6) |
| CUDA base image tag | `nvidia/cuda:12.9.1-devel-ubuntu22.04` **exists**, digest `sha256:bd4e2680…ba8`, updated 2025-07-25 | Docker Hub tag API (a newer `12.9.2-devel-ubuntu22.04` also exists) |
| `GMX_*` flag spellings | `GMX_GPU=CUDA`, `GMX_CUDA_TARGET_SM`/`_COMPUTE` (semicolon-delimited two-digit CCs), `GMX_MPI`, `GMX_DOUBLE`, `GMX_BUILD_OWN_FFTW`, `CUDA_TOOLKIT_ROOT_DIR` | GROMACS 2025.3 install guide |
| CUDA 13 drops Volta | Confirmed **twice**: NVIDIA's guidance is verbatim "remain on branch 580 … Remain on 12.9"; and nvcc 12.9.1's SM list has `sm_70`, while nvcc 13.0.0's list **starts at `sm_75`** | NVIDIA architecture-support blog (2025-08-04) + both toolkits' nvcc manuals |

**Two build-breakers found and fixed while verifying** (neither was previously flagged):

- **jammy's apt `cmake` is 3.22.1, but GROMACS 2025.3 requires ≥ 3.28.** The old
  recipe `apt-get install cmake` would have failed at configure time. `%post` now
  installs pinned **CMake 4.0.3** from Kitware's official binary tarball with
  Kitware's own published sha256, and no longer installs cmake from apt.
- **Ubuntu 22.04 vs 24.04 is a compiler decision.** GROMACS 2025.3 recommends
  "GCC … version 9.x to 11.x. Note: there are known issues with GCC 12 and
  newer." jammy gives gcc 11.x; noble gives gcc 13.2. So the 22.04 base is the
  *correct* choice and the CMake gap is the price paid for it — now documented in
  the def instead of implicit.

### ✅ `GMX_SIMD=AVX2_256` — RESOLVED, and the answer is "keep it"

This was the last `[assumption]`, and it is now **`[verified]`**. It is a genuinely
counter-intuitive resolution, so the reasoning is spelled out.

**Step 1 — the hardware (was missing, now recorded).** `[source: report 10 §4]`

| | banyan | dgx1 |
|---|---|---|
| CPU | Intel Xeon Gold **6530** (Emerald Rapids) | Intel Xeon Gold **6130** (Skylake-SP) |
| AVX-512 core set | `avx512f` `avx512dq` `avx512bw` `avx512vl` `avx512cd` | **same core set** |
| extras | VNNI, BF16, FP16, IFMA, VBMI, AMX | *(none)* |

**Both** CPUs support AVX-512. The naive least-common-denominator rule ("highest
level supported by both") therefore evaluates to `AVX_512`, and `AVX_512` **is** a
valid `GMX_SIMD` value for 2025.3 (the accepted list is `None`, `SSE2`, `SSE4.1`,
`AVX_128_FMA`, `AVX_256`, `AVX2_128`, `AVX2_256`, `AVX_512`, `AVX_512_KNL`,
`IBM_VSX`, `ARM_NEON_ASIMD`, `ARM_SVE`)
`[verified: https://manual.gromacs.org/documentation/2025.3/install-guide/index.html]`.

**Step 2 — but the GROMACS docs override the naive rule.** The 2025.3 install
guide's `AVX_512` entry says, verbatim:

> "With GPU accelerated runs `AVX2_256` can also be faster on high-end Skylake CPUs with both 512-bit FMA units enabled."

`[verified: GROMACS 2025.3 install guide, GMX_SIMD section, same URL]`

**Our runs are GPU-accelerated by construction** (`-DGMX_GPU=CUDA`,
`gmx mdrun -nb gpu`), and **dgx1 is exactly a high-end Skylake** — a Skylake-SP
Xeon Gold. That sentence is not a generic caveat; it describes this machine and
this workload.

**Step 3 — the conclusion is robust to the one fact we did not check.** The guide
also notes that AVX-512 is fastest "on the higher-end desktop and server
processors" while models such as "Xeon Bronze and Silver" have "only one AVX512
FMA unit and therefore on these processors `AVX2_256` is faster"
`[verified: same section]`. We did **not** verify the FMA-unit count of the Gold
6130 — and we do not need to, because **both branches point the same way**:

- if the 6130 has **one** FMA unit → the guide says `AVX2_256` *is* faster;
- if it has **two** → the GPU-accelerated sentence applies → `AVX2_256` *can be*
  faster.

There is no branch in which `AVX_512` is the documented choice for a
GPU-accelerated run on this CPU.

**Decision: keep `-DGMX_SIMD=AVX2_256`.** It is also trivially safe — "Present on
Intel Haswell (and later) processors (2013) and AMD Zen3 and later (2020)"
`[verified: same section]`, and both CPUs are far newer than Haswell, so there is
no illegal-instruction risk on either cluster. One `.sif`, runs on both, and it is
the flag the docs favour for a GPU run on Skylake-SP.

**What this does NOT claim.** No benchmark was run, on either CPU. banyan's
Emerald Rapids may well be faster with `AVX_512`
`[assumption: the GROMACS 2025.3 guide's AVX_512 caveats are written about
Skylake-X/SP and Zen4 and say nothing about Emerald Rapids either way; that later
Intel generations narrowed the AVX-512 downside is general industry lore I did not
verify against a citable source, and no benchmark was run here]`. So if CPU-side
PME ever becomes the bottleneck on banyan specifically, the escape hatch is a
**per-architecture build** (`-DGMX_BINARY_SUFFIX`, per the guide's own advice for
heterogeneous fleets) rather than raising the flag on the shared image. The
single-`.sif`, run-anywhere constraint is what pins this to one value.

Do **not** delete the flag and rely on CMake auto-detection: it detects the
*build host*, and one `.sif` on the shared NFS home runs on two different CPU
generations.

---

## ⛔ PI-gated mutating steps — IN ORDER (step 1 done)

Each step mutates a shared resource (the shared home or the scheduler) and needs
an explicit PI "yes". They are sequential — do not skip ahead.

1. **✅ Build the image → Docker image done; `.sif` conversion still pending.**
   *(writes a multi-GB `.sif` to shared home once conversion runs)*

   All `gromacs.def` values were resolved before the build — base-image tag,
   tarball URL, md5 + sha256, CMake version/hash, every `GMX_*` flag including
   `GMX_SIMD` — each with an inline source URL. **No blanks were left to fill.**

   - **Route B — Docker-first (SUCCEEDED, 2026-07-29).** On **banyan**, which has
     the Docker daemon (29.4.3) with this user in the `docker` group *and*
     singularity-ce 4.2.2 `[source: report 10 §3]`. **Slurm job 30 ran the three
     commands below, COMPLETED with exit 0 in 5m27s, and produced
     `gromacs-p53mdm2:latest` (image id `70659e395c53`, 10.6 GB):**
     ```
     docker build -t gromacs-p53mdm2 .          # uses ./Dockerfile
     docker save gromacs-p53mdm2 -o gromacs.tar
     singularity build gromacs.sif docker-archive://gromacs.tar
     ```
     The build-time gate reported a real, GPU-compiled binary: `GROMACS version:
     2025.3`, `Precision: mixed`, `GPU support: CUDA`, `SIMD instructions:
     AVX2_256`, `CUDA compiler: nvcc release 12.9, V12.9.86`, `CUDA runtime:
     12.90`, `CUDA driver: 0.0` (no NVIDIA driver in the CPU-only build sandbox —
     expected, not a fault). Both tarball integrity gates passed against the real
     fetched bytes, including the GROMACS sha256 that was previously only
     cross-corroborated between Spack and EasyBuild, never checked against the
     actual tarball. Full evidence:
     `__reports__/p53-mdm2/13-route_b_build_observed_v0.md` (R13).

     The **third `singularity build docker-archive://…` line above has not yet
     run** — the Docker image exists, the `.sif` does not. That conversion,
     verification and cleanup is `sif_delivery/convert_verify_cleanup`, a
     separate roadmap leaf.

     `./Dockerfile` is a **faithful translation** of `gromacs.def` — identical base
     image tag, GROMACS tarball URL, md5 **and** sha256 checks (md5 trusted first),
     pinned CMake 4.0.3 with Kitware's published sha256, and every `GMX_*` flag
     including `GMX_SIMD=AVX2_256` and `GMX_CUDA_TARGET_SM="70;90"`. It is
     deliberately **single-stage** (the `-devel` base is the final image), because
     the shared-library list a slimmer `-runtime` stage would need cannot be
     verified without an actual build; the reasoning is in the file's header.
     It sets **no `ENTRYPOINT`** — only a `CMD` — so `singularity exec --nv
     gromacs.sif gmx …` is never intercepted, and `gmx` is on `PATH` via `ENV`.

     > ### ⚠️ `Dockerfile` and `gromacs.def` are PARALLEL IMPLEMENTATIONS — keep them in sync
     > **Editing one without the other is the obvious failure mode:** the directory
     > then yields two different containers depending on which route is taken, and
     > nothing detects it until a run disagrees. Any change to a version, URL,
     > checksum, apt package, or `GMX_*` flag must land in **both files in the same
     > commit**. `gromacs.def` remains the source of truth for the pins and their
     > provenance; a divergence in `Dockerfile` is a bug in `Dockerfile`.

     **Why this was the recommendation, confirmed after the fact:** the Docker
     daemon builds as root, so the `apt-get` + compile steps worked without
     needing `--fakeroot` — which this user does not have (see "🚫 `--fakeroot`
     is NOT available" above). *Cost, stated honestly:* a `docker build` is
     unscheduled use of a shared node and `docker` group ≈ root on that box (the
     PI's own Q-003 caution).

     > **⚠️ "Off the GPUs" needs an explicit opt-out on banyan — it is not the
     > default.** banyan's Docker daemon has `Default Runtime: nvidia`, and the
     > `nvidia/cuda` base image sets `NVIDIA_VISIBLE_DEVICES=all`. Together, a
     > **plain `docker run` with no `--gpus` flag at all** still gets the host
     > driver injected and sees **both H100s** (`/dev/nvidia0`, `/dev/nvidia1`,
     > `/dev/nvidiactl` present; `nvidia-smi -L` lists both cards; the container
     > reports `CUDA driver: 13.20` against host driver 595.71.05). There is
     > effectively no such thing as a casually "CPU-only" `docker run` on banyan.
     > **`docker run -e NVIDIA_VISIBLE_DEVICES=void …` is what actually yields a
     > device-free container** (no `/dev/nvidia*`, no `libcuda.so.1`, `CUDA
     > driver: 0.0` — this is exactly the signature the build-time gate above
     > shows, because `docker build` does not inject GPU devices the way `docker
     > run` does). Given banyan GPU 0's known contention (report 10 §7), any
     > interactive `docker run` on this box should pass that flag explicitly
     > rather than relying on omission. `[observed 2026-07-29, sass_portability_audit leaf]`

   - **Route A — native `singularity build` (DEAD BY OBSERVATION).**
     `singularity build gromacs.sif gromacs.def` on banyan. This *was* the
     original recommendation; it was demoted, then **run attended on
     2026-07-29 and failed in seconds** with `FATAL: --remote, --fakeroot, or
     the proot command are required to build this source as a non-root user`
     (exit 255) — see "🚫 `--fakeroot` is NOT available" above for the full
     capture. All three of the error's named alternatives are closed: no
     subuid range, `proot` absent, `--remote` declined on principle. Only
     remaining option if Route A is wanted for real: **ask the admins for a
     subuid range**.

   **Pre-flight, on banyan, immediately before building — now with observed
   values instead of assumptions:**
   - **Free space held steady; the earlier drawdown looks like a one-off.**
     banyan's root disk fell from 586 G to 439 G free between 2026-07-21 and
     2026-07-27 `[source: report 10 §5]`, but then **held at 439 G free across
     four further days**, and the build itself only consumed ~9 G net
     `[source: R13 §6]`. This does not explain the original 147 G drop, but it
     means `/` was not still actively draining as of the build. `/tmp` remains
     confirmed on the same device as `/` (`/dev/nvme0n1p4`) — **this
     contradicts a facility doc's claim of a separate NVMe scratch device** —
     so the `TMPDIR`/`SINGULARITY_TMPDIR` redirection below stays warranted
     regardless of the one-off framing:
     ```
     df -h / /tmp /home                       # re-check RIGHT before building
     export SINGULARITY_TMPDIR=/home/eliott/p53mdm2/tmp
     export SINGULARITY_CACHEDIR=/home/eliott/p53mdm2/cache
     export TMPDIR=/home/eliott/p53mdm2/tmp   # also catches docker save's temp files
     mkdir -p "$SINGULARITY_TMPDIR" "$SINGULARITY_CACHEDIR"
     ```
     Write the `docker save` tarball to shared home too, and delete it once the
     `.sif` exists (still pending — see `sif_delivery/convert_verify_cleanup`).
   - **`TMPDIR` does NOT move `docker build`'s layer storage.** The redirection
     above catches `singularity build` and `docker save`, but a `docker build`
     writes its layers to the **daemon's** data-root, which the client cannot
     redirect. **This is now observed, not assumed:**
     ```
     $ docker info | grep -i 'Docker Root Dir'
     Docker Root Dir: /var/lib/docker
     ```
     `/var/lib/docker` sits on `/` and holds **213 G**, mostly other users'
     pre-existing images — not ours to prune. Only an admin can move the
     daemon's data-root; the client cannot redirect it. Clean-up (still
     pending):
     ```
     docker builder prune ; docker image rm gromacs-p53mdm2   # after the .sif exists
     ```
     `[source: __reports__/p53-mdm2/13-route_b_build_observed_v0.md §5]`
   - **Don't go looking for a CUDA 12.9 module.** banyan's module system tops out
     at `cuda/12.5.1` — there is no 12.9 module `[source: report 10 §8]`. This is
     **irrelevant** to the build: the container ships its own CUDA 12.9.1 from the
     base image. It only rules out a *host-side* 12.9 build. Noted so nobody
     wastes time hunting for it.

2. **⛔ Stage the `.sif` + a tiny test system into shared home.**
   `fs_mkdir /home/eliott/p53mdm2/{,smoke/in,smoke/out}` then `fs_upload` the
   `.sif` (and, if doing Step 2 of the smoke test, a tiny `conf.gro`/`topol.top`/`min.mdp`).
   *(If built on banyan — Route B or A — write the `.sif` straight to shared home
   and it is visible from dgx1 too: no upload needed, just the smoke-input dir.
   An upload is only needed for the off-cluster build option, sub-decision (b3).)*

3. **⛔ Submit the 1-GPU smoke test.** Edit the placeholders in
   `smoke_submit.sbatch` (SIF path, WORKDIR, partition/account if ever needed),
   then `submit_job` / `sbatch smoke_submit.sbatch`. Run it on **both** clusters
   in the end — one of them proves the stack, the other proves portability. Which
   goes first is now an open call: see sub-decision (c), and read the pre-flight
   below before choosing banyan. *(mutates shared Slurm + GPU state on a beta node)*

   **⚠️ Pre-flight on banyan: Slurm's view of the GPUs and reality diverge.**
   At the last refresh, **GPU 0 held another user's vLLM process consuming
   ~86 GB of 95.8 GB** while Slurm reported the node `IDLE` with an empty
   `AllocTRES` — the process is unscheduled, so Slurm does not know it is there
   `[source: report 10 §7]`. GPU 1 was fully free. A `--gres=gpu:1` job could
   therefore be handed a card with ~9.7 GB left and contend or OOM.
   - **Inspect `nvidia-smi` immediately before submitting** (occupancy is
     point-in-time and already changed once within 6 days):
     ```
     nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv
     sinfo -o '%T %C %G'          # compare Slurm's view against the above
     ```
   - **Prefer the free GPU.** If GPU 0 is still occupied, either target GPU 1
     explicitly (e.g. `CUDA_VISIBLE_DEVICES` inside the job, understanding that
     Slurm's GPU isolation here is soft), or smoke-test on **dgx1** instead —
     it was fully idle with 8 free V100s, and it is also the *harder* portability
     target (singularity 3.5.2), so going there first front-loads the real risk.
   - **Unresolved:** report 10 **could not determine whether Slurm actually hands
     out GPU 0.** No job was submitted to see which device it assigns, and it is
     unknown whether the site has any out-of-band GRES exclusion for GPU 0. Treat
     the `nvidia-smi` check as mandatory rather than assuming either way.

4. **⛔ (Downstream, NOT covered here) Build the real p53-MDM2 decks and run.**
   Solvation, ions, protonation, parameterization, and the production `.mdp`
   files for the actual 1YCR system are a **separate later step**. This directory
   only proves the *container + execution path*, not the science deck.

---

## Open sub-decisions the PI still needs to settle

- **(a) GROMACS exact version.** Scaffolded at **2025.3**. Note this is a
  deliberate pin, *not* "the newest" — **2025.4 and 2026.x now exist upstream**
  (both appear as released versions in the Spack and EasyBuild GROMACS recipes). Confirm 2025.3,
  bump, or pin to a specific 2024.x if reproducibility with an existing study is wanted.
- **(b) Which build route? — RESOLVED, Route B.** *(Was the gating technical
  question, filed as topic **Q-007**; now answered by observation.)*
  `--fakeroot` is unavailable and Route A's native `singularity build` has been
  attempted and observed to fail (see "🚫 `--fakeroot` is NOT available"
  above) — option 4 below has already happened. **Route B was used and
  succeeded** (gated step 1, job 30). The remaining options are recorded for
  completeness, not because the choice is still open:
  1. **Route B via banyan's Docker daemon** — used, succeeded. ~~Recommended~~ **Done.**
  2. **Ask the admins for an `/etc/subuid` range** — would unlock Route A
     properly; not pursued, since Route B already works.
  3. **Build off-cluster and upload the `.sif`** — not needed now that Route B
     has produced the image on-cluster.
  4. ~~Have an attended session try Route A once to settle the inference
     empirically before choosing.~~ **Done, 2026-07-29** — see the captured
     `FATAL` error above.
- **(c) Which cluster to smoke-test first.** Previously "banyan". Now genuinely
  open: banyan built the image and has the newer stack, **but its GPU 0 is
  contended by an unscheduled process** while dgx1 is fully idle *and* is the
  harder portability target (singularity 3.5.2). Arguments both ways — banyan
  first is the shorter path to a green result; dgx1 first finds the SIF-skew
  problem sooner, when it is cheapest to fix.
- **(d) Real simulation decks are downstream.** As in gated step 4 — out of scope here.

## Known risks (encoded honestly, not hidden)

- **GPU-generation portability.** Handled by CUDA 12.9 + `GMX_CUDA_TARGET_SM="70;90"`.
  If CUDA 13 is ever used, V100/dgx1 support is silently lost.
- **SIF version skew (flagged in report 07) — ownership moved, not resolved.**
  The `.sif` (once converted — still pending, see gated step 1) will be built
  under **singularity-ce 4.2.2** (banyan) but must also run under
  **singularity 3.5.2** (dgx1, a 2019 release). Newer squashfs compression
  (e.g. zstd) may not open on 3.5.2. This is no longer an open risk owned by
  this runbook: it is the explicit subject of
  `sif_delivery/crosscluster_readonly/dgx1_sif_open_check`, which computes the
  image digest from both clusters and attempts to open + exec the `.sif`
  under 3.5.2 read-only, without a GPU. That leaf's own success gate rewrites
  this entry again once it has run. Building on the older runtime remains
  harder regardless, because dgx1 has **neither** Docker access **nor**
  fakeroot for this user `[source: report 10 §3]` — hence banyan-first,
  dgx1-verify.
- **`docker` group ≈ root on a shared box.** Building with Docker on banyan is
  unscheduled use of a shared node. This risk is now **unavoidable on the
  recommended path** rather than something to route around — `--fakeroot` is
  gone, so the `singularity build` alternative is not available to prefer. Keep
  the Docker step short, off the GPUs, and clean up the saved tarball afterwards.
- **⚠️ Two build recipes for one image ⇒ drift risk.** `Dockerfile` (Route B) and
  `gromacs.def` (Route A) now describe the same container twice. Nothing in the
  repo enforces that they agree — no test builds either file. A pin bumped in one
  and not the other produces two silently different containers from one directory.
  **Mitigation is social:** change both in the same commit, and treat
  `gromacs.def` as the source of truth for pins and provenance.
- **✅ No fakeroot ⇒ Route A fails — RESOLVED to an observation.** Documented in
  full above, including the verbatim `FATAL` line. This is no longer a
  residual-inference risk: the attended probe ran on 2026-07-29 and confirmed
  it. The only way this reopens is an admin granting a subuid range, which
  would need to be re-checked (`grep -c '^eliott:' /etc/subuid /etc/subgid`)
  before assuming it still holds.
- **⚠️ banyan GPU 0 occupancy is invisible to Slurm.** ~86 GB held by another
  user's process while Slurm says `IDLE` `[source: report 10 §7]`. Mitigation is
  the `nvidia-smi` pre-flight in gated step 3. Whether Slurm actually assigns
  GPU 0 was not determined.
- **banyan root-disk drawdown — reframed as a one-off, not a trend.** 586 G →
  439 G free between 2026-07-21 and 2026-07-27 `[source: report 10 §5]`, but
  `/` then **held at 439 G free across four further days**, and the actual
  build only consumed ~9 G net `[source: R13 §6]`. The original 147 G drop's
  cause remains uninvestigated, so this is not a root-cause finding — only
  evidence that `/` was not still actively draining as of the build. `/tmp`
  is confirmed on the same device as `/` (`/dev/nvme0n1p4`), contradicting a
  facility doc's claim of separate NVMe scratch, so the
  `SINGULARITY_TMPDIR`/`TMPDIR` redirection in gated step 1 stays warranted
  regardless, plus a `df -h` immediately before any future build.
- **Point-in-time reads.** Group memberships, GPU occupancy and free space are all
  snapshots from 2026-07-27. The GPU fact already changed once within 6 days.
  Re-run report 10's "Re-observation Steps" before acting on any of them.

---
*Generated as prep scaffolding for p1b Step 2 (cycle-005). Not committed by the
generating agent; left for the orchestrator to review and commit.*
*cycle-006: upstream verification pass over `gromacs.def` — all pins but one
resolved to citable sources; two latent build-breakers (CMake floor, gcc range)
found and fixed. Still nothing built, uploaded, or submitted.*
*cycle-006 (later, this pass): reconciled against the read-only live state refresh
`__reports__/p53-mdm2/10-cluster_state_refresh_v0.md` (`c8f2cc2`) — the `--fakeroot`
claim was **corrected as false** and Route B promoted to recommended; the last
`[assumption]` (`GMX_SIMD`) **resolved to `[verified] AVX2_256`** against the
GROMACS 2025.3 install guide; GPU-contention and disk-space pre-flight checks
added. The build gate is now the async harness's permission classifier (Q-006),
not the PI's authorization, which was already given. Still nothing built,
uploaded, or submitted.*
*cycle-006 (later still): closed the gap that Route B named a `docker build` with
no `Dockerfile` present — `./Dockerfile` now exists as a faithful, single-stage
translation of `gromacs.def` (same pins, both checksums, all `GMX_*` flags, no
`ENTRYPOINT`), with the sync obligation between the two files written down here
and in both files. Shell syntax of every `RUN` body was checked with `sh -n`;
**no image was built** — nothing in this directory has been built, uploaded, or
submitted.*
*`__roadmap__/p53-mdm2-v2/p1b_container_runtime/recipe_evidence_corrections`,
Step 2 (2026-07-30): this runbook now describes a built image, not scaffolding.
An attended session on 2026-07-29 ran Route B end to end — Slurm job 30,
COMPLETED, exit 0, 5m27s, `gromacs-p53mdm2:latest` (`70659e395c53`, 10.6 GB) —
and separately ran the Route A probe that turned the `--fakeroot` finding from
inference into an observed `FATAL` error. Full evidence in
`__reports__/p53-mdm2/13-route_b_build_observed_v0.md` (R13). The docker
data-root, the disk-drawdown trend, and the SIF-version-skew risk are
corrected or reassigned above; the `BuildStatus` label/`%labels` entry is
removed from both recipe files in this leaf's Step 3, together with the
PTX-embedding and `libcuda.so.1` corrections below. **Still not built or run:**
`gromacs.sif` does not exist, no GPU has executed the container, and the
`sm_70`/`sm_90` SASS targets remain under independent audit
(`sass_portability_audit`).*
