# Exp 2 — Binary Format + Clip Templates

**Goal**: Convert the existing `.usda` assembly and clip to `.usdc` binary, benchmark the size/performance difference, and validate `clipTemplateAssetPath` with 2–3 XTC source files mapped as a clip template series.
**Pre-conditions**:
- [ ] `portability_fix` leaf complete: converters read paths from `USDBIO_DATA_DIR` env var
- [ ] `test_harness` leaf complete: harness runner exists and passes against existing v8 artifacts
- [ ] `USDBIO_DATA_DIR` set; directory contains at least 2 XTC trajectory files (e.g. `sort_traj_1.xtc` and `sort_traj_2.xtc`)
- [ ] `output/clips/trajectory_clip.usda` and `assets/level4_assemblies/abl_kinase_complex.usda` exist from the v8 foundation run
- [ ] OpenUSD `pxr` environment available via `load_env.sh`
**Success Gates**:
- ⬜ `output/clips/trajectory_clip.usdc` exists; file size is ≤ 50% of `trajectory_clip.usda` [assumption: Crate format achieves 5–10x compression on time-sampled float arrays; actual ratio confirmed by benchmark]
- ⬜ `assets/level4_assemblies/abl_kinase_complex.usdc` exists; opens and traverses identically to the `.usda` source (same prim count, same variants)
- ⬜ `output/clips/clip_template_manifest.usda` exists; `UsdClipsAPI.GetClipTemplateAssetPath()` returns a non-empty string on the stage's `/ABLComplex` prim
- ⬜ Benchmark script prints `METRIC` lines for load time and file size for both `.usda` and `.usdc` formats
- ⬜ Read-back test passes: `tests/test_binary_clips.py` opens `.usdc` artifacts fresh and asserts compositional equivalence with `.usda` sources
**References**: [R02 §5](../../../__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md) — Experiment 2 deliverable: `.usdc` assembly + trajectory; benchmark load time, scrub latency, file size; test clip template with 2–3 XTC source files

## Step 1: Convert existing .usda files to .usdc binary
**Goal**: Write `converters/usda_to_usdc.py` that batch-converts arbitrary `.usda` files to `.usdc` Crate format and reports size reduction.
**Implementation Logic**:
1. Use `Sdf.Layer.FindOrOpen(usda_path)` to open each source layer, then `layer.Export(usdc_path)` with the `.usdc` extension — the Sdf layer export infers Crate format from the extension. Confirm this API via context7 (`resolve-library-id "openusd"` → `query-docs "Sdf.Layer Export usdc"`) at execution time.
2. For each converted file, print `METRIC file=<name> usda_bytes=<N> usdc_bytes=<N> ratio=<float>`.
3. Convert: `assets/level4_assemblies/abl_kinase_complex.usda` → `abl_kinase_complex.usdc`, `output/clips/trajectory_clip.usda` → `trajectory_clip.usdc`. WHY a dedicated converter: makes conversion reusable for future multi-file pipelines and keeps benchmark logic separate.
**Deliverables**: `examples/foundation_demo_v8/converters/usda_to_usdc.py` — `convert_layer(usda_path: str, usdc_path: str) -> dict` (returns `{usda_bytes, usdc_bytes, ratio}`) and `__main__` batch entrypoint; `examples/foundation_demo_v8/assets/level4_assemblies/abl_kinase_complex.usdc` — committed binary artifact; `examples/foundation_demo_v8/output/clips/trajectory_clip.usdc` — committed binary artifact
**Consistency Checks**: `source load_env.sh && python3 converters/usda_to_usdc.py 2>&1 | grep -c "METRIC" | grep -qx "2" && echo PASS` (expected: PASS)
**Commit**: `feat(v8-gap-closure): convert assembly and clip to .usdc binary with size metrics`

## Step 2: Benchmark load time and scrub latency
**Goal**: Write `demos/binary_benchmark.py` that measures and compares open time and per-frame scrub latency between the `.usda` and `.usdc` variants.
**Implementation Logic**:
1. For each format pair (usda/usdc), measure: (a) `Usd.Stage.Open()` wall time via `time.perf_counter()`, (b) single-frame attribute read latency — call `xformable.GetLocalTransformation(Usd.TimeCode(t))` for a representative atom 20 times and average.
2. Print `METRIC format=usda|usdc load_time_s=<float> frame_read_us=<float>` for each.
3. Open a `output/binary_demo.usda` stage that SubLayers the `.usdc` files, verifying composition still works end-to-end. WHY frame_read_us as proxy: a full 20-frame scrub requires usdview; a programmatic per-frame attribute read is a reproducible substitute.
**Deliverables**: `examples/foundation_demo_v8/demos/binary_benchmark.py` — `benchmark_stage(path: str, n_frames: int) -> dict` and `print_comparison(usda_metrics: dict, usdc_metrics: dict)`; `examples/foundation_demo_v8/output/binary_demo.usda` — demo stage SubLayering `.usdc` assembly + clip, committed artifact
**Consistency Checks**: `source load_env.sh && python3 demos/binary_benchmark.py 2>&1 | grep -c "METRIC" | grep -qx "4" && echo PASS` (expected: PASS)
**Commit**: `feat(v8-gap-closure): benchmark .usda vs .usdc load time and scrub latency`

## Step 3: Implement clip template pattern for multiple XTC files
**Goal**: Extend `converters/xtc_to_clips.py` to write one `.usdc` clip per source XTC and produce a `clip_template_manifest.usda` using `clipTemplateAssetPath`.
**Implementation Logic**:
1. Convert frames from 2–3 XTC files from `USDBIO_DATA_DIR` into separate clip files `output/clips/clip_001.usdc`, `output/clips/clip_002.usdc`, named with zero-padded integers matching the template pattern.
2. Create `output/clips/clip_template_manifest.usda` defining `/ABLComplex` as an Xform with `UsdClipsAPI` metadata: `SetClipTemplateAssetPath("./clip_###.usdc")`, `SetClipTemplateStride(N_FRAMES_PER_FILE)`, `SetClipTemplateStartTime(0)`. Confirm `clipTemplateAssetPath`, `clipTemplateStride`, `clipTemplateStartTime` API via context7 at execution time.
3. WHY clip template over `SetClipAssetPaths`: clip templates map to directory-per-replica layouts (one XTC per simulation run), eliminating the need to enumerate clip paths explicitly — the resolver generates paths from the pattern.
**Deliverables**: `examples/foundation_demo_v8/converters/xtc_to_clips.py` — new function `write_clip_template_manifest(manifest_path: str, clip_dir: str, template_pattern: str, frames_per_clip: int, n_clips: int)`; `examples/foundation_demo_v8/output/clips/clip_001.usdc` — committed first-clip artifact; `examples/foundation_demo_v8/output/clips/clip_002.usdc` — committed second-clip artifact; `examples/foundation_demo_v8/output/clips/clip_template_manifest.usda` — committed manifest artifact
**Consistency Checks**: `source load_env.sh && python3 -c "from pxr import Usd; s=Usd.Stage.Open('output/clips/clip_template_manifest.usda'); api=Usd.ClipsAPI(s.GetPrimAtPath('/ABLComplex')); assert api.GetClipTemplateAssetPath(); print('PASS')"` (expected: PASS)
**Commit**: `feat(v8-gap-closure): clip template pattern mapping multiple XTC files to .usdc clips`

## Step 4: Read-back tests
**Goal**: Add `tests/test_binary_clips.py` that opens `.usdc` artifacts and the clip-template manifest fresh and asserts compositional equivalence and template wiring.
**Implementation Logic**:
1. Open `assets/level4_assemblies/abl_kinase_complex.usdc`; traverse all prims; assert prim count equals the prim count from `abl_kinase_complex.usda`.
2. Assert `/_class_/C` and `/_class_/N` class prims exist in the `.usdc` assembly.
3. Open `output/clips/clip_template_manifest.usda`; assert `UsdClipsAPI.GetClipTemplateAssetPath()` returns non-empty string on `/ABLComplex`.
4. Open `output/binary_demo.usda`; assert frame 0 and frame 9 positions differ on `/ABLComplex/Chain_A/ACE_1/HH31`.
5. Assert `trajectory_clip.usdc` file size < `trajectory_clip.usda` file size; assert `abl_kinase_complex.usdc` file size < `abl_kinase_complex.usda` file size.
**Deliverables**: `examples/foundation_demo_v8/tests/test_binary_clips.py` — `test_usdc_assembly_prim_count()`, `test_usdc_class_prims()`, `test_clip_template_manifest()`, `test_binary_demo_trajectory()`, `test_file_sizes()`, and `__main__` runner
**Consistency Checks**: `source load_env.sh && python3 tests/test_binary_clips.py` (expected: PASS)
**Commit**: `test(v8-gap-closure): read-back tests for .usdc binary conversion and clip template`
