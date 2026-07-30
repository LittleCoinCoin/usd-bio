# dgx1 SIF Open Check

**Goal**: Establish that an image written by singularity-ce 4.2.2 on banyan opens and executes under dgx1's singularity 3.5.2, and that the shared home really does present the same bytes to both clusters — all without writing to dgx1 or touching a GPU.
**Pre-conditions**:
- [x] `gromacs.sif` exists on the shared home, produced by `convert_verify_cleanup`
- [x] One shared NFS home mounted identically on both clusters — asserted from free-space output since R07, never proven byte-for-byte
- [x] Every action here is read-only, so this leaf is executable by an unattended cycle under the Q-006 policy
**Success Gates**:
- ✅ `[run]` The image digest computed from banyan and from dgx1 are **equal**, giving the stage-once-run-anywhere claim its first actual test
- ✅ `[run]` `singularity inspect` exits 0 under singularity 3.5.2 and prints the GROMACS version label
- ✅ `[run]` `singularity exec` listing the install directory exits 0 and shows the `gmx` binary, proving the squashfs mounts and reads
- ✅ `[static]` The SIF-version-skew entry in the runbook's risk register is rewritten from open risk to observation
**References**: [R07 cluster live verification](../../../../../__reports__/p53-mdm2/07-cluster_liveverify_v1.md) — where the version-skew risk and the shared-home claim were first recorded; [R10 cluster state refresh](../../../../../__reports__/p53-mdm2/10-cluster_state_refresh_v0.md) — the confirmed singularity versions on each cluster

## Step 1: Prove shared-home byte parity
**Goal**: Confirm both clusters see the identical image, since every portability argument in the runbook rests on this and none of it has been tested.
**Implementation Logic**:
The runbook has claimed stage-once-run-anywhere since the first recon, but the evidence for it was only that free-space figures matched on both hosts — which shows a common mount point, not identical content. Compute the image digest from banyan and again from dgx1 and compare. A mismatch would invalidate a claim the whole cross-cluster design depends on and would be a far more serious finding than any version skew, so capture both values verbatim rather than only their comparison result.
**Deliverables**: `examples/p53_mdm2/cluster/evidence/dgx1_sif_open.txt` — image digest as computed from each cluster, with the mount line from each host; plus an appended `manifest.jsonl` entry per cluster
**Consistency Checks**: `grep -c 'dgx1' examples/p53_mdm2/cluster/evidence/dgx1_sif_open.txt` (expected: PASS)
**Commit**: `docs(p53-mdm2): shared-home sif byte parity across banyan and dgx1`

## Step 2: Open and read the image under singularity 3.5.2
**Goal**: Settle whether a 2019 runtime can mount a squashfs written by a 2024 one.
**Implementation Logic**:
Record the runtime version, then inspect the image, then execute a trivial directory listing inside it. The listing is the real test: inspect reads metadata, whereas exec must actually mount the squashfs, so a newer compression algorithm would fail there specifically. Attempt the version query too, but treat a failure naming the driver library as expected rather than as skew — without GPU passthrough there is no host driver bound in, and that is a different fact entirely. If the mount does fail, capture which compression the image actually uses, because that turns a dead end into an actionable finding pointing at either an older-compatible rebuild or a per-cluster image.
**Deliverables**: `examples/p53_mdm2/cluster/evidence/dgx1_sif_open.txt` — appended runtime version, inspect output, directory listing, and the version-query result with its interpretation
**Consistency Checks**: `grep -c 'gmx' examples/p53_mdm2/cluster/evidence/dgx1_sif_open.txt` (expected: PASS)
**Commit**: `docs(p53-mdm2): gromacs.sif opens under dgx1 singularity 3.5.2`

## Step 3: Close the risk and gate it
**Goal**: Move the version-skew risk from speculation to a recorded observation, and assert it offline.
**Implementation Logic**:
The runbook lists SIF version skew as an open risk with a mitigation plan. Once the image is observed opening under the older runtime, rewrite that entry as an observation with its evidence citation; if it failed instead, rewrite it as a confirmed defect with the compression finding. Either way the register stops carrying a speculative entry. Add the corresponding assertions to the container-evidence module, keeping the zero-rows-when-absent rule so a deferred execution of this leaf does not redden the suite in the meantime.
**Deliverables**: `examples/p53_mdm2/cluster/README.md` — risk-register entry rewritten as observation with citation; `examples/p53_mdm2/tests/test_container_evidence.py` — added checks `dgx1_digest_parity` and `dgx1_sif_opens`
**Consistency Checks**: `PYTHONPATH="$PYTHONPATH:$(pwd)/examples" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/tests/run_tests.py` (expected: PASS)
**Commit**: `test(p53-mdm2): dgx1 sif-open gate and risk-register update`
