# Reports — p53-mdm2

End-to-end multi-scale p53–MDM2 demonstration with OpenUSD as the intermediary tying MD to systems-biology (MaBoSS) modelling. See `__threads__/p53-mdm2/INTENT.md` for the brief.

## Round 00 — cycle-000 (2026-07-08)

- [00-architecture_v0.md](00-architecture_v0.md) **(latest)** — Architecture analysis: the v8→p53_mdm2 **reuse map** (reuse-as-is / generalize / greenfield / leave-behind per asset), external-input decisions (1YCR starting structure, 5-node `p53_Mdm2` MaBoSS model, DDMut-PPI ΔG API), generalized contracts, risk register, and a 5-milestone roadmap sketch.

## Status

First cycle complete. The reuse map is the prerequisite for extraction; the next cycle builds the formal `__roadmap__/p53_mdm2/` tree and begins Pipeline 1 (MD→USD) extraction driven by the map. Two open steering questions for the PI: p53–MDM2 input-data format/availability, and the ΔG→node binarization threshold.
