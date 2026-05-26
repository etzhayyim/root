"""World Bank Open Data API bulk fetcher.

Per ADR-2605263900 W1. The World Bank Open Data API publishes ~16K
indicators across 270+ economies (national + regional + IGO aggregates)
as JSON / XML via a paged REST API + downloadable bulk archives:

  https://api.worldbank.org/v2/                            (REST API root)
  https://api.worldbank.org/v2/indicator/                   (indicator catalog)
  https://api.worldbank.org/v2/country/                     (country list)
  https://datacatalog.worldbank.org/                        (catalog UI)

License: CC-BY 4.0 (World Bank Open Data Terms of Use). Tagged Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro /
FiscalNote / CQ Roll Call Pro SDKs. Per ADR-2605263900 §6 passive-only,
fetch is limited to per-indicator paged bulk download.

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in indicator catalog paging + per-indicator
all-economies-all-years bulk fetch + NDJSON sidecar emit for
`GovStatisticsSensor` (source="worldbank").
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import httpx

from . import FetchResult

DEFAULT_API_BASE = "https://api.worldbank.org/v2"


@dataclass
class WorldBankOpenDataFetchOpts:
    api_base: str = DEFAULT_API_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    fmt: Literal["json", "xml"] = "json"
    page_size: int = 1000
    indicators: tuple[str, ...] = ()  # empty = catalog only; otherwise per-indicator data
    countries: tuple[str, ...] = ("all",)  # "all" for full set; or ISO-3 codes
    date_range: Optional[str] = None  # e.g. "2000:2025"
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: WorldBankOpenDataFetchOpts) -> FetchResult:
    """Stage World Bank Open Data into staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements indicator catalog paging +
    per-indicator all-economies bulk fetch + NDJSON sidecar for
    GovStatisticsSensor.
    """
    raise NotImplementedError(
        "World Bank Open Data fetcher path-reserved at W0 per "
        "ADR-2605263900 §7. W1 implementation will land indicator "
        "catalog paging + per-indicator bulk fetch + NDJSON sidecar "
        "emit. Acceptance flag: NOT required (Tier-A CC-BY 4.0)."
    )


__all__ = [
    "DEFAULT_API_BASE",
    "WorldBankOpenDataFetchOpts",
    "fetch",
]
