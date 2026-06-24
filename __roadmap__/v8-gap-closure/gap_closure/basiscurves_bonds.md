# Exp 5 — BasisCurves for Bonds

**Goal**: Replace the per-bond Cylinder prims in the ABL kinase assembly with a single UsdGeomBasisCurves prim encoding all bonds as line segments, and compare file size and trajectory clip size against the cylinder approach.
**Pre-conditions**:
- [ ] `portability_fix` leaf complete: scripts read paths from `USDBIO_DATA_DIR`
- [ ] `test_harness` leaf complete: harness runner exists and passes against existing v8 artifacts
- [ ] `assets/level4_assemblies/abl_kinase_complex.usda` exists (cylinder-bond baseline)
- [ ] `output/clips/trajectory_clip.usda` exists (cylinder-bond clip baseline)
- [ ] OpenUSD `pxr` environment available via `load_env.sh`
**Success Gates**:
- ⬜ `assets/level4_assemblies/abl_kinase_complex_curves.usda` exists with a UsdGeomBasisCurves prim at `/ABLComplex/Bonds`; `curveVertexCounts` length equals 2,428 (one entry per bond) [source: R02 §1 — 2,428 bonds in assembly]
- ⬜ `output/clips/trajectory_clip_curves.usda` clip animates bond-endpoint positions (points primvar time-sampled across ≥ 20 frames)
- ⬜ `abl_kinase_complex_curves.usda` file size < `abl_kinase_complex.usda` (one prim vs 2,428 Xform+Cylinder prims)
- ⬜ `trajectory_clip_curves.usda` file size < `trajectory_clip.usda` (one points primvar vs per-cylinder translate+orient)
- ⬜ Read-back test passes: `tests/test_basiscurves_bonds.py` opens both artifacts fresh and asserts all gates above
**References**: [R02 §5](../../../__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md) — Experiment 5 deliverable: alternative assembly using BasisCurves for bonds; compare file size, render quality, trajectory clip size vs the cylinder approach; current bonds are per-bond Cylinder Xform prims in `templates/04_create_assembly.py:99`

## Step 1: Build BasisCurves assembly variant
**Goal**: Create `templates/06_create_assembly_curves.py` that generates `abl_kinase_complex_curves.usda` with bonds as a single UsdGeomBasisCurves prim instead of 2,428 Xform/Cylinder prims.
**Implementation Logic**:
1. Copy logic from `templates/04_create_assembly.py` but replace `create_bond_geometry()` per-prim calls with accumulation into two lists: `points` (all bond-endpoint positions, 2 per bond = 4,856 Vec3f) and `curveVertexCounts` (2,428 entries each = 2).
2. After all bonds are accumulated, define `UsdGeomBasisCurves` at `/ABLComplex/Bonds`. Set `type = "linear"` (straight line, no basis needed), `wrap = "nonperiodic"`, `points` primvar to the accumulated array, `curveVertexCounts`, and `widths` primvar (uniform float, one value = `BOND_RADIUS * 2`). Confirm attribute names (`points`, `curveVertexCounts`, `widths`, `type`, `wrap`) via context7 (`resolve-library-id "openusd"` → `query-docs "UsdGeomBasisCurves points curveVertexCounts"`) at execution time.
3. Atom hierarchy, element class inheritance, `representation` VariantSet, and `bio:` metadata are unchanged. WHY linear curves: each covalent bond is a straight line; WHY one prim: Hydra Storm draws all segments in one draw call vs 2,428 draw calls for cylinders.
**Deliverables**: `examples/foundation_demo_v8/templates/06_create_assembly_curves.py` — `accumulate_bond_curves(stage, complex_prim, structure)`, `write_bond_curves(stage, prim_path: str, points: list, counts: list)`, and `__main__`; `examples/foundation_demo_v8/assets/level4_assemblies/abl_kinase_complex_curves.usda` — committed assembly artifact
**Consistency Checks**: `source load_env.sh && python3 templates/06_create_assembly_curves.py && python3 -c "from pxr import Usd, UsdGeom; s=Usd.Stage.Open('assets/level4_assemblies/abl_kinase_complex_curves.usda'); bc=UsdGeom.BasisCurves(s.GetPrimAtPath('/ABLComplex/Bonds')); assert bc and len(bc.GetPointsAttr().Get())==4856; print('PASS')"` (expected: PASS)
**Commit**: `feat(v8-gap-closure): BasisCurves assembly encoding all 2428 bonds as linear curve segments`

## Step 2: Build BasisCurves trajectory clip
**Goal**: Extend `converters/xtc_to_clips.py` with `write_curves_clip()` that generates a clip where the `/ABLComplex/Bonds` `points` primvar is time-sampled across frames.
**Implementation Logic**:
1. For each trajectory frame, recompute bond-endpoint positions from per-atom positions: for each bond `(atom_A, atom_B)`, look up the frame-translated positions for each atom and append both to that frame's `points` list.
2. Write `UsdGeomBasisCurves` at `/ABLComplex/Bonds` with time-sampled `points` for frames 0..N-1. `curveVertexCounts` is not time-varying (topology is static).
3. Output `output/clips/trajectory_clip_curves.usda` covering the same 20-frame window as `trajectory_clip.usda`. WHY time-sample `points` not per-atom translate: consolidates all bond motion into one attribute write per frame vs 4,856 translate writes for the cylinder approach.
**Deliverables**: `examples/foundation_demo_v8/converters/xtc_to_clips.py` — new function `write_curves_clip(output_path: str, pdb_path: str, xtc_path: str, n_frames: int)` added to the existing file; `examples/foundation_demo_v8/output/clips/trajectory_clip_curves.usda` — committed clip artifact
**Consistency Checks**: `source load_env.sh && python3 -c "from pxr import Usd, UsdGeom; s=Usd.Stage.Open('output/clips/trajectory_clip_curves.usda'); bc=UsdGeom.BasisCurves(s.GetPrimAtPath('/ABLComplex/Bonds')); assert len(bc.GetPointsAttr().GetTimeSamples())>=20; print('PASS')"` (expected: PASS)
**Commit**: `feat(v8-gap-closure): BasisCurves trajectory clip with time-sampled bond-endpoint points`

## Step 3: Size comparison and assembly demo
**Goal**: Create `demos/curves_demo.py` that composes the BasisCurves assembly + clip, prints a size comparison table, and produces a valid renderable stage.
**Implementation Logic**:
1. Create `output/curves_demo.usda` SubLayering `abl_kinase_complex_curves.usda` and applying `UsdClipsAPI` on `/ABLComplex` pointing to `trajectory_clip_curves.usda`.
2. Print a comparison table row for each artifact: `METRIC artifact=<name> cylinder_bytes=<N> curves_bytes=<N> ratio=<float>` using `os.path.getsize()`.
3. Verify the stage: assert `/ABLComplex/Bonds` is a BasisCurves prim; assert atoms still exist under `/ABLComplex/Chain_A`; assert `UsdClipsAPI` clip is wired.
**Deliverables**: `examples/foundation_demo_v8/demos/curves_demo.py` — `create_curves_demo(output_path: str, curves_assembly_path: str, curves_clip_path: str)` and `compare_file_sizes()`; `examples/foundation_demo_v8/output/curves_demo.usda` — committed demo stage
**Consistency Checks**: `source load_env.sh && python3 demos/curves_demo.py 2>&1 | grep -c "METRIC" | grep -qx "2" && echo PASS` (expected: PASS)
**Commit**: `feat(v8-gap-closure): BasisCurves demo stage with cylinder vs curves size comparison`

## Step 4: Read-back tests
**Goal**: Add `tests/test_basiscurves_bonds.py` that opens both BasisCurves artifacts fresh and asserts structural correctness and the size improvement over cylinders.
**Implementation Logic**:
1. Open `abl_kinase_complex_curves.usda`; assert `/ABLComplex/Bonds` is `UsdGeomBasisCurves`; assert `curveVertexCounts` length == 2428; assert no `Cylinder` type prims under `/ABLComplex/Bonds`.
2. Open `output/clips/trajectory_clip_curves.usda`; assert `/ABLComplex/Bonds` `points` attribute has ≥ 20 time samples.
3. Assert `abl_kinase_complex_curves.usda` file size < `abl_kinase_complex.usda` file size.
4. Assert `trajectory_clip_curves.usda` file size < `trajectory_clip.usda` file size.
5. Open `output/curves_demo.usda`; assert `UsdClipsAPI(stage.GetPrimAtPath('/ABLComplex')).GetClipAssetPaths()` is non-empty; assert frame 0 and frame 9 positions differ on a sample atom.
**Deliverables**: `examples/foundation_demo_v8/tests/test_basiscurves_bonds.py` — `test_curves_assembly_structure()`, `test_curves_clip_time_samples()`, `test_assembly_size_reduction()`, `test_clip_size_reduction()`, `test_curves_demo_trajectory()`, and `__main__` runner
**Consistency Checks**: `source load_env.sh && python3 tests/test_basiscurves_bonds.py` (expected: PASS)
**Commit**: `test(v8-gap-closure): read-back tests for BasisCurves bonds assembly and clip`
