# Cycle 004 WORKLOG — v8-gap-closure

## Situation

Woke on `pi-reviewed` (cycle-003 had proposed-resolution). The PI did **not** close: instead filed 4
INBOX bug reports about broken usdview output and answered Q-002 with follow-up conditions. `umbod diff`:
INBOX +4 items; Q-002 answered. So this is a real, reactive working cycle — not a re-verify. This
INBOX-driven bug-fix work is tracked outside the (complete, 15/15) formal roadmap; honesty-contract is the
catch-net (per honesty-contract §3).

PI signals:
- INBOX (4): (1) clips in output/clips/ render grey/static, Play dead; (2) document how to run demos/clips;
  (3) curves_demo.usda variant switch = wrong location + double display; (4) clean remnants OR
  root-cause + document + build an automated debug cycle LLM-agents can run.
- Q-002 answer (direction b, conditional): (a) verify Specializes claim vs context7 openusd → if confirmed,
  correct __design__/; (b) want runnable demo on real ShinobuLab data for live meetings; (c) elaborate the
  provenance_metadata sentinel flag + usda-vs-usdc data provenance.

## Plan

1. Diagnose the broken outputs (sub-agent, forOUSD + real usd tools) → intended-vs-bug per item.
2. Build the requested automated debug harness + README + doc callouts (sub-agent A).
3. Fix the genuine curves_demo bug + the same class the harness surfaces (sub-agent B).
4. Orchestrator (tie-breaker): verify harness green + curves fix; refine net baseline.
5. Q-002: verify Specializes vs context7 + correct doc; investigate provenance.
6. inbox-ack; findings report; verifier; finish-cycle honestly.

## Work done

**Diagnosis (Sonnet sub-agent, forOUSD + /Users/hacker/Documents/bin/OpenUSD/bin tools):** Root-caused all
4 items. Item 1/2: `output/clips/*` are intended value-clip payloads — bond Cylinders only, no atoms/color,
`HasAuthoredTimeCodeRange()==False` → grey + dead Play when opened directly; the topology + color + variants
live in the sublayer, composed only by `trajectory_demo.usda`. Documentation gap, not a defect. Item 3:
genuine bug, two causes — (a) no default `representation` selection (curves-only on fresh open); (b)
`trajectory_clip_curves.usda` drove only `/ABLComplex/Bonds`, never per-atom translates → atoms frozen at
PDB frame while bonds at MD frame (two disjoint clusters). Item 4: nothing is a remnant (all tested);
systemic fix = the automated debug cycle. Key gotcha found: `/usr/bin/usd*` are Apple SceneKit stubs
(different USD) — must use the real pxr build.

**Harness + docs (Sonnet sub-agent A):** `tests/usdview_regression_check.py` — 6-gate headless net
(structural / variant-completeness / visibility-exclusivity / clip-topology-sync / usdrecord frame-diff
[opt-in] / usdchecker floor) with a per-file role manifest. Applied to existing artifacts (INTENT's
"apply to existing v8 artifacts first"): flagged curves_demo on gates 2+4 as predicted, AND surfaced the
same gate-2 defect (no default variant selection) in binary_demo, departmental_demo, solvent_demo — latent,
never PI-reported. Commits e8979cc (README), a695fe5 (doc callouts), b7953da (harness). `README.md` (new)
documents env setup, viewer-entry-points vs payload artifacts, demo pipeline, harness usage.

**Curves fix + class fix (Sonnet sub-agent B):** cause (a) fixed in curves_demo.py + the 3 other demos
(default `representation` selection authored on the prim whose same-layer cascade actually works — B also
discovered the `/World`-wrapper cascade is a decorative no-op cross-layer, left out of scope, noted in
commits). cause (b) fixed by extending `write_curves_clip()` in converters/xtc_to_clips.py to emit per-atom
`xformOp:translate` from the SAME per-frame positions array as the bonds (single source of truth), reading
real ShinobuLab XTC via mdtraj; added a `--curves` CLI flag; regenerated curves_demo.usda +
trajectory_clip_curves.usda. New falsification-resistant test `tests/test_curves_demo.py` (3/3). Commits
10ce135, b160e7c, e7e36ca, 47b836c, f81e3c9, 7c6dd05.

**Orchestrator (tie-breaker):** Independently re-ran the harness (exit 1, one solvent_demo gate-2 residual)
and confirmed it is a genuine harness false-positive (whole-stage Traverse flags /ABLComplex template +
/Solvent/Prototypes/Water PointInstancer prototype — neither viewer-rendered; real geometry
/SolvatedComplex/Protein passes gates 1+3). Added a documented `EXPECTED_RESIDUALS` allow-list so the
baseline exits 0 (a net that always exits non-zero trains people to ignore it) while any NEW failure still
exits 1 (commit e035cb1). Independently verified the curves fix: default selection='ballstick', atom
translate resolves via ValueClips, 19.32 Å motion t0→t19, atom pos matches trajectory demo's MD frame.
Final harness: 44 pass / 0 fail / 1 known-residual, exit 0.

**Q-002:** (a) context7 CONFIRMED the Specializes claim is backwards (PcpArcType enum: Specialize last =
weakest; glossary: opinions on the specialized prim override the base). Corrected __design__/ §2.1 row S +
§7 (commit 6d109e9) — PI condition (b) satisfied. (b)/(c) provenance: all trajectory clips (both .usda and
.usdc) derive from real ShinobuLab XTC via mdtraj [xtc_to_clips.py:63,225,483-551; usda_to_usdc.py].
provenance_metadata uses placeholder sentinels — `2HYY.pdb` is WRONG (real starting structure is
atp-complex-solv35.pdb per ShinobuLab/README.md); GENESIS engine + Amber FF directionally correct. Real
lineage is wire-in-able from the data-dir README/.docx — surfaced as a steering question, not done (scope).

**Artifacts:** `__reports__/v8-gap-closure/04-findings_v0.md` (+ README update). INBOX 4 items acked
(6e5138c). Findings report committed. Working tree clean before finish.

## Verifier verdict (cycle-004, final, verbatim)

```
verdict: aligned
inbox-coverage:
  - Item 1 (clips render as grey static cylinders / dead Play in usdview) → `examples/foundation_demo_v8/README.md` + `docs/13_value_clips_for_trajectories.md` (diff) + `tests/usdview_regression_check.py` payload-classification logic; disposition documented in `__reports__/v8-gap-closure/04-findings_v0.md` (Results Table "INBOX item disposition" row 1)
  - Item 2 (document how to run demos/clips if intended) → `examples/foundation_demo_v8/README.md` (new, 213 lines) + `docs/11_trajectory_demo_guide.md` and `docs/13_value_clips_for_trajectories.md` callouts (commit `a695fe5`, `7c6dd05`)
  - Item 3 (curves_demo.usda wrong location + double display) → fixed in commits `10ce135` (drive per-atom translate from curves clip) and `b160e7c` (default representation selection); independently re-verified by running `examples/foundation_demo_v8/tests/test_curves_demo.py` fresh in this review, 3/3 PASS, confirming atom/bond desync is resolved (t0→t19 displacement 19.32 Å vs prior ~0)
  - Item 4 (clean remnants OR root-cause + automated debug cycle) → `examples/foundation_demo_v8/tests/usdview_regression_check.py` (new, 844 lines, 6-gate headless harness); re-ran independently in this review: 44 pass / 0 fail / 1 documented known-residual, matching the findings report's claimed baseline exactly
intent-tracking: aligned
work-depth: The cycle goes as deep as its INBOX commitments demanded and the claims are independently reproducible, not just asserted. I re-ran both new test artifacts fresh (`test_curves_demo.py` and `usdview_regression_check.py`) outside the cycle's own narrative and got results matching the findings report verbatim (3/3 and 44/0/1). The curves fix is a real two-line-of-reasoning root cause (asymmetric time-sampling of Bonds.points vs. atom xformOp:translate), fixed at the data-generation layer (`converters/xtc_to_clips.py`) with a regenerated real-data artifact, not a superficial patch. The Q-002 doc correction (`6d109e9`) was gated correctly on context7 verification per the PI's explicit condition before touching `__design__/`, and the diff text shows genuine care distinguishing Specializes-vs-base from Specializes-vs-Reference. One corner is explicitly named rather than silently cut: the `/World`-wrapper variant-cascade no-op bug found by sub-agent B is left unfixed and flagged as a Steering Question in the findings report rather than fixed or hidden — appropriate scope discipline, not corner-cutting. The one soft gap is process hygiene, not substance: there is no `cycles/cycle-004/WORKLOG.md` file (only `INBOX-consumed.md`), so the running narrative lives solely in commit messages and the findings report — sufficient to reconstruct the cycle here, but a deviation from the folder-spec's usual WORKLOG expectation.
recommended-action: proceed
```

Orchestrator adjudication: verdict accepted (aligned; proceed). The WORKLOG-absence note is resolved by
this file, written via `finish-cycle --worklog`. Outcome `open` (not proposed-resolution): reported bugs are
fixed and verified, but genuine open steering decisions remain (real-provenance wiring, the /World-cascade
latent bug) — re-proposing resolution with substantive open questions would violate the honesty contract.

## What I am uncertain about

- Play-button behavior is inferred from stage metadata + usdrecord, not an interactive GUI usdview session
  (none available in this environment) [assumption: standard usdview timeline-widget behavior].
- Harness gate-3/gate-4 thresholds are calibrated to this repo's known cases, not a broad corpus.
- Whether clip.001/002.usdc map to two distinct replica XTCs or the same file twice was not byte-verified;
  the generator supports distinct replicas and 10 real XTCs exist.
- The `/World`-cascade no-op is verified for several demos by sub-agent B but not exhaustively for all.
- provenance_metadata real-lineage wiring not done (scope) — surfaced for PI decision.
