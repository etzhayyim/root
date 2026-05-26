"""JP data.go.jp + e-Stat CKAN/API bulk fetcher.

Per ADR-2605263900 W1. data.go.jp is Japan's central open-data catalog
(CKAN-based; ~30K entries), and e-Stat is 政府統計の総合窓口
(Government Statistics Window) — the canonical JP statistics API
covering ~600 surveys from all ministries.

  https://www.data.go.jp/data/api/3/action/package_search   (CKAN)
  https://www.e-stat.go.jp/api/                              (statistics API)

License: CC-BY 4.0 (政府標準利用規約 2.0 — JP government standard data-
utilization terms, aligned with CC-BY 4.0). Tagged Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro /
FiscalNote / CQ Roll Call Pro SDKs. Per ADR-2605263900 §6 passive-only,
fetch is limited to CKAN bulk paging + e-Stat published bulk APIs.

The e-Stat API requires a free per-DID API key (appId) — supply via
JpDataGoJpFetchOpts.estat_app_id.

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in data.go.jp CKAN paging + e-Stat statsList API +
per-survey statsData bulk + NDJSON sidecar emit for `GovOpenDataSensor`
(jurisdiction="JPN") + `GovStatisticsSensor` (source="e-stat").
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult

DEFAULT_DATA_GO_JP_CKAN = "https://www.data.go.jp/data/api/3/action"
DEFAULT_ESTAT_API = "https://api.e-stat.go.jp/rest/3.0/app/json"


@dataclass
class JpDataGoJpFetchOpts:
    data_go_jp_ckan: str = DEFAULT_DATA_GO_JP_CKAN
    estat_api: str = DEFAULT_ESTAT_API
    estat_app_id: Optional[str] = None  # required for e-Stat statsList / statsData
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    page_size: int = 1000
    fetch_estat: bool = True  # also fetch e-Stat statsList; False = data.go.jp only
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: JpDataGoJpFetchOpts) -> FetchResult:
    """Stage JP data.go.jp + e-Stat catalog into staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements data.go.jp CKAN paging +
    e-Stat statsList API paging + per-survey bulk + NDJSON sidecar.
    """
    raise NotImplementedError(
        "JP data.go.jp + e-Stat fetcher path-reserved at W0 per "
        "ADR-2605263900 §7. W1 implementation will land CKAN paging + "
        "e-Stat statsList paging + NDJSON sidecar emit. Acceptance flag: "
        "NOT required (Tier-A CC-BY 4.0); e-Stat appId required (free "
        "per-DID; supply via JpDataGoJpFetchOpts.estat_app_id)."
    )


__all__ = [
    "DEFAULT_DATA_GO_JP_CKAN",
    "DEFAULT_ESTAT_API",
    "JpDataGoJpFetchOpts",
    "fetch",
]
