"""GLEIF LEI Concatenated Files (Level-1 + Level-2 + Relationship) fetcher.

Per ADR-2605263800 W1. The Global Legal Entity Identifier Foundation
(GLEIF) publishes daily Concatenated Data Files covering ~2.5M LEIs
plus their relationships:

  https://www.gleif.org/en/lei-data/gleif-concatenated-file
  https://leidata.gleif.org/api/v1/concatenated-files/lei2/             (L1)
  https://leidata.gleif.org/api/v1/concatenated-files/rr/               (L2-RR)
  https://leidata.gleif.org/api/v1/concatenated-files/repex/            (L2-RepEx)

License: CC0 1.0 (GLEIF publishes the LEI canonical data as public-
domain dedication). Tagged Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
Bloomberg Terminal / Refinitiv / FactSet / Moody's Orbis / D&B /
Pitchbook / Crunchbase Pro SDKs. Per ADR-2605263800 §6 passive-only,
fetch is limited to the published concatenated bulk files — no
per-LEI live lookups at organism-tick time.

LEI sensor is the canonical cross-jurisdiction key — other corp
sensors (CorpRegistrySensor, CorpDisclosureSensor) set their
`entity_lei` field by looking up the local registry ID against this
sensor's pin (ADR-2605263800 §3 LeiSensor Protocol).

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in the L1 + L2-RR + L2-RepEx XML/JSON downloads +
NDJSON sidecar emit for `LeiSensor`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import httpx

from . import FetchResult

DEFAULT_L1_API = "https://leidata.gleif.org/api/v1/concatenated-files/lei2/latest"
DEFAULT_L2_RR_API = "https://leidata.gleif.org/api/v1/concatenated-files/rr/latest"
DEFAULT_L2_REPEX_API = "https://leidata.gleif.org/api/v1/concatenated-files/repex/latest"


@dataclass
class GleifLeiFetchOpts:
    l1_url: str = DEFAULT_L1_API
    l2_rr_url: str = DEFAULT_L2_RR_API
    l2_repex_url: str = DEFAULT_L2_REPEX_API
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 900.0  # L1 file is large (~1 GB zipped XML)
    fmt: Literal["xml", "json", "csv"] = "json"
    fetch_l2: bool = True  # also fetch relationship records (L2-RR + L2-RepEx)
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: GleifLeiFetchOpts) -> FetchResult:
    """Stage GLEIF LEI Concatenated Files into staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements L1 + L2-RR + L2-RepEx download
    + canonical-LEI NDJSON sidecar emit + parent/ultimate-parent edge
    NDJSON sidecar for LeiSensor.
    """
    raise NotImplementedError(
        "GLEIF LEI fetcher path-reserved at W0 per ADR-2605263800 §7. "
        "W1 implementation will land L1 (entity) + L2-RR (relationship) "
        "+ L2-RepEx (reporting-exception) concatenated-file download + "
        "NDJSON sidecar emit. Acceptance flag: NOT required (Tier-A "
        "CC0 1.0)."
    )


__all__ = [
    "DEFAULT_L1_API",
    "DEFAULT_L2_REPEX_API",
    "DEFAULT_L2_RR_API",
    "GleifLeiFetchOpts",
    "fetch",
]
