"""Japan e-Gov 法令 API fetcher — W1 anchor (ADR-2605262800).

e-Gov 法令検索 publishes the consolidated text of Japanese statutes (法律 /
政令 / 府省令 / 規則) under **CC-BY 4.0** (法令データ提供システム利用規約). No API
key required. This fetcher targets the v2 JSON law-list endpoint:

  https://laws.e-gov.go.jp/api/2/laws?limit=N&offset=M

Tolerant of the v2 response shape (law_info / revision_info nesting) and the
older flat spellings, so an operator can stage either via ``local_source``:

  {"laws": [
     {"law_info":      {"law_id": "412AC0000000086", "law_type": "Act",
                        "law_num": "平成十五年法律第五十七号",
                        "promulgation_date": "2003-05-30"},
      "revision_info": {"law_title": "個人情報の保護に関する法律",
                        "law_revision_id": "412AC0000000086_20240401_505AC0000000047",
                        "amendment_promulgate_date": "2023-06-07"}},
     ...],
   "total_count": 9123}

→ normalized statute NDJSON (see ``legal._common`` for the shape). Bucket:
``law/statutes/jp-egov/<rev>/``. Sensor: ``legal_statute_sensor`` (jurisdiction JP).

Passive-only (ADR-2605262400 §7): operator-triggered; network mode bounds the
harvest with ``max_records`` (no implicit full-corpus scrape per tick).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

from .. import FetchResult
from . import _common

# httpx is imported lazily inside the network path so local-source mode (and
# tests) need no network dependency.

DEFAULT_API_BASE = "https://laws.e-gov.go.jp/api/2"
LAW_VIEW_BASE = "https://laws.e-gov.go.jp/law"
LICENSE_ID = "CC-BY-4.0"
TIER = "A"

# e-Gov law_type → normalized lawType.
_LAW_TYPE = {
    "constitution": "constitution",
    "act": "act",
    "cabinetorder": "cabinet-order",
    "imperialordinance": "imperial-ordinance",
    "ministerialordinance": "ministerial-ordinance",
    "rule": "rule",
    "misc": "misc",
}


@dataclass
class JpEgovFetchOpts:
    api_base: str = DEFAULT_API_BASE
    user_agent: str = "etzhayyim/root e7m-dataset (jun@etzhayyim.com)"
    timeout_sec: float = 120.0
    local_source: Optional[Path] = None
    page_size: int = 100
    max_records: Optional[int] = None
    client: Optional[Any] = None  # httpx.Client (lazy)


def _flat(rec: dict, *keys: str) -> Any:
    """Look a key up in the record and in its law_info / revision_info children."""
    for scope in (rec, rec.get("law_info") or {}, rec.get("revision_info") or {}):
        if not isinstance(scope, dict):
            continue
        for k in keys:
            if scope.get(k) not in (None, ""):
                return scope[k]
    return None


def _normalize(rec: dict) -> Optional[dict]:
    law_id = _flat(rec, "law_id", "lawId", "LawId")
    if not law_id:
        return None
    law_id = str(law_id)
    raw_type = str(_flat(rec, "law_type", "lawType") or "").replace("_", "").replace("-", "").lower()
    revision = _flat(rec, "law_revision_id", "lawRevisionId", "revision") or _flat(
        rec, "amendment_promulgate_date"
    )
    return {
        "recordId": f"JP:{law_id}",
        "jurisdiction": "JP",
        "lawId": law_id,
        "title": _flat(rec, "law_title", "lawTitle", "LawTitle", "title"),
        "lawType": _LAW_TYPE.get(raw_type, "act"),
        "lawNum": _flat(rec, "law_num", "lawNum"),
        "promulgatedDate": _common.coerce_iso_date(_flat(rec, "promulgation_date", "promulgationDate")),
        "effectiveDate": None,
        "revision": str(revision) if revision else None,
        "lang": "ja",
        "license": LICENSE_ID,
        "sourceUrl": f"{LAW_VIEW_BASE}/{law_id}",
        "payloadCid": f"{LAW_VIEW_BASE}/{law_id}",
        "bodyExcerpt": None,
    }


def _network_iter(opts: JpEgovFetchOpts, owned: bool, client: Any) -> Iterator[dict]:
    cap = opts.max_records
    emitted = 0
    offset = 0
    try:
        while True:
            url = f"{opts.api_base}/laws?limit={opts.page_size}&offset={offset}"
            resp = client.get(url)
            resp.raise_for_status()
            payload = resp.json()
            laws = payload.get("laws") if isinstance(payload, dict) else payload
            if not isinstance(laws, list) or not laws:
                break
            for rec in laws:
                if not isinstance(rec, dict):
                    continue
                row = _normalize(rec)
                if row is None:
                    continue
                yield row
                emitted += 1
                if cap is not None and emitted >= cap:
                    return
            total = payload.get("total_count") if isinstance(payload, dict) else None
            offset += opts.page_size
            if isinstance(total, int) and offset >= total:
                break
    finally:
        if owned:
            client.close()


def fetch(staging_dir: Path, opts: JpEgovFetchOpts) -> FetchResult:
    if opts.local_source is not None:
        rows = _common.iter_local_source(Path(opts.local_source), _normalize)
        meta = {"url": str(opts.local_source), "jurisdiction": "JP", "bucket": "statutes/jp-egov"}
    else:
        if opts.max_records is None:
            raise ValueError(
                "JpEgovFetchOpts.max_records must be set in network mode "
                "(passive-only: no implicit full-corpus scrape per ADR-2605262400 §7)."
            )
        import httpx

        owned = opts.client is None
        client = opts.client or httpx.Client(
            timeout=opts.timeout_sec, follow_redirects=True,
            headers={"User-Agent": opts.user_agent},
        )
        rows = _network_iter(opts, owned, client)
        meta = {"url": f"{opts.api_base}/laws", "jurisdiction": "JP", "bucket": "statutes/jp-egov"}

    return _common.write_run(
        staging_dir=staging_dir, name="jp-egov", rows=rows, source_meta=meta,
        license_id=LICENSE_ID, tier=TIER, max_records=opts.max_records,
        local_source=opts.local_source,
    )


__all__ = ["DEFAULT_API_BASE", "JpEgovFetchOpts", "fetch"]
