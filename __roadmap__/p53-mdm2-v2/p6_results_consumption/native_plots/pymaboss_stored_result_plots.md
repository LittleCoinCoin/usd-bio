# pyMaBoSS StoredResult Plots from the Committed Run

**Goal**: Generate MaBoSS's own community-standard figures from the committed run directory using `maboss.StoredResult`, write them beside that run directory as byproducts, and record in USD only a provenance pointer to the command that regenerates them — never the image bytes as data.
**Pre-conditions**:
- [ ] `raw_probtraj_payload.md` Step 1 has landed: a committed run directory exists in the flat `{prefix}_probtraj.csv` / `{prefix}_fp.csv` / `{prefix}_statdist.csv` layout that `StoredResult` requires
- [ ] `maboss` 0.8.15 is importable in the forOUSD venv, and `import maboss` already happens in `run_maboss.py`, so matplotlib, pandas, networkx and scikit-learn are already paid for at import time — this leaf adds no dependency
- [ ] R15 boundary rule accepted: an image is opaque bytes, so it is a byproduct outside USD, not an attribute value inside it
**Success Gates**:
- ⬜ `[run]` A generator invoked against the committed run directory writes PNG files beside it, one per plot kind per variant, and exits 0; the produced filenames are listed in the run directory's provenance record
- ⬜ `[run]` The generator is observed to construct `maboss.StoredResult` and to **not** invoke the MaBoSS binary, `cmaboss`, or any simulation — recorded by asserting that the committed run directory's file mtimes are unchanged across a generation pass
- ⬜ `[static]` No `.png`, `.pdf` or other image byte-stream is referenced as an attribute *value* anywhere in a committed `.usda`; the Analysis layer's `maboss` Scope carries at most a `bio:maboss:plotCommand` string recording how to regenerate the figures
- ⬜ `[run]` `plot_observed_graph` is **not** called; the leaf records the reason — `get_observed_graph_file()` is defined only on `maboss.Result`, so it raises `AttributeError` on a `StoredResult`, and its layout step needs graphviz, which is not among pyMaBoSS's declared requirements
- ⬜ `[static]` The run directory's provenance record states which nodes `StoredResult` could and could not report, since a `StoredResult` infers the node list by splitting state labels and therefore omits any node never ON in any state
**References**: [R15 results-consumption boundary](../../../../__reports__/p53-mdm2/15-results_consumption_boundary_v0.md) — §"Should pyMaBoSS's own plotting be reused?" and the verified `StoredResult` capability table; [design vision §3](../../../../__design__/openusd_for_research_architecture.md) — the Dailies / Director Review row that distinguishes review artifacts from scene data

## Step 1: StoredResult figure generator over the committed run
**Goal**: Get the plots a MaBoSS user expects, at the lowest possible cost, without adding a dependency and without letting the figures become scene data.
**Implementation Logic**:
`maboss.StoredResult(path, prefix)` is a pure post-hoc file reader — it runs no simulation and never imports the in-process backend — so it works directly on output the standalone colomoto binary wrote, which is the only backend this project trusts. Point it at each variant's directory in the committed run and call the four plot methods that a `StoredResult` supports: the state trajectory, the node trajectory, the last-state piechart, and the fixed points. Deliberately skip the observed-graph plot; it is unavailable on this class and carries an undeclared graphviz requirement.

Every plot method returns `None` and stashes its figure on a private attribute, and nothing in pyMaBoSS ever calls `savefig`, so pass an explicit `Axes` per plot and save from the figure the caller owns. Passing an axis is also the safer route because two helpers reach for the pyplot state machine rather than the axis handed in, which misplaces the legend when several plots share a figure — so give each plot its own figure. Set a non-interactive matplotlib backend before importing, since the package only enables interactive mode under IPython and a headless run should not depend on that.

Assign the palette explicitly before plotting. `StoredResult.palette` starts empty and colors are handed out in first-seen order, so two variants plotted separately can give the same Boolean state different colors — which would make the four-variant comparison the demo exists to show actively misleading.

Write the figures beside the run directory, not into `analysis/`, so their status as byproducts is legible from the filesystem alone.
**Deliverables**: `examples/p53_mdm2/maboss/plot_stored.py` — `generate_figures(run_dir)`, `STORED_PLOTS` tuple, `_shared_palette()`, `PLOT_COMMAND` string; `examples/p53_mdm2/maboss/output/run_<UTC>/<variant>/figures/` — generated PNGs; run-directory provenance record extended with the filenames produced and the node list `StoredResult` reported
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$PYTHONPATH" MPLBACKEND=Agg /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "from p53_mdm2.maboss import plot_stored; import glob; d = sorted(glob.glob('examples/p53_mdm2/maboss/output/run_*'))[-1]; out = plot_stored.generate_figures(d); assert out and all(p.endswith('.png') for p in out), out"` (expected: PASS)
**Commit**: `feat(p53-mdm2): pyMaBoSS StoredResult figures from the committed run directory`

## Step 2: Record the regeneration command and gate the boundary
**Goal**: Make the images regenerable from what USD says, and make the "no image bytes as data" rule a test rather than a convention.
**Implementation Logic**:
Author a single `bio:maboss:plotCommand` string on the Analysis layer's `maboss` Scope naming the module and entry point that regenerates the figures from the committed run directory. That is the whole USD-side footprint: a reader who wants the pictures learns how to make them, and a reader who wants the numbers already has them as time samples. No asset-valued attribute pointing at a PNG, because a resolvable pointer to a file USD cannot verify is precisely the staleness class the boundary rule exists to avoid.

Then gate it. Add a static check that scans every committed `.usda` for image-extension asset paths and fails if one appears, so a later contributor cannot quietly reintroduce the pattern. Add a check that the recorded command's module and entry point actually exist, so the pointer cannot rot into a lie. Record in the run provenance which nodes `StoredResult` reported, because its node inference differs from the model's declared node table and a reader comparing a native plot against `bio:maboss:prob:<node>` needs to know why a node might be missing from one and present in the other.
**Deliverables**: `examples/p53_mdm2/templates/build_analysis_layer.py` — `bio:maboss:plotCommand` authored on the `maboss` Scope; `examples/p53_mdm2/tests/test_plot_boundary.py` — `run()` returning rows `no_image_assets_in_usda`, `plot_command_resolvable`, `stored_result_nodes_recorded`; `examples/p53_mdm2/tests/run_tests.py` — new `plot-boundary` layer registered
**Consistency Checks**: `PYTHONPATH="/Users/hacker/Documents/bin/OpenUSD/lib/python:$(pwd)/examples:$(pwd)/examples/p53_mdm2/tests:$PYTHONPATH" /Users/hacker/Documents/src/AOUSD/forOUSD/bin/python3 -c "import test_plot_boundary as t; rows = t.run(); assert rows; import sys; sys.exit(0 if all(r.passed for r in rows) else 1)"` (expected: PASS)
**Commit**: `test(p53-mdm2): gate the image-bytes boundary and record the plot regeneration command`
