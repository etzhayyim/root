"""Microsoft Global Building Footprints fetcher (Azure-hosted CSV index).

Stages a per-country GeoJSON archive of Microsoft Maps-derived
building footprints under
``${ETZ_DATASET_ROOT}/datasets-staging/ms-buildings-{country}-{captureTs}/``.

Per ADR-2605262500 §2 (Tier A — ODbL 1.0; same share-alike treatment
as OSM Geofabrik per ADR-2605262400 §2). Used as the building polygon
fallback when Overture's buildings theme is sparse for a region (e.g.
some non-Japan / non-US extents in 2024-12 release).

Source = Microsoft's public Azure-hosted dataset distribution:

  - Index CSV: https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv
  - Per-quad-key GeoJSONL.gz files: https://minedbuildings.blob.core.windows.net/global-buildings/...

The index CSV is small (~few MB) and lists per-country + per-quadkey
GeoJSONL.gz URLs. For W2 the fetcher pulls ONE quadkey per call
(operator-chosen, or the first quadkey within the requested country).
Multi-quadkey + per-bbox spatial filtering is deferred to W3 where
the Charter Rider rescan boundary makes per-shard control valuable.

This fetcher is independent of `e7m-dataset/fetchers/overture.py` —
choose Overture by default; fall back to MS Buildings when Overture
returns no records for a region (operator-driven choice in the
SceneRecipe).
"""

from __future__ import annotations

import csv
import io
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult


DEFAULT_INDEX_URL = (
    "https://minedbuildings.z5.web.core.windows.net/"
    "global-buildings/dataset-links.csv"
)
DEFAULT_USER_AGENT = "etzhayyim-e7m-dataset/0.0.1 (https://etzhayyim.com)"


@dataclass
class MsBuildingsFetchOpts:
    # ISO 3166-1 alpha-2 / alpha-3 or MS-defined country slug.
    # When set, fetcher resolves the FIRST quadkey for this country.
    country: Optional[str] = None
    # Explicit quadkey to pull (overrides `country`).
    quadkey: Optional[str] = None
    index_url: str = DEFAULT_INDEX_URL
    user_agent: str = DEFAULT_USER_AGENT
    timeout_sec: float = 600.0
    # Inject httpx.Client for tests.
    client: Optional[httpx.Client] = None


def _parse_index_csv(index_text: str) -> list[dict[str, str]]:
    """Parse the dataset-links.csv into a list of dicts.

    Expected columns (per MS schema): Location, QuadKey, Url, Size
    """
    reader = csv.DictReader(io.StringIO(index_text))
    rows: list[dict[str, str]] = []
    for row in reader:
        rows.append({(k or "").strip(): (v or "").strip() for k, v in row.items()})
    return rows


def _select_index_row(rows: list[dict[str, str]], opts: MsBuildingsFetchOpts) -> dict[str, str]:
    if opts.quadkey:
        for r in rows:
            if r.get("QuadKey") == opts.quadkey:
                return r
        raise RuntimeError(f"MS Buildings index has no entry for quadkey '{opts.quadkey}'")
    if opts.country:
        country_norm = opts.country.lower()
        for r in rows:
            if r.get("Location", "").lower() == country_norm:
                return r
        raise RuntimeError(
            f"MS Buildings index has no Location matching '{opts.country}'. "
            f"Try the MS slug (e.g. 'Japan' not 'JP')."
        )
    raise ValueError("either `country` or `quadkey` is required")


def fetch(staging_dir: Path, opts: MsBuildingsFetchOpts) -> FetchResult:
    """Fetch one MS Buildings quadkey GeoJSONL.gz file.

    Steps:
      1. GET the index CSV.
      2. Select a row matching `quadkey` (if set) or first match for `country`.
      3. Stream the row's Url to staging.
      4. Persist the index CSV row alongside for audit trail.
      5. Return FetchResult with revision = quadkey + captureTs.
    """
    owned_client = opts.client is None
    headers = {"User-Agent": opts.user_agent}
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True, headers=headers
    )
    try:
        # 1. Index CSV.
        idx_resp = client.get(opts.index_url)
        idx_resp.raise_for_status()
        rows = _parse_index_csv(idx_resp.text)

        # 2. Row selection.
        row = _select_index_row(rows, opts)
        url = row["Url"]
        quadkey = row.get("QuadKey", opts.quadkey or "")
        location = row.get("Location", opts.country or "")

        # 3. Staging dir.
        capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        slug = location.lower().replace(" ", "-") or quadkey
        dataset_dirname = f"ms-buildings-{slug}-{quadkey}-{capture_ts}"
        out_dir = staging_dir / dataset_dirname
        out_dir.mkdir(parents=True, exist_ok=True)

        # 4. Persist the index row for the manifest.
        (out_dir / "index_row.json").write_text(
            "\n".join([f'"{k}": "{v}"' for k, v in row.items()]),
            encoding="utf-8",
        )

        # 5. Stream the GeoJSONL.gz.
        # Extract filename from URL (last path segment).
        url_basename = url.rsplit("/", 1)[-1] or f"{quadkey}.geojsonl.gz"
        out_file = out_dir / url_basename
        with client.stream("GET", url) as r:
            r.raise_for_status()
            with out_file.open("wb") as f:
                for chunk in r.iter_bytes(chunk_size=256 * 1024):
                    f.write(chunk)
    finally:
        if owned_client:
            client.close()

    size_bytes = sum(p.stat().st_size for p in out_dir.iterdir() if p.is_file())
    file_count = sum(1 for p in out_dir.iterdir() if p.is_file())

    return FetchResult(
        name=f"ms-buildings:{location}:{quadkey}",
        revision=f"ms-buildings:{quadkey}:{capture_ts}",
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "index_url": opts.index_url,
            "location": location,
            "quadkey": quadkey,
            "asset_url": url,
            "asset_size_csv": row.get("Size"),
            "captured_at": capture_ts,
            "license": "ODbL-1.0",   # ADR-2605262500 Tier A
        },
    )


__all__ = [
    "DEFAULT_INDEX_URL",
    "MsBuildingsFetchOpts",
    "fetch",
]
