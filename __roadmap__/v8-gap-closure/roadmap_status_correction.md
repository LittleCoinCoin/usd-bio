# Correct Stale v8 ROADMAP Statuses

**Goal**: Update `examples/foundation_demo_v8/ROADMAP/README.md` to reflect the true completion state of M1, M2, and M3, which are all done but currently marked "In Progress" or "Blocked".
**Pre-conditions**:
- [ ] `examples/foundation_demo_v8/ROADMAP/README.md` milestone table currently reads: M1 "In Progress", M2 "Blocked on M1", M3 "Blocked on M1+M2" [source: examples/foundation_demo_v8/ROADMAP/README.md:19-21]
- [ ] Committed evidence of M1 completion exists: `examples/foundation_demo_v8/output/assembly_demo.usda` (USD assembly from real PDB data) [source: bash find confirming assembly_demo.usda exists]
- [ ] Committed evidence of M2 completion exists: `examples/foundation_demo_v8/output/trajectory_demo.usda` and `examples/foundation_demo_v8/output/clips/trajectory_clip.usda` (trajectory playback via Value Clips) [source: bash find confirming trajectory_demo.usda and clips/trajectory_clip.usda exist]
- [ ] Committed evidence of M3 completion exists: documentation files in `examples/foundation_demo_v8/` (confirmed via perspective report §1 "What We Have Proven") [source: __reports__/foundation_demo/perspective/01_v8_to_production_perspective.md:22-44]
**Success Gates**:
- ⬜ `grep "In Progress\|Blocked" examples/foundation_demo_v8/ROADMAP/README.md` returns zero matches
- ⬜ M1, M2, and M3 each show "Complete" in the milestone table
- ⬜ The file remains valid Markdown (no broken table syntax)
**References**: [R02 §1 What We Have Proven](../../__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md) — table of claims vs. evidence confirming all three milestones are demonstrably complete

## Step 1: Correct milestone status markers and add completion evidence links
**Goal**: Replace the three stale status strings in the milestone table with "Complete" and add a brief evidence note per milestone so a reader can verify the status without running any code.
**Implementation Logic**:
1. In `examples/foundation_demo_v8/ROADMAP/README.md`, locate the milestone table at lines 17–21:
   ```
   | M1 | Parse ABL kinase PDB and create composed USD assembly | In Progress |
   | M2 | Attach MD trajectory frames via Value Clips | Blocked on M1 |
   | M3 | User guides and dev lesson documentation | Blocked on M1+M2 |
   ```
2. Replace each Status cell:
   - M1: `In Progress` → `Complete — \`output/assembly_demo.usda\``
   - M2: `Blocked on M1` → `Complete — \`output/trajectory_demo.usda\``
   - M3: `Blocked on M1+M2` → `Complete — see \`examples/foundation_demo_v8/\` docs`
3. No other content changes; this file is hand-managed markdown, not a dirtree-rdm node. [assumption: no other sections in the file depend on the "In Progress" or "Blocked" text as machine-readable markers — the file is hand-written markdown as confirmed by the ROADMAP README not being listed as a dirtree-rdm-managed roadmap]
4. WHY add evidence links rather than just "Complete": a plain "Complete" with no pointer is not materially better than "In Progress" for a reader trying to verify the claim; the committed artifact path is the falsifiable evidence.
**Deliverables**: `examples/foundation_demo_v8/ROADMAP/README.md` — modified section: Milestones table (lines 17–21)
**Consistency Checks**: `grep -c "In Progress\|Blocked" examples/foundation_demo_v8/ROADMAP/README.md | grep -q "^0$" && echo PASS` (expected: PASS)
**Commit**: `docs(v8-gap-closure): correct stale M1/M2/M3 statuses in foundation_demo_v8 ROADMAP`
