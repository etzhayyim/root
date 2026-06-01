"""RIPE NCC RIS MRT dump fetcher.

Per ADR-2605262400 W2. The RIPE Routing Information Service (RIS)
publishes BGP RIB + UPDATE dumps in MRT format from ~20 collector
points (``rrc00`` .. ``rrc26``) at:

  https://data.ris.ripe.net/<rrc>/<YYYY.MM>/{bview,updates}.<YYYYMMDD>.<HHMM>.gz

  - ``bview.*``    — 8-hourly RIB snapshot (00:00, 08:00, 16:00 UTC)
  - ``updates.*``  — 5-minute UPDATE stream

Wave-2 fetches a single RIB ``bview`` per (collector, captureAt) — that
gives the global Internet routing table as observed by that collector
at the snapshot time. The 5-min UPDATE stream is out of scope for
Wave-2 (volume implications; W3 if needed for delta-tracking).

License: open under RIPE Terms of Use. Tagged Tier A.

The fetcher stages the gzipped MRT file AS-IS. Decoding is the sensor's
responsibility (via ``mrtparse``).
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult


_DEFAULT_BASE = "https://data.ris.ripe.net"


# RRC collectors that have published since at least 2021. RRC IDs not
# in this list are treated as unknown so the fetcher fails-closed
# rather than silently 404-ing.
KNOWN_RRCS = tuple(f"rrc{i:02d}" for i in (0, 1, 3, 4, 5, 6, 7, 10, 11, 12,
                                            13, 14, 15, 16, 18, 19, 20, 21,
                                            22, 23, 24, 25, 26))


@dataclass
class RipeRisFetchOpts:
    collector: str = "rrc00"
    # Snapshot identifier — local time the RIB was dumped. For RIPE RIS
    # the bview cadence is 00:00 / 08:00 / 16:00 UTC; we accept the
    # full minute mark and let the operator round.
    year: int = 2026
    month: int = 5
    day: int = 26
    hour: int = 0  # 0 / 8 / 16 for RIB
    minute: int = 0
    base_url: str = _DEFAULT_BASE
    timeout_sec: float = 600.0
    client: Optional[httpx.Client] = None


def _build_url(opts: RipeRisFetchOpts) -> str:
    if opts.collector not in KNOWN_RRCS:
        raise ValueError(
            f"unknown RIPE RIS collector '{opts.collector}'. Known: {KNOWN_RRCS}"
        )
    yyyymm = f"{opts.year:04d}.{opts.month:02d}"
    yyyymmdd = f"{opts.year:04d}{opts.month:02d}{opts.day:02d}"
    hhmm = f"{opts.hour:02d}{opts.minute:02d}"
    return f"{opts.base_url}/{opts.collector}/{yyyymm}/bview.{yyyymmdd}.{hhmm}.gz"


def fetch(staging_dir: Path, opts: RipeRisFetchOpts) -> FetchResult:
    url = _build_url(opts)
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = (
        f"ris-mrt-{opts.collector}-"
        f"{opts.year:04d}{opts.month:02d}{opts.day:02d}-"
        f"{opts.hour:02d}{opts.minute:02d}-{capture_ts}"
    )
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    snapshot_name = (
        f"bview.{opts.year:04d}{opts.month:02d}{opts.day:02d}."
        f"{opts.hour:02d}{opts.minute:02d}.gz"
    )
    mrt_path = out_dir / snapshot_name

    owned_client = opts.client is None
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True
    )
    try:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with mrt_path.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                    f.write(chunk)
    finally:
        if owned_client:
            client.close()

    raw_sha = hashlib.sha256(mrt_path.read_bytes()).hexdigest()
    revision = f"sha256:{raw_sha}"

    size_bytes = sum(
        p.stat().st_size for p in out_dir.rglob("*") if p.is_file()
    )
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name=f"ris-mrt:{opts.collector}:{opts.year:04d}{opts.month:02d}{opts.day:02d}T{opts.hour:02d}{opts.minute:02d}Z",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": url,
            "collector": opts.collector,
            "snapshotAt": (
                f"{opts.year:04d}-{opts.month:02d}-{opts.day:02d}T"
                f"{opts.hour:02d}:{opts.minute:02d}:00Z"
            ),
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "license": "ripe-tou-open",
            "tier": "A",
            "ripeAttribution": (
                "Source: RIPE NCC Routing Information Service (RIS) — "
                "https://www.ripe.net/analyse/internet-measurements/"
                "routing-information-service-ris/"
            ),
        },
    )


__all__ = ["KNOWN_RRCS", "RipeRisFetchOpts", "fetch"]
