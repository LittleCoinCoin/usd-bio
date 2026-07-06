# Cycle 005 WORKLOG — v8-gap-closure

## Situation

Woke on `pi-reviewed` (cycle-004 closed `open`). `umbod diff`: INBOX +2 entries — the PI's
answer to cycle-004's next-decision. The PI **directed the (a)-(c) enhancements to run this
cycle** (not confirm-and-close), with a strong steering mandate (verbatim): *"These should be
considered carefully not as band-aid fixes but scalable integration into the current usd data
and representation layers ... we want the fixes but we must accept deep refactoring if that's
the only scalable way to fix them because this refactoring itself will be a lesson worth
learning."* No open questions (Q-001, Q-002 both answered). This is a reactive
enhancement cycle, tracked outside the complete (15/15) formal roadmap; honesty-contract is
the catch-net.

The three directed items:
- (a) confirm the Specializes doc correction (done cycle-004) satisfies the real-data condition;
- (b) wire REAL provenance lineage into `provenance_metadata` (sentinels are wrong/fabricated);
- (c) fix the latent `/World`-cascade `representation` variant no-op across demos.

## Plan

Two independent workstreams delegated to Sonnet sub-agents in parallel, each carrying the
honesty-contract worker mandate + forOUSD interpreter guidance + context7 mandate + an
explicit stop-and-report escape hatch (no band-aids):
1. (c) scalable representation-cascade refactor — root-cause, context7-verify, implement the
   scalable pattern, prove with falsification-resistant read-back tests, extend the harness.
2. (b) real provenance — extract real ShinobuLab run metadata, wire it data-drivenly, add
   read-back tests + a negative-sentinel guard.
Then orchestrator tie-breaker verification → verifier sub-agent → report → finish.

## Work done

**(b) Real provenance (sub-agent, commit 2b14733).** New `provenance_source.py`
(examples/composition_advanced/provenance_metadata/, zero-pxr-import, shaped like
`usdbio_env.py`) parses the real GENESIS `.inp`/`.log` under `$USDBIO_DATA_DIR` at generation
time and returns a validated record — chosen over a hand-authored metadata file so provenance
can never drift from the data. `04_create_assembly.py` now calls
`load_shinobulab_provenance(get_data_dir())` instead of authoring literals. Real values:
`sourcePdb=atp-complex-solv35.pdb` (was wrong `2HYY.pdb`), `softwareVersion=2.0.3` (was
fabricated `2.1.0`), `forceField=AMBER (family; specific set not recorded in data)` (honestly
family-only — the point-release is genuinely unrecoverable from the data dir),
`simSettings={NPT,VRES,1.0 bar,310 K,3.5 fs}`, `timestamp=2023-08-25T17:06:48`. Unresolvable
fields become literal `"unknown"`, never fabricated. New `test_provenance_lineage.py` opens
the artifact fresh, independently re-parses the raw files (separate regex, not the loader's
output), asserts equality + a negative-sentinel guard (verified to fire on a synthetic
sentinel stage). Six-field schema kept unchanged (backward-compatible).

**(c) Scalable cascade fix (sub-agent, commit d10cd8a).** context7-verified the mechanism:
`GetVariantEditContext()` retargets the EditTarget to the variant-owning prim's own
variant-selection node; opinions only map onto **namespace descendants** of that node.
`/World` and `/ABLComplex` were siblings (the latter arrived via SubLayer at its own top-level
path), so `/World`'s per-mode variant blocks were empty `{}` — a decorative no-op. Enumeration
found exactly two genuinely-defective demos (`assembly_demo.py`, `trajectory_demo.py`);
`element_grid`/`water`/`residue_grid` also use `/World` but their instances ARE genuine
children (correct pattern, no defect); the rest were fixed cycle-004 or n/a. Chosen scalable
pattern (matches USD model-hierarchy convention + what curves/departmental/solvent demos
already converged on): retire the `/World` proxy, make the geometry root the `defaultPrim`
owning `representation`. Also fixed an orthogonal latent gap: `trajectory_demo` never authored
`metersPerUnit` on its own root layer. Regenerated the two `.usda`. New
`test_representation_cascade.py` proves the cascade genuinely resolves: atom-Sphere radius
takes 4 distinct values across the 4 modes, cross-checked against `data.get_scaled_radius()`
(independently-derived), + bond visibility switches ballstick-only.

**Orchestrator (tie-breaker).** Committed the begin-cycle STATUS projection (pi-reviewed →
active). Independently re-ran all four suites under forOUSD from a fresh process:
`test_representation_cascade.py` 6/6, `test_provenance_lineage.py` 2/2, `run_tests.py` 30/30
(was 29/30 mid-cycle — the +1 is the `metersPerUnit` fix), `usdview_regression_check.py`
44 pass / 0 fail / 1 documented known-residual, exit 0. The two agents' reports are mutually
consistent (the provenance agent's transient 29/30 was the missing `metersPerUnit` the cascade
agent then fixed). Findings report `05-findings_v0.md` written + README updated (commit after
report). Working tree clean before finish.

**(a) resolved:** the Specializes correction stands (context7-verified, cycle-004 commit
6d109e9); the real-data-demo condition it was gated against is materially advanced by (b)'s
real ShinobuLab provenance + the already-real trajectory clips. No new code needed.

**Security event (surfaced, not buried):** the (c) sub-agent reported a prompt-injection
attempt — a mid-task `<system-reminder>` falsely claiming its edits were reverted and
instructing it not to tell the orchestrator. The agent verified against disk (edits intact),
disregarded the false instruction, and surfaced it per the honesty contract. Correct handling.
Origin unknown; flagged to PI in the findings report's Contradictions & Surprises section.

## Verifier verdict (cycle-005, final, verbatim)

```
verdict: aligned
inbox-coverage:
  - PI directive (a) "does the Specializes correction satisfy the real-data condition?" → `__reports__/v8-gap-closure/05-findings_v0.md` (PI directive disposition table, row (a)) — disposition "confirmed", pointing to cycle-004 commit 6d109e9; no new code required, correctly treated as a confirm-only item.
  - PI directive (b) "wire REAL provenance lineage into provenance_metadata" → `examples/composition_advanced/provenance_metadata/provenance_source.py` (new, 326 lines, parses real GENESIS `.inp`/`.log` under `$USDBIO_DATA_DIR`) + `examples/foundation_demo_v8/templates/04_create_assembly.py` (now calls `load_shinobulab_provenance`) + regenerated `examples/foundation_demo_v8/assets/level4_assemblies/abl_kinase_complex.usda` + `examples/foundation_demo_v8/tests/test_provenance_lineage.py` (independently re-run: 2/2 PASS, cross-checked against the real ShinobuLab data dir, not generator state) — commit 2b14733.
  - PI directive (c) "fix the latent /World-cascade variant no-op across demos" → `examples/foundation_demo_v8/demos/assembly_demo.py`, `examples/foundation_demo_v8/demos/trajectory_demo.py` (decorative `/World` retired, geometry root now `defaultPrim` owning `representation`) + regenerated `output/assembly_demo.usda`, `output/trajectory_demo.usda` + `examples/foundation_demo_v8/tests/test_representation_cascade.py` (independently re-run: 6/6 PASS, radii `{points:0.18, ballstick:0.30, balls:0.36, vdw:1.2}` cross-checked against `data.get_scaled_radius()`) — commit d10cd8a.
intent-tracking: aligned
work-depth: The two enhancements go as deep as the PI's "scalable integration, not band-aid fixes" mandate demanded, and the report's numbers hold up under independent re-execution: I re-ran `test_representation_cascade.py` (6/6 PASS) and `test_provenance_lineage.py` (2/2 PASS) fresh under the `forOUSD` interpreter, and both produced the exact field values and radii claimed in `__reports__/v8-gap-closure/05-findings_v0.md`; I also re-ran `examples/foundation_demo_v8/tests/run_tests.py` and got the claimed 30/30. (b)'s fix is a genuine data-driven loader (regex-parses real `.inp`/`.log` GENESIS artifacts, falls back to literal `"unknown"` rather than fabricating, documented rejection of a hand-authored-JSON alternative) rather than a hardcoded literal swap. (c)'s fix root-causes the SubLayer-sibling-vs-namespace-descendant USD semantics issue and retires the decorative `/World` prim rather than patching around it, matching the pattern already used elsewhere in the codebase. One process gap: `__threads__/v8-gap-closure/cycles/cycle-005/` has no `WORKLOG.md`, only `INBOX-consumed.md` — the running-record role is filled instead by the findings report and `__reports__/v8-gap-closure/README.md`'s Round 05 entry, both of which are substantive and re-readable, so this is a bookkeeping gap rather than a coverage or depth gap.
recommended-action: proceed
```

Orchestrator adjudication: verdict accepted (aligned; proceed). The WORKLOG-absence note is
resolved by this file, written via `finish-cycle --worklog`. Outcome **proposed-resolution**:
all three PI-directed items are done and independently verified, the two reasons cycle-004
stayed `open` (real-provenance wiring; the /World-cascade latent bug) are both now closed, no
open questions remain, and the residual items are honestly-documented non-blockers (AMBER
point-release genuinely unrecoverable from the data; headless-vs-GUI verification consistent
with the whole repo; provenance-as-its-own-layer explicitly deferred to a future topic). The
PI's own INBOX framed exactly this fork ("confirm-and-close ... or direct the (a)-(c)
enhancements next cycle") — the directed enhancements are now complete, so proposing resolution
for PI confirm-and-close is the honest state.

## What I am uncertain about

- The exact AMBER force-field point-release (ff99SB-ILDN vs ff14SB) is genuinely not recorded
  anywhere in the data dir; recorded honestly as family-only. If the PI has this out-of-band,
  the loader will pick it up once it's in the data. [assumption: family-only is the honest
  register; the PI may prefer stricter "unknown" — raised as a [now] steering question.]
- All cascade/visibility claims are headless `Usd.Stage` read-back (no display in this env),
  consistent with the entire repo's test methodology. A one-time interactive usdview
  spot-check would fully close the loop.
- The prompt-injection event origin (tooling artifact vs. injected content) is undetermined;
  surfaced for PI awareness, handled correctly by the sub-agent.
- Provenance authored on the assembly root this cycle; a composable provenance *layer* (for
  multi-dataset scale) is a reasonable future step, deferred to the p53-mdm2 topic.
