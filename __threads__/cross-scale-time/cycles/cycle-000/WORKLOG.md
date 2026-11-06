# WORKLOG — cross-scale-time cycle-000

## Decision record

First cycle of the topic (cycle start ref `6c0d57a`). INBOX and QUESTIONS are empty; no prior HANDOFF. Done-definition item 1 (literature map) already exists as `__reports__/cross-scale-time/01-dynamics_fitting_literature_v0.md`, written before the topic's first cycle. This cycle therefore takes the next two items, which are independent and run as two parallel sub-agents in isolated worktrees:

1. **Item 2 / candidate Q-C — domain-neutral problem statement.** Formalise L, H, π, τ, s, θ, adequacy as a precise problem; state unit invariance and measured adequacy as testable criteria in terms of dimensionless ratios; instantiate for three scale gaps (molecule → cell, cell → tissue, human → planet) and record where the vocabulary breaks. Folds in the four vocabulary adjustments the literature map proposed (perturbation-response adequacy, aggregation-window bias under τ, auxiliary model as a fit form, π as a modelling choice). Report `02-problem_statement_v0.md`.
2. **Item 3 / candidate Q-A — toy benchmark.** A domain-neutral fast-modulates-slow toy system with an exact reference, tunable timescale ratio, and at least two fitting methods (one stationary, one dynamic) scored on reproduction, unit invariance, and the ratio at which the stationary summary stops being adequate, plus a perturbation-response check (literature-map headline 3). Code under `examples/cross_scale_time/`, report `03-toy_benchmark_findings_v0.md`.

Out of scope this cycle, per INTENT: p53-mdm2 instance (item 4), USD provenance recording, feedback.

## Work executed

- **Problem-statement sub-agent** (isolated worktree): `b46fdad`, merged at `1389438`. Report `__reports__/cross-scale-time/02-problem_statement_v0.md` (architecture type).
  - Splits τ = A_w ∘ O_t0 ∘ C_c (+ optional warp φ); only the aggregation A_w loses information.
  - Three summary classes (one-time / multi-time / response) with a shuffle test; four fit forms.
  - Adequacy is a vector: A0 ratios ε, ω, δ, η; A1 reproduction; A2 closure; A3 perturbation response.
  - Unit invariance stated precisely; window requirements W1–W4.
  - Three-gap table (molecule → cell, cell → tissue, human → planet) and a guard verdict per term. It adds a readout ρ and finds that two of the three gaps have no ρ, so A3 is the only test that applies everywhere. The revised vocabulary is a proposal only; INTENT.md is untouched.
- **Toy-benchmark sub-agent** (isolated worktree): `67f2b55`, `4e3257e`, `9e98729`, `300ec90`, merged at `6f7d63e`.
  - Code `examples/cross_scale_time/toy_benchmark.py`, tests `examples/cross_scale_time/tests/test_toy_benchmark.py`, run `examples/cross_scale_time/outputs/run_20261106T003327Z/`, report `__reports__/cross-scale-time/03-toy_benchmark_findings_v0.md`.
  - The toy is a telegraph L gating a slow H, with an exact phase-type reference. Methods: M1 stationary, M2exp/M2ph dwell-time, M3ph lag-generator, M1c control.
  - Headlines: M1 is adequate at 5% only up to ε*≈0.079, and the controlling quantity is επ₀, not ε. Unit invariance holds to ~5e-14 when the window is declared in physical time and breaks when it is declared in L units. The window is not neutral; "averaged over a MaBoSS step" biases M3 by +8% to +38%. Base-state match ≠ response match: a slow mutant at equal occupancy gives 4.6× the reference, and M1 predicts 1.0×.
- **Coordinator checks after the merges:** the toy tests re-ran on `topic/cross-scale-time`, 6/6 PASS. The two reports use the same ε (t_L/t_H ≡ λ/(a+b)).
- **Steering questions:** 12 candidate questions from the two reports were consolidated into soft Q-001…Q-005: adequacy observable and ρ; units under dynamic summaries; time-map convention; next toy; Q-B target. Three lower-priority candidates were folded in, not asked separately: summary-class adoption, perturbation map declared or fitted, and coupling declared or fitted.
- **Not done this cycle:** done-definition item 4 (p53-MDM2 instance and USD provenance). No new literature search. Indirect inference was not prototyped.

## Verifier verdict

```
verdict: minor-concern
inbox-coverage:
  - (none) INBOX was empty. __threads__/cross-scale-time/INBOX.md holds only the "# Inbox" header, and the WORKLOG Decision record says "INBOX and QUESTIONS are empty; no prior HANDOFF". No item was acknowledged, so there was nothing to cover. Commit 0c46cf3 consumed only the pi-reviewed state flag (STATUS.md, WORKLOG.md), not an INBOX item.
intent-tracking: aligned
work-depth: The cycle committed to done-definition items 2 and 3 and goes deep on both. Item 2 is __reports__/cross-scale-time/02-problem_statement_v0.md. It formalises L, π, ρ, τ = A_w∘O_t0∘C_c, the summary classes, the fit forms and adequacy A0–A3. It applies the abstraction guard term by term (§4.4) and covers all three scale gaps that Q-C names in a sourced table (§3). It folds in the literature map's four adjustments (§4.5), and it keeps its vocabulary revision as a proposal without editing INTENT.md (§5). Item 3 is examples/cross_scale_time/toy_benchmark.py, with 6 tests in examples/cross_scale_time/tests/test_toy_benchmark.py and a seeded run in examples/cross_scale_time/outputs/run_20261106T003327Z/ that includes manifest.json and the raw and summary CSVs. It answers all three Q-A scores: reproduction, unit invariance with a negative control, and the ε* threshold, which agrees with the closed form (0.079 vs 0.0789). It adds the window and perturbation checks. The methods do not peek at the ground-truth rates: fit_all at toy_benchmark.py:222 sees only x, τ and λ. The report owns its main limits in §"Uncertainty / limits". The toy is well-specified for M2ph and M3ph, the coupling λ is given rather than fitted, the closure half of adequacy and indirect inference are untested, and phenotype probabilities are not scored. These limits feed Q-004 and Q-005 rather than being waved off. One corner was cut, in bookkeeping rather than research. __threads__/cross-scale-time/STATUS.md changed only its frontmatter state (pi-reviewed → active). Its body line still reads "cross-scale-time: scaffold topic — fill in INTENT.md with the brief.", which is stale after a cycle that delivered two milestone items. A second, cosmetic point: the WORKLOG's "6/6 PASS" claim was not re-run by the verifier, which is barred from executing work. The test count does match the six test functions in the file.
recommended-action: self-correct: rewrite the STATUS.md body line to reflect cycle-000's outcome (milestone items 2 and 3 delivered as reports 02 and 03; Q-001–Q-005 open; item 4 not started) before umbod finish-cycle, then proceed.
```

**Coordinator response:** the recommended self-correct is declined. STATUS.md is umbod-managed, and the skill's One Rule forbids hand-editing it. The body line is the CLI's scaffold text; `p53-mdm2` STATUS carries the same line after 12 cycles. The cycle's state goes into the topic through `finish-cycle --next-decision` and HANDOFF instead. The "6/6 PASS" figure was re-run by the coordinator on `topic/cross-scale-time` after the merge (see Work executed). Outcome stays `open`.

## Continuity notes

- Milestone status: item 1 (literature map, report 01) and items 2–3 (reports 02 and 03) have v0s. Item 4 (p53-MDM2 comparison plus USD provenance) has not started.
- Cycle-001 should start from the PI's answers to Q-001…Q-005. Q-004 (next toy) and Q-005 (Q-B target) decide what cycle-001 builds. The default if they stay unanswered: the misspecified 3-state hidden-L toy with a multi-lag Chapman–Kolmogorov check and indirect inference.
- The toy's τ operators and the W1–W4 window requirements (report 02) are the candidate schema for recording τ in USD provenance (Q-003).
- Literature-map gaps are still open (report 01 §"Not covered"): DTW, Kalman/particle filtering, Krusell–Smith, molecular analogues of base-state ≠ response.
