# P1b — MD-Parameter Representation (greenfield) — UNBLOCKED, PROMOTED (Q-003)

**Status**: ⬜ Planned — **on the critical path**. Q-003 answered YES by the PI (cycle-001 review, 2026-07-12): the project WILL run its own p53–MDM2 MD simulations on dgx1/banyan, so the MD setup parameters are a critical-path USDBio representation concern, not a deferred/optional greenfield [source: __threads__/p53-mdm2/QUESTIONS.md Q-003 answer].

**Goal**: The project runs its own MD simulations (dgx1/banyan) for p53–MDM2; represent the **MD setup parameters** (engine, force field, water model, thermostat/barostat, integrator, timestep, ensemble, replica-exchange / GREST-REUS parameters, box, **ionic strength/ion concentration**, **protonation state**, seeds) inside the USDBio intermediate representation, aligned with a SOTA reproducibility schema, so a simulation is reproducible from the USD stage alone.

**PI directives folded in from the Q-003 answer** [source: __threads__/p53-mdm2/QUESTIONS.md Q-003 answer, PI 2026-07-12]:
- **Ion concentration and protonation state are promoted to the `bio:md:` CORE set** (not optional) — the PI explicitly ruled these core because they are not derivable from geometry.
- **Execution model = Docker containers, not a direct install.** dgx1/banyan have no Singularity; use Docker. Pattern: a container carries the MD engine; bind-mount an input-data folder in and an output folder out. The container is a reusable asset for future MD simulations. Building/optimizing it is expected to take work.
- **The cluster connection is BETA — tread carefully.** dgx1/banyan are SHARED resources: be careful with any mutating or installation commands. Document usage patterns / friction / improvements via the **knowledge-report** format (`/writing-reports`) so the working-agent experience improves over time.

**Pre-conditions**:
- [x] PI decision on the self-run-MD track (Q-003) — **YES, critical-path** [source: __threads__/p53-mdm2/QUESTIONS.md Q-003 answer]
- [x] R01 MD reproducibility survey delivered (recommended `bio:md:` schema + which SOTA schema to align with) [source: __reports__/p53-mdm2/01-md_reproducibility_survey_v0.md]
- [ ] MD-engine Docker image built + bind-mount execution pattern validated on dgx1/banyan (no Singularity; shared resource — mutating commands used with care)

**Success Gates**:
- ⬜ A `bio:md:` (or agreed namespace) attribute schema on a designated USD prim carries the minimal reproducible MD-setup parameter set from R01, **with ion concentration + protonation state in the CORE block**
- ⬜ Field names align with the chosen SOTA schema (per R01, MDDB) for interoperability
- ⬜ Round-trip test: parameters written to USD read back and reconstruct a runnable MD input (or a faithful parameter manifest) — asserted against the independently-stated source parameters, not generator state
- ⬜ A reusable Docker image + bind-mount run pattern for the MD engine on dgx1/banyan, with a knowledge-report documenting the setup, friction, and recommended usage patterns
- ⬜ Design stays "useful, reusable, not over-engineered" — a minimal core + optional extensions, not an exhaustive dump

## Step 1: Adopt the R01-recommended schema (ion-conc + protonation in CORE)
**Goal**: Instantiate the R01 core parameter set as USD attributes; decide the carrying prim (stage-level metadata vs. a `Protocol`/`Dynamics` scope) consistent with departmental layering. Ion concentration and protonation state go in the CORE block per the PI's Q-003 directive.
**Deliverables**: `examples/p53_mdm2/templates/md_parameters.py`, a schema doc
**Commit**: `feat(p53-mdm2): USDBio MD-setup-parameter representation (bio:md:)`

## Step 2: Containerized MD execution on dgx1/banyan (Docker, bind-mount)
**Goal**: Build/optimize a reusable Docker image carrying the MD engine; validate the bind-mount execution pattern (input folder in, output folder out) on dgx1/banyan. Treat the cluster as beta and shared — no careless mutating/installation commands.
**Deliverables**: container recipe (`Dockerfile` + build/run notes), a knowledge-report per `/writing-reports` documenting the cluster setup + usage patterns + friction.
**Commit**: `feat(p53-mdm2): containerized MD execution pattern for dgx1/banyan`

**References**: [R01 MD reproducibility survey](../../__reports__/p53-mdm2/01-md_reproducibility_survey_v0.md), [ShinobuLab GREST-REUS procedure doc](file://$USDBIO_DATA_DIR/251112-grest-reus-md-procedure-shinobu-lab.docx)
