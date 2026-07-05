# Reports — v8-gap-closure

Reports for the `v8-gap-closure` topic, grouped by round (chronological).

## Round 00 — 2026-06-25 (cycle-000, scoping)

- [`00-audit_and_roadmap_v0.md`](00-audit_and_roadmap_v0.md) — refreshed gap audit (§3 + §5 against current code) + dependency-ordered roadmap rationale. `decision-required: confirm` (confirmed by PI via INBOX).

## Round 01 — 2026-06-25 (cycle-001, foundation execution)

- [`01-knowledge_transfer_v0.md`](01-knowledge_transfer_v0.md) — post-cycle retrospective: foundation wave + Amendment A01 + Exp 1 shipped; harness 20/20. (Top-of-file CORRECTION: the mdtraj/pxr "interpreter split" / Q-001 was a false premise — the forOUSD venv has both; retracted.)

## Round 02 — 2026-06-25 (cycle-002, full roadmap completion)

- [`02-knowledge_transfer_v0.md`](02-knowledge_transfer_v0.md) — entire remaining roadmap executed: gap_closure Exp 2/3/5/6 + all 6 composition_advanced arcs. 15/15 leaves done; harness 30/30; verifier aligned. Topic → proposed-resolution. Records the major finding that the architecture doc's Specializes claim is backwards.

## Round 03 — 2026-07-04 (cycle-003, independent re-verification)

- [`03-findings_v0.md`](03-findings_v0.md) — **latest** — independent fresh-process re-run of all committed test evidence under `forOUSD`: main harness 30/30 + composition_advanced 37/37 = **67/67 green**, all exit 0. Roadmap-status truthfulness audit: all 15 leaves backed by demo + `.usda` + read-back tests. Falsification-resistance spot-checked on 3 suites (non-tautological). The cycle-002 "ensemble t=2.4 offset" uncertainty does **not** reproduce — resolved. `decision-required: confirm`.

## Round 04 — 2026-07-06 (cycle-004, broken-usdview-output response)

- [`04-findings_v0.md`](04-findings_v0.md) — **latest** — response to the PI's 4 INBOX bug reports about broken usdview output. Findings: `output/clips/*` are intended intermediate value-clip payloads (grey/static only if opened directly — documentation gap, not a bug); `curves_demo.usda` was a genuine two-cause bug (no default variant selection + clip drove only bonds, not atoms) — **fixed** and independently verified (atoms now clip-driven, 19.3 Å motion, co-located with bonds). Built the PI-requested headless regression harness `tests/usdview_regression_check.py` (6 gates), which surfaced + fixed the same defect class in 3 unreported demos. Q-002: Specializes doc claim corrected (context7-verified, PI direction (b)); trajectory clip provenance confirmed real ShinobuLab data (both `.usda` and `.usdc`); `provenance_metadata` uses placeholder values (`2HYY.pdb` is wrong; real is `atp-complex-solv35.pdb`). `decision-required: confirm`.

## Status

**Reported usdview bugs fixed; regression net stood up.** Cycle-004 dispositioned all 4 INBOX items:
clips documented (intended payloads), `curves_demo` genuinely fixed, headless `usdview_regression_check.py`
built (green baseline: 44 pass / 0 fail / 1 allow-listed residual) and applied to existing artifacts —
catching 3 more latent variant-selection defects, all fixed. Architecture-doc Specializes correction landed
(context7-verified, PI-authorized). Open for PI confirm: (a) real-provenance wiring for live-meeting demos;
(b) whether to fix the latent `/World`-cascade no-op across demos. Prior status below.

---

**Roadmap complete (15/15 ✅) and independently re-verified.** Cycle-002 closed the remaining gap_closure experiments and all composition_advanced arcs under the `forOUSD` interpreter; cycle-003 independently re-ran every committed test suite from a fresh process (67/67 green) and confirmed roadmap statuses are truthful. Architecture-doc parity achieved for the in-scope §3 gaps + §5 experiments. Topic remains **proposed-resolution** for PI confirm-and-close. Out of scope (future topics): C++/schema authoring, p53-mdm2 application. Open steering question for PI: correct architecture doc R03 §2.1/§7 Specializes claim (it is backwards) — a `__design__/` edit currently out of INTENT scope, so surfaced not done.
