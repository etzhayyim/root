"""UK data.gov.uk CKAN catalog bulk fetcher.

Per ADR-2605263900 W1. data.gov.uk is the UK government's open-data
catalog (CKAN-based; ~70K dataset entries across UK central + local
government publishers). Bulk metadata published at:

  https://data.gov.uk/api/3/action/package_search   (CKAN package_search)
  https://data.gov.uk/api/3/action/package_list     (full ID listing)

License: OGL v3.0 (Open Government Licence — Crown copyright open
license); individual datasets may carry additional license tags
(license_id field). Tagged Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro /
FiscalNote / CQ Roll Call Pro SDKs. Per ADR-2605263900 §6 passive-only,
fetch is limited to CKAN bulk paging.

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in CKAN package_search paging + NDJSON sidecar emit
for `GovOpenDataSensor` (jurisdiction="GBR").
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult

DEFAULT_CKAN_BASE = "https://data.gov.uk/api/3/action"


@dataclass
class UkDataGovUkFetchOpts:
    ckan_base: str = DEFAULT_CKAN_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    page_size: int = 1000
    publisher_filter: Optional[str] = None  # e.g. "ministry-of-justice"
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: UkDataGovUkFetchOpts) -> FetchResult:
    """Stage UK data.gov.uk CKAN catalog into staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements CKAN package_search paging +
    per-dataset NDJSON sidecar for GovOpenDataSensor.
    """
    raise NotImplementedError(
        "UK data.gov.uk fetcher path-reserved at W0 per ADR-2605263900 "
        "§7. W1 implementation will land CKAN package_search paging + "
        "per-dataset NDJSON sidecar emit. Acceptance flag: NOT required "
        "(Tier-A OGL v3.0)."
    )


__all__ = [
    "DEFAULT_CKAN_BASE",
    "UkDataGovUkFetchOpts",
    "fetch",
]
