# F1 — Scaffold + Anti-Chimera Contracts

**Goal**: Stand up the `examples/p53_mdm2/` Python package with the generalized, root-path-parameterized contracts from the R00 reuse map, so every downstream pipeline extends a clean spine rather than copying ABL-coupled v8 code.

**Pre-conditions**:
- [ ] `examples/p53_mdm2/` currently holds only `README.md` (documentation scaffold from cycle-000) [source: __threads__/p53-mdm2/cycles/cycle-000/HANDOFF.md]
- [ ] R00 reuse map classifications are the authority for what to generalize vs. leave behind [source: __reports__/p53-mdm2/00-architecture_v0.md]

**Success Gates**:
- ⬜ `grep -rn "ABLComplex" examples/p53_mdm2/` returns zero matches (anti-chimera invariant)
- ⬜ `grep -rEn "\b4676\b|\b43\b" examples/p53_mdm2/*/*.py` returns zero matches in library code (dataset counts live only in per-run fixtures)
- ⬜ A shared config module threads `root_path: str` and a data-dir resolver through the package (model on v8 `usdbio_env.get_data_dir()`)
- ⬜ `tools/patch_stage_metadata.py` is **not** carried over (PI Q-001: moot under forOUSD venv) — stage metadata authored directly by the generators

## Step 1: Package skeleton + config module
**Goal**: Create the package tree (`converters/`, `templates/`, `tools/`, `tests/`, `data/` or reuse v8 `data/`) and a `p53_env.py`-style config exposing a data-dir resolver and the parameterized `root_path` default.
**Implementation Logic**: Lazy imports in `__init__.py` (v8's eager `import xtc_to_clips` broke pxr-only interpreters — leave that behind, R00). No USD imports in the config module so it is importable before the OpenUSD env loads.
**Deliverables**: `examples/p53_mdm2/__init__.py`, `examples/p53_mdm2/p53_env.py`
**Commit**: `feat(p53-mdm2): scaffold examples/p53_mdm2 package + parameterized config`

## Step 2: Port the reuse-as-is biochemistry data + element templates
**Goal**: Bring `data/**` (Bondi/Cordero radii, Shannon ionic radii, 20-AA definitions) and the `/_class_/<symbol>` element-template builder over as-is (R00 classifies them reuse-as-is, no ABL coupling).
**Deliverables**: `examples/p53_mdm2/data/**`, element-template builder
**Commit**: `feat(p53-mdm2): port biochemistry data + element-class templates`

**References**: [R00 §The Reuse Map](../../__reports__/p53-mdm2/00-architecture_v0.md), [R00 §Contracts & Invariants](../../__reports__/p53-mdm2/00-architecture_v0.md)
