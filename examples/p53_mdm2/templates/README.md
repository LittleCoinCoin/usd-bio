# USDBio MD-Setup-Parameter Representation (`bio:md:`)

P1b Step 1. This package (`p53_mdm2.templates.md_parameters`) represents the
**MD setup parameters** of a molecular-dynamics simulation as typed USD
attributes, so a run is reproducible from the USD stage alone and serialises
losslessly to an **MDDB** (EU Molecular Dynamics Data Bank) YAML key-value tree.

The schema is transcribed faithfully from the cycle-001 survey
`[source: __reports__/p53-mdm2/01-md_reproducibility_survey_v0.md]` (R01), which
derived it from the real ShinobuLab GENESIS decks and aligned the field
semantics with MDDB deliverable D1.1 and the LiveCoMS reporting checklist.

## Carrying prim & layer (decision)

- **Prim:** one dedicated `Scope` prim at `<root>/mdSetup` (default root
  `/p53_MDM2_complex`, parameterised — never an ABL literal).
- **Layer:** the **Protocol departmental layer**. The committed artifact
  (`output/p53_mdm2_md_setup.usda`) `subLayers` the Biology topology
  (`p53_mdm2_topology.usda`), so `mdSetup` composes onto the same complex root —
  a working demonstration of the CLAUDE.md departmental-layering pattern
  (Protocol over Biology).
- **Why not stage-level metadata:** stage metadata is a flat, untyped, unit-less
  blob that cannot be queried per-attribute, carry per-value units/provenance,
  or be versioned/loaded independently. A dedicated prim gives typed, unit-
  bearing, individually-provenanced attributes that map 1:1 onto MDDB's key-value
  tree `[source: R01 "Recommended bio:md: Attribute Schema" / "Where it sits"]`.

## Units & source tags

MDDB mandates a unit on every value `[source: R01 §Design Rationale "Units"]`.
USD has no per-attribute unit primitive (except length), so every non-string
attribute carries its unit in `customData["unit"]`. Every attribute also carries
`customData["source"]`, tagged either `[source: R01 ...]` (grounded in the
survey) or `[assumption: ...]` (a value the survey does not fix) — so the
artifact is self-documenting and each value's provenance is inline and auditable.

## CORE set (17 attributes — mandatory)

R01's ~15-field "conceptual-reproducibility" core (MDDB D1.1 §1 ∩ LiveCoMS
checklist) **plus** the two fields the PI promoted to CORE in Q-003 because they
are **not derivable from geometry**
`[source: __threads__/p53-mdm2/QUESTIONS.md Q-003 answer, PI 2026-07-12]`.

| `bio:md:` attribute | USD type | Unit | p53-MDM2 reference value | MDDB / checklist basis |
|---|---|---|---|---|
| `engine` | string | — | `GENESIS` | program name, mandatory (D1.1 §5) |
| `engineVersion` | string | — | `unknown` (from job env) | program version, mandatory (D1.1 §5) |
| `forceField` | string | — | `AMBER ff19SB` | force field name (D1.1 §1) |
| `waterModel` | string | — | `TIP3P` | solvent / checklist water (D1.1 §1; §4a) |
| `ensemble` | token | — | `NVT` | ensemble / conditions (D1.1 §1) |
| `integrator` | string | — | `VRES` | algorithm (D1.1 §5) |
| `timestep` | double | ps | `0.0035` | timestep (D1.1 §1) |
| `nSteps` | int64 | steps | `600000` | total length (D1.1 §1) |
| `temperature` | double | K | `310.0` | thermostat reference T (D1.1 §4.2) |
| `thermostat` | string | — | `Bussi` | T-coupling algorithm (D1.1 §1; §4b) |
| `barostat` | string | — | `Bussi` | P-coupling algorithm (D1.1 §1; §4b) |
| `pressure` | double | atm | `1.0` | conditions (D1.1 §1) |
| `electrostatics` | token | — | `PME` | electrostatics algorithm (D1.1 §1) |
| `cutoff` | double | Å | `8.0` | nonbonded cutoff (D1.1 §1; §4b) |
| `constraintAlgorithm` | string | — | `SHAKE` | constraint algorithm (D1.1 §1) |
| **`ionConcentration`** ⭐ | double | mol/L | `0.15` *(assumption)* | salt concentration (LiveCoMS §4a) |
| **`protonationState`** ⭐ | string | — | `standard states at pH 7.0` *(assumption)* | protonation state (LiveCoMS §4b) |

⭐ = **PI-promoted to CORE (Q-003)**. The methodology values are the ShinobuLab
GENESIS reference protocol the project adopts for its planned p53-MDM2 run
`[source: R01 §"What the ShinobuLab lab actually records"]`. `ionConcentration`,
`protonationState`, and `ionSpecies` are `[assumption:]` — they are p53-MDM2
system-composition choices the survey does not fix.

Plus one anchor attribute: `bio:md:startingStructure = "1YCR"` (the carry-over
back to the source structure, per R01 provenance).

## OPTIONAL extension block

Authored only when a value is available. Methodology detail that sharpens
reproducibility but is not part of the minimal core.

| `bio:md:` attribute | USD type | Unit | Value | Basis |
|---|---|---|---|---|
| `ionSpecies` | string | — | `NaCl` *(assumption)* | companion to `ionConcentration` |
| `boxType` | token | — | `PBC` | R01 (`type=PBC`) |
| `pairlistDist` | double | Å | `10.0` | R01 (`pairlistdist=10.0`) |
| `dispersionCorrection` | string | — | `EPRESS` | R01 (`dispersion_corr`) |
| `hydrogenMassRepartitioning` | bool | — | `true` | R01 (`hydrogen_mr=YES`) |
| `hmrRatio` | double | — | `3.0` | R01 (`hmr_ratio=3.0`) |
| `gammaT` | double | 1/ps | `1.0` | R01 Langevin friction (`gamma_t`) |

## REMD growth path (documented, not authored this cycle)

R01 designs a nested `bio:md:remd:` block for replica-exchange runs (the
ShinobuLab workflow is 2D gREST/REUS). Its field list is published in
`md_parameters.REMD_FIELDS` (`remd:method`, `remd:dimensions`, `remd:nReplicas`,
`remd:exchangePeriod`) and authored **only** when a caller supplies a real
`remd=` spec to `author_md_setup`. It is deliberately **not** written into the
conventional-production p53-MDM2 artifact this cycle: copying ShinobuLab's
ABL-specific 288-replica ladder onto p53-MDM2 would be fabrication. The
replica-exchange replicas map onto the project's existing Ensemble variant
pattern (`ReplicaID`) when the project runs its own REMD `[source: R01
§"Optional extension — replica exchange"]`.

## Provenance

Reuses the six-field `bio:` provenance schema from
`p53_mdm2.composition.provenance` (no re-invention) to record the parameter
deck's lineage, satisfying MDDB's provenance-record intent (D1.1 §3).

## Usage

```bash
. ./load_env.sh
PYTHONPATH="$PYTHONPATH:$(pwd)/examples" \
  ~/Documents/src/AOUSD/forOUSD/bin/python3 \
  examples/p53_mdm2/templates/md_parameters.py         # (re)build the artifact

PYTHONPATH="$PYTHONPATH:$(pwd)/examples" \
  ~/Documents/src/AOUSD/forOUSD/bin/python3 \
  examples/p53_mdm2/tests/run_tests.py                 # read-back tests
```

The read-back test (`tests/test_md_setup_readback.py`) is falsification-resistant:
it asserts the fresh-opened USD against an **independently** hand-transcribed
manifest (`templates/fixtures/md_setup_reference.json`) and against in-test R01
anchors — never against the generator's own state.
