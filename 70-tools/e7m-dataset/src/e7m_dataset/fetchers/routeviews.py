"""University of Oregon Routeviews MRT dump fetcher.

Per ADR-2605262400 W2. Routeviews is a long-running BGP collection
project at UO; archives are organized as:

  http://archive.routeviews.org/<collector>/bgpdata/<YYYY.MM>/RIBS/rib.<YYYYMMDD>.<HHMM>.bz2

  - ``rib.*``     — 2-hourly RIB snapshot
  - ``updates.*`` — 15-min UPDATE stream

Wave-2 fetches a single RIB ``rib`` per (collector, captureAt). 15-min
UPDATE streaming is out of scope for Wave-2.

License: open under UO Terms of Use. Tagged Tier A. (UO permits research
+ operational use; archives are publicly accessible without login.)

The fetcher stages the bzip2'd MRT file AS-IS. Decoding is the sensor's
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


_DEFAULT_BASE = "http://archive.routeviews.org"

# A representative subset of Routeviews collectors that have been
# publishing continuously since at least 2020. Aliases are intentional
# — the bare ``route-views2`` does not have a per-collector subpath.
KNOWN_COLLECTORS = (
    "",                # → route-views2.routeviews.org (no subpath)
    "route-views3",
    "route-views4",
    "route-views5",
    "route-views6",
    "route-views.amsix",
    "route-views.chicago",
    "route-views.eqix",
    "route-views.jinx",
    "route-views.linx",
    "route-views.napafrica",
    "route-views.nwax",
    "route-views.perth",
    "route-views.sg",
    "route-views.soxrs",
    "route-views.sydney",
    "route-views.telxatl",
    "route-views.wide",
)


@dataclass
class RouteviewsFetchOpts:
    collector: str = ""  # empty string → route-views2 (default collector)
    year: int = 2026
    month: int = 5
    day: int = 26
    hour: int = 0  # rib cadence is 2-hourly (0, 2, 4, ..., 22)
    minute: int = 0
    base_url: str = _DEFAULT_BASE
    timeout_sec: float = 600.0
    client: Optional[httpx.Client] = None


def _build_url(opts: RouteviewsFetchOpts) -> str:
    if opts.collector not in KNOWN_COLLECTORS:
        raise ValueError(
            f"unknown Routeviews collector '{opts.collector}'. "
            f"Known: {KNOWN_COLLECTORS}"
        )
    prefix = "" if opts.collector == "" else f"/{opts.collector}"
    yyyymm = f"{opts.year:04d}.{opts.month:02d}"
    yyyymmdd = f"{opts.year:04d}{opts.month:02d}{opts.day:02d}"
    hhmm = f"{opts.hour:02d}{opts.minute:02d}"
    return f"{opts.base_url}{prefix}/bgpdata/{yyyymm}/RIBS/rib.{yyyymmdd}.{hhmm}.bz2"


def fetch(staging_dir: Path, opts: RouteviewsFetchOpts) -> FetchResult:
    url = _build_url(opts)
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    coll_slug = opts.collector if opts.collector != "" else "route-views2"
    dirname = (
        f"routeviews-{coll_slug}-"
        f"{opts.year:04d}{opts.month:02d}{opts.day:02d}-"
        f"{opts.hour:02d}{opts.minute:02d}-{capture_ts}"
    )
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    snapshot_name = (
        f"rib.{opts.year:04d}{opts.month:02d}{opts.day:02d}."
        f"{opts.hour:02d}{opts.minute:02d}.bz2"
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
        name=(
            f"routeviews:{coll_slug}:"
            f"{opts.year:04d}{opts.month:02d}{opts.day:02d}T"
            f"{opts.hour:02d}{opts.minute:02d}Z"
        ),
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": url,
            "collector": coll_slug,
            "snapshotAt": (
                f"{opts.year:04d}-{opts.month:02d}-{opts.day:02d}T"
                f"{opts.hour:02d}:{opts.minute:02d}:00Z"
            ),
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "license": "uo-tou-open",
            "tier": "A",
            "uoAttribution": (
                "Source: University of Oregon Route Views Project — "
                "http://www.routeviews.org/routeviews/"
            ),
        },
    )


__all__ = ["KNOWN_COLLECTORS", "RouteviewsFetchOpts", "fetch"]
