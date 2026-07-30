# P3 USD to MaBoSS — Correlation + Emit

**Status**: ✅ Done (cycle-004) — correlation + emit committed (`1f53e38`, `6cf3cb3`), 28/28 checks pass, usdchecker exit 0. Emit is pure text templating (no MaBoSS install); the MaBoSS *run* (directional test) is deferred to P4 by design [source: __reports__/p53-mdm2/08-cycle004_findings_v0.md].

**Goal**: Emit a MaBoSS `p53_Mdm2` model (`.bnd`/`.cfg`) from the USD stage in which the parameter governing p53–Mdm2N antagonism is set by a **ΔG↔parameter correlation function** (per PI Q-002: no fixed threshold; the model's tuned parameter is correlated with ΔG, and ΔG is the inverse of that correlation). Round-trips against the PI-provided reference files.

**Pre-conditions**:
- [x] Pipeline 2 has written per-variant ΔΔG as `bio:` attributes (cycle-003)
- [x] Governing MaBoSS parameter + correlation function + inverse designed in R02 [source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md]
- [x] Reference files: `p53_Mdm2.bnd`, `p53_Mdm2_runcfg.cfg` fetched verbatim from maboss.curie.fr → `examples/p53_mdm2/maboss/reference/`; WT params match R02 exactly [source: __reports__/p53-mdm2/08-cycle004_findings_v0.md]

**Success Gates**:
- ✅ The ΔG↔parameter correlation from R02 is implemented as a pure, tested function (and its inverse) — `maboss/dg_correlation.py`, 9 unit checks
- ✅ Emitted `.bnd` byte-identical to reference (SHA-256); emitted `.cfg` differs from baseline in exactly the 2 correlated params (`$KMn_pMCD`/`$KMn_pMC`); optional `Mdm2N.istate` override implemented but off by default
- ✅ Round-trip: re-parsing the emitted `.cfg` with an independent reader recovers the ΔG-implied parameter (and the logit inverse recovers ΔΔG), asserted against a second independent computation, not generator state
- ✅ Correlation parameters carried in USDBio as `bio:maboss:*` attributes so the mapping (and its inverse) is inspectable from the stage alone; `S` self-tagged fixture-grounded

**References**: [R02 ΔG↔MaBoSS correlation design](../../__reports__/p53-mdm2/02-dg_maboss_correlation_v0.md), [R00 §Pipeline 3](../../__reports__/p53-mdm2/00-architecture_v0.md)

## Step 1: Implement + test the ΔG↔parameter correlation
**Goal**: Implement the R02 ΔG↔MaBoSS-parameter logistic correlation and its inverse as a pure, unit-tested function.
**Implementation Logic**:
`S = 1/(1+exp(-k(ΔΔG-m)))` maps ΔΔG onto the governing MaBoSS parameter; the inverse (`m + (1/k)*logit(S)`) recovers ΔΔG from a parameter value. Both directions are pure functions with no USD/MaBoSS dependency, covered by 9 unit checks against R02's hand-computed anchors.
**Deliverables**: `examples/p53_mdm2/maboss/dg_correlation.py` (forward + inverse), unit tests
**Consistency Checks**: `. ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples:$(pwd)/examples/p53_mdm2/tests" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import test_dg_correlation as t; rows = t.run(); import sys; sys.exit(0 if all(r.passed for r in rows) else 1)"` (expected: PASS)
**Commit**: `feat(p53-mdm2): ΔG↔MaBoSS-parameter correlation function + inverse`

## Step 2: `.bnd`/`.cfg` emitter from USD
**Goal**: Emit a `p53_Mdm2` MaBoSS model from the USD stage whose governing parameter is set via the Step-1 correlation, round-tripping against the PI-provided reference files.
**Implementation Logic**:
The emitted `.bnd` is byte-identical to the reference (SHA-256) since topology never changes; the emitted `.cfg` differs from the baseline in exactly the two correlated parameters (`$KMn_pMCD`/`$KMn_pMC`), with an optional `Mdm2N.istate` override left off by default. Correlation parameters are also written back onto the USD stage as `bio:maboss:*` attributes so the mapping is inspectable without re-running the emitter.
**Deliverables**: `examples/p53_mdm2/maboss/emit_model.py`, committed emitted `.bnd`/`.cfg`, round-trip test
**Consistency Checks**: `. ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples:$(pwd)/examples/p53_mdm2/tests" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import test_maboss_emit as t; rows = t.run(); import sys; sys.exit(0 if all(r.passed for r in rows) else 1)"` (expected: PASS)
**Commit**: `feat(p53-mdm2): emit MaBoSS .bnd/.cfg from USD via ΔG correlation`
