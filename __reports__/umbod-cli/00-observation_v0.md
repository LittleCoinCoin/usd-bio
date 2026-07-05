# umbod-cli — Observation (v0): uncommitted FSM flip clobbered → non-atomic finish-cycle traps the cycle

Date: 2026-07-06

---
type: observation
topic: umbod-cli
spotted-during: v8-gap-closure cycle-004 finish-cycle (daily async run)
date: 2026-07-06
domain: code
confidence: confirmed
urgency: medium
deferred-because: hit during an autonomous async cycle; recovered manually, but the two underlying umbod defects need engineer review rather than an in-cycle patch (the CLI is a separate cargo repo).
---

## What Was Noticed

`umbod finish-cycle` failed in a way that then **blocked its own retry**, on a topic that looked correctly begun. Two chained failures:

1. First `finish-cycle` aborted with `E_INTERNAL: refusing to complete topic from state pi-reviewed (a cycle must be finished from active): invalid transition: CycleCompleted not allowed from state pi-reviewed` — even though `umbod begin-cycle` had been run and reported success.
2. Retrying (after fixing the state via `begin-cycle --resume`) then failed with `E_REFUSED: working tree has untraced files` — listing `cycles/cycle-004/{HANDOFF,WORKLOG,ARTIFACTS}.md`, i.e. **finish-cycle's own output from the aborted first attempt**, left untracked.

Root cause is a chain of two independent defects:

- **Defect 1 (fragile handoff of FSM state):** `begin-cycle` performs the `pi-reviewed → active` consume by writing STATUS.md to the **working tree, uncommitted, by design** (begin_cycle.rs:277–296, comment at 282–284). Any process that cleans the tree in that window silently reverts the transition with zero warning. In this run a dispatched sub-agent ran `git checkout -- STATUS.md` (standard "leave a clean tree" hygiene) and reverted `active` back to the committed `pi-reviewed`.
- **Defect 2 (non-atomic finish-cycle):** `finish-cycle` writes the immutable cycle files (`write_cycle_files`, finish_cycle.rs:273) **before** it validates the FSM transition (`apply_cadence_and_outcome` → `can_transition`, finish_cycle.rs:284, 696–702). When the transition throws, the cycle files are already on disk and orphaned; the L3 gate (line 253) then refuses every retry on that debris, and the re-run-safety guard (lines 239–241) only covers the *post-tag* merge-conflict path, not this pre-commit failure.

## Context

Running the `usd-bio-daily-async-cycles` scheduled task. The topic `v8-gap-closure` was `pi-reviewed` (PI had `umbod ack`'d cycle-003). Cycle-004 followed the team-leader pattern: `begin-cycle`, then immediately dispatch a diagnosis sub-agent, then implementor sub-agents, then finish-cycle. The active-state flip from `begin-cycle` was **not committed before dispatching the first sub-agent** — which is where the collision happened. Prior cycles (cycle-002 `f517ecb`, cycle-003 `8749077`) committed a "wake-time STATUS projection before finish" early, which happens to have protected the flip in those runs; cycle-004 dispatched a tree-cleaning sub-agent first and lost it.

Deferred because: the fix belongs in the umbod cargo project (a separate repo under the skill dir), and the immediate cycle was recovered manually. This report is the engineer-facing handoff.

## Location Map

umbod CLI source (cargo repo, version `umbod 0.5.1 (7d8a741 2026-07-03T16:42:04Z)`):
- `/Users/hacker/.claude/skills/umbod/scripts/umbod/src/commands/llm/begin_cycle.rs:277-296` — the `pi-reviewed → active` consume; writes STATUS uncommitted (comment 282-284)
- `/Users/hacker/.claude/skills/umbod/scripts/umbod/src/commands/llm/finish_cycle.rs:253` — L3 gate `assert_clean_working_tree` (runs first)
- `.../finish_cycle.rs:273` — `write_cycle_files` (side effect BEFORE transition validation)
- `.../finish_cycle.rs:284, 675-711` — `apply_cadence_and_outcome` → `can_transition`; throws on non-`active` state
- `.../finish_cycle.rs:217-241, 384-396` — re-run-safety predicate (covers only close-commit+tag+merge-conflict; NOT the write-then-transition-fail path)
- `.../src/state.rs` — FSM edge table (`can_transition`, `Trigger::CycleStarted`, `Trigger::CycleCompleted`)

Reproduction context in this repo (usd-bio):
- STATUS state trail: `git log --oneline -- __threads__/v8-gap-closure/STATUS.md`
- The recovery commit: `952e253` ("record active-state projection before cycle-004 finish")
- PI-ack that set pi-reviewed on main: `4e2f116`

## Evidence

STATUS.md committed-state trail (each commit's `state:` value):

| commit | state: | subject |
|--------|--------|---------|
| `4e2f116` | pi-reviewed | pi-ack(v8-gap-closure): acknowledge review — fast-forwarded onto topic by begin-cycle |
| `952e253` | active | chore: record active-state projection before cycle-004 finish (the RECOVERY commit) |
| `e3d2bce` | needs-pi-review | chore: close cycle-004 (finish-cycle succeeded) |

The begin-cycle consume writes uncommitted (begin_cycle.rs:282-284, verbatim):
> Done AFTER the snapshot write so the snapshot baseline records the `pi-reviewed` STATUS; the working-tree flip to `active` is left uncommitted and rides the cycle's own commits.

The sub-agent that reverted it (diagnosis sub-agent final report, verbatim):
> a stray `__threads__/v8-gap-closure/STATUS.md` change appeared mid-session from an untraced side-effect and was reverted via `git checkout --`; working tree confirmed clean at the end.

First finish-cycle failure (state=pi-reviewed):
```
error[E_INTERNAL]: finish-cycle: refusing to complete topic from state `pi-reviewed`
  (a cycle must be finished from `active`): invalid transition:
  CycleCompleted not allowed from state pi-reviewed
```

Second finish-cycle failure (retry, after `begin-cycle --resume` flipped to active) — blocked on finish-cycle's own orphaned output:
```
error[E_REFUSED]: working tree has untraced files; commit them before finish-cycle:
    __threads__/v8-gap-closure/cycles/cycle-004/ARTIFACTS.md
    __threads__/v8-gap-closure/cycles/cycle-004/HANDOFF.md
    __threads__/v8-gap-closure/cycles/cycle-004/WORKLOG.md
    __threads__/v8-gap-closure/STATUS.md
  Only gitignored paths are exempt.
```
Those three cycle files carried complete content (HANDOFF.md had full frontmatter + next_decision), confirming `write_cycle_files` had run to completion before the transition check aborted the first attempt — i.e. the write is not rolled back on the error path.

## Re-observation Steps

Minimal synthetic repro (no sub-agent needed — the `git checkout` stands in for any tree-cleaning step):
1. Take a topic to `pi-reviewed` (`umbod ack <slug>` from the PI branch).
2. `umbod begin-cycle <slug>` — observe STATUS.md working-tree state flips to `active` but is uncommitted (`git diff __threads__/<slug>/STATUS.md`).
3. `git checkout -- __threads__/<slug>/STATUS.md` (simulates a sub-agent cleaning its tree). State is now committed `pi-reviewed` again, silently.
4. Do trivial committed cycle work, then `umbod finish-cycle <slug> --outcome open ...` → **Defect 2a**: `E_INTERNAL` invalid transition, AND `cycles/cycle-NNN/{HANDOFF,WORKLOG,ARTIFACTS}.md` are now on disk untracked.
5. `umbod finish-cycle ...` again → **Defect 2b**: `E_REFUSED` on finish-cycle's own orphaned files.

Manual recovery that worked: `umbod begin-cycle <slug> --resume` (re-runs the consume → active); `rm` the 3 orphaned cycle files; `git add`+commit STATUS.md (active projection); re-run `umbod finish-cycle`.

## Hand-off Questions

Working theory: two independent defects compound. (1) begin-cycle should not leave the authoritative FSM state in an uncommitted working-tree file for an unbounded, sub-agent-populated window; (2) finish-cycle should validate the FSM transition *before* any filesystem side effect, and/or its re-run-safety guard should recognise and clean up its own pre-tag orphans.

- Should `begin-cycle` **commit** the `pi-reviewed → active` flip itself (a `chore(<slug>): consume pi-reviewed` commit), rather than leaving it uncommitted to "ride the cycle's own commits"? That would make the transition durable against any `git checkout`/`stash`/`reset` in the cycle.
- Should `finish-cycle` reorder so the transition validation (`apply_cadence_and_outcome`/`can_transition`) runs **before** `write_cycle_files`, so a non-`active` state fails with zero filesystem side effects?
- Should the re-run-safety predicate (finish_cycle.rs:239-241) also detect "cycle files written but no close commit/tag" and treat those files as regenerable (overwrite) rather than letting the L3 gate refuse on them?
- Should `abort-cycle`/`begin-cycle --resume` be documented as the canonical recovery for the write-then-transition-fail orphan, and should finish-cycle's `E_INTERNAL` message point at it?
- Minor: should `begin-cycle` print an explicit "consumed pi-reviewed → active" line (it currently prints nothing for the consume), so a reverted flip is visible in the transcript?

## Scope Boundary

This report authorizes investigation and a fix **in the umbod cargo project only**; it does not authorize modifying the `v8-gap-closure` topic's committed cycle history (cycle-004 is closed and tagged) or re-opening that topic.
