# Native MaBoSS Plots as Out-of-Stage Byproducts

## Context
Sits one level below `p6_results_consumption/` because it consumes the run directory that `raw_probtraj_payload.md` Step 1 creates — the flat `{prefix}_probtraj.csv` layout is what `maboss.StoredResult` requires, and it does not exist until that step lands. It produces MaBoSS's own community-standard figures as files beside that run directory, and it deliberately produces nothing that enters a `.usda` except a string naming how to regenerate them.

## Reference Documents
- [R15 results-consumption boundary](../../../../__reports__/p53-mdm2/15-results_consumption_boundary_v0.md) — the opacity rule that puts these figures outside USD, and the verified `StoredResult` capability and caveat table this subtree is built on

## Goal
Answer the PI's "is it relevant to reuse MaBoSS's prepared plotting features" with working code, at zero new dependency cost, without letting image bytes become scene data.

## Pre-conditions
- [ ] `raw_probtraj_payload.md` Step 1 landed — a committed run directory exists holding the files the MaBoSS binary itself wrote
- [ ] `maboss` 0.8.15 importable in the forOUSD venv, which `run_maboss.py` already requires

## Success Gates
- ⬜ Figures generated from the committed run directory by `maboss.StoredResult`, with no simulation re-run and no new package installed
- ⬜ No committed `.usda` carries an image-extension asset path as an attribute value, enforced by a check rather than by convention
- ⬜ The regeneration command is recorded on the Analysis layer and its module and entry point are asserted to exist

## Gotchas
- **`plot_observed_graph` is unavailable here.** `get_observed_graph_file()` is defined only on `maboss.Result`, not on `StoredResult`, so the call raises `AttributeError`; it also needs graphviz, which pyMaBoSS does not declare as a requirement.
- **Colors are not stable between `StoredResult` objects.** The palette starts empty and colors are assigned in first-seen order, so a four-variant comparison must set the palette explicitly or the same Boolean state will be drawn in different colors in different panels.
- **The plot methods return `None`** and pyMaBoSS never calls `savefig`. Pass an explicit `Axes` and save from a figure the caller owns — and give each plot its own figure, because two helpers call `plt.legend`/`plt.ylim` on the pyplot current axes rather than on the axis handed in.
- **`StoredResult` infers the node list by splitting state labels**, so a node that is never ON in any state simply will not appear in a native node-trajectory plot, even though the Analysis layer carries an all-zero series for it.
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
