# Analysis Data as USD Attributes (PMF/RMSD/contacts)

**Goal**: Carry PMF, RMSD, and contact-count data as time-sampled `bio:` attributes on appropriate prims in the Analysis departmental layer, proving that derived analysis data is a first-class citizen in the usd-bio stage [source: `../../../../__design__/openusd_for_research_architecture.md` §4.1 Analysis layer; §6 ShinobuLab analysis pipeline].
**Pre-conditions**:
- [ ] Exp 3 (`departmental_layering.md`) done: 5-layer departmental stage exists with an Analysis layer (`04_analysis.usd`) that can be edited independently
- [ ] `pxr` Python environment loadable via `load_env.sh`
**Success Gates**:
- ⬜ `examples/composition_advanced/analysis_attributes/` contains `build_analysis_layer.py` and `analysis_layer.usda`
- ⬜ `usdcat --flatten analysis_layer.usda` shows `bio:rmsd`, `bio:pmf`, and `bio:contactCount` as time-sampled attributes on appropriate prims
- ⬜ `tests/composition_advanced/test_analysis_attributes.py` opens the stage fresh, samples each attribute at multiple time points, and asserts values are non-default and vary across time
- ⬜ No direct `pxr` API call is made from memory — execution agent confirms time-sampled attribute authoring API (`attr.Set(value, time=UsdTimeCode(...))`) via context7 `/websites/openusd_release`
**References**: [R03 §4.1](../../../../__design__/openusd_for_research_architecture.md) — Analysis layer in departmental stack; [R03 §6](../../../../__design__/openusd_for_research_architecture.md) — ShinobuLab analysis pipeline: RMSD, COM distance, PMF, K-means clustering outputs

## Step 1: Design analysis attribute schema and prim placement
**Goal**: Decide which prims in the ABL kinase hierarchy carry each analysis attribute, and define attribute types and time ranges — document this in comments in the build script.
**Implementation Logic**:
1. Attribute placement strategy:
   - `bio:rmsd` (float, Å): time-sampled on `/ABLComplex` root — RMSD is a whole-system or per-chain scalar, sampled at each production-MD frame (time = frame index, e.g., 0..99 for 100 sentinel frames).
   - `bio:pmf` (float, kcal/mol): time-sampled on `/ABLComplex/Analysis/PMFProfile` — PMF is a profile over a reaction coordinate; model time axis as the COM-distance bin index (0..20 for a sentinel 21-bin profile).
   - `bio:contactCount` (int): time-sampled on `/ABLComplex/Chain_A/Lig_ATP` — ligand-protein contact count per frame, same time axis as RMSD.
2. All three attributes use the `bio:` namespace for consistency with the project convention.
3. Confirm `Sdf.ValueTypeNames.Float` and `Sdf.ValueTypeNames.Int` for the above; confirm `UsdTimeCode` usage via context7.
**Deliverables**: `examples/composition_advanced/analysis_attributes/build_analysis_layer.py` (function stub `design_schema()` returning attribute specs as a dict; complete implementation in Step 2)
**Consistency Checks**: `python -c "import ast; ast.parse(open('examples/composition_advanced/analysis_attributes/build_analysis_layer.py').read())"` (expected: PASS)
**Commit**: `feat(v8-gap-closure): define analysis attribute schema for analysis_attributes experiment`

## Step 2: Author time-sampled analysis attributes in the Analysis layer
**Goal**: Populate `analysis_layer.usda` with synthetic time-sampled data for `bio:rmsd`, `bio:pmf`, and `bio:contactCount` using representative value ranges from ShinobuLab REUS outputs [assumption: RMSD range 1–5 Å, PMF range 0–10 kcal/mol, contact counts 5–20 are representative of ABL+ATP production-phase data; exact values are synthetic sentinels].
**Implementation Logic**:
1. Create a stage and define analysis prims: `/ABLComplex` (Xform), `/ABLComplex/Analysis` (Xform, scope prim for derived data), `/ABLComplex/Analysis/PMFProfile` (Xform), `/ABLComplex/Chain_A/Lig_ATP` (Xform).
2. Author `bio:rmsd` on `/ABLComplex` with 10 time samples (frames 0..9): values increasing from 1.2 to 3.8 Å (linear ramp as sentinel).
3. Author `bio:pmf` on `/ABLComplex/Analysis/PMFProfile` with 21 time samples (bins 0..20): values forming a rough Gaussian well centered at bin 10 as sentinel (peak ~0, flanks ~8 kcal/mol).
4. Author `bio:contactCount` on `/ABLComplex/Chain_A/Lig_ATP` with 10 time samples (frames 0..9): integer values 12, 11, 13, 10, 14, 11, 12, 9, 13, 12.
5. Use `attr.Set(value, time=Usd.TimeCode(t))` — confirm exact call via context7. Set stage start/end time codes to match the time ranges.
**Deliverables**: `examples/composition_advanced/analysis_attributes/build_analysis_layer.py` (functions: `build_analysis_layer`); `examples/composition_advanced/analysis_attributes/analysis_layer.usda` (time-sampled `bio:rmsd`, `bio:pmf`, `bio:contactCount`)
**Consistency Checks**: `usdcat --flatten examples/composition_advanced/analysis_attributes/analysis_layer.usda` (expected: PASS)
**Commit**: `feat(v8-gap-closure): author time-sampled bio: analysis attributes in analysis_layer.usda`

## Step 3: Read-back tests sampling attributes at multiple time points
**Goal**: Open the analysis stage fresh and assert each attribute returns the correct value at multiple time codes, confirming time-sampling is baked into the layer and not reliant on build-time state.
**Implementation Logic**:
1. Open `analysis_layer.usda` with a fresh `Usd.Stage.Open(...)`.
2. For `bio:rmsd` on `/ABLComplex`: sample at `UsdTimeCode(0)` (expect ~1.2), `UsdTimeCode(4)` (expect ~2.7), `UsdTimeCode(9)` (expect ~3.8); assert within 0.01 Å tolerance.
3. For `bio:pmf` on `/ABLComplex/Analysis/PMFProfile`: sample at `UsdTimeCode(10)` (expect ~0.0 kcal/mol, well minimum), `UsdTimeCode(0)` (expect ~8.0 kcal/mol, high flank).
4. For `bio:contactCount` on `/ABLComplex/Chain_A/Lig_ATP`: sample at `UsdTimeCode(0)` (expect 12), `UsdTimeCode(7)` (expect 9).
5. Assert that sampling at a time outside the authored range returns the held-last-value (default USD behavior) — confirms time-code boundary semantics are understood.
**Deliverables**: `tests/composition_advanced/test_analysis_attributes.py` (functions: `test_rmsd_time_samples`, `test_pmf_time_samples`, `test_contact_count_time_samples`, `test_boundary_time_code_behavior`)
**Consistency Checks**: `python tests/composition_advanced/test_analysis_attributes.py` (expected: PASS)
**Commit**: `test(v8-gap-closure): read-back tests for analysis_attributes time-sampled bio: data`
