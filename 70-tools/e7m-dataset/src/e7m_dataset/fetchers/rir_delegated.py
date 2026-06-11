"""RIR delegated-stats fetcher (APNIC / ARIN / RIPE / AFRINIC / LACNIC).

Per ADR-2605262400 W1. Each of the five Regional Internet Registries
publishes a daily-cadence ``delegated-<rir>-extended-latest`` file with
the full IPv4 / IPv6 / ASN allocation roster for its region. Format:

  https://www.apnic.net/about-apnic/corporate-documents/documents/resource-guidelines/rir-statistics-exchange-format/

Each row is pipe-delimited:

  <registry>|<cc>|<type>|<start>|<value>|<date>|<status>[|<opaque-id>...]

We stage the raw upstream file AS-IS and emit a NDJSON sidecar with
one decoded row per line.

License: public-domain de facto (no copyright assertion in the files).
Tagged Tier A in ADR-2605262400.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import httpx

from . import FetchResult


KNOWN_RIRS = ("apnic", "arin", "ripe", "afrinic", "lacnic")

_URL_BY_RIR = {
    "apnic":   "https://ftp.apnic.net/stats/apnic/delegated-apnic-extended-latest",
    "arin":    "https://ftp.arin.net/pub/stats/arin/delegated-arin-extended-latest",
    "ripe":    "https://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-extended-latest",
    "afrinic": "https://ftp.afrinic.net/pub/stats/afrinic/delegated-afrinic-extended-latest",
    "lacnic":  "https://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-extended-latest",
}


@dataclass
class RirDelegatedFetchOpts:
    rir: str = "apnic"
    base_url: Optional[str] = None
    timeout_sec: float = 600.0
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def _url_for(rir: str, base_url: Optional[str]) -> str:
    if base_url is not None:
        return base_url
    if rir not in _URL_BY_RIR:
        raise ValueError(f"unknown RIR '{rir}'. Known: {KNOWN_RIRS}")
    return _URL_BY_RIR[rir]


def _parse_row(line: str) -> dict | None:
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    parts = s.split("|")
    if len(parts) < 7:
        return None
    registry, cc, rtype, start, value, date, status = parts[:7]
    if rtype not in {"ipv4", "ipv6", "asn"}:
        return None
    opaque_id = parts[7] if len(parts) >= 8 else ""
    extensions = parts[8:] if len(parts) >= 9 else []
    out: dict = {
        "registry": registry,
        "cc": cc,
        "type": rtype,
        "start": start,
        "value": int(value) if value.isdigit() else value,
        "date": date,
        "status": status,
    }
    if opaque_id:
        out["opaqueId"] = opaque_id
    if extensions:
        out["extensions"] = extensions
    return out


def fetch(staging_dir: Path, opts: RirDelegatedFetchOpts) -> FetchResult:
    if opts.rir not in KNOWN_RIRS:
        raise ValueError(f"unknown RIR '{opts.rir}'. Known: {KNOWN_RIRS}")

    url = _url_for(opts.rir, opts.base_url)
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"rir-delegated-{opts.rir}-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_path = out_dir / f"delegated-{opts.rir}-extended-latest.txt"
    ndjson_path = out_dir / f"delegated-{opts.rir}-extended-latest.ndjson"

    owned_client = opts.client is None
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True
    )
    try:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with raw_path.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                    f.write(chunk)
    finally:
        if owned_client:
            client.close()

    rows_decoded = 0
    if opts.write_ndjson:
        with raw_path.open("r", encoding="utf-8", errors="replace") as src, \
             ndjson_path.open("w", encoding="utf-8") as dst:
            for line in src:
                row = _parse_row(line)
                if row is None:
                    continue
                rows_decoded += 1
                dst.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
                dst.write("\n")

    raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    revision = f"sha256:{raw_sha}"

    size_bytes = sum(
        p.stat().st_size for p in out_dir.rglob("*") if p.is_file()
    )
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name=f"rir-delegated:{opts.rir}",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": url,
            "rir": opts.rir,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "rowsDecoded": rows_decoded,
            "license": "public-domain-defacto",
            "tier": "A",
        },
    )


def iter_ndjson_rows(ndjson_path: Path) -> Iterable[dict]:
    """Convenience for sensors: stream decoded rows from an NDJSON sidecar."""
    with ndjson_path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                yield json.loads(s)
            except json.JSONDecodeError:
                continue


__all__ = [
    "KNOWN_RIRS",
    "RirDelegatedFetchOpts",
    "fetch",
    "iter_ndjson_rows",
]
