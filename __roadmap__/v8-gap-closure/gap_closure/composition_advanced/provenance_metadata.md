# Structured Provenance Metadata (§3.4)

**Goal**: Replace the flat `bio:source = "ShinobuLab MD simulation"` string on the assembly root with a structured lineage record — source PDB filename, force field, simulation software + version, production settings, and timestamp — as USD metadata and typed `bio:` attributes [source: `../../../../__design__/openusd_for_research_architecture.md` §3 Research-as-Movie analogy, departmental layer provenance; existing code at `examples/foundation_demo_v8/templates/04_create_assembly.py` lines 167–174].
**Pre-conditions**:
- [ ] `examples/foundation_demo_v8/templates/04_create_assembly.py` exists and is readable (the flat `bio:source` attribute is the replacement target)
- [ ] `pxr` Python environment loadable via `load_env.sh`
**Success Gates**:
- ⬜ `examples/composition_advanced/provenance_metadata/` contains `build_provenance.py` and `assembly_with_provenance.usda`
- ⬜ `usdcat --flatten assembly_with_provenance.usda` shows all six lineage fields as distinct typed attributes on `/ABLComplex`: `bio:sourcePdb`, `bio:forceField`, `bio:softwareName`, `bio:softwareVersion`, `bio:simSettings`, `bio:timestamp`
- ⬜ `tests/composition_advanced/test_provenance_metadata.py` opens the stage fresh and asserts each field is present, non-empty, and has the declared type
- ⬜ Updated `examples/foundation_demo_v8/templates/04_create_assembly.py` replaces the single flat `bio:source` attribute with the structured schema (or delegates to a shared helper)
**References**: [R03 §3](../../../../__design__/openusd_for_research_architecture.md) — Research-as-Movie analogy: provenance and reproducibility as first-class concerns; existing flat attribute at `examples/foundation_demo_v8/templates/04_create_assembly.py:167–174`

## Step 1: Define the structured provenance attribute schema
**Goal**: Establish the six typed `bio:` provenance attributes and their USD value types, encoded in a reusable helper function.
**Implementation Logic**:
1. Create `examples/composition_advanced/provenance_metadata/provenance_schema.py` with a function `apply_provenance_metadata(prim, record: dict)` that authors all six attributes:
   - `bio:sourcePdb` (string): source PDB accession or filename, e.g., `"2HYY.pdb"` (ABL kinase crystal structure [assumption: ABL kinase PDB accession representative; execution agent should verify or use a placeholder]).
   - `bio:forceField` (string): force field identifier, e.g., `"AMBER99SB-ILDN"`.
   - `bio:softwareName` (string): simulation software, e.g., `"GENESIS"`.
   - `bio:softwareVersion` (string): version string, e.g., `"2.1.0"`.
   - `bio:simSettings` (string): JSON-encoded dict of key settings (timestep, temperature, pressure), e.g., `'{"timestep_fs": 2.0, "temp_K": 310, "pressure_bar": 1.0}'`.
   - `bio:timestamp` (string): ISO-8601 datetime of when the simulation was run, e.g., `"2024-03-15T09:00:00+09:00"` (JST for ShinobuLab).
2. Use `prim.CreateAttribute(name, Sdf.ValueTypeNames.String).Set(value)` for all six — confirm this is the correct API for custom string attributes via context7.
3. The function signature must accept a `record` dict so it can be called from both the new demo and the updated `04_create_assembly.py`.
**Deliverables**: `examples/composition_advanced/provenance_metadata/provenance_schema.py` (function: `apply_provenance_metadata(prim, record: dict)`)
**Consistency Checks**: `python -c "import ast; ast.parse(open('examples/composition_advanced/provenance_metadata/provenance_schema.py').read())"` (expected: PASS)
**Commit**: `feat(v8-gap-closure): define structured provenance attribute schema helper`

## Step 2: Author assembly with structured provenance metadata
**Goal**: Create `assembly_with_provenance.usda` using `build_provenance.py`, applying all six lineage fields to the `/ABLComplex` root prim.
**Implementation Logic**:
1. Define `/ABLComplex` as an `Xform` prim with `bio:systemName = "ABL kinase + ATP complex"` (mirroring the existing assembly root from `04_create_assembly.py`).
2. Call `apply_provenance_metadata(complex_prim, record)` with the full six-field record (use representative ShinobuLab values from Step 1).
3. Do NOT include the legacy `bio:source` attribute — the structured schema fully replaces it.
4. Save as `assembly_with_provenance.usda`.
**Deliverables**: `examples/composition_advanced/provenance_metadata/build_provenance.py` (functions: `build_provenance_assembly`); `examples/composition_advanced/provenance_metadata/assembly_with_provenance.usda` (prim `/ABLComplex` with all six `bio:` provenance attributes)
**Consistency Checks**: `usdcat --flatten examples/composition_advanced/provenance_metadata/assembly_with_provenance.usda` (expected: PASS)
**Commit**: `feat(v8-gap-closure): author assembly_with_provenance.usda with structured lineage metadata`

## Step 3: Update 04_create_assembly.py to use structured provenance schema
**Goal**: Replace lines 167–174 of `examples/foundation_demo_v8/templates/04_create_assembly.py` (flat `bio:source` string) with a call to `apply_provenance_metadata`, making the production assembly template use the structured schema.
**Implementation Logic**:
1. Import `apply_provenance_metadata` from `provenance_schema.py` (adjust import path relative to `templates/`).
2. Remove the single `complex_prim.CreateAttribute("bio:source", ...)` line (line 169–170).
3. Replace with a `apply_provenance_metadata(complex_prim, { ... })` call using sensible defaults for ShinobuLab data.
4. Keep `bio:systemName` and `bio:atomCount` untouched — only the `bio:source` attribute is replaced.
**Deliverables**: Updated `examples/foundation_demo_v8/templates/04_create_assembly.py` (lines 167–174 replaced with `apply_provenance_metadata` call; `bio:source` attribute removed; six structured attributes added)
**Consistency Checks**: `python examples/foundation_demo_v8/templates/04_create_assembly.py --help 2>&1 || python examples/foundation_demo_v8/templates/04_create_assembly.py` (expected: PASS)
**Commit**: `refactor(v8-gap-closure): replace flat bio:source with structured provenance schema in 04_create_assembly.py`

## Step 4: Read-back tests asserting all provenance fields on fresh stage open
**Goal**: Confirm all six provenance attributes are present and correctly typed on `/ABLComplex` by opening `assembly_with_provenance.usda` fresh and asserting each field.
**Implementation Logic**:
1. Open `assembly_with_provenance.usda` with a fresh `Usd.Stage.Open(...)`.
2. For each of the six attributes (`bio:sourcePdb`, `bio:forceField`, `bio:softwareName`, `bio:softwareVersion`, `bio:simSettings`, `bio:timestamp`):
   a. Assert the attribute exists (`prim.GetAttribute(name).IsValid()` returns True).
   b. Assert the value is a non-empty string.
   c. Assert the declared type is `string` (via `attr.GetTypeName()`).
3. Assert `bio:source` does NOT exist (confirming the legacy attribute is gone).
4. For `bio:simSettings`: parse the string as JSON and assert `"timestep_fs"`, `"temp_K"`, and `"pressure_bar"` keys are present.
**Deliverables**: `tests/composition_advanced/test_provenance_metadata.py` (functions: `test_all_provenance_fields_present`, `test_provenance_field_types`, `test_legacy_source_absent`, `test_sim_settings_parseable_json`)
**Consistency Checks**: `python tests/composition_advanced/test_provenance_metadata.py` (expected: PASS)
**Commit**: `test(v8-gap-closure): read-back tests for structured provenance_metadata fields`
