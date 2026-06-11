"""UK Parliament Hansard API fetcher — W1 concrete impl.

Per ADR-2605263900 W1. Hansard is the official report of debates in
the UK Parliament (Commons + Lords). The Parliamentary Data Service
publishes Hansard under **OGL v3.0** (Open Parliament Licence
mirrors the Open Government Licence). No API key required.

  https://hansard-api.parliament.uk/search/debates.json?queryParameters.startDate=YYYY-MM-DD&queryParameters.endDate=YYYY-MM-DD&queryParameters.house=Commons|Lords&queryParameters.take=N&queryParameters.skip=S

Search response shape (debates endpoint):

  {
    "TotalContributionResults": 234,
    "Results": [
      {"DebateSection": "Oral Answers to Questions",
       "DebateSectionExtId": "ABC-DEF-GHI",
       "House": "Commons",
       "SittingDate": "2026-05-20T00:00:00",
       "Title": "Health and Social Care",
       "AttributedTo": "Wes Streeting (Ilford North) (Lab)",
       "ContributionText": "...",
       "ContributionExtId": "abc123",
       "OrderInDebateSection": 12, ...},
      ...
    ]
  }

Normalized into NDJSON consumable by
``kotodama.organism.sensors.gov.uk_hansard_sensor.UkHansardSensor``:

  {"recordId": "ABC-DEF-GHI",
   "sessionDateUtc": "2026-05-20T00:00:00Z",
   "payloadCid": "https://hansard.parliament.uk/Commons/2026-05-20/debates/ABC-DEF-GHI/",
   "house": "Commons",
   "nativeKind": "Oral Question",
   "speakerName": "Wes Streeting",
   "speakerRole": "Ilford North / Lab"}

``nativeKind`` is synthesized from ``DebateSection`` heuristic:
"Oral Answers..." → "Oral Question"; "Petition..." → "Petition";
"Division..." → "Division"; etc. Default = "Debate".
``AttributedTo`` is parsed for speaker name (before first parenthesis)
and role (parenthetical content joined by " / ").

Two operator paths matching the established pattern:

1. **Network mode** (default): httpx GET with paged take/skip;
   start_date + end_date MUST be set (passive-only).

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

DEFAULT_API_BASE = "https://hansard-api.parliament.uk"

# AttributedTo parser: "Name (Constituency) (Party)" or similar variants.
_ATTRIB_RE = re.compile(r"^([^(]+?)\s*(\([^)]+\)(?:\s*\([^)]+\))*)?\s*$")
_PAREN_RE = re.compile(r"\(([^)]+)\)")


@dataclass
class UkHansardFetchOpts:
    api_base: str = DEFAULT_API_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    start_date: Optional[str] = None  # YYYY-MM-DD; required in network mode
    end_date: Optional[str] = None
    house: Literal["Commons", "Lords", "Both"] = "Both"
    local_source: Optional[Path] = None
    page_size: int = 100
    max_records: Optional[int] = None
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _synthesize_native_kind(debate_section: str) -> str:
    s = (debate_section or "").lower()
    if "oral" in s and ("question" in s or "answer" in s):
        return "Oral Question"
    if "written question" in s:
        return "Written Question"
    if "petition" in s:
        return "Petition"
    if "division" in s:
        return "Division"
    if "written statement" in s:
        return "Written Statement"
    if "personal statement" in s:
        return "Personal Statement"
    if "committee" in s:
        return "Committee"
    if "bill" in s and ("reading" in s or "stage" in s):
        return "Bill Reading"
    if "bill" in s:
        return "Bill"
    return "Debate"


def _parse_attributed_to(attributed_to: str) -> tuple[Optional[str], Optional[str]]:
    if not attributed_to:
        return None, None
    m = _ATTRIB_RE.match(attributed_to.strip())
    if not m:
        return attributed_to.strip(), None
    name = m.group(1).strip() or None
    parens = m.group(2) or ""
    role_parts = _PAREN_RE.findall(parens)
    role = " / ".join(role_parts) if role_parts else None
    return name, role


def _coerce_sitting_date(raw: str) -> Optional[str]:
    if not raw:
        return None
    s = raw.strip()
    if s.endswith("Z") or re.search(r"[+-]\d{2}:?\d{2}$", s):
        return s
    if "T" in s and len(s) >= 19:
        return s[:19] + "Z"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return f"{s}T00:00:00Z"
    return None


def _normalize_hansard_contribution(rec: dict) -> Optional[dict]:
    record_id = (
        str(rec.get("DebateSectionExtId", "")).strip()
        or str(rec.get("ContributionExtId", "")).strip()
    )
    house = str(rec.get("House", "")).strip()
    sitting_date = str(rec.get("SittingDate", "")).strip()
    debate_section = str(rec.get("DebateSection", "")).strip()
    if not (record_id and house in ("Commons", "Lords") and sitting_date):
        return None
    session_date_utc = _coerce_sitting_date(sitting_date)
    if session_date_utc is None:
        return None
    native_kind = _synthesize_native_kind(debate_section)
    name, role = _parse_attributed_to(str(rec.get("AttributedTo", "")))
    payload_cid = str(rec.get("Url", "")).strip()
    if not payload_cid:
        date_part = session_date_utc[:10]
        payload_cid = (
            f"https://hansard.parliament.uk/{house}/{date_part}/debates/"
            f"{record_id}/"
        )
    return {
        "recordId": record_id,
        "sessionDateUtc": session_date_utc,
        "payloadCid": payload_cid,
        "house": house,
        "nativeKind": native_kind,
        "speakerName": name,
        "speakerRole": role,
        "bodyExcerpt": str(rec.get("ContributionText", ""))[:4096] or None,
        "debateTitle": str(rec.get("Title", "")) or None,
    }


def _iter_observations_from_payload(payload: Any) -> Iterator[dict]:
    if isinstance(payload, dict):
        results = payload.get("Results")
        if isinstance(results, list):
            for rec in results:
                if not isinstance(rec, dict):
                    continue
                if "recordId" in rec and "house" in rec:
                    yield rec
                    continue
                normalized = _normalize_hansard_contribution(rec)
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
            normalized = _normalize_hansard_contribution(entry)
            if normalized is not None:
                yield normalized


def _build_query(opts: UkHansardFetchOpts, skip: int) -> str:
    params: dict[str, str] = {
        "queryParameters.startDate": opts.start_date or "",
        "queryParameters.endDate": opts.end_date or "",
        "queryParameters.take": str(opts.page_size),
        "queryParameters.skip": str(skip),
    }
    if opts.house != "Both":
        params["queryParameters.house"] = opts.house
    return f"{opts.api_base}/search/debates.json?{urllib.parse.urlencode(params)}"


def _network_iter(
    opts: UkHansardFetchOpts, owned_client: bool, client: httpx.Client
) -> Iterator[dict]:
    cap = opts.max_records
    emitted = 0
    skip = 0
    try:
        while True:
            url = _build_query(opts, skip)
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
            if isinstance(payload, dict):
                total = payload.get("TotalContributionResults")
            if not isinstance(total, int) or yielded_in_page == 0:
                break
            skip += opts.page_size
            if skip >= total:
                break
    finally:
        if owned_client:
            client.close()


def fetch(staging_dir: Path, opts: UkHansardFetchOpts) -> FetchResult:
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"uk-hansard-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    ndjson_path = out_dir / "uk-hansard.ndjson"
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
                            normalized = _normalize_hansard_contribution(raw_row)
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
        if not (opts.start_date and opts.end_date):
            raise ValueError(
                "UkHansardFetchOpts.start_date + end_date must both be "
                "set in network mode (passive-only: no implicit full-"
                "archive scan per ADR-2605262400 §7)."
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
        url_attr = f"{opts.api_base}/search/debates.json"
        source_type = "http"

    revision = f"sha256:{raw_sha}"
    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="uk-hansard",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": source_type,
            "url": url_attr,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "contributionCount": rows_emitted,
            "startDate": opts.start_date,
            "endDate": opts.end_date,
            "house": opts.house,
            "license": "OGL-v3.0",
            "tier": "A",
        },
    )


__all__ = [
    "DEFAULT_API_BASE",
    "UkHansardFetchOpts",
    "fetch",
]
