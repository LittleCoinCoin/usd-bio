# p53-MDM2 — Roadmap Migration Audit: `p53-mdm2` → `p53-mdm2-v2` — Observation (v0)

Date: 2026-07-30

---
type: observation
topic: p53-mdm2
spotted-during: attended PI session closing p1b Step 2; the roadmap was found unmutable while trying to record the container work
date: 2026-07-30
domain: tooling
confidence: confirmed — every claim below is a captured command result reproducible with the commands in "Re-observation Steps". The one judgement call (that carrying six completed leaves at depth 0 is faithful) is argued, not measured, and is flagged as such in "What I Am Uncertain About".
urgency: medium — nothing is blocked by this audit, but the old campaign stays authoritative until it is signed off, and the new one is where all subsequent work is recorded
deferred-because: Retirement of the old campaign is deliberately withheld pending PI sign-off of this document, so a failed review costs nothing.
---

## What Was Noticed

`__roadmap__/p53-mdm2/` could not be modified at all. Every mutating `dirtree-rdm`
command pre-flight-validates its target and aborts, and **all 8 files in that
campaign fail validation**. So the routine act of marking `p4_maboss_readback` and
`p5_integrated_demo` done — both landed in cycle-006 with 39/39 checks passing —
was impossible.

Two findings turned "repair it" into "re-found it":

1. **The Mermaid node IDs are abbreviations, not filesystem stems.** `dirtree-rdm
   update` resolves a node by matching `{stem}[` in the Mermaid block and aborts on
   a miss. **6 of 7 IDs mismatch.** So the staleness could not have been fixed in
   place *even after* a successful grammar repair — the repair was necessary but
   not sufficient, which the initial plan for this work did not appreciate.
2. **The invalid arrows were a symptom of a modelling error, not sloppiness.** The
   campaign's 7 leaves are genuinely sequential, but the grammar treats siblings as
   *parallel*. A flat 7-leaf graph therefore asserts all seven pipelines run at
   once, and the author's `-->` edges were an attempt to correct that — which the
   BNF forbids precisely because depth, not arrows, is the ordering mechanism.

## Evidence

### 1. Old campaign: all 8 files fail validation

```
FAIL README.md
FAIL f1_scaffold.md
FAIL p1_topology_from_1ycr.md
FAIL p1b_md_parameter_representation.md
FAIL p2_ddg_pipeline.md
FAIL p3_maboss_emit.md
FAIL p4_maboss_readback.md
FAIL p5_integrated_demo.md
```

Root cause in `README.md:11` — `- [design vision](…)` lacks the `R<nn>` prefix that
`<reference-item>` requires, so the reference list terminates early, `## Goal` is
demanded at line 11, and every later section cascades. Behind the cascade:
7 forbidden sibling edges (`:40-46`), the non-grammar `## Traversal` section (`:65`),
6 Nodes status cells carrying annotations plus a `🔶` absent from the 5-emoji set
(`:57-63`), an amendment row with ID `—` where `A\d+` is required (`:71`), and
4 Progress rows failing on three columns each (`:78-81`). The 7 leaves fail on
`**References**` placement, `Implementation Logic` form, and missing
`Consistency Checks`; `p2`–`p5` additionally lack step-level `Goal`.

### 2. ID-to-stem correspondence — the unrepairable defect

| Mermaid ID (old) | filesystem stem | resolves? |
|:--|:--|:--|
| `f1_scaffold` | `f1_scaffold` | match |
| `p1_topology` | `p1_topology_from_1ycr` | **MISMATCH** |
| `p1b_mdparams` | `p1b_md_parameter_representation` | **MISMATCH** |
| `p2_ddg` | `p2_ddg_pipeline` | **MISMATCH** |
| `p3_maboss` | `p3_maboss_emit` | **MISMATCH** |
| `p4_readback` | `p4_maboss_readback` | **MISMATCH** |
| `p5_demo` | `p5_integrated_demo` | **MISMATCH** |

New campaign: **9 of 9 match**, because `dirtree-rdm add` generates the ID from the
filesystem name. The defect is structurally impossible to reintroduce by hand.

### 3. New campaign: 17 of 17 files valid

4 directory READMEs + 13 leaves. Sweep command in "Re-observation Steps".

### 4. Node-level mapping — every old node accounted for

| Old node | Disposition | New location | Reason |
|:--|:--|:--|:--|
| `README.md` (campaign) | superseded | `p53-mdm2-v2/README.md` | Re-authored BNF-valid; `## Traversal` content folded into `## Gotchas`, which is the grammar's home for it |
| `f1_scaffold.md` | carried + done | same name | Status was already correct |
| `p1_topology_from_1ycr.md` | carried + done | same name | Status was already correct |
| `p1b_md_parameter_representation.md` | carried + inprogress | same name | Step 1 done; Step 2 delegated (see §6) |
| `p2_ddg_pipeline.md` | carried + done | same name | Status already correct; live ΔΔG landed cycle-006 per R11 |
| `p3_maboss_emit.md` | carried + done | same name | Status was already correct |
| `p4_maboss_readback.md` | carried + **corrected to done** | same name | Old campaign said planned; landed cycle-006 per R11 |
| `p5_integrated_demo.md` | carried + **corrected to done** | same name | Old campaign said planned; landed cycle-006 per R11 |
| Amendment rows `—`, `A1`, `A2` | superseded | new `A0` founding row | History is summarised in `A0`'s rationale; the old rows remain readable in the retired campaign |

No old node was deleted, renamed, or dropped.

### 5. Step-level mapping — 15 of 15 old steps accounted for

Step titles and commit messages were compared verbatim.

| Old leaf | Steps | Titles preserved | Commit messages preserved |
|:--|:--:|:--|:--|
| `f1_scaffold` | 2 | both verbatim | both verbatim |
| `p1_topology_from_1ycr` | 3 | all three verbatim | all three verbatim |
| `p1b_md_parameter_representation` | 2 | Step 1 verbatim; **Step 2 changed** | Step 1 verbatim; **Step 2 changed** |
| `p2_ddg_pipeline` | 2 | both verbatim | both verbatim |
| `p3_maboss_emit` | 2 | both verbatim | both verbatim |
| `p4_maboss_readback` | 2 | both verbatim | both verbatim |
| `p5_integrated_demo` | 2 | both verbatim | both verbatim |

**Step counts match exactly, per leaf: 2, 3, 2, 2, 2, 2, 2 = 15.** No step was
merged, split, renumbered, or dropped. 14 of 15 steps are byte-identical in title
and commit; the single exception is the mandated delegation in §6.

### 6. Deliberate divergences — two, both in `p1b_md_parameter_representation`

These are the only intentional content changes, and both correct claims the PI
already reversed:

1. **The Docker-only premise.** The old leaf stated as a PI directive that
   "dgx1/banyan have no Singularity; use Docker". Q-005 and Q-007 reversed this:
   Docker **builds** (daemon-as-root on banyan), Singularity **runs** (on both
   clusters). The new leaf marks the old framing **superseded and quotes it
   verbatim** with the Q-005/Q-007 citation rather than deleting it, so the
   historical record survives.
2. **Step 2 becomes a delegation.** Title `(Docker, bind-mount)` →
   `(delegated to p1b_container_runtime/)`; commit
   `feat(…): containerized MD execution pattern for dgx1/banyan` →
   `chore(…): close p1b Step 2 once p1b_container_runtime/ gates pass`. The step is
   neither deleted nor renumbered — its execution is decomposed into a subtree, and
   its old Success Gate demanding "a reusable Docker image + bind-mount run
   pattern" becomes the subtree's gates.

### 7. Invented fields — disclosed, because invented content is what a reviewer must scrutinise

The old leaves lacked grammar-required fields, so these were authored rather than
carried:

| Field | Where | How derived |
|:--|:--|:--|
| `**Consistency Checks**` | all 15 steps | Derived from each step's own Deliverables; function names and signatures (`parse_pdb`, `run_all`, `default_integrated_path`, `run()` on each test module) checked against real source before writing. Not executed. |
| `**Implementation Logic**` | 13 of 15 steps | Split out of existing Goal prose where present; authored from the step's Deliverables where absent. `f1_scaffold`'s existing inline form was reshaped to header-plus-body. |
| `**Goal**` (step-level) | 8 steps in `p2`–`p5` | Authored from Deliverables and commit message. |
| `**References**` (header) | all 7 leaves | Moved from end-of-file to the header block, as the grammar requires. Content unchanged. |

One check is deliberately `(expected: FAIL)` — `p1b` Step 2's, which asserts the
container subtree still has open gates. That is honest for a step that is not yet
closeable, and it flips to PASS when the subtree completes. It is not a
placeholder.

## Re-observation Steps

```bash
D=/Users/hacker/.claude/skills/managing-roadmaps/scripts/dirtree-rdm.sh
# old campaign still invalid (expect 8 FAIL)
for f in __roadmap__/p53-mdm2/*.md; do bash $D validate "$f" >/dev/null 2>&1 \
  && echo "PASS $f" || echo "FAIL $f"; done
# new campaign valid (expect 17 PASS, 0 FAIL)
find __roadmap__/p53-mdm2-v2 -name '*.md' | while read f; do
  bash $D validate "$f" >/dev/null 2>&1 || echo "FAIL $f"; done
# step counts match per leaf
for b in f1_scaffold p1_topology_from_1ycr p1b_md_parameter_representation \
         p2_ddg_pipeline p3_maboss_emit p4_maboss_readback p5_integrated_demo; do
  printf '%-34s old=%s new=%s\n' "$b" \
    "$(grep -c '^## Step ' __roadmap__/p53-mdm2/$b.md)" \
    "$(grep -c '^## Step ' __roadmap__/p53-mdm2-v2/$b.md)"; done
```

## Scope Boundary

This audit covers roadmap structure only. It does **not** re-verify the pipeline
work the carried leaves describe — that rests on R11's 39/39 checks and the
committed artifacts. It does not touch `examples/` and makes no claim about the
container work, which is recorded separately.

## What I Am Uncertain About

- **Depth semantics for completed work is a judgement, not a measurement.** The six
  done leaves sit as depth-0 siblings, which under the grammar's semantics asserts
  they are parallel. They were not — they were sequential. The argument is that
  depth should encode *remaining* execution order and that historical order belongs
  in prose, which is now recorded in `## Gotchas`. A reviewer who disagrees would
  want them nested, at the cost of a six-level tree re-litigating shipped work.
- **The invented consistency checks were never executed.** They were derived from
  real symbols verified against source, but no command was run. Any that turn out
  to be wrong will surface the first time a leaf is re-opened, not now.
- **`p1b`'s Pre-conditions and one Success Gate were reworded** beyond the two
  mandated corrections, to stay coherent with the corrected build/run split. Intent
  is preserved; the wording is not verbatim.
- **`__reports__/p53-mdm2/README.md` is not yet updated** for this report; that
  belongs to whichever commit lands the index entry.
