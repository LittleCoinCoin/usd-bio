#!/bin/bash
# ============================================================================
# dgx1_gpu_smoke.sh — the dgx1 half of sif_delivery, PI-attended per Q-006.
#
# WHAT THIS ESTABLISHES, AND WHY IT IS NOT ALREADY KNOWN. Cycle-007 observed
# that gromacs.sif OPENS and READS under dgx1's singularity 3.5.2 (`inspect`
# rc 0, `exec ls` rc 0) and that sm_70 SASS exists in the library. Those are two
# facts, and they must not be allowed to read as one: nothing had ever EXECUTED
# on a dgx1 GPU. The cross-cluster check took no --nv and requested no device,
# by construction. This script closes exactly that gap.
#
# WHY IT IS THE FIRST TEST OF THE TWO-ARCHITECTURE BUILD. banyan's H100 is
# compute capability 9.0, so job 32/33 exercised the sm_90 half of
# GMX_CUDA_TARGET_SM="70;90" only. dgx1's V100s are compute capability 7.0, so
# this is the first run that exercises the sm_70 half — the half that justifies
# building for two architectures at all. A JIT fallback from PTX would also
# produce a working run, which is why the md.log GPU block is captured verbatim
# rather than inferred from a zero exit.
#
# UNLIKE THE DOCKER PATH, THIS GENUINELY RUNS INSIDE THE JOB'S CGROUP.
# `docker build`/`docker run` are executed by the daemon, outside the
# allocation, so wrapping them in Slurm bought courtesy but not isolation. A
# `singularity exec` runs as the job's own process, so the allocation is real
# here and the device pin is enforced.
#
# THREAD COUNT IS PINNED TO 8, NOT TAKEN FROM SLURM_CPUS_PER_TASK, so this run
# is like-for-like with the banyan .sif baseline it is compared against. A
# 2652-atom system on 64 OpenMP threads would be a different run.
#
# READ-ONLY WITH RESPECT TO THE ARTIFACT: the .sif is mounted, never rewritten.
# Nothing is built and no image is deleted. The only writes are this job's own
# run directory and evidence file under the shared home.
# ============================================================================
set -uo pipefail

WORK=/home/eliott/p53mdm2
TEMPLATES="$WORK/smoke_system"
SIF="$WORK/gromacs.sif"
RUNDIR="$WORK/smoke_run_dgx1_sif"
BANYAN_BASELINE="$WORK/smoke_run_sif/min.log"   # same NFS export, written on banyan
SENTINEL="$WORK/DGX1_SMOKE_STATUS"
OUT="$WORK/dgx1_gpu_smoke_out.txt"
SMOKE_NTOMP=8
REQUIRED_CC=7.0                                  # V100 — the sm_70 half

rc=0
note() { echo; echo "======== $* ========"; }

exec > >(tee "$OUT") 2>&1

note "dgx1_gpu_smoke.sh starting $(date -Is)  job=${SLURM_JOB_ID:-none}"
echo "host: $(hostname)"
echo "singularity: $(singularity --version)"
echo "sif: $SIF"
echo "sif_sha256: $(sha256sum "$SIF" | awk '{print $1}')"
echo "sif_bytes: $(stat -c %s "$SIF")"

# --- STEP 1: resolve the allocated device the sanctioned way -----------------
note "STEP 1: device resolution"
# Slurm can rewrite CUDA_VISIBLE_DEVICES to allocation-relative indices, so
# SLURM_JOB_GPUS is the authority and CUDA_VISIBLE_DEVICES is the last resort.
DEV=""
for v in SLURM_JOB_GPUS SLURM_STEP_GPUS; do
    val="${!v:-}"; [ -n "$val" ] && { DEV="${val%%,*}"; echo "device_source: $v=$val"; break; }
done
[ -n "$DEV" ] || { DEV="${CUDA_VISIBLE_DEVICES%%,*}"; echo "device_source: CUDA_VISIBLE_DEVICES (may be relative)"; }
echo "resolved_global_gpu: ${DEV:-none}"
nvidia-smi --query-gpu=index,name,compute_cap,memory.used,memory.total --format=csv,noheader

# --- STEP 2: does the container see a real driver on dgx1? ------------------
note "STEP 2: gmx --version under singularity exec --nv"
# The decisive field is CUDA driver. Cycle-007 saw 0.0 here WITHOUT --nv and
# with no device, which was the expected driverless reading and carried no
# information about GPU capability. A non-zero value is the falsification.
singularity exec --nv "$SIF" /opt/gromacs/bin/gmx --version 2>&1 \
    | grep -E 'GROMACS version|Precision|GPU support|SIMD instructions|CUDA driver|CUDA runtime'
ver_rc="${PIPESTATUS[0]}"
echo "version_exit: $ver_rc"
[ "$ver_rc" -eq 0 ] || rc=1

# --- STEP 3: run the identical smoke system ---------------------------------
note "STEP 3: identical smoke system on a dgx1 V100"
rm -rf "$RUNDIR"; mkdir -p "$RUNDIR"
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
mdrun_rc="${PIPESTATUS[0]}"
echo "mdrun_exit: $mdrun_rc"
[ "$mdrun_rc" -eq 0 ] || rc=1

# --- STEP 4: the GPU block, verbatim ----------------------------------------
note "STEP 4: GPU evidence from the dgx1 md.log"
# A zero exit does NOT prove device execution: GROMACS falls back to CPU
# nonbondeds with only a note. These lines are the proof.
grep -E 'GPUs detected|compute cap|GPU selected|Using GPU .* nonbonded|PME tasks will do' \
    "$RUNDIR/md.log" 2>/dev/null || { echo "NOT FOUND — no GPU block in the dgx1 md.log"; rc=1; }

note "STEP 4b: nonbonded kernel timing — did work reach the device?"
grep -E 'Nonbonded F .*kernel|Launch GPU ops|Wait GPU' "$RUNDIR/md.log" 2>/dev/null \
    || echo "no GPU kernel timing rows matched (inspect md.log manually)"

# --- STEP 5: cross-cluster parity against the banyan .sif run ---------------
note "STEP 5: cross-cluster energy parity (dgx1 V100 vs banyan H100, same .sif)"
# Both runs used the SAME image on the SAME shared home with the same inputs and
# the same thread count. The only moving part is the GPU architecture, so this
# is a direct test that the sm_70 and sm_90 code paths agree on physics.
B_PE=$(grep -m1 'Potential Energy' "$BANYAN_BASELINE" 2>/dev/null | awk '{print $4}')
D_PE=$(grep -m1 'Potential Energy' "$RUNDIR/min.log" 2>/dev/null | awk '{print $4}')
echo "banyan_h100_min_potential_energy: ${B_PE:-unavailable}"
echo "dgx1_v100_min_potential_energy:   ${D_PE:-unavailable}"
REL=""
if [ -n "${B_PE:-}" ] && [ -n "${D_PE:-}" ]; then
    REL=$(awk -v a="$B_PE" -v b="$D_PE" 'BEGIN{d=(a-b); if(d<0)d=-d; print (a==0)?d:d/((a<0)?-a:a)}')
    echo "relative_difference: $REL"
    awk -v r="$REL" 'BEGIN{exit !(r<=1e-3)}' \
        && echo "GATE_CROSSCLUSTER_ENERGY=PASS (<=1e-3)" \
        || { echo "GATE_CROSSCLUSTER_ENERGY=FAIL"; rc=1; }
else
    echo "GATE_CROSSCLUSTER_ENERGY=INCONCLUSIVE (a baseline log is missing)"; rc=1
fi

# --- machine-parseable summary ----------------------------------------------
# Explicit keys so a test can assert over this without scraping human prose.
# The downstream test module depends on these names — do not rename them.
note "SUMMARY"
CC_OBS=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | sort -u | paste -sd';' -)
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | sort -u | paste -sd';' -)
DRIVER=$(grep -m1 'CUDA driver' "$RUNDIR/md.log" 2>/dev/null | sed 's/.*CUDA driver: *//' | tr -d ' ')
RUNTIME=$(grep -m1 'CUDA runtime' "$RUNDIR/md.log" 2>/dev/null | sed 's/.*CUDA runtime: *//' | tr -d ' ')
NDET=$(grep -m1 'GPUs detected' "$RUNDIR/md.log" 2>/dev/null | grep -oE '[0-9]+' | head -1)
LOGCC=$(grep -m1 'compute cap' "$RUNDIR/md.log" 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
echo "--- SUMMARY ---"
echo "CLUSTER=dgx1"
echo "SINGULARITY_VERSION=$(singularity --version)"
echo "GPU_NAME=${GPU_NAME:-NONE}"
echo "GPU_COMPUTE_CAP_NVIDIASMI=${CC_OBS:-NONE}"
echo "GPU_COMPUTE_CAP_MDLOG=${LOGCC:-NONE}"
echo "REQUIRED_COMPUTE_CAP=$REQUIRED_CC"
echo "SM_ARCH_EXERCISED=sm_70"
echo "CUDA_DRIVER=${DRIVER:-NONE}"
echo "CUDA_RUNTIME=${RUNTIME:-NONE}"
echo "GPUS_DETECTED=${NDET:-NONE}"
echo "NONBONDED_ON_GPU=$(grep -qE 'Using GPU .* nonbonded' "$RUNDIR/md.log" 2>/dev/null && echo yes || echo no)"
echo "MDRUN_EXIT=$mdrun_rc"
echo "VERSION_EXIT=$ver_rc"
echo "DGX1_MIN_POTENTIAL_ENERGY=${D_PE:-NONE}"
echo "BANYAN_MIN_POTENTIAL_ENERGY=${B_PE:-NONE}"
echo "CROSSCLUSTER_ENERGY_REL=${REL:-NONE}"
echo "SIF_SHA256=$(sha256sum "$SIF" | awk '{print $1}')"
echo "--- END SUMMARY ---"

printf 'stage=dgx1_gpu_smoke\nexit=%s\nmdrun_exit=%s\nsif_sha256=%s\nfinished=%s\n' \
    "$rc" "$mdrun_rc" "$(sha256sum "$SIF" 2>/dev/null | awk '{print $1}')" "$(date -Is)" > "$SENTINEL"

note "RESULT: rc=$rc"
exit "$rc"
