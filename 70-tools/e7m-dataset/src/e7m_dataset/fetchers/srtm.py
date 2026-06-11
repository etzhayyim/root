"""SRTM 1-arc-second (30m) global DEM fetcher via OpenTopography.

Stages SRTMGL1 1°×1° tiles as GeoTIFF under
``${ETZ_DATASET_ROOT}/datasets-staging/srtm-{tile_id}-{captureTs}/``.

Per ADR-2605262500 §2 (Tier A — NASA SRTMGL1 is public-domain).
Used by wadachi R1 outdoor scenes as the terrain layer (per
``scenes/wadachi-r1-shibuya-1km/scene.yaml`` §world.layers[0]).

Source = OpenTopography Global DEM API (free, optional API key for
larger quotas):

  - https://portal.opentopography.org/API/globaldem
  - DEM type = SRTMGL1 (1-arc-second ≈ 30m)

Tile id convention: NASA SRTM tile naming, e.g. ``n35e139`` covers
35°-36° N × 139°-140° E (the 1°×1° square that contains Tokyo Shibuya).

Why OpenTopography and not USGS / CGIAR direct: OpenTopography
serves a clean GeoTIFF mosaic with consistent CRS (EPSG:4326), no
HGT/SRTMHGT zip-unpack ceremony, and a per-request bbox API that
returns exactly the bytes we need. NASA Earthdata Login is avoided
(Charter §2(c) — no third-party account-walled APIs in the religious-
corp ingest path).

CRITICAL: if OpenTopography ever requires authentication for SRTMGL1
(currently free up to 50 requests/day without a key, higher with a
free key), the fetcher MUST fail closed rather than silently degrade
— the operator should set ``ETZ_OPENTOPO_API_KEY`` env and re-run.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult


DEFAULT_API_URL = "https://portal.opentopography.org/API/globaldem"
DEFAULT_DEM_TYPE = "SRTMGL1"   # 1-arc-second ≈ 30m
DEFAULT_USER_AGENT = "etzhayyim-e7m-dataset/0.0.1 (https://etzhayyim.com)"


@dataclass
class SrtmFetchOpts:
    # NASA SRTM tile id, e.g. "n35e139". Determines the 1°×1° bbox.
    tile_id: str
    # Override the 1°×1° bbox with a custom one (north, south, east, west).
    # When set, takes precedence over `tile_id`'s implicit bbox.
    bbox_override: Optional[tuple[float, float, float, float]] = None
    dem_type: str = DEFAULT_DEM_TYPE
    api_url: str = DEFAULT_API_URL
    # API key — optional for ≤ 50 req/day per IP, recommended for fleet use.
    # Pulled from ETZ_OPENTOPO_API_KEY env when None.
    api_key: Optional[str] = None
    user_agent: str = DEFAULT_USER_AGENT
    timeout_sec: float = 300.0
    # Inject httpx.Client for tests.
    client: Optional[httpx.Client] = None


def _parse_tile_id(tile_id: str) -> tuple[float, float, float, float]:
    """Parse an SRTM tile id (e.g. ``n35e139``) into (N, S, E, W) bbox.

    Returns (north, south, east, west) per OpenTopography API param order.
    """
    tid = tile_id.lower().strip()
    if len(tid) < 7:
        raise ValueError(f"unrecognized SRTM tile id '{tile_id}'")
    ns_hemi = tid[0]
    if ns_hemi not in ("n", "s"):
        raise ValueError(f"SRTM tile id '{tile_id}' must start with 'n' or 's'")
    # Latitude band index is 2 digits after n/s.
    try:
        lat_idx = int(tid[1:3])
    except ValueError as e:
        raise ValueError(f"SRTM tile id '{tile_id}': bad latitude digits") from e
    ew_hemi = tid[3]
    if ew_hemi not in ("e", "w"):
        raise ValueError(f"SRTM tile id '{tile_id}' missing 'e' or 'w' separator")
    try:
        lon_idx = int(tid[4:7])
    except ValueError as e:
        raise ValueError(f"SRTM tile id '{tile_id}': bad longitude digits") from e

    south = float(lat_idx) if ns_hemi == "n" else -float(lat_idx)
    north = south + 1.0
    west = float(lon_idx) if ew_hemi == "e" else -float(lon_idx)
    east = west + 1.0
    return north, south, east, west


def fetch(staging_dir: Path, opts: SrtmFetchOpts) -> FetchResult:
    """Fetch a single SRTM tile from OpenTopography.

    Steps:
      1. Resolve bbox from tile_id (or use bbox_override).
      2. GET globaldem with demtype=SRTMGL1, outputFormat=GTiff.
      3. Stream GeoTIFF bytes into staging dir.
      4. Return FetchResult with revision = tile_id + captureTs.
    """
    if opts.bbox_override is not None:
        north, south, east, west = opts.bbox_override
    else:
        north, south, east, west = _parse_tile_id(opts.tile_id)

    api_key = opts.api_key or os.environ.get("ETZ_OPENTOPO_API_KEY")
    params = {
        "demtype": opts.dem_type,
        "south": str(south),
        "north": str(north),
        "west": str(west),
        "east": str(east),
        "outputFormat": "GTiff",
    }
    if api_key:
        params["API_Key"] = api_key

    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dataset_dirname = f"srtm-{opts.tile_id.lower()}-{capture_ts}"
    out_dir = staging_dir / dataset_dirname
    out_dir.mkdir(parents=True, exist_ok=True)
    tif_path = out_dir / f"{opts.tile_id.lower()}.tif"

    owned_client = opts.client is None
    headers = {"User-Agent": opts.user_agent, "Accept": "image/tiff"}
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True, headers=headers
    )
    try:
        with client.stream("GET", opts.api_url, params=params) as r:
            r.raise_for_status()
            with tif_path.open("wb") as f:
                for chunk in r.iter_bytes(chunk_size=256 * 1024):
                    f.write(chunk)
    finally:
        if owned_client:
            client.close()

    size_bytes = tif_path.stat().st_size
    return FetchResult(
        name=f"srtm:{opts.tile_id.lower()}",
        revision=f"srtm:{opts.dem_type}:{opts.tile_id.lower()}:{capture_ts}",
        staging_path=out_dir,
        file_count=1,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "api_url": opts.api_url,
            "dem_type": opts.dem_type,
            "tile_id": opts.tile_id.lower(),
            "bbox": {"north": north, "south": south, "east": east, "west": west},
            "captured_at": capture_ts,
            "api_key_used": api_key is not None,
            "license": "public-domain-NASA",   # ADR-2605262500 Tier A
        },
    )


__all__ = [
    "DEFAULT_API_URL",
    "DEFAULT_DEM_TYPE",
    "SrtmFetchOpts",
    "fetch",
]
