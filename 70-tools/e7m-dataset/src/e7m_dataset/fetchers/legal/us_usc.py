"""US Code (OLRC USLM) fetcher — W1 anchor (ADR-2605262800).

The Office of the Law Revision Counsel publishes the United States Code as
**USLM XML** in the **public domain** (US Govt works, 17 U.S.C. §105). There is
no paginated JSON API: the canonical artifact is a per-title USLM XML file from a
release point (https://uscode.house.gov/download/download.shtml). This fetcher
normalizes at the **section** level — the addressable legal unit:

  <uscDoc xmlns="http://xml.house.gov/schemas/uslm/1.0">
    <main><title identifier="/us/usc/t17">
      <section identifier="/us/usc/t17/s101">
        <num value="101">§ 101.</num>
        <heading>Definitions</heading> ...
      </section> ...

→ normalized statute NDJSON (see ``legal._common``). recordId = ``US:usc/tNN/sMM``.
Bucket: ``law/statutes/us-usc/<rev>/``. Sensor: ``legal_statute_sensor`` (US).

local_source is the primary path (operator stages the title USLM XML); network
mode fetches a single USLM XML URL (e.g. a release-point title file). Passive-
only (ADR-2605262400 §7): no recursive crawl of the release-point index.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

from .. import FetchResult
from . import _common

LICENSE_ID = "public-domain"
TIER = "A"
_USLM = "{http://xml.house.gov/schemas/uslm/1.0}"


@dataclass
class UsUscFetchOpts:
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 300.0
    local_source: Optional[Path] = None
    uslm_url: Optional[str] = None   # single USLM XML URL (network mode)
    release_point: Optional[str] = None  # e.g. "2024-05-13@118-78" → revision
    max_records: Optional[int] = None
    client: Optional[Any] = None     # httpx.Client (lazy)


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(el: Optional[ET.Element]) -> Optional[str]:
    if el is None:
        return None
    t = "".join(el.itertext()).strip()
    return t or None


def _govinfo_url(identifier: str) -> str:
    # /us/usc/t17/s101 → title 17, section 101 → govinfo resolver
    segs = [s for s in identifier.split("/") if s]
    title = next((s[1:] for s in segs if s.startswith("t") and s[1:].isdigit()), "")
    section = next((s[1:] for s in segs if s.startswith("s")), "")
    if title and section:
        return f"https://www.govinfo.gov/link/uscode/{title}/{section}"
    return f"https://uscode.house.gov/view.xhtml?req={identifier}"


def _iter_uslm(xml_text: str, revision: Optional[str]) -> Iterator[dict]:
    root = ET.fromstring(xml_text)
    for el in root.iter():
        if _localname(el.tag) != "section":
            continue
        identifier = (el.get("identifier") or "").strip()
        if not identifier or "/s" not in identifier:
            continue
        law_id = identifier.lstrip("/").replace("us/", "", 1)  # usc/t17/s101
        num_el = el.find(f"{_USLM}num")
        heading = _text(el.find(f"{_USLM}heading"))
        num_val = (num_el.get("value") if num_el is not None else None) or None
        yield {
            "recordId": f"US:{law_id}",
            "jurisdiction": "US",
            "lawId": law_id,
            "title": heading,
            "lawType": "us-code-section",
            "sectionNum": num_val,
            "promulgatedDate": None,
            "effectiveDate": None,
            "revision": revision,
            "lang": "en",
            "license": LICENSE_ID,
            "sourceUrl": _govinfo_url(identifier),
            "payloadCid": _govinfo_url(identifier),
            "bodyExcerpt": None,
        }


def _iter_local(path: Path, revision: Optional[str]) -> Iterator[dict]:
    if path.suffix.lower() in (".json", ".ndjson"):
        yield from _common.iter_local_source(path, lambda r: None)
        return
    yield from _iter_uslm(path.read_text(encoding="utf-8"), revision)


def fetch(staging_dir: Path, opts: UsUscFetchOpts) -> FetchResult:
    revision = opts.release_point
    if opts.local_source is not None:
        rows = _iter_local(Path(opts.local_source), revision)
        meta = {"url": str(opts.local_source), "jurisdiction": "US",
                "bucket": "statutes/us-usc", "releasePoint": revision}
    else:
        if not opts.uslm_url:
            raise ValueError(
                "UsUscFetchOpts.uslm_url must be set in network mode (a single "
                "USLM XML release-point title file; passive-only per ADR-2605262400 §7)."
            )
        import httpx

        owned = opts.client is None
        client = opts.client or httpx.Client(
            timeout=opts.timeout_sec, follow_redirects=True,
            headers={"User-Agent": opts.user_agent},
        )
        try:
            resp = client.get(opts.uslm_url)
            resp.raise_for_status()
            xml_text = resp.text
        finally:
            if owned:
                client.close()
        rows = _iter_uslm(xml_text, revision)
        meta = {"url": opts.uslm_url, "jurisdiction": "US",
                "bucket": "statutes/us-usc", "releasePoint": revision}

    return _common.write_run(
        staging_dir=staging_dir, name="us-usc", rows=rows, source_meta=meta,
        license_id=LICENSE_ID, tier=TIER, max_records=opts.max_records,
        local_source=opts.local_source,
    )


__all__ = ["UsUscFetchOpts", "fetch"]
