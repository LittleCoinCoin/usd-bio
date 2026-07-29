# p53-mdm2-v2

## Context
This campaign builds the runnable, multi-scale **p53–MDM2 demonstration** in which OpenUSD is the shared representation tying molecular dynamics to systems-biology (MaBoSS Boolean-network) modelling, across the four pipelines defined in `__threads__/p53-mdm2/INTENT.md`. It **supersedes `__roadmap__/p53-mdm2/`**, which became structurally unusable: all 8 of its files failed `dirtree-rdm validate`, so no status update or amendment could be applied, and its Mermaid node IDs were abbreviations rather than filesystem stems, which makes `dirtree-rdm update` unable to resolve six of its seven nodes even after a grammar repair. Rather than patch a frozen graph, the campaign is re-founded here with every node carried across and nothing dropped — audited row-by-row in R12 before the old campaign is retired. The parity target for the USD design remains [the design vision](../../__design__/openusd_for_research_architecture.md) (LIVERPS → research mapping: implement, don't rewrite); new work lands under `examples/p53_mdm2/`, and `foundation_demo_v8/` is inspiration, **not** a copy source.

## Reference Documents
- [R00 cycle-000 architecture + reuse map](../../__reports__/p53-mdm2/00-architecture_v0.md) — v8 asset classification, external-input decisions (1YCR, MaBoSS 5-node model, ddMut-PPI), anti-chimera invariants
- [R01 MD reproducibility survey](../../__reports__/p53-mdm2/01-md_reproducibility_survey_v0.md) — SOTA for sharing MD setup parameters; the recommended `bio:md:` schema
- [R02 ΔG↔MaBoSS correlation design](../../__reports__/p53-mdm2/02-dg_maboss_correlation_v0.md) — governing MaBoSS parameter, correlation function + inverse, round-trip test design
- [R07 cluster live verification](../../__reports__/p53-mdm2/07-cluster_liveverify_v1.md) — first live recon of banyan/dgx1; superseded on fakeroot and disk by R10
- [R10 cluster state refresh](../../__reports__/p53-mdm2/10-cluster_state_refresh_v0.md) — read-only refresh; CPU models, GPU occupancy, the missing subuid mapping; wins over R07 where they disagree
- [R11 cycle-006 findings](../../__reports__/p53-mdm2/11-cycle006_findings_v0.md) — all four pipelines plus the P5 demo on live ddMut-PPI ΔΔG; 39/39 read-back checks

## Goal
Run the full end-to-end p53–MDM2 demonstration across all four pipelines (MD/ΔG → USD → ddMut-PPI ΔΔG → binarized MaBoSS model → MaBoSS run → results back onto USD), with committed `.usda` artifacts and passing falsification-resistant read-back tests as the unit of "done", and deliver the containerized GROMACS runtime that lets the project run its own MD.

## Pre-conditions
- [x] cycle-000 reuse map + external-input decisions filed (R00)
- [x] forOUSD interpreter available (`/Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3` + `PYTHONPATH`) carrying both `pxr` and `mdtraj`
- [x] PI decision on the self-run-MD track (Q-003): **YES** — critical path
- [x] PI decision on topic structure (Q-004): lead all four pipelines in this single topic, no split
- [x] Q-006 answered (2026-07-29): container builds stay PI-attended; other clean work attempted unattended with escalation through the umbod question path
- [x] Q-007 answered (2026-07-29): Route B (Docker build → `docker save` → `singularity build docker-archive://`) confirmed by observation; Route A dead
- [ ] R12 migration audit signed off by the PI, gating retirement of `__roadmap__/p53-mdm2/`

## Success Gates
- ✅ `examples/p53_mdm2/` package exists with no `/ABLComplex` literal and no dataset atom-count in library code (anti-chimera invariant, R00)
- ✅ Pipeline 1 emits a committed topology `.usda` for 1YCR with passing read-back tests
- ✅ Pipeline 2 writes ddMut-PPI ΔΔG per p53-peptide variant back onto USD as `bio:` attributes, rate-limited and provenance-tagged, never fabricated
- ✅ Pipeline 3 emits a `.bnd`/`.cfg` pair whose governing parameter is set by the ΔG↔parameter correlation, round-tripping against the PI-provided reference files
- ✅ Pipeline 4 reads MaBoSS node-state/probability time series back as time-sampled `bio:` attributes in an analysis SubLayer
- ✅ Integrated demonstration runs the full chain with committed artifacts + passing read-back tests
- ⬜ A GROMACS `.sif` on the shared NFS home, demonstrated to execute GROMACS on a real GPU, with its CUDA SASS targets observed rather than asserted
- ⬜ `examples/p53_mdm2/cluster/` describes observed cluster reality, and the `Dockerfile`↔`gromacs.def` pin agreement is enforced by a test rather than by convention
- ⬜ Design stays "useful, reusable, not over-engineered" — a minimal core plus optional extensions, not an exhaustive dump

## Gotchas
- **Depth here encodes *remaining* execution order, not history.** The six completed pipeline leaves sit as depth-0 siblings because they are done. Their historical dependency order was `f1_scaffold → p1_topology_from_1ycr → { p2_ddg_pipeline, p1b_md_parameter_representation } → p3_maboss_emit → p4_maboss_readback → p5_integrated_demo`. The superseded campaign tried to encode that with Mermaid `-->` edges between siblings, which the grammar forbids precisely because siblings are *parallel* by definition — a flat 7-leaf graph asserts all seven pipelines run at once. Prose is the correct home for that ordering. Only live work is nested, and depth is spent on **artifact boundaries** (something that does not yet exist), never on "this comes after that" — sequential steps belong inside one leaf, capped at five.
- **`p1b_md_parameter_representation` Step 2 is delegated.** Its containerized-execution half is decomposed under `p1b_container_runtime/`; the Step closes when that subtree's gates pass. Watch the historical drift: the original Step 2 prose said "dgx1/banyan have no Singularity; use Docker", which Q-005 and Q-007 reversed — Docker *builds* on banyan, Singularity *runs* on both.
- **Cluster work is permission-split, not preference-split.** Anything that writes to a cluster or submits a job is PI-attended per Q-006. Read-only cluster verification is unattended-safe, which is why `dgx1_sif_open_check` is deferrable while the dgx1 GPU smoke test is deliberately out of scope.
- **Evidence files must never end in `.log`.** `.gitignore:99` is `*.log`, so a captured `md.log` is silently untracked. Use `…_md.log.txt`. Verify with `git check-ignore -v` before trusting any capture.
- **The `run_tests.py` harness has no skip concept** — `_rows_from` reads `passed` as a bool. A cluster-evidence test module must return zero rows when its evidence directory is absent, or the suite goes permanently red.

## Status
```mermaid
graph TD
    migration_verification[Roadmap Migration Verification]:::planned
    f1_scaffold[F1 Scaffold + Anti-Chimera Contracts]:::done
    p1_topology_from_1ycr[P1 MD to USD — Topology from 1YCR]:::done
    p1b_md_parameter_representation[P1b MD-Parameter Representation]:::inprogress
    p2_ddg_pipeline[P2 USD to ddMut-PPI to Delta-Delta-G]:::done
    p3_maboss_emit[P3 USD to MaBoSS — Correlation + Emit]:::done
    p4_maboss_readback[P4 MaBoSS to USD — Time-Sampled Attrs]:::done
    p5_integrated_demo[P5 Integrated Demonstration]:::done
    p1b_container_runtime[P1b Container Runtime Validation]:::planned
    classDef done       fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned    fill:#374151,color:#e5e7eb
    classDef amendment  fill:#1e3a5f,color:#bfdbfe
    classDef blocked    fill:#7f1d1d,color:#fecaca
```

## Nodes
| Node | Type | Status |
|:-----|:-----|:-------|
| `migration_verification.md` | 📄 Leaf Task | ⬜ Planned |
| `f1_scaffold.md` | 📄 Leaf Task | ✅ Done |
| `p1_topology_from_1ycr.md` | 📄 Leaf Task | ✅ Done |
| `p1b_md_parameter_representation.md` | 📄 Leaf Task | 🔄 In Progress |
| `p2_ddg_pipeline.md` | 📄 Leaf Task | ✅ Done |
| `p3_maboss_emit.md` | 📄 Leaf Task | ✅ Done |
| `p4_maboss_readback.md` | 📄 Leaf Task | ✅ Done |
| `p5_integrated_demo.md` | 📄 Leaf Task | ✅ Done |
| `p1b_container_runtime/` | 📁 Directory | ⬜ Planned |

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|
| A0 | 2026-07-29 | `__threads__/p53-mdm2/QUESTIONS.md` Q-006 + Q-007 answers (PI, 2026-07-29); audited by R12 | all — 7 leaves carried from `__roadmap__/p53-mdm2/` plus `migration_verification` and the `p1b_container_runtime/` subtree | Founding. Re-founds the campaign because `__roadmap__/p53-mdm2/` became unmutable: all 8 of its files failed `dirtree-rdm validate`, and its Mermaid node IDs were abbreviations rather than filesystem stems, so `dirtree-rdm update` could not resolve 6 of 7 nodes even after a grammar repair. Carries every node across, corrects `p4`/`p5` to done per R11, and decomposes `p1b` Step 2's container work now that Q-007 confirmed Route B by observation. Retirement of the old campaign is gated on PI sign-off of R12. |

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
