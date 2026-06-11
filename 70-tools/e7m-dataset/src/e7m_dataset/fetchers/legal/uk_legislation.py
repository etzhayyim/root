"""UK legislation.gov.uk fetcher — W1 anchor (ADR-2605262800).

legislation.gov.uk (The National Archives) publishes UK statutes + statutory
instruments under **OGL v3.0**. The browse/search endpoints return Atom XML
feeds; each entry is one legislation item:

  https://www.legislation.gov.uk/ukpga/2023   →  Atom feed (paged via ?page=N)

  <feed xmlns="http://www.w3.org/2005/Atom"
        xmlns:leg="http://www.legislation.gov.uk/namespaces/legislation">
    <entry>
      <id>http://www.legislation.gov.uk/ukpga/2023/1</id>
      <title>Health and Care Act 2023</title>
      <published>2023-01-11</published>
      <updated>2024-02-01</updated>
      <link rel="self" href="https://www.legislation.gov.uk/ukpga/2023/1"/>
      <leg:year>2023</leg:year><leg:number>1</leg:number>
    </entry>
    <link rel="next" href=".../ukpga/2023?page=2"/>
  </feed>

→ normalized statute NDJSON (see ``legal._common``). Bucket:
``law/statutes/uk-legislation/<rev>/``. Sensor: ``legal_statute_sensor`` (GB).

local_source accepts the Atom XML directly, or a JSON/NDJSON re-stage. Passive-
only (ADR-2605262400 §7): network mode requires an explicit ``leg_type`` + the
feed paginates only as far as ``max_records``.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

from .. import FetchResult
from . import _common

DEFAULT_BASE = "https://www.legislation.gov.uk"
LICENSE_ID = "OGL-v3.0"
TIER = "A"

_ATOM = "{http://www.w3.org/2005/Atom}"

# legislation.gov.uk type code → normalized lawType.
_LEG_TYPE = {
    "ukpga": "act", "asp": "act", "anaw": "act", "mwa": "act", "ukla": "act",
    "nia": "act", "aosp": "act", "apni": "act", "ukcm": "measure",
    "uksi": "statutory-instrument", "ssi": "statutory-instrument",
    "wsi": "statutory-instrument", "nisr": "statutory-rule",
}


@dataclass
class UkLegislationFetchOpts:
    base: str = DEFAULT_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    local_source: Optional[Path] = None
    leg_type: str = "ukpga"          # required path segment in network mode
    year: Optional[int] = None       # optional year filter
    max_records: Optional[int] = None
    client: Optional[Any] = None     # httpx.Client (lazy)


def _law_id_from_uri(uri: str) -> Optional[str]:
    # http://www.legislation.gov.uk/ukpga/2023/1 → ukpga/2023/1
    parts = [p for p in uri.replace("https://", "").replace("http://", "").split("/") if p]
    if parts and parts[0].startswith("www.legislation.gov.uk"):
        parts = parts[1:]
    return "/".join(parts[:3]) if len(parts) >= 3 else ("/".join(parts) or None)


def _entry_to_row(entry: ET.Element) -> Optional[dict]:
    uri = (entry.findtext(f"{_ATOM}id") or "").strip()
    law_id = _law_id_from_uri(uri)
    if not law_id:
        return None
    title = (entry.findtext(f"{_ATOM}title") or "").strip() or None
    published = (entry.findtext(f"{_ATOM}published") or "").strip()
    updated = (entry.findtext(f"{_ATOM}updated") or "").strip()
    type_code = law_id.split("/", 1)[0]
    src = uri.replace("http://", "https://")
    return {
        "recordId": f"GB:{law_id}",
        "jurisdiction": "GB",
        "lawId": law_id,
        "title": title,
        "lawType": _LEG_TYPE.get(type_code, "act"),
        "promulgatedDate": _common.coerce_iso_date(published),
        "effectiveDate": None,
        "revision": _common.coerce_iso_date(updated) or updated or None,
        "lang": "en",
        "license": LICENSE_ID,
        "sourceUrl": src,
        "payloadCid": src,
        "bodyExcerpt": None,
    }


def _iter_atom(xml_text: str) -> Iterator[dict]:
    root = ET.fromstring(xml_text)
    for entry in root.findall(f"{_ATOM}entry"):
        row = _entry_to_row(entry)
        if row is not None:
            yield row


def _next_link(xml_text: str) -> Optional[str]:
    root = ET.fromstring(xml_text)
    for link in root.findall(f"{_ATOM}link"):
        if link.get("rel") == "next" and link.get("href"):
            return link.get("href")
    return None


def _iter_local(path: Path) -> Iterator[dict]:
    if path.suffix.lower() in (".json", ".ndjson"):
        yield from _common.iter_local_source(path, lambda r: None)  # normalized re-stage only
        return
    yield from _iter_atom(path.read_text(encoding="utf-8"))


def _network_iter(opts: UkLegislationFetchOpts, owned: bool, client: Any) -> Iterator[dict]:
    cap = opts.max_records
    emitted = 0
    url = f"{opts.base}/{opts.leg_type}"
    if opts.year:
        url += f"/{int(opts.year)}"
    try:
        while url:
            resp = client.get(url, headers={"Accept": "application/atom+xml"})
            resp.raise_for_status()
            text = resp.text
            for row in _iter_atom(text):
                yield row
                emitted += 1
                if cap is not None and emitted >= cap:
                    return
            url = _next_link(text)
    finally:
        if owned:
            client.close()


def fetch(staging_dir: Path, opts: UkLegislationFetchOpts) -> FetchResult:
    if opts.local_source is not None:
        rows = _iter_local(Path(opts.local_source))
        meta = {"url": str(opts.local_source), "jurisdiction": "GB", "bucket": "statutes/uk-legislation"}
    else:
        if opts.max_records is None:
            raise ValueError(
                "UkLegislationFetchOpts.max_records must be set in network mode "
                "(passive-only: no implicit full-archive scrape per ADR-2605262400 §7)."
            )
        import httpx

        owned = opts.client is None
        client = opts.client or httpx.Client(
            timeout=opts.timeout_sec, follow_redirects=True,
            headers={"User-Agent": opts.user_agent},
        )
        rows = _network_iter(opts, owned, client)
        meta = {"url": f"{opts.base}/{opts.leg_type}", "jurisdiction": "GB",
                "bucket": "statutes/uk-legislation", "legType": opts.leg_type, "year": opts.year}

    return _common.write_run(
        staging_dir=staging_dir, name="uk-legislation", rows=rows, source_meta=meta,
        license_id=LICENSE_ID, tier=TIER, max_records=opts.max_records,
        local_source=opts.local_source,
    )


__all__ = ["DEFAULT_BASE", "UkLegislationFetchOpts", "fetch"]
