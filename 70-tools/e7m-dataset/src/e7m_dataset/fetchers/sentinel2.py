"""Sentinel-2 L2A COG fetcher via AWS Earth Search STAC API.

Stages a regional Sentinel-2 L2A scene (Cloud-Optimized GeoTIFFs for
the requested bands, default RGB = B04/B03/B02) under
``${ETZ_DATASET_ROOT}/datasets-staging/sentinel2-{tile_id}-{captureTs}/``.

Per ADR-2605262500 §2 (Tier A — Copernicus free, attribution required).
This module ports the Sentinel-2 access pattern proven in
ADR-2605215100 maps_sentinel_murakumo M1 T0 into the e7m-dataset
fetcher contract (matches osm.py / wikidata.py shape).

Source = AWS Earth Search STAC v1 catalog (free, no API key):

  - STAC: https://earth-search.aws.element84.com/v1/search
  - Asset bucket: s3://sentinel-cogs/sentinel-s2-l2a-cogs/

Caller passes either:

  - a Sentinel-2 MGRS tile id (e.g. ``T54SUE`` covers Tokyo 23-ku),
    plus a date window — first matching scene below cloud_cover_max
    is selected; OR
  - a STAC item id directly (e.g. ``S2A_T54SUE_20240501_0_L2A``) for
    fully reproducible pinning.

The selected scene's STAC item JSON is preserved alongside the COG
assets so the datasetPin manifest can record the exact STAC item id,
band list, and acquisition date.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult


DEFAULT_STAC_URL = "https://earth-search.aws.element84.com/v1/search"
DEFAULT_COLLECTION = "sentinel-2-l2a"
DEFAULT_BANDS: tuple[str, ...] = ("B04", "B03", "B02")  # RGB B432 per scene.yaml
DEFAULT_USER_AGENT = "etzhayyim-e7m-dataset/0.0.1 (https://etzhayyim.com)"


@dataclass
class Sentinel2FetchOpts:
    # MGRS tile id (e.g. "T54SUE") — required unless `stac_item_id` is set.
    tile_id: Optional[str] = None
    # Pin a specific STAC item id (e.g. "S2A_T54SUE_20240501_0_L2A").
    stac_item_id: Optional[str] = None
    # ISO-8601 datetime window (e.g. "2024-04-01/2024-05-31").
    datetime_range: Optional[str] = None
    # Bands to download as COGs. Default = RGB B432.
    bands: tuple[str, ...] = DEFAULT_BANDS
    # Maximum allowed cloud cover percentage on the selected scene.
    cloud_cover_max: float = 20.0
    # STAC API URL — overrideable for testing / mirror.
    stac_url: str = DEFAULT_STAC_URL
    collection: str = DEFAULT_COLLECTION
    user_agent: str = DEFAULT_USER_AGENT
    timeout_sec: float = 600.0
    # Inject httpx.Client for tests.
    client: Optional[httpx.Client] = None


def _stac_search_payload(opts: Sentinel2FetchOpts) -> dict:
    """Build a STAC `/search` POST payload."""
    payload: dict = {
        "collections": [opts.collection],
        "limit": 10,
        "sortby": [{"field": "properties.eo:cloud_cover", "direction": "asc"}],
    }
    if opts.stac_item_id:
        payload["ids"] = [opts.stac_item_id]
        return payload

    if not opts.tile_id:
        raise ValueError("either `tile_id` or `stac_item_id` is required")
    payload["query"] = {
        "grid:code": {"eq": f"MGRS-{opts.tile_id.lstrip('T')}"},
        "eo:cloud_cover": {"lt": opts.cloud_cover_max},
    }
    if opts.datetime_range:
        payload["datetime"] = opts.datetime_range
    return payload


def _select_item(features: list[dict], opts: Sentinel2FetchOpts) -> dict:
    if not features:
        raise RuntimeError(
            f"no Sentinel-2 L2A scenes matched (tile={opts.tile_id}, "
            f"range={opts.datetime_range}, cloud<{opts.cloud_cover_max})"
        )
    # STAC search is already sorted by cloud_cover asc; take the first.
    return features[0]


def fetch(staging_dir: Path, opts: Sentinel2FetchOpts) -> FetchResult:
    """Fetch a Sentinel-2 L2A scene from AWS Earth Search.

    Steps:
      1. POST `/search` with tile id + date range + cloud filter → STAC items
      2. Select the lowest-cloud-cover item
      3. Download each requested band's COG asset
      4. Write the STAC item JSON next to the COGs
      5. Return FetchResult with revision = STAC item id
    """
    owned_client = opts.client is None
    headers = {"User-Agent": opts.user_agent, "Accept": "application/json"}
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True, headers=headers
    )
    try:
        # 1. STAC search.
        payload = _stac_search_payload(opts)
        resp = client.post(opts.stac_url, json=payload)
        resp.raise_for_status()
        body = resp.json()
        features: list[dict] = body.get("features", [])
        item = _select_item(features, opts)

        # 2. Build staging dir.
        item_id = item["id"]
        capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        # Slug = scene's MGRS tile + acquisition date (stable, audit-trail friendly).
        slug = item_id.replace("/", "-")
        dataset_dirname = f"sentinel2-{slug}-{capture_ts}"
        out_dir = staging_dir / dataset_dirname
        out_dir.mkdir(parents=True, exist_ok=True)

        # 3. Persist the STAC item JSON.
        item_json_path = out_dir / "stac_item.json"
        item_json_path.write_text(json.dumps(item, indent=2), encoding="utf-8")

        # 4. Download each band asset.
        assets: dict = item.get("assets", {})
        fetched_bands: list[str] = []
        for band in opts.bands:
            asset = assets.get(band)
            if asset is None:
                # Some bands are named with lowercase or alt keys — skip + record.
                continue
            href = asset.get("href")
            if not href:
                continue
            band_path = out_dir / f"{band}.tif"
            with client.stream("GET", href) as r:
                r.raise_for_status()
                with band_path.open("wb") as f:
                    for chunk in r.iter_bytes(chunk_size=256 * 1024):
                        f.write(chunk)
            fetched_bands.append(band)

        if not fetched_bands:
            raise RuntimeError(
                f"no bands could be fetched for STAC item {item_id} "
                f"(requested: {opts.bands})"
            )

    finally:
        if owned_client:
            client.close()

    size_bytes = sum(p.stat().st_size for p in out_dir.iterdir() if p.is_file())
    file_count = sum(1 for p in out_dir.iterdir() if p.is_file())

    return FetchResult(
        name=f"sentinel2:{item_id}",
        revision=f"stac:{item_id}",
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "stac",
            "stac_url": opts.stac_url,
            "collection": opts.collection,
            "stac_item_id": item_id,
            "tile_id": opts.tile_id,
            "datetime_range": opts.datetime_range,
            "cloud_cover_max": opts.cloud_cover_max,
            "bands_requested": list(opts.bands),
            "bands_fetched": fetched_bands,
            "cloud_cover_pct": item.get("properties", {}).get("eo:cloud_cover"),
            "captured_at": capture_ts,
            "license": "Copernicus-free-attribution",   # ADR-2605262500 Tier A
        },
    )


__all__ = [
    "DEFAULT_BANDS",
    "DEFAULT_COLLECTION",
    "DEFAULT_STAC_URL",
    "Sentinel2FetchOpts",
    "fetch",
]
