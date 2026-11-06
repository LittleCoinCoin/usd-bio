# Native MaBoSS Plots as Out-of-Stage Byproducts

## Context
This node sits one level below `p6_results_consumption/` for two reasons. It consumes the run directory that `raw_probtraj_payload.md` creates, whose flat `{prefix}_probtraj.csv` layout is what `maboss.StoredResult` requires. It also references its figures from the Results layer that `results_layer_curves.md` creates. Neither exists until those siblings land. **Re-scoped 2026-11-06** by the PI's 2026-09-22 Q-013.1 answer, which overrules R15's opacity rule. The figures are committed PNGs, referenced from USD as texture-like assets with R20's run-digest stale guard. The tool-managed title above ("Out-of-Stage Byproducts") predates this and is kept because nodes are never renamed. This prose is authoritative.

## Reference Documents
- [R20 results layer + texture assets](../../../../__reports__/p53-mdm2/20-results_layer_and_texture_assets_v0.md) — how OpenUSD references textures, and the four-layer stale guard this subtree implements
- [R15 results-consumption boundary](../../../../__reports__/p53-mdm2/15-results_consumption_boundary_v0.md) — the verified `StoredResult` capability and caveat table this subtree is built on. Its opacity rule is overruled by Q-013.1

## Goal
Answer the PI's "is it relevant to reuse MaBoSS's prepared plotting features" with working code at zero new dependency cost. Commit the figures as texture assets that a test binds to the run they came from.

## Pre-conditions
- [ ] `raw_probtraj_payload.md` landed: a committed run directory exists holding the files the MaBoSS binary itself wrote, plus a provenance record listing them
- [ ] `results_layer_curves.md` landed: the Results layer exists and is composed
- [ ] `maboss` 0.8.15 importable in the forOUSD venv, which `run_maboss.py` already requires

## Success Gates
- ⬜ Figures generated from the committed run directory by `maboss.StoredResult`, with no simulation re-run and no new package installed, and named on the run digest
- ⬜ Each figure is referenced from the Results layer through `asset inputs:file` on a `UsdUVTexture`, carrying its source-run digest and image hash
- ⬜ A stale-guard check records, per texture, whether the digests and hashes match what is on disk, whether all asset paths resolve, and whether any PNG is left unreferenced

## Gotchas
- **`plot_observed_graph` is unavailable here.** `get_observed_graph_file()` is defined only on `maboss.Result`, not on `StoredResult`, so the call raises `AttributeError`; it also needs graphviz, which pyMaBoSS does not declare as a requirement.
- **Colors are not stable between `StoredResult` objects.** The palette starts empty and colors are assigned in first-seen order, so a four-variant comparison must set the palette explicitly or the same Boolean state will be drawn in different colors in different panels.
- **The plot methods return `None`** and pyMaBoSS never calls `savefig`. Pass an explicit `Axes` and save from a figure the caller owns — and give each plot its own figure, because two helpers call `plt.legend`/`plt.ylim` on the pyplot current axes rather than on the axis handed in.
- **`StoredResult` infers the node list by splitting state labels**, so a node that is never ON in any state simply will not appear in a native node-trajectory plot, even though the Analysis layer carries an all-zero series for it.
- **Matplotlib PNGs embed a `Software` text chunk carrying the matplotlib version**, observed with 3.11.1 Agg: two processes produced identical bytes, but a version bump changes them. Save with `metadata={"Software": None}`, and key filenames on the run digest rather than the PNG hash; see the [determinism probe](../../../../__reports__/p53-mdm2/evidence/20-png_determinism_probe.txt).
- **The upstream repository is `colomoto/pyMaBoSS`.** `sysbio-curie/pyMaBoSS`, named in the topic INTENT, returns 404 and does not redirect.

## Status
```mermaid
graph TD
    pymaboss_stored_result_plots[pyMaBoSS StoredResult Plots from the Committed Run]:::planned
    classDef done       fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned    fill:#374151,color:#e5e7eb
    classDef amendment  fill:#1e3a5f,color:#bfdbfe
    classDef blocked    fill:#7f1d1d,color:#fecaca
```

## Nodes
| Node | Type | Status |
|:-----|:-----|:-------|
| `pymaboss_stored_result_plots.md` | 📄 Leaf Task | ⬜ Planned |

## Amendment Log
| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress
| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
