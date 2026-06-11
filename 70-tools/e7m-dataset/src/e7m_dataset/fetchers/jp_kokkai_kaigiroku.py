"""JP 国会会議録検索 API fetcher — W1 concrete impl.

Per ADR-2605263900 W1. 国会会議録検索 (Kokkai Kaigiroku Kensaku) is
the official searchable archive of Japanese National Diet meeting
records (both Houses, all committees, since 1947). Published by the
National Diet Library (国会図書館) as **公の著作物 free-use** under
著作権法 §13. No API key required.

  https://kokkai.ndl.go.jp/api/meeting?from=YYYY-MM-DD&until=YYYY-MM-DD&recordPacking=json&maximumRecords=N&startRecord=S

Response shape (meeting endpoint, recordPacking=json):

  {
    "numberOfRecords": 234,
    "numberOfReturn": 30,
    "startRecord": 1,
    "nextRecordPosition": 31,
    "meetingRecord": [
      {"issueID": "121705254X02320250121",
       "session": 217,
       "nameOfHouse": "衆議院",
       "nameOfMeeting": "本会議",
       "issue": "第23号",
       "date": "2025-01-21",
       "speechRecord": [
         {"speechID": "...", "speechOrder": 1,
          "speaker": "額賀福志郎", "speakerYomi": "...",
          "speakerGroup": "...", "speakerPosition": "議長",
          "speech": "○議長(額賀福志郎君) ..."},
         ...
       ],
       "meetingURL": "https://kokkai.ndl.go.jp/...",
       "pdfURL": "https://kokkai.ndl.go.jp/...pdf"},
      ...
    ]
  }

This W1 fetcher emits one observation per meeting (with first-speaker
preview); W2 will optionally split into per-speech granular
observations via ``granularity="speech"`` opt.

Normalized NDJSON consumable by
``kotodama.organism.sensors.gov.jp_kokkai_kaigiroku_sensor.JpKokkaiKaigirokuSensor``:

  {"recordId": "121705254X02320250121",
   "sessionDateUtc": "2025-01-21T00:00:00Z",
   "payloadCid": "https://kokkai.ndl.go.jp/...",
   "house": "衆議院",
   "nativeKind": "本会議",
   "speakerName": "額賀福志郎",
   "speakerRole": "議長"}

``nameOfMeeting`` passes through directly as ``nativeKind`` (sensor's
_RECORD_KIND_MAP already covers 本会議 / 予算委員会 / 委員会 /
代表質問 / 法律案 / 採決 etc.). First speaker's `speaker` +
`speakerPosition` are extracted for the meeting-level preview.

Two operator paths matching the established pattern:

1. **Network mode** (default): httpx GET with start/end date range.
2. **Local-source mode**: read operator-staged JSON OR NDJSON.

Passive-only invariant boundary: this fetcher is OPERATOR-triggered,
NOT organism-tick, per ADR-2605262400 §7. Vendor commercial gov-intel
terminal imports CONSTITUTIONALLY PROHIBITED per Charter Rider
§2(e)+§2(c).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Literal, Optional

import httpx

from . import FetchResult

DEFAULT_API_BASE = "https://kokkai.ndl.go.jp/api"

# NDL meeting date format: YYYY-MM-DD.
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Canonical 院 values.
_HOUSE_VALUES: set[str] = {"衆議院", "参議院"}


@dataclass
class JpKokkaiKaigirokuFetchOpts:
    api_base: str = DEFAULT_API_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    granularity: Literal["meeting"] = "meeting"  # W2 adds "speech"
    house: Literal["衆議院", "参議院", "both"] = "both"
    from_date: Optional[str] = None  # YYYY-MM-DD; required in network mode
    until_date: Optional[str] = None
    local_source: Optional[Path] = None
    page_size: int = 100  # NDL maximumRecords max
    max_records: Optional[int] = None
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _coerce_meeting_date(raw: str) -> Optional[str]:
    """Coerce 'YYYY-MM-DD' → 'YYYY-MM-DDT00:00:00Z'. None for malformed."""
    if not raw:
        return None
    if not _DATE_RE.match(raw.strip()):
        return None
    return f"{raw.strip()}T00:00:00Z"


def _normalize_meeting(rec: dict) -> Optional[dict]:
    """Normalize one NDL meetingRecord entry → sensor row.

    Returns None for rows missing required fields (G7).
    """
    issue_id = str(rec.get("issueID", "")).strip()
    house = str(rec.get("nameOfHouse", "")).strip()
    name_of_meeting = str(rec.get("nameOfMeeting", "")).strip()
    date = str(rec.get("date", "")).strip()
    if not (issue_id and house in _HOUSE_VALUES and name_of_meeting and date):
        return None
    session_date_utc = _coerce_meeting_date(date)
    if session_date_utc is None:
        return None
    payload_cid = (
        str(rec.get("meetingURL", "")).strip()
        or str(rec.get("pdfURL", "")).strip()
        or issue_id
    )
    # First-speaker preview.
    speech_record = rec.get("speechRecord")
    speaker_name: Optional[str] = None
    speaker_role: Optional[str] = None
    body_excerpt: Optional[str] = None
    if isinstance(speech_record, list) and speech_record:
        first = speech_record[0]
        if isinstance(first, dict):
            speaker_name = str(first.get("speaker", "")) or None
            speaker_role = str(first.get("speakerPosition", "")) or None
            body_excerpt = str(first.get("speech", ""))[:4096] or None
    return {
        "recordId": issue_id,
        "sessionDateUtc": session_date_utc,
        "payloadCid": payload_cid,
        "house": house,
        "nativeKind": name_of_meeting,
        "speakerName": speaker_name,
        "speakerRole": speaker_role,
        "bodyExcerpt": body_excerpt,
        "session": rec.get("session"),
        "issue": str(rec.get("issue", "")) or None,
    }


def _iter_observations_from_payload(payload: Any) -> Iterator[dict]:
    """Dispatch: NDL meeting search / flat list / NDJSON envelope."""
    if isinstance(payload, dict):
        meetings = payload.get("meetingRecord")
        if isinstance(meetings, list):
            for rec in meetings:
                if not isinstance(rec, dict):
                    continue
                if "recordId" in rec and "house" in rec:
                    yield rec
                    continue
                normalized = _normalize_meeting(rec)
                if normalized is not None:
                    yield normalized
            return
        if "recordId" in payload and "house" in payload:
            yield payload
            return
    if isinstance(payload, list):
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            if "recordId" in entry and "house" in entry:
                yield entry
                continue
            normalized = _normalize_meeting(entry)
            if normalized is not None:
                yield normalized


def _build_query(opts: JpKokkaiKaigirokuFetchOpts, start_record: int) -> str:
    params: dict[str, str] = {
        "from": opts.from_date or "",
        "until": opts.until_date or "",
        "recordPacking": "json",
        "maximumRecords": str(opts.page_size),
        "startRecord": str(start_record),
    }
    if opts.house != "both":
        params["nameOfHouse"] = opts.house
    return f"{opts.api_base}/meeting?{urllib.parse.urlencode(params)}"


def _network_iter(
    opts: JpKokkaiKaigirokuFetchOpts, owned_client: bool, client: httpx.Client
) -> Iterator[dict]:
    cap = opts.max_records
    emitted = 0
    start_record = 1
    try:
        while True:
            url = _build_query(opts, start_record)
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
            next_pos = None
            if isinstance(payload, dict):
                total = payload.get("numberOfRecords")
                next_pos = payload.get("nextRecordPosition")
            if not isinstance(total, int) or yielded_in_page == 0:
                break
            if isinstance(next_pos, int) and next_pos > start_record:
                start_record = next_pos
            else:
                break
            if start_record > total:
                break
    finally:
        if owned_client:
            client.close()


def fetch(staging_dir: Path, opts: JpKokkaiKaigirokuFetchOpts) -> FetchResult:
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"jp-kokkai-kaigiroku-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    ndjson_path = out_dir / "jp-kokkai-kaigiroku.ndjson"
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
                        if "recordId" in raw_row and "house" in raw_row:
                            yield raw_row
                        else:
                            normalized = _normalize_meeting(raw_row)
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
        if not (opts.from_date and opts.until_date):
            raise ValueError(
                "JpKokkaiKaigirokuFetchOpts.from_date + until_date must "
                "both be set in network mode (passive-only: no implicit "
                "full-archive scan per ADR-2605262400 §7)."
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
        url_attr = f"{opts.api_base}/meeting"
        source_type = "http"

    revision = f"sha256:{raw_sha}"
    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="jp-kokkai-kaigiroku",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": source_type,
            "url": url_attr,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "meetingCount": rows_emitted,
            "fromDate": opts.from_date,
            "untilDate": opts.until_date,
            "house": opts.house,
            "granularity": opts.granularity,
            "license": "ndl-public-record-free-use",
            "tier": "A",
        },
    )


__all__ = [
    "DEFAULT_API_BASE",
    "JpKokkaiKaigirokuFetchOpts",
    "fetch",
]
