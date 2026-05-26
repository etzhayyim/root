"""US data.gov CKAN catalog bulk fetcher.

Per ADR-2605263900 W1. data.gov is the US federal government's open-
data catalog (CKAN-based; ~250K dataset entries across federal
agencies). Bulk metadata published at:

  https://catalog.data.gov/api/3/action/package_search   (CKAN package_search)
  https://catalog.data.gov/api/3/action/package_list     (full ID listing)

License: public domain (US federal government works are not
copyrighted per 17 USC 105); individual datasets may carry additional
attribution requirements (license_id field). Tagged Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro /
FiscalNote / CQ Roll Call Pro SDKs or hostnames. Per ADR-2605263900 §6
passive-only, fetch is limited to CKAN bulk paging — no per-dataset
live page scraping at organism-tick time.

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in CKAN package_search paging + NDJSON sidecar emit
for `GovOpenDataSensor` (jurisdiction="USA").
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult

DEFAULT_CKAN_BASE = "https://catalog.data.gov/api/3/action"


@dataclass
class UsDataGovFetchOpts:
    ckan_base: str = DEFAULT_CKAN_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    page_size: int = 1000  # CKAN max per request
    organization_filter: Optional[str] = None  # e.g. "epa-gov" / "fda-hhs"
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: UsDataGovFetchOpts) -> FetchResult:
    """Stage US data.gov CKAN catalog into staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements CKAN package_search paging +
    per-dataset metadata NDJSON sidecar for GovOpenDataSensor.
    """
    raise NotImplementedError(
        "US data.gov fetcher path-reserved at W0 per ADR-2605263900 §7. "
        "W1 implementation will land CKAN package_search paging + "
        "per-dataset NDJSON sidecar emit. Acceptance flag: NOT required "
        "(Tier-A public domain)."
    )


__all__ = [
    "DEFAULT_CKAN_BASE",
    "UsDataGovFetchOpts",
    "fetch",
]
