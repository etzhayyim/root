"""USGS 3DEP 1m DEM fetcher (Amazon S3 LiDAR-derived).

Stages a USGS 3D Elevation Program (3DEP) 1m-resolution GeoTIFF tile
under ``${ETZ_DATASET_ROOT}/datasets-staging/usgs-3dep-{tile_id}-{captureTs}/``.

Per ADR-2605262500 §2 (Tier A — USGS public-domain). US coverage only —
non-US scenes use SRTM 30m (`fetchers/srtm.py`) as the elevation source.

Source = USGS 3DEP S3 public buckets via the AWS Open Data registry:

  - https://registry.opendata.aws/usgs-lidar/
  - Per-project COG / GeoTIFF at:
    s3://prd-tnm/StagedProducts/Elevation/1m/Projects/<project>/TIFF/<tile>.tif

For W2 the fetcher pulls ONE tile per call given an explicit
project + tile name (operator-chosen from USGS TNM Download Client).
Per-bbox spatial fan-out lands at W3 alongside the Overture multi-shard
extension.

The fetcher does NOT use AWS credentials — `prd-tnm` is anonymous-
read enabled. If the bucket ever requires authentication, the fetcher
MUST fail closed (no Charter §2(c) auth-walled fallback).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult


DEFAULT_BASE_URL = "https://prd-tnm.s3.amazonaws.com"
DEFAULT_PRODUCT_PREFIX = "StagedProducts/Elevation/1m/Projects"
DEFAULT_USER_AGENT = "etzhayyim-e7m-dataset/0.0.1 (https://etzhayyim.com)"


@dataclass
class Usgs3depFetchOpts:
    # USGS project slug, e.g. "CA_NorCal_3DEP_2019_A19" (operator pins
    # this from the TNM Download Client).
    project: str
    # Tile file basename without extension, e.g. "USGS_1m_10_x40y455_CA_FEMA_R9_2018_B18".
    tile_name: str
    # File extension — usually 'tif' for COG. Some 3DEP projects also
    # publish '.tif.aux.xml' sidecars; W2 limits to the primary .tif.
    file_ext: str = "tif"
    base_url: str = DEFAULT_BASE_URL
    product_prefix: str = DEFAULT_PRODUCT_PREFIX
    user_agent: str = DEFAULT_USER_AGENT
    timeout_sec: float = 600.0
    # Inject httpx.Client for tests.
    client: Optional[httpx.Client] = None


def _build_asset_url(opts: Usgs3depFetchOpts) -> str:
    return (
        f"{opts.base_url}/{opts.product_prefix}/"
        f"{opts.project}/TIFF/{opts.tile_name}.{opts.file_ext}"
    )


def fetch(staging_dir: Path, opts: Usgs3depFetchOpts) -> FetchResult:
    """Fetch one 3DEP 1m DEM tile from the USGS S3 anonymous bucket.

    Steps:
      1. Build the asset URL from project + tile_name.
      2. Stream the .tif into the staging dir.
      3. Return FetchResult with revision = project:tile_name:captureTs.
    """
    if not opts.project or not opts.tile_name:
        raise ValueError("USGS 3DEP fetch requires both `project` and `tile_name`")

    asset_url = _build_asset_url(opts)

    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dataset_dirname = f"usgs-3dep-{opts.project}-{opts.tile_name}-{capture_ts}"
    out_dir = staging_dir / dataset_dirname
    out_dir.mkdir(parents=True, exist_ok=True)
    tif_path = out_dir / f"{opts.tile_name}.{opts.file_ext}"

    owned_client = opts.client is None
    headers = {"User-Agent": opts.user_agent, "Accept": "image/tiff"}
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True, headers=headers
    )
    try:
        with client.stream("GET", asset_url) as r:
            r.raise_for_status()
            with tif_path.open("wb") as f:
                for chunk in r.iter_bytes(chunk_size=256 * 1024):
                    f.write(chunk)
    finally:
        if owned_client:
            client.close()

    size_bytes = tif_path.stat().st_size
    return FetchResult(
        name=f"usgs-3dep:{opts.project}:{opts.tile_name}",
        revision=f"usgs-3dep:{opts.project}:{opts.tile_name}:{capture_ts}",
        staging_path=out_dir,
        file_count=1,
        size_bytes=size_bytes,
        source={
            "type": "s3-anonymous",
            "base_url": opts.base_url,
            "project": opts.project,
            "tile_name": opts.tile_name,
            "asset_url": asset_url,
            "captured_at": capture_ts,
            "license": "public-domain-USGS",   # ADR-2605262500 Tier A
        },
    )


__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_PRODUCT_PREFIX",
    "Usgs3depFetchOpts",
    "fetch",
]
