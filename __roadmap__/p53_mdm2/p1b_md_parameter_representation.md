# P1b — MD-Parameter Representation (greenfield) — GATED on Q-003

**Status**: 🚧 Blocked pending PI decision (Q-003). This node exists so the greenfield concern the PI raised is tracked, not to commit the project to running MD before the PI decides.

**Goal**: If the project runs its own MD simulations (dgx1/banyan) for p53–MDM2, represent the **MD setup parameters** (engine, force field, water model, thermostat/barostat, integrator, timestep, ensemble, replica-exchange / GREST-REUS parameters, box, ionic strength, seeds) inside the USDBio intermediate representation, aligned with a SOTA reproducibility schema, so a simulation is reproducible from the USD stage alone.

**Pre-conditions**:
- [ ] PI decision on the self-run-MD track (Q-003) — determines whether this is critical-path or deferred [source: PI answer to Q-001, __threads__/p53-mdm2/QUESTIONS.md]
- [ ] R01 MD reproducibility survey delivered (recommended `bio:md:` schema + which SOTA schema to align with) [source: __reports__/p53-mdm2/01-md_reproducibility_survey_v0.md]
- [ ] MD software availability on dgx1/banyan confirmed (PI: "I think we haven't installed the software for MD there")

**Success Gates**:
- ⬜ A `bio:md:` (or agreed namespace) attribute schema on a designated USD prim carries the minimal reproducible MD-setup parameter set from R01
- ⬜ Field names align with the chosen SOTA schema (per R01) for interoperability
- ⬜ Round-trip test: parameters written to USD read back and reconstruct a runnable MD input (or a faithful parameter manifest) — asserted against the independently-stated source parameters, not generator state
- ⬜ Design stays "useful, reusable, not over-engineered" — a minimal core + optional extensions, not an exhaustive dump

## Step 1 (on unblock): Adopt the R01-recommended schema
**Goal**: Instantiate the R01 core parameter set as USD attributes; decide the carrying prim (stage-level metadata vs. a `Protocol`/`Dynamics` scope) consistent with departmental layering.
**Deliverables**: `examples/p53_mdm2/templates/md_parameters.py`, a schema doc
**Commit**: `feat(p53-mdm2): USDBio MD-setup-parameter representation (bio:md:)`

**References**: [R01 MD reproducibility survey](../../__reports__/p53-mdm2/01-md_reproducibility_survey_v0.md), [ShinobuLab GREST-REUS procedure doc](file://$USDBIO_DATA_DIR/251112-grest-reus-md-procedure-shinobu-lab.docx)
