# Parameter VariantSet (ForceField)

**Goal**: Demonstrate that a `ForceField` VariantSet models methodological force-field comparison by swapping force-field-derived parameters (partial charges, LJ radii) on atoms between AMBER and CHARMM configurations [source: `../../../../__design__/openusd_for_research_architecture.md` §2.2 Pattern C].
**Pre-conditions**:
- [ ] Element and residue templates from `foundation_demo_v8` exist and are importable (`examples/foundation_demo_v8/templates/`)
- [ ] `pxr` Python environment loadable via `load_env.sh`
**Success Gates**:
- ⬜ `examples/composition_advanced/parameter_variantset/` contains `build_forcefield.py` and `forcefield_assembly.usda`
- ⬜ With `ForceField=Amber99` atoms carry AMBER partial charges on `bio:partialCharge`; with `ForceField=Charmm36` atoms carry CHARMM values — confirmed by `usdcat --flatten`
- ⬜ `tests/composition_advanced/test_parameter_variantset.py` opens the stage fresh and asserts `bio:partialCharge` values differ between `Amber99` and `Charmm36` selections on the same atom
- ⬜ No direct `pxr` API call is made from memory — execution agent confirms VariantSet + attribute override signatures via context7 `/websites/openusd_release`
**References**: [R03 §2.2](../../../../__design__/openusd_for_research_architecture.md) — Parameter Variant pattern (ForceField, methodological comparison); [R03 §4.2](../../../../__design__/openusd_for_research_architecture.md) — Variant-Based Hypothesis Testing

## Step 1: Author parameter overlay layers for AMBER and CHARMM
**Goal**: Create two minimal USDA parameter layers that each override `bio:partialCharge` and `bio:ljRadius` on a representative subset of atoms — one layer per force field.
**Implementation Logic**:
1. Create `examples/composition_advanced/parameter_variantset/params/amber99.usda` and `params/charmm36.usda`.
2. Each is an `over`-only layer that overrides attributes on `/ABLFragment/Chain_A/Res_001/Atom_N` and `/ABLFragment/Chain_A/Res_001/Atom_CA`: `bio:partialCharge` (float, e.g., AMBER Cα = −0.0518, CHARMM Cα = −0.02) and `bio:ljRadius` (float, Bondi-derived vs CHARMM radius).
3. Values are representative but clearly distinguishable for test assertions — mark as `[assumption: representative values from AMBER99SB and CHARMM36m; not from a literal parameter file]` in a comment.
4. Each file must be parseable standalone with `usdcat`.
**Deliverables**: `examples/composition_advanced/parameter_variantset/params/amber99.usda` (overs on Atom_N and Atom_CA with `bio:partialCharge`, `bio:ljRadius`); `examples/composition_advanced/parameter_variantset/params/charmm36.usda` (same overs, different values)
**Consistency Checks**: `usdcat examples/composition_advanced/parameter_variantset/params/amber99.usda` (expected: PASS)
**Commit**: `feat(v8-gap-closure): add force-field parameter override layers for parameter_variantset`

## Step 2: Build assembly with ForceField VariantSet swapping parameter SubLayers
**Goal**: Author `forcefield_assembly.usda` — an assembly prim carrying a `ForceField` VariantSet whose variants each SubLayer the appropriate parameter override file.
**Implementation Logic**:
1. Define `/ABLFragment` as an `Xform` prim with a minimal atom hierarchy (`Chain_A/Res_001/Atom_N`, `Chain_A/Res_001/Atom_CA`) carrying default positions via local opinions.
2. Add a `ForceField` VariantSet with variants `Amber99` and `Charmm36`.
3. Inside each variant's edit context, add a SubLayer (prepend) pointing to the matching parameter file (`params/amber99.usda` or `params/charmm36.usda`). Confirm the Python API for authoring a SubLayer inside a variant edit context via context7 at execution time — SubLayers inside variants have specific scoping rules.
4. Author `bio:forceFieldName` on `/ABLFragment` as a string attribute within each variant (e.g., `"AMBER99SB-ILDN"` and `"CHARMM36m"`) as provenance metadata.
5. Set default variant to `Amber99`.
**Deliverables**: `examples/composition_advanced/parameter_variantset/build_forcefield.py` (functions: `build_forcefield_assembly`); `examples/composition_advanced/parameter_variantset/forcefield_assembly.usda` (prim `/ABLFragment` with `ForceField` VariantSet, 2 variants; `bio:forceFieldName` attribute per variant)
**Consistency Checks**: `usdcat --flatten examples/composition_advanced/parameter_variantset/forcefield_assembly.usda` (expected: PASS)
**Commit**: `feat(v8-gap-closure): build ForceField VariantSet assembly for parameter_variantset`

## Step 3: Read-back tests asserting parameter values differ per ForceField variant
**Goal**: Confirm `bio:partialCharge` on a representative atom resolves to the correct force-field value when `ForceField` is switched — testing the composed stage, not build-time memory.
**Implementation Logic**:
1. Open `forcefield_assembly.usda` with a fresh `Usd.Stage.Open(...)`.
2. For `Amber99`: query `bio:partialCharge` on `/ABLFragment/Chain_A/Res_001/Atom_CA`; assert value matches the AMBER sentinel.
3. For `Charmm36`: same path; assert value matches the CHARMM sentinel.
4. For `bio:forceFieldName` on `/ABLFragment`: assert value is `"AMBER99SB-ILDN"` under `Amber99` and `"CHARMM36m"` under `Charmm36`.
5. Assert that switching variants and re-querying returns the new value.
**Deliverables**: `tests/composition_advanced/test_parameter_variantset.py` (functions: `test_amber_partial_charge`, `test_charmm_partial_charge`, `test_forcefield_name_metadata`, `test_variant_swap_updates_charge`)
**Consistency Checks**: `python tests/composition_advanced/test_parameter_variantset.py` (expected: PASS)
**Commit**: `test(v8-gap-closure): read-back tests for parameter_variantset ForceField switching`
