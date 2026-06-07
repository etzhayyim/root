"""GLEIF LEI Concatenated Files (Level-1) fetcher — W1 concrete impl.

Per ADR-2605263800 W1. GLEIF publishes daily Concatenated Data Files
covering ~2.5M LEIs under **CC0 1.0** (public-domain dedication).

  https://www.gleif.org/en/lei-data/gleif-concatenated-file
  https://leidata.gleif.org/api/v1/concatenated-files/lei2/latest

Two operator paths supported:

1. **Network mode** (``local_source=None``, default): httpx GET
   against the published concatenated-file URL, write raw bytes to
   staging, then parse → NDJSON emit.

2. **Local-source mode** (``local_source=<Path>``): skip the HTTPS
   download, read the operator-staged file directly (operator may
   have curl'd it earlier OR be running pytest with a fixture).
   This is the canonical test path AND the recommended operator path
   for air-gapped fleet nodes that can't reach goldencopy.gleif.org
   directly (e.g., behind a content-filtering proxy).

Both modes detect ZIP container automatically (GLEIF Golden Copy is
distributed as ``.zip``; the first JSON file inside is the
concatenated LEI L1 payload).

Output NDJSON row shape (consumed by
``kotodama.organism.sensors.corp.lei_sensor.GleifLeiSensor``):

    {"lei": "20-char", "legalName": "...", "jurisdictionIso3": "USA",
     "registrationStatus": "ISSUED",
     "parentLei": "...|null", "ultimateParentLei": "...|null"}

GLEIF L1 publishes ``Entity.LegalJurisdiction`` in ISO 3166-1 alpha-2
(2-char). The fetcher passes through whatever upstream emits; the
sensor's structural check (``maxLength: 3``) accommodates both
alpha-2 and alpha-3 codes.

L2 relationship records (parent / ultimate-parent fields) are
omitted when the input file is L1-only (default GLEIF concatenated
file). When the operator supplies a joined L1+L2 NDJSON (via a
separate join script outside this fetcher's scope), the fetcher
just preserves whatever fields are present.

Passive-only invariant boundary: this fetcher is OPERATOR-triggered
(via ``e7m-dataset pull gleif-lei`` CLI OR direct Python invocation),
NOT organism-tick. The sensor (``GleifLeiSensor``) that consumes
this fetcher's output is the passive-only side per ADR-2605262400 §7.
Vendor commercial-terminal imports (Bloomberg Terminal / Refinitiv /
FactSet / Moody's Orbis / D&B Hoovers / Pitchbook / Crunchbase Pro)
are CONSTITUTIONALLY PROHIBITED per Charter Rider §2(e)+§2(c).
"""

from __future__ import annotations

import hashlib
import io
import json
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal, Optional

import httpx

from . import FetchResult

DEFAULT_L1_API = "https://leidata.gleif.org/api/v1/concatenated-files/lei2/latest"
DEFAULT_L2_RR_API = "https://leidata.gleif.org/api/v1/concatenated-files/rr/latest"
DEFAULT_L2_REPEX_API = "https://leidata.gleif.org/api/v1/concatenated-files/repex/latest"


@dataclass
class GleifLeiFetchOpts:
    l1_url: str = DEFAULT_L1_API
    l2_rr_url: str = DEFAULT_L2_RR_API
    l2_repex_url: str = DEFAULT_L2_REPEX_API
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 900.0  # L1 file is large (~1 GB zipped XML)
    fmt: Literal["json"] = "json"  # CSV/XML stream deferred to W2 (stdlib JSON only at W1)
    # Local-source mode: skip HTTPS download, read this path directly.
    # Useful for pytest fixtures + air-gapped operator paths.
    local_source: Optional[Path] = None
    # Whether to also fetch L2 relationship records (RR + RepEx).
    # Default False at W1 because L2 join is a separate concern;
    # W2+ adds the join logic.
    fetch_l2: bool = False
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _detect_zip_and_extract_json(raw_bytes: bytes, out_dir: Path) -> Path:
    """Extract the first .json file from a ZIP archive (if input is ZIP),
    or write raw bytes as-is if already a .json document.

    Returns the path to the extracted/written .json file.
    """
    if raw_bytes[:2] == b"PK":
        # ZIP signature; extract first .json entry inside.
        with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
            json_names = [n for n in zf.namelist() if n.lower().endswith(".json")]
            if not json_names:
                raise ValueError("GLEIF ZIP contained no .json file")
            with zf.open(json_names[0]) as src:
                payload = src.read()
        # Normalize to a flat filename within out_dir (strip any inner
        # directory components to avoid traversal surprises).
        out_path = out_dir / Path(json_names[0]).name
        out_path.write_bytes(payload)
        return out_path
    # Assume already-JSON; write as-is.
    out_path = out_dir / "lei2-latest.json"
    out_path.write_bytes(raw_bytes)
    return out_path


def _iter_lei_records(payload_path: Path) -> Iterator[dict]:
    """Yield one normalized LEI row per record in the GLEIF L1 JSON.

    GLEIF L1 JSON top-level shape varies by Golden Copy revision; the
    most common shapes are:

      - ``[{ "LEI": ..., "Entity": {...}, "Registration": {...}}, ...]``
        (flat list at top level)
      - ``{"LEIData": {"LEIRecords": [...]}}`` (nested under LEIData)
      - ``{"records": [...]}`` (generic-key wrapper used by some
        operator-staged normalizations)

    This iterator handles all three shapes. Yields normalized rows
    in the GleifLeiSensor input shape.

    NOTE: W1 impl uses ``json.loads()`` (in-memory). For real ~2GB
    Golden Copy files, W2 will switch to ``ijson`` streaming. For
    test fixtures + operator-sampled subsets up to ~100MB, in-memory
    parse is adequate.
    """
    raw = json.loads(payload_path.read_text(encoding="utf-8"))

    # Resolve to a list of records.
    if isinstance(raw, list):
        records = raw
    elif isinstance(raw, dict):
        if "LEIData" in raw and isinstance(raw["LEIData"], dict):
            records = raw["LEIData"].get("LEIRecords") or []
        elif "records" in raw and isinstance(raw["records"], list):
            records = raw["records"]
        else:
            # Single-record envelope.
            records = [raw]
    else:
        return

    for rec in records:
        if not isinstance(rec, dict):
            continue
        lei = rec.get("lei") or rec.get("LEI")
        if isinstance(lei, dict):
            lei = lei.get("$") or lei.get("value")
        if not isinstance(lei, str) or len(lei) != 20:
            continue

        # Entity sub-record (GLEIF v3 schema).
        entity = rec.get("Entity") or rec.get("entity") or {}
        if not isinstance(entity, dict):
            entity = {}
        legal_name = (
            entity.get("LegalName")
            or entity.get("legalName")
            or rec.get("legalName")
            or ""
        )
        if isinstance(legal_name, dict):
            legal_name = legal_name.get("$") or legal_name.get("value") or ""
        jurisdiction = (
            entity.get("LegalJurisdiction")
            or entity.get("jurisdictionIso3")
            or rec.get("jurisdictionIso3")
            or ""
        )

        # Registration sub-record.
        reg = rec.get("Registration") or rec.get("registration") or {}
        if not isinstance(reg, dict):
            reg = {}
        reg_status = (
            reg.get("RegistrationStatus")
            or reg.get("registrationStatus")
            or rec.get("registrationStatus")
            or ""
        )

        yield {
            "lei": lei,
            "legalName": str(legal_name)[:512],
            "jurisdictionIso3": str(jurisdiction)[:3],
            "registrationStatus": str(reg_status),
            "parentLei": rec.get("parentLei"),
            "ultimateParentLei": rec.get("ultimateParentLei"),
        }


def _resolve_raw_bytes(opts: GleifLeiFetchOpts) -> bytes:
    """Get the raw L1 file bytes — local-source preferred, else httpx GET."""
    if opts.local_source is not None:
        return Path(opts.local_source).read_bytes()
    owned_client = opts.client is None
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec,
        follow_redirects=True,
        headers={"User-Agent": opts.user_agent},
    )
    try:
        resp = client.get(opts.l1_url)
        resp.raise_for_status()
        return resp.content
    finally:
        if owned_client:
            client.close()


def fetch(staging_dir: Path, opts: GleifLeiFetchOpts) -> FetchResult:
    """Stage GLEIF LEI L1 Concatenated File into the staging directory.

    Always writes the raw payload (extracted .json from any ZIP wrap)
    + an ``lei-l1.ndjson`` sensor-consumable sidecar when
    ``write_ndjson=True``.
    """
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"gleif-lei-l1-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_bytes = _resolve_raw_bytes(opts)
    payload_path = _detect_zip_and_extract_json(raw_bytes, out_dir)

    rows_decoded = 0
    ndjson_path = out_dir / "lei-l1.ndjson"
    if opts.write_ndjson:
        with ndjson_path.open("w", encoding="utf-8") as f:
            for row in _iter_lei_records(payload_path):
                f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
                f.write("\n")
                rows_decoded += 1

    raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    revision = f"sha256:{raw_sha}"

    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name="gleif-lei-l1",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "local" if opts.local_source else "http",
            "url": str(opts.local_source) if opts.local_source else opts.l1_url,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "leiCount": rows_decoded,
            "license": "CC0-1.0",
            "tier": "A",
            "format": opts.fmt,
        },
    )


__all__ = [
    "DEFAULT_L1_API",
    "DEFAULT_L2_REPEX_API",
    "DEFAULT_L2_RR_API",
    "GleifLeiFetchOpts",
    "fetch",
]
