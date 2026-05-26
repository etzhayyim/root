"""Overture Maps Foundation release fetcher (S3 public bucket).

Stages a theme + type slice of an Overture Maps release as Parquet
under ``${ETZ_DATASET_ROOT}/datasets-staging/overture-{theme}-{type}-{release}-{captureTs}/``.

Per ADR-2605262500 §2 (Tier A — CDLA-Permissive 2.0). Used by wadachi
R1 outdoor scenes for road network + building footprints (per
``scenes/wadachi-r1-shibuya-1km/scene.yaml`` §world.layers vector_roads
+ vector_buildings).

Source = Overture Maps S3 public bucket
(``s3://overturemaps-us-west-2/release/<release>/theme=<theme>/type=<type>/``).
Anonymous HTTP read is supported via the standard S3 REST endpoint —
no AWS credentials required, no Charter §2(c) auth-walled API.

For W1 the fetcher pulls **one Parquet shard** per (theme, type) — enough
to validate the full pipeline end-to-end on the wadachi Shibuya 1km
bbox. Multi-shard / per-region spatial filtering lands at W2 once the
W1 Shibuya scene clears the determinism gate.

Themes / types of interest for ADR-2605262500 W1:

  - ("transportation", "segment") — road network (LineString)
  - ("buildings", "building") — building footprints (Polygon)

Release id convention (Overture's own): ``YYYY-MM-DD.<rev>`` e.g.
``2024-12-12.0``. The latest release id lives in
``s3://overturemaps-us-west-2/release/`` and is the operator's
responsibility to pin in the recipe.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import httpx

from . import FetchResult


DEFAULT_BASE_URL = "https://overturemaps-us-west-2.s3.amazonaws.com"
DEFAULT_USER_AGENT = "etzhayyim-e7m-dataset/0.0.1 (https://etzhayyim.com)"

# Themes / types relevant to ADR-2605262500 W1.
KNOWN_THEME_TYPES: dict[str, tuple[str, ...]] = {
    "transportation": ("segment", "connector"),
    "buildings": ("building", "building_part"),
    "places": ("place",),
    "addresses": ("address",),
    "base": ("land", "land_use", "water", "infrastructure"),
}


@dataclass
class OvertureFetchOpts:
    # Overture release id, e.g. "2024-12-12.0". Operator pins this.
    release: str
    theme: str                          # e.g. "transportation"
    type_name: str                      # e.g. "segment" (TOML's `type` is reserved)
    # First-shard mode: pull part-00000-*.parquet only.  W2 extends to
    # all shards + per-bbox spatial filter via DuckDB extension.
    first_shard_only: bool = True
    # Concrete shard filename to pull (overrides first_shard_only).
    explicit_shard: Optional[str] = None
    base_url: str = DEFAULT_BASE_URL
    user_agent: str = DEFAULT_USER_AGENT
    timeout_sec: float = 600.0
    # Inject httpx.Client for tests.
    client: Optional[httpx.Client] = None


def _validate_theme_type(theme: str, type_name: str) -> None:
    known = KNOWN_THEME_TYPES.get(theme)
    if known is None:
        raise ValueError(
            f"unknown Overture theme '{theme}'. Known: {sorted(KNOWN_THEME_TYPES)}"
        )
    if type_name not in known:
        raise ValueError(
            f"unknown Overture type '{type_name}' for theme '{theme}'. "
            f"Known: {sorted(known)}"
        )


def _list_first_shard(client: httpx.Client, prefix_url: str) -> str:
    """List S3 prefix via REST API, return the first Parquet shard name.

    Uses the public anonymous S3 REST `list-bucket-result` (v2) endpoint
    — no signing required for the overturemaps-us-west-2 bucket.
    """
    list_url = (
        f"{prefix_url.split('/release/')[0]}/?list-type=2"
        f"&prefix={quote(prefix_url.split('amazonaws.com/')[-1])}"
        f"&max-keys=1"
    )
    resp = client.get(list_url)
    resp.raise_for_status()
    # Cheap XML scrape (avoid lxml dep): find <Key>...</Key>.
    body = resp.text
    start = body.find("<Key>")
    end = body.find("</Key>", start)
    if start == -1 or end == -1:
        raise RuntimeError(
            f"Overture S3 prefix appears empty or unreadable: {prefix_url}"
        )
    key = body[start + len("<Key>") : end]
    # Return just the basename for callers.
    return key.split("/")[-1]


def fetch(staging_dir: Path, opts: OvertureFetchOpts) -> FetchResult:
    """Fetch one Parquet shard of an Overture theme+type slice.

    Steps:
      1. Validate theme + type against KNOWN_THEME_TYPES.
      2. Compose S3 prefix:
         release/{release}/theme={theme}/type={type_name}/
      3. Resolve shard name (explicit_shard, else first-shard list).
      4. Stream the Parquet shard to staging dir.
      5. Return FetchResult with revision = release id.
    """
    _validate_theme_type(opts.theme, opts.type_name)

    prefix_path = (
        f"release/{opts.release}/theme={opts.theme}/type={opts.type_name}/"
    )
    prefix_url = f"{opts.base_url}/{prefix_path}"

    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dataset_dirname = (
        f"overture-{opts.theme}-{opts.type_name}-{opts.release}-{capture_ts}"
    )
    out_dir = staging_dir / dataset_dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    owned_client = opts.client is None
    headers = {"User-Agent": opts.user_agent}
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True, headers=headers
    )
    try:
        if opts.explicit_shard:
            shard_name = opts.explicit_shard
        elif opts.first_shard_only:
            shard_name = _list_first_shard(client, prefix_url)
        else:
            raise NotImplementedError(
                "multi-shard fetch is a W2 deliverable per ADR-2605262500 §6 "
                "(W1 is first-shard-only; W2 adds DuckDB-spatial bbox filter)."
            )

        shard_url = f"{prefix_url}{shard_name}"
        shard_path = out_dir / shard_name
        with client.stream("GET", shard_url) as r:
            r.raise_for_status()
            with shard_path.open("wb") as f:
                for chunk in r.iter_bytes(chunk_size=256 * 1024):
                    f.write(chunk)
    finally:
        if owned_client:
            client.close()

    size_bytes = sum(p.stat().st_size for p in out_dir.iterdir() if p.is_file())
    file_count = sum(1 for p in out_dir.iterdir() if p.is_file())

    return FetchResult(
        name=f"overture:{opts.theme}:{opts.type_name}",
        revision=f"overture:{opts.release}",
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "s3-anonymous",
            "base_url": opts.base_url,
            "release": opts.release,
            "theme": opts.theme,
            "overture_type": opts.type_name,
            "shard": shard_name,
            "first_shard_only": opts.first_shard_only,
            "captured_at": capture_ts,
            "license": "CDLA-Permissive-2.0",   # ADR-2605262500 Tier A
        },
    )


__all__ = [
    "DEFAULT_BASE_URL",
    "KNOWN_THEME_TYPES",
    "OvertureFetchOpts",
    "fetch",
]
