#!/bin/bash
# ============================================================================
# p53_md_submit.sbatch — HOST SIDE of the first p53-MDM2 MD run (dgx1 V100 or banyan H100).
#
# STATUS: first executed 2026-10-20 on banyan H100, job 119, rc=0 (evidence
# p53_md_banyan_job119.txt, manifest seq 18). Not yet run on dgx1 V100.
#
# WHAT THIS ESTABLISHES. That the 1YCR complex builds into a solvated,
# neutralised AMBER99SB-ILDN/TIP3P system inside the one container we have,
# minimises, equilibrates (NVT 100 ps, NPT 100 ps, heavy atoms restrained) and
# runs 100 ps of NPT production on a V100 — with nonbonded AND PME on the GPU,
# proven from md.log rather than inferred from exit 0 (GROMACS falls back to
# the CPU with only a note). SHORT ON PURPOSE: INBOX 2026-09-25 says to start
# short and read the md.log GPU block before anything long. Expected wall time
# is a few minutes; the 30 min cap is a ceiling, not an estimate.
#
# WHERE THE PARAMETERS COME FROM. Nothing physical is set here or in
# p53_md_run.sh. prep.env and <stage>.mdp are EMITTED FROM THE USD STAGE
# (output/p53_mdm2_md_setup_gromacs.usda) by templates/gromacs_deck.py, and
# tests/test_md_gromacs_deck.py fails if the committed copies are stale. Their
# sha256 is recorded below so the evidence names the exact deck that ran.
#
# STAGING (coordinator, before submit): copy examples/p53_mdm2/cluster/p53_md/
# to $WORK/p53_md/ and data/structures/1ycr.pdb into it. DECK, PDB and SIF can
# be overridden from the job environment.
#
# PATTERN: dgx1_gpu_smoke.sh / convert_verify.sh step 3 — device resolution
# from SLURM_JOB_GPUS, inputs bound read-only, a per-run run_p53md_<UTC>/,
# threads pinned to 8, tee to an out file, a STATUS sentinel, and a
# machine-parseable --- SUMMARY --- block.
# ============================================================================
#SBATCH --job-name=p53md-short
#SBATCH --partition=all
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00
#SBATCH --output=p53md-short-%j.out
set -uo pipefail

WORK=/home/eliott/p53mdm2
DECK="${DECK:-$WORK/p53_md}"
PDB="${PDB:-$DECK/1ycr.pdb}"
SIF="${SIF:-$WORK/gromacs-2025.3-cuda12.9-sm70_90.sif}"
RUN="$WORK/run_p53md_$(date -u +%Y%m%dT%H%M%SZ)"
RUNDIR="$RUN/work"
SENTINEL="$RUN/P53_MD_STATUS"
OUT="$RUN/p53_md_out.txt"
NTOMP=8                       # pinned, like-for-like with the smoke runs
CLUSTER="$(hostname -s)"
case "$CLUSTER" in banyan) DEFAULT_CC=9.0 ;; *) DEFAULT_CC=7.0 ;; esac
REQUIRED_CC="${REQUIRED_CC:-$DEFAULT_CC}"   # dgx1 V100 = 7.0, banyan H100 = 9.0
mkdir -p "$RUNDIR"

rc=0
note() { echo; echo "======== $* ========"; }
sha() { sha256sum "$1" 2>/dev/null | awk '{print $1}'; }

exec > >(tee "$OUT") 2>&1

note "p53_md_submit.sbatch starting $(date -Is)  job=${SLURM_JOB_ID:-none}"
echo "host: $(hostname)"
echo "singularity: $(singularity --version)"
echo "sif: $SIF"
echo "deck: $DECK"
echo "pdb: $PDB"
for f in "$SIF" "$PDB" "$DECK/prep.env" "$DECK/p53_md_run.sh"; do
    [ -f "$f" ] || { echo "FATAL: missing input $f"; rc=1; }
done
if [ "$rc" -ne 0 ]; then
    printf 'stage=p53_md\nexit=1\nreason=missing_input\nrun_dir=%s\nfinished=%s\n' "$RUN" "$(date -Is)" > "$SENTINEL"
    exit 1
fi

# --- STEP 1: device ----------------------------------------------------------
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

# --- STEP 2: driver visible in the container ---------------------------------
note "STEP 2: gmx --version under singularity exec --nv"
singularity exec --nv "$SIF" /opt/gromacs/bin/gmx --version 2>&1 \
    | grep -E 'GROMACS version|Precision|GPU support|SIMD instructions|CUDA driver|CUDA runtime'
ver_rc="${PIPESTATUS[0]}"
echo "version_exit: $ver_rc"
[ "$ver_rc" -eq 0 ] || rc=1

# --- STEP 3: the deck that is about to run -----------------------------------
note "STEP 3: input digests"
echo "pdb_sha256: $(sha "$PDB")"
for f in "$DECK"/prep.env "$DECK"/*.mdp "$DECK"/p53_md_run.sh; do
    echo "deck_sha256 $(basename "$f"): $(sha "$f")"
done
sed -n '/^[A-Z_]*=/p' "$DECK/prep.env"

# --- STEP 4: build + run inside the container ---------------------------------
note "STEP 4: prep + EM + NVT + NPT + production (container side)"
singularity exec --nv \
    -B "$DECK:/deck:ro" -B "$PDB:/input/1ycr.pdb:ro" -B "$RUNDIR:/work" \
    --pwd /work "$SIF" \
    bash /deck/p53_md_run.sh /deck /input/1ycr.pdb /work "$NTOMP"
run_rc=$?
echo "container_exit: $run_rc"
[ "$run_rc" -eq 0 ] || rc=1

# --- STEP 5: GPU block, verbatim, per dynamics stage --------------------------
note "STEP 5: GPU evidence from each dynamics md.log"
# A zero exit does NOT prove device execution. These lines are the proof.
for s in nvt npt md; do
    echo "--- $s.log ---"
    grep -E 'GPUs detected|compute cap|GPU selected|Using GPU .* nonbonded|PME tasks will do|on the GPU' \
        "$RUNDIR/$s.log" 2>/dev/null || { echo "NOT FOUND — no GPU block in $s.log"; rc=1; }
done
note "STEP 5b: production kernel timing — did work reach the device?"
grep -E 'Nonbonded F .*kernel|Launch GPU ops|Wait GPU|PME GPU' "$RUNDIR/md.log" 2>/dev/null \
    || echo "no GPU kernel timing rows matched (inspect md.log manually)"
grep -E '^ *(Core t|Time:|Performance:)' "$RUNDIR/md.log" 2>/dev/null || true

# --- machine-parseable summary ----------------------------------------------
note "SUMMARY"
CC_OBS=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | sort -u | paste -sd';' -)
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | sort -u | paste -sd';' -)
LOGCC=$(grep -m1 'compute cap' "$RUNDIR/md.log" 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
DRIVER=$(grep -m1 'CUDA driver' "$RUNDIR/md.log" 2>/dev/null | sed 's/.*CUDA driver: *//' | tr -d ' ')
echo "--- SUMMARY ---"
echo "CLUSTER=$CLUSTER"
echo "SYSTEM=p53-MDM2 1YCR"
echo "SINGULARITY_VERSION=$(singularity --version)"
echo "GPU_NAME=${GPU_NAME:-NONE}"
echo "GPU_COMPUTE_CAP_NVIDIASMI=${CC_OBS:-NONE}"
echo "GPU_COMPUTE_CAP_MDLOG=${LOGCC:-NONE}"
echo "REQUIRED_COMPUTE_CAP=$REQUIRED_CC"
echo "CUDA_DRIVER=${DRIVER:-NONE}"
echo "NTOMP=$NTOMP"
echo "VERSION_EXIT=$ver_rc"
echo "CONTAINER_EXIT=$run_rc"
grep -vE '^CONTAINER_EXIT=' "$RUNDIR/summary.txt" 2>/dev/null || echo "CONTAINER_SUMMARY=NONE"
echo "PDB_SHA256=$(sha "$PDB")"
echo "SIF_SHA256=$(sha "$SIF")"
echo "RUN_DIR=$RUN"
echo "--- END SUMMARY ---"

printf 'stage=p53_md\nexit=%s\ncontainer_exit=%s\nsif=%s\nsif_sha256=%s\nrun_dir=%s\nfinished=%s\n' \
    "$rc" "$run_rc" "$SIF" "$(sha "$SIF")" "$RUN" "$(date -Is)" > "$SENTINEL"

note "RESULT: rc=$rc"
exit "$rc"
