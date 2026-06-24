# Exp 1 — PointInstancer for Solvent

**Goal**: Render 61,273 water molecules (183,819 atoms) via UsdGeomPointInstancer composing with the per-atom protein in a single stage, and measure load time, mode-switch latency, and memory.
**Pre-conditions**:
- [ ] `portability_fix` leaf complete: converters read paths from `USDBIO_DATA_DIR` env var, no hard-coded ShinobuLab paths
- [ ] `test_harness` leaf complete: `examples/foundation_demo_v8/tests/harness.py` (or equivalent runner) exists and passes against existing v8 artifacts
- [ ] `USDBIO_DATA_DIR` set to a directory containing `atp-complex-solv35.pdb` (full solvated PDB)
- [ ] OpenUSD `pxr` environment available via `load_env.sh`
**Success Gates**:
- ⬜ `examples/foundation_demo_v8/demos/solvent_demo.py` runs without error under `load_env.sh` and writes `output/solvent_demo.usda`
- ⬜ `output/solvent_demo.usda` stage opens; `/SolvatedComplex/Solvent` is a UsdGeomPointInstancer prim with `prototypes` child and `protoIndices`, `positions` primvars
- ⬜ Water count in instancer `positions` matches the number of WAT/TIP3P/SOL residues in the PDB (≥61,273 points)
- ⬜ Protein `/SolvatedComplex/Protein` subtree is a standard per-atom Xform hierarchy (chain → residue → atom, 4,676 atoms)
- ⬜ Read-back test passes: `tests/test_solvent_demo.py` opens `solvent_demo.usda` fresh and asserts all gates above
**References**: [R02 §5](../../../__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md) — Experiment 1 deliverable: solvated assembly with protein (per-atom Xforms) + water (PointInstancer) composing in one scene; measure load time, mode-switch latency, memory

## Step 1: Parse solvent residues from full solvated PDB
**Goal**: Extend `pdb_parser.py` to return solvent residue oxygen-atom coordinates, enabling downstream PointInstancer construction.
**Implementation Logic**:
1. In `converters/pdb_parser.py`, add `parse_solvent(pdb_path) -> list[tuple[float,float,float]]` that reads ATOM/HETATM records for residues named WAT, HOH, TIP3P, or SOL and returns each oxygen-atom coordinate (one point per water molecule, Ångstroms).
2. Return a plain list of (x, y, z) floats — no USD types yet, keeping the parser USD-agnostic.
3. The existing `parse_pdb()` is unchanged; `parse_solvent()` is a separate entry point so callers choose protein-only vs. protein+solvent. WHY separate: adding water inline to `parse_pdb` would break existing callers that expect only protein/ligand records.
**Deliverables**: `examples/foundation_demo_v8/converters/pdb_parser.py` — new function `parse_solvent(pdb_path: str) -> list[tuple[float, float, float]]`
**Consistency Checks**: `source load_env.sh && python3 -c "from converters.pdb_parser import parse_solvent; pts=parse_solvent('$USDBIO_DATA_DIR/atp-complex-solv35.pdb'); assert len(pts)>=61000; print('PASS')"` (expected: PASS)
**Commit**: `feat(v8-gap-closure): add parse_solvent() for WAT/HOH residue coordinates`

## Step 2: Build PointInstancer solvent layer
**Goal**: Create `templates/05_create_solvent_instancer.py` that writes `assets/level5_solvent/solvent_instancer.usda` containing a UsdGeomPointInstancer for solvent molecules.
**Implementation Logic**:
1. Open a stage targeting `assets/level5_solvent/solvent_instancer.usda`; SubLayer `assets/level2_molecules/water_template.usda` to pull in `/_class_/Water`.
2. Define `/Solvent` as UsdGeomPointInstancer. Under `/Solvent/Prototypes/Water`, define an Xform that inherits `/_class_/Water`; register it as the single prototype.
3. Set `protoIndices` (VtIntArray, all zeros) and `positions` (VtVec3fArray from `parse_solvent()`) on the instancer. Confirm exact attribute names (`protoIndices`, `positions`, `prototypes`) via context7 (`resolve-library-id "openusd"` → `query-docs "UsdGeomPointInstancer protoIndices positions"`) at execution time.
4. Add `representation` VariantSet on `/Solvent` with modes `points`/`balls`/`vdw`/`ballstick`, mirroring water_demo. WHY SubLayer water_template: reuses the existing `/_class_/Water` class prim so solvent appearance is controlled from one source.
**Deliverables**: `examples/foundation_demo_v8/templates/05_create_solvent_instancer.py` — `create_solvent_instancer(output_path, water_template_path, solvent_positions)` and `__main__`; `examples/foundation_demo_v8/assets/level5_solvent/solvent_instancer.usda` — committed output artifact
**Consistency Checks**: `source load_env.sh && python3 templates/05_create_solvent_instancer.py && python3 -c "from pxr import Usd, UsdGeom; s=Usd.Stage.Open('assets/level5_solvent/solvent_instancer.usda'); pi=UsdGeom.PointInstancer(s.GetPrimAtPath('/Solvent')); assert pi; print('PASS')"` (expected: PASS)
**Commit**: `feat(v8-gap-closure): add PointInstancer solvent layer for 61k water molecules`

## Step 3: Compose solvated assembly demo
**Goal**: Create `demos/solvent_demo.py` that composes the protein assembly and solvent instancer into a single stage and prints load-time and memory metrics.
**Implementation Logic**:
1. Create `output/solvent_demo.usda`; SubLayer `assets/level4_assemblies/abl_kinase_complex.usda` and `assets/level5_solvent/solvent_instancer.usda`.
2. Define `/SolvatedComplex` root Xform; place `/SolvatedComplex/Protein` referencing `/ABLComplex` and `/SolvatedComplex/Solvent` referencing `/Solvent`. WHY references not SubLayers: isolates namespaces so protein and solvent do not collide at the root.
3. Record wall-clock load time via `time.perf_counter()` and memory via `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss`; print `METRIC load_time_s=<float>` and `METRIC mem_rss_mb=<float>`.
4. Record mode-switch latency: iterate `representation` VariantSet selections and time each round-trip.
5. Data source uses `USDBIO_DATA_DIR` env var through `parse_solvent`.
**Deliverables**: `examples/foundation_demo_v8/demos/solvent_demo.py` — `create_solvent_demo(output_path, assembly_path, solvent_path)` and `benchmark_stage(output_path)` with `__main__`; `examples/foundation_demo_v8/output/solvent_demo.usda` — committed output artifact
**Consistency Checks**: `source load_env.sh && python3 demos/solvent_demo.py 2>&1 | grep -c "METRIC" | grep -qx "2" && echo PASS` (expected: PASS)
**Commit**: `feat(v8-gap-closure): compose solvated assembly demo with PointInstancer + protein`

## Step 4: Read-back tests
**Goal**: Add `tests/test_solvent_demo.py` that opens `output/solvent_demo.usda` as a cold consumer and asserts all structural and compositional invariants.
**Implementation Logic**:
1. Open `output/solvent_demo.usda` via `Usd.Stage.Open()` — no generator code in scope.
2. Assert `/SolvatedComplex/Solvent` is a UsdGeomPointInstancer prim; assert `positions` primvar length ≥ 61,000; assert `protoIndices` length equals `positions` length.
3. Assert `/SolvatedComplex/Protein/Chain_A` exists (protein hierarchy present).
4. Assert `representation` VariantSet with variants `points`, `balls`, `vdw`, `ballstick` exists on `/SolvatedComplex/Solvent`.
5. Use the harness runner from the `test_harness` foundation leaf to register and run assertions. WHY read-back: ensures the written file is independently correct, not just consistent with in-memory generator state.
**Deliverables**: `examples/foundation_demo_v8/tests/test_solvent_demo.py` — `test_pointinstancer_exists()`, `test_water_count()`, `test_protein_hierarchy()`, `test_representation_variants()`, and `__main__` runner
**Consistency Checks**: `source load_env.sh && python3 tests/test_solvent_demo.py` (expected: PASS)
**Commit**: `test(v8-gap-closure): read-back tests for PointInstancer solvent demo`
