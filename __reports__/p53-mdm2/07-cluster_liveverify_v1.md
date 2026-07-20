# p53-mdm2 — Cluster Live-Verification for Containerized MD (p1b Step 2) — Knowledge Transfer (v1)

Date: 2026-07-21
Cycle: cycle-004
Author: Claude Opus 4.8 (async live-verify recon sub-agent)
Report type: knowledge-transfer (post-cycle retrospective; wins / pain points / next-cycle changes)
Scope: READ-ONLY live verification of dgx1 and banyan for the self-run p53–MDM2 MD track. Direct follow-up to report 05 (doc-sourced). NO jobs submitted, NO images built/pulled/run, NO files written on either cluster, NO scheduler mutation. Every cluster claim below is tagged `[live: ...]` (observed command output this cycle) or `[doc: ...]` (documentation tool) or `[assumption: ...]`.

## Executive Summary

- **Tooling is UNBLOCKED. Both clusters are reachable this cycle.** The rsync blocker and the missing banyan config are both resolved — I ran real commands on both dgx1 and banyan and captured live output. This replaces report 05's entirely doc-sourced baseline with live-verified facts `[live: fs_ls + run_command_on_cluster succeeded on both dgx1 and banyan]`.
- **The decisive Docker question is now answered — and it splits by cluster:**
  - **dgx1: unprivileged Docker is NOT usable.** User `eliott` is NOT in the `docker` group, and `docker info` returns `permission denied ... unix:///var/run/docker.sock` for the server half `[live: dgx1 id → groups=Domain Users,eliott,www-data-ldap (no docker); getent group docker → ochiai,kotone,shafi,knishida,isobe,ntanaka,su; docker info → permission denied on socket]`.
  - **banyan: unprivileged Docker IS usable.** `eliott` IS in the `docker` group and the Docker daemon answers fully (20 containers, 11 running, 51 images, Server 29.4.3) `[live: banyan id → groups include 999(docker); getent group docker → test,user,su,knishida,eliott,isobe; docker info → full Server block]`. This confirms the PI's Q-005 statement that they have deployed Docker containers on banyan before.
- **The Docker→Singularity pivot is CONFIRMED as the right cross-cluster direction** — not because Docker is broken everywhere (it works on banyan), but because Singularity is the *only portable, scheduler-integrated* path across BOTH machines. Docker on banyan works interactively yet is not the batch path and does not exist for this user on dgx1. Detail + evidence in §Conclusion.
- **All of report 05's key hardware/scheduler facts are now live-confirmed:** dgx1 = 8× Tesla V100-SXM2-16GB (driver 580.159.03); banyan = 2× H100 NVL 95830 MiB ≈94 GB (driver 595.71.05); both single-node Slurm (`all` partition, 5-day max, `--gres=gpu:N`), both idle at check time `[live: nvidia-smi + get_facility + get_resources both clusters]`.
- **No MD engine is present on either cluster** — `command -v gmx pmemd.cuda namd3 spdyn openmm` returned nothing on both, and banyan's full `module avail` has CUDA/cuDNN/NCCL/GCC/OpenMPI/Python/TensorRT/oneAPI/nvhpc but no GROMACS/GENESIS/AMBER/NAMD/OpenMM `[live: command -v both clusters → empty; banyan module avail]`. Containerizing the engine is genuinely required — the roadmap premise holds.

## Wins (what's available and live-confirmed usable)

| Concern | dgx1 | banyan | Source |
|---|---|---|---|
| GPUs | 8× Tesla V100-SXM2-16GB | 2× H100 NVL ≈94 GB (95830 MiB) | `[live: nvidia-smi]` |
| GPU driver | 580.159.03 | 595.71.05 | `[live: nvidia-smi]` |
| Container: Singularity | **3.5.2** | **singularity-ce 4.2.2** (module, loaded) | `[live: singularity --version]` |
| Container: apptainer | not installed | not installed | `[live: apptainer → command not found]` |
| Container: unprivileged Docker daemon | **NO — socket permission denied, user not in docker group** | **YES — daemon responds, user in docker group** | `[live: docker info + id + getent]` |
| MD engine (module/PATH) | none | none | `[live: command -v; banyan module avail]` |
| Scheduler | Slurm 23.11.4, accounting off | Slurm 22.05.2, accounting off | `[live+doc: get_facility]` |
| Node state at check | 1 idle / 0 alloc | 1 idle / 0 alloc | `[live: get_resources]` |
| Home (shared NFS) | `ts2:/export/home` 29T, 13T avail (56% used) | `ts2:/export/home` 29T, 13T avail (56% used) — SAME filesystem | `[live: df -h /home]` |
| Root/scratch disk | `/` 1.7T, 769G avail (holds /tmp) | `/dev/nvme0n1p4` 900G, 586G avail (holds /tmp) | `[live: df -h]` |
| module system | NONE (no `module` cmd) | Environment Modules 5.0.1 | `[live: dgx1 no module; banyan module avail]` |

Key usability wins for the MD track:
- **Home is a single shared NFS mounted identically on both clusters** — `ts2:/export/home`, and `fs_ls ~` returned byte-identical listings on dgx1 and banyan `[live: fs_ls both → identical output; df -h /home both → same ts2:/export/home]`. Inputs and a `.sif` staged once are visible from both machines — stage-once, run-anywhere.
- **Singularity's `--nv` GPU passthrough + `-B` bind-mounts are present on both**, and the docs state `submit_job` auto-wraps the command as `singularity exec` + `--nv` on GPU jobs `[doc: banyan_guide.md#containers; dgx1_guide.md#containers]`. The bind-mount execution model the PI described is natively supported via Singularity.
- **No allocation friction, live-confirmed:** no account/project, bare `--gres=gpu:N` + walltime, both nodes idle now `[live: get_facility + get_resources]`.

## Pain Points (friction this cycle)

1. **Singularity version skew across the two clusters.** dgx1 runs Singularity **3.5.2** (a 2019-era release) while banyan runs **singularity-ce 4.2.2** `[live: singularity --version both]`. A single `.sif` intended to run on both must be built for compatibility with the OLDER 3.5.2 (SIF/squashfs feature set), or maintained as per-cluster builds. Unprivileged `singularity build` / docker→sif conversion is also far more constrained on 3.5.2 (fakeroot support is limited) than on 4.2.2 — favor doing any conversion on banyan (4.2.2 + docker access) and testing the resulting `.sif` on dgx1.
2. **`docker` group = effectively root on a shared beta node.** eliott's docker-group membership on banyan grants full daemon control (which bypasses Slurm's CUDA_VISIBLE_DEVICES GPU isolation) `[live: banyan docker info responds; assumption: standard Docker security model — daemon runs as root]`. Usable, but antisocial on a shared box: a `docker run` is unscheduled GPU use that Slurm cannot see.
3. **No per-user quota is queryable.** `quota -s` produced no output on either cluster `[live: quota → no output both]`. Home is 29T shared, currently 56% full (13T free) `[live: df]`, but I could not find a per-user cap — so whether a multi-GB `.sif` + trajectory outputs will hit an individual limit is still unverified (there may simply be no quota enforcement, or it is not exposed via `quota`).
4. **`/tmp` is not a dedicated scratch volume.** `df -h /tmp` collapsed onto the root filesystem on both machines `[live: df -h /home /tmp → /tmp resolves to / on both]`. Report 05's "~1.7 TB / ~900 GB local scratch" figures are the ROOT disk sizes; `/tmp` shares that disk with the OS. Keep per-run scratch modest and clean up (no auto-purge `[doc: get_facility storage]`).

## Root Causes

- **Why tooling is unblocked now:** (a) the PI added `~/.banyan/config.json` `[live: test -f ~/.banyan/config.json → present]`; (b) in this session's shell `/opt/homebrew/bin/rsync` (3.4.4) already precedes `/usr/bin/rsync` (openrsync 2.6.9) on PATH `[live: which -a rsync → homebrew first; --version 3.4.4 vs 2.6.9]`, and the MCP transport resolved a ≥3.0 rsync — all four cluster tools (fs_ls, run_command, get_facility, get_resources) succeeded on both clusters with no rsync error this cycle `[live: no rsync error in any call]`. NOTE: I did not need to run `export PATH=...` — the resolution was already correct for the MCP server process this session. The friction point report 05 raised (server-side binary resolution not reached by a shell export) did NOT recur; the tools simply worked. `[assumption: the MCP server picked up the homebrew rsync via the already-correct login-shell PATH; I did not inspect the server process's env directly.]`
- **Why Docker splits by cluster:** membership in the host `docker` group is per-machine and hand-curated; eliott was added on banyan but not dgx1 `[live: getent group docker differs between the two hosts]`. This is an admin/provisioning fact, not a config the project controls.

## Next-Cycle Changes (scoped plan; all cluster-mutating steps stay PI-gated)

### A. Tooling (local) — DONE / no action needed
Both configs present, rsync resolves correctly, both clusters reachable. If a future session sees the old-rsync error return, prepend `export PATH=/opt/homebrew/bin:$PATH` and, if the MCP server still resolves the old binary, point remotemanager at `/opt/homebrew/bin/rsync` or set transport=scp (no install). Not needed this cycle.

### B. Container build/run strategy (refined from report 05 §C/§D)
- **Keep Docker as the LOCAL build format; RUN on-cluster via Singularity.** Build the MD-engine image with `docker build` on a laptop/CI, convert to `.sif`, run with `singularity exec --nv -B in:/data/in -B out:/data/out engine.sif <md-cmd>`.
- **Do the docker→sif conversion on banyan** (has both docker access and singularity 4.2.2), then copy the `.sif` into shared home and smoke-test it on dgx1's older 3.5.2. Because home is one shared NFS, the `.sif` is visible from both without re-upload `[live: shared ts2:/export/home]`.
- **Target SIF compatibility with singularity 3.5.2** (the older runtime) or accept per-cluster builds.

### C. Bind-mount run pattern (report 05 §D) — CONSISTENT with observation, one refinement
`singularity exec --nv -B /home/eliott/p53mdm2/in:/data/in -B /home/eliott/p53mdm2/out:/data/out engine.sif <md-command>` is consistent with what I observed (Singularity + `--nv` + `-B` on both; shared home for durable I/O) `[live: singularity present both; shared home]`. Refinement: keep heavy scratch OFF `/tmp` where it competes with the OS on the root disk; prefer a subdir in home for durable output, and if fast local scratch is needed, size it against the root-disk free space (769G dgx1 / 586G banyan) and clean up manually.

## PI-GATED mutating steps (enumerated; NOT run this cycle — each needs an explicit PI "yes")

1. **Build the MD-engine image / `.sif`.** Either local `docker build` (off-cluster, safe) then convert, OR on-cluster `singularity build engine.sif docker-daemon://<image>` on banyan — the on-cluster build writes a multi-GB `.sif` into shared NFS home → **mutation, PI-gated.**
2. **docker→sif conversion on banyan** (`singularity build ... docker-daemon://` or via `docker save` → `docker-archive://`) — writes to home → **PI-gated.**
3. **Stage inputs:** any `fs_mkdir` / `fs_upload` of input decks + the `.sif` into `/home/eliott/p53mdm2/...` → **PI-gated.**
4. **First smoke `submit_job`** (a short, e.g. 5-minute, 1-GPU MD sanity run) — mutates shared scheduler + GPU state on a beta node → **PI-gated.** Recommend banyan (idle, 94 GB H100) or dgx1 (idle) — both idle now, but state changes.
5. **(If ever chosen) `docker run` on banyan for MD** — explicitly NOT recommended (bypasses Slurm scheduling on a shared node); listed only to mark it out of scope.

## Artifacts to Preserve

- This report (v1) — the LIVE-VERIFIED capability baseline for dgx1/banyan; supersedes report 05's doc-sourced facts.
- Report 05 `[link: __reports__/p53-mdm2/05-cluster_md_recon_v0.md]` — retain as the doc-sourced predecessor; its banyan-Docker inference ("likely gated") is now REFUTED for banyan and CONFIRMED for dgx1.
- Report 01 MD reproducibility survey `[link: __reports__/p53-mdm2/01-md_reproducibility_survey_v0.md]` — GENESIS gREST/REUS reference deck for GPU/replica sizing.

## Open Questions

- **Per-user home quota:** `quota -s` returns nothing `[live]`; is there any per-user cap, or is home effectively unmetered until the shared 29T (13T free) fills? Affects whether large trajectory outputs are safe.
- **MD-engine choice for the container:** GENESIS gREST/REUS (report 01) vs a simpler GROMACS/OpenMM for the demo — a scoping decision, unchanged from report 05. banyan's 2×94 GB H100 favors a big single-system run; dgx1's 8×16 GB V100 favors replica fan-out.
- **Does `submit_job` refuse or mishandle a Docker image path?** Docs describe only `singularity exec` wrapping `[doc]`; not tested (would require a submit = mutation). Assume Singularity-only for batch.
- **SIF portability 4.2.2 → 3.5.2:** whether a `.sif` built on banyan actually runs on dgx1's 3.5.2 is unverified (verifying = running a container = mild mutation/first smoke, PI-gated).

## What I Am Uncertain About

- **The rsync/transport fix was not something I actively did** — the MCP tools simply worked this session, and I infer the server process already had a ≥3.0 rsync on its resolution path. I did not inspect the MCP server's own environment, so I cannot fully explain *why* report 05's server-side resolution problem did not recur; I can only confirm it did not `[live: zero rsync errors across 8 successful cluster calls]`. A future session on a different PATH could see it return.
- **The `submit_job` → `singularity exec --nv` wrapping is DOC-SOURCED, not observed** — I did not submit a job (mutation). The batch-path conclusion rests on the docs plus the live presence of Singularity, not on a witnessed wrapped invocation.
- **Docker daemon "works" on banyan is proven for `docker info` (read) only** — I did not `docker run` anything (mutation). Full daemon responsiveness to a read query is strong evidence, but I did not prove eliott can actually launch a container end-to-end.
- **The two clusters returned byte-identical `fs_ls ~` output.** I attribute this to a genuinely shared `ts2:/export/home` NFS (df confirms the same device on both) rather than a tooling artifact, but I did not write a sentinel file to prove the mount is the same inode namespace (writing = mutation, forbidden this cycle).
- **`getent group docker` membership lists are a point-in-time read** — admins can change group membership; the dgx1-vs-banyan split is true as of this cycle's check, not guaranteed stable.
