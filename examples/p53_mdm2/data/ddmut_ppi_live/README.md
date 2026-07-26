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
| `responses/` | **Canonical evidence.** One verbatim `DONE` body per variant, named `<variant>_<job_id>_DONE.json`. This is the authoritative set the pipeline cites and the test suite validates strictly. |
| `ddmut_ppi_live_predictions.json` | Curated ΔΔG per variant, **derived by script** from `responses/` (each entry names its `response_file`). Read by `--source captured`. |
| `encoding_diagnostic/` | Two-request proof of the cycle-006 root cause (below). |
| `run_<UTC>/` | Raw per-run capture: every exchange of one live run, plus its `manifest.jsonl` (URL, method, encoding, request fields, HTTP status, elapsed, byte count). Immutable once written. |
| `NNN_<METHOD>_single.body.txt`, `manifest.jsonl` (at root) | **Historical, not authoritative.** Raw bodies from the first two live runs, which both wrote into this root directory before per-run scoping existed and therefore interleaved (see the collision note below). Kept because every byte is genuine server output; not cited by anything. |

## Captured predictions

Endpoint: `POST` + `GET https://biosig.lab.uq.edu.au/ddmut_ppi/api/single`,
structure `1YCR` via `pdb_accession`, chain `B`.
Convention: ΔΔG of binding in kcal/mol, negative = destabilizing.

| Variant | ΔΔG | position / WT → mutant | dist. to interface | Canonical response body |
|---|---|---|---|---|
| F19A | −3.917 | 19 PHE → ALA | 3.017 Å | `responses/F19A_17850858889778712_DONE.json` |
| L26A | −2.948 | 26 LEU → ALA | 3.360 Å | `responses/L26A_17850859504748063_DONE.json` |
| W23A | −6.192 | 23 TRP → ALA | 2.831 Å | `responses/W23A_17850860117753787_DONE.json` |

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

## Why `responses/` exists separately (capture collision, 2026-07-26)

Capture filenames are numbered per client instance starting at `001`. When the
capture directory was a single shared folder, a second live run restarted at
`001` and **overwrote** the first run's bodies. That is not hypothetical: a
concurrent cycle-006 task re-ran the live path into this root directory at
17:24–17:26 UTC, overwriting bodies `001`–`008` of the 17:07 UTC run while that
run's results were mid-commit. The originally committed `008_GET_single.body.txt`
therefore holds a *different* job's `RUNNING` payload rather than the F19A
`DONE` payload it was cited for.

Two changes resolve it:

1. **Per-run scoping.** `new_run_capture_dir()` now gives every live run its own
   `run_<UTC>/` directory, so no run can renumber over another's evidence,
   regardless of concurrency.
2. **A canonical set.** `responses/` holds one immutable, byte-identical `DONE`
   body per variant, named with its own `job_id` so a filename can never drift
   from its payload. The curated predictions JSON cites only these, and the test
   suite checks that each cited body is a `DONE` payload whose `job_id`, `chain`
   and `prediction` match the citing entry *and* whose filename carries its own
   `job_id`.

The three canonical bodies were recovered byte-for-byte from committed history
(`b60e62d`) — F19A from `encoding_diagnostic/001_GET_single.body.txt`, which
holds that job's genuine `DONE` payload and was never touched by the collision;
L26A and W23A from `016`/`024`, which were also untouched. **No value was
re-queried, re-derived, or reconstructed** — the bytes are the server's original
response bytes, relocated and renamed.

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

Re-running submits new jobs into a fresh `run_<UTC>/` directory; `job_id`s are
timestamp-derived and will differ.

**Prefer `--source captured`** for anything that just needs the real values
back on the stage (re-running the pipeline, CI, a sibling task):

```bash
... examples/p53_mdm2/converters/ddmut_client.py --source captured
```

It replays the canonical bodies above with no network traffic at all, and tags
the prims `success` / `ddmut-ppi-live` because the numbers are genuine server
output — `bio:ddgLiveOutcome` records that it was a replay rather than a fresh
query. Use `--source live` only when a genuinely new prediction is wanted.

The offline fallback (`composition/fixtures/ddmut_ppi_fixture.json`, clearly
tagged synthetic) is retained for when the service is unreachable *and* no
capture exists: `--source fixture`, or the last resort of `--source auto`.
