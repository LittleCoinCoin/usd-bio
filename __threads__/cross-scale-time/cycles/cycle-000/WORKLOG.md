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

## Continuity notes
