# v8-gap-closure — Knowledge Transfer (cycle-001, v0)

Date: 2026-06-25

## Executive Summary

- **What shipped / changed:** The entire **foundation wave** of the roadmap plus the first
  gap_closure experiment, executed BFS via implementor + independent-verifier sub-agents:
  - `portability_fix` — all hard-coded ShinobuLab paths replaced by a single `USDBIO_DATA_DIR`
    contract via `examples/foundation_demo_v8/usdbio_env.py:get_data_dir()` (fails loudly when unset).
  - `roadmap_status_correction` — M1/M2/M3 in the v8 `ROADMAP/README.md` corrected to *Complete*
    with evidence links.
  - `test_harness` — a 4-layer **falsification-resistant** harness (`tests/run_tests.py`):
    layer1 `usdchecker` compliance, layer2 biological domain invariants, layer3 programmatic
    fresh-`Usd.Stage.Open` read-back, layer4 golden fixtures.
  - **Amendment A01 `baseline_artifact_fixes`** (self-discovered, self-approved) — the harness
    proved the committed baseline was *not* trustworthy; A01 fixed the defects it surfaced.
  - **Exp 1 `pointinstancer_solvent`** — 61,273 water molecules rendered via `UsdGeomPointInstancer`
    composing with the per-atom protein in a single `output/solvent_demo.usda`.
- **Primary outcomes:** Foundation wave 100% done with a **green, trustworthy baseline**
  (`run_tests.py` → **20/20 PASS, exit 0**); 1 of 5 gap_closure experiments closed; the harness
  caught and A01 remediated **4 real pre-existing artifact defects**; verifier verdict
  **minor-concern → proceed** (one prose imprecision, self-corrected).

## Wins

- **The falsification-resistant harness immediately earned its keep.** Built against the *existing*
  artifacts (as INTENT mandated), it surfaced 4 genuine defects on first run — exactly the
  tautology-resistant behavior INTENT demanded. layer3 derives assertions from source data
  (`ELEMENTS`/CPK dict, known clip samples), not generator in-memory state. Verifier independently
  confirmed it is non-tautological.
- **Sequential implementor → independent re-run → orchestrator adjudication** held a high bar: every
  leaf's success gates were re-run by the orchestrator (not trusted from the sub-agent's prose), and
  the verifier sub-agent caught a reporting imprecision the orchestrator had missed.
- **Self-driven amendment under autonomy.** A01 was raised, specced, approved, executed, and verified
  without a PI round-trip, with full audit trail (Amendment Log, gap rationale, per-step commits).

## Pain Points

- **Interpreter split (the dominant friction).** `pxr` imports *only* under the uv-managed
  CPython 3.11.14 the USD build links against; system `python3` (3.12/3.14/3.9) segfaults. `mdtraj`
  (needed to read XTC trajectories) lives *only* in miniforge3 3.12. **No single interpreter has
  both.** This blocked the `portability_fix` functional-parity gate, blocks Exp 2's clip-template
  step, and gates all future trajectory work. `load_env.sh` sets only `PYTHONPATH`, not the
  interpreter, so naive `python3 …` segfaults.
- **Sub-agents pause after the first per-step commit.** Every implementor dispatch returned control
  after one step regardless of "do all steps" instructions, forcing continuation dispatches
  (raising round-trip cost). The work landed correctly, but throughput suffered.
- **Eager mdtraj import in `converters/__init__.py`.** It re-exports `xtc_to_clips` (which
  `import mdtraj`), so `from converters.pdb_parser import …` fails under the pxr interpreter; Exp 1
  worked around it with a fragile `sys.modules` injection. Flagged as a follow-up (task_38dd255f).

## Root Causes

- The USD build was compiled against a specific uv CPython; nothing pins that interpreter for script
  execution, and `mdtraj` was never installed into it (it lives in a separate scientific stack).
- The original v8 generators never set stage metadata (`metersPerUnit`, `upAxis`, `defaultPrim`) or
  used the canonical `ballstick` token / complete element-class attributes — latent defects invisible
  until a read-back harness existed to check them.

## Next-cycle Changes

- **Instruction changes:** Always invoke USD Python via the uv interpreter
  (`/Users/hacker/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3`) after
  `. ./load_env.sh`; never plain `python3`. (Recorded in agent memory and every sub-agent prompt.)
- **Workflow changes:** Resolve the mdtraj/pxr split before scheduling the trajectory-dependent
  experiments (Exp 2 clip-template step) — see Open Questions / Q-001. Until then, prefer experiments
  that need no XTC (BasisCurves bonds, References vs SubLayers, departmental layering, PointInstancer).
- **Review process changes:** Keep the orchestrator-re-runs-every-gate discipline; it caught
  sub-agent prose drift. Continue dispatching the verifier per cycle.

## Artifacts to Preserve

- Test harness + runner: `examples/foundation_demo_v8/tests/{run_tests.py,layer1_compliance.py,layer2_domain.py,layer3_readback.py,layer4_golden.py,fixtures/}`
- Env contract: `examples/foundation_demo_v8/usdbio_env.py`; gitignored `.env` carries `USDBIO_DATA_DIR`.
- Metadata patch utility: `examples/foundation_demo_v8/tools/patch_stage_metadata.py` (idempotent).
- Exp 1 demo + artifact: `examples/foundation_demo_v8/demos/solvent_demo.py`, `output/solvent_demo.usda`, `tests/test_solvent_demo.py`.
- Roadmap state + Amendment A01 log: `__roadmap__/v8-gap-closure/README.md`.

## Open Questions

- **Q-001 (soft, posted to QUESTIONS.md): how to unblock XTC reads under the USD interpreter?**
  Options: (a) `pip install mdtraj --break-system-packages` into the uv interpreter (pollutes a
  PEP668 EXTERNALLY-MANAGED interpreter); (b) build a dedicated venv from cpython 3.11.14 with mdtraj
  + OpenUSD on `PYTHONPATH` (cleanest; needs a network install on the PI's machine — not done
  unilaterally); (c) keep them split and derive demo clips from already-committed trajectory data.
  Orchestrator leans (b). This gates Exp 2's clip-template step and future trajectory work.

## Next-cycle plan (BFS continuation)

Remaining gap_closure leaves are `planned`: `binary_clip_templates` (Exp 2 — step 3 gated on Q-001),
`departmental_layering` (Exp 3), `basiscurves_bonds` (Exp 5), `references_vs_sublayers` (Exp 6); then
the deeper `composition_advanced/` (6 arcs). INTENT frames this as multi-cycle work, so these were
intentionally left for subsequent cycles rather than rushed. Verifier confirmed this is honest.
