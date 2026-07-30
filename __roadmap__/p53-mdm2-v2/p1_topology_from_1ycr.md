# P1 MD to USD — Topology from 1YCR

**Goal**: Produce a committed topology-only `.usda` for the 1YCR p53–MDM2 complex by generalizing v8's `pdb_parser` + assembly builder off ABL specifics, with falsification-resistant read-back tests. Reframed per PI Q-001: **no trajectory is required** — the MD datum the demo needs is ΔG (Pipeline 2), so Pipeline 1 delivers topology first; time-varying positions (value clips) are an optional later extension gated on whether MD is run (see `p1b`).

**Pre-conditions**:
- [ ] No p53–MDM2 trajectory exists; `USDBIO_DATA_DIR` holds ABL (ShinobuLab) data only [source: PI answer to Q-001, __threads__/p53-mdm2/QUESTIONS.md; source: USDBIO_DATA_DIR=/Users/hacker/Documents/career/Projects/USDBio/ShinobuLab contents]
- [ ] 1YCR chosen as the starting structure (native p53 peptide + MDM2 N-term, triad Phe19/Trp23/Leu26, no small molecule) [source: __reports__/p53-mdm2/00-architecture_v0.md §External Input Decisions]
- [ ] F1 scaffold complete (parameterized `root_path`, config module)

**Success Gates**:
- ⬜ 1YCR fetched/prepared and committed under the package's data convention (or fetched deterministically by the pipeline)
- ⬜ `parse_pdb(path, *, exclude_residues=…, ligand_residues=frozenset())` parses 1YCR with caller-supplied solvent/ligand sets — no ABL `LIGAND_RESIDUES={"atp"}` module constant
- ⬜ A committed topology `.usda` with a parameterized root prim (NOT `/ABLComplex`), `bio:` element-class inherits, `metersPerUnit=1e-10`, CPK colors, and a `representation` VariantSet
- ⬜ Read-back tests open the stage FRESH and assert atom/chain counts + element assignments against expectations **independently re-derived from the 1YCR PDB** (not from generator in-memory state) — the R00 anti-tautology invariant

**References**: [R00 §Pipeline 1](../../__reports__/p53-mdm2/00-architecture_v0.md), [R00 §Testing — the crown jewel](../../__reports__/p53-mdm2/00-architecture_v0.md)

## Step 1: Generalize `pdb_parser` off ABL
**Goal**: Lift v8's parsing core (`_parse_atom_line`, `infer_element`, `parse_solvent`) into the package with solvent/ion/ligand sets as parameters.
**Implementation Logic**:
Solvent/ion/ligand residue sets become caller-supplied parameters instead of ABL module constants; drop the ABL `verify_pdb_parse()` 4676/43 asserts — those atom/ligand counts become per-run fixtures instead of library-code literals.
**Deliverables**: `examples/p53_mdm2/converters/pdb_parser.py` — `parse_pdb(...)`, dataclasses reused as-is
**Consistency Checks**: `. ./load_env.sh && /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import inspect, sys; sys.path.insert(0, 'examples'); from p53_mdm2.converters.pdb_parser import parse_pdb; sig = inspect.signature(parse_pdb); assert 'exclude_residues' in sig.parameters and 'ligand_residues' in sig.parameters"` (expected: PASS)
**Commit**: `feat(p53-mdm2): generalized pdb_parser off ABL specifics`

## Step 2: Generalize the assembly builder + emit 1YCR topology `.usda`
**Goal**: Carry v8 `04_create_assembly.py`'s LIVERPS-applied builder over with `root_path` parameterized.
**Implementation Logic**:
Preserves element-class `inherits`, LOCAL positions, and the `representation` cascade from v8; strips `/ABLComplex`, the duplicated `EXTRA_BONDS` table, and the `composition_advanced` `sys.path` reach that coupled the builder to the ABL demo tree.
**Deliverables**: `examples/p53_mdm2/templates/build_assembly.py`, committed `examples/p53_mdm2/output/p53_mdm2_topology.usda`
**Consistency Checks**: `! grep -q "ABLComplex" examples/p53_mdm2/output/p53_mdm2_topology.usda && grep -q "representation" examples/p53_mdm2/output/p53_mdm2_topology.usda` (expected: PASS)
**Commit**: `feat(p53-mdm2): emit 1YCR topology USD via generalized assembly builder`

## Step 3: Falsification-resistant read-back tests
**Goal**: Layer-2 (domain invariants) + Layer-3 (read-back vs. independently re-derived 1YCR expectations) tests, plus a grep-gate for `ABLComplex`/dataset-counts.
**Implementation Logic**:
Mirrors v8 `tests/` architecture (domain invariants imported from `data.*`, fresh-stage read-back against an independent re-derivation) with 1YCR-specific expectations rebuilt from scratch, plus the anti-chimera grep gate carried over from F1.
**Deliverables**: `examples/p53_mdm2/tests/**`
**Consistency Checks**: `. ./load_env.sh && PYTHONPATH="$PYTHONPATH:$(pwd)/examples" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 examples/p53_mdm2/tests/run_tests.py` (expected: PASS)
**Commit**: `test(p53-mdm2): read-back + anti-chimera tests for 1YCR topology`
