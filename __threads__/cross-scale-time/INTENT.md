---
topic: cross-scale-time
created: 2026-11-05
---
# Brief

## Goal — derive higher-scale parameters from lower-scale *dynamics*

Find, design and test methods that use the dynamics of a low-scale model to derive the parameters of a higher-scale model. The running example derives MaBoSS transition rates for p53–MDM2 from molecular dynamics (MD).

The method works **after the fact**. The low-scale dynamics are computed first, then aligned with the higher-scale model's time axis and fitted to give its parameters: a kind of *dynamics fitting*. The scales are not co-simulated, and the higher-scale model never waits on low-scale steps.

The question is twofold:
- what can be passed up beyond stationary summaries (for molecules, what equilibrium thermodynamics gives: ΔΔG → Kd);
- how to align two dynamics with different clocks well enough to fit one to the other.

This is a **research topic**, not a technology demonstration. `p53-mdm2` keeps its current one-way parameter passing (ΔΔG → Kd → MaBoSS rate) as the baseline. It is the first testbed and consumer; this topic does not edit it.

## Stance

1. **Not a composed, lock-step simulation.** The goal is not to make clocks advance together. Discrete-event simulation (e.g. the E-Cell multi-algorithm, multi-timescale scheduler, Takahashi, Kaizu, Hu & Tomita 2004) is cited because it has succeeded for *composed* simulations. It is inspiration, not the target architecture.
2. **Thermodynamics is not the whole answer.** It is sometimes said to have solved this already. It gives equilibrium quantities, and this topic is after something different: what the *dynamics* carry.
3. **Units are not the question.** The time unit of any one model (e.g. 1 MaBoSS step = 1 h, accepted as the working value in `p53-mdm2`) is a declared conversion, not a design decision. The method must work whatever the frames' units are; orders of magnitude are a unit-conversion problem.
4. **The state of the art is not settled.** Many groups are still working on this. Treat published methods as inspiration unless there is strong evidence one works at scale. New, untested ideas are in scope.
5. **Not only biology's scale gaps.** The method must not overfit to molecular and chemical kinetics. The same question arises between human dynamics and planetary (climate) dynamics, where kinetics vocabulary does not fit. The aim is the level of abstraction that transfers across scale gaps without becoming too abstract to apply anywhere.

## Working vocabulary (rough draft)

This is a rough first sketch to paint the picture of the topic, not a specification. Expect the terms, the table and the guard below to change as the work progresses or the problem is reframed.

Each term comes with an instance from two different scale gaps, so that the vocabulary can be checked against both overfitting and over-abstraction.

| Term | Meaning | Molecule → cell (p53–MDM2) | Human → planet (illustrative) |
|---|---|---|---|
| **Low model L** | Produces trajectories on its own clock | MD of the p53–MDM2 complex | An agent-based model of human activity |
| **High model H** | Has parameters θ and its own clock | MaBoSS network | A climate or integrated-assessment model |
| **Projection π** | What of L's state H can see | bound / unbound state | aggregate emissions, land use |
| **Time map τ** | How L's time is placed on H's axis: unit conversion, offset, and the aggregation window or warping | ps → h, averaged over a MaBoSS step | days → years, annual aggregation |
| **Summary s** | What is extracted from π(L) to fit θ. Either *stationary* (averages, equilibria) or *dynamic* (rates, waiting-time distributions, response functions, autocorrelation and memory, transients) | Kd (stationary) vs koff and residence time (dynamic) | mean emission rate (stationary) vs adoption curves and response lags (dynamic) |
| **Fit θ = f(s)** | The rule that turns s into H's parameters | residence time → node rate | adoption curve → pathway parameters |
| **Adequacy** | Does H with fitted θ reproduce π(L) at H's resolution? Does H's state at that resolution carry enough of L's history to predict its future (the closure, or Markov, condition)? | Is a memoryless MaBoSS rate enough? | Is a lag-free emission parameter enough? |
| **Feedback** | Whether H also drives L | none in p53-mdm2 (one-way) | strong: climate changes human behaviour |

Two properties follow and must be testable:
- **Unit invariance:** rescaling either clock leaves the fitted predictions unchanged.
- **Measured adequacy:** whether a stationary summary suffices, or what kind of dynamic summary is needed, is measured, not assumed. It depends on dimensionless ratios between the two models' characteristic times, so it survives any change of units.

**Abstraction guard.** A concept enters the method only if it (i) has an instance in at least two scale gaps from different domains, and (ii) maps to a computable test on the toy system below. Failing (i) means it is overfitted to one gap; failing (ii) means it is too abstract to apply.

## Scope

- **In:**
  - a domain-neutral problem statement in the vocabulary above;
  - a literature map of dynamics-fitting methods, drawn from any field (molecular kinetics, statistical physics, system identification, econometrics, climate and Earth-system modelling), with verified citations;
  - Python prototypes on a domain-neutral toy system with a known ground truth;
  - the p53–MDM2 system as the first real instance;
  - how L, H, π, τ, s and θ are recorded in USD as provenance.
- **Out:**
  - lock-step co-simulation;
  - building non-biological instances such as human → climate. These are used as a paper check on the abstraction, not as deliverables;
  - feedback (H → L) in the first milestone;
  - C++ schema authoring; edits to `p53-mdm2` deliverables; new production MD campaigns unless a cycle plans one and it is approved.

## Candidate first questions

- **(Q-A) Toy benchmark.** A domain-neutral toy system: a fast stochastic process L modulates a slow process H. The ratio between their characteristic times can be tuned, and an exact reference solution exists. Fit θ from π(L) with several candidate methods and summaries. Score each on three things: does the fitted H reproduce the reference, is the fit unit-invariant, and at what ratio does a stationary summary stop being adequate?
- **(Q-B) When do dynamic summaries matter?** Where stationary summaries agree, do dynamic ones change H's predictions? First instance: for p53–MDM2 mutants at equal ΔΔG, do koff or residence time change MaBoSS phenotype probabilities, or does Kd alone decide?
- **(Q-C) Paper check of the abstraction.** Before prototyping, write the vocabulary out for three scale gaps (molecule → cell, cell → tissue, human → planet) and record where it breaks.

## Seed material

- `__reports__/p53-mdm2/19-cycle012_findings_v0.md` §"What the literature says": the cycle-012 survey.
- `__reports__/cross-scale-time/00-literature_seed_v0.md`: coupling methods from molecular and biological sources. Its families F, A and E are the relevant ones. It does **not** cover the core dynamics-fitting literature, nor any non-biological field.

## Done definition

A research topic has no fixed end. A first milestone is:

1. a literature map of dynamics-fitting methods across fields;
2. a domain-neutral problem statement with unit-invariance and adequacy criteria, instantiated for at least two scale gaps;
3. at least two methods prototyped and benchmarked against ground truth on the toy system;
4. a p53–MDM2 comparison of dynamics-derived parameters against the ΔΔG → Kd baseline, recorded in USD with provenance and read-back tests.
