"""US Congress.gov api.congress.gov v3 fetcher — W1 concrete impl.

Per ADR-2605263900 W1. Congress.gov publishes federal legislative
data (bills + bill status + roll-call votes + Congressional Record
+ committee reports + treaty documents) under **public domain**
(US federal government works are not copyrighted per 17 USC 105).

W1 targets the **api.congress.gov v3 REST API** (`/v3/bill` endpoint)
as the operationally-cheapest passive-only entry point:

  https://api.congress.gov/v3/bill?congress=119&fromDateTime=2025-01-01T00:00:00Z&toDateTime=...&limit=N&offset=O

Requires a free per-DID API key (X-Api-Key header) from
``https://api.congress.gov/sign-up``.

Response shape:

  {
    "bills": [
      {"congress": 119, "type": "HR", "number": 1234, "title": "...",
       "introducedDate": "2025-02-13",
       "originChamber": "House", "originChamberCode": "H",
       "updateDate": "2025-02-14",
       "url": "https://api.congress.gov/v3/bill/119/hr/1234?format=json",
       ...},
      ...
    ],
    "pagination": {"count": 234, "next": "..."}
  }

W2 will add:
- Other v3 endpoints: ``/v3/congressional-record``,
  ``/v3/house-roll-call-vote``, ``/v3/senate-roll-call-vote``,
  ``/v3/committee-report``
- govinfo.gov bulkdata XML collections (BILLS / BILLSTATUS / CREC / FR)
  as a separate operator path

Normalized NDJSON consumable by
``kotodama.organism.sensors.gov.us_congress_gov_sensor.UsCongressGovSensor``:

  {"recordId": "BILLS-119hr1234",
   "sessionDateUtc": "2025-02-13T00:00:00Z",
   "payloadCid": "https://api.congress.gov/v3/bill/119/hr/1234",
   "chamber": "House",
   "nativeKind": "House Bill"}

The ``nativeKind`` is synthesized from (chamber + bill type) — e.g.,
House+HR → "House Bill", Senate+S → "Senate Bill", Either+HJRES → "Joint
Resolution", etc. (See ``_canonical_native_kind``.) Sensor maps
these to ParliamentRecordKind via its own ``_RECORD_KIND_MAP``.

Two operator paths matching the established pattern:

1. **Network mode** (default): httpx GET with api_key header + paging.
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
import re
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

import httpx

from . import FetchResult

DEFAULT_API_BASE = "https://api.congress.gov/v3"
DEFAULT_BULK_BASE = "https://www.govinfo.gov/bulkdata"  # W2

# Bill type → canonical nativeKind synthesis (sensor mapping consumer).
_BILL_TYPE_NATIVE: dict[str, str] = {
    "HR": "House Bill",
    "S": "Senate Bill",
    "HJRES": "Joint Resolution",
    "SJRES": "Joint Resolution",
    "HCONRES": "Concurrent Resolution",
    "SCONRES": "Concurrent Resolution",
    "HRES": "Simple Resolution",
    "SRES": "Simple Resolution",
}

# YYYY-MM-DD strict — bill API introducedDate / updateDate format.
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class UsCongressGovFetchOpts:
    api_base: str = DEFAULT_API_BASE
    bulk_base: str = DEFAULT_BULK_BASE  # reserved for W2 govinfo bulkdata
    api_key: Optional[str] = None  # X-Api-Key header (free per-DID)
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    congress: Optional[int] = None  # e.g. 119 for the 119th Congress
    # Optional date window (ISO-8601 datetime); applied as
    # fromDateTime + toDateTime query params.
    from_datetime_utc: Optional[str] = None
    to_datetime_utc: Optional[str] = None
    # Optional bill-type filter applied client-side after fetch.
    bill_type_allowlist: tuple[str, ...] = ()
    # Local-source mode: skip HTTPS.
    local_source: Optional[Path] = None
    page_size: int = 250  # api.congress.gov v3 supports up to 250
    max_records: Optional[int] = None
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _canonical_native_kind(chamber: str, bill_type: str) -> Optional[str]:
    """Synthesize a sensor-compatible nativeKind string from (chamber,
    bill type). Returns None for unknown bill_type (G7 sensor will skip)."""
    return _BILL_TYPE_NATIVE.get(bill_type.upper())


def _coerce_intro_date(raw: str) -> Optional[str]:
    """Coerce YYYY-MM-DD → ISO-8601 T00:00:00Z. None for malformed."""
    if not raw:
        return None
    if not _DATE_RE.match(raw.strip()):
        return None
    return f"{raw.strip()}T00:00:00Z"


def _normalize_bill(rec: dict) -> Optional[dict]:
    """Normalize a single api.congress.gov v3 bill row → sensor shape.

    Returns None for rows missing required fields (G7).
    """
    congress = rec.get("congress")
    bill_type_raw = str(rec.get("type", "")).strip()
    number = rec.get("number")
    chamber = str(rec.get("originChamber", "")).strip()
    intro_date = str(rec.get("introducedDate", "")).strip()
    url = str(rec.get("url", "")).strip()
    if not (
        isinstance(congress, int)
        and bill_type_raw
        and number is not None
        and chamber in ("House", "Senate")
        and intro_date
    ):
        return None
    session_date_utc = _coerce_intro_date(intro_date)
    if session_date_utc is None:
        return None
    native_kind = _canonical_native_kind(chamber, bill_type_raw)
    if native_kind is None:
        return None
    # Synthesize EDGAR-style recordId: BILLS-<congress><lower-type><number>
    record_id = f"BILLS-{congress}{bill_type_raw.lower()}{number}"
    return {
        "recordId": record_id,
        "sessionDateUtc": session_date_utc,
        "payloadCid": url or record_id,
        "chamber": chamber,
        "nativeKind": native_kind,
        "billType": bill_type_raw,
        "congressNumber": congress,
        "billTitle": str(rec.get("title", "")) or None,
    }


def _iter_observations_from_payload(payload: Any) -> Iterator[dict]:
    """Dispatch on payload shape: api.congress.gov / flat list / NDJSON."""
    if isinstance(payload, dict):
        bills = payload.get("bills")
        if isinstance(bills, list):
            for rec in bills:
                if not isinstance(rec, dict):
                    continue
                if "recordId" in rec and "chamber" in rec:
                    yield rec
                    continue
                normalized = _normalize_bill(rec)
                if normalized is not None:
                    yield normalized
            return
        if "recordId" in payload and "chamber" in payload:
            yield payload
            return
    if isinstance(payload, list):
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            if "recordId" in entry and "chamber" in entry:
                yield entry
                continue
            normalized = _normalize_bill(entry)
            if normalized is not None:
                yield normalized


def _build_query(opts: UsCongressGovFetchOpts, offset: int) -> str:
    params: dict[str, str] = {
        "limit": str(opts.page_size),
        "offset": str(offset),
        "format": "json",
    }
    if opts.from_datetime_utc:
        params["fromDateTime"] = opts.from_datetime_utc
    if opts.to_datetime_utc:
        params["toDateTime"] = opts.to_datetime_utc
    qs = urllib.parse.urlencode(params)
    return f"{opts.api_base}/bill/{opts.congress}?{qs}"


def _network_iter(
    opts: UsCongressGovFetchOpts, owned_client: bool, client: httpx.Client
) -> Iterator[dict]:
    cap = opts.max_records
    emitted = 0
    offset = 0
    headers = {"X-Api-Key": opts.api_key} if opts.api_key else {}
    try:
        while True:
            url = _build_query(opts, offset)
            resp = client.get(url, headers=headers)
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
            if isinstance(payload, dict):
                pag = payload.get("pagination", {})
                if isinstance(pag, dict):
                    total = pag.get("count")
            if not isinstance(total, int) or yielded_in_page == 0:
                break
            offset += opts.page_size
            if offset >= total:
                break
    finally:
        if owned_client:
            client.close()


def _apply_filters(rows: Iterator[dict], opts: UsCongressGovFetchOpts) -> Iterator[dict]:
    type_set = set(t.upper() for t in opts.bill_type_allowlist) if opts.bill_type_allowlist else None
    cap = opts.max_records
    emitted = 0
    for row in rows:
        if type_set is not None:
            bt = (row.get("billType") or "").upper()
            if bt not in type_set:
                continue
        yield row
        emitted += 1
        if cap is not None and emitted >= cap:
            return


def fetch(staging_dir: Path, opts: UsCongressGovFetchOpts) -> FetchResult:
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"us-congress-gov-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    ndjson_path = out_dir / "us-congress-gov.ndjson"
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
                        if "recordId" in raw_row and "chamber" in raw_row:
                            yield raw_row
                        else:
                            normalized = _normalize_bill(raw_row)
                            if normalized is not None:
                                yield normalized
            iterator = _ndjson_iter()
        if opts.write_ndjson:
            with ndjson_path.open("w", encoding="utf-8") as f:
                for row in _apply_filters(iterator, opts):
                    f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
                    f.write("\n")
                    rows_emitted += 1
        url_attr = str(path)
        source_type = "local"
    else:
        if opts.congress is None:
            raise ValueError(
                "UsCongressGovFetchOpts.congress must be set in network "
                "mode (e.g. 119 for the 119th Congress) — passive-only: "
                "no implicit latest-congress inference per ADR-2605262400 §7."
            )
        if not opts.api_key:
            raise ValueError(
                "UsCongressGovFetchOpts.api_key (X-Api-Key header) "
                "required in network mode. Register for free at "
                "https://api.congress.gov/sign-up."
            )
        owned_client = opts.client is None
        client = opts.client or httpx.Client(
            timeout=opts.timeout_sec,
            follow_redirects=True,
            headers={"User-Agent": opts.user_agent},
        )
        hasher = hashlib.sha256()
        with ndjson_path.open("w", encoding="utf-8") as f:
            for row in _apply_filters(_network_iter(opts, owned_client, client), opts):
                line = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
                f.write(line)
                f.write("\n")
                hasher.update(line.encode("utf-8"))
                hasher.update(b"\n")
                rows_emitted += 1
        raw_sha = hasher.hexdigest()
        url_attr = f"{opts.api_base}/bill/{opts.congress}"
        source_type = "http"

    revision = f"sha256:{raw_sha}"
    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="us-congress-gov",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": source_type,
            "url": url_attr,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "billCount": rows_emitted,
            "congress": opts.congress,
            "fromDateTime": opts.from_datetime_utc,
            "toDateTime": opts.to_datetime_utc,
            "billTypeAllowlistApplied": bool(opts.bill_type_allowlist),
            "license": "public-domain",
            "tier": "A",
        },
    )


__all__ = [
    "DEFAULT_API_BASE",
    "DEFAULT_BULK_BASE",
    "UsCongressGovFetchOpts",
    "fetch",
]
