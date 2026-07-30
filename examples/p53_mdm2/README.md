# examples/p53_mdm2

A runnable, multi-scale **p53–MDM2** demonstration in which OpenUSD is the shared representation tying molecular free-energy data to systems-biology (MaBoSS Boolean-network) modelling. Brief: `__threads__/p53-mdm2/INTENT.md`. Reuse map & architecture: `__reports__/p53-mdm2/00-architecture_v0.md`. Design vision: `__design__/openusd_for_research_architecture.md`.

> **Not a copy of `foundation_demo_v8/`.** v8 is inspiration only. Every module here is *extracted and generalized* per the reuse map — the ABL-specific hard-coded root prim path and the ABL dataset atom counts must never appear in this tree. The system root is a `root_path` parameter threaded through parser → assembly → clips → tests, and a static grep gate (`tests/test_anti_chimera.py`) enforces it.

## Run the whole thing

```bash
. ./load_env.sh                                   # PYTHONPATH for pxr, USDBIO_DATA_DIR
PYTHONPATH="$PYTHONPATH:$(pwd)/examples" \
  ~/Documents/src/AOUSD/forOUSD/bin/python3 \
  examples/p53_mdm2/demos/run_end_to_end.py       # all four hops + the composed stage

PYTHONPATH="$PYTHONPATH:$(pwd)/examples" \
  ~/Documents/src/AOUSD/forOUSD/bin/python3 \
  examples/p53_mdm2/tests/run_tests.py            # the full read-back suite
```

The entry point writes **`demos/p53_mdm2_integrated.usda`** — a single composed stage carrying all four pipelines. Inspect it with `usdcat --flatten demos/p53_mdm2_integrated.usda`, or open it in any USD viewer.

Useful flags:

| Flag | Effect |
|:--|:--|
| `--ddg-source captured` *(default)* | replay the committed **real** DDMut-PPI server predictions from `data/ddmut_ppi_live/`; no network |
| `--ddg-source live` | re-query the DDMut-PPI API (rate-limited client-side) |
| `--ddg-source fixture` | the synthetic offline fallback in `composition/fixtures/` — clearly tagged, never presented as measured |
| `--from-committed` | skip hops 1–3 and recompose from the committed artifacts (hop 4 still runs MaBoSS for real) |

## The four hops

Each hop is owned by one module; `demos/run_end_to_end.py` is orchestration plus the hop-5 composition only — it reimplements nothing.

| Hop | Pipeline | Module | In → Out |
|:--|:--|:--|:--|
| **1** | MD/structure → USD | `builders/build_assembly.py`, `converters/pdb_parser.py` | `data/structures/1ycr.pdb` → `output/p53_mdm2_topology.usda` (818 atoms, 2 chains, 98 residues, 834 bonds; `bio:element` + `/_class_/` inherits + a `representation` VariantSet) |
| **1b** | MD setup parameters | `templates/md_parameters.py` | the R01 reproducible parameter set → `output/p53_mdm2_md_setup.usda` (`bio:md:` deck, 17 CORE + 7 optional fields, units and per-field provenance in `customData`) |
| **2** | USD → ΔΔG | `composition/build_genotype.py`, `converters/ddmut_client.py` | a `Genotype` VariantSet over the p53 hydrophobic triad (Phe19/Trp23/Leu26 alanine scan, geometry built from real 1YCR coordinates) → DDMut-PPI → `bio:ddgKcalPerMol` + six-field provenance, authored **inside each variant's edit context** |
| **3** | ΔΔG → MaBoSS model | `maboss/dg_correlation.py`, `maboss/emit_model.py` | `S = 1/(1+exp(-k(ΔΔG−m)))` → the reference `.cfg` with **only** `$KMn_pMCD`/`$KMn_pMC` reset to `S` (the `.bnd` stays byte-identical) → `maboss/output/p53_Mdm2_<variant>.{bnd,cfg}` + the `bio:maboss:*` correlation contract back on the variant |
| **4** | MaBoSS → USD | `maboss/run_maboss.py`, `templates/build_analysis_layer.py` | a **real** MaBoSS 2.6.6 run → per-node probability trajectories → `analysis/p53_mdm2_analysis.usda`, time-sampled `bio:maboss:prob:<node>` over 500 frames on a separate Analysis SubLayer |
| **5** | integration | `demos/run_end_to_end.py` | the four layers → `demos/p53_mdm2_integrated.usda`: one composed stage + the `integration/` cross-pipeline join |

### Why hop 5 needs its own layer

`defaultPrim`, `metersPerUnit`, `upAxis` and the start/end time codes are resolved by USD from the **root layer only** — a sublayered Analysis layer's own time range does not propagate upward. So the integrated stage is a thin root layer that adds exactly four things and no pipeline data of its own:

1. the `subLayers` list (below),
2. the root-layer-only stage metadata,
3. a **Local**-arc `Genotype` variant selection — the "which hypothesis am I consulting" switch,
4. the `integration/` join.

The join exists because a variant's ΔΔG and `S` live *inside* that variant's edit context, so only one variant's values resolve at a time, whereas the MaBoSS trajectories sit on per-variant analysis prims that all resolve at once. The join is the single place where the whole sweep — input ΔΔG, correlated parameter, simulated outcome — is readable in one traversal. That is the "integrated MD + systems-biology consultation" the INTENT names as the done definition.

## LIVERPS mapping

Per `__design__/openusd_for_research_architecture.md` §2 and §4.1, strongest arc first:

| Arc | Research meaning (design doc) | Where this demo uses it |
|:--|:--|:--|
| **L** — Local + SubLayers | *The Lab Notebook* / departmental separation | The integrated stage's `subLayers` list **is** the departmental stack. Strongest first: `analysis/p53_mdm2_analysis.usda` (Analysis) → `composition/p53_mdm2_genotype.usda` (Perturbation) → `output/p53_mdm2_md_setup.usda` (Protocol) → `output/p53_mdm2_topology.usda` (Biology, weakest, reached transitively). Analysis is strongest so a re-analysis can override an earlier opinion without touching Biology; Biology is weakest because it is the ground truth every other layer annotates. The `integration/` join is a Local opinion in the root layer. |
| **I** — Inherits | *Biological taxonomy* | Every atom in hop 1 inherits its `bio:atomicMass`, `bio:vdwRadius`, `bio:covalentRadius`, `bio:electronegativity` and CPK `bio:cpkColor` from an element `class` prim under `/_class_/` (`builders/element_templates.py`). |
| **V** — VariantSets | *The Hypothesis* | Two of the design doc's three scientific patterns are live here. **Perturbation** (`Genotype`): one variant per p53-peptide alanine mutant, each carrying its own ΔΔG and correlated `S`. **Representation**: the canonical `points`/`balls`/`vdw`/`ballstick` visual-mode set on the atoms. (The **Ensemble** `ReplicaID` pattern is not exercised — see *Not yet done*.) |
| **E** — rElocates | path reorganization | Not used. |
| **R** — References | *Standard asset libraries* | Each `Genotype` variant authors a `Reference` on the mutation-site prim pointing at the geometry file that realises that genotype's residue (`composition/geometries/`). Swapping the variant swaps the referenced residue geometry. |
| **P** — Payloads | *The Raw Data* | Not used yet — there is no MD trajectory in this demo, only a crystal structure. Value Clips / Payloads are the growth path when a real p53–MDM2 trajectory lands. |
| **S** — Specializes | *specialized refinements* | Not used. |

## Departmental layering, verified

Mapping onto the design doc's §4.1 table:

| Research concern | Layer | Contributes |
|:--|:--|:--|
| **Biology** | `output/p53_mdm2_topology.usda` | topology, elements, bonds, `representation` variants |
| **Protocol** | `output/p53_mdm2_md_setup.usda` | the `bio:md:` setup deck on an `mdSetup` Scope |
| **Perturbation** | `composition/p53_mdm2_genotype.usda` | the `Genotype` VariantSet, ΔΔG, and the `bio:maboss:*` correlation contract |
| **Analysis** | `analysis/p53_mdm2_analysis.usda` | time-sampled `bio:maboss:prob:<node>` under a `maboss/` Scope |
| **Integration** | `demos/p53_mdm2_integrated.usda` | the composition itself + the `integration/` join |

Non-destructiveness is a tested claim, not an aspiration: every downstream layer brings the complex root in as an **`over`**, and `tests/test_integrated.py` opens the Biology layer *alone* and asserts it carries no `maboss/`, no `mdSetup`, no `integration/`, no `bio:ddg*` / `bio:md:` / `bio:maboss:` / `bio:demo:` attribute, and no `Genotype` VariantSet — while the composed stage still resolves all the atoms.

## The thesis, and the number that shows it

A destabilizing mutation weakens the p53:MDM2 interface (more negative ΔΔG), which the logistic maps to a smaller MDM2-antagonism parameter `S`, which in the Boolean model means less Mdm2N activity and therefore **more p53 up**. That ordering is fixed by the ΔΔG *inputs* alone, so it is falsifiable by a break at any hop.

Measured (real DDMut-PPI predictions; real MaBoSS 2.6.6 run; `seed_pseudorandom=100`, `thread_count=1`, 50 000 samples, 500 frames over `max_time=50`):

| Variant | ΔΔG (kcal/mol) | `S` | time-avg P(p53 up) |
|:--|--:|--:|--:|
| WildType | — (baseline) | — | 0.310018 |
| L26A | −2.948 | 0.519490 | 0.326081 |
| F19A | −3.917 | 0.201733 | 0.398497 |
| W23A | −6.192 | 0.008260 | 0.861467 |

Strictly increasing along the destabilization order, with `S` strictly decreasing — asserted in `integrated_destabilization_ordering` against three independent read-outs (the Analysis layer's raw time samples, the join row, and a fresh MaBoSS re-run). The wild type carries **no** ΔΔG and **no** `S`: the reference `.cfg` *is* the WT model (`$KMn_pMC* = 1`), so it is tagged `baseline` rather than given a fabricated `0.0`.

## Testing discipline

`tests/run_tests.py` runs everything (**39 checks**). The rule, inherited from v8's hard-won lesson and restated in the INTENT: **read-back tests assert committed artifacts against expectations derived independently from the source data — never against the generator's own in-memory state.** `tests/test_integrated.py` imports attribute *names* from the demo module and no values, and uses one independent oracle per hop:

| Hop | Oracle |
|:--|:--|
| 1 | `tests/independent_pdb.py` — re-derives atom/chain/element counts from `1ycr.pdb` by flat column slicing, a different code path from `converters/pdb_parser.py` |
| 2 | the **verbatim captured DDMut-PPI response body** named by `bio:ddgResponseFile`, read with plain `json.load` (never via `ddmut_client`); a `fixture`-sourced ΔΔG is checked against the fixture JSON instead. The oracle is dispatched on the lineage the *stage* declares, so it follows Pipeline 2's live-vs-fixture choice instead of pinning one |
| 3 | the logistic recomputed inline with `math.exp` — `dg_correlation` is deliberately *not* called — from the ΔΔG and the `(m, k)` both read off the composed stage |
| 4 | a fresh `run_maboss.run_all()`; MaBoSS is deterministic here, so a re-run is a valid oracle |

If MaBoSS cannot run, the affected checks report an **honest skip** — never a pass on fabricated data. Layers: `compliance` (usdchecker), `domain`, `readback`, `unit-correlation`, `readback-ddg`, `readback-md`, `readback-maboss`, `readback-maboss-p4`, `integrated-p5`, `anti-chimera`.

## Layout

```
examples/p53_mdm2/
  README.md              # this file
  p53_env.py             # paths + the parameterized DEFAULT_ROOT_PATH (no ABL literal)
  data/                  # element/ion/residue biochemistry; structures/1ycr.pdb
  data/ddmut_ppi_live/   # VERBATIM DDMut-PPI response bodies (live-capture evidence)
  converters/            # pdb_parser, ddmut_client (rate-limited, stdlib-only)
  builders/              # element_templates, build_assembly (root_path param)
  composition/           # build_genotype (Perturbation VariantSet), provenance, geometries/
  templates/             # md_parameters (bio:md:), build_analysis_layer (P4)
  maboss/                # dg_correlation, emit_model, run_maboss; reference/, output/
  demos/                 # run_end_to_end.py + the committed integrated .usda   <-- P5
  tests/                 # the 39-check anti-tautology read-back harness
  cluster/               # GROMACS container scaffold (PI-gated; nothing built or submitted)
  output/, analysis/     # committed .usda artifacts (evidence of "done")
```

## Key external inputs

- **Starting structure:** [1YCR](https://www.rcsb.org/structure/1YCR) — native p53 transactivation peptide (chain B, triad Phe19/Trp23/Leu26) bound to the MDM2 N-terminal domain (chain A).
- **MaBoSS model:** the 5-node `p53_Mdm2` DNA-damage oscillator (`p53`, `p53_h`, `Mdm2C`, `Mdm2N`, `Dam`), fetched verbatim from `maboss.curie.fr/files/p53Dam/` into `maboss/reference/`.
- **ΔΔG:** [DDMut-PPI](https://biosig.lab.uq.edu.au/ddmut_ppi/api) — async submit/poll, ΔΔG in kcal/mol, negative = destabilizing.
- **Correlation constants:** `m = −3.0 kcal/mol`, `k = 1.5 /(kcal/mol)` are **explicitly ad-hoc placeholders** from `__reports__/p53-mdm2/02-dg_maboss_correlation_v0.md` (PI Q-002). Both are parameters everywhere, so a re-fit is a data edit, not a code change.

## Environment

Runs under the forOUSD venv (`~/Documents/src/AOUSD/forOUSD/bin/python3`, Python 3.11.14) with `load_env.sh` on `PYTHONPATH` — it carries both `pxr` and `mdtraj`. MaBoSS comes from the standalone colomoto binary (`python -c "import maboss_setup"`); the in-process `cmaboss` backend is *not* used (it returned empty node sets on this machine — see the `run_maboss` module docstring).

## Not yet done

- **No MD trajectory.** The demo runs on a crystal structure. Payloads / Value Clips and the `ReplicaID` Ensemble VariantSet are the growth path once a real p53–MDM2 trajectory exists. The GROMACS route is no longer scaffolding: `cluster/` has **a delivered runtime** — `/home/eliott/p53mdm2/gromacs.sif` (GROMACS 2025.3, `sm_70;sm_90`), observed executing on a banyan H100 and observed opening under dgx1's older Singularity — but **no p53–MDM2 MD simulation has ever run**, on any cluster. What has run is a smoke-test water box. See `cluster/README.md` for the delivered state and what remains PI-gated (the dgx1 GPU run, a cold-cache rebuild, the last of the build scratch).
- **The ΔΔG→`S` correlation is a placeholder shape.** The logistic is monotone and invertible, which is all the mechanism needs, but `m` and `k` are not fitted to anything.
- **No Review layer.** The design doc's fifth department (annotations, cameras, PI comments) is not authored.
