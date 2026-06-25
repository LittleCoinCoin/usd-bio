# Cycle 002 WORKLOG — v8-gap-closure

## Situation

Resumed after a PI correction. The PI clarified that a wkas cycle is the boundary between agent and PI
work, NOT a checkpoint to seek review at — with a clear green roadmap I should continue and only close
on a critical issue or a PI-approval-needing inconsistency. The PI also (a) corrected my cycle-001
"mdtraj/pxr interpreter split" conclusion: the canonical `forOUSD` venv
(`/Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3`) has BOTH pxr 0.25.11 and mdtraj 1.11.1 — there
is no split (Q-001 retracted); and (b) directed: drive the whole roadmap, gap_closure first then reassess.

Recovery: synced topic↔main (merged topic into main, `wkas ack` on main → pi-reviewed, FF main into
topic), then `wkas wake`/`begin-cycle` opened cycle-002.

## Plan

Execute the roadmap BFS via implementor + verifier sub-agents (Sonnet workers, Opus orchestrator as
rigor tie-breaker), under the `forOUSD` interpreter. gap_closure (4 leaves) → reassess with PI →
composition_advanced (6 arcs). Manage status via `dirtree-rdm`; commit per step; orchestrator re-runs
every success gate independently; dispatch the verifier before finish.

## Work done

**gap_closure wave (Exp 2/3/5/6):**
- `binary_clip_templates` (0b0ea9c,1ca31d2,ab90b65,77360f7,b0b0a6e): .usdc conversion (assembly 95.8%
  smaller, clip 63%), load 2.6–6.1× faster, clip-template manifest from 2 XTC. Verifier-driven hardening
  of the read-back caught a **cosmetic clip template** — `clip_###.usdc` is silently rejected by USD
  (needs `basename.###.ext`); fixed to `clip.###.usdc`, now resolves `ResolveInfoSource=ValueClips`.
- `departmental_layering` (9cdcfe9,8f7af8c,172fea0,c774c7b): 5 SubLayers, each independently mute-
  toggleable; time-sampled bio:rmsd. (API note: USD 0.25.11 uses stage.GetCompositionErrors().)
- `basiscurves_bonds` (e054e18,d11b867,5a09445,a2a8011): 2,428 bonds → one BasisCurves prim; assembly
  38% smaller, trajectory clip 85% smaller.
- `references_vs_sublayers` (e2ff37e,9bc1bbc,a71e480,972c4d4): AddReference assembly; encapsulation
  difference proven, atom/radius parity held.

**composition_advanced wave (all 6 arcs):**
- `ensemble_payload` (1e22238,bc21e85,082cf2c): ReplicaID VariantSet swaps Payloads; sentinels 1/2/3
  resolve per replica. DEVIATION: self-contained base (avoids /ABLComplex root ambiguity).
- `perturbation_variantset` (5f5dc22,636f023,2fbfcf4): Genotype WildType/T315I swaps Referenced residue
  geometry; THR↔ILE resolves.
- `parameter_variantset` (30712a0,8e4dc8b,0dca328): ForceField Amber99/Charmm36 swaps bio:partialCharge.
  FINDING: SubLayer-in-variant does NOT compose (layer-stack-level); pivoted to Reference-in-variant.
- `specializes_arc` (cd7b1ea,a117222,f0832f7,776fab8): demonstrates true Inherits-vs-Specializes contrast
  across a reference boundary. MAJOR FINDING: architecture doc §2.1/§7 "Specializes source overrides
  instance" is BACKWARDS — with Specializes the base is always WEAKER than instance opinions. Doc not
  altered (out of scope); flagged for PI.
- `analysis_attributes` (348c7f4,fe22e07,6e2e9e6): time-sampled bio:rmsd/pmf/contactCount.
- `provenance_metadata` (6125f0d,c6d02bc,a907436,71e6d68): structured 6-field lineage replaces flat
  bio:source; 04_create_assembly.py refactored.

All leaves verified by the orchestrator re-running each success gate; harness 30/30 throughout; 11
standalone read-back suites green. Roadmap nodes all ✅ (directories closed bottom-up).

## Verifier verdict (cycle-002, final, verbatim)

```
verdict: aligned
inbox-coverage:
  - INBOX.md is empty (zero items this cycle, as stated in the dispatch directive) → no artifact required; coverage is vacuously satisfied
intent-tracking: aligned
work-depth: All ten leaf tasks claimed as done in cycle-002 are substantiated by committed artifacts and passing tests that were run live during this verification. The main test harness (examples/foundation_demo_v8/tests/run_tests.py) returns 30/30 as claimed. All six tests/composition_advanced/ test suites were executed and pass at their claimed counts: ensemble_payload 6/6, specializes_arc 5/5, parameter_variantset 9/9, analysis_attributes 4/4, provenance_metadata 4/4, perturbation_variantset 9/9. Tests are genuinely falsification-resistant: each opens Usd.Stage.Open fresh with no generator state in scope, switches variant selections on a live stage to prove composition operates at the USD layer (not just at authoring time), and asserts independently stated sentinel values (e.g., ensemble payload points (1,0,0)/(2,0,0)/(3,0,0) per replica; parameter partial charges -0.0518/-0.02 from committed param overlay files; perturbation residue names THR/ILE from committed geometry stubs). The specializes_arc leaf honestly documents a MAJOR FINDING - the architecture doc §2.1/§7 claim "Specializes source overrides instance" is empirically backwards - in __roadmap__/v8-gap-closure/gap_closure/composition_advanced/README.md line 56, the test file docstring, and the build script; the doc is not altered (correctly flagged as out-of-scope for PI decision). All other deviations (ensemble self-contained base, parameter SubLayer→Reference-in-variant pivot, analysis rmsd hint inconsistency, provenance sentinel values as representative assumptions) are explicitly recorded in the roadmap Progress notes and/or test source comments. The gap between the specializes leaf spec (Step 3, gate 3b: "Specializes prim shows base-class value winning") and the delivered test (which correctly asserts the empirically observed reverse) is itself evidence of honest science: the spec was wrong, the implementation detected the error, and the deviation is fully documented rather than papered over. Architecture-doc parity is a fair claim for the in-scope §3/§5 backlog: every §5 experiment (Exp 1-6) and every §3.3 arc (References, Payloads, Ensemble/Perturbation/Parameter VariantSets, Specializes, departmental layering, analysis-as-attributes) plus §3.4 provenance has a committed artifact and read-back tests. One residual open item exists that the cycle itself flags and defers appropriately: the architecture doc's Specializes claim needs correction, but that is a doc edit that is out of this topic's scope and is surfaced, not hidden.
recommended-action: proceed
```

Orchestrator adjudication: verdict accepted (aligned). Tiebreaker calls made this cycle: (1) required
the clip-template read-back to prove live resolution → caught the cosmetic-template defect; (2) rejected
the specializes flat-file "no contrast" result and required the cross-reference construction → surfaced
the architecture-doc error with a genuine, tested demonstration. Outcome `proposed-resolution` — the
in-scope backlog is fully closed.

## What I am uncertain about

- Architecture doc R03 §2.1/§7 Specializes claim is empirically wrong (documented, doc not edited — PI
  decision).
- Provenance values are representative sentinels, not real ShinobuLab run metadata.
- `ensemble_payload` time-sample mapping showed a t=2.4 vs t=1.0 offset (hold-interpolation still
  returns correct sentinels; not fully root-caused) — does not affect the payload-swap proof.
