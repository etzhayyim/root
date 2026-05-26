"""EU Eurostat SDMX bulk fetcher.

Per ADR-2605263900 W1. Eurostat is the statistical office of the
European Union; the Statistics API publishes ~10K indicators across
EU-27 + EEA + candidate countries as SDMX (Statistical Data and
Metadata eXchange):

  https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/<flow>/
  https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/dataflow/
  https://ec.europa.eu/eurostat/data/bulkdownload                       (bulk archives)

License: Eurostat free re-use (Decision 2011/833/EU — Commission's open
data policy). Tagged Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro /
FiscalNote / CQ Roll Call Pro SDKs. Per ADR-2605263900 §6 passive-only,
fetch is limited to per-flow bulk SDMX download (no per-indicator live
API queries at organism-tick time).

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in dataflow listing → per-flow SDMX bulk download +
NDJSON sidecar emit for `GovStatisticsSensor` (source="eurostat").
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import httpx

from . import FetchResult

DEFAULT_SDMX_BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1"
DEFAULT_BULK_BASE = "https://ec.europa.eu/eurostat/data/bulkdownload"


@dataclass
class EuEurostatFetchOpts:
    sdmx_base: str = DEFAULT_SDMX_BASE
    bulk_base: str = DEFAULT_BULK_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 300.0
    fmt: Literal["sdmx-2.1", "sdmx-csv", "tsv"] = "sdmx-2.1"
    dataflows: tuple[str, ...] = ()  # empty = fetch dataflow catalog only
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: EuEurostatFetchOpts) -> FetchResult:
    """Stage Eurostat SDMX bulk archive into staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements dataflow listing → per-flow
    SDMX bulk download + NDJSON sidecar for GovStatisticsSensor.
    """
    raise NotImplementedError(
        "Eurostat fetcher path-reserved at W0 per ADR-2605263900 §7. "
        "W1 implementation will land dataflow listing + per-flow SDMX "
        "bulk download + NDJSON sidecar emit. Acceptance flag: NOT "
        "required (Tier-A Eurostat free re-use per Decision 2011/833)."
    )


__all__ = [
    "DEFAULT_BULK_BASE",
    "DEFAULT_SDMX_BASE",
    "EuEurostatFetchOpts",
    "fetch",
]
