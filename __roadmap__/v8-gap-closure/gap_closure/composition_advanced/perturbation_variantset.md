# Perturbation VariantSet (Genotype)

**Goal**: Demonstrate that a `Genotype` VariantSet models in-silico mutagenesis by swapping a mutation-site residue's atom geometry between wild-type and point-mutant configurations [source: `../../../../__design__/openusd_for_research_architecture.md` §2.2 Pattern B].
**Pre-conditions**:
- [ ] Element and residue templates from `foundation_demo_v8` exist and are importable (`examples/foundation_demo_v8/templates/`)
- [ ] `pxr` Python environment loadable via `load_env.sh`
**Success Gates**:
- ⬜ `examples/composition_advanced/perturbation_variantset/` contains `build_genotype.py` and `genotype_assembly.usda`
- ⬜ With `Genotype=WildType` the mutation-site residue's sidechain atom carries wild-type position data; with `Genotype=T315I` it carries mutant-residue geometry — confirmed by `usdcat --flatten`
- ⬜ `tests/composition_advanced/test_perturbation_variantset.py` opens the stage fresh and asserts the mutation-site atom position differs between `WildType` and `T315I` selections
- ⬜ No direct `pxr` API call is made from memory — execution agent confirms VariantSet authoring signatures via context7 `/websites/openusd_release`
**References**: [R03 §2.2](../../../../__design__/openusd_for_research_architecture.md) — Perturbation Variant pattern (Genotype, mutagenesis mapping); [R03 §4.2](../../../../__design__/openusd_for_research_architecture.md) — Variant-Based Hypothesis Testing

## Step 1: Author minimal mutation-site geometry for wild-type and T315I
**Goal**: Define the two residue geometry variants that the `Genotype` VariantSet will swap — threonine (Thr-315, wild-type) vs isoleucine (Ile-315, T315I mutant).
**Implementation Logic**:
1. Create two minimal USDA files in `examples/composition_advanced/perturbation_variantset/geometries/`: `res315_wt.usda` (Thr-315 with representative Cβ/Oγ1 atoms and positions, `bio:residueName = "THR"`) and `res315_t315i.usda` (Ile-315 with Cβ/Cγ1/Cγ2 atoms and positions, `bio:residueName = "ILE"`).
2. Both files reference the element class templates from Exp 1 for element-level properties (radius, color) via SubLayers — avoid duplicating element properties inline.
3. Atom positions should be distinct sentinel values (e.g., Thr Oγ1 at `(5.0, 0.0, 0.0)`, Ile Cγ1 at `(6.0, 0.0, 0.0)`) to make test assertions unambiguous.
**Deliverables**: `examples/composition_advanced/perturbation_variantset/geometries/res315_wt.usda` (prim `/Res315/Atom_OG1`, `bio:residueName = "THR"`); `examples/composition_advanced/perturbation_variantset/geometries/res315_t315i.usda` (prim `/Res315/Atom_CG1`, `bio:residueName = "ILE"`)
**Consistency Checks**: `usdcat examples/composition_advanced/perturbation_variantset/geometries/res315_wt.usda` (expected: PASS)
**Commit**: `feat(v8-gap-closure): add mutation-site residue geometry stubs for perturbation_variantset`

## Step 2: Build assembly with Genotype VariantSet referencing mutation-site geometry
**Goal**: Author `genotype_assembly.usda` — a minimal ABL kinase assembly prim carrying a `Genotype` VariantSet that swaps a Reference to the mutation-site geometry file.
**Implementation Logic**:
1. Define `/ABLKinase` as an `Xform` prim representing a simplified ABL kinase complex.
2. Add child prim `/ABLKinase/Res315` as the mutation site.
3. On `/ABLKinase`, add a `Genotype` VariantSet with variants `WildType` and `T315I`.
4. Inside `WildType` edit context: add a Reference arc on `/ABLKinase/Res315` pointing to `geometries/res315_wt.usda`. Inside `T315I` edit context: add a Reference arc pointing to `geometries/res315_t315i.usda`. Confirm Python API for authoring a Reference inside a variant edit context via context7 at execution time.
5. Author a `bio:mutationSite` attribute on `/ABLKinase` (value `"T315"`, type `string`) as provenance.
6. Set default variant to `WildType`.
**Deliverables**: `examples/composition_advanced/perturbation_variantset/build_genotype.py` (functions: `build_genotype_assembly`); `examples/composition_advanced/perturbation_variantset/genotype_assembly.usda` (prim `/ABLKinase` with `Genotype` VariantSet, 2 variants, each referencing a geometry file; `bio:mutationSite = "T315"`)
**Consistency Checks**: `usdcat --flatten examples/composition_advanced/perturbation_variantset/genotype_assembly.usda` (expected: PASS)
**Commit**: `feat(v8-gap-closure): build Genotype VariantSet assembly for perturbation_variantset`

## Step 3: Read-back tests asserting mutation-site geometry differs per Genotype variant
**Goal**: Confirm the composed `bio:residueName` and atom positions on `/ABLKinase/Res315` change when `Genotype` is switched — testing the resolved stage, not build-time state.
**Implementation Logic**:
1. Open `genotype_assembly.usda` with a fresh `Usd.Stage.Open(...)` call.
2. For `WildType`: assert `/ABLKinase/Res315.bio:residueName` resolves to `"THR"` and Oγ1 position is the wild-type sentinel.
3. For `T315I`: assert `bio:residueName` resolves to `"ILE"` and Cγ1 position is the mutant sentinel.
4. Assert that switching variants and re-querying the attribute returns the new value (confirms composition is live, not cached from the build stage).
**Deliverables**: `tests/composition_advanced/test_perturbation_variantset.py` (functions: `test_wildtype_residue_name`, `test_t315i_residue_name`, `test_variant_swap_updates_position`)
**Consistency Checks**: `python tests/composition_advanced/test_perturbation_variantset.py` (expected: PASS)
**Commit**: `test(v8-gap-closure): read-back tests for perturbation_variantset Genotype switching`
