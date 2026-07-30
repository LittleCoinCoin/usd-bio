# Recipe + Runbook Corrections

**Goal**: Make `examples/p53_mdm2/cluster/` describe the observed 2026-07-29 state — image built, Route A observed-dead, docker data-root observed, disk drawdown a one-off, libcuda question resolved — and remove the build-status lie that would otherwise be baked into the delivered image.
**Pre-conditions**:
- [x] Docker image `gromacs-p53mdm2:latest` built on banyan (Slurm job 30, exit 0, 5m27s, 10.6 GB)
- [x] `docker info` observed `Docker Root Dir=/var/lib/docker`, i.e. on `/`, and the client cannot redirect it
- [x] `/` observed at 439 G free on 2026-07-29 and unchanged four days later, so R10's 147 G drawdown was a one-off
- [x] Route A failure and `proot` absence captured verbatim from an attended probe
**Success Gates**:
- ⬜ `[static]` No file under `examples/p53_mdm2/cluster/` still *asserts* the container was never built — quoting an old claim as explicitly superseded is correct and does not violate this gate, so check the assertion's status, never a bare string count
- ⬜ `[static]` The value `SCAFFOLDING-not-built` appears in neither `Dockerfile` nor `gromacs.def`, so no build-status label can reach the `.sif`
- ⬜ `[static]` No `[assumption]` remains for the docker data-root, the subuid mapping, or the `libcuda.so.1` DT_NEEDED question
- ⬜ `[run]` R13 exists with `type: observation` front-matter and is indexed in the reports README
- ⬜ `[static]` The commit touching pins changes `Dockerfile` and `gromacs.def` together, mechanising a sync obligation the runbook admits is otherwise only social
**References**: [R10 cluster state refresh](../../../__reports__/p53-mdm2/10-cluster_state_refresh_v0.md) — the observations being promoted from inference to fact; [R07 cluster live verification](../../../__reports__/p53-mdm2/07-cluster_liveverify_v1.md) — the superseded fakeroot claim this corrects

## Step 1: File R13 as the observation of record
**Goal**: Capture the Route B build and its resolved assumptions as a citable report, so later corrections reference a document rather than a conversation.
**Implementation Logic**:
Follow R10's observation shape exactly: YAML front-matter carrying type, topic, spotted-during, date, domain, confidence and urgency, then numbered Evidence subsections each holding captured command output, then Re-observation Steps. Evidence must cover the job-30 record, the BUILD_STATUS sentinel, the build log tail, the in-image gmx version block, the docker data-root, disk free space, the Route A failure text, and the absence of both a subuid mapping and proot. Confidence must be stated per finding rather than blanket — R10's own front-matter said confirmed while its headline finding was an inference, and that is the error being corrected here. Append the round entry to the reports index in the same commit so the report is never orphaned.
**Deliverables**: `__reports__/p53-mdm2/13-route_b_build_observed_v0.md` (front-matter keys type/topic/spotted-during/date/domain/confidence/urgency; sections Evidence 1..8, Re-observation Steps, Scope Boundary) and an appended round entry in `__reports__/p53-mdm2/README.md`
**Consistency Checks**: `grep -c '^type: observation' __reports__/p53-mdm2/13-route_b_build_observed_v0.md` (expected: PASS)
**Commit**: `docs(p53-mdm2): observation report for the Route B build on banyan`

## Step 2: Rewrite the runbook to describe a built image
**Goal**: Remove every claim that nothing has been built, and convert Route A's status from predicted failure to observed failure with the captured error.
**Implementation Logic**:
The banner at the top of the runbook is the first thing any reader sees and currently states in bold that nothing has been built, uploaded or submitted; that is now false and actively misleading. Rewrite it to state what exists, where, and what remains. Convert the fakeroot section from inference to observation, quoting the probe's verbatim FATAL line and recording that proot is absent so the third hatch singularity names is closed too. Mark gated step 1 as done with its job id. Replace the data-root assumption block with the observed value and the fact that only an admin can move it. Reframe the disk drawdown as a one-off rather than a trend, since free space held steady. Move the SIF-skew risk from open to owned-by-the-dgx1-leaf. Leave the risk register honest: the docker-group-equals-root risk is unchanged and stays.
**Deliverables**: `examples/p53_mdm2/cluster/README.md` (rewritten banner, fakeroot-to-observed section, gated-step-1 status, data-root block, disk-drawdown framing, risk register, footer)
**Consistency Checks**: `grep -q 'Slurm job 30' examples/p53_mdm2/cluster/README.md` (expected: PASS)
**Commit**: `docs(p53-mdm2): runbook describes the built image, not scaffolding`

## Step 3: Sync both recipes and delete the BuildStatus label
**Goal**: Correct the recipe twins together and remove the only machine-readable falsehood, which would otherwise become the delivered image's permanent provenance claim.
**Implementation Logic**:
`BuildStatus` is a Docker LABEL and a Singularity `%labels` entry, not a comment, so it is baked into the image and carried into the `.sif` by `docker-archive://` conversion — `singularity inspect` would report SCAFFOLDING-not-built forever. Build status is per-build state and does not belong in a recipe literal; delete the key from both files rather than editing its value, and note that a build-time `--label` is the right mechanism if it is ever wanted. In the same commit, resolve the `libcuda.so.1` DT_NEEDED assumption: the build reached exit 0, which means the in-sandbox `gmx --version` gate passed with no driver present, and `CUDA driver: 0.0` is precisely that signature. Both files must change in one commit — they are parallel implementations of one image and the repo has no automated guard against their divergence yet.
**Deliverables**: `examples/p53_mdm2/cluster/Dockerfile` and `examples/p53_mdm2/cluster/gromacs.def` (BuildStatus label removed from both; header status text, data-root assumption and libcuda assumption corrected in both)
**Consistency Checks**: `grep -q 'SCAFFOLDING-not-built' examples/p53_mdm2/cluster/Dockerfile examples/p53_mdm2/cluster/gromacs.def` (expected: FAIL)
**Commit**: `docs(p53-mdm2): sync recipe twins and drop the BuildStatus label`
