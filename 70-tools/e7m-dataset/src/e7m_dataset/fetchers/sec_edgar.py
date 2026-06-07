"""SEC EDGAR full-index master.idx fetcher — W1 concrete impl.

Per ADR-2605263800 W1. SEC EDGAR is the US Securities and Exchange
Commission's public filings repository (~10K active filers) under
**public domain** (US federal government works are not copyrighted
per 17 USC 105; SEC data is published per 17 CFR 200).

Bulk archives published at:

  https://www.sec.gov/Archives/edgar/full-index/<YYYY>/<QTR>/master.idx
  https://data.sec.gov/submissions/CIK<10-digit>.json
  https://data.sec.gov/api/xbrl/companyfacts/CIK<10-digit>.json

This W1 fetcher targets the **quarterly master.idx** bulk archive
which is the operationally-cheapest passive-only path:

- Single ~5-50MB pipe-delimited text file per quarter
- Stable since 2001; covers every filing in that quarter
- No per-CIK enumeration → respects ADR-2605262400 §7

W2 will add the per-CIK Submissions JSON path (for richer metadata
fields) + the per-CIK companyfacts JSON path (for XBRL structured
financial facts).

master.idx format (after ~11 header lines):

  CIK|Company Name|Form Type|Date Filed|Filename
  320193|Apple Inc.|10-K|2024-11-01|edgar/data/320193/0000320193-24-000123-index.htm
  789019|Microsoft Corp|10-Q|2025-01-29|edgar/data/789019/0000789019-25-000004-index.htm
  ...

Normalized into NDJSON rows consumable by
``kotodama.organism.sensors.corp.sec_edgar_sensor.SecEdgarSensor``:

  {"entityLocalId": "0000320193",        # zero-padded to 10 digits
   "formTypeNative": "10-K",
   "filedAtUtc": "2024-11-01T00:00:00Z", # ISO-8601 (date-only coerce; time fixed at 00:00:00Z)
   "payloadCid": "edgar/data/320193/0000320193-24-000123-index.htm",  # EDGAR archive path; W2 → IPFS CID after publish-ipfs)
   "companyName": "Apple Inc."}

Two operator paths (matching gleif_lei.py / worldbank_open_data.py /
eu_eurostat.py pattern):

1. **Network mode** (``local_source=None``, default): httpx GET
   against the quarterly master.idx URL. ``year`` + ``quarter`` MUST
   be specified explicitly (passive-only: no implicit latest-quarter
   inference).

2. **Local-source mode** (``local_source=<Path>``): read pre-staged
   master.idx file OR pre-normalized NDJSON pass-through.

SEC's published rate-limit guidance (max 10 req/s + User-Agent
identification) is respected via the default User-Agent string +
single-file fetch per call.

Passive-only invariant boundary: this fetcher is OPERATOR-triggered,
NOT organism-tick, per ADR-2605262400 §7. Vendor commercial-terminal
imports (Bloomberg Terminal / Refinitiv / FactSet / Moody's Orbis /
D&B Hoovers / Pitchbook / Crunchbase Pro) are CONSTITUTIONALLY
PROHIBITED per Charter Rider §2(e)+§2(c).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal, Optional

import httpx

from . import FetchResult

DEFAULT_USER_AGENT = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
DEFAULT_FULL_INDEX_BASE = "https://www.sec.gov/Archives/edgar/full-index"
DEFAULT_SUBMISSIONS_BASE = "https://data.sec.gov/submissions"

# Date Filed column format in master.idx (YYYY-MM-DD).
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class SecEdgarFetchOpts:
    full_index_base: str = DEFAULT_FULL_INDEX_BASE
    submissions_base: str = DEFAULT_SUBMISSIONS_BASE
    user_agent: str = DEFAULT_USER_AGENT
    timeout_sec: float = 120.0
    fmt: Literal["master.idx"] = "master.idx"  # W2 adds Submissions JSON path
    year: Optional[int] = None
    quarter: Optional[Literal[1, 2, 3, 4]] = None
    # Local-source mode: skip HTTPS, read this path (master.idx OR
    # pre-normalized NDJSON).
    local_source: Optional[Path] = None
    # Optional filter: only emit rows whose CIK matches the allowlist
    # (post zero-padding). Empty tuple = no restriction.
    cik_allowlist: tuple[str, ...] = ()
    # Optional filter: only emit rows whose form type matches.
    form_type_allowlist: tuple[str, ...] = ()
    max_records: Optional[int] = None
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _quarter_url(opts: SecEdgarFetchOpts) -> str:
    if opts.year is None or opts.quarter is None:
        raise ValueError(
            "SecEdgarFetchOpts.year + quarter must both be set in network mode "
            "(passive-only: no implicit latest-quarter inference per "
            "ADR-2605262400 §7)."
        )
    return f"{opts.full_index_base}/{opts.year}/QTR{opts.quarter}/master.idx"


def _pad_cik(raw: str) -> Optional[str]:
    """Zero-pad a CIK to 10 digits (SEC canonical form).

    Returns None for non-numeric input.
    """
    s = raw.strip()
    if not s.isdigit():
        return None
    return s.zfill(10)


def _iter_master_idx_rows(text: str) -> Iterator[dict]:
    """Parse a master.idx text body and yield normalized NDJSON rows.

    Handles the ~11-line header block (skip until the dashed-line
    separator) and the pipe-delimited body. Malformed rows are
    skipped silently per G7 schema discipline.
    """
    body_started = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r")
        if not body_started:
            # Header block: continue until we see the dashed separator
            # line ("---|---|---|---|---") OR a clear pipe-row that looks
            # like body data (CIK numeric first column).
            if line.startswith("---"):
                body_started = True
                continue
            # Some legacy index headers don't include the dashed line;
            # treat the first row with a numeric leading CIK as data.
            parts = line.split("|")
            if len(parts) == 5 and parts[0].strip().isdigit():
                body_started = True
                # Fall through to process this line as data.
            else:
                continue
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 5:
            continue
        cik = _pad_cik(parts[0])
        if cik is None:
            continue
        company_name = parts[1].strip()
        form_type = parts[2].strip()
        date_filed = parts[3].strip()
        filename = parts[4].strip()
        if not (company_name and form_type and date_filed and filename):
            continue
        if not _DATE_RE.match(date_filed):
            continue
        yield {
            "entityLocalId": cik,
            "formTypeNative": form_type,
            "filedAtUtc": f"{date_filed}T00:00:00Z",
            "payloadCid": filename,
            "companyName": company_name,
        }


def _iter_observations_from_payload(text: str) -> Iterator[dict]:
    """Dispatch on local-source payload format: master.idx vs NDJSON."""
    # Heuristic: master.idx starts with "Description:" or "Last Data
    # Received:" header lines OR has a leading numeric CIK followed by
    # "|". NDJSON starts with "{".
    stripped = text.lstrip()
    if stripped.startswith("{"):
        # Pre-normalized NDJSON pass-through.
        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue
            try:
                row = json.loads(s)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and "entityLocalId" in row:
                yield row
        return
    # Otherwise treat as master.idx.
    yield from _iter_master_idx_rows(text)


def _apply_filters(rows: Iterator[dict], opts: SecEdgarFetchOpts) -> Iterator[dict]:
    cik_set = set(opts.cik_allowlist) if opts.cik_allowlist else None
    form_set = set(opts.form_type_allowlist) if opts.form_type_allowlist else None
    cap = opts.max_records
    emitted = 0
    for row in rows:
        if cik_set is not None and row.get("entityLocalId") not in cik_set:
            continue
        if form_set is not None and row.get("formTypeNative") not in form_set:
            continue
        yield row
        emitted += 1
        if cap is not None and emitted >= cap:
            return


def _resolve_raw_text(opts: SecEdgarFetchOpts) -> tuple[str, str]:
    """Get raw text + source-URL string."""
    if opts.local_source is not None:
        path = Path(opts.local_source)
        return path.read_text(encoding="utf-8", errors="replace"), str(path)
    url = _quarter_url(opts)
    owned_client = opts.client is None
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec,
        follow_redirects=True,
        headers={"User-Agent": opts.user_agent},
    )
    try:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text, url
    finally:
        if owned_client:
            client.close()


def fetch(staging_dir: Path, opts: SecEdgarFetchOpts) -> FetchResult:
    """Stage SEC EDGAR quarterly master.idx into the staging directory.

    Always writes ``sec-edgar.ndjson`` (sensor-consumable).
    Also persists the raw master.idx (if fetched from network) at
    ``raw-master.idx`` for forensic auditability.
    """
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"sec-edgar-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_text, url_attr = _resolve_raw_text(opts)
    source_type = "local" if opts.local_source else "http"

    # Persist the raw bytes for forensic auditability (regardless of mode).
    raw_path = out_dir / "raw-master.idx"
    raw_path.write_text(raw_text, encoding="utf-8")
    raw_sha = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    revision = f"sha256:{raw_sha}"

    ndjson_path = out_dir / "sec-edgar.ndjson"
    rows_emitted = 0
    if opts.write_ndjson:
        with ndjson_path.open("w", encoding="utf-8") as f:
            for row in _apply_filters(_iter_observations_from_payload(raw_text), opts):
                f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
                f.write("\n")
                rows_emitted += 1

    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="sec-edgar",
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
            "year": opts.year,
            "quarter": opts.quarter,
            "license": "public-domain",
            "tier": "A",
            "format": opts.fmt,
            "cikAllowlistApplied": bool(opts.cik_allowlist),
            "formTypeAllowlistApplied": bool(opts.form_type_allowlist),
        },
    )


__all__ = [
    "DEFAULT_FULL_INDEX_BASE",
    "DEFAULT_SUBMISSIONS_BASE",
    "DEFAULT_USER_AGENT",
    "SecEdgarFetchOpts",
    "fetch",
]
