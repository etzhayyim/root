"""Shared scaffolding for the ``law/`` bucket fetchers (ADR-2605262800 W1).

The 5 W1 anchor fetchers all emit the SAME normalized statute record shape and
share an identical dual-mode (network / local-source) write path, so that
boilerplate lives here once rather than being copy-pasted per source (the
opposite of the older self-contained fetchers like ``uk_hansard``; legal sources
are uniform enough to justify a shared core).

Normalized statute record (one NDJSON line, consumed by
``kotodama.organism.sensors.legal.legal_statute_sensor.LegalStatuteSensor``):

    {"recordId":       "JP:412AC0000000086",   # "<jurisdiction>:<native law id>"
     "jurisdiction":   "JP",                    # ISO-3166 alpha-2 (or "EU")
     "lawId":          "412AC0000000086",       # native statute identifier
     "title":          "個人情報の保護に関する法律",
     "lawType":        "act",                   # act|cabinet-order|regulation|directive|treaty|...
     "promulgatedDate":"2003-05-30",            # YYYY-MM-DD or null
     "effectiveDate":  null,
     "revision":       "2024-04-01",            # version / amendment / release-point id
     "lang":           "ja",
     "license":        "CC-BY-4.0",
     "sourceUrl":      "https://laws.e-gov.go.jp/law/412AC0000000086",
     "payloadCid":     "https://laws.e-gov.go.jp/law/412AC0000000086",  # canonical URL until ipfs-pinned
     "bodyExcerpt":    null}                     # optional first ~4 KiB of text

``None`` fields are kept (NDJSON, not Datom) so the sensor sees an explicit
absence. ``recordId`` + ``jurisdiction`` + ``lawId`` are the only required keys.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Optional

from .. import FetchResult

# A normalize fn maps one raw upstream record (dict) → a normalized statute dict,
# or None to drop it.
Normalizer = Callable[[dict], Optional[dict]]

_DATE_ONLY = re.compile(r"^(\d{4})-?(\d{2})-?(\d{2})")


def coerce_iso_date(raw: Any) -> Optional[str]:
    """Best-effort coerce an upstream date to ``YYYY-MM-DD`` (or None)."""
    if not raw:
        return None
    s = str(raw).strip()
    m = _DATE_ONLY.match(s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # Japanese-style 令和N年M月D日 etc. are passed through to the operator as-is
    # only when ISO extraction fails; we return None rather than guess an era.
    return None


def already_normalized(row: dict) -> bool:
    """True if a staged row is already in normalized shape (re-stage / NDJSON)."""
    return isinstance(row, dict) and "recordId" in row and "jurisdiction" in row


def iter_local_source(path: Path, normalize: Normalizer) -> Iterator[dict]:
    """Yield normalized rows from an operator-staged JSON or NDJSON file.

    A JSON file may be a list, or a dict whose first list-valued member holds the
    records. NDJSON is one raw record per line. Rows already in normalized shape
    pass straight through; everything else goes through ``normalize``.
    """
    raw_text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        for line in raw_text.splitlines():
            s = line.strip()
            if not s:
                continue
            try:
                row = json.loads(s)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            yield row if already_normalized(row) else normalize(row)  # type: ignore[misc]
        return
    yield from _iter_payload(payload, normalize)


def _iter_payload(payload: Any, normalize: Normalizer) -> Iterator[dict]:
    records: Iterable[Any]
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        if already_normalized(payload):
            yield payload
            return
        records = next(
            (v for v in payload.values() if isinstance(v, list)),
            [],
        )
    else:
        return
    for rec in records:
        if not isinstance(rec, dict):
            continue
        out = rec if already_normalized(rec) else normalize(rec)
        if out is not None:
            yield out


def write_run(
    *,
    staging_dir: Path,
    name: str,
    rows: Iterator[Optional[dict]],
    source_meta: dict,
    license_id: str,
    tier: str,
    max_records: Optional[int],
    local_source: Optional[Path],
) -> FetchResult:
    """Drain ``rows`` into ``<staging>/<name>-<ts>/<name>.ndjson`` + build a FetchResult.

    Hashes the emitted NDJSON line-by-line so ``revision`` is content-stable
    regardless of network vs local-source provenance.
    """
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_dir = staging_dir / f"{name}-{capture_ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    ndjson_path = out_dir / f"{name}.ndjson"

    hasher = hashlib.sha256()
    emitted = 0
    with ndjson_path.open("w", encoding="utf-8") as f:
        for row in rows:
            if row is None:
                continue
            line = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
            f.write(line)
            f.write("\n")
            hasher.update(line.encode("utf-8"))
            hasher.update(b"\n")
            emitted += 1
            if max_records is not None and emitted >= max_records:
                break

    raw_sha = hasher.hexdigest()
    size_bytes = sum(p.stat().st_size for p in out_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())
    return FetchResult(
        name=name,
        revision=f"sha256:{raw_sha}",
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "local" if local_source is not None else "http",
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "recordCount": emitted,
            "license": license_id,
            "tier": tier,
            **source_meta,
        },
    )


__all__ = [
    "Normalizer",
    "coerce_iso_date",
    "already_normalized",
    "iter_local_source",
    "write_run",
]
