# foundation_demo_v8

Working Python prototypes exploring OpenUSD composition patterns (LIVERPS)
against real ABL kinase MD simulation data (ShinobuLab). See the repo-root
`CLAUDE.md` and `__design__/openusd_for_research_architecture.md` for the
architectural vision this directory validates.

## 1. Environment Setup

This project requires a **custom-built OpenUSD Python environment**. Do not
use system Python or system USD tools — they either segfault or give
misleading results.

```bash
# From the repo root:
. ./load_env.sh
# Sets PYTHONPATH=/Users/hacker/Documents/bin/OpenUSD/lib/python
#      USDBIO_DATA_DIR=<ShinobuLab data root>
```

**Interpreter**: use
`/Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3` (3.11.14) for every
script in this directory. It is the only interpreter with both `pxr` and
`mdtraj` available. Bare `uv`/system Pythons either lack `mdtraj` or
segfault on `import pxr`.

```bash
/Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 demos/trajectory_demo.py
```

**CLI tools (usdview, usdrecord, usdchecker, usdcat, usdtree)**: the real
Pixar build lives at `/Users/hacker/Documents/bin/OpenUSD/bin/`. Always use
the full path:

```bash
/Users/hacker/Documents/bin/OpenUSD/bin/usdview output/trajectory_demo.usda
```

> **WARNING**: macOS ships `/usr/bin/usdcat`, `/usr/bin/usdview`, etc. as
> part of Apple's SceneKit framework. These are NOT Pixar's USD tools —
> they parse a different, incompatible dialect and will silently produce
> wrong or misleading output (or simply fail) on files from this project.
> Never rely on bare `usdview`/`usdchecker`/etc. on `$PATH` unless you have
> personally confirmed `which usdview` resolves to the real build.

## 2. Output Files — What To Open

`output/` contains two categories of artifact. Opening the wrong category
directly in usdview is the single most common source of "this looks
broken" reports — see `docs/11_trajectory_demo_guide.md` and
`docs/13_value_clips_for_trajectories.md` for the full explanation.

### Viewer entry points — open these in usdview

| File | Animated? | Notes |
|---|---|---|
| `trajectory_demo.usda` | Yes — press Play | Cylinder bonds + per-atom Xform, MD trajectory via Value Clips. Default representation: `points`. |
| `curves_demo.usda` | Yes (nominally) | BasisCurves bond encoding + Value Clips. **Known incomplete**: no default `representation` variant selection is authored, and the curves clip does not drive per-atom positions — see the callout in `docs/13_value_clips_for_trajectories.md`. Run `tests/usdview_regression_check.py` to see this flagged mechanically. |
| `binary_demo.usda` | Yes — press Play | Same trajectory as `trajectory_demo.usda`, but topology + clip are `.usdc` (binary) SubLayers. No default `representation` variant is authored on this file either — atoms are invisible until you pick a variant selection yourself in usdview. |
| `departmental_demo.usda` | Yes — press Play | 5-layer SubLayer stack (biology/protocol/dynamics/analysis/review). Same missing-default-selection caveat as `binary_demo.usda`. |
| `assembly_demo.usda` | No (static) | Full ABL kinase assembly, default representation `balls`. |
| `element_grid_demo.usda` | No (static) | Periodic-table-style grid of element class prims. |
| `residue_grid_demo.usda` | No (static) | Grid of amino-acid residue class prims. |
| `solvent_demo.usda` | No (static) | Protein (per-atom Xforms) + solvent shell (`UsdGeomPointInstancer`, ~61k waters). No default `representation` variant authored on the protein atoms (same caveat as above). |
| `water_demo.usda` | No (static) | Single water molecule template demo. |

If a file above says "no default variant authored," fresh `usdview` open
will show bond geometry (Cylinders) but zero atom Spheres, because no
ancestor has an authored `representation` selection to cascade down to the
per-atom variant sets. Select any representation manually in usdview's
metadata/layer panel to see atoms appear. This is a real authoring gap,
tracked by Gate 2 of the regression check below — it is not specific to
`curves_demo.usda`, though `curves_demo.usda` additionally has the clip
desync bug described in doc 13.

### Intermediate payload / manifest artifacts — do NOT open directly

| File | What you'll see if you open it anyway |
|---|---|
| `clips/trajectory_clip.usda` | Grey bond cylinders only, no atoms, dead Play button — **expected**; open `trajectory_demo.usda` instead. |
| `clips/trajectory_clip.usdc` | Same as above (binary twin). |
| `clips/clip.001.usdc`, `clips/clip.002.usdc` | Same as above (clip-template shards). |
| `clips/clip_template_manifest.usda` | Empty viewport — this file is pure metadata (a `clipTemplateAssetPath` dictionary on an otherwise-empty `Xform`), no geometry at all. |
| `clips/trajectory_clip_curves.usda` | A small, disconnected blob of curve geometry with no atoms — this is the curves-mode clip payload, incomplete per the `curves_demo.usda` caveat above. |

These files exist because USD Value Clips separate static topology from
time-varying position data (see doc 13). The clip files intentionally carry
*only* time-sampled `xformOp:translate`/`points` data at matching prim
paths — no hierarchy metadata, no colors, no variant definitions, and (for
the clip payloads specifically) no authored stage time range. All of that
lives in the topology SubLayer and the consuming `*_demo.usda` file. This
is correct, tested behavior (`tests/test_binary_clips.py`), not a bug —
but it does mean these files look broken if you open them standalone.

## 3. Running the Demo Generators

Prerequisites are level-ordered: run `templates/` scripts before any
`demos/` script that depends on their output.

```bash
cd examples/foundation_demo_v8
. ../../load_env.sh
PY=/Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3

# Templates (run once; later steps depend on these)
$PY templates/01_create_element_templates.py     # -> assets/level1_elements/
$PY templates/02_create_water_template.py        # -> assets/level2_molecules/
$PY templates/03_create_residue_templates.py     # -> assets/level3_residues/
$PY templates/04_create_assembly.py              # -> assets/level4_assemblies/abl_kinase_complex.usda
$PY templates/05_create_solvent_instancer.py     # -> assets/level5_solvent/
$PY templates/06_create_assembly_curves.py       # -> assets/level4_assemblies/abl_kinase_complex_curves.usda
$PY templates/07_create_element_library.py
$PY templates/08_create_assembly_refstyle.py
$PY templates/09_create_departmental_layers.py   # -> assets/level6_departmental/

# Converters (trajectory + binary conversion)
$PY converters/xtc_to_clips.py                   # -> output/clips/trajectory_clip.usda
$PY converters/usda_to_usdc.py                   # -> .usdc twins of assembly + clip
```

`converters/xtc_to_clips.py`'s `__main__` block only drives
`generate_clips()`, which writes `trajectory_clip.usda`. Two more
generators live in the same module but are **not wired to a CLI
entrypoint** — `generate_clip_template_series()` (writes
`clip.001.usdc`/`clip.002.usdc`/`clip_template_manifest.usda`, see the
"Clip Template Pattern" subsection of `docs/13_value_clips_for_trajectories.md`)
and `write_curves_clip()` (writes `trajectory_clip_curves.usda`, consumed
by `demos/curves_demo.py`). To regenerate those artifacts, call the
functions directly from a Python session/script; there is currently no
single command that reproduces the full `output/clips/` directory.

```bash

# Demos (each writes one output/*.usda)
$PY demos/element_grid_demo.py     # -> output/element_grid_demo.usda
$PY demos/residue_grid_demo.py     # -> output/residue_grid_demo.usda
$PY demos/water_demo.py            # -> output/water_demo.usda
$PY demos/assembly_demo.py         # -> output/assembly_demo.usda
$PY demos/solvent_demo.py          # -> output/solvent_demo.usda
$PY demos/trajectory_demo.py       # -> output/trajectory_demo.usda   (needs xtc_to_clips.py first)
$PY demos/curves_demo.py           # -> output/curves_demo.usda        (needs 06_create_assembly_curves.py first)
$PY demos/departmental_demo.py     # -> output/departmental_demo.usda  (needs 09_create_departmental_layers.py first)
$PY demos/references_demo.py
$PY demos/binary_benchmark.py      # perf METRIC lines; ALSO verifies output/binary_demo.usda if present
```

`output/binary_demo.usda` itself is small hand-authored/ad-hoc content
(4 lines: `subLayers` pointing at the two `.usdc` files + an empty
`over "ABLComplex"`) — no script in `demos/` or `converters/` currently
regenerates it from scratch. `demos/binary_benchmark.py` only *verifies*
it if the file already exists (and prints a WARN + skip if it doesn't).
If you need to recreate it, mirror the 4-line structure shown at the top
of this README's file table, pointing at
`../assets/level4_assemblies/abl_kinase_complex.usdc` and
`clips/trajectory_clip.usdc`, with `startTimeCode=0`, `endTimeCode=19`,
`framesPerSecond=10`.

Then view any entry point from the table above:

```bash
/Users/hacker/Documents/bin/OpenUSD/bin/usdview output/trajectory_demo.usda
```

## 4. Test Suites

### 4-layer compliance/domain/readback/golden harness

```bash
$PY tests/run_tests.py               # all layers
$PY tests/run_tests.py --layer domain
```

### usdview regression check (this cycle's deliverable)

`tests/usdview_regression_check.py` is a headless, 6-gate check that
catches the "static / grey / double-display / wrong-file" bug class
*before* a human opens usdview. It opens every file in the manifest above
FRESH via `Usd.Stage.Open` and asserts independently-stated expectations —
it never trusts generator in-memory state.

```bash
$PY tests/usdview_regression_check.py
# or, to also run the slow pixel-diff gate (needs PIL + numpy, which the
# forOUSD interpreter does NOT currently have installed — this gate will
# report a clear failure rather than crash if they're missing):
$PY tests/usdview_regression_check.py --render
# tune the per-file usdchecker budget (default 60s):
$PY tests/usdview_regression_check.py --usdchecker-timeout 120
```

Exit code is nonzero if any gate fails on any file. What it checks, per
declared **viewer entry point**:

| Gate | Catches |
|---|---|
| 1 — Structural | Authored time range + `start < end` for animated demos; `>0` renderable gprims and `>0` colored/materialed prims resolve across the whole fresh stage ("wrong file, nothing renders" / "grey block"). |
| 2 — Variant-selection completeness | Every `variantSet` on the fresh composed stage has an authored default selection, checked *before* any `SetVariantSelection` call ("opens with curves visible and atoms invisible because nothing is selected"). |
| 3 — Cross-representation visibility-exclusivity | Cycles the top-level `representation` variant and flags any sibling geometry group (e.g. `Bonds`) that stays visible under *every* selection instead of being properly variant-gated (double-display). |
| 4 — Clip/topology position-sync | For `UsdClipsAPI`-wired prims: at least one descendant resolves via `Usd.ResolveInfoSourceValueClips`, and coupled clip-driven groups (e.g. `Bonds` centroid vs. the atom-cloud centroid) don't diverge beyond a bounding-box-scaled tolerance — catches PDB-frame-vs-MD-frame desync. |
| 5 — Frame-diff (opt-in, `--render`) | `usdrecord`s the first/last declared frame and asserts mean-abs pixel delta exceeds a small threshold — catches "fully static despite having a timeline." Off by default (slow, needs offscreen GL + PIL/numpy). |
| 6 — usdchecker floor | Runs the real `usdchecker --skipVariants` as a fast compliance floor. Necessary, not sufficient — it reports clean "Success!" on files with real semantic bugs (see Gates 1-4); it exists to catch schema-level breakage fast, with an explicit report (not silent skip) if a file's check times out. |

Payload/manifest files (`output/clips/*`) are automatically skipped for
gates 1-4 (their role in the manifest is `payload_or_manifest`, not a
viewer entry point) but still run through Gate 6.

As of this writing, running the check reports 5 real failures: `curves_demo.usda`
fails gates 2 and 4 (its known-incomplete Value Clips wiring, see doc 13's
callout), and `binary_demo.usda`, `departmental_demo.usda`, and
`solvent_demo.usda` fail gate 2 (no default `representation` variant
selection authored anywhere in their composition, so atoms are invisible
on fresh open — a real, previously-undetected authoring gap distinct from
`curves_demo.usda`'s bug).
