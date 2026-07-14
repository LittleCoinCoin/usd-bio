# Reports — p53-mdm2

End-to-end multi-scale p53–MDM2 demonstration with OpenUSD as the intermediary tying MD to systems-biology (MaBoSS) modelling. See `__threads__/p53-mdm2/INTENT.md` for the brief.

## Round 00 — cycle-000 (2026-07-08)

- [00-architecture_v0.md](00-architecture_v0.md) — Architecture analysis: the v8→p53_mdm2 **reuse map** (reuse-as-is / generalize / greenfield / leave-behind per asset), external-input decisions (1YCR starting structure, 5-node `p53_Mdm2` MaBoSS model, DDMut-PPI ΔG API), generalized contracts, risk register, and a 5-milestone roadmap sketch.

## Round 01–03 — cycle-001 (2026-07-10, planning/design)

- [01-md_reproducibility_survey_v0.md](01-md_reproducibility_survey_v0.md) — SOTA survey for sharing MD setup parameters; identifies MDDB (EU Molecular Dynamics Data Bank) and recommends a ~14-attribute `bio:md:` schema grounded in the ShinobuLab GENESIS decks.
- [02-dg_maboss_correlation_v0.md](02-dg_maboss_correlation_v0.md) — ΔG↔MaBoSS-parameter correlation design: governing knob, logistic ΔΔG→S mapping + closed-form inverse, anti-tautology round-trip test.
- [03-cycle001_findings_v0.md](03-cycle001_findings_v0.md) — cycle-001 synthesis + decisions (roadmap authored, topic-split rationale, Q-003/Q-004 filed).

## Round 04 — cycle-002 (2026-07-13, first code cycle)

- [04-cycle002_findings_v0.md](04-cycle002_findings_v0.md) — Pipeline 1 (MD→USD topology) landed: committed 1YCR topology `.usda` (`/p53_MDM2_complex`, 2 chains, 818 atoms), 9/9 falsification-resistant read-back tests, 2 clean anti-chimera gates; PI Q-003/Q-004 folded into the roadmap (p1b unblocked + promoted to critical-path).

## Round 05–06 — cycle-003 (2026-07-14, Pipeline 2 + p1b schema)

- [05-cluster_md_recon_v0.md](05-cluster_md_recon_v0.md) — knowledge-transfer: read-only recon of dgx1/banyan for the self-run MD track. Key finding — the clusters support **Singularity, not unprivileged Docker** (contradicts the Q-003 assumption); both were unreachable this cycle (local rsync blocker / missing banyan config) so all facts are doc-sourced pending live verification. Scoped, PI-gated plan for p1b Step 2.
- [06-cycle003_findings_v0.md](06-cycle003_findings_v0.md) **(latest)** — Pipeline 2 (OpenUSD→MD ΔG) landed: p53-peptide `Genotype` VariantSet (off ABL T315I) + rate-limited ddMut-PPI client writing ΔΔG back as provenance-tagged `bio:` attrs; live submit worked but retrieval 500'd → honest `unavailable` (no fabricated ΔG), fixture path for the reviewable artifact. p1b Step 1 seeded: `bio:md:` schema (17 CORE incl. PI-promoted ion-conc + protonation, 7 optional) on a Protocol-layer prim. 17/17 checks pass. Q-005 filed (Docker→Singularity pivot).

## Status

Cycle-003 complete — 2 of 4 pipelines with committed artifacts. Pipeline 2 (ddMut-PPI ΔΔG) mechanics done + tested (live values pending server recovery); `bio:md:` MD-parameter representation seeded (p1b Step 1). Next: Pipeline 3 (MaBoSS emit via ΔG↔param correlation) recommended, plus unblock cluster tooling + read-only live-verification for p1b Step 2 once Q-005 is answered. See [findings v0 steering questions](06-cycle003_findings_v0.md).
