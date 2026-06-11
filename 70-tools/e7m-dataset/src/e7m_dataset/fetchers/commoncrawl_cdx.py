"""Common Crawl URL index (CDX) fetcher.

Per ADR-2605262400 W4. Common Crawl publishes monthly+ web-archive
crawls; the **URL index** (CDX) is the catalog — one row per archived
URL with offset + length pointers into the corresponding WARC. CDX
records are line-oriented JSON (CDX-J) or columnar (CDX-A).

Wave-4 ships the CDX-J monthly index, which is the catalog the organism
needs for host-graph reasoning. Pulling full WARCs is out of scope (and
would explode storage budget).

License/TOS: Common Crawl is freely accessible from the AWS Public
Dataset bucket; redistribution under share-alike research-use terms.
Tier C — admitted under G13 fleet-internal carve-out per the user's
W3 decision.

PII-sensitivity: TRUE by default — CDX records contain raw URLs which
can embed user-bearing query strings, email addresses, session tokens.
Sensor-layer PII filter scrubs the URL field.

Acceptance flag (mandatory):

  ~/.etzhayyim/source-acceptance/commoncrawl.toml
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult
from ._acceptance import require_acceptance


_DEFAULT_BASE = "https://data.commoncrawl.org"


@dataclass
class CommonCrawlCdxFetchOpts:
    # Crawl identifier — e.g. "CC-MAIN-2026-22" (monthly slug).
    crawl_id: str = ""
    # Specific CDX index shard within the crawl — e.g.
    # "cc-index/collections/CC-MAIN-2026-22/indexes/cdx-00000.gz".
    archive_path: str = ""
    base_url: str = _DEFAULT_BASE
    timeout_sec: float = 1800.0
    client: Optional[httpx.Client] = None
    acceptance_source: str = "commoncrawl"


def fetch(staging_dir: Path, opts: CommonCrawlCdxFetchOpts) -> FetchResult:
    if not opts.crawl_id:
        raise ValueError(
            "CommonCrawlCdxFetchOpts.crawl_id is required "
            "(e.g. 'CC-MAIN-2026-22')."
        )
    if not opts.archive_path:
        raise ValueError(
            "CommonCrawlCdxFetchOpts.archive_path is required "
            "(e.g. 'cc-index/collections/CC-MAIN-2026-22/"
            "indexes/cdx-00000.gz')."
        )

    acceptance = require_acceptance(opts.acceptance_source)

    url = f"{opts.base_url}/{opts.archive_path}"
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    archive_slug = opts.archive_path.replace("/", "_")
    dirname = f"commoncrawl-cdx-{opts.crawl_id}-{archive_slug}-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    archive_path = out_dir / opts.archive_path.rsplit("/", 1)[-1]

    owned_client = opts.client is None
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec, follow_redirects=True
    )
    try:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with archive_path.open("wb") as f:
                for chunk in resp.iter_bytes(chunk_size=64 * 1024):
                    f.write(chunk)
    finally:
        if owned_client:
            client.close()

    raw_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    revision = f"sha256:{raw_sha}"

    size_bytes = sum(
        p.stat().st_size for p in out_dir.rglob("*") if p.is_file()
    )
    file_count = sum(1 for p in out_dir.rglob("*") if p.is_file())

    return FetchResult(
        name=f"commoncrawl-cdx:{opts.crawl_id}:{opts.archive_path}",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": url,
            "crawlId": opts.crawl_id,
            "archivePath": opts.archive_path,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "license": "commoncrawl-research-use",
            "tier": "C",
            "g13FleetInternalOnly": True,
            "piiSensitiveDefault": True,
            "attribution": (
                "Source: Common Crawl Foundation "
                "(https://commoncrawl.org/)"
            ),
            "acceptance": {
                "source": acceptance.source,
                "acceptedAt": acceptance.accepted_at,
                "acceptedByDid": acceptance.accepted_by_did,
                "upstreamTosUrl": acceptance.upstream_tos_url,
            },
        },
    )


__all__ = ["CommonCrawlCdxFetchOpts", "fetch"]
