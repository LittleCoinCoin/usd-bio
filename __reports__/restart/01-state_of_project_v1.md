# usd-bio — State of the Project (v1)

Date: 2026-06-19

---
type: findings
topic: restart
date: 2026-06-19
version: v1
prior-version: 00-state_of_project_v0.md
key-metric: phase-readiness: prototyping-complete, backlog locked (prior: Phase-2-blocked, delta: decisions resolved)
decision-required: confirm-and-close
---

> **Purpose.** This v1 supersedes [v0](00-state_of_project_v0.md) by folding in
> the PI's review decisions (cycle-000 → cycle-001). v0 produced the orientation
> snapshot and a *proposed* 4-topic slicing; the PI has since answered every open
> question (Q-001/002/003) and the INBOX directive. This v1 records the **locked
> decisions**, the **reconciliation actually applied** this cycle, and the
> **final approved backlog**. A fresh agent should read this as the current
> orientation; v0 remains for the underlying evidence (status tables, maturity
> map) which is unchanged. Claims are tagged `[source: <path/commit>]` or
> `[assumption: …]`.

## Headline Result

metric: phase-readiness
value: Orientation complete; backlog locked to 2 active topics (gap-analysis+impl merged, then p53-mdm2); C++ deferred indefinitely; restart ready to close
unit: qualitative
prior: Python prototyping validated; C++ Phase-2 blocked; slicing proposed (v0)
direction: resolved

**One-paragraph orientation.** usd-bio remains in its **manual Python
prototyping phase**, with `examples/foundation_demo_v8/` as the load-bearing
keystone (full inventory and maturity assessment in [v0](00-state_of_project_v0.md))
`[source: 00-state_of_project_v0.md]`. What changed this cycle is *direction, not
code*: the PI has locked the backlog. C++ Phase-2 / build / CI / vcpkg concerns —
the single biggest blocker in v0 — are **deliberately deferred**: "Everything is
being prototyped on the Python version… dismissing any work on C++ for now"
`[source: __threads__/restart/INBOX.md]`. The project's path forward is to **build
Python examples and learn from them; the C++ schema is expected to *arise* from
that work rather than be scheduled up front** `[source: QUESTIONS.md Q-001 answer]`.
With C++ deferred, the v0 "biggest blocker" no longer blocks anything on the
active path.

## PI Decisions Folded In This Cycle

| Channel | PI decision | Action taken this cycle |
|---|---|---|
| INBOX (2026-06-17) | Resolve all 6 surfaced contradictions; C++ resolved by *dismissing* C++ work; v8 is the only version, ignore pre-v8 history | Acknowledged (commit `d829b7e`); doc-only contradictions fixed, C++ ones closed-by-deferral (see Resolutions table) |
| Q-001 | **Merge T1+T2** (gap-analysis → implementation is one logical path); T3 (p53-mdm2) is the next research question; **drop T4** | Backlog re-sliced to 2 topics (see Final Slicing) |
| Q-002 | **Drop T4** (cpp-build-revival) for the near-to-intermediate future | T4 removed from backlog |
| Q-003 | Keep analysis docs only if they serve future LLM-agents; the real need is *cheap OpenUSD doc access* (docs existed to avoid context7 round-trips when LLMs struggled with USD) | Verified context7 now covers OpenUSD richly → recommend relying on it; analysis docs no longer need to be kept solely as a doc cache (see Doc-access) |

## Final Approved Topic Slicing (Deliverable 3 — locked)

Supersedes the v0 proposed T1–T4 table. Per Q-001/Q-002. **Still PI's job to
`wkas init`; this cycle does not scaffold them.**

| # | Topic slug (proposed) | Scope (one line) | Done-criteria | Depends on | Status |
|---|---|---|---|---|---|
| A | `v8-gap-closure` (merge of old T1+T2) | Audit `foundation_demo_v8` against its own `ROADMAP/` + the architecture doc, then close the agreed gaps in the Python prototype — the audit produces a roadmap-described implementation path that the same topic executes. | A gap report under `__reports__/v8-gap-closure/`; each agreed gap closed with a runnable demo + committed `.usda`; v8 `ROADMAP/` statuses corrected. | none — **ready now** | proposed |
| B | `p53-mdm2-infra-extraction` (old T3) | Next research question: extract/generalize v8 infra for the multi-scale p53-mdm2 case; build/stub the 4 pipelines (MD→USD reuse; USD→MD ΔG server; USD→MaBoSS; MaBoSS→USD). | A reuse map + the MD→USD pipeline generalized off ABL specifics; designs/stubs for the 3 greenfield pipelines. | A (real dependency, but **PI decides when to move on** — B does not need A's internal detail) | proposed |
| ~~T4~~ | ~~`cpp-build-revival`~~ | **DROPPED** per Q-002. C++ build/CI/vcpkg/TBB revival is deferred indefinitely; revisit only if/when the schema phase is explicitly triggered. | — | — | dropped |

**Ordering rationale (PI's words).** "We merge T1 and T2 because the audit of the
gap analysis will be logically followed by a roadmap-described implementation
path. T3 is the next research question… the dependency is real. T3 does not need
to know about the details of T1+T2; simply I, the PI, will decide when to move
on." `[source: QUESTIONS.md Q-001 answer]`. Effort hints from the reminders:
gap-analysis ~90m + implementation ~180m, p53-mdm2 ~120m `[source: 00-state_of_project_v0.md "macOS Reminders tags"]`.

## Contradiction Resolutions (Deliverable 2 — follow-through)

v0 surfaced 6 contradictions rather than silently fixing them. With PI approval
("we can move forward with resolving all of them"), this cycle applied the
trivially-fixable doc-only corrections and closed the C++ ones by deferral.

| # | Contradiction (from v0) | Resolution this cycle | Evidence |
|---|---|---|---|
| 1 | `README.md` claims "Phase 2+ in development" — overstates maturity | **Fixed**: status line now reads "Manual prototyping phase… validated in Python before the C++ schema is committed" | commit `1f0e49e` |
| 2 | `README.md` two different "Phase 1 complete" meanings (C++ infra vs Python demo env) | **Fixed**: milestone list re-headed as one-time *C++ scaffolding*, distinct from active Python prototyping | commit `1f0e49e` |
| 3 | `__reports__/foundation_demo/README.md` evolutionary log frozen at "Version 5 (Current)" while repo is at v8; v0–v7 deleted | **Fixed**: collapsed to a "Current Version" section stating v8 is the current and only version; no fabricated v6–v8 changelog (per "ignore history") | commit `3af6829` |
| 4 | Local C++ build only succeeded via undocumented TBB override | **Closed by deferral** — C++ work dropped (Q-002); not touched | INBOX directive |
| 5 | CI workflows dead (require removed vcpkg) | **Closed by deferral** — C++/CI work dropped; not touched | INBOX directive |
| 6 | `out/build/Clang/` stale failed vcpkg configure misleading to a cold agent | **No repo change** — gitignored, local-only; not part of committed state | `[source: .gitignore; out/build is untracked]` |

**Not touched, deliberately:** v8 `ROADMAP/` status corrections (belong to topic A,
`v8-gap-closure`); `__design__/usd_bio_roadmap_v0.1.0.md` (stale but a design
artifact — left as historical record); all CMake/CI/vcpkg files (C++ deferred).

## Doc-access for future agents (resolves Q-003 intent)

The PI reframed Q-003: the question is not "archive aggressiveness" but whether
the analysis docs earn their keep as a **cheap OpenUSD documentation cache** for
the LLM-agents running the work cycles — they originally existed because
4-months-ago LLMs struggled with OpenUSD concepts and context7 round-trips were
expensive `[source: QUESTIONS.md Q-003 answer]`.

**Finding: that need is now met by the live `context7` MCP server.** A
`resolve-library-id` query for OpenUSD returns multiple high-reputation sources
with deep coverage `[source: context7 resolve-library-id "OpenUSD", this cycle]`:

| context7 library ID | Snippets | Reputation |
|---|---|---|
| `/websites/openusd_release` | 86,994 | High |
| `/websites/openusd` | 29,206 | High |
| `/websites/openusd_release_api` | 37,083 | High |
| `/nvidia-omniverse/openusd-code-samples` | 143 (Py/C++/USDA) | Low |

**Recommendation.** Future cycle agents should treat `context7` as the primary
on-demand OpenUSD reference (resolve `/websites/openusd_release`, then
`query-docs`), rather than re-deriving USD concepts from scratch or depending on
the in-repo analysis docs. Consequently the kept analysis docs (04, 06–10) no
longer need to be retained *solely* as a doc cache; they can be re-evaluated for
unique design content on their own merits during topic A. This cycle does **not**
archive any further docs — that re-evaluation rides along with `v8-gap-closure`
where the docs are actually consulted. `[assumption: context7 remains available
to the cycle runtime; it was present this session but interactively-authenticated
MCP servers can be absent in headless runs — worth confirming in the first
`v8-gap-closure` cycle.]`

## On the async rhythm (reminder item 1 — the test run)

`restart` was partly the Tier-2 daily-cycle test run. Two cycles in, the per-cycle
rhythm holds up: `wkas` enforced ordering cleanly, the manifest read-order
oriented each cycle fast, and the proposed-resolution → PI-review → fold-in loop
worked exactly as designed (cycle-000 proposed; PI answered via QUESTIONS/INBOX;
cycle-001 folded the answers in). **One recurring friction, now confirmed across
both cycles:** the runtime woke on `main`, not `topic/restart`; `begin-cycle`
refuses unless HEAD is on the topic branch, so the agent had to `git checkout
topic/restart` manually first. This is a runtime/worktree-setup gap, not a `wkas`
bug — worth fixing in the daily-cycle harness so agents don't have to work around
it. Done-criteria for the daily cycle ("one orientation/assessment deliverable +
verifier + finish-cycle within bounds") proved achievable inside the tool/time
budget.

## Steering Questions

No open questions. Q-001/Q-002/Q-003 are all answered and folded in; the INBOX
directive is consumed. The only decision left is the PI's confirm-and-close.

## Pointers

- v0 evidence base (unchanged): [00-state_of_project_v0.md](00-state_of_project_v0.md)
- Reconciliation commits this cycle: `1f0e49e` (README phase status), `3af6829` (foundation-demo log → v8-only)
- INBOX consumption: commit `d829b7e`; archived to `__threads__/restart/cycles/cycle-001/INBOX-consumed.md`
- Keystone code: `examples/foundation_demo_v8/`
- Keystone architecture: `__design__/openusd_for_research_architecture.md`
- OpenUSD doc access for future agents: context7 → `/websites/openusd_release`

## What I Am Uncertain About

- **context7 availability in headless cycle runs.** Confirmed present this
  session; interactively-authenticated MCP servers can be missing in cron/headless
  runs — the doc-access recommendation should be re-confirmed in the first
  `v8-gap-closure` cycle `[assumption]`.
- **Whether the Python demos run today** — unchanged from v0; assessed from code
  structure + committed `.usda`, not a live run (needs the custom `pxr` env +
  ShinobuLab dataset) `[source: 00-state_of_project_v0.md uncertainties]`.
- **Unique content in kept analysis docs 04/06–10** — deferred to topic A rather
  than re-litigated here; they are kept, not archived, this cycle.
- **p53-mdm2 feasibility detail** — no p53/MaBoSS code or design exists in-repo;
  the reuse map is intent-level only, to be grounded in topic B `[source: 00-state_of_project_v0.md]`.
