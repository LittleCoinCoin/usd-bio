#!/bin/bash
# ============================================================================
# sass_audit.sh — prove which CUDA architectures the built GROMACS actually
# carries, from INSIDE the container. No GPU, no Slurm, no container toolkit.
#
# WHY THIS EXISTS: `gmx --version` reports "GPU support: CUDA" but does NOT
# list the compiled target architectures. So `GMX_CUDA_TARGET_SM="70;90"` — the
# entire cross-cluster portability claim (V100/sm_70 on dgx1, H100/sm_90 on
# banyan) — is an asserted build flag, not an observed property. cuobjdump
# settles it by reading the fat binary.
#
# HOW TO RUN (banyan, CPU-only, seconds):
#   docker run --rm -v "$PWD/sass_audit.sh:/audit.sh:ro" \
#       gromacs-p53mdm2:latest bash /audit.sh
#
# WHAT ELF vs PTX MEANS HERE — read before interpreting the output:
#   * ELF entries are real, pre-compiled SASS for a specific architecture. An
#     arch present in ELF runs directly.
#   * PTX entries are portable intermediate code, JIT-compiled by the driver at
#     load time. An arch present ONLY in PTX still runs, but pays a JIT cost and
#     depends on the driver being new enough.
#   The recipes set GMX_CUDA_TARGET_SM="70;90" (SASS for both) and
#   GMX_CUDA_TARGET_COMPUTE="90" (PTX for 90 only, so future GPUs can JIT). So
#   the EXPECTED result is: ELF contains sm_70 AND sm_90; PTX contains sm_90
#   only. PTX lacking sm_70 is intentional, not a defect.
#
# Output is a parseable summary block; `tests/test_container_evidence.py`
# asserts over the SM_ELF / SM_PTX / LIBCUDA_DT_NEEDED keys, so do not rename
# them without updating that module.
# ============================================================================
set -uo pipefail

GMX_BIN=/opt/gromacs/bin/gmx
FAILED=0

echo "=== sass_audit.sh ==="
echo "audit_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "container_id: $(cat /etc/hostname 2>/dev/null || echo unknown)"
echo

# --- locate the CUDA-bearing object -----------------------------------------
# Glob rather than hardcode: the GROMACS install layout (lib vs lib64, and the
# libgromacs suffix) varies by version and build flags.
LIB=""
for cand in /opt/gromacs/lib*/libgromacs*.so*; do
    # Skip symlinks so cuobjdump reads the real object once, not N aliases.
    if [ -f "$cand" ] && [ ! -L "$cand" ]; then LIB="$cand"; break; fi
done
if [ -z "$LIB" ]; then
    echo "FATAL: no libgromacs shared object found under /opt/gromacs/lib*" >&2
    echo "       (searched: /opt/gromacs/lib*/libgromacs*.so*)" >&2
    ls -la /opt/gromacs/lib* 2>&1 >&2 || true
    exit 2
fi
echo "library: $LIB"
echo "library_bytes: $(stat -c %s "$LIB" 2>/dev/null || echo unknown)"
echo

command -v cuobjdump >/dev/null 2>&1 || {
    echo "FATAL: cuobjdump not on PATH (expected in a CUDA -devel image)" >&2
    exit 2
}
echo "cuobjdump: $(command -v cuobjdump)"
echo

# --- architectures actually present ------------------------------------------
# cuobjdump emits one record per kernel per arch, which for libgromacs is
# thousands of lines. Reduce to the unique arch set (the actual signal) and
# keep the record counts as corroboration that the sets are not empty.
ELF_RAW="$(cuobjdump -lelf "$LIB" 2>/dev/null || true)"
PTX_RAW="$(cuobjdump -lptx "$LIB" 2>/dev/null || true)"

SM_ELF="$(printf '%s\n' "$ELF_RAW" | grep -oE 'sm_[0-9]+[a-z]?' | sort -u | paste -sd';' -)"
SM_PTX="$(printf '%s\n' "$PTX_RAW" | grep -oE 'sm_[0-9]+[a-z]?|compute_[0-9]+[a-z]?' | sort -u | paste -sd';' -)"
ELF_N="$(printf '%s\n' "$ELF_RAW" | grep -c 'ELF' || true)"
PTX_N="$(printf '%s\n' "$PTX_RAW" | grep -c 'PTX' || true)"

# --- driver-library dependency ----------------------------------------------
# Settles whether the gmx binary carries a direct DT_NEEDED on libcuda.so.1.
# A -devel base ships libcuda only as a link-time stub under lib64/stubs, which
# is not on the loader path — so a hard dependency here would mean `gmx
# --version` cannot run without a host driver bind-mounted in.
if readelf -d "$GMX_BIN" 2>/dev/null | grep -q 'libcuda\.so\.1'; then
    LIBCUDA_DT_NEEDED=yes
else
    LIBCUDA_DT_NEEDED=no
fi

# --- summary (machine-parseable; keys are a contract with the test module) ---
echo "--- SUMMARY ---"
echo "SM_ELF=${SM_ELF:-NONE}"
echo "SM_PTX=${SM_PTX:-NONE}"
echo "ELF_RECORDS=${ELF_N:-0}"
echo "PTX_RECORDS=${PTX_N:-0}"
echo "LIBCUDA_DT_NEEDED=${LIBCUDA_DT_NEEDED}"

# Assert the portability claim rather than leaving it to the reader.
for want in sm_70 sm_90; do
    case ";${SM_ELF};" in
        *";${want};"*) echo "CHECK_${want}_ELF=present" ;;
        *)             echo "CHECK_${want}_ELF=MISSING"; FAILED=1 ;;
    esac
done
echo "--- END SUMMARY ---"
echo

# --- raw corroboration -------------------------------------------------------
echo "--- GMX_VERSION_BLOCK ---"
"$GMX_BIN" --version 2>&1 || echo "(gmx --version exited non-zero: $?)"
echo "--- END GMX_VERSION_BLOCK ---"
echo
echo "--- LDD_GMX ---"
ldd "$GMX_BIN" 2>&1 || true
echo "--- END LDD_GMX ---"
echo
echo "--- READELF_NEEDED ---"
readelf -d "$GMX_BIN" 2>&1 | grep -E 'NEEDED|RPATH|RUNPATH' || true
echo "--- END READELF_NEEDED ---"
echo
echo "--- CUOBJDUMP_ELF_HEAD ---"
printf '%s\n' "$ELF_RAW" | head -20
echo "--- END CUOBJDUMP_ELF_HEAD ---"
echo
echo "--- CUOBJDUMP_PTX_HEAD ---"
printf '%s\n' "$PTX_RAW" | head -20
echo "--- END CUOBJDUMP_PTX_HEAD ---"

if [ "$FAILED" -ne 0 ]; then
    echo
    echo "RESULT: FAIL — a required SM target is absent from the ELF set." >&2
    echo "        The image must be rebuilt; do NOT convert it to .sif." >&2
    exit 1
fi
echo
echo "RESULT: PASS — both sm_70 and sm_90 present as real SASS."
