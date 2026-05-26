"""JP 金融庁 EDINET XBRL bulk archive fetcher.

Per ADR-2605263800 W1. EDINET (Electronic Disclosure for Investors'
NETwork) is the JP 金融庁 (Financial Services Agency) public filings
repository for ~4K filers — 有価証券報告書 / 半期報告書 / 大量保有報告書 etc.

Bulk archives published at:

  https://disclosure.edinet-fsa.go.jp/api/v2/documents.json    (list API)
  https://disclosure.edinet-fsa.go.jp/api/v2/documents/<doc_id> (per-doc XBRL)

License: 金融庁 open-data utilization terms (free redistribution with
attribution; equivalent to CC-BY 4.0 for practical purposes). Tagged
Tier A.

Charter Rider §2 compatibility: this fetcher does NOT import or call
Bloomberg Terminal / Refinitiv / FactSet / Moody's Orbis / D&B /
Pitchbook / Crunchbase Pro SDKs. Per ADR-2605263800 §6 passive-only,
fetch is limited to date-bounded bulk-list paging + per-document XBRL
package downloads — no live 縦覧 page scraping.

W0 status: interface defined, stub raises NotImplementedError. W1
deliverable wires in date-bounded paging against the v2 documents API
+ per-document XBRL ZIP download + NDJSON sidecar emit for
`CorpRegistrySensor` (提出者) and `CorpDisclosureSensor` (有報 / 半期).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult

DEFAULT_DOCUMENTS_API = "https://disclosure.edinet-fsa.go.jp/api/v2/documents.json"
DEFAULT_DOCUMENT_DOWNLOAD = "https://disclosure.edinet-fsa.go.jp/api/v2/documents"


@dataclass
class JpEdinetFetchOpts:
    documents_api: str = DEFAULT_DOCUMENTS_API
    document_download_base: str = DEFAULT_DOCUMENT_DOWNLOAD
    api_key: Optional[str] = None  # EDINET v2 API key (free; per-DID)
    timeout_sec: float = 120.0
    date_from: Optional[str] = None  # ISO-8601 YYYY-MM-DD
    date_to: Optional[str] = None
    # form_type filter: "120" = 有報, "140" = 半期, "350" = 大量保有
    form_types: tuple[str, ...] = ("120", "140", "350")
    client: Optional[httpx.Client] = None
    write_ndjson: bool = True


def fetch(staging_dir: Path, opts: JpEdinetFetchOpts) -> FetchResult:
    """Stage JP EDINET XBRL bulk archive into staging directory.

    W0 (this commit): interface defined; raises NotImplementedError.
    W1 (next commit chain): implements date-bounded list paging +
    per-document XBRL ZIP download + NDJSON sidecar for
    CorpRegistrySensor + CorpDisclosureSensor.
    """
    raise NotImplementedError(
        "JP EDINET fetcher path-reserved at W0 per ADR-2605263800 §7. "
        "W1 implementation will land date-bounded v2 documents API "
        "paging + per-document XBRL download + NDJSON shard emit. "
        "EDINET v2 API requires a free per-DID API key — supply via "
        "JpEdinetFetchOpts.api_key. Acceptance flag: NOT required "
        "(Tier-A 金融庁 open-data terms)."
    )


__all__ = [
    "DEFAULT_DOCUMENTS_API",
    "DEFAULT_DOCUMENT_DOWNLOAD",
    "JpEdinetFetchOpts",
    "fetch",
]
