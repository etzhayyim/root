"""World Bank Open Data API fetcher — W1 concrete impl.

Per ADR-2605263900 W1. The World Bank Open Data API publishes ~16K
indicators across 270+ economies under **CC-BY 4.0** (World Bank
Open Data Terms of Use).

  https://api.worldbank.org/v2/country/<country>/indicator/<indicator>?format=json&per_page=N&page=P
  https://api.worldbank.org/v2/indicator/                 (indicator catalog)
  https://api.worldbank.org/v2/country/                   (country catalog)

The API response for per-indicator queries is a **2-element JSON
array**:

  [
    {"page": 1, "pages": 5, "per_page": 50, "total": 234, ...},
    [
      {"indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
       "country": {"id": "US", "value": "United States"},
       "countryiso3code": "USA",
       "date": "2024", "value": 29167779200000.0,
       "unit": "", "obs_status": "", "decimal": 0},
      ...
    ]
  ]

This fetcher normalizes that shape into NDJSON rows consumable by
``kotodama.organism.sensors.gov.worldbank_open_data_sensor.WorldBankOpenDataSensor``:

  {"indicatorCode": "NY.GDP.MKTP.CD",
   "indicatorTitle": "GDP (current US$)",
   "dimensions": [["country", "USA"], ["year", "2024"]],
   "value": 29167779200000, "valueUnit": "USD",
   "observationPeriod": "2024", "payloadCid": ""}

Two operator paths supported (matching gleif_lei.py pattern):

1. **Network mode** (``local_source=None``, default): httpx GET against
   the WB API for each (indicator, country) pair declared in
   ``opts.indicators`` × ``opts.countries``; paginates per WB
   ``per_page``.

2. **Local-source mode** (``local_source=<Path>``): skip HTTPS,
   read operator-staged file directly. Useful for pytest fixtures +
   air-gapped fleet nodes.

Passive-only invariant boundary: this fetcher is OPERATOR-triggered
(via ``e7m-dataset pull worldbank-open-data`` CLI OR direct Python
invocation), NOT organism-tick. The sensor is the passive-only side
per ADR-2605262400 §7. Vendor commercial gov-intel terminal imports
(GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro /
FiscalNote / CQ Roll Call Pro) are CONSTITUTIONALLY PROHIBITED per
Charter Rider §2(e)+§2(c).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Literal, Optional

import httpx

from . import FetchResult

DEFAULT_API_BASE = "https://api.worldbank.org/v2"


@dataclass
class WorldBankOpenDataFetchOpts:
    api_base: str = DEFAULT_API_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    fmt: Literal["json", "xml"] = "json"  # XML stream deferred (W2)
    page_size: int = 1000
    indicators: tuple[str, ...] = ()  # required in network mode
    countries: tuple[str, ...] = ("all",)
    date_range: Optional[str] = None  # e.g. "2000:2025"
    # Local-source mode: skip HTTPS, read this path (single JSON OR
    # NDJSON of pre-flattened observation rows).
    local_source: Optional[Path] = None
    # Cap on total observations to fetch (across pagination + indicator
    # × country fan-out). None = no cap (operator-trusted).
    max_observations: Optional[int] = None
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _wb_query_url(opts: WorldBankOpenDataFetchOpts, indicator: str, country: str, page: int) -> str:
    """Build a World Bank API URL for a given (indicator, country, page)."""
    params = [
        f"format={opts.fmt}",
        f"per_page={opts.page_size}",
        f"page={page}",
    ]
    if opts.date_range:
        params.append(f"date={opts.date_range}")
    qs = "&".join(params)
    return f"{opts.api_base}/country/{country}/indicator/{indicator}?{qs}"


def _normalize_wb_observation(raw: dict) -> Optional[dict]:
    """Normalize one WB observation dict to the sensor's NDJSON row shape.

    Returns None for rows missing required fields (G7 schema
    discipline — sensor would skip them too, but better to drop at
    fetcher).
    """
    ind = raw.get("indicator") or {}
    if not isinstance(ind, dict):
        return None
    indicator_code = str(ind.get("id", "")).strip()
    indicator_title = str(ind.get("value", "")).strip()
    if not indicator_code or not indicator_title:
        return None

    # Resolve country: prefer countryiso3code, else country.id (ISO-2).
    country_iso3 = str(raw.get("countryiso3code", "")).strip()
    if not country_iso3:
        country_dict = raw.get("country") or {}
        if isinstance(country_dict, dict):
            country_iso3 = str(country_dict.get("id", "")).strip()
    if not country_iso3:
        return None

    date = str(raw.get("date", "")).strip()
    if not date:
        return None

    # Build SDMX-style ordered dimensions.
    dimensions = [["country", country_iso3], ["year", date]]

    raw_value = raw.get("value")
    value: Optional[float] = (
        float(raw_value) if isinstance(raw_value, (int, float)) else None
    )

    return {
        "indicatorCode": indicator_code,
        "indicatorTitle": indicator_title,
        "dimensions": dimensions,
        "value": value,
        "valueUnit": str(raw.get("unit", "")) or None,
        "observationPeriod": date,
        "payloadCid": "",
    }


def _iter_observations_from_json_payload(payload: Any) -> Iterator[dict]:
    """Yield normalized rows from a parsed WB API JSON payload.

    Accepts:
    - Native WB 2-element array: ``[header, [observation_dicts...]]``
    - Operator-flat list of observation dicts: ``[observation_dicts...]``
    - Operator-staged pre-normalized rows (already in sensor shape) —
      preserved as-is so they pass through unchanged.
    """
    if not isinstance(payload, list):
        return
    # Native WB shape detection: 2-element [header, data].
    if (
        len(payload) == 2
        and isinstance(payload[0], dict)
        and isinstance(payload[1], list)
        and any(k in payload[0] for k in ("page", "pages", "per_page", "total"))
    ):
        observations = payload[1]
    else:
        observations = payload

    for raw in observations:
        if not isinstance(raw, dict):
            continue
        # Pre-normalized row passthrough: detect via presence of our
        # sensor-shape keys.
        if "indicatorCode" in raw and "dimensions" in raw and "observationPeriod" in raw:
            yield raw
            continue
        normalized = _normalize_wb_observation(raw)
        if normalized is not None:
            yield normalized


def _network_iter(
    opts: WorldBankOpenDataFetchOpts, owned_client: bool, client: httpx.Client
) -> Iterator[dict]:
    """Iterate over (indicator × country × paginated-pages) and yield rows."""
    cap = opts.max_observations
    emitted = 0
    try:
        for indicator in opts.indicators:
            for country in opts.countries:
                page = 1
                while True:
                    url = _wb_query_url(opts, indicator, country, page)
                    resp = client.get(url)
                    resp.raise_for_status()
                    payload = resp.json()
                    yielded_in_page = 0
                    for row in _iter_observations_from_json_payload(payload):
                        yield row
                        emitted += 1
                        yielded_in_page += 1
                        if cap is not None and emitted >= cap:
                            return
                    # Decide whether to advance the page.
                    pages_total = None
                    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
                        pages_total = payload[0].get("pages")
                    if pages_total is None or page >= int(pages_total):
                        break
                    if yielded_in_page == 0:
                        # Defensive against malformed pagination.
                        break
                    page += 1
    finally:
        if owned_client:
            client.close()


def fetch(staging_dir: Path, opts: WorldBankOpenDataFetchOpts) -> FetchResult:
    """Stage World Bank Open Data into the staging directory.

    Always writes ``worldbank-open-data.ndjson`` (sensor-consumable).
    """
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"worldbank-open-data-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    ndjson_path = out_dir / "worldbank-open-data.ndjson"
    rows_emitted = 0

    if opts.local_source is not None:
        # Local-source mode: read either JSON OR NDJSON.
        path = Path(opts.local_source)
        raw_text = path.read_text(encoding="utf-8")
        raw_sha = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        try:
            payload = json.loads(raw_text)
            iterator = _iter_observations_from_json_payload(payload)
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
                    if not isinstance(raw_row, dict):
                        continue
                    if "indicatorCode" in raw_row:
                        yield raw_row
                    else:
                        normalized = _normalize_wb_observation(raw_row)
                        if normalized is not None:
                            yield normalized
            iterator = _ndjson_iter()

        if opts.write_ndjson:
            with ndjson_path.open("w", encoding="utf-8") as f:
                cap = opts.max_observations
                for row in iterator:
                    f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
                    f.write("\n")
                    rows_emitted += 1
                    if cap is not None and rows_emitted >= cap:
                        break
        url_attr = str(path)
        source_type = "local"
    else:
        # Network mode.
        if not opts.indicators:
            raise ValueError(
                "WorldBankOpenDataFetchOpts.indicators must be non-empty "
                "in network mode (no implicit full-catalog fetch — caller "
                "must select indicators explicitly per ADR-2605262400 §7 "
                "passive-only discipline)."
            )
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
        url_attr = f"{opts.api_base}/country/<country>/indicator/<indicator>"
        source_type = "http"

    revision = f"sha256:{raw_sha}"
    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="worldbank-open-data",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": source_type,
            "url": url_attr,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "observationCount": rows_emitted,
            "indicators": list(opts.indicators) if opts.indicators else [],
            "countries": list(opts.countries),
            "dateRange": opts.date_range,
            "license": "CC-BY-4.0",
            "tier": "A",
            "format": opts.fmt,
        },
    )


__all__ = [
    "DEFAULT_API_BASE",
    "WorldBankOpenDataFetchOpts",
    "fetch",
]
