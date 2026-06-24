# Falsification-Resistant Test Harness

**Goal**: Build a 4-layer test harness (usdchecker compliance, domain validators, programmatic read-back, golden diffing) applied to the existing committed `.usda` artifacts so every subsequent gap-closure step has a regression net before it lands.
**Pre-conditions**:
- [ ] `examples/foundation_demo_v8/output/*.usda` (5 files) and `examples/foundation_demo_v8/output/clips/trajectory_clip.usda` (1 file) are committed and readable [source: find output confirmed 6 .usda files]
- [ ] Existing tests cover only Python data dicts (`examples/foundation_demo_v8/tests/test_element_data.py`) and a C++ version string (`tests/smoke_test.cpp`) — neither opens a USD file [source: examples/foundation_demo_v8/tests/test_element_data.py:1-17, tests/smoke_test.cpp]
- [ ] `portability_fix` leaf is complete (scripts can run without absolute paths)
- [ ] OpenUSD Python environment loadable via `. load_env.sh` at repo root
**Success Gates**:
- ⬜ `python3 examples/foundation_demo_v8/tests/run_tests.py --layer compliance` exits 0 and reports usdchecker PASS for all 6 committed `.usda` files
- ⬜ `python3 examples/foundation_demo_v8/tests/run_tests.py --layer domain` exits 0 and reports all biological invariant checks PASS against the committed artifacts
- ⬜ `python3 examples/foundation_demo_v8/tests/run_tests.py --layer readback` exits 0 and reports composed-value assertions PASS (bio:element resolves via inherit, variant cascade resolves at all 4 levels, clip positions populate across the 20-frame range)
- ⬜ `python3 examples/foundation_demo_v8/tests/run_tests.py --layer golden` exits 0 and reports no diff against committed reference fixtures
- ⬜ `python3 examples/foundation_demo_v8/tests/run_tests.py` (no flags, all layers) exits 0 end-to-end
**References**: [R02 §3 Gap Analysis](../../__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md) — §3 gaps including scale, composition arcs not exercised, and the validation plugin gap at §8

## Step 1: Layer 1 — usdchecker compliance gate
**Goal**: Assert that every committed `.usda` file passes `usdchecker` with no errors, establishing a baseline compliance gate before any domain-specific logic.
**Implementation Logic**:
1. Create `examples/foundation_demo_v8/tests/layer1_compliance.py` with a single public function `run(usda_paths: list[str]) -> list[dict]` that shells out to `usdchecker <file>` for each path and collects stdout/returncode.
2. The six target paths are resolved relative to the repo root: `examples/foundation_demo_v8/output/{element_grid_demo,trajectory_demo,water_demo,assembly_demo,residue_grid_demo}.usda` and `examples/foundation_demo_v8/output/clips/trajectory_clip.usda`. Paths are discovered dynamically with `glob` so new artifacts picked up automatically. [source: bash find confirming these 6 files exist]
3. Each file either PASS (returncode 0, no "Error" lines) or FAIL (report the first error line). The function returns structured results; the caller in `run_tests.py` decides how to display.
4. WHY `usdchecker` first: it is the lowest-overhead gate — if a file fails USD's own checker, none of the higher layers are meaningful. Running it programmatically also makes it part of the CI-runnable suite.
5. Note: `UsdValidation` API shape (namespace, `ValidationRegistry`, `RegisterPrimValidator` signatures) must be confirmed at execution time via the context7 MCP tool (`mcp__context7__query-docs` with library `/websites/openusd_release`) — do not rely on training-data knowledge of the API.
**Deliverables**: `examples/foundation_demo_v8/tests/layer1_compliance.py` — symbols: `run`, `ComplianceResult` (namedtuple or dataclass with fields `path`, `passed`, `errors`)
**Consistency Checks**: `python3 -c "import sys; sys.path.insert(0,'examples/foundation_demo_v8/tests'); import layer1_compliance; print('import OK')"` (expected: PASS)
**Commit**: `test(v8-gap-closure): add layer1 usdchecker compliance gate`

## Step 2: Layer 2 — domain validator (biological invariants)
**Goal**: Encode biology-specific structural invariants as programmatic checks against the committed artifacts, catching USD-valid but biologically malformed stages that usdchecker cannot detect.
**Implementation Logic**:
1. Create `examples/foundation_demo_v8/tests/layer2_domain.py` with a public function `run(stage_paths: list[str]) -> list[dict]`.
2. For each stage, open with `Usd.Stage.Open(path)` and enforce three invariants:
   - **Atom invariant**: every prim whose name matches the atom naming convention (type Xform, under a Residue prim) must carry `bio:element` (non-empty token) and inherit from a `/_class_/<Symbol>` class prim. Check via `prim.GetAttribute("bio:element").Get()` and `prim.GetInherits().GetAllDirectInherits()`.
   - **Element class invariant**: every `/_class_/` child prim must carry `bio:vdwRadius` (float > 0) and `bio:cpkColor` (Color3f). Check on `assembly_demo.usda` and `element_grid_demo.usda`.
   - **Representation variant invariant**: any prim carrying a `representation` VariantSet must have all four variants (`points`, `balls`, `vdw`, `ballstick`) registered. Check on `assembly_demo.usda`.
3. Apply only the invariants appropriate to each artifact — `trajectory_clip.usda` (positions only) does not assert atom or variant invariants.
4. WHY programmatic invariants rather than relying solely on usdchecker: `usdchecker` validates USD correctness but knows nothing about `bio:` conventions; a stage could pass usdchecker while missing `bio:element` on every atom.
5. Note: confirm `prim.GetInherits()` API and `UsdValidation.ValidationRegistry` availability at execution time via context7 (`mcp__context7__query-docs`).
**Deliverables**: `examples/foundation_demo_v8/tests/layer2_domain.py` — symbols: `run`, `DomainResult`, `check_atom_invariant`, `check_element_class_invariant`, `check_representation_invariant`
**Consistency Checks**: `python3 -c "import sys; sys.path.insert(0,'examples/foundation_demo_v8/tests'); import layer2_domain; print('import OK')"` (expected: PASS)
**Commit**: `test(v8-gap-closure): add layer2 biological domain invariant validators`

## Step 3: Layer 3 — programmatic read-back tests
**Goal**: Open each committed artifact fresh with `Usd.Stage.Open`, traverse the stage, and assert composed/inherited values match expectations derived from the SOURCE data — not from the generator's in-memory state — proving that USD's composition engine actually resolved the data correctly.
**Implementation Logic**:
1. Create `examples/foundation_demo_v8/tests/layer3_readback.py` with a public function `run(output_dir: str) -> list[dict]`.
2. For `assembly_demo.usda`: open fresh, find the first atom prim, resolve `bio:element` via `GetAttribute("bio:element").Get()` (must be a known element symbol), resolve `displayColor` (must match the CPK color for that element — compare against the `ELEMENTS` dict from `data.py`), confirm inherit chain reaches `/_class_/<symbol>`.
3. For `assembly_demo.usda` variant cascade: set `representation` to each of `["points","balls","vdw","ballstick"]` in turn via `stage.GetRootLayer().GetPrimAtPath(...).GetVariantSets().GetVariantSet("representation").SetVariantSelection(v)`, then call `stage.Reload()` and check that child prims' visibility/geometry attributes differ across selections. Assert that the variant cascade reaches at least 4 hierarchy levels.
4. For `trajectory_demo.usda` with clips: open stage, pick an atom prim at path with known clip coverage, sample `xformOp:translate` at `Usd.TimeCode(0)` and `Usd.TimeCode(10)`, assert the two positions differ (non-zero displacement confirms clip data is live). [source: examples/foundation_demo_v8/output/trajectory_demo.usda exists and clips/trajectory_clip.usda exists]
5. WHY "fresh open": if tests share the generator's in-memory `stage` object, they test the generator's internal state, not USD's composition. `Usd.Stage.Open` from a path forces a cold parse, which is what a downstream consumer does.
6. Note: exact `UsdClipsAPI` sample-time query API must be confirmed via context7 at execution time.
**Deliverables**: `examples/foundation_demo_v8/tests/layer3_readback.py` — symbols: `run`, `ReadbackResult`, `assert_atom_composition`, `assert_variant_cascade`, `assert_clip_positions_vary`
**Consistency Checks**: `python3 -c "import sys; sys.path.insert(0,'examples/foundation_demo_v8/tests'); import layer3_readback; print('import OK')"` (expected: PASS)
**Commit**: `test(v8-gap-closure): add layer3 programmatic USD read-back tests`

## Step 4: Layer 4 — golden/baseline diffing and test runner
**Goal**: Commit small reference `.usda` fixture files for three representative prims and wire all four layers into a single `run_tests.py` entry point, completing the harness.
**Implementation Logic**:
1. Create `examples/foundation_demo_v8/tests/fixtures/` directory. Populate three small hand-authored `.usda` files:
   - `fixture_carbon_element.usda`: the `/_class_/C` prim with expected `bio:vdwRadius`, `bio:cpkColor`, `bio:symbol`.
   - `fixture_atom_inherit.usda`: one atom prim that inherits from `/_class_/C` with `bio:element = "C"`.
   - `fixture_representation_variants.usda`: a minimal prim with a `representation` VariantSet containing all four variant names.
2. Create `examples/foundation_demo_v8/tests/layer4_golden.py` with `run(output_dir: str, fixture_dir: str) -> list[dict]`. For each fixture, shell out to `usdcat --flatten <output_file> | grep <key_attribute>` and compare against the fixture's expected value using `usddiff` or a substring match when `usddiff` is unavailable.
3. Create `examples/foundation_demo_v8/tests/run_tests.py` as the CLI entry point: `--layer {compliance,domain,readback,golden}` flag (default: run all). Loads the USD environment (calls `. load_env.sh` equivalent or requires it pre-loaded), dispatches to each layer module, aggregates results, prints a summary table, exits 0 on all-pass / 1 on any failure.
4. WHY small fixtures rather than diffing the full 12 MB assembly: full-file diffing is fragile (any regeneration with a timestamp change breaks it); targeted key-attribute fixtures are stable and document intent.
**Deliverables**: `examples/foundation_demo_v8/tests/fixtures/fixture_carbon_element.usda`; `fixture_atom_inherit.usda`; `fixture_representation_variants.usda`; `layer4_golden.py` (symbols: `run`, `GoldenResult`); `run_tests.py` (symbols: `main`, `parse_args`, `run_all_layers`)
**Consistency Checks**: `python3 examples/foundation_demo_v8/tests/run_tests.py --help` (expected: PASS)
**Commit**: `test(v8-gap-closure): add layer4 golden fixtures and run_tests.py harness entry point`
