# SASS vs JIT Kernel Provenance

**Goal**: Settle by measurement whether the V100 executes embedded `sm_70` SASS or just-in-time compiles PTX — the question that decides whether `GMX_CUDA_TARGET_SM="70;90"` is doing the work the campaign credits it with.
**Pre-conditions**:
- [x] A dgx1 GPU run exists to reason about — `dgx1_gpu_smoke` done, job 28
- [x] Q-008 settled: PTX exists for **both** architectures, so a working V100 run no longer implies the `sm_70` SASS path was taken
- [x] An attended session, per Q-006
**Success Gates**:
- ✅ `[run]` The measurement has a working **positive control**: a `CUDA_FORCE_PTX_JIT=1` run writes a non-empty JIT cache, so an empty cache in the default run is meaningful rather than an artifact of a disabled or misdirected cache — control wrote 9 files / 13486671 bytes
- ✅ `[run]` The default minimisation run writes **zero** JIT cache entries, establishing that the nonbonded kernels are loaded from embedded `sm_70` SASS
- ✅ `[run]` The measurement covers the **full** min+md workload, not only minimisation, so the verdict is not a claim about half the run — full run wrote 4 entries / 47471 bytes on the PME path
- ✅ `[static]` The real `~/.nv/ComputeCache` is never read, written or cleared by the probe, and its size is recorded before and after as evidence of that — 192K both times
- ✅ `[run]` The 4 JIT entries on the PME path are attributed to either `libgromacs` PTX or an independently-shipped CUDA library. Cheapest discriminator: re-run md with `-pme cpu` against a fresh cache — if the entries vanish they belong to the PME/cuFFT path, if they persist they are `libgromacs` — they vanish: job 31 arm D wrote 0 entries / 0 bytes under `-pme cpu` against arm C's 4 entries / 47471 bytes with PME on the GPU, with arm D's own forced-JIT control writing 13 files / 13767931 bytes and the `PME tasks will do all aspects on the GPU` md.log line present in C and absent in D; `PME_JIT_ORIGIN_VERDICT=PME_PATH`
**References**: [R14 cycle-007 findings](../../__reports__/p53-mdm2/14-cycle007_findings_v0.md) — the `SM_PTX` ambiguity that created this question; [sass_portability_audit](../p53-mdm2-v2/p1b_container_runtime/sass_portability_audit.md) — gate 2, whose reworded text this leaf's result bears on

## Step 1: Build a JIT-detecting probe with a positive control
**Goal**: Turn "did it JIT?" from an inference into a measurement that cannot be satisfied by an ambiguous negative.
**Implementation Logic**:
The CUDA driver caches JIT output under `~/.nv/ComputeCache`, so a populated cache after a run is evidence that PTX was compiled. Two traps make the naive check worthless. First, that cache sits on the **shared NFS home**, so entries seen after a dgx1 run may have been written by a banyan run — the probe must redirect `CUDA_CACHE_PATH` to a fresh empty directory rather than inspect the real one, which also guarantees the real cache is left untouched. Second, an empty directory is indistinguishable from a cache that was disabled or pointed somewhere unexpected, which is exactly the class of ambiguity this campaign has been correcting; so pair every default run with a `CUDA_FORCE_PTX_JIT=1` control and require it to write something before believing the negative. Set the variables both bare and with the `SINGULARITYENV_` prefix rather than relying on 3.5.2's pass-through behaviour. Run the full min+md sequence as well as minimisation alone, because the md step additionally places PME on the GPU and loads different modules — a minimisation-only verdict would silently cover half the workload.
**Deliverables**: `examples/p53_mdm2/cluster/dgx1_sass_vs_jit_probe.sh` — functions `run_probe` (default and forced-JIT, minimisation) and `run_full` (full min+md), a SUMMARY block carrying keys `DEFAULT_RUN_JIT_FILES`, `DEFAULT_RUN_JIT_BYTES`, `FORCED_JIT_RUN_JIT_FILES`, `FORCED_JIT_RUN_JIT_BYTES`, `FULLRUN_JIT_FILES`, `FULLRUN_JIT_BYTES`, `SASS_OR_JIT_VERDICT`, and a verdict that reports `INCONCLUSIVE` when the control writes nothing
**Consistency Checks**: `bash -n examples/p53_mdm2/cluster/dgx1_sass_vs_jit_probe.sh` (expected: PASS)
**Commit**: `feat(p53-mdm2): SASS-vs-JIT probe with a forced-JIT positive control`

## Step 2: Execute and record the verdict honestly
**Goal**: Capture the result including the part that does not support a clean story.
**Implementation Logic**:
Submit as a single GPU job and commit the output verbatim. The expected outcome was a clean SASS verdict; the actual outcome is mixed, and the mixed half is the more informative one — recording only the minimisation result would reproduce exactly the over-claim pattern the cycle-007 gate audit was convened to fix. State plainly which claim the evidence supports (nonbonded kernels come from SASS, with a control) and which it does not (the image is not entirely JIT-free on dgx1), and leave the attribution open rather than guessing at cuFFT.
**Deliverables**: `examples/p53_mdm2/cluster/evidence/dgx1_sass_vs_jit.txt` — all three runs with cache counts before and after, real-cache size before and after, and the verdict string; plus an appended `manifest.jsonl` entry
**Consistency Checks**: `git check-ignore -q examples/p53_mdm2/cluster/evidence/dgx1_sass_vs_jit.txt` (expected: FAIL)
**Commit**: `docs(p53-mdm2): sm_70 SASS confirmed for nonbondeds, PME path JITs`

## Step 3: Gate the provenance result
**Goal**: Keep the SASS claim under test, including the control that makes it meaningful.
**Implementation Logic**:
Assert the control fired before asserting the negative — a check that only reads `DEFAULT_RUN_JIT_FILES == 0` would pass in exactly the broken environment where the cache never worked, which is the failure mode this leaf exists to avoid. Assert the real cache was untouched. Deliberately do **not** encode the PME-path count as a fixed expectation: it is an unattributed observation, and hard-coding 4 would bless a number whose cause is unknown and would go red on a benign CUDA library update. Record it in the detail payload instead, so the value travels with the test result without becoming a promise.
**Deliverables**: `examples/p53_mdm2/tests/test_container_evidence.py` — constant `_DGX1_SASS_JIT`, check `sass_not_jit_for_nonbondeds` asserting a non-empty forced-JIT control, a zero-entry default run, and an untouched real cache
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/tests/run_tests.py` (expected: PASS)
**Commit**: `test(p53-mdm2): gate SASS-over-JIT with its positive control`
