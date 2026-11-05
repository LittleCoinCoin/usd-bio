---
topic: cross-scale-time
created: 2026-11-05
---
# Brief

> Drafted by the agent on 2026-11-06 from the PI's Q-020 answer (p53-mdm2) during an attended session. **PI to review and amend before the first cycle.**

## Goal — algorithms for integrating time across biological scales

Find, design and test algorithms that let heterogeneous biological models running on different clocks advance *together* as one composed simulation: molecular dynamics (fs–µs), molecular kinetics (MSM, kinetic Monte Carlo), cell-level networks (MaBoSS / Boolean, hours), and later tissue or agent models (days). The aim is a method usd-bio can carry as data: each model keeps its own clock, and the coupling rule is explicit, inspectable and testable.

This is a **research topic**, not a technology demonstration. `p53-mdm2` keeps its current stance (one-way parameter passing ΔΔG → Kd → MaBoSS rate, each layer on its own clock) and is a candidate testbed and consumer, not something this topic edits.

## PI stance (2026-11-06)

1. **Units are not the question.** The time unit of any one model (e.g. 1 MaBoSS step = 1 h, accepted as the working value in `p53-mdm2`) is a declared conversion, not a design decision. The framework must work whatever the frames' units are; how many orders of magnitude a unit spans is a unit-conversion problem, not an architectural one.
2. **The state of the art is not settled.** Many groups are still trying to solve this. Treat published methods as inspiration, not as the answer, unless there is strong evidence one works in practice at scale. The cycle-012 survey (parameter passing; on-the-fly kinetic Monte Carlo, Henkelman & Jónsson 2001) is one family among several.
3. **The search space is wide and under-explored.** Few people have spent long on this, and better algorithms probably exist. Known families include:
   - the multi-algorithm, multi-timescale discrete-event scheduling of E-Cell (Takahashi, Kaizu, Hu & Tomita 2004, *Bioinformatics*; the PI's PI);
   - hybrid particle-based (fine scale) / compartment-based (coarse scale) simulation;
   - new, untested algorithmic ideas, which are in scope.
4. **The hard limit is physical**, not algorithmic: causality and relative physics bound what any coupling can do.

## Working distinction (agent, for PI review)

Two things are easy to conflate:

- **Unit** — how many seconds one tick of a model's clock represents. A declared scale factor. Changing it must leave the composed result unchanged (*unit invariance*), and that is testable.
- **Timescale separation** — the ratio between the characteristic times of the coupled *processes* (e.g. MDM2 unbinding vs. a p53 pulse). It is dimensionless, so it does not depend on units. It is a property of the biology, and it decides which coupling assumptions hold (quasi-steady state, averaging, or none).

The PI's point 1 is about the first. The cycle-012 claim that "the coarse model only sees equilibrium occupancy" is about the second. A framework should be unit-invariant by construction and should *measure* the separation rather than assume it.

## Scope

- **In:** a literature map with verified citations and a taxonomy of coupling algorithms by the assumption each needs; a precise problem statement (what "correct" means for a composed clock); Python prototypes of several schedulers on a toy multiscale system where the separation ratio can be tuned and a ground truth computed; then the p53-mdm2 system as a real case. Also: how a cross-scale clock is expressed in USD (layer offsets, `timeCodesPerSecond`, value clips, a `bio:time:` namespace), and how unit invariance is tested.
- **Out:** C++ schema authoring; edits to `p53-mdm2` deliverables; new production MD campaigns unless a cycle plans one and the PI approves it.

## Candidate first questions (PI picks)

- **(Q-A) Benchmark first.** Build a toy coupled system (a fast binding reaction driving a slow stochastic switch) with a tunable separation ratio and an exact reference solution. Score each candidate algorithm on accuracy, cost and unit invariance as the ratio varies.
- **(Q-B) Does kinetics matter beyond Kd?** For p53-MDM2 mutants at equal ΔΔG, do koff or residence time change MaBoSS phenotype probabilities, or does Kd alone decide? (Proposed in p53-mdm2 Q-020.)

## Seed material

- `__reports__/p53-mdm2/19-cycle012_findings_v0.md` §"What the literature says": the cycle-012 survey.
- `__reports__/cross-scale-time/00-literature_seed_v0.md`: the 2026-11-06 broader search (three parallel searches: multi-algorithm cell simulation, MD-to-network coupling, general multirate / co-simulation algorithms).

## Done definition (draft)

A research topic has no fixed end. A first milestone is: (1) the literature map and taxonomy; (2) a written problem statement with a unit-invariance criterion; (3) at least two algorithms prototyped and benchmarked against ground truth on the toy system; (4) a recommendation for how usd-bio represents cross-scale time, with read-back tests.
