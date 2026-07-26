# DDMut-PPI live capture — 2026-07-26

**Real server output.** Every file in this directory is a verbatim response body
from the DDMut-PPI public API, written unmodified by
`examples/p53_mdm2/converters/ddmut_client.py` at request time. Nothing here is
hand-written, reformatted, or reconstructed.

This directory is the evidence backing the `bio:ddgKcalPerMol` values on the
`Genotype` variants of `examples/p53_mdm2/composition/p53_mdm2_genotype.usda`.
Each variant carries `bio:ddgResponseFile`, naming the exact body its number was
read out of.

## Contents

| Path | What it is |
|---|---|
| `manifest.jsonl` | One row per HTTP exchange: URL, method, request encoding, request fields, HTTP status, elapsed seconds, body filename, byte count. |
| `NNN_<METHOD>_single.body.txt` | The verbatim response body for exchange `NNN`. |
| `ddmut_ppi_live_predictions.json` | Parsed ΔΔG per variant, **derived by script** from the bodies above (each entry names its `response_file`). |
| `encoding_diagnostic/` | Two-request proof of the cycle-006 root cause (below). |

## Captured predictions

Endpoint: `POST` + `GET https://biosig.lab.uq.edu.au/ddmut_ppi/api/single`,
structure `1YCR` via `pdb_accession`, chain `B`.
Convention: ΔΔG of binding in kcal/mol, negative = destabilizing.

| Variant | ΔΔG | position / WT → mutant | dist. to interface | Response body |
|---|---|---|---|---|
| F19A | −3.917 | 19 PHE → ALA | 3.017 Å | `008_GET_single.body.txt` |
| L26A | −2.948 | 26 LEU → ALA | 3.360 Å | `016_GET_single.body.txt` |
| W23A | −6.192 | 23 TRP → ALA | 2.831 Å | `024_GET_single.body.txt` |

The server-reported `position` / `wild-type` / `mutant` fields independently
agree with a flat-column re-parse of `data/structures/1ycr.pdb` chain B
(PHE 19, TRP 23, LEU 26) — so these responses are for the intended sites.

## Root cause of the cycles 002–005 failure

Earlier cycles could submit jobs (real `job_id`s came back) but every retrieval
returned `{"message": "Internal Server Error"}`, so no real prediction was ever
captured and a synthetic fixture stood in.

The cause was the **retrieval request encoding**, not server downtime. The
documented example is `curl .../api/single -X GET -F job_id=<id>` — `-F` puts
`job_id` in a **multipart form body**. The old client sent it as a URL query
string instead, which the server answers with HTTP 500.

`encoding_diagnostic/` proves this with two GETs against the *same already
completed* job (no new job submitted):

| File | Request | Result |
|---|---|---|
| `001_GET_single.body.txt` | `job_id` in multipart form body | HTTP 200, `status: DONE`, `prediction: -3.917` |
| `002_GET_single.body.txt` | `job_id` in URL query string | HTTP 500, `{"message": "Internal Server Error"}` |

One documented deviation: the in-progress sentinel arrives as
`{"job_id": ..., "status": "RUNNING"}`, whereas the docs describe
`message - RUNNING`. The client now inspects both fields.

## Good-internet-citizen notes

This is a free public academic service (Biosig Lab, University of Queensland).
The client enforces sequential requests with a ≥1 s client-side throttle and
exponentially backed-off polling. Only the three variants this project actually
uses were submitted — 3 jobs, 24 exchanges total, all HTTP 200. Do not run bulk
sweeps against this endpoint; the API offers dedicated batch endpoints
(`/list`, `/interface`) if many mutations are ever genuinely needed.

## Reproducing

```bash
. ./load_env.sh
PYTHONPATH="$PYTHONPATH:$(pwd)/examples" \
  /path/to/forOUSD/bin/python3 examples/p53_mdm2/converters/ddmut_client.py \
  --source live --max-wait 300
```

Re-running submits new jobs and appends new capture files; `job_id`s are
timestamp-derived and will differ. The offline fallback
(`composition/fixtures/ddmut_ppi_fixture.json`, clearly tagged synthetic) is
retained for use when the service is unreachable: `--source fixture` or
`--source auto`.
