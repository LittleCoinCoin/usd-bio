# examples/p53_mdm2

A runnable, multi-scale **p53–MDM2** demonstration in which OpenUSD is the shared representation tying molecular dynamics to systems-biology (MaBoSS Boolean-network) modelling. Brief: `__threads__/p53-mdm2/INTENT.md`. Reuse map & architecture: `__reports__/p53-mdm2/00-architecture_v0.md`.

> **Not a copy of `foundation_demo_v8/`.** v8 is inspiration only. Every module here is *extracted and generalized* per the reuse map — the ABL-specific root path `/ABLComplex` and dataset atom counts (`4676`, `43`) must never appear in this tree. The system root is a `root_path` parameter threaded through parser → assembly → clips → tests.

## The four pipelines

| # | Pipeline | Source in v8 | Extraction plan |
|---|---|---|---|
| 1 | **MD → OpenUSD** | `pdb_parser.py`, `xtc_to_clips.py`, `04_create_assembly.py` (generalize) | Parameterize off ABL; drive with the 1YCR p53–MDM2 complex. |
| 2 | **OpenUSD → MD (ΔG)** | `perturbation_variantset/build_genotype.py` (generalize) + greenfield ddMut-PPI client | Genotype VariantSet per p53-peptide variant → DDMut-PPI ΔΔG → written back as `bio:` attrs. |
| 3 | **OpenUSD → MaBoSS** | greenfield | Binarize ΔG → `Mdm2N.istate`; emit `.bnd`/`.cfg` matching the 5-node `p53_Mdm2` model. |
| 4 | **MaBoSS → OpenUSD** | `09_create_departmental_layers.py` analysis-layer pattern (generalize) | Read node-state/probability time series back as time-sampled `bio:` attrs in an analysis SubLayer. |

## Planned structure (built incrementally, map-driven)

```
examples/p53_mdm2/
  README.md              # this file
  data/                  # reuse-as-is from v8: element/ion/residue biochemistry
  converters/            # generalize: parse_pdb(), xtc→clips (lazy mdtraj import)
  builders/              # generalize: assembly builder (root_path param), analysis-layer
  maboss/                # greenfield: USD↔MaBoSS .bnd/.cfg emit + read-back
  ddmut/                 # greenfield: rate-limited DDMut-PPI client
  tests/                 # generalize: 4-layer anti-tautology read-back harness
  output/                # committed .usda artifacts (evidence of "done")
```

## Key external inputs (see architecture report for rationale)

- **Starting structure:** [1YCR](https://www.rcsb.org/structure/1YCR) — native p53 transactivation peptide (chain B, triad Phe19/Trp23/Leu26) bound to MDM2 N-terminal domain (chain A); fallback 4HFZ.
- **MaBoSS model:** the 5-node `p53_Mdm2` DNA-damage oscillator (`p53`, `p53_h`, `Mdm2C`, `Mdm2N`, `Dam`); PI-provided `.bnd`/`.cfg` at `maboss.curie.fr/files/p53Dam/`.
- **ΔG API:** [DDMut-PPI](https://biosig.lab.uq.edu.au/ddmut_ppi/api) — async submit/poll, ΔΔG in kcal/mol; client-side rate-limited.

## Environment

Runs under the forOUSD venv (`~/Documents/src/AOUSD/forOUSD/bin/python3`, Python 3.11.14) with `load_env.sh` on `PYTHONPATH` — it carries both `pxr` and `mdtraj`.

## Status

Cycle-000: scaffold + reuse map only — no pipeline code yet (deliberately, to avoid premature chimera copy). Extraction begins next cycle with Pipeline 1.
