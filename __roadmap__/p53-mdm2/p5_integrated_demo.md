# P5 — Integrated Demonstration (end-to-end)

**Goal**: Wire the four pipelines into a single runnable demonstration that, from a variant selection, drives MD/ΔG → USD → ddMut-PPI ΔΔG → ΔG↔parameter-correlated MaBoSS model → MaBoSS run → node-state time series back onto the same USD stage — the "integrated MD + systems-biology consultation" the INTENT names as the done definition.

**Pre-conditions**:
- [ ] Pipelines 1–4 each pass their own read-back tests
- [ ] A single composed stage carries topology (P1), ΔΔG `bio:` attrs (P2), the correlation parameters (P3), and the time-sampled node states (P4) across departmental SubLayers

**Success Gates**:
- ⬜ One entry-point script runs the full chain for at least a wild-type + one destabilizing p53-peptide variant
- ⬜ The destabilizing variant demonstrably shifts the MaBoSS p53 dynamics via the ΔG↔parameter correlation (the whole thesis: MD ΔG steering a systems-biology model through USDBio)
- ⬜ All committed `.usda` artifacts present; the full read-back suite passes (unit of "done" per INTENT)
- ⬜ A demo README/walkthrough explains the four hops and the LIVERPS mapping, consistent with the design vision

## Step 1: End-to-end orchestration script
**Deliverables**: `examples/p53_mdm2/demos/run_end_to_end.py`, committed integrated `.usda`
**Commit**: `feat(p53-mdm2): end-to-end p53-MDM2 integrated demonstration`

## Step 2: Integrated read-back suite + walkthrough
**Deliverables**: `examples/p53_mdm2/tests/test_integrated.py`, `examples/p53_mdm2/README.md` update
**Commit**: `test(p53-mdm2): integrated end-to-end read-back suite + walkthrough`

**References**: [INTENT.md §Done definition](../../__threads__/p53-mdm2/INTENT.md), [design vision](../../__design__/openusd_for_research_architecture.md)
