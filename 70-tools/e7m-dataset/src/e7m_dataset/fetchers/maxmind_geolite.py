"""MaxMind GeoLite2 fetcher (City / Country / ASN MMDB).

Per ADR-2605262400 W1. MaxMind distributes GeoLite2 under CC-BY-SA 4.0
since 2019; access requires a free license key (registered MaxMind
account). Pass the key via the ``MAXMIND_LICENSE_KEY`` env var or the
``opts.license_key`` field.

License-tier: Tier A — but **SA propagates**. Corpora derived from
GeoLite2 are licensed CC-BY-SA 4.0 downstream.
"""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult


KNOWN_EDITIONS = ("GeoLite2-City", "GeoLite2-Country", "GeoLite2-ASN")

_DOWNLOAD_URL = "https://download.maxmind.com/app/geoip_download"


@dataclass
class MaxmindGeoliteFetchOpts:
    edition: str = "GeoLite2-Country"
    license_key: Optional[str] = None
    base_url: str = _DOWNLOAD_URL
    timeout_sec: float = 600.0
    client: Optional[httpx.Client] = None
    extract_mmdb: bool = True


class MissingMaxmindKey(RuntimeError):
    """Raised when no MaxMind license key is available."""


def _resolve_key(opts: MaxmindGeoliteFetchOpts) -> str:
    key = opts.license_key or os.environ.get("MAXMIND_LICENSE_KEY", "")
    if not key:
        raise MissingMaxmindKey(
            "No MaxMind license key found. Set MAXMIND_LICENSE_KEY in the "
            "environment or pass license_key= to MaxmindGeoliteFetchOpts."
        )
    return key


def fetch(staging_dir: Path, opts: MaxmindGeoliteFetchOpts) -> FetchResult:
    if opts.edition not in KNOWN_EDITIONS:
        raise ValueError(
            f"unknown GeoLite2 edition '{opts.edition}'. Known: {KNOWN_EDITIONS}"
        )

    license_key = _resolve_key(opts)
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"geolite2-{opts.edition.lower()}-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    tar_path = out_dir / f"{opts.edition}.tar.gz"
    params = {
        "edition_id": opts.edition,
        "license_key": license_key,
        "suffix": "tar.gz",
    }

    owned_client = opts.client is None
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True
    )
    try:
        with client.stream("GET", opts.base_url, params=params) as resp:
            resp.raise_for_status()
            with tar_path.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                    f.write(chunk)
    finally:
        if owned_client:
            client.close()

    extracted: list[str] = []
    if opts.extract_mmdb:
        import tarfile
        with tarfile.open(tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith(".mmdb"):
                    tar.extract(member, path=out_dir)
                    extracted.append(member.name)
                elif member.name.endswith((".txt", ".md", "README", "COPYRIGHT")):
                    tar.extract(member, path=out_dir)
                    extracted.append(member.name)

    tar_sha = hashlib.sha256(tar_path.read_bytes()).hexdigest()
    revision = f"sha256:{tar_sha}"

    size_bytes = sum(
        p.stat().st_size for p in out_dir.rglob("*") if p.is_file()
    )
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name=f"geolite2:{opts.edition.lower()}",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": f"{opts.base_url}?edition_id={opts.edition}&suffix=tar.gz",
            "edition": opts.edition,
            "capturedAt": capture_ts,
            "tarSha256": tar_sha,
            "extractedMembers": extracted,
            "license": "CC-BY-SA-4.0",
            "tier": "A",
            "saPropagates": True,
        },
    )


__all__ = [
    "KNOWN_EDITIONS",
    "MaxmindGeoliteFetchOpts",
    "MissingMaxmindKey",
    "fetch",
]
