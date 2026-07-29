# CUDA SASS Portability Audit

**Goal**: Turn `GMX_CUDA_TARGET_SM="70;90"` — the entire cross-cluster portability claim — from an asserted build flag into observed SASS inside the image, using `cuobjdump` in a plain container with no GPU, no Slurm and no container toolkit involved.
**Pre-conditions**:
- [x] `docker image inspect gromacs-p53mdm2:latest` succeeds on banyan
- [x] The image was configured with `GMX_CUDA_TARGET_SM="70;90"` and `GMX_CUDA_TARGET_COMPUTE="90"` per both recipes
- [ ] An attended session, since even a short `docker run --rm` is a cluster-mutating action under Q-006
**Success Gates**:
- ⬜ `[run]` `cuobjdump -lelf` output in the committed evidence names **both** `sm_70` and `sm_90`, proving real SASS rather than JIT-only PTX
- ⬜ `[run]` `cuobjdump -lptx` shows `sm_90` only, matching `GMX_CUDA_TARGET_COMPUTE="90"` — recorded as the intended asymmetry, not reported as a defect
- ⬜ `[static]` `ldd` and `readelf -d` output for the `gmx` binary is captured, settling whether it carries a direct `libcuda.so.1` dependency
- ⬜ `[static]` Every evidence file is tracked by git, verified with `git check-ignore`, since `.gitignore` swallows `*.log`
**References**: [R10 cluster state refresh](../../../__reports__/p53-mdm2/10-cluster_state_refresh_v0.md) — the GPU architectures the SM targets must cover; [R01 MD reproducibility survey](../../../__reports__/p53-mdm2/01-md_reproducibility_survey_v0.md) — why a build's actual compiled targets are a reproducibility datum, not a detail

## Step 1: Write the audit script
**Goal**: Produce a repeatable, parseable audit that runs entirely inside the container and needs no GPU.
**Implementation Logic**:
The script must locate the CUDA-bearing object itself rather than hardcoding a path, because the GROMACS install layout varies by version — glob the installed library directory for the libgromacs shared object. Run cuobjdump in both ELF and PTX listing modes against it, plus ldd and readelf on the gmx binary and the gmx version block for correlation. Emit a machine-parseable summary with explicit keys so a test can assert over it without scraping human prose; the downstream test module depends on that stability. Keep it read-only inside the container, and exit non-zero when the library cannot be found so a silently empty result is impossible.
**Deliverables**: `examples/p53_mdm2/cluster/sass_audit.sh` — locates libgromacs by glob; emits keys `SM_ELF=`, `SM_PTX=`, `LIBCUDA_DT_NEEDED=` and a `GMX_VERSION_BLOCK` section; exits non-zero when the library is absent
**Consistency Checks**: `sh -n examples/p53_mdm2/cluster/sass_audit.sh` (expected: PASS)
**Commit**: `feat(p53-mdm2): CPU-only cuobjdump SASS audit script for the GROMACS image`

## Step 2: Execute on banyan and capture verbatim
**Goal**: Run the audit against the real image and commit its output as evidence carrying provenance.
**Implementation Logic**:
Run via a short docker run with the remove flag on banyan and no GPU request — this needs neither the nvidia runtime nor Slurm, which is exactly why it is a separate leaf from the GPU smoke test and the cheapest check available. Capture stdout and stderr verbatim to a dated evidence file whose extension is not the ignored log extension. Record a manifest line carrying the file digest, capture timestamp, cluster, exact command and image id, so evidence can be distinguished from an edited copy later. If either SM target is missing, stop and report rather than proceeding: a wrong-SASS image must be rebuilt, and any conversion or GPU work done first would be discarded.
**Deliverables**: `examples/p53_mdm2/cluster/evidence/sass_audit_banyan.txt` — verbatim cuobjdump, ldd, readelf and gmx version output; and `examples/p53_mdm2/cluster/evidence/manifest.jsonl` — one object with keys sha256, captured_on, cluster, command, image_id
**Consistency Checks**: `git check-ignore -q examples/p53_mdm2/cluster/evidence/sass_audit_banyan.txt` (expected: FAIL)
**Commit**: `docs(p53-mdm2): captured sm_70 and sm_90 SASS evidence from banyan`

## Step 3: Gate the evidence in the test suite
**Goal**: Make the SASS and pin claims machine-checked offline, so they cannot silently rot when a version is bumped.
**Implementation Logic**:
Add the first test module that reads cluster artifacts, closing the documented gap that no test touches container work. Its highest-value assertion is not the SASS list but recipe-versus-evidence consistency: parse the SM targets, SIMD flag, base image tag and GROMACS version out of both recipe files, assert the twins agree with each other, then assert they agree with the captured output. That mechanises the sync obligation the runbook concedes is only social, runs fully offline, and goes red the moment a pin moves without re-capture. Also assert manifest integrity, that each recorded digest matches the file on disk, which is this evidence class's real failure mode. The harness has no skip concept and reads the passed field as a bool, so the module must return zero rows when the evidence directory is absent or the suite goes permanently red; it therefore lands in the same commit as the evidence, never before.
**Deliverables**: `examples/p53_mdm2/tests/test_container_evidence.py` — functions `run`, `_load_manifest`, `_parse_summary_block`, `_recipe_pins`, constant `_REQUIRED_SM`, returning zero rows when evidence is absent; and `examples/p53_mdm2/tests/run_tests.py` registering layer `container-evidence`
**Consistency Checks**: `PYTHONPATH="$PYTHONPATH:$(pwd)/examples" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/tests/run_tests.py` (expected: PASS)
**Commit**: `test(p53-mdm2): offline gates over captured container evidence and recipe pins`
