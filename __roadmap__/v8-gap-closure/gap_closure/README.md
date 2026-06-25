# Gap Closure — §5 Experiments + §3 Arcs

## Context
The gap-closure work proper. Runs **after** the campaign's foundation leaves (`portability_fix`, `test_harness`, `roadmap_status_correction`) because BFS executes a directory's leaf siblings before its subdirectories. The five leaves here are mutually independent §5 experiments executable in parallel; the `composition_advanced/` subdirectory holds arcs that depend on the layering and clip-template outputs produced here, so it is one level deeper. Each leaf produces a runnable demo + committed `.usda` + read-back tests using the harness from the foundation wave.

## Reference Documents
- [R01 cycle-000 audit + roadmap](../../../__reports__/v8-gap-closure/00-audit_and_roadmap_v0.md) — refreshed gap status
- [R02 v8→production perspective §5](../../../__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md) — experiment deliverables

## Goal
Close the §5 experiments that have no cross-dependency (Exp 1, 2, 3, 5, 6), establishing the scale, layering, and bond strategies the advanced arcs build on.

## Pre-conditions
- [ ] Foundation wave done: test harness exists and passes against existing artifacts; converters run without hard-coded paths
- [ ] `pxr` environment available for demos/tests

## Success Gates
- ✅ Exp 1 (PointInstancer solvent), Exp 2 (binary + clip templates), Exp 3 (5-layer departmental), Exp 5 (BasisCurves bonds), Exp 6 (References vs SubLayers) each closed with demo + artifact + read-back tests
- ✅ Clip-template and 5-layer outputs exist for `composition_advanced/` to consume

## Status
```mermaid
graph TD
    binary_clip_templates[Exp 2 — Binary Format + Clip Templates]:::done
    pointinstancer_solvent[Exp 1 — PointInstancer for Solvent]:::done
    departmental_layering[Exp 3 — Departmental Layering (5-layer)]:::planned
    basiscurves_bonds[Exp 5 — BasisCurves for Bonds]:::planned
    references_vs_sublayers[Exp 6 — References vs SubLayers]:::planned
    composition_advanced[Advanced Composition Arcs (depend on layering + clip templates)]:::planned
    classDef done       fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned    fill:#374151,color:#e5e7eb
    classDef amendment  fill:#1e3a5f,color:#bfdbfe
    classDef blocked    fill:#7f1d1d,color:#fecaca
```

## Nodes
| Node | Type | Status |
|:-----|:-----|:-------|
| `binary_clip_templates.md` | 📄 Leaf Task | ✅ Done |
| `pointinstancer_solvent.md` | 📄 Leaf Task | ✅ Done |
| `departmental_layering.md` | 📄 Leaf Task | ⬜ Planned |
| `basiscurves_bonds.md` | 📄 Leaf Task | ⬜ Planned |
| `references_vs_sublayers.md` | 📄 Leaf Task | ⬜ Planned |
| `composition_advanced/` | 📁 Directory | ⬜ Planned |

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
| `binary_clip_templates.md` | topic/v8-gap-closure | 0b0ea9c, 1ca31d2, ab90b65, 77360f7 | Exp 2 done (cycle-002, under forOUSD): .usda→.usdc (assembly 95.8% smaller, clip 63% smaller); load 2.6–6.1× faster; clip-template manifest (`./clip_###.usdc`, stride 10) from 2 real XTC files; read-back test 5/5; harness 24/24. Confirms NO interpreter split — XTC reads work under forOUSD venv. |
| `pointinstancer_solvent.md` | topic/v8-gap-closure | 970d7d5, b12ef63, b7c6df8, a636332 | Exp 1 done: 61,273 waters via UsdGeomPointInstancer composing with per-atom protein in solvent_demo.usda. Two test surfaces: standalone `tests/test_solvent_demo.py` 4/4 PASS (PointInstancer-specific read-back), and the existing `tests/run_tests.py` harness 20/20 PASS (solvent_demo.usda now swept by compliance+domain layers; the 4 solvent read-back tests are NOT part of that 20/20 — they run separately). No mdtraj needed (PDB-only). NOTE (cycle-001 correction): the implementor hit a missing-mdtraj error only because it ran the bare uv python; under the canonical `forOUSD` venv (which has mdtraj) `converters/__init__.py` imports cleanly, so the sys.modules workaround is unnecessary — guarding the import remains a minor robustness nice-to-have, not a blocker. |
