"""EU Eurostat SDMX-JSON fetcher — W1 concrete impl.

Per ADR-2605263900 W1. Eurostat publishes ~10K SDMX dataflows across
EU-27 + EEA + candidate countries under **EU re-use Decision 2011/833/
EU** (Commission's open data policy).

  https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/<flow>/?format=JSON

SDMX-JSON 2.0 response shape (Eurostat-flavored):

  {
    "version": "2.0", "class": "dataset",
    "label": "Population on 1 January",
    "id":   ["freq", "sex", "age", "unit", "geo", "time"],
    "size": [1, 3, 100, 1, 27, 5],
    "dimension": {
      "freq":  {"category": {"index": {"A": 0},          "label": {"A": "Annual"}}},
      "geo":   {"category": {"index": {"DE": 5, "FR": 9, ...}}},
      "time":  {"category": {"index": {"2024": 4, "2025": 5}}},
      ...
    },
    "value": {"0": 83100000.0, "1": 83200000.0, ...},
    "status": {"5": "p", ...}
  }

The ``value`` dict is keyed by a **flattened index** (row-major
linearization of the multi-dim cube defined by ``size`` + ``id``).
This fetcher decodes each entry into the sensor's expected NDJSON
row shape:

  {"indicatorCode": "DEMO_PJAN",  # from extension.datastructure.id or url
   "indicatorTitle": "Population on 1 January",  # from dataset.label
   "dimensions": [["geo", "DE"], ["time", "2025"]],
   "value": 83440000, "valueUnit": "NR",
   "observationPeriod": "2025", "payloadCid": ""}

Consumed by ``kotodama.organism.sensors.gov.eu_eurostat_sensor.EuEurostatSensor``.

Two operator paths supported (matching gleif_lei.py + worldbank_open_data.py pattern):

1. **Network mode** (``local_source=None``, default): httpx GET per
   dataflow in ``opts.dataflows`` against the SDMX 2.1 endpoint with
   ``format=JSON`` query param.

2. **Local-source mode** (``local_source=<Path>``): skip HTTPS, read
   operator-staged file (single SDMX-JSON OR NDJSON pre-normalized
   pass-through). Canonical test path + air-gapped fleet path.

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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Literal, Optional

import httpx

from . import FetchResult

DEFAULT_SDMX_BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1"
DEFAULT_BULK_BASE = "https://ec.europa.eu/eurostat/data/bulkdownload"

# Dimension codes whose label-value should be reported as the row's
# `valueUnit` field (Eurostat's unit-of-measure convention).
_UNIT_DIM_CANDIDATES: tuple[str, ...] = ("unit",)
# Dimension code whose label-value populates the row's
# `observationPeriod` field. Eurostat always uses "time".
_TIME_DIM_CANDIDATES: tuple[str, ...] = ("time", "TIME_PERIOD")


@dataclass
class EuEurostatFetchOpts:
    sdmx_base: str = DEFAULT_SDMX_BASE
    bulk_base: str = DEFAULT_BULK_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 300.0
    fmt: Literal["JSON", "sdmx-2.1"] = "JSON"
    dataflows: tuple[str, ...] = ()  # required in network mode
    # Local-source mode: skip HTTPS.
    local_source: Optional[Path] = None
    max_observations: Optional[int] = None
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _wb_query_url(opts: EuEurostatFetchOpts, dataflow: str) -> str:
    """Build the SDMX 2.1 data URL for a given dataflow."""
    fmt = "JSON" if opts.fmt == "JSON" else "sdmx-2.1"
    return f"{opts.sdmx_base}/data/{dataflow}/?format={fmt}"


def _build_index_lookup(dim_block: dict) -> dict[int, str]:
    """Build a {position_index: code} lookup from a dimension block.

    SDMX-JSON ``dimension.<id>.category.index`` is shaped
    ``{"DE": 0, "FR": 1, ...}`` (code → position). We invert it to
    ``{0: "DE", 1: "FR"}`` (position → code) for fast lookup during
    flat-index decode.
    """
    raw_index = dim_block.get("category", {}).get("index", {})
    if not isinstance(raw_index, dict):
        return {}
    out: dict[int, str] = {}
    for code, pos in raw_index.items():
        if isinstance(pos, int):
            out[pos] = str(code)
    return out


def _decode_flat_index(flat: int, sizes: list[int]) -> list[int]:
    """Decode a row-major flat index into per-dimension indices.

    Given ``sizes = [s0, s1, ..., sN]`` and a flat index, returns
    ``[d0, d1, ..., dN]`` where ``flat == d0 * (s1*s2*...*sN) +
    d1 * (s2*s3*...*sN) + ... + dN``.
    """
    out: list[int] = [0] * len(sizes)
    remaining = flat
    # Build strides from right to left: strides[i] = product of sizes[i+1..N].
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]
    for i, stride in enumerate(strides):
        out[i] = remaining // stride
        remaining = remaining % stride
    return out


def _iter_observations_from_sdmx_json(
    payload: dict, fallback_dataflow_id: str = ""
) -> Iterator[dict]:
    """Yield normalized rows from a parsed Eurostat SDMX-JSON 2.0 payload."""
    if not isinstance(payload, dict):
        return
    dim_ids = payload.get("id") or []
    sizes = payload.get("size") or []
    dim_blocks = payload.get("dimension") or {}
    values = payload.get("value") or {}
    if not (
        isinstance(dim_ids, list)
        and isinstance(sizes, list)
        and isinstance(dim_blocks, dict)
        and isinstance(values, dict)
        and len(dim_ids) == len(sizes)
    ):
        return

    # Resolve indicator code + title.
    ext = payload.get("extension") or {}
    ds = ext.get("datastructure") if isinstance(ext, dict) else None
    indicator_code = ""
    if isinstance(ds, dict):
        indicator_code = str(ds.get("id", "")).strip()
    if not indicator_code:
        indicator_code = fallback_dataflow_id
    indicator_title = str(payload.get("label", "")).strip() or indicator_code

    # Pre-build per-dim {position: code} lookups.
    per_dim_lookups: list[dict[int, str]] = [
        _build_index_lookup(dim_blocks.get(dim_id, {})) for dim_id in dim_ids
    ]

    # Detect unit + time dimension positions for valueUnit + observationPeriod.
    unit_dim_pos: Optional[int] = None
    time_dim_pos: Optional[int] = None
    for pos, dim_id in enumerate(dim_ids):
        if dim_id in _UNIT_DIM_CANDIDATES and unit_dim_pos is None:
            unit_dim_pos = pos
        if dim_id in _TIME_DIM_CANDIDATES and time_dim_pos is None:
            time_dim_pos = pos

    for flat_str, raw_val in values.items():
        try:
            flat = int(flat_str)
        except (TypeError, ValueError):
            continue
        per_dim_idx = _decode_flat_index(flat, sizes)
        # Resolve codes for every dimension.
        dim_pairs: list[list[str]] = []
        observation_period = ""
        value_unit: Optional[str] = None
        for pos, dim_id in enumerate(dim_ids):
            lookup = per_dim_lookups[pos]
            code = lookup.get(per_dim_idx[pos], "")
            if pos == time_dim_pos:
                observation_period = code
            elif pos == unit_dim_pos:
                value_unit = code or None
            else:
                if code:
                    dim_pairs.append([dim_id, code])
        if not observation_period:
            continue
        # Append (time, period) at the END so dimensions tuple matches
        # downstream consumer expectation: geo first, time last.
        dim_pairs.append(["time", observation_period])

        value_num: Optional[float] = (
            float(raw_val) if isinstance(raw_val, (int, float)) else None
        )

        yield {
            "indicatorCode": indicator_code,
            "indicatorTitle": indicator_title,
            "dimensions": dim_pairs,
            "value": value_num,
            "valueUnit": value_unit,
            "observationPeriod": observation_period,
            "payloadCid": "",
        }


def _iter_observations_from_payload(payload: Any, fallback_id: str = "") -> Iterator[dict]:
    """Dispatch on payload shape: SDMX-JSON dict vs flat list vs pre-normalized."""
    if isinstance(payload, dict):
        # SDMX-JSON 2.0 OR pre-normalized envelope.
        if "value" in payload and "dimension" in payload and "size" in payload:
            yield from _iter_observations_from_sdmx_json(payload, fallback_id)
            return
        # Single pre-normalized row envelope.
        if "indicatorCode" in payload and "dimensions" in payload:
            yield payload
            return
    if isinstance(payload, list):
        for raw in payload:
            if isinstance(raw, dict) and "indicatorCode" in raw and "dimensions" in raw:
                yield raw


def _network_iter(
    opts: EuEurostatFetchOpts, owned_client: bool, client: httpx.Client
) -> Iterator[dict]:
    """Iterate over dataflows, fetching SDMX-JSON per flow + decoding observations."""
    cap = opts.max_observations
    emitted = 0
    try:
        for dataflow in opts.dataflows:
            url = _wb_query_url(opts, dataflow)
            resp = client.get(url)
            resp.raise_for_status()
            payload = resp.json()
            for row in _iter_observations_from_payload(payload, fallback_id=dataflow):
                yield row
                emitted += 1
                if cap is not None and emitted >= cap:
                    return
    finally:
        if owned_client:
            client.close()


def fetch(staging_dir: Path, opts: EuEurostatFetchOpts) -> FetchResult:
    """Stage Eurostat SDMX-JSON into the staging directory.

    Always writes ``eurostat.ndjson`` (sensor-consumable).
    """
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"eurostat-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    ndjson_path = out_dir / "eurostat.ndjson"
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
                    if isinstance(raw_row, dict) and "indicatorCode" in raw_row:
                        yield raw_row
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
        if not opts.dataflows:
            raise ValueError(
                "EuEurostatFetchOpts.dataflows must be non-empty in "
                "network mode (no implicit full-catalog fetch — caller "
                "must select dataflows explicitly per ADR-2605262400 §7 "
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
        url_attr = f"{opts.sdmx_base}/data/<dataflow>/?format={opts.fmt}"
        source_type = "http"

    revision = f"sha256:{raw_sha}"
    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="eurostat",
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
            "dataflows": list(opts.dataflows) if opts.dataflows else [],
            "license": "eurostat-free-reuse",
            "tier": "A",
            "format": opts.fmt,
        },
    )


__all__ = [
    "DEFAULT_BULK_BASE",
    "DEFAULT_SDMX_BASE",
    "EuEurostatFetchOpts",
    "fetch",
]
