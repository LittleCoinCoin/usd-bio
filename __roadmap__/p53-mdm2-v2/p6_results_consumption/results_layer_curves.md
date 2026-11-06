# Results Layer — In-Stage Result Curves

**Goal**: Author a dedicated Results SubLayer, separate from an annotations-only Review layer per the PI's Q-013.2 answer (2026-09-22). It carries the MaBoSS node-probability series as renderable `UsdGeomBasisCurves`, so the result is legible in vanilla `usdview` and every curve vertex stays assertable against the Analysis layer's own time samples. Amendment of `review_layer_plots.md`, which put these curves in Review.
**Pre-conditions**:
- [ ] `analysis/p53_mdm2_analysis.usda` carries `bio:maboss:prob:<node>` time samples for four variants over frames 0..499 [source: `examples/p53_mdm2/README.md` §"The four hops" hop 4]
- [ ] `demos/p53_mdm2_integrated.usda` composes the departmental stack and owns the root-layer-only stage metadata, so the Results SubLayer is added there and nowhere else [source: `examples/p53_mdm2/demos/run_end_to_end.py` `source_layers()`, `build_integrated_stage()`]
- [ ] PI Q-013.2 answer read: Review holds annotations only, so results get their own layer [source: `__threads__/p53-mdm2/QUESTIONS.md` Q-013]
**Success Gates**:
- ⬜ `[static]` A committed `results/p53_mdm2_results.usda` exists. It SubLayers the Analysis layer, and its only `def` prims sit under a `results/` Scope. The composed stage's atom, `mdSetup`, `maboss/`, `dynamics` and `integration/` prims are unchanged by its presence
- ⬜ `[run]` Opening the Analysis layer alone resolves no `results/` Scope and no `bio:results:` attribute, matching the non-destructiveness assertion already applied to the Biology layer in `tests/test_integrated.py`
- ⬜ `[run]` A read-back check reads every vertex of every curve prim off a freshly opened composed stage, inverts the recorded axis mapping, and compares the result against the matching `bio:maboss:prob:<node>` time sample on the same stage. The observed maximum absolute difference per node is recorded in this leaf's Progress notes
- ⬜ `[run]` `usdchecker` exits 0 on the composed stage with the Results layer present, and `tests/run_tests.py` reports a total check count greater than its pre-leaf count, with zero failures
- ⬜ `[behavioral]` An attended `usdview` session on `demos/p53_mdm2_integrated.usda` is recorded, with a screenshot committed under `examples/p53_mdm2/results/evidence/`. The record states what the default camera frames and whether the curves are visible at the Ångström scale. It records what was seen and does not assert legibility
**References**: [R20 results layer + texture assets](../../../__reports__/p53-mdm2/20-results_layer_and_texture_assets_v0.md) — the placement contract, strength order and cost table; [R15 results-consumption boundary](../../../__reports__/p53-mdm2/15-results_consumption_boundary_v0.md) — the curve-geometry contract and axis-mapping invariant, which carry over with `bio:review:` renamed to `bio:results:`

## Step 1: Curve-geometry builder and committed Results layer
**Goal**: Turn the Analysis layer's time samples into renderable geometry in a separate Results SubLayer, with the plot's coordinate mapping carried on the stage so it can be inverted rather than being baked into the builder.
**Implementation Logic**:
Nothing is recomputed and no simulation is re-run. Read the series back off a composed stage, never from a builder's in-memory state. For each genotype variant, emit one linear `UsdGeomBasisCurves` per model node. Linear curves need `points`, `curveVertexCounts` and `widths`; `basis` does not apply.
The coordinate mapping is the substance of this step. The stage uses `metersPerUnit = 1e-10`, so place the plot under one `Xform` beside the complex. Record the frame range, the probability range, and the plot box's world width and height as `bio:results:` attributes on the plot Scope.
Assign per-node `primvars:displayColor`. Leave cameras and human commentary to a future Review layer, which is the department the PI reserved for annotations. A framing camera for the plots is optional and, if authored, lives in Results only because it frames results.
The Results layer SubLayers the Analysis layer so that it opens standalone, following the pattern Analysis uses with topology. It sets its own stage metadata for that standalone open, because composed metadata comes from the root layer only.
**Deliverables**: `examples/p53_mdm2/templates/build_results_layer.py` — `build_results_layer()`, `PlotAxes` dataclass with `frame_range`/`prob_range`/`plot_width`/`plot_height`, `RESULTS_SCOPE`, `RESULTS_ATTR_PREFIX`, `_curve_points()`; `examples/p53_mdm2/results/p53_mdm2_results.usda` — committed Results layer with a `results/` Scope per variant, one `BasisCurves` per node, an axis frame, and the `bio:results:frameRange`/`probRange`/`plotWidth`/`plotHeight` mapping attributes
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "from pxr import Usd, UsdGeom; s = Usd.Stage.Open('examples/p53_mdm2/results/p53_mdm2_results.usda'); c = [p for p in s.Traverse() if p.IsA(UsdGeom.BasisCurves)]; assert c, 'no BasisCurves authored'; assert all(UsdGeom.BasisCurves(p).GetTypeAttr().Get() == 'linear' for p in c)"` (expected: PASS)
**Commit**: `feat(p53-mdm2): Results layer with MaBoSS probability curves as in-stage geometry`

## Step 2: Read-back check against the Analysis time samples
**Goal**: Show that the curves are the data rather than a picture of it, by asserting each vertex against the observable it was drawn from, read off the same freshly opened stage.
**Implementation Logic**:
Open the composed stage fresh. Read the recorded axis mapping off the plot Scope, invert it per vertex, and compare against `bio:maboss:prob:<node>` at the matching time code. Import attribute names from the builder but no values, as `tests/test_integrated.py` already does.
Add the non-destructiveness half in the same module: open the Analysis layer alone and assert it carries no `results/` Scope and no `bio:results:` attribute.
Report the observed maximum absolute difference per node in the row detail, not only a pass flag. The harness has no skip concept, so return zero rows when the Results layer is absent.
**Deliverables**: `examples/p53_mdm2/tests/test_results_layer.py` — `run()` returning rows `results_curve_matches_timesamples`, `results_axis_mapping_present`, `results_absent_from_analysis_layer`; `examples/p53_mdm2/tests/run_tests.py` — new `results` layer registered
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$(pwd)/examples/p53_mdm2/tests:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import test_results_layer as t; rows = t.run(); assert rows; import sys; sys.exit(0 if all(r.passed for r in rows) else 1)"` (expected: PASS)
**Commit**: `test(p53-mdm2): results-layer curves asserted against analysis time samples`

## Step 3: Compose the Results layer and record what usdview shows
**Goal**: Put the Results layer above Analysis in the departmental stack, and capture an honest observation of the rendered result.
**Implementation Logic**:
Add the Results layer as the strongest entry of `source_layers()`, ahead of Analysis. It is derived from Analysis, as Analysis is derived from Perturbation, and a future Review layer will sit above it. The root layer keeps its existing contract: this is one list entry and no new pipeline data. Update `test_integrated.py`'s expected `bio:demo:sourceLayers` and the README's LIVERPS L row and departmental table.
Then open the composed stage in `usdview` in an attended session and record what is on screen: which camera is used by default, whether the curves are visible at the complex's scale, and whether timeline scrubbing moves anything. Do not edit `__design__/` here. Adding Results to design §4.1 is a PI decision raised by R20.
**Deliverables**: `examples/p53_mdm2/demos/run_end_to_end.py` — Results layer added to `source_layers()`; `examples/p53_mdm2/demos/p53_mdm2_integrated.usda` — regenerated; `examples/p53_mdm2/tests/test_integrated.py` — source-layer expectation updated; `examples/p53_mdm2/results/evidence/usdview_results.png` and `examples/p53_mdm2/results/evidence/usdview_results_notes.md` — the attended observation of record; `examples/p53_mdm2/README.md` — Results row added to the departmental table and LIVERPS L row
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/tests/run_tests.py` (expected: PASS)
**Commit**: `feat(p53-mdm2): compose the Results layer and record the usdview observation`
