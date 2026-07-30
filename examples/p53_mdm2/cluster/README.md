# p53-MDM2 — Containerized GROMACS on banyan / dgx1 (p1b Step 2 runbook)

**Purpose.** PI-facing runbook for running the project's own p53–MDM2 MD with
**GROMACS** (PI's engine choice, INBOX 2026-07-23) inside a portable container on
the two shared clusters.

> ## ✅ THE `.sif` IS DELIVERED, HAS RUN ON AN H100, AND OPENS ON dgx1
> **Slurm job 30 on banyan COMPLETED, exit 0, in 5m27s (2026-07-29).** It
> produced `gromacs-p53mdm2:latest` (image id `70659e395c53`, 10.6 GB),
> independently corroborated by the `/home/eliott/p53mdm2/BUILD_STATUS`
> sentinel (`stage=docker_build exit=0 finished=2026-07-29T23:31:29+09:00`).
> Full evidence: `__reports__/p53-mdm2/13-route_b_build_observed_v0.md` (R13).
>
> **Two further attended jobs then closed the gaps this banner used to list.**
> **Job 32** (COMPLETED, exit 0, 6s, 2026-07-30) ran `gmx` on a real **H100 NVL**
> through banyan's Docker daemon: `CUDA driver: 13.20`, `Number of GPUs
> detected: 1`, PME and the nonbonded kernels both on device
> `[source: evidence/docker_gpu_smoke_banyan.txt]`. **Job 33** (COMPLETED,
> exit 0, 17m03s, finished 2026-07-31 01:42 JST) delivered
> **`/home/eliott/p53mdm2/gromacs.sif`** — 5750255616 bytes, sha256
> `1fc04f8b…d20c81ac` — to the shared home, re-ran the identical smoke system
> through `singularity exec --nv` on the same H100, and gated docker-vs-`.sif`
> parity at a relative minimisation-energy difference of **1.39e-06**; `inspect`
> on the delivered artifact carries `GromacsVer 2025.3`, `TargetSM 70;90` and
> **no** `BuildStatus` key `[source: evidence/convert_verify_banyan.txt]`. The
> SASS audit has also run — `SM_ELF=sm_70;sm_90`, 98 ELF records, re-checked
> byte-identically against the rebuilt image
> `[source: evidence/sass_audit_banyan.txt]`. And the image is **observed to
> open and exec under dgx1's singularity 3.5.2**, read-only and without a GPU
> `[source: evidence/dgx1_sif_open.txt, commit a46515b]`.
>
> **Still true — do not read past this line as "everything is done":**
> - **No dgx1 GPU has run this image.** Every GPU observation above is
>   banyan/H100 (`sm_90`). The V100 (`sm_70`) path has been compiled and
>   inspected, never executed; the cross-cluster check that did run took no
>   `--nv` flag and requested no device *by construction*. A dgx1 GPU run
>   stays **PI-attended** under Q-006.
> - **Build reproducibility is NOT established.** Job 33's equivalence check
>   ran against a **cached** compile layer (`#7 CACHED`, `#8 CACHED`), so what
>   it proves is that removing the `BuildStatus` label altered no compiled
>   content — *not* that the build reproduces from a cold cache
>   `[source: evidence/convert_verify_banyan.txt "STEP 1a"; evidence/manifest.jsonl seq 3 caveat]`.
> - **The build scratch is only partly reclaimed.** The 9.9 GB archive is gone
>   from shared home, no `gromacs-p53mdm2` image rows remain and the builder
>   cache is pruned — but `/` **did not** return to its pre-work free space
>   (430 G before, 430 G after). Releasing the last ~10 GB, now merely
>   *reclaimable*, needs `docker image prune`, which would delete other users'
>   dangling images from a store holding 52 of them. Left undone deliberately
>   `[source: evidence/convert_verify_banyan.txt "STEP 5 CLEANUP"]`.
>
> The open steps live under `__roadmap__/p53-mdm2-v2/p1b_container_runtime/`.
> Every remaining cluster-mutating action stays **PI-gated** and attended.
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
| `smoke_submit.sbatch` | Slurm template for a **1-GPU** smoke test (`gmx --version` on the GPU node + a trivial energy minimization) via `singularity exec --nv`. **Still never submitted** — the `.sif` it needs now exists, and the banyan-side equivalent was performed inside job 33's own script (`convert_verify.sh`, step 3), so this template's remaining use is the **dgx1** run, which is PI-attended. |
| `README.md` | This runbook. |

## Why this shape (grounded in the live recon)

Cluster facts below are live-verified. The baseline is
`__reports__/p53-mdm2/07-cluster_liveverify_v1.md` (cycle-004), **refreshed and
partly corrected** by `__reports__/p53-mdm2/10-cluster_state_refresh_v0.md`
(cycle-006, commit `c8f2cc2`) — report 10 wins where they disagree. The engine
choice (GROMACS) is the PI's.

- **One shared NFS home** (`ts2:/export/home`, ~13 TB free) mounted identically on
  both clusters → **stage the `.sif` once, run on either cluster** (no re-upload).
  Confirmed still 13 TB free `[source: report 10 §5]`. **This is no longer an
  inference from matching `df` output.** Both hosts are observed mounting the same
  NFSv4 export `ts2:/export/home` from the same server address `10.5.1.206` at the
  same target `/home`, and `sha256sum` of the staged `gromacs.sif` computed *on
  banyan* and again *on dgx1* returns the identical
  `1fc04f8b48a87f7e0cce4c4b1f3ae7ea5cd640b55c22586c115ce3bed20c81ac` at the
  identical size 5750255616 — the same digest recorded at delivery time. Stage-once-
  run-anywhere is therefore byte-proven for this artifact, not argued from free
  space `[source: evidence/dgx1_sif_open.txt, commit a46515b]`.
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

1. **✅ Build the image → done, converted to `gromacs.sif`, and verified on a GPU.**
   *(wrote a 5.75 GB `.sif` to shared home; job 33, 2026-07-31)*

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

     The **third `singularity build docker-archive://…` line above has since
     run too.** An attended **job 33** (COMPLETED, exit 0, 17m03s, finished
     2026-07-31 01:42 JST) rebuilt from the corrected recipe, saved a
     10593997824-byte archive to shared home, converted it, and delivered
     `/home/eliott/p53mdm2/gromacs.sif` — **5750255616 bytes, sha256
     `1fc04f8b48a87f7e0cce4c4b1f3ae7ea5cd640b55c22586c115ce3bed20c81ac`**.
     `singularity inspect` on the delivered artifact reports `GromacsVer:
     2025.3`, `TargetSM: 70;90` and **no** `BuildStatus` key, so the recipe
     correction reached the artifact; the same smoke system re-run through
     `singularity exec --nv` detected one **H100 NVL (compute cap 9.0)** and
     agreed with the Docker run's minimisation potential energy to
     **1.39e-06** relative (gate tolerance 1e-3)
     `[source: evidence/convert_verify_banyan.txt]`. Conversion from a
     `docker-archive://` executes no `%post`, which is why it needed neither
     root nor `--fakeroot`.

     **Two things that job did NOT establish — do not upgrade them when
     citing it:**
     - *Not a cold-cache reproduction.* The rebuild's equivalence check
       (SASS summary and version block identical to the pre-correction
       capture) ran with `#7 CACHED` and `#8 CACHED`, i.e. the expensive
       compile layer was reused. It proves the `BuildStatus` removal altered
       no compiled content; it does **not** show the build reproduces from a
       clean cache, and that gate of `convert_verify_cleanup` stays open
       `[source: evidence/convert_verify_banyan.txt "STEP 1a";
       evidence/manifest.jsonl seq 3 caveat]`.
     - *Cleanup is partial.* See the `docker builder prune` note below —
       `/` did not return to its pre-work free space and that gate is
       recorded as not met rather than ticked.

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
     `.sif` exists. **Job 33 did exactly this:** pre-flight showed 430 G free on
     `/` and 13 T on `/home`, the 9.9 GB tarball went to shared home, and it was
     removed after the `.sif` verified (`tar present: no`)
     `[source: evidence/convert_verify_banyan.txt]`.
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
     daemon's data-root; the client cannot redirect it. Clean-up, **run at the
     end of job 33**:
     ```
     docker builder prune ; docker image rm gromacs-p53mdm2   # after the .sif exists
     ```
     `[source: __reports__/p53-mdm2/13-route_b_build_observed_v0.md §5]`

     > **⚠️ The clean-up gate is NOT met, and was reworded rather than ticked.**
     > What did happen: the archive was deleted, `gromacs-p53mdm2:latest` was
     > untagged and its image `2846bd6447df` deleted, the builder cache went
     > from 16.46 GB with 34.3 kB reclaimable to 0 B reclaimable, and no
     > `gromacs-p53mdm2` rows remain. What did **not** happen: `/` free space
     > moved not at all — **430 G before, 430 G after** — because deleting the
     > image only shifted ~10 GB from *active* to *reclaimable* (image store
     > 213.3 GB with 169.7 GB → 179.9 GB reclaimable, 53 → 52 images).
     > Releasing it needs `docker image prune`, which on this shared daemon
     > would take **other users' dangling images**, so it was deliberately not
     > run. Treat "the node is as clean as we found it" as **false**: ~10 GB of
     > our layers is still resident, awaiting either an admin or a
     > sufficiently narrow prune `[source: evidence/convert_verify_banyan.txt
     > "STEP 5 CLEANUP"]`.
   - **Don't go looking for a CUDA 12.9 module.** banyan's module system tops out
     at `cuda/12.5.1` — there is no 12.9 module `[source: report 10 §8]`. This is
     **irrelevant** to the build: the container ships its own CUDA 12.9.1 from the
     base image. It only rules out a *host-side* 12.9 build. Noted so nobody
     wastes time hunting for it.

2. **✅ Stage the `.sif` + a tiny test system into shared home — done, no upload
   needed.** Job 33 wrote the `.sif` straight to `/home/eliott/p53mdm2/` on the
   shared home, and the smoke system (`smoke_system/make_box.sh` → 884 solvated
   molecules, 2652 atoms, with `min.mdp`/`md.mdp`/`topol.top`) was built and run
   there `[source: evidence/convert_verify_banyan.txt]`. Because banyan and dgx1
   mount the same export, **the artifact is already visible from dgx1** — and that
   is now byte-proven rather than assumed (see the shared-NFS bullet above, and
   `evidence/dgx1_sif_open.txt`). `fs_upload` is only relevant to the off-cluster
   build option, sub-decision (b3), which was not taken.

3. **◐ Submit the 1-GPU smoke test — banyan half DONE, dgx1 half ⛔ still gated.**
   The banyan half happened twice, both attended and both exit 0: job 32 under
   Docker and job 33's step 3 under `singularity exec --nv`, each detecting one
   H100 NVL at compute cap 9.0 with PME on device
   `[source: evidence/docker_gpu_smoke_banyan.txt, evidence/convert_verify_banyan.txt]`.
   **The dgx1 half has not run and is the remaining portability evidence.** What
   exists for dgx1 is read-only: `inspect` and `exec` both exit 0 under
   singularity 3.5.2, which proves the image *opens and reads* there but takes no
   `--nv` and requests no device `[source: evidence/dgx1_sif_open.txt]`. To do it:
   edit the placeholders in `smoke_submit.sbatch` (SIF path, WORKDIR,
   partition/account if ever needed), then `submit_job` / `sbatch
   smoke_submit.sbatch` on dgx1. *(mutates shared Slurm + GPU state; PI-attended
   per Q-006)*

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
   - **Resolved, and the answer is the unwelcome one: Slurm DOES hand out GPU 0.**
     Report 10 could not determine this because no job had been submitted. Jobs 32
     and 33 both received `SLURM_JOB_GPUS=0` and the job script itself logged
     `WARNING: Slurm allocated GPU 0 but it already holds 86061 MiB from an
     unscheduled process` — so there is **no** out-of-band GRES exclusion for the
     contended card `[source: evidence/docker_gpu_smoke_banyan.txt]`. Both runs
     still completed exit 0, because the smoke system is tiny; a real MD deck has
     no such margin. **The `nvidia-smi` pre-flight is therefore mandatory, not
     precautionary**, and a job that needs the full card should pin the free one
     explicitly.

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
- **(c) Which cluster to smoke-test first — SETTLED BY EVENTS, banyan went
  first.** Jobs 32 and 33 both ran on banyan's H100, on the contended GPU 0 as
  it happens (Slurm allocated it while another user's process held ~86 GB; the
  runs still completed, exit 0)
  `[source: evidence/docker_gpu_smoke_banyan.txt]`. The argument for dgx1-first
  was that it would find the SIF-skew problem sooner — that problem has since
  been looked for directly and **not found** (see the risk register below), so
  the ordering cost nothing. **The remaining open call is narrower:** whether the
  dgx1 *GPU* run is worth an attended session now, or waits until the real
  p53-MDM2 decks exist.
- **(d) Real simulation decks are downstream.** As in gated step 4 — out of scope here.

## Known risks (encoded honestly, not hidden)

- **GPU-generation portability.** Handled by CUDA 12.9 + `GMX_CUDA_TARGET_SM="70;90"`.
  If CUDA 13 is ever used, V100/dgx1 support is silently lost. **Now partly
  observed rather than trusted:** the compiled `libgromacs.so.10.0.0` carries real
  SASS for both targets — `SM_ELF=sm_70;sm_90` over 98 ELF records — and the same
  summary came back byte-identical from the rebuilt image in job 33
  `[source: evidence/sass_audit_banyan.txt; evidence/convert_verify_banyan.txt
  "STEP 1b"]`. **The `sm_70` half has still never been executed** — no V100 has
  run this image — so this is a compile-time observation, not a run-time one. The
  audit's own remaining questions belong to `sass_portability_audit`.
- **✅ SIF version skew (flagged in report 07) — RESOLVED TO AN OBSERVATION, with
  one caveat that stops it being a guarantee.** The delivered `.sif` was written on
  banyan by **singularity-ce 4.2.2** and has now been **opened and executed under
  dgx1's singularity 3.5.2** (a 2019 release), read-only and with no GPU:
  `singularity inspect` exits **0** and prints `GromacsVer: 2025.3` and `TargetSM:
  70;90` with **no** `BuildStatus` key, and `singularity exec … ls
  /opt/gromacs/bin` exits **0** and shows `gmx` (120984 bytes). The `exec` is the
  decisive half — `inspect` only reads metadata, whereas `exec` must actually mount
  and read through the squashfs, which is exactly where a too-new compressor would
  have failed `[source: evidence/dgx1_sif_open.txt, commit a46515b]`.
  - **Why it mounted — a mechanism, not luck.** The payload is squashfs 4.0 with
    **gzip** compression at a 128 KiB block size. gzip is the oldest and most
    universally supported squashfs compressor, so 4.2.2 never reached for zstd or
    lz4, which is what the 2019 runtime could have failed to decode
    `[source: same file, SQUASHFS_COMPRESSION]`. No older-compatible rebuild and
    no per-cluster image is needed.
  - **⚠️ Caveat — this is a builder *default*, not a contracted guarantee.** Nothing
    promises that singularity-ce keeps defaulting to gzip, and an explicit
    `--compress` choice would reintroduce precisely this risk
    `[assumption: no source consulted here contracts gzip as a stable default; the
    observation covers this image, built by this builder, on this host]`. So
    **re-run the open check after any change of build host, singularity version, or
    compression flag** — it is cheap and read-only: `singularity inspect` then
    `singularity exec <sif> ls /opt/gromacs/bin` on dgx1.
  - **What this does NOT establish:** that the image can drive a dgx1 **GPU**. The
    check took no `--nv` flag and requested no device, so `gmx --version` printing
    `CUDA driver: 0.0` there is the expected reading of a driverless run — `gmx`
    carries no `libcuda.so.1` `DT_NEEDED` entry and resolves the driver lazily —
    and it says nothing about skew in either direction. A dgx1 GPU run remains
    untested and PI-attended per Q-006.
  - Building *on* the older runtime remains harder regardless, because dgx1 has
    **neither** Docker access **nor** fakeroot for this user
    `[source: report 10 §3]` — hence banyan-build, dgx1-verify.
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
- **⚠️ banyan GPU 0 occupancy is invisible to Slurm — and Slurm allocates it
  anyway.** ~86 GB held by another user's process while Slurm says `IDLE`
  `[source: report 10 §7]`. The open half of this risk is now closed by
  observation: jobs 32 and 33 were both **handed GPU 0** (`SLURM_JOB_GPUS=0`)
  with that process still resident, so there is no out-of-band GRES exclusion
  `[source: evidence/docker_gpu_smoke_banyan.txt]`. Both completed only because
  the smoke system is small. Mitigation remains the `nvidia-smi` pre-flight in
  gated step 3, now mandatory rather than advisory.
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
`libcuda.so.1` correction (the `docker run` note in gated step 1 — the SASS and
PTX captures themselves live in `evidence/sass_audit_banyan.txt` and their
write-up belongs to `sass_portability_audit`, not to this footer). **As recorded
on that date and superseded the next day:** `gromacs.sif` did not yet exist, no
GPU had executed the container, and the `sm_70`/`sm_90` SASS targets were still
under audit — see the 2026-07-31 entry below, which is the live state.*
*`sif_delivery/crosscluster_readonly/dgx1_sif_open_check`, Step 3 (2026-07-31):
**all three "still not built or run" clauses of the entry above are now false**,
and this runbook describes a delivered, GPU-exercised, cross-cluster-readable
image. Attended **job 32** (2026-07-30, exit 0) ran GROMACS on a real H100 under
Docker — `CUDA driver: 13.20`, one GPU detected, PME on device. Attended **job
33** (finished 2026-07-31 01:42 JST, exit 0, 17m03s) delivered
`/home/eliott/p53mdm2/gromacs.sif` (5750255616 bytes, sha256
`1fc04f8b…d20c81ac`), re-ran the identical smoke system under `singularity exec
--nv` on that H100 with docker-vs-`.sif` minimisation energy agreeing to
1.39e-06 relative, and confirmed `inspect` carries no `BuildStatus`. The SASS
audit is captured — `SM_ELF=sm_70;sm_90` — and re-verified against the rebuilt
image. This unattended cycle-007 pass added the read-only cross-cluster
observation (one digest computed on both clusters, `inspect` and `exec` both
exit 0 under dgx1's singularity 3.5.2, payload squashfs/gzip) and rewrote the
SIF-version-skew risk from an open risk to an observation carrying its
gzip-is-only-a-default caveat. Evidence, all indexed in
`evidence/manifest.jsonl`: `evidence/docker_gpu_smoke_banyan.txt`,
`evidence/convert_verify_banyan.txt`, `evidence/sass_audit_banyan.txt`,
`evidence/dgx1_sif_open.txt` (commit `a46515b`). **Still not true, and not
claimed anywhere above:** no dgx1 GPU has run the image (that check took no
`--nv` and requested no device, by construction); build equivalence was measured
against a **cached** compile layer (`#7`/`#8 CACHED`) so it is not a cold-cache
reproduction; and the cleanup gate asking `/` to return to its pre-work free
space is **not met** — 430 G before and after, the last ~10 GB releasable only
by a `docker image prune` that would take other users' dangling images.*
