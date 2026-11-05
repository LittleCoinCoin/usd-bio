# Dynamics fitting across scales: literature map (v0)

2026-11-06 · topic `cross-scale-time` · follows `00-literature_seed_v0.md`

## How this was produced, and how far to trust it

Three Haiku sub-agents searched in parallel (arXiv, web search). Each was briefed in the INTENT's working vocabulary: low model L, high model H, projection π, time map τ, summary s, fit θ = f(s), adequacy, feedback. The three angles were:

1. temporal coarse-graining in physics and molecular science;
2. domain-agnostic statistics and system identification;
3. the same problem outside molecular biology: climate, human → planet, ecology, economics.

**Every entry rests on abstracts, listings or search snippets. No full text was read.** The arXiv API rate-limited all three agents, and DuckDuckGo returned nothing for one of them, so coverage has holes (listed at the end). The coordinator did not open the sources. Items marked `[unverified]` are ones the agents could not confirm as cited, and speed-ups or accuracy figures are the authors' own claims.

## Headline

1. **No source was found that fits one model's parameters to another model's dynamics across a scale gap and tests it at scale.** All three searches report the same. The closest are Hasselmann's stochastic climate programme and its linear-response descendants (climate), data-driven generalized Langevin equations (molecular), and indirect inference with a dynamic auxiliary model (econometrics). None has been tested across a gap in the sense of this topic. This is consistent with the topic's stance that the problem is open.
2. **Six concepts recur across at least two domains and can be computed on a toy two-process system**, so they pass the INTENT's abstraction guard (§"Concepts that pass the guard").
3. **Matching stationary statistics does not guarantee matching the response to a perturbation.** This was found independently in climate (Abramov & Kjerland 2013) and in cell → tissue biology (Metzcar et al. 2025). It bears directly on candidate question Q-B, and it suggests an adequacy test should include a perturbation, not only a fit to the base state.
4. **The time map is not neutral.** Projecting a Markov process generally makes it non-Markovian (Lade 2009). The sampling interval biases rate estimates (Honisch & Friedrich 2011; the econometric temporal-aggregation literature). Whether a coarsely sampled chain has a continuous-time generator at all is the "embedding problem", hard in general (Kingman 1962). The unit is irrelevant, as the INTENT says, but the *aggregation window* in τ is not.
5. **The vocabulary breaks in predictable places for social systems:** projection, feedback, timescale separation and the time map (§"Where the vocabulary fits and breaks").

## Concepts that pass the guard

The guard asks for an instance in at least two scale gaps from different domains, and a computable test on a toy system.

| Concept | Vocabulary slot | Instances (domain) | Toy test | Caveat |
|---|---|---|---|---|
| **Memory kernel of a projected observable**, learned from data (Mori–Zwanzig, GLE, non-Markovian closure) | s (dynamic), adequacy | Lei, Baker & Li 2016 (molecular); Kondrashov, Chekroun & Ghil 2015 (geophysics); Lin & Lu 2020 (turbulence, **no scale separation needed**); Schonfeld et al. 2026 (convective closures, learned latent memory) | linear Gaussian two-process system, where the exact kernel and autocovariance are known | Many molecular variants assume fluctuation–dissipation or Hamiltonian dynamics and fail the transfer test as stated |
| **Lag time as the time map, validated by an implied-timescale plateau or a Chapman–Kolmogorov test** | τ, adequacy | Prinz et al. 2011 (MD); VAMP, Wu & Noé 2020 (generic time series); Koopman analysis of turbulence data (Lin & Lu) | two-state chain vs. its coarse-grained chain: does the coarse model's timescale stay put as the lag grows? | Assumes stationarity; the choice of lag matters |
| **Linear response from fine-scale fluctuations** (fluctuation–dissipation, Ruelle response) | s (dynamic) | Leith 1975 and Lucarini & Sarno 2011 (climate); Chekroun, Zagli & Lucarini 2024 (jump-diffusion, ENSO); GLE/FDT models (molecular); Hairer & Majda 2010 (rigorous) | perturb a two-process linear system and compare its response with the fluctuation prediction | Classical FDT needs stationarity and near-Gaussianity. Ruelle response relaxes this, but the operator's non-normality can spoil it (Hassanzadeh & Kuang 2015) |
| **Base-state match ≠ response match** | adequacy | Abramov & Kjerland 2013 (multiscale Lorenz-96); Metzcar et al. 2025 (Boolean → agent-based, equal single-cell interventions diverge in tissue) | fit H to L's unperturbed statistics, then perturb both | Molecular instance not yet searched |
| **Projection- and sampling-induced distortion** | π, τ | Lade 2009 (projection makes Markov non-Markov; biological examples); Honisch & Friedrich 2011 (Kramers–Moyal correction for low sampling rate; turbulence); temporal-aggregation bias (econometrics) `[authors unverified]`; Netz 2024 (time filter as an explicit τ, molecular) | subsample an Ornstein–Uhlenbeck or two-state process and watch the estimated rates drift | Correction methods exist for specific estimators only |
| **Auxiliary-model summaries / indirect inference** | s, fit | Smith 1993, Gouriéroux, Monfort & Renault 1993 `[venue unverified]`, Gallant & Tauchen `[unverified]` (econometrics); Carrella, Bailey & Madsen 2018 (agent-based fishery); Drovandi 2018 (links to ABC) | AR(1) at a fine and a coarse clock, fitting an auxiliary AR to each | Model-to-model use across a scale gap was **not confirmed** in any source |

Two further concepts recur but are weaker here:
- **Quasi-steady-state / slow–fast reduction** (Hasselmann 1976; Rinaldi & Scheffer 2000 in ecology): the stationary baseline, which breaks in slow–fast cycles.
- **Multi-pattern adequacy** (pattern-oriented modelling, Grimm et al. 2005): judging a fit against several patterns at several levels at once.

## Method map by field

### Temporal coarse-graining (physics, molecular science)

| Work | What it does | Transfers? |
|---|---|---|
| Lei, Baker & Li 2016, PNAS 113:14183, arXiv:1606.02596; Grogan et al. 2019, arXiv:1912.00265 | GLE kernel fitted from MD; checked on autocorrelation and transition rates | Molecular (assumes FDT) |
| Chorin, Hald & Kupferman 2000, PNAS 97:2968 | Optimal prediction as a Mori–Zwanzig projection | In principle |
| Lin & Lu 2020, J Comput Phys, arXiv:1908.07725 | Data-driven Mori–Zwanzig **without sharp scale separation**; the choice of observable strongly affects error | Yes (data only) |
| Kondrashov, Chekroun & Ghil 2015, Physica D, arXiv:1411.4700 | Multilayer stochastic non-Markovian closures from partial observations | Yes (geophysics) |
| Netz 2024, arXiv:2409.12429 | Exact GLE for time-filtered observables: the filter *is* the time map | Molecular (Hamiltonian) |
| Xie, Qiu & E 2024, arXiv:2405.12356 | Criteria for when the Markovian limit suffices | Molecular |
| Ge, Zhang & Lei 2023, arXiv:2310.18582 | Homogeneous kernels fail; state-dependent memory needed | Molecular |
| Mehrotra, Koch & Schilling 2026, arXiv:2607.02268 | Linear memory, a potential of mean force and Kubo FDT cannot all hold exactly | Molecular |
| Wu & Noé 2020, J Nonlinear Sci, arXiv:1707.04659 (VAMP); Mardt et al. 2017, arXiv:1710.06012 (VAMPnets); Wu et al. 2016, arXiv:1610.06773; Paul et al. 2018, arXiv:1811.12551 (non-equilibrium) | Koopman singular functions; a VAMP score validates the model; the lag is the time map | Yes (data only, needs stationarity) |
| Prinz et al. 2011, J Chem Phys 134:174105 | MSM generation; Chapman–Kolmogorov and implied-timescale validation | Molecular in practice, generic in form |
| Lorpaiboon et al. 2023, arXiv:2311.07881; IGME / qMSM, J Chem Phys 159:134106 `[authors unverified]` | Memory-augmented estimators that need less data | Form transfers; tested on molecules only |

### Statistics and system identification

| Work | What it does | Model-to-model? |
|---|---|---|
| Fearnhead & Prangle 2012, JRSS B, arXiv:1004.1112; Prangle 2015, arXiv:1512.05633; Jiang et al. 2015, arXiv:1510.02175; Wiqvist et al. 2019, arXiv:1901.10230 | Choosing or learning summary statistics for ABC; no general principle exists outside special cases | No |
| Cranmer, Brehmer & Louppe 2020, PNAS 117:30055, arXiv:1911.01429 | Review of simulation-based inference | Mostly no |
| Kennedy & O'Hagan 2000, Biometrika 87:1; 2001, JRSS B 63:425, doi:10.1111/1467-9868.00294 | Multi-fidelity emulation; calibration with an explicit discrepancy term | 2000: yes, but pointwise, not dynamic |
| Andrianakis et al. 2015, PLOS Comput Biol, doi:10.1371/journal.pcbi.1003968; Vernon et al. 2014, arXiv:1405.4976 and 2018, arXiv:1801.01538 | History matching with emulators (epidemiology, galaxies, plants) | No |
| Brunton, Proctor & Kutz 2016, PNAS 113:3932, doi:10.1073/pnas.1517384113; Champion et al. 2019, PNAS 116:22445, arXiv:1904.02107 | Sparse equation discovery (SINDy), with learned coordinates in the later paper | No; "multiscale SINDy" not found |
| Friedrich–Peinke Kramers–Moyal, doi:10.1007/978-3-030-18472-8_15; Lade 2009, arXiv:0908.0975; Honisch & Friedrich 2011, arXiv:1102.5264 | Langevin reconstruction from data; projection and sampling corrections | Scale-to-scale in turbulence cascades |
| Kingman 1962; Israel, Rosenthal & Wei 2001 `[venue unverified]`; arXiv:2005.00818 | Embedding problem: does a sampled chain have a generator? | Generic |

### Outside molecular biology

| Work | L → H | Summary | Feedback |
|---|---|---|---|
| Hasselmann 1976, Tellus 28:473 `[DOI conflict: 10.1111/j.2153-3490.1976.tb00696.x vs 10.3402/tellusa.v28i6.11316]` | weather → climate | dynamic: fast autocorrelation gives damping and noise | one-way |
| Leith 1975, J Atmos Sci `[DOI unchecked]`; Lucarini & Sarno 2011, arXiv:1008.0340; Abramov & Kjerland 2013, arXiv:1305.0862; Hassanzadeh & Kuang 2015, arXiv:1511.02214 | fluctuations → forced response | dynamic: response functions | one-way |
| Berner et al. 2017, BAMS 98(3), doi:10.1175/BAMS-D-15-00268.1 | review of stochastic parameterisation | asks whether stochastic terms are validated against fine-scale statistics or only tuned | — |
| Rasp, Pritchard & Gentine 2018, PNAS 115:9684; Brenowitz & Bretherton 2018, GRL 45:6289; Zanna & Bolton 2020, GRL 47; Yuval & O'Gorman 2020, arXiv:2001.03151 | cloud-resolving / eddy-resolving → GCM closure | stationary, memoryless; poor generalisation to warmer states | yes (online) |
| Smith et al. 2018, FAIR v1.3, GMD 11:2273 | Earth-system model → impulse-response emulator | stationary | one-way |
| Beckage et al. 2018, Nat Clim Change 8:79; Moore et al. 2022, Nature 603:103 | social behaviour ↔ climate | behavioural parameters assumed or partly constrained, not fitted from a lower model | strong |
| Naumann-Woleske 2023, arXiv:2301.08135 | agent-based integrated assessment models (review) | names feedbacks, distributional effects and space as open | yes |
| Grimm et al. 2005, Science 310:987; Rinaldi & Scheffer 2000, Ecosystems 3:507 | individuals → populations; slow–fast ecology | multi-pattern; quasi-steady state | varies |
| Metzcar et al. 2025, arXiv:2501.16052; PhysiBoSS tutorial, arXiv:2406.18371 | Boolean network → agent-based tissue | thresholding; internal dynamics matter | — |

## Where the vocabulary fits and breaks

- **Fits cleanly:** weather → climate (Hasselmann, emulators) and cell → tissue. π is a spatial or ensemble average, τ is a unit conversion plus an averaging window, and stationary vs dynamic summaries separate cleanly into emulators vs linear response.
- **Projection breaks for social systems.** π is not a passive observation: the modeller chooses which variables are visible (beliefs, norms, prices). In Beckage and Moore it is an assumed functional form.
- **Feedback is close to unavoidable when L is social,** because L responds to H's outputs. Fitting θ after the fact from data generated under feedback confounds the closure with the system's own history. The INTENT's choice to exclude feedback from the first milestone holds for molecule → cell, but it will not survive human → planet.
- **Timescale separation is weak for social → climate:** policy cycles of years to decades overlap climate inertia of decades to centuries. The same happens in ecology's slow–fast cycles. Methods that need no separation (Lin & Lu's data-driven Mori–Zwanzig, Ruelle response) matter more there.
- **The time map can be a modelling choice,** not just a unit conversion, when regimes change (calendar, policy regimes). This also strains stationarity, which FDT, VAMP and Leith all assume.

Possible adjustments to the rough vocabulary, for whoever revises it:
- add *response to perturbation* as an adequacy test;
- note under τ that the aggregation window biases estimates;
- list an *auxiliary model* as one form of the fit rule;
- flag that π may be a modelling choice rather than an observation.

## Open problems the sources name

- No scale separation: memory kernels become long and hard to estimate (Lin & Lu).
- Closure stability over long horizons (Kondrashov et al.; Xie et al.), and online generalisation to unseen regimes (Rasp et al.; Brenowitz & Bretherton).
- Summary choice: no guiding principle outside special cases; the curse of dimensionality limits summary size (Jiang et al.; Prangle).
- Aggregation in time: efficiency loss and bias; projection-induced non-Markovianity; the embedding problem.
- Stochastic terms tuned rather than validated (Berner et al.).
- Behavioural uncertainty is as large as physical uncertainty in coupled social–climate models (Beckage et al.).
- Reduced models that match the base state but not the response (Abramov & Kjerland).

## Not covered or not verified

- **Not searched**, or lost to rate limits: dynamic time warping for model-to-model alignment; Kalman and particle-filter parameter estimation; heterogeneous-agent aggregation in macroeconomics (e.g. Krusell–Smith); moment closure; Schmid's DMD and Kutz's book; hidden-MSM work; follow-ups to Chorin, Hald & Kupferman; Ghil & Lucarini's review (arXiv:1910.00583, title only).
- **Not verified:**
  - the Hasselmann DOI conflict and the Leith DOI;
  - the Gouriéroux–Monfort–Renault and Gallant–Tauchen venues;
  - the authors of the temporal-aggregation review (doi:10.1111/j.1467-6419.2007.00538.x), the IGME paper and the Klippenstein–van der Vegt review (J Phys Chem B 2021, PMC8154603);
  - the content of Moore et al. and Beckage et al. beyond their abstracts;
  - whether Carrella et al. fit one model to another.
- **Molecular-side analogues** of the "base-state ≠ response" finding were not searched.
