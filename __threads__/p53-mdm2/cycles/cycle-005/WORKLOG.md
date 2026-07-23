# Cycle-005 WORKLOG — p53-mdm2

## Scope
Two tracks, both from the cycle-004 recommended next-decision and the PI's ack (INBOX 2026-07-23: chose **GROMACS**; acknowledged reports 07+08; "move forward with the next steps you propose").

- **Track 1 (primary): Pipeline 4 — MaBoSS → OpenUSD read-back.** Completes the 4th of 4 pipelines.
- **Track 2 (non-mutating prep): p1b Step 2 GROMACS container scaffold.** PI chose GROMACS; produced reviewable `cluster/` scaffolding only. **No cluster was touched** — every build/upload/submit stays PI-gated (Q-003) and the PI was not present in this unattended session.

## Work done (delegated to sub-agents; orchestrator integrated + independently re-verified)
- `feat 9dfadad` — `maboss/run_maboss.py`: real MaBoSS 2.6.6 run wrapper + plain-Python probtraj parser. cmaboss in-process backend found flaky (empty node columns) → distrusted; external colomoto binary used; SKIPs honestly (never fabricates) if no binary.
- `feat e056ea3` — `templates/build_analysis_layer.py` + committed `analysis/p53_mdm2_analysis.usda` + `tests/test_maboss_readback.py` (wired into `run_tests.py`); removed the superseded directional placeholder in `test_maboss_emit.py`. Time-sampled `bio:maboss:prob:<node>` on a separate analysis SubLayer; base topology untouched.
- `chore f084561` — `cluster/{gromacs.def,smoke_submit.sbatch,README.md}` (GROMACS 2025.3 / CUDA 12.9 for sm_70+sm_90; PI runbook of ordered gated steps).
- `docs 7398775` — findings report `09-cycle005_findings_v0.md` + report index README.

## Results
- **Full suite: 31/31 PASS** (was 28: −1 removed placeholder, +4 new P4 checks). Independently re-run by the orchestrator AND the verifier. usdchecker clean on the analysis stage.
- **Directional biology verified against a real run:** time-avg P(p53 up) — WT 0.310018 < L26A 0.313429 < F19A 0.322447 < **W23A 0.396226** (strict `>`, destabilization-monotone). Identical from an independent re-run and from the committed USD samples.
- All four pipelines now carry a committed, tested artifact — the topic's "done" unit is met per-pipeline; P5 integrated demo remains.

## Verifier verdict (spec-verifier, against `__roadmap__/p53_mdm2/p4_maboss_readback.md`) — VERBATIM

VERDICT: aligned

Rationale: Every named Deliverable is present and every Success Gate is met. Both scripts exist (`run_maboss.py`, `build_analysis_layer.py`), the analysis `.usda` is committed (10,114 lines, 4 variants × 5 nodes × 500 frames of time samples), and a read-back test (`test_maboss_readback.py`) is wired into the suite under group `readback-maboss-p4`. I ran the full suite myself under the forOUSD interpreter: 31/31 PASS, with all four P4 checks passing (`maboss_readback_probtraj`, `maboss_directional`, `maboss_departmental_layering`, `maboss_provenance_honesty`). The genuine-run gate is confirmed: `run_maboss.run_cfg` drives the external MaBoSS binary via `maboss.load(...).run()` (no `cmaboss=True`), `ensure_backend()` raises `MabossUnavailableError` rather than fabricating when no binary is found, and the committed engine string is the real `MaBoSS version 2.6.6`; the honest account of the flaky `cmaboss` backend is documented in the module docstring. The anti-tautology gate holds — the test builds its oracle from a FRESH independent `run_maboss.run_all()` re-run (deterministic under `seed_pseudorandom=100`, `thread_count=1`) and compares committed USD time samples against it, never against the builder's in-memory `BuildResult`. Base topology is untouched (root is an `over` with zero attributes, only a new `def Scope "maboss"` child; `git status` on `output/` is empty). The directional test is real and matches the reported values exactly (re-run and USD both: WT 0.310018 < W23A 0.396226, strict `>`), with the expectation derived independently from the ΔΔG/S ordering per R02 §Round-trip #3.

Evidence:
- Test count observed: 31/31 PASS, including `readback-maboss-p4: maboss_readback_probtraj / maboss_directional / maboss_departmental_layering / maboss_provenance_honesty`. Directional detail: rerun_p53_avg_WT=0.310018, rerun_p53_avg_W23A=0.396226, usd_p53_avg_WT=0.310018, usd_p53_avg_W23A=0.396226.
- Anti-tautology: `test_maboss_readback.py:226` builds the oracle via a fresh `run_maboss.run_all()`; `:108` sets `expected = pt.series(node)` from that re-run and `:114` compares it to the freshly-opened stage's `attr.Get(Usd.TimeCode(frame))` — the generator's in-memory state is never passed in.
- Base topology untouched: `build_analysis_layer.py:148` uses `stage.OverridePrim(root_path)`; committed `analysis/p53_mdm2_analysis.usda:16` is `over "p53_MDM2_complex"` carrying no attributes, only the analysis `def Scope "maboss"`; `test_maboss_readback.py:185` asserts the composed root carries no `bio:maboss:prob:*`. Composed atoms resolve from the SubLayer (composed_atoms: 818).

Concerns (none blocking):
- Minor transparency note (not drift): the `maboss` scope's provenance attr declares "genuine MaBoSS simulation output (not fabricated)", which is accurate about the simulation run itself. The upstream ΔΔG/S inputs driving the mutant `.cfg`s remain fixture-grounded (cycle-003), and that fixture lineage is carried honestly on the variant prims by the earlier pipelines (`fixture_honestly_tagged` / `md_fixture_honestly_tagged` pass). The P4 provenance claim is correctly scoped to the run output and does not launder the fixture inputs into "experimental" — consistent; worth a one-line mention in the report (done) but does not lower the verdict.
- The `test_maboss_emit.py` change is a clean removal of the superseded directional placeholder (now genuinely implemented in P4); no substantive coverage was lost.

## Prompt-injection watch
None observed this cycle. (Cycle-005 sub-agents returned clean; the automated background-task SYSTEM NOTIFICATIONs were standard harness events, not user input, and were not treated as approval.)

## Outcome
`open` — all four pipelines committed + tested, but P5 (integrated demo) remains, plus the PI-gated GROMACS build/smoke-submit and the later live-ddMut-PPI replacement of fixture ΔΔG. PI to review and `umbod ack p53-mdm2`.
