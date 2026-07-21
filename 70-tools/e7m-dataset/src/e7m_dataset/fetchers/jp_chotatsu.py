"""JP 政府調達情報ポータル (調達ポータル / p-portal.go.jp) fetcher — W3 concrete impl.

Per ADR-2605263900 W3. 落札実績オープンデータ (successful-bid / award-results open data)
from the unified 調達ポータル — https://www.p-portal.go.jp/ (formerly chotatsu.portal.go.jp /
GEPS, which now redirects there). Published under 政府標準利用規約 2.0 (CC-BY 4.0 equivalent),
Tier A. No API key required.

The portal publishes 落札実績 as bulk open data — JSON via direct URL access (per the
portal's file spec, ``rakusatsuopendata.pdf``) and CSV (ZIP) via the portal UI. There is
no formal REST API; **bulk direct-URL JSON / staged-CSV access is the G3-compliant passive
path** — no live per-query scraping, no organism-tick fetch (ADR-2605262400 §7).

**URL / field-name honesty note.** The exact bulk-download URL pattern + the precise CSV/JSON
column names are defined in the portal's ``rakusatsuopendata.pdf`` file spec, which is NOT
checked into this repo. ``DEFAULT_BULK_URL`` below is the documented open-data landing page;
the OPERATOR must confirm the exact JSON file URL against the current file spec before
network mode is exercised against the live portal, and may extend ``_FIELD_ALIASES`` for any
column-name drift. ``local_source`` mode (operator-staged JSON / CSV / NDJSON) is the
primary, immediately-usable path and is what the tests cover.

Normalized NDJSON (one row per 落札実績 award) consumable by danjo's procurement_beat and,
eventually, ``kotodama.organism.sensors.gov.jp_chotatsu_sensor``:

  {"noticeId": "...", "recordKind": "award", "contractingAuthority": "...",
   "title": "...", "awardeeName": "...", "awardeeLocalId": "...",
   "awardAmountLocal": <int yen minor units>, "currencyIso4217": "JPY",
   "awardDateUtc": "YYYY-MM-DDT00:00:00Z", "jurisdiction": "JPN",
   "sourceSensor": "jp_chotatsu", "payloadCid": "<portal notice URL or noticeId>"}

Two operator paths (mirrors jp_kokkai_kaigiroku.py):

1. **Network mode** (default): httpx GET of the bulk JSON over a date range.
2. **Local-source mode**: read operator-staged JSON / NDJSON / CSV.

Passive-only invariant boundary: this fetcher is OPERATOR-triggered, NOT organism-tick, per
ADR-2605262400 §7. Vendor commercial gov-intelligence terminal imports CONSTITUTIONALLY
PROHIBITED per Charter Rider §2(e)+§2(c) (same wall as jp_kokkai_kaigiroku).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Literal, Optional

import httpx

from . import FetchResult

DEFAULT_API_BASE = "https://www.p-portal.go.jp"
# 落札実績オープンデータ landing page (the bulk JSON file URL is documented in
# rakusatsuopendata.pdf; operator confirms the exact endpoint). Used as the network-mode
# default; tests inject a mock base via MockTransport.
DEFAULT_BULK_URL = "https://www.p-portal.go.jp/pps-web-biz/UAB02/OAB0201"

# 落札実績 = award results → every emitted row is recordKind "award".
_RECORD_KIND = "award"
_JURISDICTION = "JPN"
_SOURCE_SENSOR = "jp_chotatsu"
_LICENSE = "政府標準利用規約-2.0"
_TIER = "A"

# Tolerant column-name aliases. p-portal CSV/JSON headers are Japanese; the exact names live
# in rakusatsuopendata.pdf (not in-repo). The first present alias wins; operator may extend.
# English normalized keys (used by the representative fixture + tests) are accepted too.
_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "noticeId": ("noticeId", "公告番号", "結果公告番号", "落札結果番号", "resultId", "bidId"),
    "title": ("title", "件名", "入札件名", "調達件名", "業務名"),
    "contractingAuthority": ("contractingAuthority", "発注機関名", "発注機関", "機関名"),
    "awardeeName": ("awardeeName", "落札者名", "落札者", "落札業者名"),
    "awardeeLocalId": ("awardeeLocalId", "落札者番号", "事業者番号", "法人番号"),
    "awardAmountLocal": ("awardAmountLocal", "落札金額", "落札金額（円）", "落札金額(円)", "契約金額"),
    "awardDateRaw": ("awardDateUtc", "awardDate", "結果公告日", "公告日", "契約日", "開札日"),
}


@dataclass
class JpChotatsuFetchOpts:
    api_base: str = DEFAULT_API_BASE
    bulk_url: str = DEFAULT_BULK_URL
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    from_date: Optional[str] = None  # YYYY-MM-DD; required in network mode
    until_date: Optional[str] = None
    local_source: Optional[Path] = None
    page_size: int = 1000
    max_records: Optional[int] = None
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _pick(raw: dict[str, Any], canonical: str) -> Optional[Any]:
    """First present alias value for a canonical field, else None."""
    for alias in _FIELD_ALIASES[canonical]:
        if alias in raw and raw[alias] not in (None, ""):
            return raw[alias]
    return None


def _coerce_date(raw: Any) -> Optional[str]:
    """Coerce YYYY-MM-DD (or YYYY/MM/DD) → YYYY-MM-DDT00:00:00Z. None for malformed."""
    if raw is None:
        return None
    s = str(raw).strip().replace("/", "-")
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return f"{s[:10]}T00:00:00Z"
    return None


def _coerce_yen(raw: Any) -> Optional[int]:
    """Coerce a yen amount (string with commas / int) → int minor units (1円 = 1)."""
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    digits = str(raw).replace(",", "").replace("円", "").replace(" ", "").strip()
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _normalize_record(raw: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Normalize one p-portal 落札実績 entry → procurementRecord-conformant sensor row.

    Returns None for rows missing a required identity field (noticeId OR contractingAuthority
    OR awardeeName), mirroring jp_kokkai._normalize_meeting's G7 skip-on-malformed discipline.
    """
    if not isinstance(raw, dict):
        return None
    notice_id = _pick(raw, "noticeId")
    authority = _pick(raw, "contractingAuthority")
    awardee = _pick(raw, "awardeeName")
    # An award row is useless for cross-reference without at least one of these identities.
    if not any([notice_id, authority, awardee]):
        return None
    rid = str(notice_id or f"{authority or '?'}:{awardee or '?'}")
    amount = _coerce_yen(_pick(raw, "awardAmountLocal"))
    return {
        "noticeId": rid,
        "recordKind": _RECORD_KIND,
        "title": str(_pick(raw, "title") or "")[:1024],
        "contractingAuthority": str(authority or "")[:512],
        "awardeeName": str(awardee or "")[:512],
        "awardeeLocalId": str(_pick(raw, "awardeeLocalId") or ""),
        "awardAmountLocal": amount if amount is not None else 0,
        "currencyIso4217": "JPY",
        "awardDateUtc": _coerce_date(_pick(raw, "awardDateRaw")) or "",
        "jurisdiction": _JURISDICTION,
        "sourceSensor": _SOURCE_SENSOR,
        # payloadCid = the portal notice/result URL if present, else the noticeId (stable).
        "payloadCid": str(raw.get("payloadCid") or raw.get("url") or raw.get("結果URL") or rid),
    }


def _iter_records_from_payload(payload: Any) -> Iterator[dict[str, Any]]:
    """Dispatch: a JSON object with a list, a bare list, or a single record object."""
    if isinstance(payload, dict):
        for list_key in ("results", "records", "data", "落札実績", "items"):
            lst = payload.get(list_key)
            if isinstance(lst, list):
                for rec in lst:
                    if isinstance(rec, dict):
                        if "noticeId" in rec or "contractingAuthority" in rec:
                            yield rec
                        else:
                            norm = _normalize_record(rec)
                            if norm is not None:
                                yield rec
                return
        if "noticeId" in payload or "contractingAuthority" in payload:
            yield payload
        return
    if isinstance(payload, list):
        for rec in payload:
            if isinstance(rec, dict):
                yield rec


def _build_query(opts: JpChotatsuFetchOpts, start_record: int) -> str:
    params = {
        "from": opts.from_date or "",
        "until": opts.until_date or "",
        "format": "json",
        "count": str(opts.page_size),
        "start": str(start_record),
    }
    sep = "&" if "?" in opts.bulk_url else "?"
    return f"{opts.bulk_url}{sep}{'&'.join(f'{k}={v}' for k, v in params.items())}"


def _network_iter(
    opts: JpChotatsuFetchOpts, owned_client: bool, client: httpx.Client
) -> Iterator[dict[str, Any]]:
    """Paginated GET of the bulk JSON endpoint. Yields RAW records (normalized by caller)."""
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
            for rec in _iter_records_from_payload(payload):
                yield rec
                emitted += 1
                yielded_in_page += 1
                if cap is not None and emitted >= cap:
                    return
            # Stop if the page was empty or there is no explicit next-page signal.
            total = payload.get("numberOfRecords") if isinstance(payload, dict) else None
            if yielded_in_page == 0:
                break
            if isinstance(total, int) and emitted >= total:
                break
            start_record += yielded_in_page
            if isinstance(total, int) and start_record > total:
                break
    finally:
        if owned_client:
            client.close()


def _iter_local(path: Path) -> Iterator[dict[str, Any]]:
    """Read operator-staged JSON (single object/array) / NDJSON / CSV (UTF-8, comma)."""
    raw_text = path.read_text(encoding="utf-8-sig")
    # Try JSON first (object or array).
    try:
        payload = json.loads(raw_text)
        for rec in _iter_records_from_payload(payload):
            yield rec
        return
    except json.JSONDecodeError:
        pass
    # NDJSON (one JSON object per non-blank line).
    first_char = raw_text.lstrip()[:1]
    if first_char == "{":
        for line in raw_text.splitlines():
            s = line.strip()
            if not s:
                continue
            try:
                rec = json.loads(s)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict):
                yield rec
        return
    # CSV fallback (p-portal UI download).
    reader = csv.DictReader(io.StringIO(raw_text))
    for row in reader:
        yield {k: (v if v != "" else None) for k, v in row.items()}


def fetch(staging_dir: Path, opts: JpChotatsuFetchOpts) -> FetchResult:
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"jp-chotatsu-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    ndjson_path = out_dir / "jp-chotatsu.ndjson"
    rows_emitted = 0

    if opts.local_source is not None:
        path = Path(opts.local_source)
        raw_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if opts.write_ndjson:
            with ndjson_path.open("w", encoding="utf-8") as f:
                cap = opts.max_records
                for raw in _iter_local(path):
                    norm = _normalize_record(raw)
                    if norm is None:
                        continue
                    f.write(json.dumps(norm, ensure_ascii=False, separators=(",", ":")))
                    f.write("\n")
                    rows_emitted += 1
                    if cap is not None and rows_emitted >= cap:
                        break
        url_attr = str(path)
        source_type = "local"
    else:
        if not (opts.from_date and opts.until_date):
            raise ValueError(
                "JpChotatsuFetchOpts.from_date + until_date must both be set in network "
                "mode (passive-only: no implicit full-archive scan per ADR-2605262400 §7)."
            )
        owned_client = opts.client is None
        client = opts.client or httpx.Client(
            timeout=opts.timeout_sec,
            follow_redirects=True,
            headers={"User-Agent": opts.user_agent},
        )
        hasher = hashlib.sha256()
        with ndjson_path.open("w", encoding="utf-8") as f:
            for raw in _network_iter(opts, owned_client, client):
                norm = _normalize_record(raw)
                if norm is None:
                    continue
                line = json.dumps(norm, ensure_ascii=False, separators=(",", ":"))
                f.write(line)
                f.write("\n")
                hasher.update(line.encode("utf-8"))
                hasher.update(b"\n")
                rows_emitted += 1
        raw_sha = hasher.hexdigest()
        url_attr = opts.bulk_url
        source_type = "http"

    revision = f"sha256:{raw_sha}"
    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="jp-chotatsu",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": source_type,
            "url": url_attr,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "awardCount": rows_emitted,
            "fromDate": opts.from_date,
            "untilDate": opts.until_date,
            "license": _LICENSE,
            "tier": _TIER,
            "sourceSensor": _SOURCE_SENSOR,
        },
    )


__all__ = [
    "DEFAULT_API_BASE",
    "DEFAULT_BULK_URL",
    "JpChotatsuFetchOpts",
    "fetch",
]
