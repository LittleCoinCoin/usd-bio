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
>
> ### The gate is now TOOLING, not authorization
> **The PI has already given authorization.** INBOX 2026-07-25T07:58 authorized
> gated steps 1–3 (build on banyan, GROMACS 2025.3 / CUDA 12.9, then the 1-GPU
> smoke test). Cycle-006 dispatched that work **twice** and both dispatches were
> **refused by Claude Code's auto-mode permission classifier**, which blocks
> cluster-mutating actions in unattended sessions regardless of an authorization
> written into project files — the classifier does not read the thread as
> permission. See topic **Q-006** (`__threads__/p53-mdm2/QUESTIONS.md`) for the
> three ways out (attended session / pre-allow rule in
> `.claude/settings.local.json` / keep it permanently attended by policy).
>
> So: **not waiting on the PI's approval — waiting on a harness that can act on
> it.** Cycle-006 therefore did only the non-mutating half (read-only state
> refresh + finishing the version pins), and everything below is build-ready.

## Files here

| File | What it is |
|---|---|
| `gromacs.def` | Singularity/Apptainer definition: GPU-enabled **GROMACS 2025.3** on a **CUDA 12.9.1 / Ubuntu 22.04** base, built for both V100 (sm_70) and H100 (sm_90). Every pin carries an inline source URL. Not built. |
| `smoke_submit.sbatch` | Slurm template for a **1-GPU** smoke test (`gmx --version` on the GPU node + a trivial energy minimization) via `singularity exec --nv`. Not submitted. |
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

### 🚫 `--fakeroot` is NOT available to this user — the build route changed

Report 07 asserted banyan "has singularity-ce 4.2.2 + fakeroot". The version half
is right; **the fakeroot half was never tested and is wrong.** `/etc/subuid` and
`/etc/subgid` contain **no mapping for this user on either cluster** — banyan has
only `user` and `test`, dgx1 only `lxd` and `root` `[source: report 10 §3]`.
Unprivileged user namespaces are otherwise enabled on banyan
(`kernel.unprivileged_userns_clone = 1`), so the constraint is specifically the
**missing subuid/subgid range**, not a kernel lockdown. This was a
capability-vs-entitlement conflation: singularity 4.2.2 *supports* fakeroot; this
*user* is not entitled to it.

`gromacs.def`'s `%post` runs `apt-get install` and compiles, i.e. it needs
root-in-container, i.e. `--fakeroot`. **So `singularity build gromacs.sif
gromacs.def` (Route A) is expected to fail.**

> **This is inference, not an observed failure.** The missing subuid mapping is
> *proved*; no build was ever attempted (that would be a gated mutating action).
> The expectation rests on singularity's documented requirement that an
> unprivileged `--fakeroot` build needs an `/etc/subuid` entry for the invoking
> user. **One attended command settles it in seconds:**
> `singularity build --fakeroot /tmp/probe.sif gromacs.def` (or simply
> `singularity build gromacs.sif gromacs.def` and read the error). If
> singularity-ce 4.2.2 has an unprivileged `%post` path we are unaware of, this
> whole finding is void and Route A returns.

**Route B is the live path** and is now the recommendation: build with banyan's
Docker daemon, then convert to `.sif`. See gated step 1.

*Podman is a lead, not a route.* banyan has `podman 3.4.4` reporting
`Rootless: true` `[source: report 10 §3]`, but **rootless podman builds normally
consume subuid ranges too**, and no build was attempted. Do not plan around it
until someone tries it.

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

**What this does NOT claim.** No benchmark was run. banyan's Emerald Rapids may
well be faster with `AVX_512` (its AVX-512 implementation does not suffer
Skylake's clock-throttling penalty to the same degree), so if CPU-side PME ever
becomes the bottleneck on banyan specifically, the escape hatch is a
**per-architecture build** (`-DGMX_BINARY_SUFFIX`, per the guide's own advice for
heterogeneous fleets) rather than raising the flag on the shared image. The
single-`.sif`, run-anywhere constraint is what pins this to one value.

Do **not** delete the flag and rely on CMake auto-detection: it detects the
*build host*, and one `.sif` on the shared NFS home runs on two different CPU
generations.

---

## ⛔ PI-gated mutating steps — IN ORDER (none done)

Each step mutates a shared resource (the shared home or the scheduler) and needs
an explicit PI "yes". They are sequential — do not skip ahead.

1. **⛔ Build the image → `.sif`.** *(writes a multi-GB `.sif` to shared home)*

   All `gromacs.def` values are now resolved — base-image tag, tarball URL,
   md5 + sha256, CMake version/hash, every `GMX_*` flag including `GMX_SIMD` —
   each with an inline source URL. **No blanks left to fill.**

   - **Route B — Docker-first (RECOMMENDED).** On **banyan**, which has the Docker
     daemon (29.4.3) with this user in the `docker` group *and* singularity-ce
     4.2.2 `[source: report 10 §3]`. Build an equivalent Docker image from the same
     base + `%post` steps, then convert:
     ```
     docker build -t gromacs-p53mdm2 .          # same base + %post steps
     docker save gromacs-p53mdm2 -o gromacs.tar
     singularity build gromacs.sif docker-archive://gromacs.tar
     ```
     **Why this is now the recommendation:** the Docker daemon builds as root, so
     `%post`'s `apt-get` + compile work without needing `--fakeroot` — which this
     user does not have (see "🚫 `--fakeroot` is NOT available" above).
     *Cost, stated honestly:* a `docker build` is unscheduled use of a shared node
     and `docker` group ≈ root on that box (the PI's own Q-003 caution). Keep it
     short and off the GPUs.

   - **Route A — native `singularity build` (DEMOTED — expected to fail).**
     `singularity build gromacs.sif gromacs.def` on banyan. This *was* the
     recommendation; it is demoted because `%post` needs root-in-container via
     `--fakeroot` and there is **no `/etc/subuid`/`/etc/subgid` mapping for this
     user on either cluster** `[source: report 10 §3]`. **Not an observed failure —
     inference from a proved-missing mapping.** If someone is at a terminal, run it
     once anyway: it is the cheapest possible experiment and it either restores
     Route A or converts this expectation into a fact. Third option if Route A is
     wanted for real: **ask the admins for a subuid range**.

   **Pre-flight, on banyan, immediately before building:**
   - **Check free space and keep build scratch OFF the root filesystem.** banyan's
     root disk fell from 586 G to **439 G free in 6 days**, and `/tmp` sits on the
     root filesystem `[source: report 10 §5]`. A multi-GB container build plus a
     `docker save` tarball writing scratch to `/tmp` is a real risk of filling `/`
     on a shared node. Point build scratch at the shared home (13 TB free) instead:
     ```
     df -h / /tmp /home                       # re-check RIGHT before building
     export SINGULARITY_TMPDIR=/home/eliott/p53mdm2/tmp
     export SINGULARITY_CACHEDIR=/home/eliott/p53mdm2/cache
     export TMPDIR=/home/eliott/p53mdm2/tmp   # also catches docker save's temp files
     mkdir -p "$SINGULARITY_TMPDIR" "$SINGULARITY_CACHEDIR"
     ```
     Write the `docker save` tarball to shared home too, and delete it once the
     `.sif` exists.
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
- **(b) Which build route?** *(This is the gating technical question — filed as
  topic **Q-007**.)* `--fakeroot` is unavailable, so the native
  `singularity build` route is out unless the inference is wrong. Options:
  1. **Route B via banyan's Docker daemon** — works today; cost is unscheduled
     `docker build` on a shared node. **Recommended.**
  2. **Ask the admins for an `/etc/subuid` range** — unlocks Route A properly,
     but needs a human request and admin turnaround.
  3. **Build off-cluster and upload the `.sif`** — avoids shared-node load
     entirely, at the cost of a multi-GB upload over the (now-working, rsync
     3.4.4) transfer path.
  4. **Have an attended session try Route A once** to settle the inference
     empirically before choosing. Cheap; do this first if someone is at a
     terminal anyway.
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
- **SIF version skew (flagged in report 07).** The `.sif` is built under
  **singularity-ce 4.2.2** (banyan) but must also run under **singularity 3.5.2**
  (dgx1, a 2019 release). Newer squashfs compression (e.g. zstd) may not open on
  3.5.2. **Mitigation:** smoke-test on dgx1 explicitly (gated step 3); if the
  `.sif` fails to open there, either rebuild with an older-compatible compression
  or maintain a per-cluster build. Building on the older runtime is harder because
  dgx1 has **neither** Docker access **nor** fakeroot for this user
  `[source: report 10 §3]` — hence banyan-first, dgx1-verify.
- **`docker` group ≈ root on a shared box.** Building with Docker on banyan is
  unscheduled use of a shared node. This risk is now **unavoidable on the
  recommended path** rather than something to route around — `--fakeroot` is
  gone, so the `singularity build` alternative is not available to prefer. Keep
  the Docker step short, off the GPUs, and clean up the saved tarball afterwards.
- **⚠️ No fakeroot ⇒ Route A expected to fail.** Documented in full above. The
  residual risk is the inverse: this is an *inference*, so someone may burn a
  session assuming Route A is dead when it isn't. One attended `singularity build`
  attempt removes the ambiguity permanently.
- **⚠️ banyan GPU 0 occupancy is invisible to Slurm.** ~86 GB held by another
  user's process while Slurm says `IDLE` `[source: report 10 §7]`. Mitigation is
  the `nvidia-smi` pre-flight in gated step 3. Whether Slurm actually assigns
  GPU 0 was not determined.
- **⚠️ banyan root-disk drawdown.** 586 G → **439 G free in 6 days**, cause
  uninvestigated, and `/tmp` is on that filesystem `[source: report 10 §5]`. A
  multi-GB build with default scratch paths could fill `/` on a shared node.
  Mitigation is the `SINGULARITY_TMPDIR`/`TMPDIR` redirection in gated step 1,
  plus a `df -h` immediately before building.
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
