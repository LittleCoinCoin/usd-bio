#!/bin/bash
# ============================================================================
# docker_gpu_smoke.sh — prove the GROMACS container computes on a real H100.
#
# Submitted through the banyan `submit_job` tooling (the sanctioned path), which
# supplies the Slurm directives from its JobSpec. This file therefore carries NO
# #SBATCH headers on purpose: two sources of truth for the resource request is
# how you end up requesting one thing and running another.
#
# ---------------------------------------------------------------------------
# WHAT WRAPPING THIS IN SLURM DOES AND DOES NOT BUY — read before trusting it
# ---------------------------------------------------------------------------
# `docker run` is executed by the DAEMON, outside this job's cgroup. So Slurm
# gives us a reservation, a job id, a log and courtesy toward other users — but
# NOT resource isolation, and `scancel` will NOT stop a container once the
# daemon has started it. Stopping it for real needs `docker stop`.
#
# ---------------------------------------------------------------------------
# THE DEVICE-SELECTION TRAP (two independent hazards, both handled below)
# ---------------------------------------------------------------------------
# 1. banyan's daemon has `Default Runtime: nvidia` and the CUDA base image
#    carries `NVIDIA_VISIBLE_DEVICES=all`. So a container with NO --gpus flag
#    still gets the host driver injected and sees BOTH H100s. Omitting the flag
#    is not a safe default — it is the unsafe one. We therefore pin the device
#    EXPLICITLY via NVIDIA_VISIBLE_DEVICES, which is the lever the toolkit
#    actually reads under the default runtime.
# 2. `CUDA_VISIBLE_DEVICES` is the WRONG variable to read. Slurm can rewrite it
#    to ALLOCATION-RELATIVE indices, so "0" means "your first allocated GPU",
#    not global GPU 0. Feeding that to the daemon — which speaks global indices
#    — can land us on exactly the card we are trying to avoid. banyan's GPU 0
#    has repeatedly held another user's ~86 GB process that Slurm cannot see.
#    So prefer SLURM_JOB_GPUS / SLURM_STEP_GPUS, which carry GLOBAL indices.
#
# Runs as the invoking user (--user) rather than root: this NFS home does NOT
# squash root, so a root container would leave root-owned files in the user's
# own directory. Verified that gmx runs fine unprivileged.
# ============================================================================
set -uo pipefail

WORK=/home/eliott/p53mdm2
TEMPLATES="$WORK/smoke_system"
RUNDIR="$WORK/smoke_run_docker"
IMAGE=gromacs-p53mdm2:latest
SENTINEL="$WORK/SMOKE_STATUS"

rc_overall=0
note() { echo "=== $* ==="; }

note "docker_gpu_smoke.sh starting $(date -Is)"
echo "slurm_job_id: ${SLURM_JOB_ID:-none}"
echo "host: $(hostname)"

# --- resolve the allocated GPU, global index ---------------------------------
DEV=""
for var in SLURM_JOB_GPUS SLURM_STEP_GPUS; do
    val="${!var:-}"
    if [ -n "$val" ]; then DEV="${val%%,*}"; echo "device_source: $var=$val"; break; fi
done
if [ -z "$DEV" ]; then
    # Last resort only. Logged loudly because it may be allocation-relative.
    DEV="${CUDA_VISIBLE_DEVICES:-}"
    DEV="${DEV%%,*}"
    echo "device_source: CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset} (WARNING: may be allocation-relative, not global)"
fi
if [ -z "$DEV" ]; then
    echo "FATAL: no GPU index resolvable from SLURM_JOB_GPUS, SLURM_STEP_GPUS or CUDA_VISIBLE_DEVICES." >&2
    echo "       Refusing to run unpinned: with Default Runtime=nvidia the container would take BOTH GPUs." >&2
    printf 'stage=docker_gpu_smoke\nexit=2\nreason=no_gpu_index_resolved\nfinished=%s\n' "$(date -Is)" > "$SENTINEL"
    exit 2
fi
echo "resolved_global_gpu: $DEV"

# --- mandatory pre-flight: occupancy is point-in-time and has changed before --
note "pre-flight nvidia-smi (host view)"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader || true
note "pre-flight df"
df -h / /home | tail -2 || true

USED_MIB="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$DEV" 2>/dev/null | tr -d ' ')"
echo "target_gpu_${DEV}_used_mib: ${USED_MIB:-unknown}"
if [ -n "${USED_MIB:-}" ] && [ "$USED_MIB" -gt 10000 ] 2>/dev/null; then
    echo "WARNING: Slurm allocated GPU $DEV but it already holds ${USED_MIB} MiB from an unscheduled process."
    echo "         Continuing — the smoke system is tiny — but a real run should not share this card."
fi

rm -rf "$RUNDIR"; mkdir -p "$RUNDIR"

DOCKER_COMMON=(
    run --rm
    --user "$(id -u):$(id -g)"
    # Suppress core dumps INSIDE the container. Job 31's grompp segfault wrote a
    # 1.4 GB core.<pid> straight into the bind-mounted NFS home. An outer
    # `ulimit -c 0` does not reach the container, so it has to be set here.
    --ulimit core=0
    -e NVIDIA_VISIBLE_DEVICES="$DEV"
    -v "$TEMPLATES:/templates:ro"
    -v "$RUNDIR:/work"
    -w /work
    "$IMAGE"
)

# --- 1. version, now WITH a driver present ----------------------------------
note "gmx --version (expect a NON-ZERO CUDA driver, unlike the build-time 0.0)"
docker "${DOCKER_COMMON[@]}" /opt/gromacs/bin/gmx --version 2>&1 | \
    grep -E 'GROMACS version|Precision|GPU support|SIMD|CUDA driver|CUDA runtime' || rc_overall=1

# --- 2. build the water box --------------------------------------------------
# ABORT if this fails. Job 31 continued past a failed box build and handed
# grompp a malformed topology, which segfaulted and produced a core dump plus
# two cascading errors that obscured the real cause. Everything below depends
# on conf.gro, so there is nothing to salvage by continuing.
note "make_box.sh"
docker "${DOCKER_COMMON[@]}" bash /templates/make_box.sh /templates /work 3.0 2>&1 | tail -14
box_rc="${PIPESTATUS[0]}"
if [ "$box_rc" -ne 0 ]; then
    echo "FATAL: box build failed (rc=$box_rc); refusing to run grompp on an incomplete system." >&2
    printf 'stage=docker_gpu_smoke\nexit=%s\nreason=box_build_failed\ngpu_index=%s\nfinished=%s\n' \
        "$box_rc" "$DEV" "$(date -Is)" > "$SENTINEL"
    exit "$box_rc"
fi

# --- 3. minimisation (grompp warm-up; NOT the GPU proof) --------------------
note "grompp + mdrun: energy minimisation"
docker "${DOCKER_COMMON[@]}" bash -c '
  set -e
  /opt/gromacs/bin/gmx grompp -f min.mdp -c conf.gro -p topol.top -o min.tpr -maxwarn 2
  /opt/gromacs/bin/gmx mdrun -deffnm min -nb gpu -ntmpi 1 -ntomp '"${SLURM_CPUS_PER_TASK:-8}"'
' 2>&1 | tail -20
min_rc="${PIPESTATUS[0]}"
[ "$min_rc" -eq 0 ] || rc_overall=1
grep -E 'Potential Energy|Steepest Descents converged|did not converge' "$RUNDIR/min.log" 2>/dev/null | head -4 || true

# --- 4. the actual GPU proof -------------------------------------------------
note "grompp + mdrun: short MD — THIS is the GPU evidence"
docker "${DOCKER_COMMON[@]}" bash -c '
  set -e
  /opt/gromacs/bin/gmx grompp -f md.mdp -c min.gro -p topol.top -o md.tpr -maxwarn 2
  /opt/gromacs/bin/gmx mdrun -deffnm md -nb gpu -ntmpi 1 -ntomp '"${SLURM_CPUS_PER_TASK:-8}"'
' 2>&1 | tail -20
# PIPESTATUS[0], not $? — after a pipeline $? is tail's status, which is always
# 0 and would silently mask a failed mdrun.
md_rc="${PIPESTATUS[0]}"
[ "$md_rc" -eq 0 ] || rc_overall=1

note "GPU detection block from md.log"
grep -E 'GPUs detected|compute cap|GPU selected|selected for this run' "$RUNDIR/md.log" 2>/dev/null || \
    { echo "NOT FOUND — md.log has no GPU-detection block"; rc_overall=1; }

note "leftover containers on the shared node (expect none)"
docker ps -a --filter ancestor="$IMAGE" --format '{{.ID}} {{.Status}}' || true

printf 'stage=docker_gpu_smoke\nexit=%s\ngpu_index=%s\nmdrun_exit=%s\nfinished=%s\n' \
    "$rc_overall" "$DEV" "$md_rc" "$(date -Is)" > "$SENTINEL"

note "RESULT: rc_overall=$rc_overall (sentinel written to $SENTINEL)"
exit "$rc_overall"
