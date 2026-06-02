"""Wikidata SPARQL fetcher.

Stages SPARQL query results as JSONL under
``${ETZ_DATASET_ROOT}/datasets-staging/wikidata-{query}-{captureTs}/``.

Two canonical queries are provided (callers can also pass a raw query
via `query_text=`):

  - ``legal-entities-with-lei`` — companies that have an ISO 17442 LEI.
    Feeds com.etzhayyim.maps.legalEntity Tier B seeds.
  - ``admin-areas`` — administrative subdivisions with WGS84 coords +
    ISO 3166-2 code. Feeds com.etzhayyim.maps.region Tier A seeds.

The query text is included verbatim in the FetchResult.source so the
datasetPin manifest row records the exact query that produced the
snapshot. SPARQL endpoint is mockable via the `client` parameter.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx

from . import FetchResult


DEFAULT_SPARQL_URL = "https://query.wikidata.org/sparql"
DEFAULT_USER_AGENT = "etzhayyim-e7m-dataset/0.0.1 (https://etzhayyim.com)"


# ─── canned queries (Phase 3 Tier B seeds) ──────────────────────────


QUERY_LEGAL_ENTITIES_WITH_LEI = """SELECT ?entity ?entityLabel ?lei ?countryCode ?inception WHERE {
  ?entity wdt:P31/wdt:P279* wd:Q4830453 .   # business enterprise (subclass*)
  ?entity wdt:P5305 ?lei .                  # LEI (ISO 17442)
  OPTIONAL { ?entity wdt:P17 ?country . ?country wdt:P297 ?countryCode . }
  OPTIONAL { ?entity wdt:P571 ?inception . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT %(limit)d
"""

QUERY_ADMIN_AREAS = """SELECT ?area ?areaLabel ?iso ?lat ?lng ?level WHERE {
  ?area wdt:P31/wdt:P279* wd:Q56061 .       # administrative territorial entity (subclass*)
  ?area wdt:P300 ?iso .                     # ISO 3166-2 code
  OPTIONAL {
    ?area wdt:P625 ?coords .
    BIND(GEOF:LATITUDE(?coords)  AS ?lat)
    BIND(GEOF:LONGITUDE(?coords) AS ?lng)
  }
  OPTIONAL { ?area wdt:P1612 ?level . }     # admin level
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT %(limit)d
"""


CANNED_QUERIES: dict[str, str] = {
    "legal-entities-with-lei": QUERY_LEGAL_ENTITIES_WITH_LEI,
    "admin-areas": QUERY_ADMIN_AREAS,
}


@dataclass
class WikidataFetchOpts:
    query_name: str
    limit: int = 5000
    sparql_url: str = DEFAULT_SPARQL_URL
    user_agent: str = DEFAULT_USER_AGENT
    timeout_sec: float = 120.0
    # Raw query override (skips CANNED_QUERIES). Useful for ad-hoc pulls.
    query_text: Optional[str] = None
    # Inject for tests.
    client: Optional[httpx.Client] = None


def fetch(staging_dir: Path, opts: WikidataFetchOpts) -> FetchResult:
    """Run the SPARQL query, write `result.jsonl` to the staging dir,
    return a FetchResult."""
    raw_query = opts.query_text or CANNED_QUERIES.get(opts.query_name)
    if not raw_query:
        raise KeyError(
            f"unknown query '{opts.query_name}'. Known: {list(CANNED_QUERIES)}"
        )
    query = raw_query % {"limit": opts.limit}

    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    name = f"wikidata:{opts.query_name}"
    dataset_dirname = f"wikidata-{opts.query_name}-{capture_ts}"
    out_dir = staging_dir / dataset_dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    # Capture the query verbatim for provenance — the datasetPin manifest
    # row links back to this file via `source.query_file`.
    (out_dir / "query.sparql").write_text(query, encoding="utf-8")

    owned_client = opts.client is None
    client = opts.client or httpx.Client(timeout=opts.timeout_sec)
    try:
        resp = client.post(
            opts.sparql_url,
            data=urllib.parse.urlencode({"query": query}),
            headers={
                "accept": "application/sparql-results+json",
                "content-type": "application/x-www-form-urlencoded",
                "user-agent": opts.user_agent,
            },
        )
        resp.raise_for_status()
        payload = resp.json()
    finally:
        if owned_client:
            client.close()

    bindings = payload.get("results", {}).get("bindings", [])
    jsonl_path = out_dir / "result.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in bindings:
            f.write(json.dumps(row, separators=(",", ":"), sort_keys=True))
            f.write("\n")

    # Revision = sha256 of (query || result body). Stable so re-fetch on
    # the same logical date yields the same revision iff Wikidata's
    # response is byte-identical.
    hasher = hashlib.sha256()
    hasher.update(query.encode("utf-8"))
    hasher.update(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    revision = f"sha256:{hasher.hexdigest()}"

    size_bytes = sum(
        p.stat().st_size for p in out_dir.iterdir() if p.is_file()
    )
    file_count = sum(1 for _ in out_dir.iterdir() if _.is_file())

    return FetchResult(
        name=name,
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "sparql",
            "endpoint": opts.sparql_url,
            "query_name": opts.query_name,
            "query_file": "query.sparql",
            "limit": opts.limit,
            "binding_count": len(bindings),
            "captured_at": capture_ts,
        },
    )


__all__ = [
    "CANNED_QUERIES",
    "DEFAULT_SPARQL_URL",
    "DEFAULT_USER_AGENT",
    "QUERY_ADMIN_AREAS",
    "QUERY_LEGAL_ENTITIES_WITH_LEI",
    "WikidataFetchOpts",
    "fetch",
]
