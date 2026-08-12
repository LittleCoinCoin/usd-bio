#!/bin/bash
# ============================================================================
# dgx1_sass_vs_jit_probe.sh — did the V100 run use sm_70 SASS, or JIT from PTX?
#
# WHY THIS QUESTION ONLY EXISTS NOW. The campaign's headline portability claim
# is that GMX_CUDA_TARGET_SM="70;90" puts REAL SASS in the image for both
# cluster architectures, so neither cluster depends on JIT. While PTX was
# believed to be sm_90-only, a working V100 run was itself proof that the sm_70
# SASS path was taken — there was nothing else it could have used. Settling
# Q-008 removed that inference: PTX exists for sm_70 too (49 records), so a
# V100 run could in principle JIT from PTX and the sm_70 SASS could be dead
# weight. Job 28 left three new entries in ~/.nv/ComputeCache, which proves
# SOME JIT occurred but not WHICH module — so it settles nothing on its own.
#
# THE DISCRIMINATOR. CUDA_CACHE_PATH redirects the JIT cache. Point it at a
# fresh empty directory and run the identical workload:
#   - nothing written  -> no JIT occurred -> kernels were loaded from SASS
#   - files written    -> JIT occurred    -> at least one module came from PTX
# This touches NOTHING else: the real cache at ~/.nv/ComputeCache is not read,
# not written and not cleared, and the .sif is mounted read-only as always.
#
# A SECOND, POSITIVE CONTROL. The same workload is then run with
# CUDA_FORCE_PTX_JIT=1, which forces the PTX path. If the probe directory stays
# empty in run A but fills in run B, run A's emptiness is meaningful rather than
# an artifact of the cache being disabled or misdirected in this environment.
# Without that control an empty directory is ambiguous, which is the same
# mistake this campaign has been correcting all along.
# ============================================================================
set -uo pipefail

WORK=/home/eliott/p53mdm2
TEMPLATES="$WORK/smoke_system"
SIF="$WORK/gromacs.sif"
PROBE_A="$WORK/tmp/jitprobe_default"
PROBE_B="$WORK/tmp/jitprobe_forced"
PROBE_C="$WORK/tmp/jitprobe_fullrun"
RUNDIR_A="$WORK/smoke_run_jitprobe_a"
RUNDIR_B="$WORK/smoke_run_jitprobe_b"
RUNDIR_C="$WORK/smoke_run_jitprobe_c"
OUT="$WORK/dgx1_sass_vs_jit_out.txt"
SMOKE_NTOMP=8

note() { echo; echo "======== $* ========"; }
exec > >(tee "$OUT") 2>&1

note "dgx1_sass_vs_jit_probe.sh starting $(date -Is)  job=${SLURM_JOB_ID:-none}"
echo "host: $(hostname)"
echo "singularity: $(singularity --version)"
echo "sif_sha256: $(sha256sum "$SIF" | awk '{print $1}')"
echo "real_cache_untouched: $HOME/.nv/ComputeCache (never read, written or cleared by this probe)"
echo "real_cache_size_before: $(du -sh "$HOME/.nv/ComputeCache" 2>/dev/null | awk '{print $1}')"

# Only the minimisation step is needed: it is what loads the nonbonded kernels.
run_probe() {
    local label="$1" cache="$2" rundir="$3" force="$4"
    note "RUN $label: CUDA_CACHE_PATH=$cache CUDA_FORCE_PTX_JIT=$force"
    rm -rf "$cache" "$rundir"; mkdir -p "$cache" "$rundir"
    echo "cache_files_before: $(find "$cache" -type f 2>/dev/null | wc -l | tr -d ' ')"
    # Singularity 3.5 passes the host environment through, but the
    # SINGULARITYENV_ prefix is the contracted way to set a container variable,
    # so both are set rather than relying on pass-through behaviour.
    SINGULARITYENV_CUDA_CACHE_PATH="$cache" \
    SINGULARITYENV_CUDA_FORCE_PTX_JIT="$force" \
    SINGULARITYENV_CUDA_CACHE_DISABLE=0 \
    CUDA_CACHE_PATH="$cache" CUDA_FORCE_PTX_JIT="$force" CUDA_CACHE_DISABLE=0 \
    singularity exec --nv -B "$TEMPLATES:/templates:ro" -B "$rundir:/work" --pwd /work "$SIF" \
        bash -c '
          set -e
          echo "in_container_CUDA_CACHE_PATH=${CUDA_CACHE_PATH:-unset}"
          echo "in_container_CUDA_FORCE_PTX_JIT=${CUDA_FORCE_PTX_JIT:-unset}"
          bash /templates/make_box.sh /templates /work 3.0
          /opt/gromacs/bin/gmx grompp -f min.mdp -c conf.gro -p topol.top -o min.tpr -maxwarn 2
          /opt/gromacs/bin/gmx mdrun -deffnm min -nb gpu -ntmpi 1 -ntomp '"$SMOKE_NTOMP"'
        ' 2>&1 | grep -E 'in_container_|compute cap|GPU selected|Using GPU .* nonbonded|Potential Energy|converged'
    local rc="${PIPESTATUS[0]}"
    local n; n=$(find "$cache" -type f 2>/dev/null | wc -l | tr -d ' ')
    local sz; sz=$(du -sb "$cache" 2>/dev/null | awk '{print $1}')
    echo "run_exit: $rc"
    echo "cache_files_after: $n"
    echo "cache_bytes_after: ${sz:-0}"
    eval "RC_$label=$rc; N_$label=$n; SZ_$label=${sz:-0}"
}

run_probe A "$PROBE_A" "$RUNDIR_A" 0
run_probe B "$PROBE_B" "$RUNDIR_B" 1


# Run C covers the FULL min+md sequence that job 28 ran. Run A used minimisation
# only, so it could not account for the three cache entries job 28 left behind:
# the md step additionally puts PME on the GPU, which loads different modules.
# Without this, "no JIT" would be a claim about half the workload.
run_full() {
    local label="$1" cache="$2" rundir="$3"
    note "RUN $label: FULL min+md sequence (matches job 28), CUDA_CACHE_PATH=$cache"
    rm -rf "$cache" "$rundir"; mkdir -p "$cache" "$rundir"
    echo "cache_files_before: $(find "$cache" -type f 2>/dev/null | wc -l | tr -d ' ')"
    SINGULARITYENV_CUDA_CACHE_PATH="$cache" SINGULARITYENV_CUDA_CACHE_DISABLE=0 \
    CUDA_CACHE_PATH="$cache" CUDA_CACHE_DISABLE=0 \
    singularity exec --nv -B "$TEMPLATES:/templates:ro" -B "$rundir:/work" --pwd /work "$SIF" \
        bash -c '
          set -e
          echo "in_container_CUDA_CACHE_PATH=${CUDA_CACHE_PATH:-unset}"
          bash /templates/make_box.sh /templates /work 3.0
          /opt/gromacs/bin/gmx grompp -f min.mdp -c conf.gro -p topol.top -o min.tpr -maxwarn 2
          /opt/gromacs/bin/gmx mdrun -deffnm min -nb gpu -ntmpi 1 -ntomp '"$SMOKE_NTOMP"'
          /opt/gromacs/bin/gmx grompp -f md.mdp -c min.gro -p topol.top -o md.tpr -maxwarn 2
          /opt/gromacs/bin/gmx mdrun -deffnm md -nb gpu -ntmpi 1 -ntomp '"$SMOKE_NTOMP"'
        ' 2>&1 | grep -E 'in_container_|GPU selected|Using GPU .* nonbonded|PME tasks will do|Potential Energy|converged|steps,'
    local rc="${PIPESTATUS[0]}"
    local n; n=$(find "$cache" -type f 2>/dev/null | wc -l | tr -d ' ')
    local sz; sz=$(du -sb "$cache" 2>/dev/null | awk '{print $1}')
    echo "run_exit: $rc"; echo "cache_files_after: $n"; echo "cache_bytes_after: ${sz:-0}"
    eval "RC_$label=$rc; N_$label=$n; SZ_$label=${sz:-0}"
}

run_full C "$PROBE_C" "$RUNDIR_C"

note "SUMMARY"
echo "real_cache_size_after: $(du -sh "$HOME/.nv/ComputeCache" 2>/dev/null | awk '{print $1}')"
VERDICT="INCONCLUSIVE"
if [ "${N_B:-0}" -eq 0 ]; then
    # Forced-JIT wrote nothing either, so the probe cannot detect JIT at all here.
    VERDICT="INCONCLUSIVE - forced-JIT control wrote no cache, so an empty default run proves nothing"
elif [ "${N_A:-0}" -eq 0 ]; then
    VERDICT="SASS - default run JIT-compiled nothing while the forced control did, so kernels came from the embedded sm_70 SASS"
elif [ "${N_A:-0}" -gt 0 ]; then
    VERDICT="JIT - the default run wrote JIT cache entries, so at least one module was compiled from PTX rather than loaded from SASS"
fi
# Run C is the one that covers the whole workload; it overrides A's narrower result.
if [ "${N_B:-0}" -gt 0 ] && [ "${N_C:-0}" -eq 0 ]; then
    VERDICT="SASS - neither the minimisation-only run nor the FULL min+md run (PME on GPU included) JIT-compiled anything, while the forced control wrote ${N_B} files; kernels come from the embedded sm_70 SASS"
elif [ "${N_C:-0}" -gt 0 ]; then
    VERDICT="MIXED - minimisation loaded from SASS but the full min+md run wrote ${N_C} JIT cache entries, so the md/PME path compiles at least one module from PTX"
fi
echo "--- SUMMARY ---"
echo "CLUSTER=dgx1"
echo "GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | sort -u | paste -sd';' -)"
echo "DEFAULT_RUN_EXIT=${RC_A:-NONE}"
echo "DEFAULT_RUN_JIT_FILES=${N_A:-NONE}"
echo "DEFAULT_RUN_JIT_BYTES=${SZ_A:-NONE}"
echo "FORCED_JIT_RUN_EXIT=${RC_B:-NONE}"
echo "FORCED_JIT_RUN_JIT_FILES=${N_B:-NONE}"
echo "FORCED_JIT_RUN_JIT_BYTES=${SZ_B:-NONE}"
echo "FULLRUN_EXIT=${RC_C:-NONE}"
echo "FULLRUN_JIT_FILES=${N_C:-NONE}"
echo "FULLRUN_JIT_BYTES=${SZ_C:-NONE}"
echo "SASS_OR_JIT_VERDICT=$VERDICT"
echo "SIF_SHA256=$(sha256sum "$SIF" | awk '{print $1}')"
echo "--- END SUMMARY ---"

note "RESULT: verdict=$VERDICT"
exit 0
