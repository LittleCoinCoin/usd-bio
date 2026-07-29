# P1b MD-Parameter Representation

**Status**: ⬜ Planned — on the critical path (Q-003 answered YES by the PI, cycle-001 review, 2026-07-12): the project WILL run its own p53–MDM2 MD simulations on dgx1/banyan, so the MD setup parameters are a critical-path USDBio representation concern, not a deferred/optional greenfield [source: __threads__/p53-mdm2/QUESTIONS.md Q-003 answer].

**Goal**: The project runs its own MD simulations (dgx1/banyan) for p53–MDM2; represent the **MD setup parameters** (engine, force field, water model, thermostat/barostat, integrator, timestep, ensemble, replica-exchange / GREST-REUS parameters, box, **ionic strength/ion concentration**, **protonation state**, seeds) inside the USDBio intermediate representation, aligned with a SOTA reproducibility schema, so a simulation is reproducible from the USD stage alone.

**PI directives folded in from the Q-003 answer** [source: __threads__/p53-mdm2/QUESTIONS.md Q-003 answer, PI 2026-07-12]:
- **Ion concentration and protonation state are promoted to the `bio:md:` CORE set** (not optional) — the PI explicitly ruled these core because they are not derivable from geometry.
- **Execution model = a Docker-build / Singularity-run split, not a single tool.** Docker *builds* the MD-engine image — on banyan the daemon builds as root, which is why it works despite there being no `/etc/subuid`/`/etc/subgid` mapping for this user on either cluster — and Singularity *runs* it on both clusters; the two are complementary stages of one pipeline, not competitors. This corrects the original directive here, which assumed Docker end-to-end: native `singularity build` as a non-root user is dead, confirmed by observation (not inference) on 2026-07-29 — no subuid/subgid range and no `proot` on banyan, and `--remote` declined to avoid shipping the recipe off-site [source: __threads__/p53-mdm2/QUESTIONS.md Q-005 answer, Q-007 answer, PI 2026-07-20 and 2026-07-29]. Pattern: build the Docker image on banyan, `docker save` it, `singularity build gromacs.sif docker-archive://…` to convert it, then bind-mount an input-data folder in and an output folder out under `singularity exec --nv`. The resulting `.sif` is a reusable asset for future MD simulations, staged once on the shared NFS home and run on either cluster.
- **The cluster connection is BETA — tread carefully.** dgx1/banyan are SHARED resources: be careful with any mutating or installation commands. Document usage patterns / friction / improvements via the **knowledge-report** format (`/writing-reports`) so the working-agent experience improves over time.

**Pre-conditions**:
- [x] PI decision on the self-run-MD track (Q-003) — **YES, critical-path** [source: __threads__/p53-mdm2/QUESTIONS.md Q-003 answer]
- [x] R01 MD reproducibility survey delivered (recommended `bio:md:` schema + which SOTA schema to align with) [source: __reports__/p53-mdm2/01-md_reproducibility_survey_v0.md]
- [ ] MD-engine containerized execution validated on dgx1/banyan via the Docker-build / Singularity-run split (no native `singularity build`; shared resource — mutating commands used with care, PI-attended per Q-006)

**Success Gates**:
- ⬜ A `bio:md:` (or agreed namespace) attribute schema on a designated USD prim carries the minimal reproducible MD-setup parameter set from R01, **with ion concentration + protonation state in the CORE block**
- ⬜ Field names align with the chosen SOTA schema (per R01, MDDB) for interoperability
- ⬜ Round-trip test: parameters written to USD read back and reconstruct a runnable MD input (or a faithful parameter manifest) — asserted against the independently-stated source parameters, not generator state
- ⬜ Containerized MD execution on dgx1/banyan delegated to and closed by `p1b_container_runtime/`'s own gates (Docker build → `.sif` conversion → GPU-verified run), with a knowledge-report documenting the setup, friction, and recommended usage patterns
- ⬜ Design stays "useful, reusable, not over-engineered" — a minimal core + optional extensions, not an exhaustive dump

**References**: [R01 MD reproducibility survey](../../__reports__/p53-mdm2/01-md_reproducibility_survey_v0.md), [ShinobuLab GREST-REUS procedure doc](file://$USDBIO_DATA_DIR/251112-grest-reus-md-procedure-shinobu-lab.docx)

## Step 1: Adopt the R01-recommended schema (ion-conc + protonation in CORE)
**Goal**: Instantiate the R01 core parameter set as USD attributes; decide the carrying prim (stage-level metadata vs. a `Protocol`/`Dynamics` scope) consistent with departmental layering.
**Implementation Logic**:
Ion concentration and protonation state go in the CORE block per the PI's Q-003 directive, since they are not derivable from geometry. Field names align with the R01-recommended SOTA schema (MDDB) so the representation stays interoperable rather than bespoke.
**Deliverables**: `examples/p53_mdm2/templates/md_parameters.py`, a schema doc
**Consistency Checks**: `. ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples:$(pwd)/examples/p53_mdm2/tests" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import test_md_setup_readback as t; rows = t.run(); import sys; sys.exit(0 if all(r.passed for r in rows) else 1)"` (expected: PASS)
**Commit**: `feat(p53-mdm2): USDBio MD-setup-parameter representation (bio:md:)`

## Step 2: Containerized MD execution on dgx1/banyan (delegated to `p1b_container_runtime/`)
**Goal**: Deliver a reusable, GPU-verified GROMACS container runtime for dgx1/banyan via the Docker-build / Singularity-run split; this Step closes when `p1b_container_runtime/`'s own Success Gates all pass.
**Implementation Logic**:
Superseded framing: the original Step 2 here assumed a Docker-only execution model ("dgx1/banyan have no Singularity; use Docker"), which Q-005 and Q-007 reversed by observation — Docker builds (daemon-as-root on banyan), Singularity runs (on both clusters). This campaign decomposes that work under `p1b_container_runtime/` (`recipe_evidence_corrections`, `sass_portability_audit`, `docker_gpu_smoke`, `sif_delivery/`) rather than re-stating it here, per the historical-order note in this campaign's `README.md`. No cluster-mutating action is taken from this leaf directly; cluster mutation stays PI-attended per Q-006.
**Deliverables**: delegated to `__roadmap__/p53-mdm2-v2/p1b_container_runtime/` — see that subtree's own leaf tasks for the Dockerfile/`gromacs.def` recipe, the GPU smoke test, and the `.sif` delivery; a knowledge-report documenting cluster setup, usage patterns, and friction is one of its deliverables.
**Consistency Checks**: `! grep -q '^- ⬜' __roadmap__/p53-mdm2-v2/p1b_container_runtime/README.md` (expected: FAIL)
**Requires**: `p1b_container_runtime/` Success Gates (see that subtree's `README.md`)
**Commit**: `chore(p53-mdm2): close p1b Step 2 once p1b_container_runtime/ gates pass`
