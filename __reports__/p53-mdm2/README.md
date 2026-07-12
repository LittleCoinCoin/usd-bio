# Reports — p53-mdm2

End-to-end multi-scale p53–MDM2 demonstration with OpenUSD as the intermediary tying MD to systems-biology (MaBoSS) modelling. See `__threads__/p53-mdm2/INTENT.md` for the brief.

## Round 00 — cycle-000 (2026-07-08)

- [00-architecture_v0.md](00-architecture_v0.md) — Architecture analysis: the v8→p53_mdm2 **reuse map** (reuse-as-is / generalize / greenfield / leave-behind per asset), external-input decisions (1YCR starting structure, 5-node `p53_Mdm2` MaBoSS model, DDMut-PPI ΔG API), generalized contracts, risk register, and a 5-milestone roadmap sketch.

## Round 01–03 — cycle-001 (2026-07-10, planning/design)

- [01-md_reproducibility_survey_v0.md](01-md_reproducibility_survey_v0.md) — SOTA survey for sharing MD setup parameters; identifies MDDB (EU Molecular Dynamics Data Bank) and recommends a ~14-attribute `bio:md:` schema grounded in the ShinobuLab GENESIS decks.
- [02-dg_maboss_correlation_v0.md](02-dg_maboss_correlation_v0.md) — ΔG↔MaBoSS-parameter correlation design: governing knob, logistic ΔΔG→S mapping + closed-form inverse, anti-tautology round-trip test.
- [03-cycle001_findings_v0.md](03-cycle001_findings_v0.md) — cycle-001 synthesis + decisions (roadmap authored, topic-split rationale, Q-003/Q-004 filed).

## Round 04 — cycle-002 (2026-07-13, first code cycle)

- [04-cycle002_findings_v0.md](04-cycle002_findings_v0.md) **(latest)** — Pipeline 1 (MD→USD topology) landed: committed 1YCR topology `.usda` (`/p53_MDM2_complex`, 2 chains, 818 atoms), 9/9 falsification-resistant read-back tests, 2 clean anti-chimera gates; PI Q-003/Q-004 folded into the roadmap (p1b unblocked + promoted to critical-path).

## Status

Cycle-002 complete — first committed pipeline artifact. Pipeline 1 topology is done and tested. Next: Pipeline 2 (ddMut-PPI ΔΔG) recommended, with p1b's containerized MD on dgx1/banyan as a parallel multi-cycle workstream. See [findings v0 steering questions](04-cycle002_findings_v0.md).
