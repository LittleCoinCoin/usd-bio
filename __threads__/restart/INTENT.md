---
topic: restart
created: 2026-06-16
---

# Brief

## Purpose — take stock before the next push

`restart` is a single orientation cycle. The project has just completed a `foundation_demo_v8` prototype three months and could only burst-committed it recently (and rewrote the work history at the same time for the purpose of clarity). It contains
architecture doc, a minimal C++ scaffold, and a pile of design/brainstorming reports). Before I assign the next substantive to build from.

Your job is **assessment + reconciliation**, not feature work. Read widely,
report honestly, tidy what is safe to tidy, and propose how the downstream
backlog should be sliced into topics. When that is done, mark the topic as a
proposed resolution for my review.

## Deliverable 1 — State-of-the-project report

Produce one stakeholder-reviewable report (use the `writing-reports` skill,
saved under `__reports__/restart/`) that answers: *if a fresh agent picked up
this project cold tomorrow, what would it need to know?* Expect to have to cover:

- **What exists and how mature it is** — `__design__/` (esp.
  `openusd_for_research_architecture.md` and the roadmap), `examples/foundation_demo_v8/`
  (converters, demos, guides, generated USD output), `src/` + `tests/` (C++ scaffold),
  build/docs/CI infrastructure.
- **What is solid vs. fragile** — flag the keystone vs. the placeholder; note
  known weak spots (e.g. CMake TBB detection, untested doc build) only where you
  can evidence them.
- **What is stale, scattered, or contradictory** — especially brainstorming
  reports that the permanent architecture doc supersedes. Name them with paths.
- **Gaps and blockers** — what is missing before Phase 2 / C++ schema work can
  begin. Distinguish "blocking" from "nice-to-have".

Lead with structure (tables, a status-at-a-glance), not prose dumps. Tag claims
per the honesty contract — `[source: <path/commit>]` or `[assumption: ...]` —
and close with what you remain uncertain about.

## Deliverable 2 — Reconciliation (safe tidying only)

Leave the repo in a cleaner state, with these guardrails:

- **Archive superseded material** rather than deleting it — e.g. move
  brainstorming reports under `__reports__/foundation_demo/analysis/` that the
  architecture doc has genuinely superseded into an `archive/` subfolder.
  **Verify supersession before moving anything**; if a doc holds unique content
  not captured elsewhere, leave it and flag it instead.
- **Surface, don't silently fix, contradictions.** If two docs disagree (e.g.
  roadmap vs. reality), record it in the report and, where trivial and
  unambiguous, correct the doc. Do not rewrite design decisions.
- **No new feature work, no C++ logic, no schema authoring.** That belongs to
  the downstream topics below.

Commit reconciliation changes in small, conventional commits (`docs(...)`,
`chore(...)`) with WHY-focused messages (see skill `/committing-changes`).

## Deliverable 3 — Proposed topic slicing for the backlog

The downstream work lives in my `USD Bio` macOS reminders. Read it, then propose (in
the report) how to turn it into the next `working-async` topics — recommended
order, dependencies, and a one-line scope + done-criteria each. Do **not** run
`wkas init` for them; just recommend the slicing for me to approve.

The backlog, verbatim:

1. **Async setup: USD Bio (Tier 2, daily)** — define the per-cycle baby step +
   done-criteria, create the daily weekday cycle, test run. *(This `restart`
   cycle is partly that test run; comment on whether the per-cycle rhythm and
   done-criteria worked in practice.)*
2. **Check the remaining gap analysis for the foundational v8** — what is still
   missing/incomplete in `foundation_demo_v8` relative to its own roadmap and
   the architecture doc.
3. **Implement the relevant gaps for the v8** — close the gaps found in (2).
4. **Extract from v8 the infrastructure reusable for the next p53-mdm2
   application case.** p53-mdm2 is meant to demonstrate OpenUSD in a
   *multi-scale* setting, requiring these data pipelines:
   - MD data → OpenUSD (partially reusable from the existing demo)
   - OpenUSD → MD data (link to a server giving ΔG values per variant)
   - OpenUSD → MaBoSS (the complex's ΔG is binarized to active/inactive state
     for the model)
   - MaBoSS → OpenUSD (simulation results returned to USD for integrated
     consultation by the MD team)

For (2)–(4), assess how ready the current codebase is to support each, and call
out anything in the stocktake that changes their feasibility or ordering.

## Scope boundaries

- **In scope:** reading, assessing, reporting, safe archiving/flagging, proposing
  the topic slicing.
- **Out of scope:** implementing v8 gaps, building the p53-mdm2 pipelines,
  writing C++ schema code, scaffolding the downstream topics, or altering the
  architecture/design decisions.

## Done definition

- The state-of-the-project report exists under `__reports__/restart/` and a fresh
  agent could orient from it alone.
- Superseded material is archived (or flagged with a reason it was kept);
  contradictions are surfaced.
- A concrete, ordered topic-slicing proposal for the backlog is in the report.
- Open questions for me are raised via `wkas ask`; the cycle finishes with
  outcome `proposed-resolution` for my review.
