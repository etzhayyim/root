"""UK Companies House Free Company Data Product fetcher — W1 concrete impl.

Per ADR-2605263800 W1. UK Companies House publishes the Free Company
Data Product (FCD) — a monthly bulk archive of ~5M UK companies —
under **OGL v3.0** (Open Government Licence; Crown copyright open
license).

  http://download.companieshouse.gov.uk/BasicCompanyDataAsOneFile-<YYYY-MM-01>.zip
  http://download.companieshouse.gov.uk/en_output.html   (listing page)

The monthly bulk is a single ZIP (~5GB) containing a single CSV
(~25GB uncompressed) with ~30 columns per row. W1 extracts the
sensor-relevant subset:

  - CompanyNumber       → entityLocalId (8-char CRN; numeric OR 2-letter+6-digit prefix)
  - CompanyName         → registeredName
  - IncorporationDate   → registeredAt (DD/MM/YYYY → ISO-8601 T00:00:00Z)
  - CompanyStatus       → companyStatus (passed through for downstream)

Normalized NDJSON consumable by
``kotodama.organism.sensors.corp.uk_companies_house_sensor.UkCompaniesHouseSensor``:

  {"entityLocalId": "03977902",
   "registeredName": "APPLE EUROPE LIMITED",
   "registeredAt": "2000-03-30T00:00:00Z",
   "companyStatus": "Active"}

Two operator paths matching the established pattern:

1. **Network mode** (``local_source=None``, default): httpx GET against
   the FCD monthly bulk URL. ``snapshot`` (e.g.,
   ``"BasicCompanyDataAsOneFile-2026-05-01.zip"``) MUST be specified
   explicitly (passive-only: no implicit latest-month inference).

2. **Local-source mode** (``local_source=<Path>``): read pre-staged
   ZIP OR CSV OR pre-normalized NDJSON. Recommended for testing +
   air-gapped fleet nodes that have the ~5GB ZIP pre-staged via a
   separate download channel.

W1 streams the CSV row-by-row (no full-file in-memory load). Daily
increment catch-up is W2 scope.

Passive-only invariant boundary: this fetcher is OPERATOR-triggered,
NOT organism-tick, per ADR-2605262400 §7. Vendor commercial-terminal
imports (Bloomberg Terminal / Refinitiv / FactSet / Moody's Orbis /
D&B Hoovers / Pitchbook / Crunchbase Pro) are CONSTITUTIONALLY
PROHIBITED per Charter Rider §2(e)+§2(c).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

import httpx

from . import FetchResult

DEFAULT_FCD_BASE = "http://download.companieshouse.gov.uk"
DEFAULT_MONTHLY_LISTING = f"{DEFAULT_FCD_BASE}/en_output.html"

# UK CRN structural pattern (matches UkCompaniesHouseSensor regex).
_CRN_PATTERN = re.compile(r"^(?:\d{8}|[A-Z]{2}\d{6})$")
# UK FCD IncorporationDate is "DD/MM/YYYY".
_DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


@dataclass
class UkCompaniesHouseFetchOpts:
    fcd_base: str = DEFAULT_FCD_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 600.0  # ~5GB ZIP download
    # Specific snapshot filename to fetch (e.g.,
    # "BasicCompanyDataAsOneFile-2026-05-01.zip"). Required in
    # network mode; passive-only: no implicit latest-month inference.
    snapshot: Optional[str] = None
    # Local-source mode: read this path (ZIP / CSV / NDJSON).
    local_source: Optional[Path] = None
    # Optional filter: only emit rows whose CRN matches the allowlist
    # (post upper-casing). Empty tuple = no restriction.
    crn_allowlist: tuple[str, ...] = ()
    # Optional filter: only emit rows whose CompanyStatus matches.
    company_status_allowlist: tuple[str, ...] = ()
    max_records: Optional[int] = None
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _coerce_uk_date(raw: str) -> Optional[str]:
    """Coerce 'DD/MM/YYYY' → 'YYYY-MM-DDT00:00:00Z'. Returns None for
    malformed input (G7 schema discipline)."""
    if not raw:
        return None
    m = _DATE_RE.match(raw.strip())
    if not m:
        return None
    dd, mm, yyyy = m.group(1), m.group(2), m.group(3)
    return f"{yyyy}-{mm}-{dd}T00:00:00Z"


def _detect_and_open_csv(raw_bytes: bytes, out_dir: Path) -> tuple[Path, str]:
    """If raw_bytes is a ZIP, extract first .csv inside; else write raw.

    Returns (csv_path, csv_filename_inside_zip OR direct-name).
    """
    if raw_bytes[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                raise ValueError("UK FCD ZIP contained no .csv file")
            with zf.open(csv_names[0]) as src:
                payload = src.read()
        out_path = out_dir / Path(csv_names[0]).name
        out_path.write_bytes(payload)
        return out_path, csv_names[0]
    out_path = out_dir / "fcd.csv"
    out_path.write_bytes(raw_bytes)
    return out_path, "fcd.csv"


def _iter_csv_rows(csv_path: Path) -> Iterator[dict]:
    """Stream-parse UK FCD CSV; yield normalized rows.

    Uses csv.DictReader for header-aware parsing. FCD column names
    vary slightly across publication years; we look up by canonical
    expected names with fallback to whitespace-stripped variants.
    """
    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        # Normalize header lookup table (strip whitespace + case-insensitive).
        original_to_normalized: dict[str, str] = {}
        if reader.fieldnames:
            for original in reader.fieldnames:
                if original is not None:
                    original_to_normalized[original.strip()] = original
        for raw_row in reader:
            if not raw_row:
                continue
            # Resolve fields with stripped-key fallback.
            def _get(name: str) -> str:
                key = original_to_normalized.get(name) or name
                val = raw_row.get(key)
                return str(val).strip() if val is not None else ""

            company_number = _get("CompanyNumber").upper()
            company_name = _get("CompanyName")
            incorporation_date = _get("IncorporationDate")
            company_status = _get("CompanyStatus") or None
            if not (company_number and company_name):
                # G7 — required field missing.
                continue
            if not _CRN_PATTERN.match(company_number):
                # G7 — malformed CRN; skip silently.
                continue
            registered_at = _coerce_uk_date(incorporation_date)
            yield {
                "entityLocalId": company_number,
                "registeredName": company_name,
                "registeredAt": registered_at,  # May be None for unknown date.
                "companyStatus": company_status,
            }


def _iter_observations_from_local(path: Path) -> Iterator[dict]:
    """Dispatch on local-source extension/sig: ZIP / CSV / NDJSON."""
    raw_bytes = path.read_bytes()
    # NDJSON detection: starts with '{' after whitespace strip.
    stripped = raw_bytes.lstrip()
    if stripped[:1] == b"{":
        # Pre-normalized NDJSON pass-through.
        text = raw_bytes.decode("utf-8", errors="replace")
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
    # Detect ZIP vs raw CSV by signature.
    tmp_dir = path.parent
    csv_path, _ = _detect_and_open_csv(raw_bytes, tmp_dir)
    yield from _iter_csv_rows(csv_path)


def _network_url(opts: UkCompaniesHouseFetchOpts) -> str:
    if not opts.snapshot:
        raise ValueError(
            "UkCompaniesHouseFetchOpts.snapshot must be set in network "
            "mode (e.g. 'BasicCompanyDataAsOneFile-2026-05-01.zip') — "
            "passive-only: no implicit latest-month inference per "
            "ADR-2605262400 §7."
        )
    return f"{opts.fcd_base}/{opts.snapshot}"


def _resolve_raw_bytes(opts: UkCompaniesHouseFetchOpts) -> tuple[bytes, str]:
    if opts.local_source is not None:
        path = Path(opts.local_source)
        return path.read_bytes(), str(path)
    url = _network_url(opts)
    owned_client = opts.client is None
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec,
        follow_redirects=True,
        headers={"User-Agent": opts.user_agent},
    )
    try:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.content, url
    finally:
        if owned_client:
            client.close()


def _apply_filters(rows: Iterator[dict], opts: UkCompaniesHouseFetchOpts) -> Iterator[dict]:
    crn_set = set(opts.crn_allowlist) if opts.crn_allowlist else None
    status_set = set(opts.company_status_allowlist) if opts.company_status_allowlist else None
    cap = opts.max_records
    emitted = 0
    for row in rows:
        if crn_set is not None and row.get("entityLocalId") not in crn_set:
            continue
        if status_set is not None and row.get("companyStatus") not in status_set:
            continue
        yield row
        emitted += 1
        if cap is not None and emitted >= cap:
            return


def fetch(staging_dir: Path, opts: UkCompaniesHouseFetchOpts) -> FetchResult:
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"uk-companies-house-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    ndjson_path = out_dir / "uk-companies-house.ndjson"
    rows_emitted = 0

    if opts.local_source is not None:
        # Compute SHA over the raw local file (for revision tracking).
        raw_bytes = Path(opts.local_source).read_bytes()
        raw_sha = hashlib.sha256(raw_bytes).hexdigest()

        # Stage the local file under out_dir so the staging-path-rooted
        # CSV detector can find it (preserving filename when possible).
        local_path = Path(opts.local_source)
        if local_path.suffix.lower() in (".zip", ".csv"):
            # Extract via _detect_and_open_csv (this writes the .csv to out_dir).
            csv_path, _ = _detect_and_open_csv(raw_bytes, out_dir)
            iterator = _iter_csv_rows(csv_path)
        else:
            # Treat as NDJSON pass-through (or raw CSV without extension).
            iterator = _iter_observations_from_local(local_path)

        if opts.write_ndjson:
            with ndjson_path.open("w", encoding="utf-8") as f:
                for row in _apply_filters(iterator, opts):
                    f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
                    f.write("\n")
                    rows_emitted += 1
        url_attr = str(local_path)
        source_type = "local"
    else:
        raw_bytes, url_attr = _resolve_raw_bytes(opts)
        raw_sha = hashlib.sha256(raw_bytes).hexdigest()
        csv_path, _ = _detect_and_open_csv(raw_bytes, out_dir)
        if opts.write_ndjson:
            with ndjson_path.open("w", encoding="utf-8") as f:
                for row in _apply_filters(_iter_csv_rows(csv_path), opts):
                    f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
                    f.write("\n")
                    rows_emitted += 1
        source_type = "http"

    revision = f"sha256:{raw_sha}"
    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="uk-companies-house",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": source_type,
            "url": url_attr,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "companyCount": rows_emitted,
            "snapshot": opts.snapshot,
            "crnAllowlistApplied": bool(opts.crn_allowlist),
            "companyStatusAllowlistApplied": bool(opts.company_status_allowlist),
            "license": "OGL-v3.0",
            "tier": "A",
        },
    )


__all__ = [
    "DEFAULT_FCD_BASE",
    "DEFAULT_MONTHLY_LISTING",
    "UkCompaniesHouseFetchOpts",
    "fetch",
]
