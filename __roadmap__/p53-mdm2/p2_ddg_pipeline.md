# P2 — OpenUSD → MD (ΔG): variant → ddMut-PPI → ΔΔG write-back

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

## Step 1: Generalize the Genotype VariantSet
**Deliverables**: `examples/p53_mdm2/composition/build_genotype.py`
**Commit**: `feat(p53-mdm2): p53-peptide Genotype VariantSet (off ABL T315I)`

## Step 2: Rate-limited ddMut-PPI client + ΔΔG write-back
**Deliverables**: `examples/p53_mdm2/converters/ddmut_client.py`, ΔΔG-write-back, committed `.usda` variant edits
**Commit**: `feat(p53-mdm2): rate-limited ddMut-PPI client + ΔΔG write-back as bio: attrs`

**References**: [R00 §Pipeline 2](../../__reports__/p53-mdm2/00-architecture_v0.md), [ddMut-PPI API](https://biosig.lab.uq.edu.au/ddmut_ppi/api)
