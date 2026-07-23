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

- [05-cluster_md_recon_v0.md](05-cluster_md_recon_v0.md) — knowledge-transfer: read-only recon of dgx1/banyan for the self-run MD track. Key finding — the clusters support **Singularity, not unprivileged Docker** (contradicts the Q-003 assumption); both were unreachable this cycle (local rsync blocker / missing banyan config) so all facts are doc-sourced pending live verification. **Superseded by report 07** (live-verified). Scoped, PI-gated plan for p1b Step 2.
- [06-cycle003_findings_v0.md](06-cycle003_findings_v0.md) — Pipeline 2 (OpenUSD→MD ΔG) landed: p53-peptide `Genotype` VariantSet (off ABL T315I) + rate-limited ddMut-PPI client writing ΔΔG back as provenance-tagged `bio:` attrs; live submit worked but retrieval 500'd → honest `unavailable` (no fabricated ΔG), fixture path for the reviewable artifact. p1b Step 1 seeded: `bio:md:` schema (17 CORE incl. PI-promoted ion-conc + protonation, 7 optional) on a Protocol-layer prim. 17/17 checks pass. Q-005 filed (Docker→Singularity pivot).

## Round 07–08 — cycle-004 (2026-07-21, Pipeline 3 emit + cluster live-verify)

- [07-cluster_liveverify_v1.md](07-cluster_liveverify_v1.md) — knowledge-transfer (v1, supersedes 05): **LIVE-verified** dgx1/banyan recon after the PI's Q-005 config fixes. Tooling unblocked; both clusters reachable. **Key correction:** banyan's unprivileged Docker *works* (user in `docker` group — reverses 05's inference), dgx1's does not; Singularity present on both (dgx1 3.5.2 / banyan 4.2.2). Docker→Singularity pivot **confirmed** on portability + Slurm-integration grounds. Hardware/scheduler facts all live-confirmed. Container build/convert/stage/submit enumerated as PI-gated.
- [08-cycle004_findings_v0.md](08-cycle004_findings_v0.md) — Pipeline 3 (OpenUSD→MaBoSS emit) landed: R02 ΔG↔param logistic correlation + logit inverse (`dg_correlation.py`) and a text-templating emitter (`emit_model.py`) producing byte-identical `.bnd` + `$KMn_pMCD`/`$KMn_pMC`-substituted `.cfg` per mutant, with `bio:maboss:*` write-back (inverse reconstructable from USD). Reference matches R02 exactly. 28/28 checks pass; usdchecker exit 0. p1b Step 2 substrate live-verified (report 07). Q-005 effectively resolved.

## Round 09 — cycle-005 (2026-07-24, Pipeline 4 read-back + GROMACS scaffold)

- [09-cycle005_findings_v0.md](09-cycle005_findings_v0.md) **(latest)** — Pipeline 4 (MaBoSS→OpenUSD read-back) landed → **all 4 pipelines now committed + tested**. `run_maboss.py` drives a **real MaBoSS 2.6.6 run** (external colomoto binary; the in-process `cmaboss` backend was flaky and distrusted); `build_analysis_layer.py` writes node-probability trajectories as time-sampled `bio:maboss:prob:<node>` onto a separate analysis SubLayer (base topology untouched). Deferred directional test now real and **passes**: W23A time-avg P(p53↑) 0.396 > WT 0.310 (correct sign, destabilization-monotone). 31/31 checks; verifier verdict **aligned**. Also: non-mutating **GROMACS Singularity scaffold** for p1b Step 2 (`cluster/`, PI chose GROMACS) — nothing built/uploaded/submitted; every cluster mutation stays PI-gated.

## Status

Cycle-005 complete — **4 of 4 pipelines** with committed, tested artifacts (P1 topology, P2 ΔΔG, P3 MaBoSS emit, **P4 MaBoSS read-back**). The ΔG↔MaBoSS biological expectation is verified against a real simulation (destabilizing variant releases more p53 than WT). 31/31 checks; usdchecker clean. GROMACS container scaffold ready for the PI's go (nothing mutated). Next: **P5 integrated demo** (compose topology + genotype + MaBoSS analysis on one stage for joint MD + systems-biology consultation), plus the first PI-gated GROMACS container build/smoke-submit for p1b Step 2, and (later) a live ddMut-PPI re-run to replace fixture ΔΔG. See [findings v0 steering questions](09-cycle005_findings_v0.md).
