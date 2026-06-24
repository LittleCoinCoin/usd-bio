# Exp 6 — References vs SubLayers

**Goal**: Build an alternative ABL kinase assembly that references element templates as assets instead of sublayering them, and compare editability, namespace encapsulation, and file organisation against the existing SubLayer approach.
**Pre-conditions**:
- [ ] `portability_fix` leaf complete: scripts read paths from `USDBIO_DATA_DIR`
- [ ] `test_harness` leaf complete: harness runner exists and passes against existing v8 artifacts
- [ ] `assets/level1_elements/element_templates.usda` exists (the SubLayer-based element library from v8 foundation)
- [ ] OpenUSD `pxr` environment available via `load_env.sh`
**Success Gates**:
- ⬜ `assets/level1_elements/element_library.usda` exists as a self-contained reference-friendly asset with a default prim under `/_ElementLibrary/`
- ⬜ `assets/level4_assemblies/abl_kinase_complex_refstyle.usda` exists and opens without errors; `/_ElementLibrary/_class_/C` and `/_ElementLibrary/_class_/N` prims are reachable under `/ElementLib` in the composed stage
- ⬜ `demos/references_demo.py` prints ≥ 4 structured `FINDING` lines comparing encapsulation, prim count, file size, and override path depth
- ⬜ Read-back test passes: `tests/test_references_vs_sublayers.py` opens both assemblies and asserts prim counts match and encapsulation differs as expected
**References**: [R02 §5](../../../__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md) — Experiment 6 deliverable: same assembly built with References instead of SubLayers for element templates; compare editability, encapsulation, file organisation; current state: SubLayers used throughout, no AddReference calls

## Step 1: Author a reference-friendly element library asset
**Goal**: Create `assets/level1_elements/element_library.usda` as a self-contained asset with a declared default prim, suitable for `AddReference` calls.
**Implementation Logic**:
1. The existing `element_templates.usda` has no default prim — it is designed as a sublayer. A referenceable asset needs a root prim that callers reference into a target namespace.
2. Create `element_library.usda` with root Xform `/_ElementLibrary` as the default prim. Under it, define all element class prims as children: `/_ElementLibrary/_class_/H`, `/_ElementLibrary/_class_/C`, etc., identical content to the existing templates (CPK colors, VDW radii, `bio:` namespace attributes).
3. Write `templates/07_create_element_library.py` that generates `element_library.usda`, reusing data from `data/element_properties.py`. WHY a root Xform wrapper: when a caller writes `prim.GetReferences().AddReference("element_library.usda")`, USD maps the asset's default prim to `prim`'s path. The `_ElementLibrary` wrapper scopes the class hierarchy under the caller's chosen path rather than merging at the stage root as SubLayers do.
**Deliverables**: `examples/foundation_demo_v8/templates/07_create_element_library.py` — `create_element_library(output_path: str)` with `__main__`; `examples/foundation_demo_v8/assets/level1_elements/element_library.usda` — committed library artifact with default prim `/_ElementLibrary`
**Consistency Checks**: `source load_env.sh && python3 templates/07_create_element_library.py && python3 -c "from pxr import Usd; s=Usd.Stage.Open('assets/level1_elements/element_library.usda'); dp=s.GetDefaultPrim(); assert dp.IsValid() and s.GetPrimAtPath('/_ElementLibrary/_class_/C').IsValid(); print('PASS')"` (expected: PASS)
**Commit**: `feat(v8-gap-closure): author reference-friendly element_library.usda with default prim`

## Step 2: Build the reference-style assembly
**Goal**: Create `templates/08_create_assembly_refstyle.py` that generates `abl_kinase_complex_refstyle.usda` using `AddReference` for element templates.
**Implementation Logic**:
1. Start from a new stage (do not SubLayer `element_templates.usda`).
2. At the stage root, add a reference to `element_library.usda` on a prim `/ElementLib`, pulling the class hierarchy into the stage under `/ElementLib/_ElementLibrary/_class_/`. Confirm `GetReferences().AddReference()` API via context7 (`resolve-library-id "openusd"` → `query-docs "UsdPrim GetReferences AddReference"`) at execution time.
3. Atom prims `inherit` from `/ElementLib/_ElementLibrary/_class_/<Symbol>` instead of `/_class_/<Symbol>`. This is the only structural change: Inherits arc path changes; the inheritance mechanism is unchanged.
4. All other assembly logic (chain/residue/atom hierarchy, `bio:` attributes, `representation` VariantSet) is identical to `04_create_assembly.py`. WHY this matters: with SubLayers, `/_class_/C` is globally visible at the stage root; with References, the library is namespaced under `/ElementLib`, making the dependency explicit and replaceable.
**Deliverables**: `examples/foundation_demo_v8/templates/08_create_assembly_refstyle.py` — `create_assembly_refstyle(output_path: str, pdb_path: str, element_library_path: str)` with `__main__`; `examples/foundation_demo_v8/assets/level4_assemblies/abl_kinase_complex_refstyle.usda` — committed assembly artifact
**Consistency Checks**: `source load_env.sh && python3 templates/08_create_assembly_refstyle.py && python3 -c "from pxr import Usd; s=Usd.Stage.Open('assets/level4_assemblies/abl_kinase_complex_refstyle.usda'); assert s.GetPrimAtPath('/ElementLib').IsValid() and s.GetPrimAtPath('/ABLComplex/Chain_A').IsValid(); print('PASS')"` (expected: PASS)
**Commit**: `feat(v8-gap-closure): reference-style assembly using AddReference for element templates`

## Step 3: Comparison analysis and demo
**Goal**: Create `demos/references_demo.py` that opens both assemblies, compares key properties, and prints structured `FINDING` lines.
**Implementation Logic**:
1. Open `abl_kinase_complex.usda` (SubLayer style) and `abl_kinase_complex_refstyle.usda` (Reference style).
2. Compare and print `FINDING category=<name> sublayer=<value> reference=<value>` for: (a) **encapsulation** — `/_class_/C` visible at stage root in sublayer (`True`/`False`); (b) **prim_count** — `sum(1 for _ in s.Traverse())`; (c) **file_size_bytes** — `os.path.getsize()`; (d) **override_path_depth** — length of path to the class prim (shorter in sublayer style, longer in reference style due to `/ElementLib` container). WHY structured FINDING lines: machine-readable for future automation and easy to grep in CI.
**Deliverables**: `examples/foundation_demo_v8/demos/references_demo.py` — `compare_assemblies(sublayer_path: str, refstyle_path: str)` with `__main__`
**Consistency Checks**: `source load_env.sh && python3 demos/references_demo.py 2>&1 | grep -c "FINDING" | awk '{if($1>=4) print "PASS"; else print "FAIL"}'` (expected: PASS)
**Commit**: `feat(v8-gap-closure): comparison demo printing References vs SubLayers encapsulation findings`

## Step 4: Read-back tests
**Goal**: Add `tests/test_references_vs_sublayers.py` that opens both assemblies and asserts parity of biological content plus the expected encapsulation difference.
**Implementation Logic**:
1. Open both `abl_kinase_complex.usda` and `abl_kinase_complex_refstyle.usda`; assert both stages have no errors.
2. Assert atom count under `/ABLComplex` is the same for both (traverse and count prims with `bio:element` attribute).
3. Assert `representation` VariantSet exists on `/ABLComplex` in both.
4. Assert SubLayer style: `stage_sublayer.GetPrimAtPath("/_class_/C").IsValid() == True`.
5. Assert Reference style: `stage_refstyle.GetPrimAtPath("/_class_/C").IsValid() == False` and `stage_refstyle.GetPrimAtPath("/ElementLib").IsValid() == True`.
6. Assert inherited `bio:vdwRadius` on a carbon atom equals the same value in both assemblies (same element data, different inheritance path).
**Deliverables**: `examples/foundation_demo_v8/tests/test_references_vs_sublayers.py` — `test_both_stages_open()`, `test_atom_count_parity()`, `test_representation_variantset()`, `test_sublayer_root_class_prim()`, `test_reference_namespaced_class_prim()`, `test_inherited_radius_parity()`, and `__main__` runner
**Consistency Checks**: `source load_env.sh && python3 tests/test_references_vs_sublayers.py` (expected: PASS)
**Commit**: `test(v8-gap-closure): read-back tests verifying References vs SubLayers parity and encapsulation`
