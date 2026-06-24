# Cycle 000 WORKLOG — v8-gap-closure

## Situation (from manifest)

First cycle of the topic. STATUS `active`, per-cycle cadence, stall_threshold 3.
INTENT is a large multi-cycle brief: bring `examples/foundation_demo_v8/` to
architecture-doc parity by closing the in-scope backlog of
`__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md`
(§3 gaps + §5 experiments). The brief directs: start from the existing gap report
(validate/refresh, don't re-derive), drive with a roadmap (`/managing-roadmaps`),
build a falsification-resistant test harness early, work as a team, verify every
leaf. QUESTIONS empty; INBOX held one placeholder entry (`# Inbox`).

Runtime woke on `main`; checked out `topic/v8-gap-closure` manually so `begin-cycle`
would accept HEAD (known friction, per memory note `wkas-runtime-wakes-on-main`).
An orphan cycle-000 dir (created by the inbox-ack) was taken over with
`begin-cycle --resume` rather than discarded, preserving the INBOX-consumed trail.

## Plan (decide step)

This is a SCOPING cycle, not implementation. Owed: (1) refresh the gap audit against
current code; (2) author a dependency-ordered, BFS-executable roadmap; (3) a
stakeholder-reviewable findings report. No experiment implemented this cycle —
implementation is future-cycle work the roadmap drives.

## Work done

- **INBOX-ack** (commit `ddf6707`): consumed the lone placeholder entry (`# Inbox`,
  scaffolding noise). No action item.
- **Audit refresh** (Sonnet sub-agent, observation-only): re-validated every §3 gap
  and §5 experiment against current code. Result: nothing material closed since
  2026-02-15. All §3.3 arcs and §5 experiments still-open (deferred-by-design);
  departmental layering still 2-layer (partial). Two genuine defects CONFIRMED:
  hard-coded ShinobuLab paths in 3 files (`xtc_to_clips.py:60-68`,
  `04_create_assembly.py:45-48`, `pdb_parser.py:313-317`) + 1 ROADMAP literal;
  shallow data-gated tests (only `test_element_data.py` data dicts + `smoke_test.cpp`
  version string; ad-hoc `verify_*` blocks aren't standalone tests). v8 `ROADMAP/`
  parent README statuses stale (M1/M2/M3 all complete but marked In Progress/Blocked).
  New since report: water_template/water_demo, ion_properties, 13 docs — none close a
  §3/§5 gap.
- **Roadmap** (commit `0b6ce39`): authored `__roadmap__/v8-gap-closure/` via
  `dirtree-rdm`. 14 leaves across 3 depth waves (depth encodes BFS order; leaves run
  before subdirs within a directory):
    - Foundation (root leaves): `portability_fix`, `test_harness`,
      `roadmap_status_correction`.
    - `gap_closure/` (after foundation): Exp 2 binary_clip_templates, Exp 1
      pointinstancer_solvent, Exp 3 departmental_layering, Exp 5 basiscurves_bonds,
      Exp 6 references_vs_sublayers (independent, parallel).
    - `gap_closure/composition_advanced/` (deepest): Exp 4 ensemble_payload (needs
      Exp 2 + Exp 3), perturbation_variantset, parameter_variantset, specializes_arc,
      analysis_attributes (needs Exp 3 Analysis layer), provenance_metadata.
  Leaf bodies authored by 3 parallel Sonnet sub-agents; all 17 files BNF-validate;
  orchestrator committed the integration (avoids concurrent-index races). Each leaf's
  final step is read-back tests; pxr API signatures deferred to context7 at execution
  time rather than guessed.
  Intentional deviation from §5 pure priority order: `test_harness` is sequenced as
  foundation (not a §5 item) because INTENT makes it the regression net every later
  closure depends on. Documented in campaign README + report Contradictions section.
- **Findings report** (commit `75f8f24`): `__reports__/v8-gap-closure/00-audit_and_roadmap_v0.md`
  + topic README. decision-required: confirm. Refreshed gap table, roadmap shape,
  Mermaid dependency graph, 3 steering questions.

## Verifier verdict (cycle-000, verbatim)

```
verdict: aligned
inbox-coverage:
  - INBOX.md (no items present): confirmed empty at __threads__/v8-gap-closure/INBOX.md — no items to cover; cycle-000 INBOX-consumed.md shows no consumed items, consistent with an empty inbox at cycle start; no coverage gap
intent-tracking: aligned
work-depth: The cycle's stated commitment was a scoping cycle — refresh the gap audit and author a dependency-ordered roadmap; no implementation was owed. That commitment is fully met. The findings report (__reports__/v8-gap-closure/00-audit_and_roadmap_v0.md) provides a row-by-row refreshed gap table against current code (with explicit source citations: colgrep hits, file:line references, filesystem finds), a 14-leaf roadmap encoded as BFS directory depth, a Mermaid graph with data-dependency edges, contradiction documentation (test_harness promoted to foundation wave over §5's priority order), and three steering questions for PI confirmation. The roadmap (__roadmap__/v8-gap-closure/) is fully populated: a campaign README with pre-conditions, success gates, and node table; 14 leaf task files each with goal, pre-conditions, success gates, implementation logic, deliverables, consistency checks, and commit message — exactly what INTENT.md asked for when it said "the roadmap — not this brief — defines the per-leaf deliverables and success gates." No corners are visible that the scoping commitment demanded be filled.
recommended-action: proceed
```

Orchestrator adjudication: verdict accepted (aligned). Outcome `open` — the topic is
scoped, not resolved; execution begins next cycle at the foundation wave.

## What I am uncertain about

- The report's links to `__design__/openusd_for_research_architecture.md` use section
  numbers (e.g. §2.2, §6) that sub-agents tagged as assumptions; the architecture doc
  was not re-read this cycle to confirm exact section numbering. Low risk — the leaf
  specs instruct the execution agent to verify against the doc and context7 before
  authoring assertions.
- Several leaf specs defer pxr API signatures (UsdValidation.ValidationRegistry,
  UsdGeomPointInstancer, clipTemplateAssetPath, MuteLayer, Specializes vs Inherits
  strength) to context7 at execution time. This is intentional (avoids guessing) but
  means the specs are not yet API-precise — by design for a planning cycle.
- `abl_kinase_complex.usda` atom/bond counts (4,676 / 2,428) and the clip's internal
  structure were asserted by the old report, not re-counted this cycle. The
  test_harness leaf's read-back tests are designed to verify these at execution time.
