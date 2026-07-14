# p53-mdm2 — Cluster Reconnaissance for Containerized MD (p1b Step 2) — Knowledge Transfer (v0)

Date: 2026-07-14
Cycle: cycle-003
Author: Claude Opus 4.8 (async recon sub-agent)
Report type: knowledge-transfer (post-cycle retrospective; wins / pain points / next-cycle changes)
Scope: READ-ONLY reconnaissance of dgx1 and banyan for the self-run p53–MDM2 MD track. No jobs submitted, no images pulled/built/run, no files written on either cluster.

## Executive Summary

- **Headline for the PI: the assumed execution model needs revision.** The PI's Q-003 directive assumes "no Singularity on these clusters; we use Docker with bind-mounts" `[source: __threads__/p53-mdm2/QUESTIONS.md Q-003 answer]`. The cluster docs say the **opposite**: **Singularity is installed and is the *supported* container path on BOTH clusters**, and Docker, while installed, is explicitly *not* the batch path `[source: dgx1 docs "Containers"; banyan docs "Containers"; get_facility dgx1 & banyan]`. On banyan Singularity 4.2.2 is even loaded as a default module `[source: get_facility banyan]`. The recommendation is to **build with Docker locally, run with Singularity on the cluster** — this satisfies the PI's real goal (a reusable containerized MD engine, bind-mounted I/O, GPU passthrough) via the path the cluster actually supports.
- **I could not verify a single live cluster fact this cycle.** Every command / filesystem / live-status call to **both** clusters failed at the transport layer (details in Pain Points). All findings below are therefore **doc-sourced** (the docs tools worked) and must be re-confirmed live next cycle. This is flagged honestly throughout.
- **GPUs are strong and need no account.** dgx1 = 8× V100-SXM2 16 GB; banyan = 2× H100 NVL ~94 GB; both single-node Slurm, `--gres=gpu:N`, no `--account` needed `[source: get_facility dgx1 & banyan]`.
- **No MD engine is pre-installed** as a module on either cluster (banyan's module list has CUDA/cuDNN/NCCL/GCC/OpenMPI/Python/TensorRT but **no GROMACS/GENESIS/AMBER/NAMD/OpenMM**; dgx1 has no module system at all) — so containerizing the engine is genuinely required, confirming the roadmap premise `[source: get_facility banyan modules list; dgx1 docs "Software (no module system)"]`.

## Wins (what's available and usable)

| Concern | dgx1 | banyan | Source |
|---|---|---|---|
| GPUs | 8× **V100-SXM2 16 GB** | 2× **H100 NVL ~94 GB** | `[source: get_facility]` |
| CPU / RAM | 32c/64t, 754 GB | 64c/128t, 1007 GB | `[source: get_facility]` |
| Scheduler | Slurm 23.11.4 | Slurm 22.05.2 | `[source: get_facility]` |
| GPU request syntax | `--gres=gpu:N` (1–8); `--gpus*` does NOT work | `--gres=gpu:N` (1–2); `--gpus*` does NOT work | `[source: get_facility; docs "Using the GPUs"]` |
| Account/project | none required | none required | `[source: docs "Submitting jobs"]` |
| Max walltime | 5 days (120:00:00) | 5 days (120:00:00) | `[source: get_facility]` |
| Container runtime (supported) | **Singularity** (Docker also installed, not preferred) | **Singularity 4.2.2** default module (Docker+podman installed, not preferred) | `[source: docs "Containers"; get_facility]` |
| GPU-in-container | agent auto-adds `singularity exec --nv` when GPUs requested | same | `[source: docs "Containers"]` |
| Home (shared, for scripts+outputs) | `/home/<user>` NFS ~29 TB | `/home/<user>` NFS ~29 TB | `[source: docs "Storage"]` |
| Fast scratch | `/tmp` local ~1.7 TB, no auto-purge | `/tmp` local NVMe ~900 GB, no auto-purge | `[source: docs "Storage"]` |

Key usability wins for the MD track:
- **Singularity does exactly what the PI wants Docker to do**: bind-mounts (`-B host:container`) and automatic GPU passthrough (`--nv`), and the MCP `submit_job` tool *already wraps commands in `singularity exec --nv`* `[source: docs "Containers"]`. The bind-mount execution pattern the PI described is natively supported — just via Singularity, not Docker.
- **No allocation friction**: no account, no project, no queue charging — submission is a bare `--gres=gpu:N` + walltime `[source: docs "Submitting jobs"]`.
- **banyan's 94 GB H100s** comfortably hold a solvated p53–MDM2 complex; **dgx1's 8 GPUs** are the better fit for replica-exchange (gREST/REUS) fan-out if the demo uses multiple replicas `[source: get_facility; R01 §"replica exchange" for the 288-replica reference deck]`.

## Pain Points (friction — the working-agent experience this cycle)

1. **dgx1: the entire HPC toolset is dead on arrival — local `rsync` too old.** Every `run_command_on_cluster`, `fs_ls`, and `get_resources` call failed with: *"rsync version (2.6.9) is less than the required 3.0.0"* `[source: run_command_on_cluster dgx1 → error; fs_ls dgx1 → error; get_resources dgx1 → error]`. The dgx1 plugin *is* configured (`~/.dgx1/config.json` exists, `~/.ssh/config` has a `dgx1` alias) `[source: local test -f; grep Host ~/.ssh/config]`, so this is purely a local transport-binary problem, not an auth or config problem.
2. **banyan: not configured at all.** Every banyan tool failed with *"Plugin not configured — run the 'banyan-configuring' skill to create /Users/hacker/.banyan/config.json"* `[source: run_command_on_cluster banyan → error; get_resources banyan → error]`. Confirmed `~/.banyan/config.json` is **MISSING**, even though a `banyan` SSH alias already exists `[source: local test -f → MISSING; grep Host ~/.ssh/config → present]`. Once configured, banyan would then hit the **same** rsync blocker as dgx1.
3. **Net effect: zero live verification.** I could not run `docker info`, `nvidia-smi`, `module avail`, `df`, or a quota check on either machine. The single most important question — *can an unprivileged user actually reach the Docker daemon?* — remains **unanswered by observation** (see Open Questions). All capability claims are doc-sourced only.
4. **The docs assert Docker is "installed" but say nothing about unprivileged daemon access.** This is the classic HPC trap: a `docker` CLI on PATH does not mean a user can use it — the daemon socket usually requires `docker` group membership, which is effectively root on a shared node `[assumption: standard Docker security model; not verified on these hosts because commands were blocked]`. The docs' silence + their steering toward Singularity is itself weak evidence that Docker is not the intended unprivileged path.

## Root Causes

- **rsync blocker (dgx1, and latent on banyan):** macOS ships `/usr/bin/rsync` = Apple **openrsync (protocol 29, reports as 2.6.9)**, and it sits *ahead* of Homebrew's `/opt/homebrew/bin/rsync` **3.4.4 (protocol 32)** on PATH `[source: local which -a rsync → /usr/bin/rsync then /opt/homebrew/bin/rsync; rsync --version → openrsync; brew rsync --version → 3.4.4]`. The `remotemanager` transport resolves the first `rsync` on PATH, gets the ancient Apple one, and refuses. Homebrew rsync 3.4.4 is already installed — the fix is purely PATH ordering / transport config, no new install.
- **banyan unconfigured:** first-time setup was simply never run for banyan (dgx1 was). The `banyan-configuring` skill writes `~/.banyan/config.json` `[source: banyan-configuring SKILL.md]`.
- **PI's Docker assumption:** likely from prior familiarity with these boxes as generic Docker hosts; the *batch/agent* path was standardized on Singularity after that, and the roadmap captured the older assumption `[source: QUESTIONS.md Q-003 vs. docs "Containers"]`.

## Next-Cycle Changes (scoped, low-risk plan for a future supervised cycle)

### A. Unblock the tooling first (local machine only — no cluster mutation, safe to do now)
1. **Fix rsync PATH for the MCP server process** so `/opt/homebrew/bin` precedes `/usr/bin` (or point `remotemanager` at `/opt/homebrew/bin/rsync`, or switch its transport to `scp` per the error's linked tutorial). Re-test with any dgx1 `fs_ls`.
2. **Configure banyan**: run the `banyan-configuring` skill to write `~/.banyan/config.json` (`{"ssh":{"host":"banyan"}}`; SSH alias already present), `chmod 600`, then validate with `banyan-doctor` `[source: banyan-configuring SKILL.md]`. These touch only the local machine.

### B. Read-only live verification pass (safe on cluster — the recon that got blocked this cycle)
Once A is done, a future agent should run these **read-only** checks on **each** cluster to confirm the doc claims and answer the Docker question. None mutates state:
- `id` and `getent group docker` — **the decisive test**: is the user in the `docker` group?
- `docker info` — does the daemon answer for this unprivileged user, or "permission denied on /var/run/docker.sock"?
- `singularity --version` — confirm the supported runtime.
- `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv` — confirm GPUs + driver.
- `module avail 2>&1` (banyan only) and `command -v gmx pmemd.cuda namd3 spdyn openmm` (both) — confirm no MD engine present.
- `df -h /home /tmp` and `quota -s 2>/dev/null || true` — confirm space; find the real per-user home quota (the ~29 TB figure is node-wide, not a per-user limit `[source: docs "Storage"]`).

### C. Execution-model decision to put to the PI (BLOCKING — needs PI sign-off)
Recommend **pivoting p1b Step 2 from Docker to Singularity/Apptainer**, keeping Docker only as the *local build* format:
- Build the MD-engine image locally with `docker build` (developer laptop / CI), then convert to a `.sif` — either `singularity build engine.sif docker-daemon://…` or, cleaner, push to a registry / save a `docker-archive` tarball and `singularity build engine.sif docker-archive://engine.tar`. This reconciles the PI's "we use Docker" instinct (build side) with the cluster's Singularity reality (run side).
- Rationale to give the PI: Singularity is the *supported, rootless-friendly* HPC path, needs no `docker` group (which is effectively root on a shared node), and the `submit_job` tooling already emits `singularity exec --nv` — so bind-mount + GPU MD works with zero tooling fight `[source: docs "Containers"]`.

### D. Proposed bind-mount run pattern (to validate under supervision, not this cycle)
Stage inputs under home, bind-mount in/out, keep heavy scratch on `/tmp`:
- `singularity exec --nv -B /home/<user>/p53mdm2/in:/data/in -B /home/<user>/p53mdm2/out:/data/out engine.sif <md-command>`
- home for durable inputs/outputs (NFS, survives), `/tmp` for fast per-run scratch (clean up manually — no auto-purge) `[source: docs "Storage"]`.

### E. Commands that MUTATE the shared cluster — require explicit PI approval before ANY future cycle runs them
- `singularity build …` / `singularity pull …` on the cluster (writes a multi-GB `.sif` into shared NFS home).
- Any `docker pull` / `docker build` / `docker run` **on the cluster** (also potentially requires privileged daemon access).
- `submit_job` (launches real GPU work on a shared beta node) — even a 5-minute smoke test is a mutation of the shared scheduler state.
- Any `fs_upload` / `fs_mkdir` staging of input decks into home.
Each of these should be gated behind a PI "yes" in a supervised cycle, per the beta/shared-resource caution in Q-003.

## Artifacts to Preserve

- This report — the doc-sourced capability baseline for dgx1/banyan; supersede its facts with live-verified ones next cycle.
- R01 MD reproducibility survey `[link: __reports__/p53-mdm2/01-md_reproducibility_survey_v0.md]` — provides the GENESIS gREST/REUS reference deck (288 replicas) that sizes the GPU/replica scoping decision.
- The two configuring skills as the fix references: `dgx1-configuring` / `banyan-configuring` SKILL.md (SSH + doctor validation flow).

## Open Questions

- **[Docker daemon access — THE blocker to resolve first]** Can an unprivileged user reach the Docker daemon on either host, or is it root/`docker`-group-gated? Unverified — commands were blocked. If gated (the likely case), the Docker execution model is dead and the Singularity pivot (C) is mandatory, not optional.
- **Per-user home quota**: the 29 TB is the node-wide NFS home size, not a per-user cap `[source: docs "Storage"]`; the real quota (and whether a multi-GB `.sif` + trajectory outputs fit) is unverified.
- **MD-engine choice for the container**: R01's reference workflow is GENESIS gREST/REUS `[source: R01]`, but GENESIS on 2 (banyan) or 8 (dgx1) GPUs constrains replica count; a simpler engine (GROMACS/OpenMM) may suit the *demo* better. Scoping decision, not yet made.
- **octopus as an alternative** (RIKEN, dual-vendor H200 + MI300x, and its plugin exposes allocation tools that dgx1/banyan lack): not surveyed this cycle per mission scope; worth a comparison if dgx1/banyan container access proves gated.
- **Whether the MCP `submit_job` path can drive a Docker container at all**: docs describe it only wrapping `singularity exec` `[source: docs "Containers"]`; there may be no supported Docker submission path even if the daemon is reachable interactively.

## What I Am Uncertain About

- **Everything cluster-side is doc-sourced, not observation-sourced.** Both clusters' live tooling was blocked (rsync on dgx1; missing config on banyan), so I ran **zero** commands on either machine. The docs tools are described as authoritative `[source: docs tool descriptions]`, but per the umbod honesty contract these are still *documentation claims*, not observed behavior — treat the whole capability table as "asserted by docs, pending live confirmation."
- **The Docker-vs-Singularity conclusion rests on doc wording + the standard Docker security model**, not on a failed/succeeded `docker info`. I am confident Singularity is the supported path (docs say so on both clusters); I am *inferring* (not proving) that unprivileged Docker is unavailable.
- **The rsync fix is verified locally** (brew rsync 3.4.4 present, PATH order is the cause) but I did **not** modify PATH or the transport, so I have not proven the fix actually unblocks the tools — that is step A's job next cycle.
- **Module/MD-software absence** is from banyan's `get_facility` module list + dgx1's "no modules" doc, not from a live `module avail` / `which` — a user-space MD install in someone's home could exist and would not show here.
