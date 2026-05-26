"""US Congress.gov bulk + GovInfo bulk fetcher.

Per ADR-2605263900 W1. Congress.gov publishes bulk data for federal
bills, roll-call votes, member info, Congressional Record, and treaty
documents — primary sources are Congress.gov Bulk Data Repository
(govinfo.gov mirrored):

  https://www.congress.gov/help/using-data-offsite           (overview)
  https://www.govinfo.gov/bulkdata                            (bulk repository)
  https://api.congress.gov/v3/                                (paginated API)

License: public domain (US federal government works are not
copyrighted per 17 USC 105). Tagged Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro /
FiscalNote / CQ Roll Call Pro SDKs. Per ADR-2605263900 §6 passive-only,
fetch is limited to bulk-data downloads + paginated API for catch-up.

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in govinfo bulk-data sync (BILLS / BILLSTATUS /
CREC / FR / CHRG collections) + NDJSON sidecar emit for
`GovParliamentSensor` (jurisdiction="USA", legislature="us-congress").
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult

DEFAULT_BULK_BASE = "https://www.govinfo.gov/bulkdata"
DEFAULT_API_BASE = "https://api.congress.gov/v3"


@dataclass
class UsCongressGovFetchOpts:
    bulk_base: str = DEFAULT_BULK_BASE
    api_base: str = DEFAULT_API_BASE
    api_key: Optional[str] = None  # api.congress.gov v3 key (free per-DID)
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 300.0
    collections: tuple[str, ...] = (
        "BILLS",       # bill text
        "BILLSTATUS",  # bill status XML
        "CREC",        # Congressional Record
        "FR",          # Federal Register
    )
    congress: Optional[int] = None  # e.g. 119; None = latest
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: UsCongressGovFetchOpts) -> FetchResult:
    """Stage US Congress.gov bulk archive into staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements govinfo bulk-data sync for
    listed collections + per-collection NDJSON normalization for
    GovParliamentSensor.
    """
    raise NotImplementedError(
        "US Congress.gov fetcher path-reserved at W0 per ADR-2605263900 "
        "§7. W1 implementation will land govinfo bulkdata directory "
        "sync (BILLS / BILLSTATUS / CREC / FR) + NDJSON sidecar emit. "
        "Acceptance flag: NOT required (Tier-A public domain). "
        "api.congress.gov v3 key (free per-DID) only required for "
        "catch-up paging beyond the bulkdata snapshot."
    )


__all__ = [
    "DEFAULT_API_BASE",
    "DEFAULT_BULK_BASE",
    "UsCongressGovFetchOpts",
    "fetch",
]
