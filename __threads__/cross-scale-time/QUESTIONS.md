# Questions

## Q-001 ADEQUACY FOR p53-MDM2: which H observable and tolerance define 'adequate'? Options: (a) H's mean waiting time, (b) the full waiting-time distribution, (c) MaBoSS phenotype probabilities at a fixed time. On the toy, a single memoryless rate (the MaBoSS form) gets the mean right at every timescale ratio but fails the distribution (KS>0.05) from eps~1. So (a) means one MaBoSS rate is enough, and (b) can need a phase-type H, i.e. a hidden node. A related point: report 02 finds the p53 baseline has no readout rho, since pi sets a parameter of H rather than a state of H. Adequacy tests A1 (reproduction) and A2 (closure) are then not computable against MD, and only A3 (perturbation response) is. Should rho, and the coupling pattern (state / parameter / forcing), enter the vocabulary? And should p53 adequacy come from adding a binding sub-model to H, or from A3 alone? [source: __reports__/cross-scale-time/02-problem_statement_v0.md, 03-toy_benchmark_findings_v0.md]
*asked: cycle-000*
*priority: soft*
*answer:*

## Q-002 UNITS STANCE 3 under dynamic summaries. Report 02 shows that the p53 baseline is unit-invariant only because Kd carries no time dimension. Once a dynamic summary (a rate or waiting time from MD) sets ONE MaBoSS rate while the network's other rates stay hand-set, the declared '1 step = 1 h' stops being a free unit and becomes a calibration. Choose: (a) re-express all MaBoSS rates in physical time first; (b) accept the 1 h unit as a calibration and record it as such in USD; (c) reword INTENT stance 3 to 'units are free only for dimensionless summaries'. The toy confirms exact unit invariance (to ~5e-14) only when every time-carrying parameter is rescaled together. [source: __reports__/cross-scale-time/02-problem_statement_v0.md §unit invariance; 03-toy_benchmark_findings_v0.md]
*asked: cycle-000*
*priority: soft*
*answer:*

## Q-003 TIME-MAP CONVENTION for the USD provenance record. On the toy, the aggregation window matters as much as the operator. The INTENT's own operator ('averaged over a MaBoSS step') biases the best method (lag-generator) by +8% at a window of one L relaxation time and +38% at three, while snapshots stay within 0.5%. Declaring the window in L units, rather than physical/H units, breaks unit invariance (2.2% at a factor of 10, 787% at a factor of 1e3). Proposed default: snapshot sampling plus a lag-generator fit, the window declared in physical time with its unit, a sensitivity sweep over [w0/4, 4 w0] that must plateau (W1-W4 in report 02), and a ceiling of ~0.1 L-relaxation times for dwell-time summaries. Accept this default, or set the plateau tolerance and grid yourself? [source: 03-toy_benchmark_findings_v0.md; 02-problem_statement_v0.md W1-W4]
*asked: cycle-000*
*priority: soft*
*answer:*

## Q-004 NEXT TOY: the current toy is exactly representable by the dynamic methods (M2ph, M3ph), so their success is expected. It does not test the Markov/closure half of adequacy. Proposed for cycle-001: a misspecified toy, a 3-state L with a hidden state projected onto 2 observed states, with a multi-lag Chapman-Kolmogorov check and indirect inference as a fourth method. Alternatives: (b) a forced, non-stationary variant to exercise the offset/warp/feedback slots that report 02 kept only as declared slots; (c) move straight to done-definition item 4 (p53-MDM2). Which first? [source: 03-toy_benchmark_findings_v0.md §Uncertainty/limits; 02-problem_statement_v0.md §guard]
*asked: cycle-000*
*priority: soft*
*answer:*

## Q-005 Q-B TARGET. Report 02 predicts eps ~ 3e-7 for p53-MDM2 binding (ms binding vs 1 h MaBoSS step; order-of-magnitude anchors from abstracts, not verified), which would make 'Kd alone decides' for binding. The toy shows the controlling quantity is eps*pi0 = lambda*b/(a+b)^2, not eps alone: M1 stays within 5% only for eps*pi0 <~ 0.053, and for a mutant the check must be made at the MUTANT's eps. Also, the 100 ps job-119 trajectory gives eta = T_obs/t_L ~ 1e-7, so no dynamic binding summary can be estimated from existing MD. Should Q-B (a) confirm 'Kd decides' for binding with literature koff values, (b) target a slower L process where a dynamic summary could matter, or (c) wait for a kinetic-sampling campaign (MSM/WE), which would need a planned and approved MD run? [source: 02-problem_statement_v0.md; 03-toy_benchmark_findings_v0.md]
*asked: cycle-000*
*priority: soft*
*answer:*

