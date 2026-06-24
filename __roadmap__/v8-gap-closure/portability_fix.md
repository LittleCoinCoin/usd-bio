# Portability Fix — De-hardcode ShinobuLab Paths

**Goal**: Replace all hard-coded `~/Documents/career/Projects/USDBio/ShinobuLab/...` default paths with a single `USDBIO_DATA_DIR` environment variable that fails loudly when unset.
**Pre-conditions**:
- [ ] `examples/foundation_demo_v8/converters/xtc_to_clips.py` lines 60–68 contain `DEFAULT_PDB` and `DEFAULT_XTC` built via `os.path.expanduser("~")` [source: examples/foundation_demo_v8/converters/xtc_to_clips.py:60-68]
- [ ] `examples/foundation_demo_v8/templates/04_create_assembly.py` lines 45–48 contain `DEFAULT_PDB` built via `os.path.expanduser("~")` [source: examples/foundation_demo_v8/templates/04_create_assembly.py:45-48]
- [ ] `examples/foundation_demo_v8/converters/pdb_parser.py` lines 313–317 contain `default_pdb` built via `os.path.expanduser("~")` in `__main__` [source: examples/foundation_demo_v8/converters/pdb_parser.py:313-317]
- [ ] `examples/foundation_demo_v8/ROADMAP/README.md` line 25 contains a literal `/Users/hacker/Documents/career/Projects/USDBio/ShinobuLab/` path [source: examples/foundation_demo_v8/ROADMAP/README.md:25]
**Success Gates**:
- ⬜ `grep -r "expanduser" examples/foundation_demo_v8/` returns zero matches
- ⬜ `grep -r "career/Projects/USDBio" examples/foundation_demo_v8/` returns zero matches in `.py` files
- ⬜ Running any of the three modified scripts without `USDBIO_DATA_DIR` set exits with a non-zero status and a message referencing `USDBIO_DATA_DIR`
- ⬜ Running the scripts with `USDBIO_DATA_DIR` set to a valid path produces the same outputs as before
**References**: [R02 §3 Gap Analysis](../../__reports__/foundation_demo/perspective/01_v8_to_production_perspective.md) — §3 gap table covering data-path coupling that blocks portability

## Step 1: Introduce `get_data_dir()` helper in a shared config module
**Goal**: Provide a single, importable function that reads `USDBIO_DATA_DIR` from the environment and raises `EnvironmentError` with an actionable message when it is unset, so every consumer fails at the same call site.
**Implementation Logic**:
1. Create `examples/foundation_demo_v8/usdbio_env.py` (new file, minimal, zero USD imports so it is safe to import before the OpenUSD env is loaded).
2. Define `get_data_dir() -> str` — reads `os.environ.get("USDBIO_DATA_DIR")`, raises `EnvironmentError("USDBIO_DATA_DIR is not set. Export the path to your ShinobuLab data directory before running usd-bio scripts.")` if absent.
3. Define two convenience constants built lazily on first use (or just derive them inside callers): this module exposes only `get_data_dir()` — individual scripts build their own sub-paths from it to keep cohesion.
4. WHY a shared helper: three scripts currently duplicate the same fallback logic; centralizing it means fixing the env message once rather than three times, and makes it testable without touching any script.
**Deliverables**: `examples/foundation_demo_v8/usdbio_env.py` — symbols: `get_data_dir`
**Consistency Checks**: `python3 -c "import sys; sys.path.insert(0, 'examples/foundation_demo_v8'); import usdbio_env; usdbio_env.get_data_dir()" 2>&1 | grep -q "USDBIO_DATA_DIR" && echo PASS` (expected: PASS)
**Commit**: `feat(v8-gap-closure): add usdbio_env.get_data_dir() shared env helper`

## Step 2: Replace hard-coded paths in `xtc_to_clips.py`
**Goal**: Remove the `DEFAULT_PDB` / `DEFAULT_XTC` constants that embed the absolute ShinobuLab path and replace them with `get_data_dir()`-based defaults.
**Implementation Logic**:
1. In `examples/foundation_demo_v8/converters/xtc_to_clips.py`, remove lines 60–68 (the two `os.path.join(os.path.expanduser("~"), ...)` assignments).
2. Import `get_data_dir` from `usdbio_env` (adjust `sys.path` if needed, or use a relative import consistent with the existing import style in the file).
3. Re-define `DEFAULT_PDB` and `DEFAULT_XTC` using `get_data_dir()` as the root:
   - `DEFAULT_PDB = os.path.join(get_data_dir(), "files", "atp-complex-solv35.pdb")`
   - `DEFAULT_XTC = os.path.join(get_data_dir(), "analysis", "0_traj", "sort_traj_1.xtc")`
4. WHY keep `DEFAULT_*` names: the rest of the script uses them in `argparse` defaults; renaming would widen the diff unnecessarily.
**Deliverables**: `examples/foundation_demo_v8/converters/xtc_to_clips.py` — modified symbols: `DEFAULT_PDB`, `DEFAULT_XTC`
**Consistency Checks**: `USDBIO_DATA_DIR="" python3 examples/foundation_demo_v8/converters/xtc_to_clips.py 2>&1 | grep -q "USDBIO_DATA_DIR" && echo PASS` (expected: PASS)
**Commit**: `fix(v8-gap-closure): de-hardcode ShinobuLab paths in xtc_to_clips.py`

## Step 3: Replace hard-coded paths in `04_create_assembly.py` and `pdb_parser.py`
**Goal**: Apply the same `get_data_dir()` substitution to the remaining two files, leaving no absolute home-directory paths in any Python source.
**Implementation Logic**:
1. In `examples/foundation_demo_v8/templates/04_create_assembly.py`, remove lines 45–48 and replace `DEFAULT_PDB` with `os.path.join(get_data_dir(), "files", "atp-complex-solv35.pdb")` using the same import pattern as Step 2.
2. In `examples/foundation_demo_v8/converters/pdb_parser.py`, remove lines 313–317 in the `__main__` block and replace `default_pdb` with `os.path.join(get_data_dir(), "files", "atp-complex-solv35.pdb")`.
3. Verify both files: `grep -n "expanduser\|career/Projects" <file>` must return empty for each.
4. WHY do both files in one step: they are symmetric single-occurrence fixes with no interaction; batching them into one commit keeps the commit history readable.
**Deliverables**: `examples/foundation_demo_v8/templates/04_create_assembly.py` (modified: `DEFAULT_PDB`); `examples/foundation_demo_v8/converters/pdb_parser.py` (modified: `default_pdb` in `__main__`)
**Consistency Checks**: `grep -r "expanduser" examples/foundation_demo_v8/ | wc -l | grep -q "^0$" && echo PASS` (expected: PASS)
**Commit**: `fix(v8-gap-closure): de-hardcode ShinobuLab paths in 04_create_assembly.py and pdb_parser.py`

## Step 4: Scrub literal path from `ROADMAP/README.md` and add `USDBIO_DATA_DIR` setup note
**Goal**: Replace the absolute user-home path in `ROADMAP/README.md` line 25 with a portable reference and add one-sentence setup guidance so the data location convention is documented in the file users read first.
**Implementation Logic**:
1. In `examples/foundation_demo_v8/ROADMAP/README.md` line 25, replace the literal `/Users/hacker/Documents/career/Projects/USDBio/ShinobuLab/` with `$USDBIO_DATA_DIR/` so the path is expressed as a variable reference.
2. Immediately after the Data Source section header (or as a new Note line), add: `> Set `USDBIO_DATA_DIR` to the root of your ShinobuLab data directory before running any script.`
3. WHY touch the README: the literal path would re-introduce the portability gap at the documentation level; a user setting up the repo should see the env-var pattern in the first document they read about data sources.
**Deliverables**: `examples/foundation_demo_v8/ROADMAP/README.md` — modified section: Data Source
**Consistency Checks**: `grep -n "career/Projects/USDBio\|expanduser\|/Users/hacker" examples/foundation_demo_v8/ROADMAP/README.md | wc -l | grep -q "^0$" && echo PASS` (expected: PASS)
**Commit**: `docs(v8-gap-closure): replace literal ShinobuLab path with $USDBIO_DATA_DIR in ROADMAP README`
