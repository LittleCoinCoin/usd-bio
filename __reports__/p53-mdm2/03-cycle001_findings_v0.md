# p53-mdm2 — Cycle-001 Findings Synthesis (v0)

Date: 2026-07-10
Cycle: cycle-001
Author: Claude Opus 4.8 (async orchestrator)
Report type: findings (synthesis of the cycle's two design surveys + decision record)

## Executive Summary

Cycle-001 consumed the PI's cycle-000 review (answers to Q-001/Q-002), which **reframed** the topic on two axes, and turned that steering into (a) a formal four-pipeline roadmap and (b) two grounded design surveys the PI explicitly requested. No pipeline code was written this cycle — deliberately, so the roadmap and the two greenfield design decisions are settled before extraction begins (same anti-premature-chimera discipline as cycle-000).

- **Reframe 1 — MD is ΔG, not a trajectory.** No p53–MDM2 trajectory exists, and the PI questioned whether one is even needed: the MD datum the demo consumes is **ΔG** (Pipeline 2, from ddMut-PPI) `[source: __threads__/p53-mdm2/QUESTIONS.md:6]`. Optionally the project could run its **own** MD (dgx1/banyan), which would make MD **setup parameters** a greenfield USDBio concern.
- **Reframe 2 — no fixed ΔG threshold; correlate instead.** The PI rejected picking a ΔG binarization cutoff (Q-002) in favour of **correlating ΔG with the MaBoSS model's ad-hoc "hill" parameters**, ΔG being the *inverse* of that correlation `[source: __threads__/p53-mdm2/QUESTIONS.md:12]`.

## What this cycle produced

| Deliverable | Artifact | Commit |
|---|---|---|
| Four-pipeline roadmap (7 leaves) reflecting the reframe | `__roadmap__/p53_mdm2/` | `5d110ac` |
| MD reproducibility SOTA survey + `bio:md:` schema | `__reports__/p53-mdm2/01-md_reproducibility_survey_v0.md` | `f53535b` |
| ΔG↔MaBoSS correlation design (Pipeline 3) | `__reports__/p53-mdm2/02-dg_maboss_correlation_v0.md` | `ff16e93` |
| This synthesis + decision record | `__reports__/p53-mdm2/03-cycle001_findings_v0.md` | (this commit) |

## Finding 1 — the EU database is MDDB; a ~14-attr `bio:md:` core suffices

The "European-funded MD trajectory database" the PI referenced is **MDDB** (Molecular Dynamics Data Bank, EU HORIZON-INFRA-2022 #101094651) `[source: __reports__/p53-mdm2/01-md_reproducibility_survey_v0.md §"The EU database: MDDB"]`. Its metadata is a **two-tier YAML key-value tree, units mandatory, program+version mandatory** — a shape to mirror, not a frozen field list. The recommended representation is a single `/<root>/mdSetup` prim in the **Protocol SubLayer** carrying ~14 core `bio:md:` attributes (engine, forceField, waterModel, ensemble, integrator, timestep, nSteps, temperature, thermostat, barostat, pressure, electrostatics, cutoff, constraintAlgorithm) + an optional `bio:md:remd:` block for replica-exchange that maps onto the project's existing Ensemble `ReplicaID` VariantSet `[source: __reports__/p53-mdm2/01-md_reproducibility_survey_v0.md §Recommended schema]`. Every field is populated by the real ShinobuLab GENESIS decks (GENESIS/AMBER/TIP3P, PME 8 Å, VRES+HMR 3.5 fs, Bussi 310 K, 2D gREST/REUS 288 replicas) `[source: __reports__/p53-mdm2/01-md_reproducibility_survey_v0.md §"What the ShinobuLab lab actually records"]`. The design is contingency for the "run-our-own-MD" branch (Q-003) — if the demo stays ΔG-only, most of `bio:md:` is unneeded.

## Finding 2 — ΔG hooks onto `$KMn_pMCD`, via a logistic correlation with a logit inverse

The p53↔MDM2 antagonism is a hard Boolean (`p53.logic = NOT Mdm2N`), so there is no continuous knob on the inhibition edge itself; the only "hill" knobs are on Mdm2N's own activation — the `$KMn_*` family `[source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md §"The governing parameter"]`. The governing knob is **`$KMn_pMCD`** (WT=1, companion `$KMn_pMC`), which the model's own comment names the p53+MDM2C+damage case toggle. A variant's ΔΔG maps to antagonism strength `S = 1/(1+exp(−k(ΔΔG−m)))`, written into those knobs; the PI's "ΔG is the inverse of the correlation" is the logit `ΔΔG = m + (1/k)·ln(S/(1−S))`. Defaults `m=−3 kcal/mol`, `k=1.5` are deliberately ad-hoc placeholders `[source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md §"The correlation function"]`. The full `{S,m,k}` is carried on the variant prim as `bio:maboss:*` attributes so the inverse is reconstructable from USD alone. This **supersedes** the cycle-000 arch-doc's `Mdm2N.istate` TRUE/FALSE binarization contract — a documented supersession per the newer Q-002 answer, not silent drift `[source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md §"Supersession note"]`.

## Decisions recorded this cycle

- **Lead all four pipelines in THIS topic** rather than seeding separate umbod topics for pipelines 2/3/4. Rationale: the pipelines are coupled *through the shared USDBio representation*, which is the entire thesis of the topic; splitting would fragment the representation design and add the cross-topic communication overhead the PI explicitly wants to avoid. The team-leader + sub-agent model (two parallel design sub-agents this cycle) is the mechanism for absorbing the breadth. Surfaced as **Q-004** (soft) so the PI can override if breadth becomes unmanageable `[source: __threads__/p53-mdm2/QUESTIONS.md:13 "if you manage your subagents perfectly … lead the exploration directly in THIS topic"]`.
- **No pipeline code this cycle.** The reframe changed the foundations (Pipeline 1 is now topology-first; two greenfield designs were unmade); locking the roadmap + designs first is the anti-chimera discipline. Pipeline 1 topology extraction (roadmap leaf `p1_topology_from_1ycr`) is the next cycle's first executable leaf.
- **`tools/patch_stage_metadata.py` will not be carried over** (PI Q-001; moot under the forOUSD venv). Recorded in roadmap leaf `f1_scaffold` success gates.

## Steering questions filed (via `umbod ask`, not buried here)

- **Q-003 (soft)** — the self-run-MD decision: run our own p53–MDM2 MD on dgx1/banyan (making `bio:md:` critical-path, node `p1b`), or stay ΔG-only? Sub-part: should ion concentration + protonation state (not geometry-derivable) be promoted into the `bio:md:` core?
- **Q-004 (soft)** — confirm/override the "lead all pipelines here vs. split into topics" decision above.

The full open-question text and any answers live in `__threads__/p53-mdm2/QUESTIONS.md` and the `umbod questions` dashboard.

## What I am uncertain about

- **Both greenfield designs are unrun.** The `bio:md:` schema's key strings are not reconciled against MDDB's eventual released schema (MDDB publishes principles, not canonical keys) `[source: __reports__/p53-mdm2/01-md_reproducibility_survey_v0.md §uncertainty]`; the `$KMn_pMCD` attractor sensitivity is a logic-level inference not verified by a MaBoSS run `[source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md §uncertainty]`. Both are validated only when their pipelines execute (P1b / P3–P4) — deliberately deferred.
- **The `m,k` correlation defaults are placeholders by design**, not fitted to data; the PI's framing accepts this for a tutorial model.
- **pyMaBoSS packaging.** The `sysbio-curie/pyMaBoSS` path in the cycle-000 brief 404s; the maintained package is `maboss` on PyPI — re-confirm signatures at the Pipeline-4 install boundary `[source: __reports__/p53-mdm2/02-dg_maboss_correlation_v0.md §uncertainty]`.
- **Whether to also correlate a second MD observable** (e.g. residence time onto `$tMNu`) — the PI hinted at "linking MD simulations with the dG results"; the current design uses ΔΔG only. Left as a future extension, connected to Q-003.
