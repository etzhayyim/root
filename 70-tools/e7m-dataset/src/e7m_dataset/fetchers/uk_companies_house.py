"""UK Companies House Free Company Data Product bulk fetcher.

Per ADR-2605263800 W1. UK Companies House (registrar of UK companies)
publishes a Free Company Data Product as monthly + daily bulk archives:

  http://download.companieshouse.gov.uk/                  (monthly snapshots)
  http://download.companieshouse.gov.uk/en_output.html    (daily increments)
  https://data.gov.uk/dataset/companies-house-data        (catalog)

License: OGL v3.0 (Open Government Licence — Crown copyright open
license). Tagged Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
Bloomberg Terminal / Refinitiv / FactSet / Moody's Orbis / D&B /
Pitchbook / Crunchbase Pro SDKs. Per ADR-2605263800 §6 passive-only,
fetch is limited to the published bulk archives (monthly + daily
increment ZIPs) — no per-company live API queries at organism-tick
time. Companies House also publishes a streaming API + per-company REST
API; those are NOT used here.

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in monthly snapshot download + daily-increment
catch-up + NDJSON sidecar emit for `CorpRegistrySensor` (per company
profile) + `CorpDisclosureSensor` (annual confirmation statements /
accounts filings, if bundled with the FCD product).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult

DEFAULT_FCD_BASE = "http://download.companieshouse.gov.uk"
DEFAULT_MONTHLY_LISTING = f"{DEFAULT_FCD_BASE}/en_output.html"


@dataclass
class UkCompaniesHouseFetchOpts:
    fcd_base: str = DEFAULT_FCD_BASE
    monthly_listing_url: str = DEFAULT_MONTHLY_LISTING
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 600.0  # the monthly bulk file is large (~5 GB ZIP)
    # Specific snapshot to fetch; if None, latest is auto-discovered.
    snapshot: Optional[str] = None  # e.g. "BasicCompanyDataAsOneFile-2026-05-01.zip"
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: UkCompaniesHouseFetchOpts) -> FetchResult:
    """Stage UK Companies House FCD bulk archive into staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements monthly-snapshot listing parse
    + ZIP download + member CSV → NDJSON normalization for
    CorpRegistrySensor.
    """
    raise NotImplementedError(
        "UK Companies House fetcher path-reserved at W0 per "
        "ADR-2605263800 §7. W1 implementation will land monthly-listing "
        "scan + bulk ZIP download + CSV → NDJSON normalization. "
        "Acceptance flag: NOT required (Tier-A OGL v3.0). Daily-increment "
        "catch-up deferred to W2."
    )


__all__ = [
    "DEFAULT_FCD_BASE",
    "DEFAULT_MONTHLY_LISTING",
    "UkCompaniesHouseFetchOpts",
    "fetch",
]
