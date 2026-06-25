# Cycle 001 WORKLOG — v8-gap-closure

## Situation (from manifest)

Second cycle. STATUS `pi-reviewed` → `active` (wake projection). PI reviewed cycle-000's
roadmap and, via INBOX, (1) agreed with the roadmap content, (2) confirmed the
`USDBIO_DATA_DIR` env-var data contract in a gitignored `.env`, and (3) pointed at the
ShinobuLab test data location. QUESTIONS empty at start. The PI also intervened mid-cycle
to direct: drive the whole roadmap forward (not just foundation), with full autonomy,
escalating only on a blatant mistake or critical gap.

## Plan (decide step)

Execute the roadmap BFS via implementor + verifier sub-agents (Sonnet for workers per INTENT;
Opus orchestrator for synthesis/adjudication). Foundation level first (its leaves precede the
gap_closure subdirectory), then gap_closure experiments. Manage roadmap status with `dirtree-rdm`
(orchestrator-owned; not `--roadmap-refs`, to avoid double-mutation). Commit per step. Run every
success gate independently as orchestrator (rigor tie-breaker). Dispatch the verifier before
finish-cycle.

## Work done

- **INBOX-ack** (commit `3ec5f78`): consumed the PI agreement/data-contract item. Action: wrote
  `USDBIO_DATA_DIR` into the gitignored `.env` (verified `.gitignore:421` excludes `.env`).
- **Environment discovery (load-bearing):** `pxr` imports ONLY under the uv-managed CPython 3.11.14
  the USD build links (`/Users/hacker/.local/share/uv/.../cpython-3.11.14-.../bin/python3`); system
  `python3` segfaults. `load_env.sh` sets only `PYTHONPATH`. Recorded to agent memory.
- **`portability_fix`** (done; `71f2b3a`,`416b444`,`21985b2`,`a11cb02`): `usdbio_env.get_data_dir()`
  + de-hardcoded 3 scripts + ROADMAP README. Gates 1–3 PASS (independently re-verified: 0 expanduser,
  0 career/Projects in .py, loud-fail message). Gate 4 (functional parity) BLOCKED — mdtraj (py3.12)
  and pxr (uv py3.11) share no interpreter.
- **`roadmap_status_correction`** (done; `603142f`): M1/M2/M3 → Complete w/ evidence; 0 In Progress/Blocked.
- **`test_harness`** (done; `e0b93c7`,`4698806`,`c27f7a8`,`000feae`): 4-layer falsification-resistant
  harness. First run against existing artifacts FAILED compliance (6/6) + domain (1/6) — surfacing
  REAL baseline defects, not harness bugs (exit codes verified: compliance=1, domain=1, readback=0,
  golden=0). readback layer (the core) opens artifacts fresh and asserts against source data.
- **Amendment A01 `baseline_artifact_fixes`** (self-discovered, self-approved; done;
  `5e90cf1`,`a6a4fce`,`b47b75c`): fixed the defects the harness caught — `metersPerUnit`+`upAxis` in
  all 5 generators; `sticks`→`ballstick` token + `/_class_/H` `bio:cpkColor`; regenerated 4
  non-trajectory artifacts + idempotent `tools/patch_stage_metadata.py` for the 2 mdtraj-blocked
  trajectory artifacts; also fixed a 4th defect surfaced en route (`trajectory_clip` missing
  `defaultPrim`). Harness then **18/18 PASS** (independently re-run, exit 0). Logged in Amendment Log.
- **gap_closure Exp 1 `pointinstancer_solvent`** (done; `970d7d5`,`b12ef63`,`b7c6df8`,`a636332`):
  61,273 waters via `UsdGeomPointInstancer` composing with the per-atom protein in
  `output/solvent_demo.usda`. Standalone read-back test 4/4; full harness now **20/20 PASS**
  (independently re-run, instancer valid, 61273 positions). FINDING: `converters/__init__.py` eagerly
  imports mdtraj via `xtc_to_clips`, broke clean imports under pxr; worked around with sys.modules
  injection → flagged as follow-up task_38dd255f.
- **Steering question Q-001** (soft, `wkas ask`): how to unblock XTC reads under the USD interpreter
  (mdtraj/pxr split). Non-trajectory experiments proceed regardless.
- **Roadmap bookkeeping** (`d564f84`, gap_closure progress commits, verifier self-correction): statuses
  marked done via `dirtree-rdm`, Amendment Log + Progress tables populated, all `dirtree-rdm validate` OK.

## Verifier verdict (cycle-001, verbatim)

```
verdict: minor-concern
inbox-coverage:
  - PI agreement on roadmap sequencing + USDBIO_DATA_DIR env-var contract → examples/foundation_demo_v8/usdbio_env.py (get_data_dir() raises actionable EnvironmentError when unset); .gitignore line 421 confirms .env already excluded; no separate artifact created for the .env guidance but the contract is implemented
intent-tracking: aligned
work-depth: The cycle's stated commitments — foundation wave (portability_fix, roadmap_status_correction, test_harness), Amendment A01 (baseline_artifact_fixes), and Exp 1 (pointinstancer_solvent) — are each backed by concrete artifacts with specific commit hashes recorded in the roadmap Progress table. The falsification-resistant harness claim holds: layer3_readback.py derives all assertions from source data (the ELEMENTS dict and hard-coded known clip-sample values from the committed .usda, not generator in-memory state), and opens files with a fresh Usd.Stage.Open() call. The 20/20 count is internally consistent: solvent_demo.usda was added post-test_harness, raising the compliance and domain sweep from 6→7 files each (7+7+3+3=20). One minor imprecision: the progress note for pointinstancer_solvent claims "read-back test + harness 20/20 PASS" but the four solvent-specific read-back tests live in the standalone test_solvent_demo.py, which is NOT integrated into run_tests.py — so the main harness does not execute those four assertions. The "read-back test" parenthetical is technically accurate (it does run separately) but could mislead a reader into thinking solvent read-back is covered by the 20/20 count. The remaining gap_closure leaves marked planned is honest: INTENT.md explicitly frames this as multi-cycle work, the roadmap's BFS ordering is clear, and the blocking constraint (mdtraj/pxr interpreter split) is named in QUESTIONS.md Q-001 and in the portability_fix Progress notes. No fabricated progress detected.
recommended-action: proceed
```

Orchestrator adjudication: verdict accepted (minor-concern → proceed). Self-corrected the flagged
prose imprecision in the gap_closure Progress note (commit clarifying the two test surfaces). Outcome
`open` — foundation is complete and the baseline is green/trustworthy, but the topic is not resolved:
4 gap_closure experiments + 6 composition_advanced arcs remain.

## What I am uncertain about

- **mdtraj/pxr interpreter split (Q-001).** Gates Exp 2's clip-template step and future trajectory
  work. I did not install mdtraj unilaterally (the USD interpreter is PEP668 EXTERNALLY-MANAGED; a
  network install on the PI's machine is a side effect I left to PI direction).
- **`metersPerUnit = 1e-10` choice.** Ångström-correct, applied uniformly; if the PI prefers a
  different convention (e.g. nm or unit-1.0-with-documented-scale) it is a one-line change in the
  generators + a re-patch.
- **`converters/__init__.py` mdtraj-eager-import** workaround is fragile; clean fix flagged
  (task_38dd255f), not done in-cycle to keep scope bounded.
