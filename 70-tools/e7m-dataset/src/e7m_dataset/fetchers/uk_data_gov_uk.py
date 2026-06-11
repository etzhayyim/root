"""UK data.gov.uk CKAN catalog fetcher — W1 concrete impl.

Per ADR-2605263900 W1. data.gov.uk is the UK government's open-data
catalog (CKAN-based; ~70K dataset entries across UK central + local
government publishers) under **OGL v3.0** (Crown copyright open
license). Individual datasets MAY carry additional license tags
(e.g., ``cc-by`` for cross-licensed sub-datasets).

  https://data.gov.uk/api/3/action/package_search?rows=N&start=S

CKAN ``package_search`` response shape (paginated):

  {
    "success": true,
    "result": {
      "count": 70000,
      "results": [{"id": "...", "name": "...", "title": "...",
                   "license_id": "uk-ogl", "organization": {...},
                   "metadata_created": "...", "notes": "..."}, ...]
    }
  }

NOTE: UK data.gov.uk follows the CKAN core schema, so the
**organization** field name in CKAN's JSON is American English (CKAN
core convention). British English ``organisation`` appears only as a
constructor-parameter name (``organisation_filter``) for British UX +
consistency with ``UkDataGovUkSensor``.

Normalized NDJSON consumable by
``kotodama.organism.sensors.gov.uk_data_gov_uk_sensor.UkDataGovUkSensor``:

  {"datasetId": "ons-gdp-quarterly", "title": "GDP Quarterly",
   "license": "uk-ogl",
   "descriptionExcerpt": "...",
   "publisher": "Office for National Statistics",
   "publishedAtUtc": "2024-09-15T00:00:00Z",
   "organisation": "ons-gov-uk",  # British English spelling (sensor expects this key)
   "payloadCid": "<package_uuid>"}

Two operator paths matching us_data_gov.py pattern:

1. **Network mode** (default): httpx GET against
   ``data.gov.uk/api/3/action/package_search`` with paging +
   optional Solr ``fq`` organisation filter.

2. **Local-source mode**: read operator-staged CKAN JSON OR NDJSON.

Passive-only invariant boundary: this fetcher is OPERATOR-triggered,
NOT organism-tick, per ADR-2605262400 §7. Vendor commercial gov-intel
terminal imports (GovWin IQ / Bloomberg Government / Politico Pro /
E&E News Pro / FiscalNote / CQ Roll Call Pro) are CONSTITUTIONALLY
PROHIBITED per Charter Rider §2(e)+§2(c).
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

import httpx

from . import FetchResult

DEFAULT_CKAN_BASE = "https://data.gov.uk/api/3/action"


@dataclass
class UkDataGovUkFetchOpts:
    ckan_base: str = DEFAULT_CKAN_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    page_size: int = 1000
    # British English param name for UX consistency; maps to CKAN
    # ``organization:<id>`` Solr fq under the hood.
    organisation_filter: Optional[str] = None
    q: Optional[str] = None
    local_source: Optional[Path] = None
    max_records: Optional[int] = None
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _ckan_search_url(opts: UkDataGovUkFetchOpts, start: int) -> str:
    params: dict[str, str] = {
        "rows": str(opts.page_size),
        "start": str(start),
    }
    fq_parts: list[str] = []
    if opts.organisation_filter:
        # CKAN core uses 'organization' even on UK; the user-facing
        # param is British-spelt for sensor consistency.
        fq_parts.append(f"organization:{opts.organisation_filter}")
    if fq_parts:
        params["fq"] = " AND ".join(fq_parts)
    if opts.q:
        params["q"] = opts.q
    return f"{opts.ckan_base}/package_search?{urllib.parse.urlencode(params)}"


def _normalize_ckan_pkg(pkg: dict) -> Optional[dict]:
    dataset_id = str(pkg.get("name", "")).strip()
    title = str(pkg.get("title", "")).strip()
    license_id = str(pkg.get("license_id", "")).strip()
    payload_cid = str(pkg.get("id", "")).strip()
    if not (dataset_id and title and license_id and payload_cid):
        return None
    org = pkg.get("organization") or {}
    if not isinstance(org, dict):
        org = {}
    return {
        "datasetId": dataset_id,
        "title": title,
        "descriptionExcerpt": str(pkg.get("notes", ""))[:4096],
        "license": license_id,
        "publisher": str(org.get("title", "")) or str(pkg.get("author", "")) or None,
        "publishedAtUtc": (
            str(pkg.get("metadata_created"))
            if pkg.get("metadata_created")
            else None
        ),
        # NOTE: British English spelling — UkDataGovUkSensor expects
        # ``organisation`` (with 's') in the row shape.
        "organisation": str(org.get("name", "")) or None,
        "payloadCid": payload_cid,
    }


def _iter_observations_from_payload(payload: Any) -> Iterator[dict]:
    if isinstance(payload, dict):
        if "result" in payload and isinstance(payload["result"], dict):
            results = payload["result"].get("results")
            if isinstance(results, list):
                for pkg in results:
                    if isinstance(pkg, dict):
                        if "datasetId" in pkg and "license" in pkg:
                            yield pkg
                            continue
                        normalized = _normalize_ckan_pkg(pkg)
                        if normalized is not None:
                            yield normalized
                return
            single = payload["result"]
            if isinstance(single, dict):
                normalized = _normalize_ckan_pkg(single)
                if normalized is not None:
                    yield normalized
                return
        if "datasetId" in payload and "license" in payload:
            yield payload
            return
    if isinstance(payload, list):
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            if "datasetId" in entry and "license" in entry:
                yield entry
                continue
            normalized = _normalize_ckan_pkg(entry)
            if normalized is not None:
                yield normalized


def _network_iter(
    opts: UkDataGovUkFetchOpts, owned_client: bool, client: httpx.Client
) -> Iterator[dict]:
    cap = opts.max_records
    emitted = 0
    start = 0
    try:
        while True:
            url = _ckan_search_url(opts, start)
            resp = client.get(url)
            resp.raise_for_status()
            payload = resp.json()
            yielded_in_page = 0
            for row in _iter_observations_from_payload(payload):
                yield row
                emitted += 1
                yielded_in_page += 1
                if cap is not None and emitted >= cap:
                    return
            total = None
            if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
                total = payload["result"].get("count")
            if not isinstance(total, int):
                break
            start += opts.page_size
            if start >= total or yielded_in_page == 0:
                break
    finally:
        if owned_client:
            client.close()


def fetch(staging_dir: Path, opts: UkDataGovUkFetchOpts) -> FetchResult:
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"uk-data-gov-uk-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    ndjson_path = out_dir / "uk-data-gov-uk.ndjson"
    rows_emitted = 0

    if opts.local_source is not None:
        path = Path(opts.local_source)
        raw_text = path.read_text(encoding="utf-8")
        raw_sha = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        try:
            payload = json.loads(raw_text)
            iterator = _iter_observations_from_payload(payload)
        except json.JSONDecodeError:
            def _ndjson_iter():
                for line in raw_text.splitlines():
                    s = line.strip()
                    if not s:
                        continue
                    try:
                        raw_row = json.loads(s)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(raw_row, dict):
                        if "datasetId" in raw_row and "license" in raw_row:
                            yield raw_row
                        else:
                            normalized = _normalize_ckan_pkg(raw_row)
                            if normalized is not None:
                                yield normalized
            iterator = _ndjson_iter()
        if opts.write_ndjson:
            with ndjson_path.open("w", encoding="utf-8") as f:
                cap = opts.max_records
                for row in iterator:
                    f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
                    f.write("\n")
                    rows_emitted += 1
                    if cap is not None and rows_emitted >= cap:
                        break
        url_attr = str(path)
        source_type = "local"
    else:
        owned_client = opts.client is None
        client = opts.client or httpx.Client(
            timeout=opts.timeout_sec,
            follow_redirects=True,
            headers={"User-Agent": opts.user_agent},
        )
        hasher = hashlib.sha256()
        with ndjson_path.open("w", encoding="utf-8") as f:
            for row in _network_iter(opts, owned_client, client):
                line = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
                f.write(line)
                f.write("\n")
                hasher.update(line.encode("utf-8"))
                hasher.update(b"\n")
                rows_emitted += 1
        raw_sha = hasher.hexdigest()
        url_attr = f"{opts.ckan_base}/package_search"
        source_type = "http"

    revision = f"sha256:{raw_sha}"
    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="uk-data-gov-uk",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": source_type,
            "url": url_attr,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "packageCount": rows_emitted,
            "organisationFilter": opts.organisation_filter,
            "query": opts.q,
            "license": "OGL-v3.0",
            "tier": "A",
        },
    )


__all__ = [
    "DEFAULT_CKAN_BASE",
    "UkDataGovUkFetchOpts",
    "fetch",
]
