"""US data.gov CKAN catalog fetcher — W1 concrete impl.

Per ADR-2605263900 W1. data.gov is the US federal government's
open-data catalog (CKAN-based; ~250K dataset entries across federal
agencies) under **public domain** (US federal government works are
not copyrighted per 17 USC 105). Individual datasets may carry
additional attribution requirements via their CKAN ``license_id``
field (preserved by this fetcher).

  https://catalog.data.gov/api/3/action/package_search?rows=N&start=S

CKAN `package_search` response shape (paginated):

  {
    "help": "...",
    "success": true,
    "result": {
      "count": 250000,
      "results": [
        {
          "id": "uuid",
          "name": "noaa-cdo",
          "title": "Climate Data Online",
          "notes": "Daily / monthly weather observations...",
          "license_id": "us-pd",
          "license_title": "U.S. Public Domain",
          "organization": {"name": "noaa-gov", "title": "NOAA"},
          "metadata_created": "2020-01-15T00:00:00Z",
          "metadata_modified": "2025-06-01T00:00:00Z",
          ...
        },
        ...
      ]
    }
  }

Normalized into NDJSON consumable by
``kotodama.organism.sensors.gov.us_data_gov_sensor.UsDataGovSensor``:

  {"datasetId": "noaa-cdo", "title": "Climate Data Online",
   "license": "us-pd",
   "descriptionExcerpt": "Daily / monthly weather observations...",
   "publisher": "NOAA",
   "publishedAtUtc": "2020-01-15T00:00:00Z",
   "organization": "noaa-gov",
   "payloadCid": "<package_uuid>"}

Two operator paths matching the established pattern:

1. **Network mode** (default): httpx GET against
   ``catalog.data.gov/api/3/action/package_search`` with paging
   (start + rows). Optional ``q`` query filter or
   ``organization_filter`` server-side filter.

2. **Local-source mode**: read operator-staged JSON OR NDJSON.

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

DEFAULT_CKAN_BASE = "https://catalog.data.gov/api/3/action"


@dataclass
class UsDataGovFetchOpts:
    ckan_base: str = DEFAULT_CKAN_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    page_size: int = 1000  # CKAN max per request
    # Server-side organization filter (e.g. "noaa-gov" / "epa-gov").
    organization_filter: Optional[str] = None
    # Free-text CKAN search query (Solr syntax). None = match-all.
    q: Optional[str] = None
    # Local-source mode: skip HTTPS, read this path (CKAN JSON OR NDJSON).
    local_source: Optional[Path] = None
    max_records: Optional[int] = None
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _ckan_search_url(opts: UsDataGovFetchOpts, start: int) -> str:
    """Build a CKAN package_search URL for a given pagination start."""
    params: dict[str, str] = {
        "rows": str(opts.page_size),
        "start": str(start),
    }
    fq_parts: list[str] = []
    if opts.organization_filter:
        fq_parts.append(f"organization:{opts.organization_filter}")
    if fq_parts:
        params["fq"] = " AND ".join(fq_parts)
    if opts.q:
        params["q"] = opts.q
    return f"{opts.ckan_base}/package_search?{urllib.parse.urlencode(params)}"


def _normalize_ckan_pkg(pkg: dict) -> Optional[dict]:
    """Normalize a single CKAN package dict to the sensor's NDJSON shape.

    Returns None for rows missing required fields (G7 schema discipline).
    """
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
        "organization": str(org.get("name", "")) or None,
        "payloadCid": payload_cid,
    }


def _iter_observations_from_payload(payload: Any) -> Iterator[dict]:
    """Yield normalized rows from a parsed CKAN-or-list-or-NDJSON payload.

    Handles 4 shapes:
    - Native CKAN `package_search` response: ``{"result": {"results": [...]}}``
    - CKAN single-pkg envelope: ``{"result": pkg_dict}``
    - Flat list of packages: ``[pkg, pkg, ...]``
    - Operator-staged pre-normalized rows preserved as-is.
    """
    if isinstance(payload, dict):
        # Native CKAN.
        if "result" in payload and isinstance(payload["result"], dict):
            results = payload["result"].get("results")
            if isinstance(results, list):
                for pkg in results:
                    if isinstance(pkg, dict):
                        # Pre-normalized passthrough check.
                        if "datasetId" in pkg and "license" in pkg:
                            yield pkg
                            continue
                        normalized = _normalize_ckan_pkg(pkg)
                        if normalized is not None:
                            yield normalized
                return
            # Single-pkg envelope.
            single = payload["result"]
            if isinstance(single, dict):
                normalized = _normalize_ckan_pkg(single)
                if normalized is not None:
                    yield normalized
                return
        # Pre-normalized single envelope.
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
    opts: UsDataGovFetchOpts, owned_client: bool, client: httpx.Client
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
            # Advance pagination.
            total = None
            if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
                total = payload["result"].get("count")
            if not isinstance(total, int):
                # Defensive: end pagination if header is malformed.
                break
            start += opts.page_size
            if start >= total or yielded_in_page == 0:
                break
    finally:
        if owned_client:
            client.close()


def fetch(staging_dir: Path, opts: UsDataGovFetchOpts) -> FetchResult:
    """Stage US data.gov CKAN catalog into the staging directory.

    Always writes ``us-data-gov.ndjson`` (sensor-consumable).
    """
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"us-data-gov-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    ndjson_path = out_dir / "us-data-gov.ndjson"
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
        name="us-data-gov",
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
            "organizationFilter": opts.organization_filter,
            "query": opts.q,
            "license": "public-domain",
            "tier": "A",
        },
    )


__all__ = [
    "DEFAULT_CKAN_BASE",
    "UsDataGovFetchOpts",
    "fetch",
]
