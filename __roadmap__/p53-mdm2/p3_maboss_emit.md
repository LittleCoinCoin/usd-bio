# P3 — OpenUSD → MaBoSS: ΔG↔parameter correlation → emit `.bnd`/`.cfg`

**Goal**: Emit a MaBoSS `p53_Mdm2` model (`.bnd`/`.cfg`) from the USD stage in which the parameter governing p53–Mdm2N antagonism is set by a **ΔG↔parameter correlation function** (per PI Q-002: no fixed threshold; the model's tuned parameter is correlated with ΔG, and ΔG is the inverse of that correlation). Round-trips against the PI-provided reference files.

**Status**: ✅ Done (cycle-004) — correlation + emit committed (`1f53e38`, `6cf3cb3`), 28/28 checks pass, usdchecker exit 0. Emit is pure text templating (no MaBoSS install); the MaBoSS *run* (directional test) is deferred to P4 by design [source: __reports__/p53-mdm2/08-cycle004_findings_v0.md].

**Pre-conditions**:
- [x] Pipeline 2 has written per-variant ΔΔG as `bio:` attributes (cycle-003)
- [x] Governing MaBoSS parameter + correlation function + inverse designed in R02 [source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md]
- [x] Reference files: `p53_Mdm2.bnd`, `p53_Mdm2_runcfg.cfg` fetched verbatim from maboss.curie.fr → `examples/p53_mdm2/maboss/reference/`; WT params match R02 exactly [source: __reports__/p53-mdm2/08-cycle004_findings_v0.md]

**Success Gates**:
- ✅ The ΔG↔parameter correlation from R02 is implemented as a pure, tested function (and its inverse) — `maboss/dg_correlation.py`, 9 unit checks
- ✅ Emitted `.bnd` byte-identical to reference (SHA-256); emitted `.cfg` differs from baseline in exactly the 2 correlated params (`$KMn_pMCD`/`$KMn_pMC`); optional `Mdm2N.istate` override implemented but off by default
- ✅ Round-trip: re-parsing the emitted `.cfg` with an independent reader recovers the ΔG-implied parameter (and the logit inverse recovers ΔΔG), asserted against a second independent computation, not generator state
- ✅ Correlation parameters carried in USDBio as `bio:maboss:*` attributes so the mapping (and its inverse) is inspectable from the stage alone; `S` self-tagged fixture-grounded

## Step 1: Implement + test the ΔG↔parameter correlation
**Deliverables**: `examples/p53_mdm2/maboss/dg_correlation.py` (forward + inverse), unit tests
**Commit**: `feat(p53-mdm2): ΔG↔MaBoSS-parameter correlation function + inverse`

## Step 2: `.bnd`/`.cfg` emitter from USD
**Deliverables**: `examples/p53_mdm2/maboss/emit_model.py`, committed emitted `.bnd`/`.cfg`, round-trip test
**Commit**: `feat(p53-mdm2): emit MaBoSS .bnd/.cfg from USD via ΔG correlation`

**References**: [R02 ΔG↔MaBoSS correlation design](../../__reports__/p53-mdm2/02-dg_maboss_correlation_v0.md), [R00 §Pipeline 3](../../__reports__/p53-mdm2/00-architecture_v0.md)
