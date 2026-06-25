# v8-gap-closure — Knowledge Transfer (cycle-002, v0)

Date: 2026-06-25

## Executive Summary

- **What shipped / changed:** Cycle-002 executed the **entire remaining roadmap** — the 4 remaining
  gap_closure experiments and all 6 composition_advanced arcs — to completion, under the corrected
  `forOUSD` interpreter. Combined with cycle-001 (foundation wave + Amendment A01 + Exp 1), the full
  **15-leaf roadmap is now ✅ done**, achieving architecture-doc parity for the in-scope §3 gaps + §5
  experiments.
- **Primary outcomes:** Every §5 experiment (Exp 1–6) and every §3.3 arc (References, Payloads,
  Ensemble/Perturbation/Parameter VariantSets, Specializes, departmental layering, analysis-as-
  attributes) plus §3.4 provenance is demonstrated with a runnable demo + committed `.usda` (or
  `.usdc`) + falsification-resistant read-back tests. Foundation harness **30/30 PASS**; 11 standalone
  read-back suites green. Verifier verdict: **aligned → proceed**. Topic finishes `proposed-resolution`.

## What landed this cycle

| Leaf | Arc / experiment | Headline evidence |
|---|---|---|
| `binary_clip_templates` | Exp 2 — binary + clip templates | `.usdc` assembly 95.8% smaller, clip 63% smaller; load 2.6–6.1× faster; clip template resolves live from 2 XTC |
| `departmental_layering` | Exp 3 — 5-layer departmental | biology/protocol/dynamics/analysis/review SubLayers; each independently mute-toggleable; time-sampled `bio:rmsd` |
| `basiscurves_bonds` | Exp 5 — BasisCurves bonds | 2,428 bonds → one curves prim; assembly 38% smaller, trajectory clip **85%** smaller |
| `references_vs_sublayers` | Exp 6 — References vs SubLayers | `AddReference` assembly; encapsulation difference proven; biological parity held |
| `ensemble_payload` | §3.3 Ensemble | `ReplicaID` VariantSet swaps Payloads; sentinels (1/2/3) resolve per replica |
| `perturbation_variantset` | §3.3 Perturbation | `Genotype` (WildType/T315I) swaps Referenced residue geometry; THR↔ILE resolves |
| `parameter_variantset` | §3.3 Parameter | `ForceField` (Amber99/Charmm36) swaps `bio:partialCharge` (−0.0518 vs −0.02) |
| `specializes_arc` | §3.3 Specializes | true Inherits-vs-Specializes contrast across a reference boundary |
| `analysis_attributes` | §3.3 analysis-as-attributes | time-sampled `bio:rmsd`/`bio:pmf`/`bio:contactCount` |
| `provenance_metadata` | §3.4 provenance | structured 6-field lineage replaces flat `bio:source`; `04_create_assembly.py` refactored |

## Wins

- **Rigor net kept paying off.** Verifier-driven hardening of `test_binary_clips.py` exposed a
  **cosmetic clip template** (`clip_###.usdc` is silently rejected by USD's resolver; it requires
  `basename.###.ext`). The original Exp 2 "PASS" was a false pass; now the clips genuinely resolve
  (`ResolveInfoSource=ValueClips`). A read-back test that only checks a metadata string is not enough.
- **Sub-agents surfaced real USD truths instead of forcing the spec.** `parameter_variantset`
  discovered SubLayer-in-variant doesn't compose (pivoted to Reference-in-variant). `specializes_arc`
  empirically falsified the architecture doc's claim. Both documented honestly, no test weakening.
- **The interpreter correction unblocked everything.** Once `forOUSD` (pxr + mdtraj) was identified,
  every trajectory-dependent experiment (Exp 2, Exp 5) ran without issue — the cycle-001 "split" was a
  non-issue.

## Pain Points

- **Sub-agents pause after the first per-step commit.** Every fresh-leaf dispatch did step 1 then
  yielded, requiring a continuation dispatch. Mitigated by strong "do all steps" prompts (continuations
  usually completed the rest), but it doubled round-trips.
- **Leaf specs carried a few inaccuracies** (specializes prediction backwards; analysis rmsd hint vs
  formula; clip `###` path format). The falsification-resistant tests caught each — exactly their job.

## Root Causes

- The architecture doc (R03) was written ahead of empirical USD validation, so a few composition-arc
  claims (notably Specializes strength) didn't match real resolver behavior. The experiments are the
  first time these were executed and checked.

## Next-Cycle Changes

- **Architecture-doc correction (flagged, not done — out of scope):** R03 §2.1 row S / §7 should be
  corrected — with Specializes the **base/source is always weaker** than instance opinions (even across
  references); it is **Inherits** (stronger than References) that lets a root base-class opinion override
  a referenced instance's local opinion. This is a doc decision for the PI.
- **Provenance sentinel values** (`2HYY.pdb`, `AMBER99SB-ILDN`, `GENESIS 2.1.0`, timestamp) are
  representative assumptions — replace with real ShinobuLab run metadata when available.

## Artifacts to Preserve

- New demos/assets under `examples/foundation_demo_v8/{demos,templates,converters,assets,output}/` and
  the standalone read-back tests in `examples/foundation_demo_v8/tests/`.
- New composition-arc tree: `examples/composition_advanced/{ensemble_payload,perturbation_variantset,parameter_variantset,specializes_arc,analysis_attributes,provenance_metadata}/` + `tests/composition_advanced/`.
- Reusable helper `provenance_schema.apply_provenance_metadata`; `tools/patch_stage_metadata.py`.
- Roadmap (all nodes ✅): `__roadmap__/v8-gap-closure/` with per-leaf Progress notes recording every deviation/finding.

## Open Questions

- **Architecture-doc Specializes correction** (above) — PI decision on whether/when to amend R03.
- **Q-001 (mdtraj/pxr split)** is **retracted/moot** — resolved by using the `forOUSD` venv.

## Disposition

The in-scope backlog of `01_v8_to_production_perspective.md` (§3 gaps + §5 experiments) is closed with
runnable evidence + tests; v8 ROADMAP statuses are truthful; defects fixed. Per the Done definition in
INTENT, the topic finishes **proposed-resolution** for PI confirm-and-close. C++/schema authoring and
the p53-mdm2 application remain explicitly out of scope (future topics).
