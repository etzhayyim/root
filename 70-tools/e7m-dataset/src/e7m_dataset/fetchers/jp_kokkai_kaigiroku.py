"""JP 国会会議録検索 (National Diet meeting records) bulk fetcher.

Per ADR-2605263900 W1. 国会会議録検索 is the official searchable
archive of Japanese National Diet meeting records (both Houses, all
committees, since 1947). Bulk + per-meeting JSON API:

  https://kokkai.ndl.go.jp/api/                              (search + retrieval API)
  https://kokkai.ndl.go.jp/api/meeting                       (per-meeting full text)
  https://kokkai.ndl.go.jp/api/speech                        (per-speech segment)

License: 国会会議録 is published by the National Diet Library and is
treated as 公の著作物 — free use as official record per 著作権法 §13.
Tagged Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro /
FiscalNote / CQ Roll Call Pro SDKs. Per ADR-2605263900 §6 passive-only,
fetch is limited to date-bounded API paging respecting NDL's published
rate limits.

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in date-bounded meeting/speech API paging + NDJSON
sidecar emit for `GovParliamentSensor` (jurisdiction="JPN",
legislature="jp-kokkai").
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import httpx

from . import FetchResult

DEFAULT_API_BASE = "https://kokkai.ndl.go.jp/api"


@dataclass
class JpKokkaiKaigirokuFetchOpts:
    api_base: str = DEFAULT_API_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    granularity: Literal["meeting", "speech"] = "meeting"
    house: Literal["shugiin", "sangiin", "both"] = "both"
    date_from: Optional[str] = None  # ISO-8601 YYYY-MM-DD
    date_to: Optional[str] = None
    page_size: int = 100  # NDL API max per request
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: JpKokkaiKaigirokuFetchOpts) -> FetchResult:
    """Stage JP 国会会議録 into staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements date-bounded meeting/speech
    API paging + NDJSON sidecar for GovParliamentSensor.
    """
    raise NotImplementedError(
        "JP 国会会議録検索 fetcher path-reserved at W0 per "
        "ADR-2605263900 §7. W1 implementation will land date-bounded "
        "API paging + NDJSON sidecar emit. Acceptance flag: NOT required "
        "(Tier-A 国会会議録 public-record use per 著作権法 §13)."
    )


__all__ = [
    "DEFAULT_API_BASE",
    "JpKokkaiKaigirokuFetchOpts",
    "fetch",
]
