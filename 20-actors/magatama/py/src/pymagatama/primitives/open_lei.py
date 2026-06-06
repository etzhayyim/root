from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

LOG = logging.getLogger("open_lei")


# Bulk paginated API for Level 2 (distinct from per-entity endpoint)
GLEIF_RR_CDF_BULK_API = "https://api.gleif.org/api/v1/relationship-records"

GLEIF_DATASETS: dict[str, dict[str, Any]] = {
    "lei-cdf": {
        "label": "GLEIF Level 1 LEI-CDF",
        "question": "who-is-who",
        "format": "LEI-CDF v3.1",
        "targetTables": ["vertex_open_lei_entity", "vertex_open_lei_gleif_file"],
        "downloadPage": "https://www.gleif.org/en/lei-data/gleif-concatenated-file/download-the-concatenated-file",
        "apiEndpoint": "https://api.gleif.org/api/v1/lei-records",
    },
    "rr-cdf": {
        "label": "GLEIF Level 2 Relationship Record CDF",
        "question": "who-owns-whom",
        "format": "RR-CDF v2.1",
        "targetTables": ["vertex_open_lei_ownership", "edge_open_lei_ownership_pair", "vertex_open_lei_gleif_file"],
        "downloadPage": "https://www.gleif.org/en/lei-data/gleif-concatenated-file/download-the-concatenated-file",
        "apiEndpoint": "https://api.gleif.org/api/v1/lei-records/{lei}/direct-parent",
    },
    "reporting-exception": {
        "label": "GLEIF Level 2 Reporting Exceptions",
        "question": "why-parent-not-reported",
        "format": "Reporting Exceptions v2.1",
        "targetTables": ["vertex_open_lei_reporting_exception", "vertex_open_lei_gleif_file"],
        "downloadPage": "https://www.gleif.org/en/lei-data/gleif-concatenated-file/download-the-concatenated-file",
        "apiEndpoint": "https://api.gleif.org/api/v1/lei-records/{lei}/direct-parent-reporting-exception",
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _str_list(value: Any) -> list[str]:
    return [str(item) for item in _as_list(value) if item]


def gleif_manifest_plan(*, as_of_date: str | None = None, datasets: Any = None, mode: str = "delta") -> dict[str, Any]:
    selected = _str_list(datasets) or ["lei-cdf", "rr-cdf", "reporting-exception"]
    dataset_plans = [
        {
            "datasetKind": key,
            **GLEIF_DATASETS[key],
            "mode": mode if mode in {"delta", "backfill", "repair", "verify"} else "delta",
            "partitionKey": f"{key}:{as_of_date or _utc_now()[:10]}",
        }
        for key in selected
        if key in GLEIF_DATASETS
    ]
    return {
        "openLeiGleifManifestPlan": {
            "manifestId": f"gleif-manifest-{as_of_date or _utc_now()[:10]}",
            "asOfDate": as_of_date or _utc_now()[:10],
            "mode": mode if mode in {"delta", "backfill", "repair", "verify"} else "delta",
            "datasets": dataset_plans,
            "terms": [
                "use official GLEIF public LEI data source",
                "store raw files by content hash before normalization",
                "keep Level 1 entity, Level 2 relationship, and reporting-exception streams separate",
            ],
        }
    }


def _fetch_rr_cdf_page(*, page_number: int, page_size: int) -> tuple[list[dict[str, Any]], str, int]:
    base = os.environ.get("GLEIF_RR_API_BASE", GLEIF_RR_CDF_BULK_API).strip()
    query = urlencode({"page[number]": page_number, "page[size]": page_size})
    url = f"{base}?{query}"
    req = Request(
        url,
        headers={
            "Accept": "application/vnd.api+json, application/json",
            "User-Agent": os.environ.get("GLEIF_USER_AGENT", "etzhayyim-open-lei-zeebe/0.1"),
        },
    )
    with urlopen(req, timeout=int(os.environ.get("GLEIF_FETCH_TIMEOUT_SEC", "90"))) as res:
        body = res.read()
    payload = json.loads(body.decode("utf-8"))
    records = payload.get("data") if isinstance(payload.get("data"), list) else []
    return (
        [record for record in records if isinstance(record, dict)],
        hashlib.sha256(body).hexdigest(),
        len(body),
    )


def _fetch_lei_cdf_page(*, page_number: int, page_size: int) -> tuple[list[dict[str, Any]], str, int]:
    base = os.environ.get("GLEIF_API_BASE", GLEIF_DATASETS["lei-cdf"]["apiEndpoint"]).strip()
    query = urlencode({"page[number]": page_number, "page[size]": page_size})
    url = f"{base}?{query}"
    req = Request(
        url,
        headers={
            "Accept": "application/vnd.api+json, application/json",
            "User-Agent": os.environ.get("GLEIF_USER_AGENT", "etzhayyim-open-lei-zeebe/0.1"),
        },
    )
    with urlopen(req, timeout=int(os.environ.get("GLEIF_FETCH_TIMEOUT_SEC", "90"))) as res:
        body = res.read()
    payload = json.loads(body.decode("utf-8"))
    records = payload.get("data") if isinstance(payload.get("data"), list) else []
    return (
        [record for record in records if isinstance(record, dict)],
        hashlib.sha256(body).hexdigest(),
        len(body),
    )


def gleif_bulk_collect(
    *,
    dataset_kind: str = "lei-cdf",
    as_of_date: str | None = None,
    shard: int = 0,
    shard_count: int = 1,
    limit: int | None = None,
    page_size: int = 200,
    fetch: bool = False,
) -> dict[str, Any]:
    dataset = GLEIF_DATASETS.get(dataset_kind, GLEIF_DATASETS["lei-cdf"])
    shard_no = max(0, int(shard))
    as_of = as_of_date or _utc_now()[:10]
    out = {
        "openLeiGleifBulkCollect": {
            "collectionId": f"gleif-{dataset_kind}-{as_of}-{shard_no}",
            "datasetKind": dataset_kind,
            "asOfDate": as_of,
            "shard": shard_no,
            "shardCount": max(1, int(shard_count)),
            "limit": limit if isinstance(limit, int) and limit > 0 else None,
            "source": {
                "downloadPage": dataset["downloadPage"],
                "apiEndpoint": dataset["apiEndpoint"],
                "format": dataset["format"],
            },
            "targetTables": dataset["targetTables"],
            "rawBlobPrefix": f"open-lei/gleif/{dataset_kind}/{as_of}/",
            "nextTask": "openLei.gleif.record.normalize",
        }
    }
    body = out["openLeiGleifBulkCollect"]
    if not fetch:
        body["fetchMode"] = "plan"
        return out

    page = shard_no + 1
    bounded_page_size = max(1, min(int(page_size or 200), 200))

    if dataset_kind == "rr-cdf":
        records, sha256, byte_size = _fetch_rr_cdf_page(page_number=page, page_size=bounded_page_size)
        if isinstance(limit, int) and limit > 0:
            records = records[:limit]
        body.update({
            "fetchMode": "api-page",
            "pageNumber": page,
            "pageSize": bounded_page_size,
            "records": records,
            "sourceCount": len(records),
            "sha256": sha256,
            "byteSize": byte_size,
            "fetchedAt": _utc_now(),
        })
        return out

    if dataset_kind not in ("lei-cdf",):
        body["fetchMode"] = "unsupported"
        body["fetchSupported"] = False
        body["records"] = []
        body["sourceCount"] = 0
        return out

    records, sha256, byte_size = _fetch_lei_cdf_page(page_number=page, page_size=bounded_page_size)
    if isinstance(limit, int) and limit > 0:
        records = records[:limit]
    body.update(
        {
            "fetchMode": "api-page",
            "pageNumber": page,
            "pageSize": bounded_page_size,
            "records": records,
            "sourceCount": len(records),
            "sha256": sha256,
            "byteSize": byte_size,
            "fetchedAt": _utc_now(),
        }
    )
    return out


def normalize_lei_record(record: dict[str, Any]) -> dict[str, Any]:
    attributes = record.get("attributes") if isinstance(record.get("attributes"), dict) else record
    entity = attributes.get("entity") if isinstance(attributes.get("entity"), dict) else {}
    registration = attributes.get("registration") if isinstance(attributes.get("registration"), dict) else {}
    legal_name = entity.get("legalName")
    if isinstance(legal_name, dict):
        legal_name = legal_name.get("name")
    legal_address = entity.get("legalAddress") if isinstance(entity.get("legalAddress"), dict) else {}
    return {
        "vertex_id": f"at://did:web:open-lei.etzhayyim.com/com.etzhayyim.apps.openLei.entity/{attributes.get('lei') or record.get('id')}",
        "lei": attributes.get("lei") or record.get("id"),
        "legal_name": legal_name or attributes.get("legalName"),
        "country": legal_address.get("country") or entity.get("legalJurisdiction"),
        "legal_form": (entity.get("legalForm") or {}).get("id") if isinstance(entity.get("legalForm"), dict) else entity.get("legalForm"),
        "registration_authority": (entity.get("registeredAt") or {}).get("id") if isinstance(entity.get("registeredAt"), dict) else entity.get("registeredAt"),
        "registration_status": registration.get("status") or attributes.get("registrationStatus") or "UNKNOWN",
        "issued_at": registration.get("initialRegistrationDate") or attributes.get("issuedAt"),
        "next_renewal_at": registration.get("nextRenewalDate") or attributes.get("nextRenewalAt"),
        "status": "active" if (registration.get("status") or attributes.get("registrationStatus")) == "ISSUED" else "lapsed",
        "created_at": _utc_now(),
        "owner_did": "did:web:open-lei.etzhayyim.com",
        "sensitivity_ord": 1,
        "org_id": "did:web:open-lei.etzhayyim.com",
        "user_id": "did:web:open-lei.etzhayyim.com",
        "actor_id": "sys.langserver.open-lei.gleif",
    }


def gleif_record_normalize(*, dataset_kind: str = "lei-cdf", records: Any = None, as_of_date: str | None = None) -> dict[str, Any]:
    raw_records = [item for item in _as_list(records) if isinstance(item, dict)]
    entity_rows = [normalize_lei_record(record) for record in raw_records if dataset_kind == "lei-cdf"]
    return {
        "openLeiGleifRecordNormalize": {
            "normalizationId": f"gleif-normalize-{dataset_kind}-{as_of_date or _utc_now()[:10]}",
            "datasetKind": dataset_kind,
            "asOfDate": as_of_date or _utc_now()[:10],
            "recordsRead": len(raw_records),
            "entityRows": entity_rows,
            "ownershipRows": [] if dataset_kind != "rr-cdf" else raw_records,
            "reportingExceptionRows": [] if dataset_kind != "reporting-exception" else raw_records,
            "targetTables": GLEIF_DATASETS.get(dataset_kind, GLEIF_DATASETS["lei-cdf"])["targetTables"],
        }
    }


_OWNER_DID = "did:web:open-lei.etzhayyim.com"
_ACTOR_ID = "sys.langserver.open-lei.gleif"


def normalize_ownership_record(record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Normalize a GLEIF rr-cdf relationship record into (vertex_open_lei_ownership, edge) rows.

    Handles both GLEIF API format ({attributes: {relationship: {...}}}) and
    flat dict format ({parentLei, childLei, ...}).
    """
    attributes = record.get("attributes") if isinstance(record.get("attributes"), dict) else record
    relationship = attributes.get("relationship") if isinstance(attributes.get("relationship"), dict) else {}

    start_node = relationship.get("startNode") or {}
    end_node = relationship.get("endNode") or {}
    child_lei = (start_node.get("nodeID") or attributes.get("childLei") or attributes.get("lei") or "").strip()
    parent_lei = (end_node.get("nodeID") or attributes.get("parentLei") or "").strip()

    if not child_lei or not parent_lei or child_lei == parent_lei:
        return None

    rel_type = relationship.get("relationshipType") or attributes.get("relationshipType") or "IS_DIRECTLY_CONSOLIDATED_BY"
    status = relationship.get("status") or attributes.get("status") or "ACTIVE"

    periods = relationship.get("periods") or []
    period_start = periods[0].get("startDate") if periods else None
    period_end = periods[0].get("endDate") if periods else None

    raw_pct = relationship.get("percentageDirectlyOwned") or attributes.get("ownershipPct") or attributes.get("percentageDirectlyOwned")
    try:
        pct = float(raw_pct) if raw_pct is not None else None
    except (TypeError, ValueError):
        pct = None

    now = _utc_now()
    vertex_id = f"at://{_OWNER_DID}/com.etzhayyim.apps.openLei.ownership/{parent_lei}--{child_lei}"
    edge_id = f"edge-ownership-{parent_lei}--{child_lei}"
    parent_vid = f"at://{_OWNER_DID}/com.etzhayyim.apps.openLei.entity/{parent_lei}"
    child_vid = f"at://{_OWNER_DID}/com.etzhayyim.apps.openLei.entity/{child_lei}"

    ownership_row: dict[str, Any] = {
        "vertex_id": vertex_id,
        "parent_lei": parent_lei,
        "child_lei": child_lei,
        "relationship_type": rel_type,
        "ownership_pct": pct,
        "relationship_period_start": period_start,
        "relationship_period_end": period_end,
        "confidence": 1.0,
        "source": "gleif-rr-cdf",
        "status": "active" if status == "ACTIVE" else "inactive",
        "created_at": now,
        "sensitivity_ord": 1,
        "owner_did": _OWNER_DID,
        "org_id": _OWNER_DID,
        "user_id": _OWNER_DID,
        "actor_id": _ACTOR_ID,
    }
    edge_row: dict[str, Any] = {
        "edge_id": edge_id,
        "src_vid": child_vid,
        "dst_vid": parent_vid,
        "role": rel_type,
        "created_at": now,
        "sensitivity_ord": 1,
        "owner_did": _OWNER_DID,
        "org_id": _OWNER_DID,
        "user_id": _OWNER_DID,
        "actor_id": _ACTOR_ID,
    }
    return ownership_row, edge_row


from pymagatama.kotoba_datomic import get_kotoba_client

            kotoba_client = get_kotoba_client()
            for i in range(0, len(normalized), int(batch_size)):
                batch = normalized[i : i + int(batch_size)]
                for ownership_row, edge_row in batch:
                    try:
                        kotoba_client.insert_row("vertex_open_lei_ownership", ownership_row)
                        kotoba_client.insert_row("edge_open_lei_ownership_pair", edge_row)
                        inserted += 1
                        except Exception as exc:
                            skipped += 1
                            errors.append(str(exc)[:120])
        except Exception as exc:
            errors.append(f"batch write failed: {exc}")

    LOG.info("ownership_ingest: read=%d normalized=%d inserted=%d skipped=%d dry=%s",
             len(raw), len(normalized), inserted, skipped, dry_run)
    return {
        "openLeiOwnershipIngest": {
            "ingestId": f"gleif-ownership-ingest-{_utc_now()[:10]}",
            "recordsRead": len(raw),
            "recordsNormalized": len(normalized),
            "inserted": inserted,
            "skipped": skipped,
            "dryRun": dry_run,
            "errors": errors[:20],
        }
    }


def gleif_ems_match(*, entity_rows: Any = None, countries: Any = None, keywords: Any = None) -> dict[str, Any]:
    country_set = {item.upper() for item in _str_list(countries)}
    keyword_list = [item.lower() for item in (_str_list(keywords) or ["electronics", "manufacturing", "technology", "assembly", "industrial"])]
    candidates = []
    for row in [item for item in _as_list(entity_rows) if isinstance(item, dict)]:
        name = str(row.get("legal_name") or row.get("legalName") or "")
        country = str(row.get("country") or "").upper()
        if country_set and country not in country_set:
            continue
        matched = [kw for kw in keyword_list if kw in name.lower()]
        if matched:
            candidates.append({
                "lei": row.get("lei"),
                "legalName": name,
                "country": country,
                "matchedKeywords": matched,
                "score": min(100, 50 + len(matched) * 20),
                "nextEvidence": ["verify EMS capability", "collect website/profile evidence", "request RFQ"],
            })
    return {
        "openLeiGleifEmsMatch": {
            "matchId": f"gleif-ems-match-{_utc_now()[:10]}",
            "candidateCount": len(candidates),
            "candidates": candidates[:500],
        }
    }


def task_gleif_manifest_plan(**kwargs: Any) -> dict[str, Any]:
    return gleif_manifest_plan(as_of_date=kwargs.get("asOfDate"), datasets=kwargs.get("datasets"), mode=str(kwargs.get("mode") or "delta"))


def task_gleif_bulk_collect(**kwargs: Any) -> dict[str, Any]:
    return gleif_bulk_collect(
        dataset_kind=str(kwargs.get("datasetKind") or "lei-cdf"),
        as_of_date=kwargs.get("asOfDate"),
        shard=int(kwargs.get("shard") or 0),
        shard_count=int(kwargs.get("shardCount") or 1),
        limit=kwargs.get("limit"),
        page_size=int(kwargs.get("pageSize") or 200),
        fetch=not bool(kwargs.get("dryRun")),
    )


def task_gleif_record_normalize(**kwargs: Any) -> dict[str, Any]:
    collect = kwargs.get("openLeiGleifBulkCollect")
    if isinstance(collect, dict):
        records = kwargs.get("records") or collect.get("records")
        dataset_kind = str(kwargs.get("datasetKind") or collect.get("datasetKind") or "lei-cdf")
        as_of_date = kwargs.get("asOfDate") or collect.get("asOfDate")
    else:
        records = kwargs.get("records")
        dataset_kind = str(kwargs.get("datasetKind") or "lei-cdf")
        as_of_date = kwargs.get("asOfDate")
    return gleif_record_normalize(
        dataset_kind=dataset_kind,
        records=records,
        as_of_date=as_of_date,
    )


def task_gleif_ems_match(**kwargs: Any) -> dict[str, Any]:
    return gleif_ems_match(entity_rows=kwargs.get("entityRows"), countries=kwargs.get("countries"), keywords=kwargs.get("keywords"))


def task_gleif_ownership_ingest(**kwargs: Any) -> dict[str, Any]:
    # Accept ownershipRows directly or from upstream openLeiGleifRecordNormalize output
    normalize = kwargs.get("openLeiGleifRecordNormalize")
    ownership_rows = (
        kwargs.get("ownershipRows")
        or (normalize.get("ownershipRows") if isinstance(normalize, dict) else None)
        or []
    )
    return gleif_ownership_ingest(
        ownership_rows=ownership_rows,
        batch_size=int(kwargs.get("batchSize") or 500),
        dry_run=bool(kwargs.get("dryRun")),
    )


def register(worker: Any, timeout_ms: int = 180_000) -> None:
    worker.task(task_type="openLei.gleif.manifest.plan", single_value=False, timeout_ms=timeout_ms)(task_gleif_manifest_plan)
    worker.task(task_type="openLei.gleif.bulk.collect", single_value=False, timeout_ms=timeout_ms)(task_gleif_bulk_collect)
    worker.task(task_type="openLei.gleif.record.normalize", single_value=False, timeout_ms=timeout_ms)(task_gleif_record_normalize)
    worker.task(task_type="openLei.gleif.ownership.ingest", single_value=False, timeout_ms=timeout_ms)(task_gleif_ownership_ingest)
    worker.task(task_type="openLei.gleif.ems.match", single_value=False, timeout_ms=timeout_ms)(task_gleif_ems_match)
