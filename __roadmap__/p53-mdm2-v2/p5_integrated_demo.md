# P5 Integrated Demonstration

**Goal**: Wire the four pipelines into a single runnable demonstration that, from a variant selection, drives MD/ΔG → USD → ddMut-PPI ΔΔG → ΔG↔parameter-correlated MaBoSS model → MaBoSS run → node-state time series back onto the same USD stage — the "integrated MD + systems-biology consultation" the INTENT names as the done definition.

**Pre-conditions**:
- [ ] Pipelines 1–4 each pass their own read-back tests
- [ ] A single composed stage carries topology (P1), ΔΔG `bio:` attrs (P2), the correlation parameters (P3), and the time-sampled node states (P4) across departmental SubLayers

**Success Gates**:
- ⬜ One entry-point script runs the full chain for at least a wild-type + one destabilizing p53-peptide variant
- ⬜ The destabilizing variant demonstrably shifts the MaBoSS p53 dynamics via the ΔG↔parameter correlation (the whole thesis: MD ΔG steering a systems-biology model through USDBio)
- ⬜ All committed `.usda` artifacts present; the full read-back suite passes (unit of "done" per INTENT)
- ⬜ A demo README/walkthrough explains the four hops and the LIVERPS mapping, consistent with the design vision

**References**: [INTENT.md §Done definition](../../__threads__/p53-mdm2/INTENT.md), [design vision](../../__design__/openusd_for_research_architecture.md)

## Step 1: End-to-end orchestration script
**Goal**: One entry-point script that drives all four pipelines for at least a wild-type + one destabilizing p53-peptide variant and commits the resulting integrated stage.
**Implementation Logic**:
The script composes the four hops in order (topology+protocol, genotype+ΔΔG, MaBoSS emit, MaBoSS run+read-back) onto one stage as per-hop functions rather than one monolith, so each hop can also be exercised independently by the integrated test suite.
**Deliverables**: `examples/p53_mdm2/demos/run_end_to_end.py`, committed integrated `.usda`
**Consistency Checks**: `. ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import os; from p53_mdm2.demos.run_end_to_end import run_end_to_end, default_integrated_path; assert os.path.isfile(default_integrated_path())"` (expected: PASS)
**Commit**: `feat(p53-mdm2): end-to-end p53-MDM2 integrated demonstration`

## Step 2: Integrated read-back suite + walkthrough
**Goal**: A read-back suite that opens the committed integrated stage fresh and asserts all four hops against independent oracles, plus a walkthrough documenting the four hops and their LIVERPS mapping.
**Implementation Logic**:
Each hop is checked against an oracle built independently of the demo builder (never against `DemoResult` values) — an independently re-derived PDB oracle for topology, the verbatim captured ddMut-PPI response or fixture for ΔΔG, an inline-recomputed logistic for the correlation, and MaBoSS's own reported probabilities for the dynamics — so a chimeric or self-agreeing demo cannot pass.
**Deliverables**: `examples/p53_mdm2/tests/test_integrated.py`, `examples/p53_mdm2/README.md` update
**Consistency Checks**: `. ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples:$(pwd)/examples/p53_mdm2/tests" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import test_integrated as t; rows = t.run(); import sys; sys.exit(0 if all(r.passed for r in rows) else 1)"` (expected: PASS)
**Commit**: `test(p53-mdm2): integrated end-to-end read-back suite + walkthrough`
