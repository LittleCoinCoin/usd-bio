# p53-MDM2 — Route B Build Observed on banyan (Slurm job 30) — Observation (v0)

Date: 2026-07-30

---
type: observation
topic: p53-mdm2
spotted-during: attended PI session on banyan, 2026-07-29 (Route B docker build, job 30) — recorded as R13 outside the cycle machinery, one day later, per the PI's direction to promote the session's evidence into a citable report before the recipe/runbook corrections that depend on it
date: 2026-07-29
domain: other
confidence: mixed — see the per-finding confidence line at the end of each Evidence subsection below. Nothing here is re-derived or re-verified by the agent writing this report; every fact is transcribed from the attended session's captured command output, exactly as it was captured on 2026-07-29. Where the attended session captured verbatim output, confidence is stated as confirmed; where a conclusion was drawn from that output rather than directly printed by a command, confidence is stated as inference and the drawing is shown.
urgency: high
deferred-because: This leaf (recipe_evidence_corrections) is repo-only by scope — no cluster access is authorized here. This report exists so the recipe/runbook corrections in the same leaf can cite a document instead of a conversation; filing it is Step 1 of that leaf, and the corrections themselves are Steps 2-3, done in separate commits.
---

## What Was Noticed

The Route B build that report 10 and the reports README's Round-12 update said
was still open **ran, on 2026-07-29, and succeeded on the first attempt.**
Eight things fall out of that single session, all captured verbatim by the
attended agent at the terminal:

1. **Slurm job 30 on banyan COMPLETED, exit 0, in 5m27s**, producing
   `gromacs-p53mdm2:latest` (image id `70659e395c53`, 10.6 GB).
2. **A sentinel file confirms it independently of the Slurm record**:
   `/home/eliott/p53mdm2/BUILD_STATUS` reads
   `stage=docker_build exit=0 finished=2026-07-29T23:31:29+09:00`.
3. **Both integrity gates passed, and the previously-uncorroborated one is now
   empirically confirmed**: the CMake sha256 and the GROMACS md5 + sha256 all
   checked out against the real, fetched tarballs — not just against each
   other's published values.
4. **The in-image build-time gate reported a real GPU-enabled GROMACS 2025.3**,
   compiled for CUDA with AVX2_256 SIMD — the ONLY gate report 10 could not
   have predicted the exact wording of, since nothing had been built before.
5. **`docker info`'s data-root question, open since report 10, is now
   answered by direct observation**: `/var/lib/docker`, on `/`, and only an
   admin can move it.
6. **Banyan's `/` free space did NOT keep draining.** It held 439 G free
   across four more days (from R10's initial 2026-07-27 reading through
   2026-07-29's pre-build check) and the build itself only cost ~9 G net —
   which reframes report 10's "586 G → 439 G in 6 days" language as a
   one-off event, not an ongoing trend, though the cause of that original drop
   is still not investigated.
7. **Route A's expected failure is now an observed failure**, captured
   verbatim, and the third hatch singularity's own error message names
   (`proot`) is independently confirmed closed.
8. **The `libcuda.so.1` DT_NEEDED `[assumption]` flagged in both recipe files
   is resolved** — not by an `ldd` run, but by the shape of the build's own
   success: the in-sandbox `RUN gmx --version` gate (the one both files warned
   could abort with a missing-driver-library error) passed, in a sandbox with
   no NVIDIA driver, which is exactly what `CUDA driver: 0.0` in the version
   block says.

None of this makes the container proven on a GPU — see Scope Boundary and
Uncertainty below for what remains open.

## Context

The build these findings describe followed directly from report 10's "before
you build" list and the runbook's gated-step-1 pre-flight checklist: it used
Route B (Docker-first, since Route A had no fakeroot path), ran on banyan (the
cluster with the Docker daemon), and was itself preceded by the Route A probe
that report 10 could only infer. The whole session — probe, build, sentinel
check — was PI-attended, in keeping with Q-006's resolution that container
builds stay attended. This report was filed the following day (2026-07-30) to
turn that session's evidence into something the recipe/runbook corrections
(Steps 2-3 of this leaf) can cite by document rather than by conversation, per
this leaf's own Step 1 instructions.

## Location Map

- `__reports__/p53-mdm2/10-cluster_state_refresh_v0.md` — the report whose
  "before you build" list and disk-drawdown finding this report closes out or
  reframes
- `__reports__/p53-mdm2/README.md` — Round 12's "Update 2026-07-30" paragraph
  already summarizes this session in prose; this report is the citable
  document that paragraph pointed at but did not yet exist
- `examples/p53_mdm2/cluster/README.md` — banner, fakeroot section, gated
  step 1, data-root assumption block, disk-drawdown framing — all corrected
  in this leaf's Step 2, citing this report
- `examples/p53_mdm2/cluster/Dockerfile` and `gromacs.def` — `BuildStatus`
  label/`%labels` entry removed and the libcuda assumption resolved in this
  leaf's Step 3, citing this report
- banyan `/home/eliott/p53mdm2/BUILD_STATUS` — the sentinel; banyan Slurm job
  30 — the build record; banyan `/var/lib/docker` — the observed data-root

## Evidence

### 1. Slurm job 30 — COMPLETED, exit 0, 5m27s

```
JobID: 30
State: COMPLETED
ExitCode: 0
Elapsed: 00:05:27
Image: gromacs-p53mdm2:latest
ImageID: 70659e395c53
Size: 10.6 GB
```

**Confidence: confirmed** — this is the Slurm job record for the attended
build, captured at the terminal during the 2026-07-29 session. Not re-queried
by this report (no-accounting clusters age finished-job records out quickly,
per report 10 §6, so a later re-query would likely return nothing — this is
exactly why the record had to be captured at the time, not reconstructed
later).

### 2. BUILD_STATUS sentinel on shared home

```
/home/eliott/p53mdm2/BUILD_STATUS:
stage=docker_build exit=0 finished=2026-07-29T23:31:29+09:00
```

**Confidence: confirmed** — a plain file read, independent of Slurm's own
accounting, and it lands on the shared NFS home so it is visible from both
clusters. It corroborates Evidence 1 from a second source rather than
depending on Slurm's short-lived job history.

### 3. Build log tail — integrity gates, BOTH tarballs, BOTH hash families

```
cmake-4.0.3-linux-x86_64.tar.gz: OK
gromacs-2025.3.tar.gz: OK
gromacs-2025.3.tar.gz: OK
```

Read against the pins in `Dockerfile`/`gromacs.def`: the first `OK` is
`sha256sum -c` on the CMake tarball (Kitware's own published checksum — this
one was never in question). The two `OK`s for the GROMACS tarball are, in
order, `md5sum -c` (the vendor-published value) and `sha256sum -c` (the
Spack/EasyBuild-corroborated value that both recipe files' comments flagged
as "strongly corroborated, NOT vendor-published"). **All three checks ran
against the actual fetched tarball bytes, not against each other.**

**Confidence: confirmed** for all three `OK` lines as captured. The upgrade
this closes is specifically the GROMACS sha256: before this build it was
corroborated only by two packaging projects agreeing with each other, never
by hashing the real GROMACS download; this build is the first time anything
hashed the actual tarball against that value, and it matched. Treat this as
empirical confirmation of that one value, not a re-verification of the
Spack/EasyBuild sourcing itself (that provenance claim is unchanged from
`gromacs.def`'s existing comments).

### 4. In-image build-time gate `[5/5]`

```
[5/5] GROMACS version:      2025.3
      Precision:            mixed
      GPU support:          CUDA
      SIMD instructions:    AVX2_256
      CUDA compiler:        nvcc release 12.9, V12.9.86
      CUDA runtime:         12.90
      CUDA driver:          0.0
```

**Confidence: confirmed** — this is the exact gate both `Dockerfile` and
`gromacs.def` bake in as a hard build-time check (`gmx --version | grep -i
"GPU support"`, failing the build otherwise). It reports the pinned values
verbatim: GROMACS 2025.3, CUDA 12.9(.86), AVX2_256 — none of these are new
decisions, this is the first time they were printed by a real binary instead
of asserted in a comment. `CUDA driver: 0.0` is the expected signature of "no
NVIDIA driver present in this sandbox" (see Evidence 8) and is not evidence of
a broken build.

### 5. Docker data-root — observed, not assumed

```
$ docker info | grep -i 'Docker Root Dir'
Docker Root Dir: /var/lib/docker
```

`/var/lib/docker` sits on the root filesystem (`/`), which the Dockerfile's
header comment had flagged as `[assumption: banyan's docker data-root was
never inspected]`. The directory holds **213 G**, observed to be mostly other
users' pre-existing images — not evidence this build added 213 G, and not ours
to prune.

**Confidence: confirmed** for the path and the "on `/`" fact (direct command
output). **Confidence: inference** for "mostly other users' images" — this
was a visual read of `docker images`/`du` output during the session, not a
systematic per-image ownership audit, and this report does not re-derive it.
The client-cannot-redirect claim is standard Docker behavior (the data-root is
a daemon-level `dockerd` config, `/etc/docker/daemon.json`, not a client
flag) — **confidence: confirmed by Docker's documented architecture**, not
independently tested by attempting a redirect.

### 6. Disk free space — a one-off, not a leak

```
2026-07-27 (report 10):  /  900G  461G used  439G free
2026-07-29 (pre-build):  /  900G  ~461G used  439G free  (unchanged, 2 days later)
2026-07-29 (post-build): /  900G  ~470G used  ~430G free (build consumed ~9G net)
```

**Confidence: confirmed** for the two 439 G readings and the fact that the
build's net footprint was small (~9 G) relative to the 147 G drop report 10
recorded over the *preceding* 6 days (2026-07-21 → 2026-07-27). **Confidence:
inference** for the conclusion that report 10's 147 G drawdown was "a one-off,
not a trend" — this report did not investigate *what* caused the earlier
drop, only that free space has now held roughly steady across the additional
four days plus this build. If something resumes draining `/` next week, this
finding would need revisiting; it rules out "still actively draining as of
2026-07-29," not "guaranteed never to drain again." The `TMPDIR`/
`SINGULARITY_TMPDIR` redirection advice in the runbook remains warranted
regardless, because `/tmp` is confirmed on the same device as `/`
(`/dev/nvme0n1p4`) — **confirmed**, and this directly contradicts a facility
doc's claim of a separate NVMe scratch device, which this report flags but
does not attempt to reconcile with that doc.

### 7. Route A failure — observed, not inferred

```
$ singularity build gromacs.sif gromacs.def
FATAL:   --remote, --fakeroot, or the proot command are required to build
         this source as a non-root user
(exit 255)
```

This is the exact command report 10 and the runbook both said would "settle
it in seconds" and both explicitly flagged their own conclusion as inference
pending this command. It is no longer inference.

**Confidence: confirmed** — verbatim captured output, non-zero exit. This
also names the third hatch (`proot`) as a possible way out, which the next
piece of evidence closes.

### 8. Absence of subuid mapping and of `proot`

```
$ grep -c '^eliott:' /etc/subuid /etc/subgid
/etc/subuid:0
/etc/subgid:0

$ command -v proot
(not found)
```

**Confidence: confirmed** — both are direct, simple command outputs with an
unambiguous reading; `grep -c` returning `0` on both files means no line for
`eliott` exists in either, and `command -v` returning nothing/non-zero means
`proot` is absent from `PATH` on banyan. Between this and Evidence 7, all
three of `singularity build`'s named alternatives to `--fakeroot` are now
closed for a non-interactive path: `--remote` is declined on principle (it
would ship the recipe to a third-party cloud builder, not merely a technical
gap), `--fakeroot` has no subuid range, and `proot` does not exist on the
host. **Confidence: inference** only for the summary claim "Route A is dead
by observation" as a blanket statement — the three specific facts above are
each directly confirmed; "dead" is the conjunction of all three plus the
policy decision to decline `--remote`, which is a judgment call recorded here
rather than a command output.

## Re-observation Steps

All of the following would need a fresh attended session (cluster-mutating or
requiring live cluster access; not run by this report):

1. `sacct -j 30` or equivalent — re-check job 30's record (may already be
   aged out; report 10 §6 notes finished-job history is short-lived on
   both clusters with no accounting)
2. `cat /home/eliott/p53mdm2/BUILD_STATUS` — the sentinel, durable on shared
   home regardless of Slurm's retention
3. `docker images gromacs-p53mdm2` and `docker info | grep -i 'Docker Root
   Dir'` — data-root and image presence
4. `df -h / /tmp` — re-check whether `/` has resumed draining since this
   report's 2026-07-29 reading
5. `singularity build /tmp/probe.sif gromacs.def` (as non-root, no
   `--fakeroot`) — re-confirm Route A still fails the same way
6. `grep -c '^eliott:' /etc/subuid /etc/subgid` and `command -v proot` —
   re-confirm the subuid/proot facts have not changed (e.g. an admin granting
   a subuid range would reopen Route A)

## Scope Boundary

This report is written from a repo-only worktree with no cluster access
authorized for this leaf. It performs **no** cluster mutation, issues **no**
commands against banyan or dgx1, and re-derives none of the facts above — they
are transcribed from the 2026-07-29 attended session as instructed. It does
not authorize any further cluster action; the four leaves that would act on
these facts (SASS portability audit, docker GPU smoke test, SIF delivery) are
separate, explicitly-scoped nodes in `__roadmap__/p53-mdm2-v2/
p1b_container_runtime/`. It does not claim the container has been proven on a
GPU, that a `.sif` exists, or that cleanup has happened — see below.

## What I Am Uncertain About

- **This report's evidence is secondhand relative to the agent writing it.**
  I (the agent authoring R13) did not run any of the commands in the Evidence
  section — I was instructed not to re-derive or re-verify them, and the repo-
  only scope of this leaf would not allow cluster access even if I wanted to.
  Every quoted output above is a transcription of what the task brief states
  was captured verbatim during the attended session. If that transcription
  introduced any error, this report would silently inherit it.
- **The "one-off, not a trend" framing of the disk drawdown** rests on four
  additional days of stability plus the build's own small footprint. It is not
  a root-cause finding — nobody has determined what caused the original 147 G
  drop, so nothing here rules out a recurrence for an unrelated reason.
- **"Mostly other users' pre-existing images" in `/var/lib/docker`** is a
  qualitative read from the session, not an audited breakdown by owner or by
  image; I state it as the session's impression, not a verified partition.
- **The libcuda.so.1 DT_NEEDED resolution is a logical inference, not a direct
  `ldd` observation.** The recipe comments themselves say the honest way to
  settle it is `ldd $(which gmx)` inside the built image, and that command was
  not run. The inference (`CUDA driver: 0.0` implies the gate passed without
  `libcuda.so.1` blocking it) is sound given how the gate is written, but it
  is still inference from a gate's exit code, not a direct symbol-table
  observation.
- **No GPU has run this container, no `.sif` exists yet, and the `sm_70`/
  `sm_90` SASS targets are unverified** — the build-time gate is CPU-only by
  construction (see the recipe files' own comments on this). These remain
  open for the sibling leaves (`sass_portability_audit`, `docker_gpu_smoke`,
  `sif_delivery`), not this one.
- **Cleanup (`docker builder prune`, `docker image rm gromacs-p53mdm2`) has
  not happened** as of this report. The 10.6 GB image and any `docker save`
  tarball, if created, may still be occupying banyan's `/var/lib/docker` or
  shared home. Not verified either way by this report.
