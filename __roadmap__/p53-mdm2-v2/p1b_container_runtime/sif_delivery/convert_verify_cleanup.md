# Convert, Verify, Cleanup

**Goal**: Rebuild from the corrected recipe, convert to `gromacs.sif` on the shared home, prove the conversion changed nothing observable, and reclaim the build scratch from the shared node.
**Pre-conditions**:
- [ ] `sass_portability_audit` green — converting an image whose SASS targets are wrong is wasted work
- [ ] `docker_gpu_smoke` green, or explicitly blocked with a recorded reason, so a red `.sif` result is attributable to conversion rather than ambiguous
- [ ] `recipe_evidence_corrections` landed, since the rebuild consumes the corrected recipe
- [ ] `df -h /home` shows at least 30 G free and the Singularity scratch and cache variables are redirected under the shared home
- [ ] An attended session, per Q-006
**Success Gates**:
- ⬜ `[run]` The rebuilt image's SASS summary and version block are identical to the pre-correction capture, giving the campaign its first build-reproducibility datum
- ⬜ `[run]` `gromacs.sif` exists on the shared home with the digests of both the intermediate archive and the image recorded
- ⬜ `[run]` `singularity inspect` reports `GromacsVer 2025.3` and `TargetSM 70;90`, and **no** `BuildStatus` key reaches the delivered artifact
- ⬜ `[run]` The image and the container agree on the GROMACS version, SIMD, CUDA runtime and GPU-support lines, and on minimisation potential energy to within one part in a thousand
- ⬜ `[run]` No archive and no `gromacs-p53mdm2` image remain, and `/` free space is recorded before and after
**References**: [R10 cluster state refresh](../../../../__reports__/p53-mdm2/10-cluster_state_refresh_v0.md) — disk headroom and the scratch-redirection requirement; [R01 MD reproducibility survey](../../../../__reports__/p53-mdm2/01-md_reproducibility_survey_v0.md) — why rebuild equivalence is a reproducibility claim worth capturing

## Step 1: Rebuild and prove build equivalence
**Goal**: Rebuild from the corrected recipe and show the correction changed documentation only, not the compiled artifact.
**Implementation Logic**:
Deleting the build-status label edits the recipe above every expensive compile layer, so a rebuild is forced whether or not we want one. Rather than treat that as a cost, use it: re-run the SASS audit and the version query against the rebuilt image and diff both against the captures taken from the original build. Identical output means the recipe corrections were genuinely documentation-only and the build is reproducible from a clean cache — a claim this campaign, which exists to make MD reproducible, currently cannot make at all. A difference is itself the finding and must stop the leaf rather than be smoothed over.
**Deliverables**: `examples/p53_mdm2/cluster/evidence/rebuild_equivalence.txt` — the rebuilt image's SASS summary and version block alongside a diff against the original captures; plus an appended `manifest.jsonl` entry
**Consistency Checks**: `grep -c 'SM_ELF=' examples/p53_mdm2/cluster/evidence/rebuild_equivalence.txt` (expected: PASS)
**Commit**: `feat(p53-mdm2): rebuild from corrected recipe and prove build equivalence`

## Step 2: Convert to a Singularity image
**Goal**: Produce the actual deliverable on the shared home, where both clusters can reach it.
**Implementation Logic**:
Save the image to an archive under the shared home rather than the root filesystem, then build the Singularity image from that archive. This is the step that makes Route B work at all: converting an archive executes no percent-post section, so it needs neither root nor fakeroot, and the missing subuid mapping that killed the native build path is simply irrelevant here. Record the digest of both the archive and the resulting image, plus the full inspect output including the environment block, so the delivered artifact's provenance is captured at the moment of creation rather than reconstructed later. Confirm the build-status label is genuinely absent from the inspect output — that is the check that the recipe correction reached the artifact.
**Deliverables**: `/home/eliott/p53mdm2/gromacs.sif` on the shared home; `examples/p53_mdm2/cluster/evidence/sif_build.txt` — archive and image digests, full inspect output, environment block
**Consistency Checks**: `grep -c BuildStatus examples/p53_mdm2/cluster/evidence/sif_build.txt` (expected: FAIL)
**Commit**: `feat(p53-mdm2): convert the GROMACS image to gromacs.sif on shared home`

## Step 3: Run the identical smoke system under Singularity
**Goal**: Exercise the converted image with exactly the inputs the Docker run used, so any difference is attributable to conversion alone.
**Implementation Logic**:
Submit a fresh single-GPU job that runs the same water box, the same two mdp files and the same GROMACS invocations, differing only in that the container is entered through Singularity with GPU passthrough instead of the Docker daemon. Using identical inputs is the whole point — a like-for-like comparison is only meaningful if nothing else moved. Note that unlike the Docker path, this one genuinely runs inside the job's cgroup, so Slurm's allocation is real here; that difference is worth recording because it makes this the pattern all future MD runs should follow.
**Deliverables**: `examples/p53_mdm2/cluster/sif_gpu_smoke.sbatch` — single-GPU request, Singularity execution with GPU passthrough, bind mounts for the smoke inputs and outputs; `examples/p53_mdm2/cluster/evidence/sif_gpu_smoke.txt` and `sif_md.log.txt`
**Consistency Checks**: `grep -c 'GPU support' examples/p53_mdm2/cluster/evidence/sif_gpu_smoke.txt` (expected: PASS)
**Commit**: `feat(p53-mdm2): like-for-like GPU smoke of gromacs.sif under singularity`

## Step 4: Gate docker-to-singularity parity
**Goal**: Assert mechanically that conversion preserved the things that matter.
**Implementation Logic**:
Parse both version blocks into structured form and compare the fields that must not drift across conversion — GROMACS version, precision, SIMD selection, CUDA runtime and GPU support. Compare the minimisation potential energy from both runs within a relative tolerance rather than exactly, since floating-point reduction order is not guaranteed identical. Deliberately do not compare wall-clock timings or step rates: those vary with node load and would produce a flaky gate that teaches people to ignore failures.
**Deliverables**: `examples/p53_mdm2/tests/test_container_evidence.py` — added functions `_parse_gmx_version`, `_potential_energy`, checks `docker_sif_version_parity` and `docker_sif_energy_parity`
**Consistency Checks**: `PYTHONPATH="$PYTHONPATH:$(pwd)/examples" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/tests/run_tests.py` (expected: PASS)
**Commit**: `test(p53-mdm2): docker to singularity parity gates`

## Step 5: Reclaim the build scratch
**Goal**: Leave the shared node no dirtier than we found it, and record the reclamation.
**Implementation Logic**:
Delete the intermediate archive, remove the tagged image, and prune the builder cache, capturing free space and the daemon's disk usage before and after so the reclamation is evidenced rather than asserted. This step is irreversible: once the archive and image are gone, none of the previous four steps can be re-run without a full rebuild, which is precisely why it is last. Do not prune anything not created by this work — the daemon's store holds a large volume of other users' images, which are not ours to remove.
**Deliverables**: `examples/p53_mdm2/cluster/evidence/cleanup.txt` — free space and daemon disk usage before and after, with the removal commands and their exit statuses
**Consistency Checks**: `grep -c 'after' examples/p53_mdm2/cluster/evidence/cleanup.txt` (expected: PASS)
**Commit**: `chore(p53-mdm2): reclaim banyan build scratch after sif delivery`
