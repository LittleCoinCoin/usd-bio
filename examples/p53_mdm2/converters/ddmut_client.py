#!/usr/bin/env python3
"""
ddmut_client.py -- Pipeline 2 Step 2: a rate-limited DDMut-PPI client and a
ddG write-back that records the result onto Genotype variants as ``bio:``
attributes with six-field provenance.

DDMut-PPI API (confirmed from the API page, not guessed):
  - Single-mutation submit:  POST {base}/single  with fields
        pdb_accession (or pdb_file), chain (required), mutation (required),
        Reverse (optional), email (optional)  ->  JSON {"job_id": "..."}
  - Single-mutation retrieve: GET {base}/single?job_id=...  ->  completed JSON
        with fields job_id, status, prediction (ddG kcal/mol, negative =
        destabilizing), chain, position, wild-type, mutant, ...; in-progress
        returns {"message": "RUNNING"}.
  [source: https://biosig.lab.uq.edu.au/ddmut_ppi/api]

Good-internet-citizen policy (enforced here):
  - Sequential requests only, with a client-side throttle of >= MIN_INTERVAL_S
    (default 1.0 s) between ANY two HTTP calls.
  - Backed-off polling for job completion (exponential, capped).
  - A descriptive User-Agent identifying the project and a contact.

Error model (NON-NEGOTIABLE):
  A submit/poll failure, timeout, or an unreachable/erroring API surfaces as an
  explicit ``unavailable``/``unknown`` status with ``prediction=None`` -- NEVER
  a fabricated ddG. The write-back writes NO numeric ``bio:ddgKcalPerMol`` when
  no real value exists; the honest status tag is written instead.

Live-vs-fixture (see write_back_ddg): the write-back can run against the live
API (``source="live"``), a committed fixture (``source="fixture"``), or attempt
live and fall back to the fixture (``source="auto"``). Fixture values are
clearly tagged (``bio:ddgStatus="fixture"``, ``bio:ddgSource="fixture"``) and
are NEVER presented as server output.

Only the standard library is used (urllib) -- the forOUSD venv has no
``requests`` and this keeps the client dependency-free.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from urllib import request as _urlrequest
from urllib import parse as _urlparse
from urllib.error import HTTPError, URLError

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_PARENT = os.path.dirname(os.path.dirname(_HERE))  # examples/
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_BASE_URL = "https://biosig.lab.uq.edu.au/ddmut_ppi/api"
DEFAULT_USER_AGENT = (
    "usd-bio-research/0.1 (p53-mdm2 OpenUSD pipeline; "
    "https://github.com/LittleCoinCoin/usd-bio; contact eliott.jacopin@riken.jp)"
)
MIN_INTERVAL_S = 1.0          # >= 1 request/second (good citizen)
DEFAULT_TIMEOUT_S = 30.0      # per-request socket timeout
DEFAULT_MAX_POLL_S = 180.0    # give up polling after this many seconds

_RUNNING_TOKENS = ("RUNNING", "PENDING", "QUEUED", "IN PROGRESS", "PROCESSING")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
@dataclass
class DDMutResult:
    """Outcome of a single-mutation ddG query.

    ``prediction`` is a float ONLY on ``status == "success"``; it is ``None`` for
    every failure/unavailable path (the error-model invariant -- never a
    fabricated ddG).
    """
    mutation: str
    chain: str
    prediction: Optional[float] = None
    status: str = "unknown"        # "success" | "unavailable" | "unknown"
    job_id: Optional[str] = None
    detail: str = ""
    timestamp: str = field(default_factory=_now_iso)
    raw: Optional[dict] = None


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
class DDMutClient:
    """Rate-limited DDMut-PPI single-mutation client (stdlib urllib only)."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        user_agent: str = DEFAULT_USER_AGENT,
        min_interval_s: float = MIN_INTERVAL_S,
        timeout_s: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.min_interval_s = float(min_interval_s)
        self.timeout_s = float(timeout_s)
        self._last_request_t = 0.0

    # -- throttle: enforce >= min_interval between any two HTTP calls --
    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_t
        wait = self.min_interval_s - elapsed
        if wait > 0:
            time.sleep(wait)

    def _finish_request(self) -> None:
        self._last_request_t = time.monotonic()

    @staticmethod
    def _encode_multipart(fields: Dict[str, str]) -> tuple:
        boundary = "----usdbio" + uuid.uuid4().hex
        parts = []
        for key, value in fields.items():
            parts.append("--" + boundary)
            parts.append(f'Content-Disposition: form-data; name="{key}"')
            parts.append("")
            parts.append(str(value))
        parts.append("--" + boundary + "--")
        parts.append("")
        body = "\r\n".join(parts).encode("utf-8")
        return body, f"multipart/form-data; boundary={boundary}"

    def _http(self, method: str, path: str, *,
              fields: Optional[dict] = None,
              params: Optional[dict] = None) -> tuple:
        """Perform one throttled HTTP call. Returns (status_code, parsed_json).

        A non-2xx response whose body is JSON is returned as (code, json) rather
        than raised, so the caller can read an API error message (e.g.
        {"message": "Internal Server Error"}). Network-level failures raise.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        data = None
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        if params:
            url = url + "?" + _urlparse.urlencode(params)
        if fields is not None:
            data, content_type = self._encode_multipart(fields)
            headers["Content-Type"] = content_type

        req = _urlrequest.Request(url, data=data, headers=headers, method=method)
        self._throttle()
        try:
            with _urlrequest.urlopen(req, timeout=self.timeout_s) as resp:
                code = resp.getcode()
                body = resp.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            code = exc.code
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        finally:
            self._finish_request()

        try:
            parsed = json.loads(body) if body.strip() else {}
        except json.JSONDecodeError:
            parsed = {"_nonjson_body": body[:400]}
        return code, parsed

    @staticmethod
    def _looks_running(payload: dict) -> bool:
        msg = str(payload.get("message", "")).upper()
        return any(tok in msg for tok in _RUNNING_TOKENS)

    def submit_single(
        self, mutation: str, chain: str, *,
        pdb_accession: Optional[str] = None,
        pdb_file: Optional[str] = None,
        reverse: bool = False,
    ) -> Optional[str]:
        """Submit one single-mutation job. Returns the job_id, or None on failure."""
        if not (pdb_accession or pdb_file):
            raise ValueError("submit_single needs pdb_accession or pdb_file")
        fields = {"chain": chain, "mutation": mutation}
        if pdb_accession:
            fields["pdb_accession"] = pdb_accession
        if pdb_file:
            fields["pdb_file"] = pdb_file
        if reverse:
            fields["Reverse"] = "True"
        code, payload = self._http("POST", "single", fields=fields)
        job_id = payload.get("job_id")
        return str(job_id) if job_id else None

    def poll_single(
        self, job_id: str, *,
        max_wait_s: float = DEFAULT_MAX_POLL_S,
        initial_backoff_s: float = 2.0,
        backoff_factor: float = 1.6,
        max_backoff_s: float = 20.0,
    ) -> Optional[dict]:
        """Backed-off polling for a completed job.

        Returns the completed payload (dict containing ``prediction``), or None
        if the job never completed within ``max_wait_s`` or the retrieval
        endpoint erred. NEVER invents a value.
        """
        deadline = time.monotonic() + max_wait_s
        backoff = initial_backoff_s
        while time.monotonic() < deadline:
            code, payload = self._http("GET", "single", params={"job_id": job_id})
            if isinstance(payload, dict) and payload.get("prediction") is not None:
                return payload
            if self._looks_running(payload):
                pass  # still computing -- keep polling
            # else: an error message (e.g. Internal Server Error) or empty ->
            # keep trying until the deadline, then give up honestly.
            time.sleep(min(backoff, max(0.0, deadline - time.monotonic())))
            backoff = min(backoff * backoff_factor, max_backoff_s)
        return None

    def query_single(
        self, mutation: str, chain: str, *,
        pdb_accession: Optional[str] = None,
        pdb_file: Optional[str] = None,
        reverse: bool = False,
        max_wait_s: float = DEFAULT_MAX_POLL_S,
    ) -> DDMutResult:
        """Submit + poll one mutation. Returns a DDMutResult, never raising for
        network/server issues (those become status='unavailable')."""
        try:
            job_id = self.submit_single(
                mutation, chain, pdb_accession=pdb_accession,
                pdb_file=pdb_file, reverse=reverse)
        except (HTTPError, URLError, OSError) as exc:
            return DDMutResult(mutation, chain, status="unavailable",
                               detail=f"submit failed: {exc}")
        if not job_id:
            return DDMutResult(mutation, chain, status="unavailable",
                               detail="submit returned no job_id")

        try:
            payload = self.poll_single(job_id, max_wait_s=max_wait_s)
        except (HTTPError, URLError, OSError) as exc:
            return DDMutResult(mutation, chain, status="unavailable",
                               job_id=job_id, detail=f"poll failed: {exc}")
        if payload is None:
            return DDMutResult(
                mutation, chain, status="unavailable", job_id=job_id,
                detail="retrieve endpoint did not return a prediction "
                       "within timeout")
        try:
            prediction = float(payload["prediction"])
        except (KeyError, TypeError, ValueError):
            return DDMutResult(mutation, chain, status="unavailable",
                               job_id=job_id, detail="prediction not numeric",
                               raw=payload)
        return DDMutResult(mutation, chain, prediction=prediction,
                           status="success", job_id=job_id, raw=payload)


# ---------------------------------------------------------------------------
# Fixture loader (clearly-labelled, NOT server output)
# ---------------------------------------------------------------------------
def default_fixture_path() -> str:
    return os.path.join(
        _PKG_PARENT, "p53_mdm2", "composition", "fixtures",
        "ddmut_ppi_fixture.json")


def load_fixture(path: Optional[str] = None) -> dict:
    """Load the committed ddG fixture. Returns {mutation: prediction_float}."""
    path = path or default_fixture_path()
    with open(path, "r") as fh:
        doc = json.load(fh)
    preds = doc.get("predictions", {})
    return {mut: float(v["prediction"]) for mut, v in preds.items()}


# ---------------------------------------------------------------------------
# Write-back: record ddG + provenance onto each Genotype variant
# ---------------------------------------------------------------------------
def write_back_ddg(
    genotype_path: str,
    *,
    source: str = "auto",              # "live" | "fixture" | "auto"
    pdb_accession: str = "1YCR",
    client: Optional[DDMutClient] = None,
    fixture_path: Optional[str] = None,
    max_wait_s: float = DEFAULT_MAX_POLL_S,
    verbose: bool = True,
) -> dict:
    """Write ddG + six-field provenance onto every mutant Genotype variant.

    For each variant other than the wild type, reads ``bio:mutation`` and
    ``bio:mutationChain`` off the composed stage, obtains a ddG per *source*,
    and authors -- inside that variant's edit context -- ``bio:ddgKcalPerMol``
    (only when a real/fixture value exists), the honest status/source tags, and
    the six ``bio:`` provenance fields.

    source:
        "live"    -- query the DDMut-PPI API; failures => status 'unavailable',
                     no numeric written.
        "fixture" -- use the committed fixture; tags 'fixture'.
        "auto"    -- attempt live; on live failure fall back to the fixture
                     (clearly tagged 'fixture'), recording the live outcome in
                     ``bio:ddgLiveOutcome``.

    Returns a summary dict {mutation: {status, source, prediction}}.
    """
    from pxr import Usd, Sdf
    from p53_mdm2.composition.provenance import (
        apply_provenance_metadata, ddmut_provenance_record, UNKNOWN)

    if source not in ("live", "fixture", "auto"):
        raise ValueError(f"source must be live|fixture|auto, got {source!r}")

    fixture = {}
    if source in ("fixture", "auto"):
        try:
            fixture = load_fixture(fixture_path)
        except FileNotFoundError:
            if source == "fixture":
                raise

    if client is None and source in ("live", "auto"):
        client = DDMutClient()

    stage = Usd.Stage.Open(genotype_path)
    root = stage.GetDefaultPrim()
    chain = root.GetAttribute("bio:mutationChain").Get()
    genotype = root.GetVariantSets().GetVariantSet("Genotype")
    summary = {}

    for variant in genotype.GetVariantNames():
        genotype.SetVariantSelection(variant)
        mutation = root.GetAttribute("bio:mutation").Get()
        if not mutation or mutation == "none":
            continue  # wild-type baseline has no mutation to query

        prediction = None
        status = "unknown"
        ddg_source = "none"
        job_id = None
        live_outcome = ""

        # --- obtain a value honestly ---
        if source in ("live", "auto"):
            result = client.query_single(
                mutation, str(chain), pdb_accession=pdb_accession,
                max_wait_s=max_wait_s)
            job_id = result.job_id
            live_outcome = f"{result.status}: {result.detail}".strip(": ")
            if result.status == "success":
                prediction = result.prediction
                status = "success"
                ddg_source = "ddmut-ppi-live"

        if prediction is None and source in ("fixture", "auto") and mutation in fixture:
            prediction = fixture[mutation]
            status = "fixture"
            ddg_source = "fixture"

        if prediction is None and status != "success":
            # nothing real available -> explicit unavailable, no numeric
            status = "unavailable" if source != "fixture" else "unknown"

        # --- author onto the variant (inside its edit context) ---
        with genotype.GetVariantEditContext():
            root.CreateAttribute("bio:ddgStatus", Sdf.ValueTypeNames.Token).Set(status)
            root.CreateAttribute("bio:ddgSource", Sdf.ValueTypeNames.Token).Set(ddg_source)
            root.CreateAttribute("bio:ddgUnits", Sdf.ValueTypeNames.Token).Set("kcal/mol")
            root.CreateAttribute("bio:ddgJobId", Sdf.ValueTypeNames.String).Set(job_id or UNKNOWN)
            if source in ("live", "auto"):
                root.CreateAttribute("bio:ddgLiveOutcome", Sdf.ValueTypeNames.String).Set(
                    live_outcome or UNKNOWN)
            if prediction is not None:
                # numeric written ONLY when a real/fixture value exists
                root.CreateAttribute("bio:ddgKcalPerMol", Sdf.ValueTypeNames.Float).Set(
                    float(prediction))

            record = ddmut_provenance_record(
                source_pdb=pdb_accession or UNKNOWN,
                mutation=mutation, chain=str(chain),
                endpoint=f"{DEFAULT_BASE_URL}/single",
                timestamp=_now_iso())
            apply_provenance_metadata(root, record)

        summary[mutation] = {
            "status": status, "source": ddg_source,
            "prediction": prediction, "job_id": job_id,
            "live_outcome": live_outcome,
        }
        if verbose:
            val = f"{prediction:+.3f} kcal/mol" if prediction is not None else "(none)"
            print(f"  {mutation:6s} status={status:11s} source={ddg_source:14s} "
                  f"ddG={val}")

    genotype.SetVariantSelection("WildType")
    stage.GetRootLayer().Save()
    if verbose:
        print(f"[write_back_ddg] saved: {genotype_path}")
    return summary


if __name__ == "__main__":
    import argparse
    from p53_mdm2.composition.build_genotype import default_output_path

    ap = argparse.ArgumentParser(description="ddMut-PPI ddG write-back")
    ap.add_argument("--source", choices=("live", "fixture", "auto"),
                    default="auto")
    ap.add_argument("--stage", default=default_output_path())
    ap.add_argument("--max-wait", type=float, default=DEFAULT_MAX_POLL_S)
    args = ap.parse_args()

    print(f"[ddmut_client] write-back source={args.source} stage={args.stage}")
    write_back_ddg(args.stage, source=args.source, max_wait_s=args.max_wait)
