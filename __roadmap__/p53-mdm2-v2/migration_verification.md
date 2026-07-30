# Roadmap Migration Verification

**Goal**: Prove that re-founding the campaign lost nothing — every node and every step of the superseded `__roadmap__/p53-mdm2/` is accounted for here — and only then retire the old campaign.
**Pre-conditions**:
- [x] `__roadmap__/p53-mdm2-v2/` authored, with all nodes added breadth-first through `dirtree-rdm`
- [x] The superseded campaign is untouched, so it remains an unambiguous source of truth for the comparison
- [ ] The seven carried leaves have had their bodies ported and validated
**Success Gates**:
- ⬜ `[static]` Every node in the old campaign appears exactly once in the mapping table, marked carried, done or superseded, each with a reason
- ⬜ `[static]` Every step of every old leaf appears exactly once in the mapping table — step-level, not just node-level, since a leaf can survive while a step silently vanishes
- ⬜ `[run]` `dirtree-rdm validate` exits clean on the new campaign README, all four directory READMEs, and all thirteen leaves
- ⬜ `[static]` Old and new step counts match per leaf, or every difference carries an explicit justification
- ⬜ `[behavioral]` PI sign-off is recorded **before** the old campaign is annotated as retired
**References**: [R11 cycle-006 findings](../../__reports__/p53-mdm2/11-cycle006_findings_v0.md) — the cycle-006 outcomes that make `p4_maboss_readback` and `p5_integrated_demo` genuinely done despite the old campaign still listing them as planned

## Step 1: Build the old-to-new mapping table
**Goal**: Produce the audit that makes step loss visible rather than assumed.
**Implementation Logic**:
Enumerate the old campaign mechanically rather than by reading — seven leaf files plus the campaign README — and for each, list every step heading. Build a table with one row per old node and one row per old step, each mapped to its destination in the new campaign and marked carried, done or superseded with a stated reason. Node-level checking is not sufficient: the failure mode being guarded against is a leaf that survives while one of its steps quietly disappears during the port. Where a field had to be invented to satisfy the grammar — the old leaves lacked implementation logic and consistency checks entirely — say so explicitly, because invented content is exactly what a reviewer needs to scrutinise. Record the two known deliberate prose changes as superseded rather than carried: the claim that the clusters have no Singularity, and the old Step 2 success gate demanding a Docker bind-mount pattern.
**Deliverables**: `__reports__/p53-mdm2/12-roadmap_migration_audit_v0.md` — front-matter with type, topic, date and confidence; a node-level mapping table; a step-level mapping table; an invented-fields section; a deliberate-divergence section
**Consistency Checks**: `grep -c '^| ' __reports__/p53-mdm2/12-roadmap_migration_audit_v0.md` (expected: PASS)
**Commit**: `docs(p53-mdm2): roadmap migration audit for the v2 campaign`

## Step 2: Sweep the whole new campaign through the validator
**Goal**: Establish that the replacement is grammatically sound everywhere, which the campaign it replaces never was.
**Implementation Logic**:
Validate every README and every leaf, not just the campaign root — the superseded campaign failed on all eight of its files, and its root passing would have said nothing about its leaves. Record the full output in the audit so the claim is evidenced. Confirm too that the Mermaid node identifiers match the filesystem stems exactly, since that mismatch is what made status updates impossible in the old campaign and is the specific defect this re-founding exists to avoid; a passing validator does not by itself check it, so assert it separately by comparing the node table against the directory listing.
**Deliverables**: `__reports__/p53-mdm2/12-roadmap_migration_audit_v0.md` — appended validator sweep output for all seventeen files (four directory READMEs plus thirteen leaves) and an identifier-to-stem correspondence check
**Consistency Checks**: `bash /Users/hacker/.claude/skills/managing-roadmaps/scripts/dirtree-rdm.sh validate __roadmap__/p53-mdm2-v2/` (expected: PASS)
**Commit**: `docs(p53-mdm2): validator sweep evidence for the v2 campaign`

## Step 3: Retire the superseded campaign
**Goal**: Mark the old campaign unmistakably dead, but only after the audit has been reviewed.
**Implementation Logic**:
This step runs only on PI sign-off, which is why it is last: until then the old campaign remains authoritative and a failed review costs nothing. Retirement cannot be done with the tooling — status lives in a parent Nodes table and a campaign root has no parent, and the files are BNF-invalid so every mutating command aborts on pre-flight anyway. So annotate by hand, which is legitimate precisely because the file is no longer a live managed graph: a blocked banner at the top of the old README naming its successor and the audit, plus a short migration note explaining why it was retired rather than repaired. Never delete the directory — blocked is the sanctioned way to end a node's life, and the old campaign is the evidence base the audit cites.
**Deliverables**: `__roadmap__/p53-mdm2/README.md` — hand-written blocked banner naming the successor campaign and citing the audit; `__roadmap__/p53-mdm2/MIGRATION.md` — why it was retired, what replaced it, and the two deliberate divergences
**Consistency Checks**: `grep -c 'p53-mdm2-v2' __roadmap__/p53-mdm2/README.md` (expected: PASS)
**Commit**: `docs(p53-mdm2): retire the superseded roadmap campaign`
