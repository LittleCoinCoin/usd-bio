# Baseline Artifact Fixes — Make Harness Green (Amendment A01)

**Goal**: Fix the three pre-existing defects in the committed v8 `.usda` artifacts that the falsification-resistant test harness surfaced, so the `compliance` and `domain` layers pass and the baseline is trustworthy before any gap_closure experiment builds on it.
**Pre-conditions**:
- [ ] `test_harness` leaf is complete and runnable (`run_tests.py` exists) [source: __roadmap__/v8-gap-closure/test_harness.md done]
- [ ] Harness `compliance` layer fails 6/6 with `usdGeomValidators:StageMetadataChecker.MissingMetersPerUnitMetadata` on every committed `.usda` [source: run_tests.py --layer compliance, exit 1]
- [ ] Harness `domain` layer fails on `element_grid_demo.usda`: `representation` VariantSet has `sticks` instead of `ballstick` (actual=['balls','points','sticks','vdw']) [source: run_tests.py --layer domain, exit 1]
- [ ] Harness `domain` layer flags `/_class_/H` missing `bio:cpkColor` on `assembly_demo.usda` (DEVIATION) [source: run_tests.py --layer domain]
- [ ] Only `converters/xtc_to_clips.py` imports `mdtraj`; the element/water/residue/assembly generators do not, so they are regenerable under the uv OpenUSD interpreter; the two trajectory artifacts are not (mdtraj absent in that interpreter) and must be metadata-patched in place [source: grep mdtraj; openusd-python-interpreter memory]
**Success Gates**:
- ⬜ `run_tests.py --layer compliance` exits 0 (all 6 artifacts carry `metersPerUnit`)
- ⬜ `run_tests.py --layer domain` exits 0 (element_grid has `ballstick`; `/_class_/H` carries `bio:cpkColor`)
- ⬜ `run_tests.py --layer readback` and `--layer golden` still exit 0 (no regression)
- ⬜ `run_tests.py` (all layers) exits 0 end-to-end
- ⬜ The generator source fixes are present so future regenerations stay green (not only the committed outputs patched)
**References**: [R01 cycle-000 audit](../../__reports__/v8-gap-closure/00-audit_and_roadmap_v0.md) — foundation-first/trustworthy-baseline rationale; [test_harness leaf](test_harness.md) — the harness that surfaced these defects

## Step 1: Set `metersPerUnit` (+ `upAxis`) stage metadata in all generators
**Goal**: Every generator that authors a stage must declare its linear scale so `usdchecker` passes; molecular coordinates from PDB/XTC are in Ångström, but USD stage metadata should declare a consistent unit (use `metersPerUnit = 1e-10` for Ångström, or 1.0 with a documented WHY — pick one and apply uniformly). Also set `upAxis` to `Y` (USD default) explicitly.
**Implementation Logic**:
Confirm the exact API at execution time via context7 (`UsdGeom.SetStageMetersPerUnit`, `UsdGeom.SetStageUpAxis`). In each of `templates/01_create_element_templates.py`, `templates/02_create_water_template.py`, `templates/03_create_residue_templates.py`, `templates/04_create_assembly.py`, and `converters/xtc_to_clips.py`, after the stage is created and before save, call `UsdGeom.SetStageMetersPerUnit(stage, <chosen>)` and `UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)`. WHY: missing `metersPerUnit` is the single compliance error across all 6 artifacts; fixing it at the generator is the durable fix.
**Deliverables**: modified `templates/01_create_element_templates.py`, `templates/02_create_water_template.py`, `templates/03_create_residue_templates.py`, `templates/04_create_assembly.py`, `converters/xtc_to_clips.py` — each calling `SetStageMetersPerUnit` + `SetStageUpAxis`
**Consistency Checks**: `COLGREP_BYPASS=1 grep -rl "SetStageMetersPerUnit" examples/foundation_demo_v8/templates examples/foundation_demo_v8/converters | wc -l | tr -d ' '` (expected: 5)
**Commit**: `fix(v8-gap-closure): declare metersPerUnit + upAxis stage metadata in all v8 generators`

## Step 2: Fix the `sticks`→`ballstick` variant name and the `/_class_/H` cpkColor gap
**Goal**: Bring `element_grid_demo` into convention compliance (the `representation` VariantSet must register `ballstick`, not `sticks`) and ensure the Hydrogen element class carries `bio:cpkColor`.
**Implementation Logic**:
Locate where the `representation` VariantSet variant names are authored for the element grid (search the element-template / grid generator) and rename `sticks` → `ballstick`, matching the convention used by `assembly_demo`. Locate the Hydrogen entry in the element data / class authoring and ensure `bio:cpkColor` (Color3f, CPK white ≈ (1,1,1)) is set on `/_class_/H`. WHY: `ballstick` is the project-standard variant token (CLAUDE.md conventions); `bio:cpkColor` is a required element-class attribute per the domain invariant.
**Deliverables**: modified generator/data source(s) for the element grid variant names and the H element class — symbols touched: the `representation` variant registration, the `H` element `bio:cpkColor`
**Consistency Checks**: `COLGREP_BYPASS=1 grep -rl "sticks" examples/foundation_demo_v8 --include="*.py" | wc -l | tr -d ' '` returns 0 for the variant token (verify no stray `sticks` variant remains) (expected: 0)
**Commit**: `fix(v8-gap-closure): use ballstick variant token and add H cpkColor in element generators`

## Step 3: Regenerate (or metadata-patch) the committed artifacts and confirm the harness is green
**Goal**: Bring the committed `.usda` outputs into agreement with the fixed generators, then prove all four harness layers pass.
**Implementation Logic**:
Under the uv OpenUSD interpreter (`. load_env.sh` first), regenerate the four non-trajectory artifacts via their fixed generators (`assembly_demo`, `element_grid_demo`, `residue_grid_demo`, `water_demo`). For the two trajectory artifacts (`trajectory_demo.usda`, `trajectory_clip.usda`), which cannot be regenerated because `xtc_to_clips.py` needs `mdtraj` (absent in the uv interpreter), write a small idempotent pxr patch script that opens each, sets `metersPerUnit`/`upAxis` if absent, and saves — committed as a maintenance utility (e.g. `examples/foundation_demo_v8/tools/patch_stage_metadata.py`). Re-run the full harness. WHY a patch script for trajectory: the interpreter split blocks full regeneration; an idempotent metadata patch is the honest, reproducible fix and documents the constraint. Record the metersPerUnit value chosen and which artifacts were regenerated vs patched.
**Deliverables**: regenerated `output/{assembly_demo,element_grid_demo,residue_grid_demo,water_demo}.usda`; patched `output/trajectory_demo.usda` + `output/clips/trajectory_clip.usda`; new `examples/foundation_demo_v8/tools/patch_stage_metadata.py` (symbols: `patch_stage`, `main`)
**Consistency Checks**: `. ./load_env.sh >/dev/null 2>&1; /Users/hacker/.local/share/uv/python/cpython-3.11.14-macos-aarch64-none/bin/python3 examples/foundation_demo_v8/tests/run_tests.py; echo "exit=$?"` (expected: exit=0)
**Commit**: `fix(v8-gap-closure): regenerate/patch v8 artifacts to pass compliance+domain harness layers`
