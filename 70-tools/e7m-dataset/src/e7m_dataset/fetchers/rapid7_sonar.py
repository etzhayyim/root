"""Rapid7 Open Data — Sonar FDNS archive fetcher.

Per ADR-2605262400 W3. Rapid7's Project Sonar publishes globally
collected forward-DNS scan archives (FDNS) under research-use terms.
The archives are large (~200 GB / month at peak) and are TIER C — they
admit acceptance-flag-gated ingest under the G13 fleet-internal
carve-out, with `-nc-` infix mandatory on derived artifacts and
PostSink/JudahLiteLLM/SBT-gate as the only viable serving path.

License/TOS: research-use (per Rapid7 Open Data acceptance terms).
NOT Apache/CC0/CC-BY publishable — Tier C, internal-only.

Acceptance flag (mandatory, ADR-2605262400 W3):

  ~/.etzhayyim/source-acceptance/rapid7-open-data.toml

with at least:

  [acceptance]
  source           = "rapid7-open-data"
  accepted_at      = "<RFC3339>"
  accepted_by_did  = "did:web:..."
  upstream_tos_url = "https://opendata.rapid7.com/about/"

PII-sensitivity: TRUE by default — Sonar TXT records routinely contain
user email artifacts (e.g. ACME / SPF / DKIM contacts that bleed
operator contact info into TXT). The redacted view (via
``kotodama.organism.sensors.pii_filter.redact_text``) is what the
sensor + corpus assembler MUST consume; original bytes stay in the
annex.

The fetcher does NOT mirror the entire monthly archive — it pulls a
single named file (e.g. ``fdns_any.json.gz``) per invocation. The
operator chains multiple invocations (per archive shard) and DataLad
groups them.
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


_DEFAULT_BASE = "https://opendata.rapid7.com/sonar.fdns_v2"


@dataclass
class Rapid7SonarFetchOpts:
    # File name within the upstream archive (e.g. "2026-05-23-fdns_any.json.gz").
    archive_file: str = ""
    base_url: str = _DEFAULT_BASE
    timeout_sec: float = 1800.0  # Sonar files run several GB
    client: Optional[httpx.Client] = None
    # Source slug used for the acceptance flag lookup. Overridable for
    # tests; production callers should leave the default.
    acceptance_source: str = "rapid7-open-data"


def fetch(staging_dir: Path, opts: Rapid7SonarFetchOpts) -> FetchResult:
    if not opts.archive_file:
        raise ValueError(
            "Rapid7SonarFetchOpts.archive_file is required "
            "(e.g. '2026-05-23-fdns_any.json.gz')."
        )

    # G13 acceptance gate — runs BEFORE any HTTP request is issued.
    acceptance = require_acceptance(opts.acceptance_source)

    url = f"{opts.base_url}/{opts.archive_file}"
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dirname = f"rapid7-sonar-{opts.archive_file.replace('/', '_')}-{capture_ts}"
    out_dir = staging_dir / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    archive_path = out_dir / opts.archive_file.rsplit("/", 1)[-1]

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
        name=f"rapid7-sonar-fdns:{opts.archive_file}",
        revision=revision,
        staging_path=out_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            "type": "http",
            "url": url,
            "archiveFile": opts.archive_file,
            "capturedAt": capture_ts,
            "rawSha256": raw_sha,
            "license": "rapid7-research-use",
            "tier": "C",
            "g13FleetInternalOnly": True,
            "piiSensitiveDefault": True,
            "acceptance": {
                "source": acceptance.source,
                "acceptedAt": acceptance.accepted_at,
                "acceptedByDid": acceptance.accepted_by_did,
                "upstreamTosUrl": acceptance.upstream_tos_url,
            },
        },
    )


__all__ = ["Rapid7SonarFetchOpts", "fetch"]
