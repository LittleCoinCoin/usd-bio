# P2 USD to ddMut-PPI to Delta-Delta-G

**Goal**: Author a `Genotype`/Perturbation VariantSet of p53-peptide variants on the USD stage, query the **ddMut-PPI API** for each variant's ΔΔG (kcal/mol), and write the result back onto USD prims as provenance-tagged `bio:` attributes — the ΔG that Pipeline 3 binarizes. This is the MD datum the PI says the demo actually needs (Q-001).

**Pre-conditions**:
- [ ] Pipeline 1 topology `.usda` exists (variants swap geometry on chain B, the p53 peptide)
- [ ] ddMut-PPI API shape confirmed: POST-submit → GET-by-`job_id`; single-mutation endpoint takes `pdb_accession`/`pdb_file` + `chain` + `mutation` (e.g. `L45G`); returns `prediction` = ΔΔG (negative = destabilizing) [source: __reports__/p53-mdm2/00-architecture_v0.md §External Input Decisions]

**Success Gates**:
- ⬜ A `Genotype` VariantSet generalizing v8 `build_genotype.py` off the T315I/ABL specifics (geometry-swap-by-Reference mechanism transfers directly)
- ⬜ A rate-limited ddMut-PPI client (sequential submits ≥1/s, backed-off polling, batch via `/list`) — a good internet citizen
- ⬜ ΔΔG written back as `bio:` attributes per variant, with six-field `bio:` provenance (reuse v8 `apply_provenance_metadata`)
- ⬜ **Error model**: ddMut job failure/timeout surfaces as an explicit `unknown`-tagged provenance value, **never a fabricated ΔG** (v8 `provenance_source.py` philosophy)
- ⬜ Read-back test asserts the recorded ΔΔG against an independent re-query or a committed fixture

**References**: [R00 §Pipeline 2](../../__reports__/p53-mdm2/00-architecture_v0.md), [ddMut-PPI API](https://biosig.lab.uq.edu.au/ddmut_ppi/api)

## Step 1: Generalize the Genotype VariantSet
**Goal**: Port v8's `build_genotype.py` geometry-swap-by-Reference mechanism off the T315I/ABL specifics onto p53-peptide chain-B mutations.
**Implementation Logic**:
The geometry-swap-by-Reference VariantSet mechanism transfers directly from v8 — each `Genotype` variant References a per-mutation geometry payload rather than re-authoring atoms inline. Only the mutation vocabulary and the referenced chain change; no ABL-specific literal (`T315I`, the ABL root prim) survives into the library code.
**Deliverables**: `examples/p53_mdm2/composition/build_genotype.py`
**Consistency Checks**: `! grep -q "T315I" examples/p53_mdm2/composition/build_genotype.py` (expected: PASS)
**Commit**: `feat(p53-mdm2): p53-peptide Genotype VariantSet (off ABL T315I)`

## Step 2: Rate-limited ddMut-PPI client + ΔΔG write-back
**Goal**: Query ddMut-PPI for each Genotype variant's ΔΔG and write it back onto USD prims as provenance-tagged `bio:` attributes, without ever fabricating a value on failure.
**Implementation Logic**:
The client is rate-limited (sequential submits ≥1/s, backed-off polling, batch via `/list`) to stay a good internet citizen against the shared ddMut-PPI service. Write-back reuses v8's six-field `bio:` provenance (`apply_provenance_metadata`) so every ΔΔG is traceable to its source. Error model: a job failure/timeout is written as an explicit `unknown`-tagged provenance value, never a fabricated ΔG, matching v8's `provenance_source.py` philosophy.
**Deliverables**: `examples/p53_mdm2/converters/ddmut_client.py`, ΔΔG-write-back, committed `.usda` variant edits
**Consistency Checks**: `. ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples:$(pwd)/examples/p53_mdm2/tests" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import test_ddg_readback as t; rows = t.run(); import sys; sys.exit(0 if all(r.passed for r in rows) else 1)"` (expected: PASS)
**Commit**: `feat(p53-mdm2): rate-limited ddMut-PPI client + ΔΔG write-back as bio: attrs`
