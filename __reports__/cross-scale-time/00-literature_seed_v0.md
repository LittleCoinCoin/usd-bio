# Cross-scale time integration: literature seed (v0)

2026-11-06 · topic `cross-scale-time` · seed material for the first cycle

## How this was produced, and how far to trust it

Three Haiku sub-agents searched in parallel (arXiv, web search, DuckDuckGo). Each had one angle: multi-algorithm cell simulation, MD-to-network coupling, and general multirate / co-simulation algorithms. **They read abstracts and bibliographic records, not full texts.** The coordinator did not open each source either. Treat every mechanism description as a lead to check, and every speed-up or accuracy figure as the authors' own claim. Items marked `[unverified]` are ones the agents could not confirm exist as cited. The coordinator also corrected one agent error: Karr et al. 2012 models *M. genitalium*, not JCVI-syn3A.

Per the PI's stance (INTENT §2), **nothing here is taken as a solution**. No item was found that integrates MD kinetics into a Boolean or MaBoSS network in time, rather than by passing a parameter. That absence comes from searching, not from a systematic review.

## Taxonomy by the assumption each family needs

| Family | Assumes | Representative work | Fit for usd-bio |
|---|---|---|---|
| **A. Parameter passing / averaging** | Strict timescale separation (fast scale is at quasi-steady state) | ΔΔG → Kd → rate (current p53-mdm2); HMM (E & Engquist 2003; E et al. 2007); equation-free / coarse projective integration (Kevrekidis et al. 2003, Comm Math Sci 1:715); Haseltine & Rawlings 2002 hybrid SSA (J Chem Phys 117:6959, doi:10.1063/1.1505860) | Established, but it is exactly the assumption the topic wants to test, not inherit |
| **B. Spatial resolution partition** | A region can be resolved finely and the rest coarsely, with a justified interface | Two-regime method (Flegg, Chapman & Erban 2012, J R Soc Interface 9:859, doi:10.1098/rsif.2011.0574); pseudo-compartment (Yates & Flegg 2015, arXiv:1501.02976); blending region (Yates et al. 2020, arXiv:2010.00124); AdResS (Praprotnik, Delle Site & Kremer 2005, arXiv:cond-mat/0510223); MD-GFRD (Vijaykumar et al. 2015, J Chem Phys 143:214102; 2017, arXiv:1611.09239) | The PI's "particles for the lower scale, compartments for the higher" idea. Mostly couples *space*; time follows from it |
| **C. Event-driven multi-algorithm scheduling / co-simulation** | Only that each component can step, report its next event time, and be interpolated | **E-Cell multi-algorithm, multi-timescale scheduler** (Takahashi, Kaizu, Hu & Tomita 2004, Bioinformatics 20:538, doi:10.1093/bioinformatics/btg442); GFRD (van Zon & ten Wolde 2005, PRL 94:128103); Spatiocyte (Arjunan & Tomita 2010); on-the-fly KMC (Henkelman & Jónsson 2001, doi:10.1063/1.1415500); co-simulation master algorithms: FMI Jacobi/Gauss–Seidel, F3ORNITS (arXiv:2101.09309), ECCO (arXiv:1602.06434); DEVS (Zeigler) `[not searched]` | Needs no scale separation, so it is the natural home for a unit-invariant design. Error control across heterogeneous steppers is the open part |
| **D. Parallel-in-time** | A cheap, reasonably accurate coarse propagator | Parareal (Lions, Maday & Turinici 2001) `[not searched]`; stochastic parareal (Pentland et al. 2021, arXiv:2106.10139; arXiv:2502.12909); PFASST-ER (arXiv:1912.00702); RandNet-Parareal (arXiv:2411.06225) | Untested on stochastic biology across ps to hours. A candidate for the "new algorithm" space |
| **E. Learned time bridges** | A training distribution, plus a stability argument | Implicit Transfer Operator learning (Schreiner, Winther & Olsson 2023, arXiv:2305.18046); multiscale graph-network CG-MD (arXiv:2204.10348); learned HMM micro-solvers with an error proof (arXiv:2507.13902) | The weakest evidence (stability, out-of-distribution), but ITO targets multiple time resolutions directly |
| **F. Fine-scale kinetics extraction** (feeds A or C) | Enough sampling to resolve the transitions | SEEKR / SEEKR2 (MD milestoning + BD; Votapka et al. 2017, Biophys J); weighted-ensemble milestoning (arXiv:2007.09325); MSMs (Bowman, Pande & Noé 2014, doi:10.1007/978-94-007-7606-7); MSM/RD (arXiv:2103.06889); BrownDye, SDA7 | Gives kon, koff and residence time, which a family-C scheduler could consume as event rates instead of Kd |

Coupling frameworks that sit across families: MUSCLE3 and the scale separation map / MML (Veen & Hoekstra 2020, doi:10.1007/978-3-030-50433-5_33; Borgdorff et al. 2013; Chopard, Borgdorff & Hoekstra 2014); MaMiCo (doi:10.1016/j.cpc.2015.10.029); preCICE v2 (arXiv:2109.14470).

## Evidence that kinetics beyond Kd matters (bears on candidate Q-B)

- The drug–target residence-time model: Copeland, Pompliano & Meek 2006 (Nat Rev Drug Discov 5:730, doi:10.1038/nrd2082), and its 10-year retrospective (doi:10.1038/nrd.2015.18), which also records where the model was over-applied.
- Residence-time PK/PD coupling (Chem Sci 2016, PMC4988406) `[authors unverified]`. This is the clearest example found of time integrated from binding kinetics up to organism scale, but it uses ODEs, not a logical network.
- p53–MDM2 kinetics: stopped-flow work with two-state binding on the ms scale (J Phys Chem B 2018, doi:10.1021/acs.jpcb.8b03876), phosphorylation effects (Sci Rep 2018, doi:10.1038/s41598-018-36589-5), and the MDM2–peptide MSM (Paul et al. 2017, doi:10.1038/s41467-017-01163-6, from the cycle-012 survey).

## Cell-level side

- MaBoSS: rates are inverse mean times, with no unit named (Stoll et al. 2012, doi:10.1186/1752-0509-6-116). PhysiBoSS 2.0 (doi:10.1038/s41540-023-00314-4) takes the MaBoSS unit as calibrated by the modeller. In both, rates are set by the modeller, not derived.
- Whole-cell models: Karr et al. 2012 (*M. genitalium*, Cell 150:389) integrates time over heterogeneous sub-models using data-derived rates, with no MD input. The JCVI-syn3A 4D model (Cell 2026) is `[not checked for molecular-kinetics input]`.

## Open problems the sources themselves name

- No generally accepted generic methodology for multiscale computing (Chopard et al. 2018, *"Multiscale modeling: recent progress and open questions"*) `[venue unverified]`.
- Integration across scales needs new mathematical and computational solutions (Fletcher & Osborne, *"Seven challenges in the multiscale modeling of multicellular tissues"*, WIREs Mech Dis) `[year and DOI unverified]`.
- The justifications of hybrid and equilibrium approximations have weaknesses (Haseltine & Rawlings 2005, J Chem Phys).
- MSM/RD: no general coupling framework yet; limited to isotropic ligands in one conformation (arXiv:2103.06889).
- Co-simulation coupling error is **not monotone in macro step size**: reducing the step can increase it (Kyllingstad 2025, arXiv:2512.13845). An adaptive cross-clock step rule cannot simply shrink the step to be safe.

## Gaps that look under-explored

1. A single master algorithm that schedules a discrete-event network (MaBoSS, DEVS) together with continuous or stochastic molecular simulation in biology. No instance surfaced. E-Cell 3 is the nearest, and it predates MaBoSS.
2. Stochastic multirate or parallel-in-time coupling across ps to hours. Stochastic parareal exists, but no biology application surfaced.
3. Formal error and stability propagation across coupled stochastic clocks. Such proofs exist for HMM with learned micro-solvers, but not for chemical-master-equation co-simulation.
4. Feeding kinetics (koff, residence time) rather than Kd into a logical network as event rates.
5. Unit invariance as an explicit test criterion. The search found no paper that states it as one.

## Could not verify

Author lists for SEEKR, MSM/RD, SDA7, PMC4988406 and PMC5567610; the venues of Borgdorff et al. 2013, Chopard et al. 2014 and 2018, and Fletcher & Osborne; the Karr 2012 DOI; the eGFRD details; the scheduler error control in Takahashi et al. 2004. MCell, Smoldyn, VCell and COPASI hybrid modes were not searched, and DEVS, Time Warp and parareal were cited from memory. A PaCS-MD koff estimate for MDM2 is mentioned on a Tokyo Tech page (Kitao lab), but no paper was found.
