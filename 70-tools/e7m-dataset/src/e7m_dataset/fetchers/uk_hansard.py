"""UK Hansard (Parliament debates) bulk fetcher.

Per ADR-2605263900 W1. Hansard is the official report of debates in
the UK Parliament (Commons + Lords). The Parliamentary Data Service
exposes bulk archives and an API:

  https://hansard-api.parliament.uk/                          (API root)
  https://hansard.parliament.uk/                              (HTML mirror)
  https://www.theyworkforyou.com/                              (third-party Hansard mirror, NOT used here)

License: OGL v3.0 (Open Parliament Licence — Crown copyright open
license, mirroring OGL v3.0). Tagged Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro /
FiscalNote / CQ Roll Call Pro SDKs. Per ADR-2605263900 §6 passive-only,
fetch is limited to date-bounded bulk archive download.

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in date-bounded debates + members + divisions API
paging + NDJSON sidecar emit for `GovParliamentSensor` (jurisdiction=
"GBR", legislature="uk-parliament").
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import httpx

from . import FetchResult

DEFAULT_API_BASE = "https://hansard-api.parliament.uk"


@dataclass
class UkHansardFetchOpts:
    api_base: str = DEFAULT_API_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    house: Literal["commons", "lords", "both"] = "both"
    date_from: Optional[str] = None  # ISO-8601 YYYY-MM-DD
    date_to: Optional[str] = None
    include_divisions: bool = True
    include_members: bool = True
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: UkHansardFetchOpts) -> FetchResult:
    """Stage UK Hansard debates into staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements date-bounded debates + members
    + divisions API paging + NDJSON sidecar for GovParliamentSensor.
    """
    raise NotImplementedError(
        "UK Hansard fetcher path-reserved at W0 per ADR-2605263900 §7. "
        "W1 implementation will land date-bounded debates + members + "
        "divisions API paging + NDJSON sidecar emit. Acceptance flag: "
        "NOT required (Tier-A OGL v3.0)."
    )


__all__ = [
    "DEFAULT_API_BASE",
    "UkHansardFetchOpts",
    "fetch",
]
