# Reports — umbod-cli

Engineer-facing reports about the **umbod CLI tool itself** (the async-cycle FSM
enforcer), as distinct from any research topic. Filed here when a umbod bug or
rough edge is hit during normal cycle work in this repo.

## Round 00 — 2026-07-06

- [`00-observation_v0.md`](00-observation_v0.md) — **confirmed bug.** During `v8-gap-closure` cycle-004, `finish-cycle` failed and then blocked its own retry. Two chained defects: (1) `begin-cycle` leaves the `pi-reviewed → active` FSM flip **uncommitted** in the working tree, so a sub-agent's `git checkout -- STATUS.md` silently reverted it; (2) `finish-cycle` writes the immutable cycle files **before** validating the FSM transition, so the failed transition orphaned those files and the L3 gate then refused every retry on that debris. Includes source-line citations (umbod 0.5.1 `7d8a741`), git-history evidence, and a minimal synthetic repro. `urgency: medium`.

## Status

Open for umbod-engineer review. Scope boundary: fix lives in the umbod cargo repo
(`~/.claude/skills/umbod/scripts/umbod`); does not touch this repo's committed cycle
history. Recovery that worked in-cycle: `begin-cycle --resume` + remove orphaned
cycle files + commit the STATUS active-projection + re-run `finish-cycle`.
