"""OSM PBF extract fetcher (Geofabrik mirror).

Stages a regional ``.osm.pbf`` under
``${ETZ_DATASET_ROOT}/datasets-staging/osm-{region-slug}-{captureTs}/``.

Region is the Geofabrik path slug (no leading slash, no extension), e.g.:

  - ``japan``                                 → asia/japan-latest.osm.pbf
  - ``asia/japan``                            → asia/japan-latest.osm.pbf (explicit)
  - ``europe/germany/berlin``                 → europe/germany/berlin-latest.osm.pbf
  - ``north-america/us/california``           → north-america/us/california-latest.osm.pbf

Geofabrik also serves an MD5 sidecar (``.osm.pbf.md5``) which we fetch
and store next to the bytes for integrity verification. The fetched
checksum is the revision id.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult


DEFAULT_BASE_URL = "https://download.geofabrik.de"

# Top-level Geofabrik regions — used to expand a bare region slug like
# "japan" → "asia/japan" automatically. Operator can always pass the
# full slug to skip this.
GEOFABRIK_TOP_LEVEL = {
    "africa", "antarctica", "asia", "australia-oceania", "central-america",
    "europe", "north-america", "russia", "south-america",
}

# Common shortcuts for popular regions (single-word slugs that resolve
# to a known continent/country).
REGION_ALIASES: dict[str, str] = {
    "japan": "asia/japan",
    "germany": "europe/germany",
    "france": "europe/france",
    "spain": "europe/spain",
    "italy": "europe/italy",
    "united-kingdom": "europe/united-kingdom",
    "great-britain": "europe/great-britain",
    "us": "north-america/us",
    "usa": "north-america/us",
    "canada": "north-america/canada",
    "mexico": "north-america/mexico",
    "brazil": "south-america/brazil",
    "india": "asia/india",
    "china": "asia/china",
    "korea": "asia/south-korea",
    "south-korea": "asia/south-korea",
}


@dataclass
class OsmFetchOpts:
    region: str
    base_url: str = DEFAULT_BASE_URL
    timeout_sec: float = 1800.0
    # If True, additionally fetch the .osm.pbf.md5 sidecar and store it.
    fetch_md5: bool = True
    # Inject for tests.
    client: Optional[httpx.Client] = None


def _resolve_region(region: str) -> str:
    """Normalize the region slug to a Geofabrik path."""
    if "/" in region:
        return region
    if region in REGION_ALIASES:
        return REGION_ALIASES[region]
    if region in GEOFABRIK_TOP_LEVEL:
        # User asked for an entire continent dump — Geofabrik provides
        # these at the top level: e.g. 'europe-latest.osm.pbf'.
        return region
    raise ValueError(
        f"unknown OSM region slug '{region}'. Pass a full Geofabrik path "
        f"(e.g. 'asia/japan', 'europe/germany/berlin') or one of the "
        f"known aliases: {sorted(REGION_ALIASES)}"
    )


def fetch(staging_dir: Path, opts: OsmFetchOpts) -> FetchResult:
    region_path = _resolve_region(opts.region)
    pbf_url = f"{opts.base_url}/{region_path}-latest.osm.pbf"
    md5_url = f"{pbf_url}.md5"

    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    region_slug = region_path.replace("/", "-")
    dataset_dirname = f"osm-{region_slug}-{capture_ts}"
    out_dir = staging_dir / dataset_dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    pbf_path = out_dir / f"{region_slug}-latest.osm.pbf"

    owned_client = opts.client is None
    client = opts.client or httpx.Client(timeout=opts.timeout_sec, follow_redirects=True)
    try:
        with client.stream("GET", pbf_url) as resp:
            resp.raise_for_status()
            with pbf_path.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=256 * 1024):
                    f.write(chunk)

        md5_text: Optional[str] = None
        if opts.fetch_md5:
            md5_resp = client.get(md5_url)
            if md5_resp.status_code == 200:
                md5_text = md5_resp.text
                (out_dir / f"{region_slug}-latest.osm.pbf.md5").write_text(md5_text, encoding="utf-8")
            else:
                # Some regions lack md5 sidecars — non-fatal.
                md5_text = None
    finally:
        if owned_client:
            client.close()

    # Revision = Geofabrik-published MD5 when available; falls back to
    # the local sha256 of the downloaded PBF.
    if md5_text:
        md5_hex = md5_text.split()[0].strip()
        revision = f"md5:{md5_hex}"
    else:
        import hashlib
        sha = hashlib.sha256(pbf_path.read_bytes()).hexdigest()
        revision = f"sha256:{sha}"

    size_bytes = sum(p.stat().st_size for p in out_dir.iterdir() if p.is_file())
    file_count = sum(1 for p in out_dir.iterdir() if p.is_file())

    return FetchResult(
        name=f"osm:{region_path}",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": pbf_url,
            "region": region_path,
            "captured_at": capture_ts,
            "md5_url": md5_url if opts.fetch_md5 else None,
        },
    )


__all__ = [
    "DEFAULT_BASE_URL",
    "GEOFABRIK_TOP_LEVEL",
    "OsmFetchOpts",
    "REGION_ALIASES",
    "fetch",
]
