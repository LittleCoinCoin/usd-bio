# Migration: `p53-mdm2` → `p53-mdm2-v2`

**Retired** 2026-07-30, on PI sign-off of
[R12 roadmap migration audit](../../__reports__/p53-mdm2/12-roadmap_migration_audit_v0.md).
Live work is in [`../p53-mdm2-v2/`](../p53-mdm2-v2/README.md).

## Why this campaign was retired rather than repaired

All 8 files here fail `dirtree-rdm validate`. Every mutating `dirtree-rdm` command
pre-flight-validates its target and aborts, so this graph had been frozen — which is
why cycle-006's completed `p4_maboss_readback` and `p5_integrated_demo` were never
marked done.

The decisive finding is that **a grammar repair would not have been sufficient.**
`dirtree-rdm update` locates a node by matching `{filesystem-stem}[` inside the
Mermaid block and fails when it misses. Six of seven IDs here are abbreviations:

| Mermaid ID | filesystem stem | resolves? |
|:--|:--|:--|
| `f1_scaffold` | `f1_scaffold` | match |
| `p1_topology` | `p1_topology_from_1ycr` | **no** |
| `p1b_mdparams` | `p1b_md_parameter_representation` | **no** |
| `p2_ddg` | `p2_ddg_pipeline` | **no** |
| `p3_maboss` | `p3_maboss_emit` | **no** |
| `p4_readback` | `p4_maboss_readback` | **no** |
| `p5_demo` | `p5_integrated_demo` | **no** |

Renaming those IDs by hand is possible, but at that point the file is being rewritten
anyway — and rewriting in place would have destroyed the only unambiguous source of
truth for auditing what was carried. Re-founding as a sibling kept this campaign
readable while the successor was built and checked against it.

A second, deeper reason: the forbidden sibling `-->` edges were a **symptom of a
modelling error**, not sloppiness. The grammar treats siblings as *parallel*, so a
flat 7-leaf campaign asserts all seven pipelines run concurrently. The original
author's arrows were an attempt to correct that, using the one mechanism the BNF
forbids. The successor spends depth on artifact boundaries and records the historical
pipeline ordering as prose in `## Gotchas`, which is the grammar's home for it.

## What was carried

All 7 leaves, with **step counts preserved exactly** (2, 3, 2, 2, 2, 2, 2 = 15 steps)
and 14 of 15 step titles and commit messages byte-identical. R12 holds the row-by-row
node-level and step-level mapping.

Corrections applied during the carry:

- `p4_maboss_readback` and `p5_integrated_demo` → **done** (both landed in cycle-006;
  this campaign could not record it)
- `p1b_md_parameter_representation` → **inprogress**, with Step 2 reframed as a
  delegation to the successor's `p1b_container_runtime/` subtree

## The two deliberate divergences

Both are in `p1b_md_parameter_representation`, and both correct claims the PI had
already reversed:

1. **The Docker-only premise.** This campaign recorded as a PI directive that
   "dgx1/banyan have no Singularity; use Docker". Q-005 and Q-007 reversed it: Docker
   **builds** the image (the daemon builds as root on banyan, which is why Route B
   works), Singularity **runs** it on both clusters. The successor marks the old
   framing superseded and **quotes it verbatim** rather than deleting it.
2. **Step 2's scope.** Title and commit changed to express delegation. The step is
   neither deleted nor renumbered; its old Success Gate demanding "a reusable Docker
   image + bind-mount run pattern" became the subtree's own gates.

## Fields that were invented, not carried

The leaves here predate several grammar requirements, so the successor's versions
contain authored content: **all 15 `Consistency Checks`, 13 `Implementation Logic`
bodies, and 8 step-level `Goal`s**. Each was derived from the step's own Deliverables,
with referenced function names and signatures checked against real source — but none
were executed. R12 §7 lists them, because invented content is what a reviewer needs
to scrutinise.

## If you need something from here

Read it, don't run it. This campaign's Amendment Log (`—`, `A1`, `A2`) records the
Q-003/Q-004 fold-in and the Docker→Singularity pivot; the successor summarises that
history in its own `A0` founding row rather than restating it.
