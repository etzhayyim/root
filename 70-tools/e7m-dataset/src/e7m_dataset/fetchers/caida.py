"""CAIDA dataset fetcher (AS-rank / prefix2as / AS-relationship).

Per ADR-2605262400 W3. CAIDA (https://www.caida.org/) publishes several
research-grade AS-graph datasets:

  - **AS-rank** — per-AS rank + customer cone size, monthly.
  - **prefix2as** — RouteViews-derived IPv4/IPv6 prefix → origin AS
    mapping, daily.
  - **AS-relationship** — c2p / p2p classification of AS pairs.

License/TOS: CC-BY-NC 4.0 (per CAIDA Data Sharing Agreement). Tier C,
internal-only under the G13 fleet-internal carve-out.

Acceptance flag (mandatory):

  ~/.etzhayyim/source-acceptance/caida.toml

PII-sensitivity: FALSE by default — these are pure graph / inference
datasets (no per-user content). Operators MAY enable pii_filter at the
sensor layer for defense-in-depth.

Wave-3 fetches a single named archive (e.g. ``20260501.as-rel.txt.bz2``)
per invocation. Multi-dataset assembly is done via the corpus assembler.
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


_DEFAULT_BASE = "https://publicdata.caida.org"

KNOWN_DATASETS = ("as-rank", "prefix2as", "as-relationship")


@dataclass
class CaidaFetchOpts:
    dataset: str = "as-relationship"
    # Path relative to the dataset root, e.g.
    # "as-relationships/serial-1/20260501.as-rel.txt.bz2".
    archive_path: str = ""
    base_url: str = _DEFAULT_BASE
    timeout_sec: float = 1200.0
    client: Optional[httpx.Client] = None
    acceptance_source: str = "caida"


def fetch(staging_dir: Path, opts: CaidaFetchOpts) -> FetchResult:
    if opts.dataset not in KNOWN_DATASETS:
        raise ValueError(
            f"unknown CAIDA dataset '{opts.dataset}'. Known: {KNOWN_DATASETS}"
        )
    if not opts.archive_path:
        raise ValueError(
            "CaidaFetchOpts.archive_path is required "
            "(e.g. 'as-relationships/serial-1/20260501.as-rel.txt.bz2')."
        )

    acceptance = require_acceptance(opts.acceptance_source)

    url = f"{opts.base_url}/{opts.archive_path}"
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    archive_slug = opts.archive_path.replace("/", "_")
    dirname = f"caida-{opts.dataset}-{archive_slug}-{capture_ts}"
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
        name=f"caida:{opts.dataset}:{opts.archive_path}",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": url,
            "dataset": opts.dataset,
            "archivePath": opts.archive_path,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "license": "CC-BY-NC-4.0",
            "tier": "C",
            "g13FleetInternalOnly": True,
            "piiSensitiveDefault": False,
            "attribution": (
                "Source: CAIDA — Center for Applied Internet Data Analysis "
                "(https://www.caida.org/)"
            ),
            "acceptance": {
                "source": acceptance.source,
                "acceptedAt": acceptance.accepted_at,
                "acceptedByDid": acceptance.accepted_by_did,
                "upstreamTosUrl": acceptance.upstream_tos_url,
            },
        },
    )


__all__ = ["CaidaFetchOpts", "KNOWN_DATASETS", "fetch"]
