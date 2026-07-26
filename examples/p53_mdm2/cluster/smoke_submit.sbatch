#!/bin/bash
# ============================================================================
# smoke_submit.sbatch — 1-GPU smoke test for the GROMACS container.
#
# STATUS: TEMPLATE / SCAFFOLDING ONLY. This has NOT been submitted to any
#         scheduler. Running it (`sbatch smoke_submit.sbatch`) mutates shared
#         Slurm + GPU state on a beta cluster and is a PI-GATED step. Do NOT
#         submit unattended. See ./README.md for the full gated sequence.
#
# WHAT IT DOES (minimal, on purpose):
#   1. Prints `gmx --version` on the GPU node (proves the .sif runs there and
#      GPU support is compiled in — the build-time %test could not see a GPU).
#   2. Runs a trivial energy minimization on a tiny built-in-ish system to
#      exercise `gmx mdrun` on ONE GPU end-to-end.
# Keep it short (a few minutes). This is a sanity check, NOT a production run
# and NOT the real p53-MDM2 system (decks are a downstream step — see README).
#
# INVOCATION MODEL: Slurm's submit_job wraps GPU jobs as `singularity exec --nv`
# [doc: report 07]. This script calls singularity explicitly so it is correct
# whether launched via raw `sbatch` on a login shell or via the submit_job tool.
# ============================================================================

# ---- Slurm directives -------------------------------------------------------
#SBATCH --job-name=gmx-smoke
#SBATCH --partition=all              # <PLACEHOLDER> both clusters expose the "all" partition [live: report 07]. Confirm per cluster.
#SBATCH --gres=gpu:1                 # exactly ONE GPU. Same syntax on banyan (Slurm 22.05.2) and dgx1 (Slurm 23.11.4) [live: report 07].
#SBATCH --cpus-per-task=8            # <PLACEHOLDER> modest CPU count for the tiny system; tune per node.
#SBATCH --time=00:15:00              # 15 min hard cap; smoke test should finish in ~minutes.
#SBATCH --output=gmx-smoke-%j.out    # stdout/stderr into the submit dir (shared home).
# --- Account/QOS: NOT required on either cluster (accounting is OFF) [live: report 07]. ---
# If a future policy adds accounting, uncomment and fill:
# #SBATCH --account=<PLACEHOLDER_ACCOUNT>
# #SBATCH --qos=<PLACEHOLDER_QOS>
#
# ---- Cluster-specific notes (Slurm version skew) ----------------------------
# banyan: Slurm 22.05.2, 2x H100 NVL (sm_90). Has the Docker daemon + singularity
#         4.2.2 used to build the .sif. BUT SEE THE GPU-CONTENTION WARNING BELOW —
#         banyan is no longer the obvious first target.
# dgx1:   Slurm 23.11.4, 8x V100 (sm_70), singularity 3.5.2 (2019). `--gres=gpu:1`
#         is identical. The RISK on dgx1 is SIF-format skew (built under 4.2.2,
#         run under 3.5.2) — see README "SIF version skew". If the .sif fails to
#         open on 3.5.2, that is the skew, not this script.
#         dgx1 was FULLY IDLE at the last refresh (8 free V100s, no processes), so
#         it is the contention-free option AND the harder portability target.
#
# ---- !! MANDATORY PRE-FLIGHT ON BANYAN: Slurm's GPU view diverges from reality --
# At the last read-only refresh, banyan GPU 0 held ANOTHER USER'S vLLM process
# consuming 86061 MiB of 95830 MiB, while Slurm reported the node IDLE with an
# EMPTY AllocTRES. The process is unscheduled, so Slurm does not know it exists and
# can hand a `--gres=gpu:1` job the already-full card (~9.7 GB left) -> contention
# or OOM. GPU 1 was fully free.
#   [source: __reports__/p53-mdm2/10-cluster_state_refresh_v0.md §7
#            (nvidia-smi vs scontrol, cycle-006, commit c8f2cc2)]
# UNRESOLVED: it is NOT known whether Slurm actually assigns GPU 0 — no job was
# submitted to observe which device it hands out, and it is unknown whether the
# site applies any out-of-band GRES exclusion for GPU 0. So do not assume either
# way; RUN THE CHECK. Occupancy is point-in-time and already changed once in 6 days.
# BEFORE SUBMITTING, on the target cluster:
#   nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv
#   sinfo -o '%T %C %G'      # compare Slurm's view against the above
# If GPU 0 is still occupied: prefer the free GPU (see the guard in Step 1 below,
# and CUDA_VISIBLE_DEVICES if you must force it — GPU isolation here is soft), or
# smoke-test on dgx1 instead.

set -euo pipefail

# ---- Paths (ALL placeholders — edit before the PI-approved submit) ----------
# The .sif and I/O live on the shared NFS home (ts2:/export/home), visible from
# BOTH clusters, so these paths are the same regardless of which cluster runs.
SIF=/home/eliott/p53mdm2/gromacs.sif          # <PLACEHOLDER> path to the built .sif
WORKDIR=/home/eliott/p53mdm2/smoke            # <PLACEHOLDER> scratch/output dir on shared home
INDIR=${WORKDIR}/in                           # tiny input system goes here
OUTDIR=${WORKDIR}/out                         # mdrun output lands here

mkdir -p "${INDIR}" "${OUTDIR}"

echo "=== Node / GPU visible to this job ==="
nvidia-smi -L || echo "WARN: nvidia-smi not on PATH of the batch shell (still fine if --nv passes the GPU into the container)"

# ---- In-job GPU occupancy guard ---------------------------------------------
# Slurm may hand us a GPU that another (unscheduled) process already fills —
# proved on banyan, where GPU 0 held 86 GB of a 95.8 GB card while Slurm reported
# the node IDLE [source: __reports__/p53-mdm2/10-cluster_state_refresh_v0.md §7].
# This is a WARNING, not a hard failure: the tiny smoke system needs very little
# memory, so a contended card may still work — but if mdrun OOMs or crawls, this
# output is the first place to look. Non-fatal by design (`|| true` throughout).
echo "=== GPU occupancy as seen from inside the job ==="
echo "    (CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-<unset>} — what Slurm gave us)"
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu \
           --format=csv,noheader 2>/dev/null || echo "    (query unavailable)"
echo "=== Foreign processes on the visible GPU(s) ==="
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory \
           --format=csv,noheader 2>/dev/null || echo "    (query unavailable)"
# Flag any visible card that is more than ~50% consumed before we even start.
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null \
  | awk -F', *' '$3 > 0 && ($2/$3) > 0.5 {
        printf "WARN: GPU %s is already %.0f%% full (%s of %s MiB) — foreign process likely. Expect contention.\n", $1, 100*$2/$3, $2, $3
    }' || true
# To pin a specific card manually (soft isolation — see README gated step 3):
#   export CUDA_VISIBLE_DEVICES=1     # e.g. banyan's free GPU

echo "=== Step 1: gmx --version inside the container (on the GPU node) ==="
singularity exec --nv "${SIF}" gmx --version

# ---- Step 2: trivial energy minimization -----------------------------------
# The absolute-minimum end-to-end GPU exercise. This template assumes a tiny
# prepared system (conf.gro + topol.top + a min.mdp) has been staged into
# ${INDIR}. Preparing even a tiny system is itself a (small) deck-building task;
# if no system is staged, Step 1 alone (gmx --version on the GPU node) is a valid
# minimal smoke result and Step 2 can be skipped.
#
# [assumption] filenames below (conf.gro/topol.top/min.mdp) are placeholders for
# whatever tiny test system the PI/operator stages; they are NOT the p53-MDM2
# system (that deck — solvation/ions/parameterization/mdp — is a downstream step).
if [[ -f "${INDIR}/conf.gro" && -f "${INDIR}/topol.top" && -f "${INDIR}/min.mdp" ]]; then
    echo "=== Step 2: grompp + 1-GPU energy minimization ==="
    singularity exec --nv \
        -B "${INDIR}:/data/in" \
        -B "${OUTDIR}:/data/out" \
        "${SIF}" \
        gmx grompp -f /data/in/min.mdp -c /data/in/conf.gro -p /data/in/topol.top \
                   -o /data/out/min.tpr -maxwarn 1

    singularity exec --nv \
        -B "${OUTDIR}:/data/out" \
        "${SIF}" \
        gmx mdrun -deffnm /data/out/min -nb gpu -ntmpi 1 -ntomp "${SLURM_CPUS_PER_TASK:-8}"
    echo "=== Smoke minimization complete. Check ${OUTDIR}/min.log for GPU detection. ==="
else
    echo "=== Step 2 SKIPPED: no tiny test system staged in ${INDIR}. ==="
    echo "    Step 1 (gmx --version on GPU node) is the minimal smoke result."
fi

echo "=== Smoke test finished. ==="
