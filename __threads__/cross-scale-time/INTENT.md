---
topic: cross-scale-time
created: 2026-11-05
---
# Brief

> Drafted by the agent on 2026-11-06 from the PI's Q-020 answer (p53-mdm2) and the PI's correction in the same attended session. **PI to review and amend before the first cycle.**

## Goal — derive higher-scale parameters from lower-scale *dynamics*

Find, design and test methods that use the dynamics of a low-scale model to derive the parameters of a higher-scale model. In the running example, that means deriving MaBoSS transition rates for p53–MDM2 from molecular dynamics (MD) or molecular kinetics.

The method works **after the fact**. The low-scale dynamics are computed first. They are then aligned with the higher-scale model's time axis and fitted to give its parameters: a kind of *dynamics fitting*. The scales are not co-simulated, and the higher-scale model never waits on MD steps.

The question is what can be passed up beyond what equilibrium thermodynamics already gives (ΔΔG → Kd), and how to align two dynamics with different clocks well enough to fit one to the other.

This is a **research topic**, not a technology demonstration. `p53-mdm2` keeps its current one-way parameter passing (ΔΔG → Kd → MaBoSS rate) as the baseline. It is the first testbed and consumer; this topic does not edit it.

## PI stance (2026-11-06)

1. **Not a composed, lock-step simulation.** The goal is not to make clocks advance together. Discrete-event simulation (e.g. the E-Cell multi-algorithm, multi-timescale scheduler, Takahashi, Kaizu, Hu & Tomita 2004) is cited because it has succeeded for *composed* simulations. It is inspiration, not the target architecture.
2. **Thermodynamics is not the whole answer.** It is sometimes said to have solved this already. It gives equilibrium quantities, and this topic is after something different: what the *dynamics* carry.
3. **Units are not the question.** The time unit of any one model (e.g. 1 MaBoSS step = 1 h, accepted as the working value in `p53-mdm2`) is a declared conversion, not a design decision. The method must work whatever the frames' units are; orders of magnitude are a unit-conversion problem.
4. **The state of the art is not settled.** Many groups are still working on this. Treat published methods as inspiration unless there is strong evidence one works at scale. New, untested ideas are in scope.

## Working distinction (agent, for PI review)

What is passed up from the low scale falls into one of two kinds:

- **Equilibrium quantities**: ΔG, Kd, fraction bound. These are what thermodynamics provides, and the current baseline.
- **Dynamic quantities**: rates (kon, koff), residence times, waiting-time distributions, memory (non-Markovian effects) and transient responses. These need the dynamics themselves, and they need a time alignment between the two scales.

Fitting a Markovian rate to a higher-scale model is only valid when the lower-scale process looks memoryless at the higher-scale resolution. That depends on the ratio between the processes' characteristic times. This ratio has no unit, so it survives any change of units. The method should therefore **measure** whether a memoryless rate is adequate rather than assume it. It should also be **unit-invariant** by construction: rescaling either clock must leave the fitted predictions unchanged, and that can be tested.

## Scope

- **In:**
  - a literature map of "dynamics fitting" methods, with verified citations;
  - a precise problem statement: what is aligned, what is fitted, and what makes a fit good;
  - Python prototypes on a toy two-scale system with a known ground truth, then on p53–MDM2;
  - how the derived parameters and the alignment are recorded in USD as provenance (e.g. the `bio:` namespace, layer offsets, value clips).
- **Out:** lock-step co-simulation; C++ schema authoring; edits to `p53-mdm2` deliverables; new production MD campaigns unless a cycle plans one and the PI approves it.

## Candidate first questions (PI picks)

- **(Q-A) Toy benchmark.** Build a toy system: a fast binding process drives a slow stochastic switch. The ratio between their timescales can be tuned, and an exact reference solution exists. Fit the switch model's parameters from the fast process's trajectories using several candidate methods. Score each on three things: does the fitted model reproduce the reference, is the fit unit-invariant, and at what ratio does a memoryless rate stop being adequate?
- **(Q-B) Does kinetics matter beyond Kd?** For p53–MDM2 mutants at equal ΔΔG, do koff or residence time change MaBoSS phenotype probabilities, or does Kd alone decide? (Proposed in p53-mdm2 Q-020.)

## Seed material

- `__reports__/p53-mdm2/19-cycle012_findings_v0.md` §"What the literature says": the cycle-012 survey.
- `__reports__/cross-scale-time/00-literature_seed_v0.md`: the 2026-11-06 broader search. It was run under the earlier co-simulation framing. Its families F, A and E are the relevant ones here. It does **not** yet cover the core "dynamics fitting" literature (temporal coarse-graining, memory kernels, system identification, simulation-based inference).

## Done definition (draft)

A research topic has no fixed end. A first milestone is:

1. a literature map of dynamics-fitting methods;
2. a written problem statement with a unit-invariance criterion;
3. at least two methods prototyped and benchmarked against ground truth on the toy system;
4. a p53–MDM2 comparison of dynamics-derived parameters against the ΔΔG → Kd baseline, recorded in USD with provenance and read-back tests.
