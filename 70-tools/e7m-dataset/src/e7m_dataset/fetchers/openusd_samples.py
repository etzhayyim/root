"""Pixar OpenUSD sample-scene fetcher (Apache-2.0).

Stages a single canonical OpenUSD sample (Kitchen Set, Attic, etc.)
under ``${ETZ_DATASET_ROOT}/datasets-staging/openusd-{slug}-{captureTs}/``.

Per ADR-2605262500 §2 (Tier A — Apache 2.0). These scenes are the
reference material for `kami-usd` (tinyusdz) round-tripping and for
`kami-pbrt` shading binding regression tests; they also serve as
known-good USD stages that e7m-sim can load on day 0 without any
external geospatial data.

Source = openusd.org public release downloads — canonical Pixar/AOUSD
hosted ZIPs, no GitHub LFS required:

  - https://openusd.org/release/usd_kitchen_set.zip
  - https://openusd.org/release/usd_shading_attic.zip
  - (smaller samples: instancing shootout, ASWF wg-* archives)

The fetcher exposes a small allowlist of known sample slugs that
have been verified Apache-2.0; callers can also pass an arbitrary
URL via ``explicit_url`` (operator opt-in, license-on-them).
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult


DEFAULT_USER_AGENT = "etzhayyim-e7m-dataset/0.0.1 (https://etzhayyim.com)"

# Allowlist of known-Apache-2.0 sample bundles. The operator pins via
# `slug` — the URL is fixed in-source so a typo can't widen the
# license surface.
KNOWN_SAMPLES: dict[str, str] = {
    "kitchen-set":   "https://openusd.org/release/usd_kitchen_set.zip",
    "shading-attic": "https://openusd.org/release/usd_shading_attic.zip",
    "instancing-shootout": "https://openusd.org/release/usd_instancing_shootout.zip",
}


@dataclass
class OpenUsdSamplesFetchOpts:
    # One of KNOWN_SAMPLES, or use `explicit_url` instead.
    slug: Optional[str] = None
    # Operator-supplied URL for a sample not in KNOWN_SAMPLES. The
    # operator is responsible for verifying the source's license.
    explicit_url: Optional[str] = None
    user_agent: str = DEFAULT_USER_AGENT
    timeout_sec: float = 600.0
    # Inject httpx.Client for tests.
    client: Optional[httpx.Client] = None


def _resolve_url(opts: OpenUsdSamplesFetchOpts) -> tuple[str, str]:
    """Return (url, effective_slug) per opts."""
    if opts.explicit_url:
        # Use the URL basename (minus extension) as the slug.
        base = opts.explicit_url.rsplit("/", 1)[-1]
        for ext in (".zip", ".tar.gz", ".tgz"):
            if base.endswith(ext):
                base = base[: -len(ext)]
                break
        return opts.explicit_url, base
    if opts.slug is None:
        raise ValueError("either `slug` or `explicit_url` is required")
    url = KNOWN_SAMPLES.get(opts.slug)
    if url is None:
        raise ValueError(
            f"unknown OpenUSD sample slug '{opts.slug}'. Known: "
            f"{sorted(KNOWN_SAMPLES)}"
        )
    return url, opts.slug


def fetch(staging_dir: Path, opts: OpenUsdSamplesFetchOpts) -> FetchResult:
    """Fetch one OpenUSD sample archive.

    Steps:
      1. Resolve URL (allowlist or explicit).
      2. Stream the archive to staging dir.
      3. Compute sha256 over the archive for `revision`.
      4. Return FetchResult.
    """
    url, slug = _resolve_url(opts)
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dataset_dirname = f"openusd-{slug}-{capture_ts}"
    out_dir = staging_dir / dataset_dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    # Preserve the upstream filename for transparency.
    archive_name = url.rsplit("/", 1)[-1] or f"{slug}.zip"
    archive_path = out_dir / archive_name

    owned_client = opts.client is None
    headers = {"User-Agent": opts.user_agent}
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True, headers=headers
    )
    try:
        sha = hashlib.sha256()
        with client.stream("GET", url) as r:
            r.raise_for_status()
            with archive_path.open("wb") as f:
                for chunk in r.iter_bytes(chunk_size=256 * 1024):
                    sha.update(chunk)
                    f.write(chunk)
    finally:
        if owned_client:
            client.close()

    size_bytes = archive_path.stat().st_size
    sha_hex = sha.hexdigest()

    return FetchResult(
        name=f"openusd-samples:{slug}",
        revision=f"sha256:{sha_hex}",
        staging_path=out_dir,
        file_count=1,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": url,
            "slug": slug,
            "explicit_url": opts.explicit_url is not None,
            "captured_at": capture_ts,
            "license": "Apache-2.0",   # ADR-2605262500 Tier A — KNOWN_SAMPLES allowlist
        },
    )


__all__ = [
    "KNOWN_SAMPLES",
    "OpenUsdSamplesFetchOpts",
    "fetch",
]
