"""US Code of Federal Regulations (eCFR) fetcher — W1 anchor (ADR-2605262800).

The eCFR (GPO / Office of the Federal Register) publishes the CFR in the **public
domain** with a documented JSON+XML API. This fetcher reads the per-title
*structure* JSON (the hierarchy of chapters/parts/sections) and normalizes at the
**section** level:

  https://www.ecfr.gov/api/versioner/v1/structure/{date}/title-{n}.json

  {"type":"title","identifier":"12","label":"Title 12 — Banks and Banking",
   "children":[ {"type":"part","identifier":"1","children":[
     {"type":"section","identifier":"1.1","label":"§ 1.1 Authority.",
      "label_description":"Authority."}, ... ]} ]}

→ normalized statute NDJSON (see ``legal._common``). recordId = ``US-CFR:tNN/ID``.
Bucket: ``law/statutes/us-cfr/<rev>/`` (+ ``procedures/us-cfr-procedures/`` for
procedural titles). Sensor: ``legal_statute_sensor`` (US).

local_source accepts the structure JSON or a JSON/NDJSON re-stage. Passive-only
(ADR-2605262400 §7): one title + one ``date`` per network call; no full-title
sweep per tick.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

from .. import FetchResult
from . import _common

DEFAULT_API_BASE = "https://www.ecfr.gov/api/versioner/v1"
LICENSE_ID = "public-domain"
TIER = "A"


@dataclass
class UsCfrFetchOpts:
    api_base: str = DEFAULT_API_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 180.0
    local_source: Optional[Path] = None
    title: Optional[int] = None       # CFR title number (network mode)
    date: Optional[str] = None        # YYYY-MM-DD version date (network mode)
    max_records: Optional[int] = None
    client: Optional[Any] = None      # httpx.Client (lazy)


def _walk_sections(node: dict, title_no: str, date: Optional[str]) -> Iterator[dict]:
    if not isinstance(node, dict):
        return
    if node.get("type") == "section":
        ident = str(node.get("identifier") or "").strip()
        if ident:
            law_id = f"{title_no}/{ident}"
            title_txt = node.get("label_description") or node.get("label")
            src = f"https://www.ecfr.gov/current/title-{title_no}/section-{ident}"
            yield {
                "recordId": f"US-CFR:{law_id}",
                "jurisdiction": "US",
                "lawId": f"cfr/t{title_no}/s{ident}",
                "title": title_txt,
                "lawType": "cfr-section",
                "promulgatedDate": None,
                "effectiveDate": _common.coerce_iso_date(date),
                "revision": date,
                "lang": "en",
                "license": LICENSE_ID,
                "sourceUrl": src,
                "payloadCid": src,
                "bodyExcerpt": None,
            }
    for child in node.get("children") or []:
        yield from _walk_sections(child, title_no, date)


def _iter_structure(payload: Any, title_hint: Optional[int], date: Optional[str]) -> Iterator[dict]:
    if not isinstance(payload, dict):
        return
    title_no = str(payload.get("identifier") or (title_hint if title_hint is not None else "")).strip()
    yield from _walk_sections(payload, title_no, date)


def _iter_local(path: Path, title_hint: Optional[int], date: Optional[str]) -> Iterator[dict]:
    raw = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        yield from _common.iter_local_source(path, lambda r: None)  # NDJSON re-stage
        return
    if isinstance(payload, dict) and payload.get("type") == "title":
        yield from _iter_structure(payload, title_hint, date)
    else:
        # already-normalized JSON list / wrapper
        yield from _common.iter_local_source(path, lambda r: None)


def fetch(staging_dir: Path, opts: UsCfrFetchOpts) -> FetchResult:
    if opts.local_source is not None:
        rows = _iter_local(Path(opts.local_source), opts.title, opts.date)
        meta = {"url": str(opts.local_source), "jurisdiction": "US",
                "bucket": "statutes/us-cfr", "title": opts.title, "date": opts.date}
    else:
        if opts.title is None or not opts.date:
            raise ValueError(
                "UsCfrFetchOpts.title + date must both be set in network mode "
                "(one title + one version date; passive-only per ADR-2605262400 §7)."
            )
        import httpx

        owned = opts.client is None
        client = opts.client or httpx.Client(
            timeout=opts.timeout_sec, follow_redirects=True,
            headers={"User-Agent": opts.user_agent},
        )
        url = f"{opts.api_base}/structure/{opts.date}/title-{int(opts.title)}.json"
        try:
            resp = client.get(url)
            resp.raise_for_status()
            payload = resp.json()
        finally:
            if owned:
                client.close()
        rows = _iter_structure(payload, opts.title, opts.date)
        meta = {"url": url, "jurisdiction": "US", "bucket": "statutes/us-cfr",
                "title": opts.title, "date": opts.date}

    return _common.write_run(
        staging_dir=staging_dir, name="us-cfr", rows=rows, source_meta=meta,
        license_id=LICENSE_ID, tier=TIER, max_records=opts.max_records,
        local_source=opts.local_source,
    )


__all__ = ["DEFAULT_API_BASE", "UsCfrFetchOpts", "fetch"]
