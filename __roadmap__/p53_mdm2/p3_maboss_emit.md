# P3 — OpenUSD → MaBoSS: ΔG↔parameter correlation → emit `.bnd`/`.cfg`

**Goal**: Emit a MaBoSS `p53_Mdm2` model (`.bnd`/`.cfg`) from the USD stage in which the parameter governing p53–Mdm2N antagonism is set by a **ΔG↔parameter correlation function** (per PI Q-002: no fixed threshold; the model's tuned parameter is correlated with ΔG, and ΔG is the inverse of that correlation). Round-trips against the PI-provided reference files.

**Pre-conditions**:
- [ ] Pipeline 2 has written per-variant ΔΔG as `bio:` attributes
- [ ] Governing MaBoSS parameter + correlation function + inverse designed in R02 [source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md]
- [ ] Reference files: `p53_Mdm2.bnd`, `p53_Mdm2_runcfg.cfg` (5-node DNA-damage oscillator; `p53.logic = NOT Mdm2N`) [source: __reports__/p53-mdm2/00-architecture_v0.md §External Input Decisions]

**Success Gates**:
- ⬜ The ΔG↔parameter correlation from R02 is implemented as a pure, tested function (and its inverse)
- ⬜ Emitted `.bnd` matches the reference network topology; emitted `.cfg` differs from baseline only in the correlation-set parameter(s) (+ optional forced-node override)
- ⬜ Round-trip: re-parsing the emitted `.cfg` recovers the ΔG-implied parameter within tolerance (the inverse), asserted against the independently-computed value
- ⬜ Correlation parameters carried in USDBio as `bio:` attributes so the mapping is inspectable from the stage

## Step 1: Implement + test the ΔG↔parameter correlation
**Deliverables**: `examples/p53_mdm2/maboss/dg_correlation.py` (forward + inverse), unit tests
**Commit**: `feat(p53-mdm2): ΔG↔MaBoSS-parameter correlation function + inverse`

## Step 2: `.bnd`/`.cfg` emitter from USD
**Deliverables**: `examples/p53_mdm2/maboss/emit_model.py`, committed emitted `.bnd`/`.cfg`, round-trip test
**Commit**: `feat(p53-mdm2): emit MaBoSS .bnd/.cfg from USD via ΔG correlation`

**References**: [R02 ΔG↔MaBoSS correlation design](../../__reports__/p53-mdm2/02-dg_maboss_correlation_v0.md), [R00 §Pipeline 3](../../__reports__/p53-mdm2/00-architecture_v0.md)
