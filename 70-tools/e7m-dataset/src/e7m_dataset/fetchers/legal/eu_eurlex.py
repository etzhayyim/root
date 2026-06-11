"""EU EUR-Lex (CELLAR SPARQL) fetcher — W1 anchor (ADR-2605262800).

EUR-Lex publishes EU treaties, regulations, directives, decisions and CJEU case
law for **free reuse with citation** (A-compatible). The open machine surface is
the CELLAR SPARQL endpoint:

  https://publications.europa.eu/webapi/rdf/sparql

A SELECT returns ``application/sparql-results+json``:

  {"results":{"bindings":[
     {"celex":{"value":"32016R0679"},
      "title":{"value":"Regulation (EU) 2016/679 ... (GDPR)"},
      "date":{"value":"2016-04-27"},
      "work":{"value":"http://publications.europa.eu/resource/celex/32016R0679"}},
     ...]}}

→ normalized statute NDJSON (see ``legal._common``). ``lawType`` is derived from
the CELEX descriptor letter (R→regulation, L→directive, D→decision, …). recordId
= ``EU:<celex>``. Buckets: ``law/statutes/eu-eurlex/<rev>/`` (legislation) +
``law/cases/eu-cjeu/<rev>/`` (sector-6 CELEX). Sensor: ``legal_statute_sensor``.

local_source accepts the SPARQL-results JSON or a JSON/NDJSON re-stage. Passive-
only (ADR-2605262400 §7): network mode bounds the SELECT with ``max_records``
(LIMIT) — no unbounded corpus dump.
"""

from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

from .. import FetchResult
from . import _common

DEFAULT_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
CELEX_BASE = "http://publications.europa.eu/resource/celex"
LICENSE_ID = "EUR-Lex-free-reuse-with-citation"
TIER = "A"

# CELEX descriptor letter → normalized lawType.
_CELEX_TYPE = {
    "R": "regulation", "L": "directive", "D": "decision", "H": "recommendation",
    "M": "treaty", "A": "treaty", "C": "communication", "J": "judgment",
    "B": "budget", "X": "other",
}

_DEFAULT_SELECT = """
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
PREFIX dct: <http://purl.org/dc/terms/>
SELECT DISTINCT ?work ?celex ?title ?date WHERE {{
  ?work cdm:resource_legal_id_celex ?celex .
  OPTIONAL {{ ?work cdm:work_date_document ?date . }}
  OPTIONAL {{ ?exp cdm:expression_belongs_to_work ?work ;
                  cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> ;
                  cdm:expression_title ?title . }}
}}
ORDER BY DESC(?date)
LIMIT {limit} OFFSET {offset}
""".strip()


@dataclass
class EuEurlexFetchOpts:
    endpoint: str = DEFAULT_ENDPOINT
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 180.0
    local_source: Optional[Path] = None
    sparql: Optional[str] = None      # override SELECT (must expose ?celex ?title ?date)
    page_size: int = 100
    max_records: Optional[int] = None
    client: Optional[Any] = None      # httpx.Client (lazy)


def _bval(binding: dict, key: str) -> Optional[str]:
    cell = binding.get(key)
    if isinstance(cell, dict):
        v = cell.get("value")
        return str(v).strip() if v not in (None, "") else None
    if cell not in (None, ""):
        return str(cell).strip()
    return None


def _celex_law_type(celex: str) -> tuple[str, str]:
    """Return (lawType, bucket) from a CELEX id (sector 6 = CJEU case law)."""
    sector = celex[:1]
    letters = "".join(c for c in celex[5:9] if c.isalpha())[:1].upper()
    if sector == "6":
        return "judgment", "cases/eu-cjeu"
    return _CELEX_TYPE.get(letters, "regulation"), "statutes/eu-eurlex"


def _normalize(binding: dict) -> Optional[dict]:
    celex = _bval(binding, "celex")
    if not celex:
        return None
    law_type, bucket = _celex_law_type(celex)
    work = _bval(binding, "work") or f"{CELEX_BASE}/{celex}"
    src = f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}"
    return {
        "recordId": f"EU:{celex}",
        "jurisdiction": "EU",
        "lawId": celex,
        "title": _bval(binding, "title"),
        "lawType": law_type,
        "bucket": bucket,
        "promulgatedDate": _common.coerce_iso_date(_bval(binding, "date")),
        "effectiveDate": None,
        "revision": _bval(binding, "date"),
        "lang": "en",
        "license": LICENSE_ID,
        "sourceUrl": src,
        "payloadCid": work,
        "bodyExcerpt": None,
    }


def _iter_results(payload: Any) -> Iterator[dict]:
    """Yield normalized rows from a SPARQL-results JSON object (or normalized re-stage)."""
    if isinstance(payload, dict):
        bindings = (payload.get("results") or {}).get("bindings")
        if isinstance(bindings, list):
            for b in bindings:
                if isinstance(b, dict):
                    row = _normalize(b)
                    if row is not None:
                        yield row
            return
        if _common.already_normalized(payload):
            yield payload
            return
    if isinstance(payload, list):
        for r in payload:
            if _common.already_normalized(r):
                yield r
            elif isinstance(r, dict):
                row = _normalize(r)
                if row is not None:
                    yield row


def _iter_local(path: Path) -> Iterator[dict]:
    raw = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        for line in raw.splitlines():
            s = line.strip()
            if not s:
                continue
            try:
                row = json.loads(s)
            except json.JSONDecodeError:
                continue
            if _common.already_normalized(row):
                yield row
            elif isinstance(row, dict):
                out = _normalize(row)
                if out is not None:
                    yield out
        return
    yield from _iter_results(payload)


def _network_iter(opts: EuEurlexFetchOpts, owned: bool, client: Any) -> Iterator[dict]:
    cap = opts.max_records or 0
    emitted = 0
    offset = 0
    try:
        while True:
            limit = opts.page_size if cap == 0 else min(opts.page_size, cap - emitted)
            if limit <= 0:
                return
            q = (opts.sparql or _DEFAULT_SELECT).format(limit=limit, offset=offset)
            url = f"{opts.endpoint}?{urllib.parse.urlencode({'query': q, 'format': 'application/sparql-results+json'})}"
            resp = client.get(url, headers={"Accept": "application/sparql-results+json"})
            resp.raise_for_status()
            payload = resp.json()
            page_rows = list(_iter_results(payload))
            if not page_rows:
                break
            for row in page_rows:
                yield row
                emitted += 1
                if cap and emitted >= cap:
                    return
            offset += limit
    finally:
        if owned:
            client.close()


def fetch(staging_dir: Path, opts: EuEurlexFetchOpts) -> FetchResult:
    if opts.local_source is not None:
        rows = _iter_local(Path(opts.local_source))
        meta = {"url": str(opts.local_source), "jurisdiction": "EU", "bucket": "statutes/eu-eurlex"}
    else:
        if opts.max_records is None:
            raise ValueError(
                "EuEurlexFetchOpts.max_records must be set in network mode "
                "(bounds the SPARQL LIMIT; passive-only per ADR-2605262400 §7)."
            )
        import httpx

        owned = opts.client is None
        client = opts.client or httpx.Client(
            timeout=opts.timeout_sec, follow_redirects=True,
            headers={"User-Agent": opts.user_agent},
        )
        rows = _network_iter(opts, owned, client)
        meta = {"url": opts.endpoint, "jurisdiction": "EU", "bucket": "statutes/eu-eurlex"}

    return _common.write_run(
        staging_dir=staging_dir, name="eu-eurlex", rows=rows, source_meta=meta,
        license_id=LICENSE_ID, tier=TIER, max_records=opts.max_records,
        local_source=opts.local_source,
    )


__all__ = ["DEFAULT_ENDPOINT", "EuEurlexFetchOpts", "fetch"]
