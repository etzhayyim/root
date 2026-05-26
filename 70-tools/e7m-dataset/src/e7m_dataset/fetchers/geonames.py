"""GeoNames bulk dataset fetcher.

Stages the gazetteer dump under
``${ETZ_DATASET_ROOT}/datasets-staging/geonames-{dataset}-{captureTs}/``.

Available datasets per the GeoNames `export/dump/` directory:

  - ``cities1000``      (default) — ~3 MB, ~150K rows
  - ``cities5000``      — smaller
  - ``cities15000``     — smaller still
  - ``allCountries``    — ~470 MB compressed, ~12M rows
  - ``allCountriesV2``  — UTF-8 v2

The downloaded zip is extracted in place; both the zip and the unpacked
``.txt`` are kept so the operator can choose what to annex.
"""

from __future__ import annotations

import hashlib
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult


DEFAULT_BASE_URL = "https://download.geonames.org/export/dump"

KNOWN_DATASETS = {
    "cities500",
    "cities1000",
    "cities5000",
    "cities15000",
    "allCountries",
}


@dataclass
class GeonamesFetchOpts:
    dataset: str = "cities1000"
    base_url: str = DEFAULT_BASE_URL
    timeout_sec: float = 600.0
    # Inject for tests.
    client: Optional[httpx.Client] = None


def fetch(staging_dir: Path, opts: GeonamesFetchOpts) -> FetchResult:
    if opts.dataset not in KNOWN_DATASETS:
        raise ValueError(
            f"unknown GeoNames dataset '{opts.dataset}'. Known: {sorted(KNOWN_DATASETS)}"
        )

    url = f"{opts.base_url}/{opts.dataset}.zip"
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dataset_dirname = f"geonames-{opts.dataset}-{capture_ts}"
    out_dir = staging_dir / dataset_dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    zip_path = out_dir / f"{opts.dataset}.zip"

    owned_client = opts.client is None
    client = opts.client or httpx.Client(timeout=opts.timeout_sec, follow_redirects=True)
    try:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with zip_path.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                    f.write(chunk)
    finally:
        if owned_client:
            client.close()

    # Unpack txt next to the zip (operator can annex either or both).
    with zipfile.ZipFile(zip_path) as zf:
        txt_names = [n for n in zf.namelist() if n.endswith(".txt")]
        for tn in txt_names:
            zf.extract(tn, path=out_dir)

    # Revision = sha256 of the downloaded zip. Stable even if GeoNames
    # re-uploads an identical file.
    zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    revision = f"sha256:{zip_sha}"

    size_bytes = sum(
        p.stat().st_size for p in out_dir.rglob("*") if p.is_file()
    )
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name=f"geonames:{opts.dataset}",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": url,
            "dataset": opts.dataset,
            "captured_at": capture_ts,
            "zip_sha256": zip_sha,
        },
    )


__all__ = ["DEFAULT_BASE_URL", "GeonamesFetchOpts", "KNOWN_DATASETS", "fetch"]
