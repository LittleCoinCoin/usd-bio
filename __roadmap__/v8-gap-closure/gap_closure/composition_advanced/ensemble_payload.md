# Exp 4 — Ensemble VariantSet + Payload Swapping

**Goal**: Demonstrate that a `ReplicaID` VariantSet swapping Payload references to different trajectory clip files correctly models REUS replica ensembles in USD [source: `../../../../__design__/openusd_for_research_architecture.md` §2.2 Pattern A].
**Pre-conditions**:
- [ ] Exp 2 (`binary_clip_templates.md`) done: clip template pattern (topology USDC + per-replica clip files) exists and is consumable
- [ ] Exp 3 (`departmental_layering.md`) done: 5-layer stage with Dynamics layer exists as a consumable base assembly
- [ ] `USDBIO_DATA_DIR` env var points to ShinobuLab REUS pull directories (`rep_01/` … `rep_50/`)
- [ ] `pxr` Python environment loadable via `load_env.sh`
**Success Gates**:
- ⬜ `examples/composition_advanced/ensemble_payload/` contains `build_ensemble.py`, `ensemble_assembly.usda`, and at least 3 synthetic clip stubs
- ⬜ Running `usdcat --flatten ensemble_assembly.usda` with `ReplicaID=rep_01` shows that assembly's Dynamics sublayer payload pointing to `rep_01` clip file; same test for `rep_02` shows a different path
- ⬜ `tests/composition_advanced/test_ensemble_payload.py` opens the stage fresh (no generator state), switches `ReplicaID` variants, and asserts composed payload asset path per variant (not build-time values)
- ⬜ No direct `pxr` API call is made from memory — execution agent confirms signatures against context7 `/websites/openusd_release` before authoring
**References**: [R03 §2.2](../../../../__design__/openusd_for_research_architecture.md) — Ensemble Variant pattern (ReplicaID, Payload swapping, REUS mapping); [R03 §6](../../../../__design__/openusd_for_research_architecture.md) — ShinobuLab replica directory structure

## Step 1: Scaffold synthetic replica clip stubs
**Goal**: Create 3–5 minimal USDC/USDA clip files that stand in for real REUS trajectory clips so the build script is testable without the full dataset.
**Implementation Logic**:
1. Under `examples/composition_advanced/ensemble_payload/clips/`, generate `rep_01.usda`, `rep_02.usda`, `rep_03.usda` — each a minimal Value Clips layer containing a single time-sampled `points` attribute on `/ABLComplex/Chain_A/Res_001/Atom_CA` with distinct sentinel values (e.g., `(1.0, 0.0, 0.0)` for rep_01, `(2.0, 0.0, 0.0)` for rep_02).
2. Each clip file must be parseable standalone by `usdcat` — no external references.
3. Confirm exact `UsdClipsAPI` attribute names (`primvars:skel:jointIndices` vs `points`) and clip metadata keys (`clipActive`, `clipTimes`, `clipAssetPaths`, `clipManifestAssetPath`) via context7 `/websites/openusd_release` at execution time.
**Deliverables**: `examples/composition_advanced/ensemble_payload/clips/rep_01.usda`, `rep_02.usda`, `rep_03.usda` (each containing a `points` time sample)
**Consistency Checks**: `usdcat examples/composition_advanced/ensemble_payload/clips/rep_01.usda` (expected: PASS)
**Commit**: `feat(v8-gap-closure): add synthetic REUS clip stubs for ensemble_payload experiment`

## Step 2: Build assembly with ReplicaID VariantSet + Payload swapping
**Goal**: Author `ensemble_assembly.usda` via `build_ensemble.py` — an assembly prim that carries a `ReplicaID` VariantSet whose variants each add a Payload referencing the corresponding clip stub.
**Implementation Logic**:
1. Define `/ABLEnsemble` as an `Xform` prim that SubLayers the departmental-layering stage from Exp 3 for its Biology + Protocol base.
2. Add a `ReplicaID` VariantSet with variants `rep_01`, `rep_02`, `rep_03`.
3. Inside each variant's edit context, author a Payload arc on `/ABLEnsemble` pointing to the matching clip file (e.g., `clips/rep_01.usda`). Confirm the Python call for adding a payload inside a variant edit context (`variantSet.SetVariantSelection(name)` + `with variantSet.GetVariantEditContext():` + `prim.GetPayloads().AddPayload(...)`) via context7 at execution time — do not guess the exact signature.
4. Set default variant to `rep_01`.
5. Save as `ensemble_assembly.usda`.
**Deliverables**: `examples/composition_advanced/ensemble_payload/build_ensemble.py` (functions: `build_replica_clips`, `build_ensemble_assembly`); `examples/composition_advanced/ensemble_payload/ensemble_assembly.usda` (prim `/ABLEnsemble` with `ReplicaID` VariantSet, 3 variants, each with a Payload)
**Consistency Checks**: `usdcat --flatten examples/composition_advanced/ensemble_payload/ensemble_assembly.usda` (expected: PASS)
**Commit**: `feat(v8-gap-closure): build ReplicaID VariantSet + Payload assembly for ensemble_payload`

## Step 3: Read-back tests asserting composed payload paths per variant
**Goal**: Verify the composed Payload asset path changes when the `ReplicaID` variant is switched — testing the stage's resolved state, not the build script's in-memory state.
**Implementation Logic**:
1. Open `ensemble_assembly.usda` with a fresh `Usd.Stage.Open(...)` call (not reusing the build stage).
2. For each replica variant (`rep_01`, `rep_02`, `rep_03`):
   a. Set `ReplicaID` variant on `/ABLEnsemble` via `prim.GetVariantSet("ReplicaID").SetVariantSelection(variant)`.
   b. Load the Payload (call `stage.LoadAndUnload(Usd.StageLoadRules.LoadAll(), ...)` or equivalent) — confirm exact API via context7.
   c. Assert the composed `points` time sample at time=1.0 matches the sentinel value for that replica (e.g., `(1.0, 0.0, 0.0)` for `rep_01`).
3. Assert switching variants updates the sampled value — this proves Payload swapping works at composition level, not just at authoring level.
**Deliverables**: `tests/composition_advanced/test_ensemble_payload.py` (functions: `test_variant_swaps_payload_path`, `test_sentinel_positions_per_replica`)
**Consistency Checks**: `python tests/composition_advanced/test_ensemble_payload.py` (expected: PASS)
**Commit**: `test(v8-gap-closure): read-back tests for ensemble_payload ReplicaID variant switching`
