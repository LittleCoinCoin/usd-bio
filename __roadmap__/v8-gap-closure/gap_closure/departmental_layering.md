# Exp 3 — Departmental Layering (5-layer)

**Goal**: Build a 5-layer stage for ABL kinase (Biology / Protocol / Dynamics / Analysis / Review) where each layer is an independently editable SubLayer, and verify that toggling any single layer on or off leaves the remaining layers composing without error.
**Pre-conditions**:
- [ ] `portability_fix` leaf complete: all scripts read paths from `USDBIO_DATA_DIR`
- [ ] `test_harness` leaf complete: harness runner exists and passes against existing v8 artifacts
- [ ] `output/clips/trajectory_clip.usda` (or `.usdc`) exists from the v8 foundation or `binary_clip_templates` leaf
- [ ] `assets/level4_assemblies/abl_kinase_complex.usda` exists
- [ ] OpenUSD `pxr` environment available via `load_env.sh`
**Success Gates**:
- ⬜ Five separate layer files exist: `biology.usda`, `protocol.usda`, `dynamics.usda`, `analysis.usda`, `review.usda` under `assets/level6_departmental/`
- ⬜ Root stage `output/departmental_demo.usda` SubLayers all five; `stage.Traverse()` finds prims contributed by each layer
- ⬜ Mute-and-check: muting any single sublayer leaves the stage valid (`stage.GetErrors()` returns an empty list)
- ⬜ Analysis layer contributes a time-sampled `bio:rmsd` attribute on `/ABLComplex` (float, ≥ 20 time samples)
- ⬜ Read-back test passes: `tests/test_departmental_layering.py` opens `departmental_demo.usda` and asserts all gates above
**References**: [R02 §5](../../../__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md) — Experiment 3 deliverable: 5-layer stage (biology, protocol, dynamics, analysis, review) for ABL kinase; test toggling layers on/off

## Step 1: Author the five individual department layers
**Goal**: Create five minimal-but-meaningful `.usda` layer files under `assets/level6_departmental/`, each contributing distinct, non-overlapping content to the `/ABLComplex` namespace.
**Implementation Logic**:
1. **biology.usda**: SubLayer `../../assets/level4_assemblies/abl_kinase_complex.usda`. This is the topology layer — chain/residue/atom hierarchy, `bio:` metadata, element class inheritance, `representation` VariantSet. It is the base layer all others build on.
2. **protocol.usda**: Defines `/ABLComplex/ProtocolMetadata` Xform with custom attributes: `bio:solventModel = "TIP3P"` (token), `bio:boxDimensions = (75.0, 75.0, 75.0)` (float3), `bio:ionCount = 42` (int), `bio:equilibrationNs = 2.5` (float). [assumption: ShinobuLab box dimensions not verified from PDB CRYST1 here; execution agent should replace with values from the CRYST1 record if available]
3. **dynamics.usda**: Applies Value Clips to `/ABLComplex` via `UsdClipsAPI`, pointing to `../../output/clips/trajectory_clip.usda`. WHY a separate dynamics layer: allows removing trajectory data without affecting topology or analysis.
4. **analysis.usda**: Defines time-sampled float attribute `bio:rmsd` on `/ABLComplex` with 20 synthetic samples (values ≈ 1.0–3.0 Å at frames 0–19). WHY synthetic: validates USD composition pattern without requiring a live analysis pipeline; real values substituted when MDAnalysis data is available.
5. **review.usda**: Defines `UsdGeomCamera` at `/ABLComplex/ReviewCamera` and annotation Xform `/ABLComplex/ATPAnnotation` with `bio:annotationText = "ATP binding site"`. Each layer opens cleanly on its own; prims added to `/ABLComplex` by protocol/analysis/review are over-opinions that resolve only when composed.
**Deliverables**: `examples/foundation_demo_v8/assets/level6_departmental/biology.usda`, `protocol.usda`, `dynamics.usda`, `analysis.usda`, `review.usda` — five committed layer artifacts; a Python script `templates/09_create_departmental_layers.py` with `create_all_layers(layer_dir: str)` and `__main__` that generates all five
**Consistency Checks**: `source load_env.sh && python3 templates/09_create_departmental_layers.py && python3 -c "from pxr import Usd; layers=['biology','protocol','dynamics','analysis','review']; [Usd.Stage.Open(f'assets/level6_departmental/{l}.usda') for l in layers]; print('PASS')"` (expected: PASS)
**Commit**: `feat(v8-gap-closure): author 5 departmental layers for ABL kinase stage`

## Step 2: Compose the root departmental demo stage
**Goal**: Create `demos/departmental_demo.py` that SubLayers all five department layers into a single root stage and verifies clean composition.
**Implementation Logic**:
1. Create `output/departmental_demo.usda`; add all five layers as `subLayerPaths` in order: biology → protocol → dynamics → analysis → review (review opinions are strongest, biology topology weakest).
2. Set `/ABLComplex` as default prim; set timeline to match the dynamics layer frame range.
3. Call `stage.GetErrors()` and assert it is empty.
4. Print summary: prim count from `stage.Traverse()`, sublayer count, attribute count on `/ABLComplex`, whether `bio:rmsd` is time-sampled.
5. USD paths are repo-relative; `USDBIO_DATA_DIR` is used only for the underlying PDB/XTC in upstream layers.
**Deliverables**: `examples/foundation_demo_v8/demos/departmental_demo.py` — `create_departmental_stage(output_path: str, layer_dir: str)` and `verify_departmental_stage(output_path: str)` with `__main__`; `examples/foundation_demo_v8/output/departmental_demo.usda` — committed root stage artifact
**Consistency Checks**: `source load_env.sh && python3 demos/departmental_demo.py` (expected: PASS)
**Commit**: `feat(v8-gap-closure): compose 5-layer departmental demo stage for ABL kinase`

## Step 3: Mute-toggle test
**Goal**: Add `demos/departmental_mute_test.py` that iteratively mutes each of the five sublayers and confirms the stage remains valid after each mute.
**Implementation Logic**:
1. Open `output/departmental_demo.usda` with `Usd.Stage.Open()`.
2. Retrieve the five sublayer identifiers from `stage.GetRootLayer().subLayerPaths`.
3. For each sublayer path: call `stage.MuteLayer(path)`, call `stage.GetErrors()`, assert the result is empty, call `stage.UnmuteLayer(path)`. Confirm `MuteLayer`/`UnmuteLayer` API via context7 at execution time.
4. Print `PASS: muted <layer>, stage valid` for each. WHY one-at-a-time mute/check/unmute: tests "does toggling one layer break composition?" in isolation — cumulative muting would conflate multiple causes.
**Deliverables**: `examples/foundation_demo_v8/demos/departmental_mute_test.py` — `test_mute_toggle(stage_path: str)` with `__main__`
**Consistency Checks**: `source load_env.sh && python3 demos/departmental_mute_test.py` (expected: PASS)
**Commit**: `feat(v8-gap-closure): mute-toggle test confirms each departmental layer is independently removable`

## Step 4: Read-back tests
**Goal**: Add `tests/test_departmental_layering.py` that opens `output/departmental_demo.usda` as a cold consumer and asserts all structural and compositional invariants.
**Implementation Logic**:
1. Open `output/departmental_demo.usda` via `Usd.Stage.Open()` — no generator code in scope.
2. Assert `stage.GetErrors()` is empty; assert five sublayer paths in `stage.GetRootLayer().subLayerPaths`.
3. Assert `/ABLComplex/ProtocolMetadata` exists with attribute `bio:solventModel`.
4. Assert `/ABLComplex` has attribute `bio:rmsd` with ≥ 20 time samples via `attr.GetTimeSamples()`.
5. Assert `/ABLComplex/ReviewCamera` is a `UsdGeomCamera` prim; assert `UsdClipsAPI(stage.GetPrimAtPath('/ABLComplex')).GetClipAssetPaths()` is non-empty.
6. Assert `representation` VariantSet exists on `/ABLComplex`. WHY read-back: ensures the written file is independently correct, not just consistent with in-memory generator state.
**Deliverables**: `examples/foundation_demo_v8/tests/test_departmental_layering.py` — `test_no_composition_errors()`, `test_sublayer_count()`, `test_protocol_metadata()`, `test_analysis_rmsd()`, `test_review_camera()`, `test_dynamics_clips()`, `test_representation_variantset()`, and `__main__` runner
**Consistency Checks**: `source load_env.sh && python3 tests/test_departmental_layering.py` (expected: PASS)
**Commit**: `test(v8-gap-closure): read-back tests for 5-layer departmental composition`
