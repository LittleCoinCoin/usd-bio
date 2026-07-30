#!/bin/bash
# ============================================================================
# convert_verify.sh — steps 1-3 of the convert_verify_cleanup leaf.
#
#   1. rebuild from the corrected recipe, and prove build equivalence
#   2. docker save -> singularity build -> gromacs.sif on the SHARED HOME
#   3. run the IDENTICAL smoke system under `singularity exec --nv`
#
# CLEANUP (step 5) IS DELIBERATELY NOT HERE. It is irreversible — it destroys
# the ability to re-run these steps — so it stays a separate, explicit action
# taken only after these results are verified.
#
# WHY THE REBUILD IS NOT WASTED WORK: removing the BuildStatus label edited the
# Dockerfile above every expensive RUN, so a rebuild is forced regardless. That
# makes it free to turn into a build-reproducibility datum: re-run the SASS
# audit and the version query against the rebuilt image and diff both against
# the captures taken from the original build. Identical output means the
# correction was documentation-only and the build reproduces from a clean cache
# — a claim this campaign otherwise cannot make at all.
#
# WHY CONVERSION NEEDS NO ROOT (the crux of Route B): building a .sif from a
# docker-archive executes no %post section, so it needs neither root nor
# --fakeroot. The missing /etc/subuid mapping that killed the native
# `singularity build` path is simply irrelevant here.
#
# All scratch is redirected under the shared home: `/tmp` is on `/`, and `/` is
# the 900 G filesystem also holding 213 G of other users' docker layers.
# ============================================================================
set -uo pipefail

WORK=/home/eliott/p53mdm2
TEMPLATES="$WORK/smoke_system"
IMAGE=gromacs-p53mdm2:latest
TAR="$WORK/gromacs.tar"
SIF="$WORK/gromacs.sif"
RUNDIR="$WORK/smoke_run_sif"
BASELINE="$WORK/sass_audit_banyan.txt"
SENTINEL="$WORK/CONVERT_STATUS"
OUT="$WORK/convert_verify_out.txt"

rc=0
note() { echo; echo "======== $* ========"; }
fail() { echo "FATAL: $*" >&2; printf 'stage=convert_verify\nexit=1\nreason=%s\nfinished=%s\n' "$1" "$(date -Is)" > "$SENTINEL"; exit 1; }

exec > >(tee "$OUT") 2>&1

note "convert_verify.sh starting $(date -Is)  job=${SLURM_JOB_ID:-none}"

export SINGULARITY_TMPDIR="$WORK/tmp"
export SINGULARITY_CACHEDIR="$WORK/cache"
export TMPDIR="$WORK/tmp"
mkdir -p "$SINGULARITY_TMPDIR" "$SINGULARITY_CACHEDIR"
echo "SINGULARITY_TMPDIR=$SINGULARITY_TMPDIR"

note "pre-flight disk"
df -h / /home | tail -2
[ "$(df -P /home | awk 'NR==2{print int($4/1048576)}')" -ge 30 ] || fail insufficient_home_space

# --- STEP 1: rebuild + build equivalence ------------------------------------
note "STEP 1a: docker build from the corrected recipe"
docker build --cpuset-cpus="0-63" -t "$IMAGE" -f "$WORK/Dockerfile" "$WORK" 2>&1 | tail -12
[ "${PIPESTATUS[0]}" -eq 0 ] || fail docker_build_failed
NEW_ID="$(docker images --no-trunc --format '{{.ID}}' "$IMAGE")"
echo "rebuilt_image_id: $NEW_ID"

note "STEP 1b: re-run the SASS audit on the rebuilt image (device-free)"
docker run --rm -i --ulimit core=0 -e NVIDIA_VISIBLE_DEVICES=void "$IMAGE" \
    bash -s < "$WORK/sass_audit.sh" > "$WORK/sass_audit_rebuild.txt" 2>&1
echo "rebuild audit exit: $?"
sed -n '/--- SUMMARY ---/,/--- END SUMMARY ---/p' "$WORK/sass_audit_rebuild.txt"

note "STEP 1c: build equivalence — diff rebuilt vs original captures"
for blk in SUMMARY GMX_VERSION_BLOCK; do
    a=$(sed -n "/--- ${blk} ---/,/--- END ${blk} ---/p" "$BASELINE")
    b=$(sed -n "/--- ${blk} ---/,/--- END ${blk} ---/p" "$WORK/sass_audit_rebuild.txt")
    if [ "$a" = "$b" ]; then
        echo "EQUIVALENCE_${blk}=identical"
    else
        echo "EQUIVALENCE_${blk}=DIFFERS"
        diff <(printf '%s\n' "$a") <(printf '%s\n' "$b") | head -20
        rc=1
    fi
done
[ "$rc" -eq 0 ] || fail build_not_equivalent

# --- STEP 2: convert --------------------------------------------------------
note "STEP 2a: docker save -> shared home"
rm -f "$TAR"
docker save "$IMAGE" -o "$TAR" || fail docker_save_failed
echo "tar_bytes: $(stat -c %s "$TAR")"
echo "tar_sha256: $(sha256sum "$TAR" | awk '{print $1}')"

note "STEP 2b: singularity build (no %post -> no root, no --fakeroot needed)"
rm -f "$SIF"
singularity build "$SIF" "docker-archive://$TAR" 2>&1 | tail -12
[ "${PIPESTATUS[0]}" -eq 0 ] || fail singularity_build_failed
echo "sif_bytes: $(stat -c %s "$SIF")"
echo "sif_sha256: $(sha256sum "$SIF" | awk '{print $1}')"
echo "sif_filesystem: $(df -P "$SIF" | awk 'NR==2{print $1" "$6}')"

note "STEP 2c: singularity inspect — labels must be truthful"
singularity inspect "$SIF" 2>&1
if singularity inspect "$SIF" 2>&1 | grep -qi 'BuildStatus'; then
    echo "GATE_NO_BUILDSTATUS=FAIL (the label reached the artifact)"; rc=1
else
    echo "GATE_NO_BUILDSTATUS=PASS"
fi
singularity inspect "$SIF" 2>&1 | grep -q 'GromacsVer.*2025.3' && echo "GATE_GROMACSVER=PASS" || { echo "GATE_GROMACSVER=FAIL"; rc=1; }
singularity inspect "$SIF" 2>&1 | grep -q 'TargetSM.*70;90'   && echo "GATE_TARGETSM=PASS"   || { echo "GATE_TARGETSM=FAIL"; rc=1; }

# --- STEP 3: like-for-like GPU smoke under singularity ----------------------
note "STEP 3: identical smoke system under singularity exec --nv"
DEV=""
for v in SLURM_JOB_GPUS SLURM_STEP_GPUS; do
    val="${!v:-}"; [ -n "$val" ] && { DEV="${val%%,*}"; echo "device_source: $v=$val"; break; }
done
[ -n "$DEV" ] || { DEV="${CUDA_VISIBLE_DEVICES%%,*}"; echo "device_source: CUDA_VISIBLE_DEVICES (may be relative)"; }
echo "resolved_global_gpu: ${DEV:-none}"
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader

rm -rf "$RUNDIR"; mkdir -p "$RUNDIR"
# Thread count is PINNED to 8 to match the docker baseline exactly, NOT taken
# from SLURM_CPUS_PER_TASK. The job requests 64 cores for the build's cpuset,
# but running the smoke with 64 OpenMP threads on a 2652-atom system would make
# it a different run from the one we are comparing against.
SMOKE_NTOMP=8
# Unlike the docker path, this genuinely runs inside the job's cgroup.
singularity exec --nv -B "$TEMPLATES:/templates:ro" -B "$RUNDIR:/work" --pwd /work "$SIF" \
    bash -c '
      set -e
      /opt/gromacs/bin/gmx --version
      bash /templates/make_box.sh /templates /work 3.0
      /opt/gromacs/bin/gmx grompp -f min.mdp -c conf.gro -p topol.top -o min.tpr -maxwarn 2
      /opt/gromacs/bin/gmx mdrun -deffnm min -nb gpu -ntmpi 1 -ntomp '"$SMOKE_NTOMP"'
      /opt/gromacs/bin/gmx grompp -f md.mdp -c min.gro -p topol.top -o md.tpr -maxwarn 2
      /opt/gromacs/bin/gmx mdrun -deffnm md -nb gpu -ntmpi 1 -ntomp '"$SMOKE_NTOMP"'
    ' 2>&1 | grep -E 'GROMACS version|Precision|GPU support|SIMD|CUDA driver|CUDA runtime|solvated_molecules|sol_lines|atoms_in_conf|Potential Energy|converged|steps,|Performance:'
sif_rc="${PIPESTATUS[0]}"
echo "sif_run_exit: $sif_rc"
[ "$sif_rc" -eq 0 ] || rc=1

note "STEP 3b: GPU evidence from the .sif run"
grep -E 'GPUs detected|compute cap|GPU selected|Using GPU .* nonbonded|PME tasks will do' "$RUNDIR/md.log" 2>/dev/null \
    || { echo "NOT FOUND — no GPU block in the .sif md.log"; rc=1; }

note "STEP 3c: docker-vs-sif parity"
D_PE=$(grep -m1 'Potential Energy' "$WORK/smoke_run_docker/min.log" 2>/dev/null | awk '{print $4}')
S_PE=$(grep -m1 'Potential Energy' "$RUNDIR/min.log" 2>/dev/null | awk '{print $4}')
echo "docker_min_potential_energy: ${D_PE:-unavailable}"
echo "sif_min_potential_energy:    ${S_PE:-unavailable}"
if [ -n "${D_PE:-}" ] && [ -n "${S_PE:-}" ]; then
    REL=$(awk -v a="$D_PE" -v b="$S_PE" 'BEGIN{d=(a-b); if(d<0)d=-d; print (a==0)?d:d/((a<0)?-a:a)}')
    echo "relative_difference: $REL"
    awk -v r="$REL" 'BEGIN{exit !(r<=1e-3)}' && echo "GATE_ENERGY_PARITY=PASS (<=1e-3)" || { echo "GATE_ENERGY_PARITY=FAIL"; rc=1; }
else
    echo "GATE_ENERGY_PARITY=INCONCLUSIVE (a baseline log is missing)"; rc=1
fi

printf 'stage=convert_verify\nexit=%s\nsif_sha256=%s\nrebuilt_image=%s\nfinished=%s\n' \
    "$rc" "$(sha256sum "$SIF" 2>/dev/null | awk '{print $1}')" "$NEW_ID" "$(date -Is)" > "$SENTINEL"

note "RESULT: rc=$rc  (cleanup NOT performed — that is a separate, irreversible step)"
exit "$rc"
