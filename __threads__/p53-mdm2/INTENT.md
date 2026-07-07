---
topic: p53-mdm2
created: 2026-07-07
---
# Brief

## Goal — a runnable, multi-scale p53-mdm2 demonstration with OpenUSD as the intermediary

Deliver an end-to-end demonstration in which OpenUSD is the shared representation tying molecular dynamics to systems-biology modelling for the p53-mdm2 complex: MD trajectory → USD → ΔG per variant → binarized node states → MaBoSS Boolean-network simulation → results returned to USD for integrated MD + systems-biology consultation. This is a large research question expected to span many work cycles. Work lands under a new `examples/p53_mdm2/` scaffold; `foundation_demo_v8/` stays intact and serves as inspiration, not a copy source.

## The four data pipelines

| Pipeline | Status today | What the topic must build |
|---|---|---|
| **MD → OpenUSD** | Complete but ABL-specific in v8 | Generalize the PDB/XTC→USD path off ABL specifics; drive it with the p53-mdm2 complex. |
| **OpenUSD → MD (ΔG)** | Designed only (arch doc §4.2 Perturbation Variant) | Variant→query→result flow. ΔG source is the ddMut PPI API (`https://biosig.lab.uq.edu.au/ddmut_ppi/api`) — reuse it, with client-side rate limiting to stay a good internet citizen. |
| **OpenUSD → MaBoSS** | Greenfield | Binarize the complex's ΔG to active/inactive node state; emit a MaBoSS model (`.bnd`/`.cfg`) from USD. |
| **MaBoSS → OpenUSD** | Greenfield | Read MaBoSS output (node states/probabilities over time) back onto USD prims as time-sampled `bio:` attributes for joint MD + systems-biology consultation. |

## Codebase philosophy (project-wide)

We want a useful, reusable, not over-engineered, performant, low-footprint codebase — not chimera code. Draw inspiration and rationalized lessons from v8 rather than copying it: bring the valuable tools and hard-won lessons (e.g. falsification-resistant read-back testing — assert artifacts against independently-stated expectations derived from the source data, not from the generator's own in-memory state) and leave the rest. Strip-and-rebuild, or paying the cost of a refactor, is acceptable when it yields a better product. This holds for the whole project, not just this topic.

## Tooling & external resources

- **OpenUSD reference:** the `context7` MCP tools (`/websites/openusd_release`).
- **Python environment:** the forOUSD venv (`~/Documents/src/AOUSD/forOUSD/bin/python3`, Python 3.11.14) with the `load_env.sh` PYTHONPATH — it carries both `pxr` and `mdtraj`.
- **ΔG values:** the ddMut PPI API above, rate-limited client-side.
- **MaBoSS:** not on `context7`. Take install and API details from `https://maboss.curie.fr` and the pyMaBoSS repository (`sysbio-curie/pyMaBoSS`); its source may be cloned read-only into a gitignored `ro/` at the project root for easy local search, or searched via the GitHub MCP repo-search tools.

## Scope boundaries

- **In scope:** the Python prototype — the four pipelines and their integrated demonstration under `examples/p53_mdm2/`, with committed `.usda` artifacts and read-back tests as evidence.
- **Out of scope:** C++/schema authoring and CMake/CI/vcpkg revival (deferred per `restart`); rewriting the architecture doc's decisions (implement them, don't alter them).

## Done definition

The full end-to-end p53-mdm2 demonstration runs across all four pipelines, with committed `.usda` outputs and passing read-back tests as the unit of "done", built up over multiple cycles.
