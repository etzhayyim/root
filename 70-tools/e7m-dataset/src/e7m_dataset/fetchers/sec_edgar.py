"""SEC EDGAR companyfacts + Submissions bulk archive fetcher.

Per ADR-2605263800 W1. SEC EDGAR is the US Securities and Exchange
Commission's public filings repository for ~10K public-traded companies
and registered filers. Bulk archives published at:

  https://www.sec.gov/Archives/edgar/data/                (filing artifacts)
  https://data.sec.gov/submissions/CIK<10-digit>.json     (per-CIK submissions)
  https://www.sec.gov/Archives/edgar/full-index/          (quarterly indexes)

License: public domain (17 CFR 200; US government works are not
copyrighted). Tagged Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
Bloomberg Terminal / S&P Capital IQ / Refinitiv Eikon / FactSet /
Moody's Orbis / D&B Hoovers / Pitchbook / Crunchbase Pro SDKs or
hostnames. Per ADR-2605263800 §6 passive-only invariant, fetch is
limited to pre-published bulk archives — no per-company live API
queries at organism-tick time. SEC's request rate guidance (10 req/s
with User-Agent identification) is respected.

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in the actual httpx GET against the bulk archive
endpoint, parses the per-CIK Submissions JSON, and stages NDJSON
sidecars suitable for the `CorpRegistrySensor` /
`CorpDisclosureSensor` / `CorpFilingEventSensor` Protocols
(ADR-2605263800 §3).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult

DEFAULT_USER_AGENT = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
DEFAULT_SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
DEFAULT_FULL_INDEX_BASE = "https://www.sec.gov/Archives/edgar/full-index"


@dataclass
class SecEdgarFetchOpts:
    submissions_base: str = DEFAULT_SUBMISSIONS_BASE
    full_index_base: str = DEFAULT_FULL_INDEX_BASE
    user_agent: str = DEFAULT_USER_AGENT
    timeout_sec: float = 120.0
    # Per ADR-2605263800 N2 + ADR-2605262400 §7 passive-only: caller MUST
    # NOT enumerate the full CIK space at fetch time. Either supply a
    # bounded CIK list, or set `quarter_index_only=True` to download just
    # the SEC-published quarterly index (a single bulk archive that lists
    # every filing accepted in that quarter).
    quarter: Optional[str] = None  # e.g. "2026/QTR1"
    quarter_index_only: bool = True
    cik_allowlist: tuple[str, ...] = ()
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: SecEdgarFetchOpts) -> FetchResult:
    """Stage SEC EDGAR bulk archive into the staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements quarterly-index download +
    optional per-CIK Submissions JSON paging + NDJSON sidecar emit.
    """
    raise NotImplementedError(
        "SEC EDGAR fetcher path-reserved at W0 per ADR-2605263800 §7. "
        "W1 implementation will land quarterly-index bulk download + "
        "optional CIK-allowlist Submissions JSON paging + NDJSON shard "
        "emit for CorpRegistrySensor / CorpDisclosureSensor / "
        "CorpFilingEventSensor. Acceptance flag: NOT required (Tier-A "
        "public-domain). Charter Rider §2 deny-list (Bloomberg Terminal "
        "et al.) MUST be enforced at W1 lint integration."
    )


__all__ = [
    "DEFAULT_FULL_INDEX_BASE",
    "DEFAULT_SUBMISSIONS_BASE",
    "DEFAULT_USER_AGENT",
    "SecEdgarFetchOpts",
    "fetch",
]
