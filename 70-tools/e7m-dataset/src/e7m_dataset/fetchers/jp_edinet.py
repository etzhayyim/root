"""JP 金融庁 EDINET v2 documents API fetcher — W1 concrete impl.

Per ADR-2605263800 W1. EDINET (Electronic Disclosure for Investors'
NETwork) is the JP 金融庁 (Financial Services Agency) public filings
repository for ~4K filers — 有価証券報告書 / 半期報告書 / 大量保有報告書
etc. — under **金融庁 open-data utilization terms** (~CC-BY 4.0
equivalent for practical purposes).

  https://disclosure.edinet-fsa.go.jp/api/v2/documents.json?date=YYYY-MM-DD&type=2
  https://disclosure.edinet-fsa.go.jp/api/v2/documents/<docID>?type=1     (XBRL ZIP)

The v2 documents.json endpoint returns per-day filing metadata:

  {
    "metadata": {
      "title": "提出された有価証券報告書等",
      "resultset": {"count": 234},
      "processDateTime": "..."
    },
    "results": [
      {"seqNumber": 1, "docID": "S100ABCD",
       "edinetCode": "E01777", "filerName": "ソニーグループ株式会社",
       "fundCode": null, "ordinanceCode": "010", "formCode": "120000",
       "docTypeCode": "120",
       "periodStart": "2024-04-01", "periodEnd": "2025-03-31",
       "submitDateTime": "2025-06-23T07:00:00+09:00",
       "docDescription": "有価証券報告書－第108期",
       ...},
      ...
    ]
  }

This fetcher normalizes the per-day results into NDJSON consumable
by ``kotodama.organism.sensors.corp.jp_edinet_sensor.JpEdinetSensor``:

  {"entityLocalId": "E01777", "formTypeNative": "120",
   "filedAtUtc": "2025-06-22T22:00:00Z",  # JST → UTC
   "payloadCid": "S100ABCD",              # docID; W2 → actual IPFS CID after publish-ipfs
   "entityLei": null,
   "filerName": "ソニーグループ株式会社"}

Per-document XBRL download is W2 scope; W1 publishes the docID as
payloadCid (operator can resolve to actual XBRL bytes via a W2
`e7m-dataset fetch-edinet-xbrl --doc-id S100ABCD` follow-up call).

Two operator paths matching the established pattern:

1. **Network mode** (``local_source=None``, default): httpx GET
   against the v2 documents.json endpoint per day in
   ``date_from``..``date_to`` range. Requires ``api_key`` (free
   per-DID Subscription-Key from EDINET registration).

2. **Local-source mode** (``local_source=<Path>``): read operator-
   staged documents.json OR pre-normalized NDJSON. Canonical test
   path + air-gapped fleet path.

Passive-only invariant boundary: this fetcher is OPERATOR-triggered,
NOT organism-tick, per ADR-2605262400 §7. Vendor commercial-terminal
imports (Bloomberg Terminal / Refinitiv / FactSet / Moody's Orbis /
D&B Hoovers / Pitchbook / Crunchbase Pro) are CONSTITUTIONALLY
PROHIBITED per Charter Rider §2(e)+§2(c).

Per ADR-2605263800 §5 publication-redaction policy: EDINET pass-
through (upstream publishes 役員 + 大量保有提出者 + 株主 lists).
個人情報保護法 + 金融商品取引法 redaction is upstream-applied at
publication time; this fetcher does NOT re-redact. GDPR-class
right-to-be-forgotten DSARs route through ``chigiri.data_privacy``
to upstream publisher.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

import httpx

from . import FetchResult

DEFAULT_DOCUMENTS_API = "https://disclosure.edinet-fsa.go.jp/api/v2/documents.json"
DEFAULT_DOCUMENT_DOWNLOAD = "https://disclosure.edinet-fsa.go.jp/api/v2/documents"

# EDINET submitDateTime format: "YYYY-MM-DDTHH:MM:SS+09:00" (JST fixed).
_SUBMIT_DT_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})([+-]\d{2}):(\d{2})$"
)


@dataclass
class JpEdinetFetchOpts:
    documents_api: str = DEFAULT_DOCUMENTS_API
    document_download_base: str = DEFAULT_DOCUMENT_DOWNLOAD
    api_key: Optional[str] = None  # EDINET v2 Subscription-Key (free per-DID)
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    date_from: Optional[str] = None  # ISO-8601 YYYY-MM-DD
    date_to: Optional[str] = None
    # Optional filter: only emit rows whose docTypeCode matches.
    # Default = the canonical 7 codes covered by JpEdinetSensor's
    # _FORM_CLASS_MAP (030/120/140/150/160/350/360).
    doc_type_filter: tuple[str, ...] = ()
    # Local-source mode: read this path (documents.json OR NDJSON).
    local_source: Optional[Path] = None
    max_records: Optional[int] = None
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _coerce_jst_to_utc(submit_dt: str) -> Optional[str]:
    """Convert EDINET submitDateTime (JST or +HH:MM tz) → UTC ISO-8601 'T..Z'.

    Returns None for malformed input (G7 schema discipline).
    """
    if not submit_dt:
        return None
    m = _SUBMIT_DT_RE.match(submit_dt.strip())
    if not m:
        return None
    yyyy, mm, dd, hh, mi, ss, tz_h, tz_m = m.groups()
    try:
        dt = _dt.datetime(
            int(yyyy), int(mm), int(dd), int(hh), int(mi), int(ss),
            tzinfo=_dt.timezone(
                _dt.timedelta(hours=int(tz_h), minutes=int(tz_m) if tz_h.startswith("+") else -int(tz_m))
            ),
        )
    except (ValueError, TypeError):
        return None
    utc = dt.astimezone(_dt.timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_edinet_doc(rec: dict) -> Optional[dict]:
    """Normalize a single EDINET v2 documents.json result row.

    Returns None for rows missing required fields (G7 schema discipline).
    """
    edinet_code = str(rec.get("edinetCode", "")).strip()
    doc_id = str(rec.get("docID", "")).strip()
    submit_dt = str(rec.get("submitDateTime", "")).strip()
    doc_type_code = str(rec.get("docTypeCode", "")).strip()
    if not (edinet_code and doc_id and submit_dt and doc_type_code):
        return None
    filed_at_utc = _coerce_jst_to_utc(submit_dt)
    if filed_at_utc is None:
        return None
    return {
        "entityLocalId": edinet_code,
        "formTypeNative": doc_type_code,
        "filedAtUtc": filed_at_utc,
        "payloadCid": doc_id,
        "entityLei": None,  # EDINET response does not carry LEI
        "filerName": str(rec.get("filerName", "")) or None,
    }


def _iter_observations_from_payload(payload: Any) -> Iterator[dict]:
    """Dispatch on payload shape: documents.json native / flat list /
    pre-normalized NDJSON envelope."""
    if isinstance(payload, dict):
        # Native EDINET documents.json shape.
        results = payload.get("results")
        if isinstance(results, list):
            for rec in results:
                if not isinstance(rec, dict):
                    continue
                if "entityLocalId" in rec and "formTypeNative" in rec:
                    yield rec
                    continue
                normalized = _normalize_edinet_doc(rec)
                if normalized is not None:
                    yield normalized
            return
        # Pre-normalized single envelope.
        if "entityLocalId" in payload and "formTypeNative" in payload:
            yield payload
            return
    if isinstance(payload, list):
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            if "entityLocalId" in entry and "formTypeNative" in entry:
                yield entry
                continue
            normalized = _normalize_edinet_doc(entry)
            if normalized is not None:
                yield normalized


def _iter_date_range(date_from: str, date_to: str) -> Iterator[str]:
    """Yield 'YYYY-MM-DD' strings inclusively from date_from to date_to."""
    start = _dt.date.fromisoformat(date_from)
    end = _dt.date.fromisoformat(date_to)
    if end < start:
        raise ValueError(f"date_to ({date_to}) must be >= date_from ({date_from})")
    cur = start
    while cur <= end:
        yield cur.isoformat()
        cur += _dt.timedelta(days=1)


def _network_iter(
    opts: JpEdinetFetchOpts, owned_client: bool, client: httpx.Client
) -> Iterator[dict]:
    cap = opts.max_records
    emitted = 0
    headers = {"Subscription-Key": opts.api_key} if opts.api_key else {}
    try:
        for date_iso in _iter_date_range(opts.date_from, opts.date_to):
            url = f"{opts.documents_api}?date={date_iso}&type=2"
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
            for row in _iter_observations_from_payload(payload):
                yield row
                emitted += 1
                if cap is not None and emitted >= cap:
                    return
    finally:
        if owned_client:
            client.close()


def _apply_filters(rows: Iterator[dict], opts: JpEdinetFetchOpts) -> Iterator[dict]:
    type_set = set(opts.doc_type_filter) if opts.doc_type_filter else None
    cap = opts.max_records
    emitted = 0
    for row in rows:
        if type_set is not None and row.get("formTypeNative") not in type_set:
            continue
        yield row
        emitted += 1
        if cap is not None and emitted >= cap:
            return


def fetch(staging_dir: Path, opts: JpEdinetFetchOpts) -> FetchResult:
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"jp-edinet-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    ndjson_path = out_dir / "jp-edinet.ndjson"
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
                        if "entityLocalId" in raw_row and "formTypeNative" in raw_row:
                            yield raw_row
                        else:
                            normalized = _normalize_edinet_doc(raw_row)
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
        if not (opts.date_from and opts.date_to):
            raise ValueError(
                "JpEdinetFetchOpts.date_from + date_to must both be set "
                "in network mode (passive-only: no implicit full-archive "
                "scan per ADR-2605262400 §7)."
            )
        if not opts.api_key:
            raise ValueError(
                "JpEdinetFetchOpts.api_key (EDINET v2 Subscription-Key) "
                "required in network mode. Register for free at "
                "https://disclosure.edinet-fsa.go.jp/."
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
        url_attr = f"{opts.documents_api}?date=<YYYY-MM-DD>&type=2"
        source_type = "http"

    revision = f"sha256:{raw_sha}"
    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="jp-edinet",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": source_type,
            "url": url_attr,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "filingCount": rows_emitted,
            "dateFrom": opts.date_from,
            "dateTo": opts.date_to,
            "docTypeFilterApplied": bool(opts.doc_type_filter),
            "license": "fsa-open-data-utilization-terms",
            "tier": "A",
        },
    )


__all__ = [
    "DEFAULT_DOCUMENTS_API",
    "DEFAULT_DOCUMENT_DOWNLOAD",
    "JpEdinetFetchOpts",
    "fetch",
]
