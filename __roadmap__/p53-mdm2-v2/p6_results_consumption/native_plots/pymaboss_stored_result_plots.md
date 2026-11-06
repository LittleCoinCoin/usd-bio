# pyMaBoSS StoredResult Plots from the Committed Run

**Goal**: Generate MaBoSS's own community-standard figures from the committed run directory using `maboss.StoredResult`, commit them as PNGs, and reference them from the Results layer as texture-like assets (`asset inputs:file` on `UsdUVTexture`), guarded against staleness by R20's run-digest scheme. Re-scoped on 2026-11-06 from the PI's 2026-09-22 Q-013.1 answer, which overrules R15's opacity rule: committed PNGs are "the equivalent of the textures that artists would originally author and keep track of in OpenUSD".
**Pre-conditions**:
- [ ] `raw_probtraj_payload.md` landed: a committed run directory exists in the flat `{prefix}_probtraj.csv` / `{prefix}_fp.csv` / `{prefix}_statdist.csv` layout that `StoredResult` requires, with a provenance record listing the binary-written files
- [ ] `results_layer_curves.md` landed: `results/p53_mdm2_results.usda` exists and is composed into the integrated stage
- [ ] `maboss` 0.8.15 is importable in the forOUSD venv, and `import maboss` already happens in `run_maboss.py`, so this leaf adds no dependency [source: R15 §pyMaBoSS]
- [ ] PI Q-013.1 answer read: the opacity rule is overruled and a stale guard is wanted [source: `__threads__/p53-mdm2/QUESTIONS.md` Q-013]
**Success Gates**:
- ⬜ `[run]` A generator invoked against the committed run directory writes one PNG per plot kind per variant, named `<plotKind>_<variant>.<runDigest12>.png`, and exits 0. `runDigest` is recomputed from the binary-written files listed in the run's provenance record
- ⬜ `[run]` The generator is observed to construct `maboss.StoredResult` and not to invoke the MaBoSS binary, `cmaboss`, or any simulation. This is recorded by asserting that the run directory's binary-written files have unchanged SHA-256s across a generation pass
- ⬜ `[static]` Each PNG is referenced from the Results layer through `asset inputs:file` on a `UsdUVTexture` shader. That shader prim carries `bio:results:sourceRunDigest`, `bio:results:imageSha256`, `bio:results:generator` and `bio:results:matplotlibVersion`, and the Results root prim carries `assetInfo` `version` equal to the run digest
- ⬜ `[run]` A stale-guard check reports, per texture, whether: the recomputed run digest equals the recorded digest and the filename token; the PNG's SHA-256 equals the recorded one; `UsdUtils.ComputeAllDependencies` on the composed stage returns zero unresolved paths; and every PNG under the run's `figures/` is referenced by the stage. The observed values are recorded in this leaf's Progress notes
- ⬜ `[run]` `plot_observed_graph` is not called, and the leaf records why: `get_observed_graph_file()` exists only on `maboss.Result`, and graphviz is not among pyMaBoSS's declared requirements
- ⬜ `[static]` The run provenance records which nodes `StoredResult` could and could not report
**References**: [R20 §The stale guard](../../../../__reports__/p53-mdm2/20-results_layer_and_texture_assets_v0.md) — the four-layer guard and why the filename keys on the run digest rather than the PNG hash; [R15 §pyMaBoSS](../../../../__reports__/p53-mdm2/15-results_consumption_boundary_v0.md) — the verified `StoredResult` capability and caveat table; [PNG determinism probe](../../../../__reports__/p53-mdm2/evidence/20-png_determinism_probe.txt) — the observed `Software` chunk that makes content-addressed names churn

## Step 1: StoredResult figure generator over the committed run
**Goal**: Get the plots a MaBoSS user expects at the lowest possible cost, named so that a new run always yields a new path.
**Implementation Logic**:
`maboss.StoredResult(path, prefix)` is a pure post-hoc file reader, so it works directly on the standalone binary's output. Call the four plot methods a `StoredResult` supports: state trajectory, node trajectory, last-state piechart and fixed points. Skip the observed graph.
Every plot method returns `None` and pyMaBoSS never calls `savefig`. Pass an explicit `Axes` per plot, give each plot its own figure, and save from a figure the caller owns. Set the Agg backend before import.
Set the palette explicitly so the same Boolean state has the same colour in every variant.
Compute `runDigest` as a SHA-256 over the sorted (relative path, file SHA-256) pairs of the binary-written files named in the provenance record. Write each figure into the run directory's `figures/` as `<plotKind>_<variant>.<runDigest12>.png`. Save with `metadata={"Software": None}` so the bytes do not embed the matplotlib version string; record the version separately in USD instead. Delete any PNG under `figures/` whose token is not the current digest, and let git hold the history.
**Deliverables**: `examples/p53_mdm2/maboss/plot_stored.py` — `generate_figures(run_dir)`, `run_digest(run_dir)`, `STORED_PLOTS` tuple, `_shared_palette()`; `examples/p53_mdm2/maboss/output/run_<UTC>/<variant>/figures/` — generated PNGs; run provenance extended with the node list `StoredResult` reported
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$PYTHONPATH" MPLBACKEND=Agg /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "from p53_mdm2.maboss import plot_stored; import glob; d = sorted(glob.glob('examples/p53_mdm2/maboss/output/run_*'))[-1]; out = plot_stored.generate_figures(d); tok = plot_stored.run_digest(d)[:12]; assert out and all(p.endswith(tok + '.png') for p in out), out"` (expected: PASS)
**Commit**: `feat(p53-mdm2): pyMaBoSS StoredResult figures named on the committed run digest`

## Step 2: Reference the PNGs from the Results layer as texture assets
**Goal**: Put each figure into the stage the way a texture is put into a stage: a path on a shader input, plus the provenance needed to prove it is current.
**Implementation Logic**:
Under `results/figures/`, author per figure a `Mesh` quad with `st` texture coordinates and a `Material` with a `UsdPreviewSurface` whose `diffuseColor` connects to a `UsdUVTexture`. The texture's `st` input is fed by a `UsdPrimvarReader_float2`, and its `asset inputs:file` is a path relative to the Results layer, which is the anchor for relative asset paths.
Size and place the quads from the plot box mapping already recorded by `results_layer_curves.md`, rather than inventing a second mapping.
Author the four `bio:results:` provenance attributes on each texture shader prim, and `assetInfo` `version = runDigest` on the Results root prim. Do not use `expressionVariables`; they compose only from the root layer.
**Deliverables**: `examples/p53_mdm2/templates/build_results_layer.py` — `author_figure_textures()`, `FIGURES_SCOPE`, provenance attribute-name constants; `examples/p53_mdm2/results/p53_mdm2_results.usda` — regenerated with texture quads
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "from pxr import Usd, UsdShade; s = Usd.Stage.Open('examples/p53_mdm2/demos/p53_mdm2_integrated.usda'); t = [UsdShade.Shader(p) for p in s.Traverse() if p.IsA(UsdShade.Shader) and UsdShade.Shader(p).GetIdAttr().Get() == 'UsdUVTexture']; assert t; assert all(x.GetInput('file').Get().resolvedPath for x in t)"` (expected: PASS)
**Commit**: `feat(p53-mdm2): reference MaBoSS figures from the Results layer as texture assets`

## Step 3: Stale-guard check
**Goal**: Make "this PNG belongs to the committed run" a tested fact rather than a naming convention.
**Implementation Logic**:
Open the composed stage fresh. For each `UsdUVTexture`, recompute the run digest from disk and compare it with `bio:results:sourceRunDigest` and with the filename token. Recompute the PNG's SHA-256 and compare it with `bio:results:imageSha256`. Run `UsdUtils.ComputeAllDependencies` and require zero unresolved paths. List `figures/` and require every PNG to be referenced.
These checks need no rendering and no matplotlib, so they are deterministic across machines.
An optional regeneration row re-renders and byte-compares only when the installed matplotlib equals `bio:results:matplotlibVersion`. Otherwise it returns zero rows, never a pixel diff.
Return zero rows when the run directory or Results layer is absent. Put both digests in a mismatching row's detail.
**Deliverables**: `examples/p53_mdm2/tests/test_results_textures.py` — `run()` returning rows `texture_run_digest_matches`, `texture_filename_token_matches`, `texture_image_sha_matches`, `texture_paths_all_resolve`, `texture_no_orphan_pngs`, `stored_result_nodes_recorded`; `examples/p53_mdm2/tests/run_tests.py` — new `results-textures` layer registered
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$(pwd)/examples/p53_mdm2/tests:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import test_results_textures as t; rows = t.run(); assert rows; import sys; sys.exit(0 if all(r.passed for r in rows) else 1)"` (expected: PASS)
**Commit**: `test(p53-mdm2): stale guard binding committed figure PNGs to the committed run`
