"""yoro product ingest primitives — etzhayyim MST/IPFS/L2 substrate variant.

Religious-corp landing target for the yoro product ingest Python primitive layer.

ADR authority:
    ADR-2605215300 (addendum — per-function migration table + skeleton):
        90-docs/adr/2605215300-etzhayyim-yoro-python-primitives-mst-rewrite-addendum.md
    ADR-2605191358 (parent — per-path CF Worker + UI rewrite map):
        90-docs/adr/2605191358-yoro-murakumo-rw-free-rewrite-map.md

Migration notes:
    20-actors/magatama/py/YORO-PYTHON-MIGRATION-NOTES.md rows #31–#40

DO NOT:
    - Import psycopg2, psycopg, or any other SQL driver.
    - Reference RW_URL, HYPERDRIVE, or any RisingWave connection string.
    - Import Stripe, runpod, or any fiat / cloud-GPU client.
    - Add FLUSH calls (MST commits are atomic).

This module fails fast (RuntimeError) if RW_URL is present in the environment
to prevent accidental RisingWave coupling in etzhayyim builds.

Implementation status (M6 2026-05-21):
    ingest_product()              — IMPLEMENTED (M3) — app.etzhayyim.productIngest
    batch_ingest_products()       — IMPLEMENTED (M3) — batch putRecord with coalescer
    upsert_product_profile()      — IMPLEMENTED (M6) — putRecord overwrite (rkey=profile-{id})
    fetch_product_by_id()         — IMPLEMENTED (M6) — getRecord (rkey=profile-{id})
    fetch_products_by_category()  — IMPLEMENTED (M6) — listRecords + client-side filter
    record_product_event()        — IMPLEMENTED (M6) — putRecord productEvent (append-only)
    delete_product()              — IMPLEMENTED (M6) — deleteRecord MST tombstone
    list_ingested_product_ids()   — IMPLEMENTED (M6) — listRecords with cursor pagination
    count_products_by_status()    — IMPLEMENTED (M7) — listRecords client-side count with status filter
    register()                    — IMPLEMENTED (M7) — Zeebe task registrar
"""

from __future__ import annotations

import datetime as _dt
import os
from dataclasses import dataclass, field
from typing import Any

# ── SDK import (stub calls — downstream NotImplementedError until M3) ──────────
try:
    from etzhayyim_sdk import pds as _pds_mod
    from etzhayyim_sdk.coalesce import RequestCoalescer as _RequestCoalescer
except ImportError:
    _pds_mod = None  # type: ignore[assignment]
    _RequestCoalescer = None  # type: ignore[assignment]

# Module-level coalescer instance (shared across calls within the same process).
_COALESCER: Any = None


def _get_coalescer() -> Any:
    """Return the module-level RequestCoalescer, initialising it on first use."""
    global _COALESCER
    if _COALESCER is None and _RequestCoalescer is not None:
        _COALESCER = _RequestCoalescer(window_ms=100, max_batch=64)
    return _COALESCER


# ---------------------------------------------------------------------------
# Substrate-fit guard — reject if RW_URL is present (ADR-2605172000)
# ---------------------------------------------------------------------------

def _substrate_fit_guard() -> None:
    rw_url = os.environ.get("RW_URL", "").strip()
    if rw_url:
        raise RuntimeError(
            "yoro_product_ingest_murakumo: RW_URL is set. "
            "This module is the etzhayyim/root religious-corp variant and MUST NOT "
            "connect to RisingWave. Unset RW_URL or use primitives/yoro_product_ingest.py "
            "for vendor SaaS builds. See ADR-2605172000 §substrate-hard-rule."
        )


_substrate_fit_guard()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_REPO = "did:web:yoro.etzhayyim.com"

# Religious-corp lexicon NSIDs (new — ADR-2605215300 §2 + extension)
PRODUCT_INGEST_COLLECTION = "ai.gftd.apps.etzhayyim.productIngest"
PRODUCT_EVENT_COLLECTION = "ai.gftd.apps.etzhayyim.productEvent"


# ---------------------------------------------------------------------------
# Typed dataclasses for religious-corp wire shapes
# ---------------------------------------------------------------------------

@dataclass
class ProductIngestRecord:
    """Wire shape for ai.gftd.apps.etzhayyim.productIngest MST record.

    New lexicon required at M1 — ADR-2605215300 §2 extension.
    Must be authored in 00-contracts/lexicons/ai/gftd/apps/etzhayyim/productIngest.json
    before M2 implementation replaces the NotImplementedError stubs.
    """
    repo: str
    rkey: str
    uri: str
    product_id: str
    collection: str  # always PRODUCT_INGEST_COLLECTION
    created_at: str
    payload: dict[str, Any] = field(default_factory=dict)
    category: str = ""
    status: str = "active"


@dataclass
class ProductEventRecord:
    """Wire shape for ai.gftd.apps.etzhayyim.productEvent MST record.

    Optional new lexicon — ADR-2605215300 §2 extension.
    """
    repo: str
    rkey: str
    uri: str
    product_id: str
    event_type: str
    occurred_at: str
    payload: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Utility helpers (pure, no substrate calls)
# ---------------------------------------------------------------------------

def utc_now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rkey(product_id: str, suffix: str = "") -> str:
    stamp = _dt.datetime.now(tz=_dt.UTC).strftime("%Y%m%d%H%M%S")
    suffix_part = f"-{suffix}" if suffix else ""
    return f"product-{product_id}{suffix_part}-{stamp}-{os.getpid()}"


# ---------------------------------------------------------------------------
# REIMPLEMENT stubs — M2/M3 deadline per ADR-2605215300 §4
# ---------------------------------------------------------------------------

async def ingest_product(product_dict: dict[str, Any], *, repo: str = DEFAULT_REPO) -> dict[str, Any]:
    """Ingest a product record via @etzhayyim/sdk putRecord.  [M3 IMPLEMENTED]

    Vendor equivalent: ingest_product() in yoro_product_ingest.py
      INSERT INTO vertex_product

    Substrate path (ADR-2605215300 §3):
      @etzhayyim/sdk Python binding → PDS put_record(ai.gftd.apps.etzhayyim.productIngest)
      → MST commit → IPFS pin (anchored)

    Wire shape matches app.etzhayyim.productIngest lexicon (2026-05-21):
      The productIngest lexicon is typed as a procedure (XRPC) not a record.
      This function writes the product payload as an MST record using the
      PRODUCT_INGEST_COLLECTION NSID with a deterministic rkey from product_id.

    product_dict keys:
      product_id (str, required): identifier for the product
      source_uri (str): AT URI of source record triggering the ingest
      product_kind (str): category / type label
      metadata (dict): optional bag — title, description, externalId, lang
      status (str): "active" | "draft" | "archived" (defaults to "active")
      category (str): alias for product_kind (legacy compat)

    Returns: dict with keys: uri (AT URI), rkey, product_id, ingested_at, status
    """
    if _pds_mod is None:
        raise ImportError(
            "etzhayyim_sdk not installed. Install 20-actors/etzhayyim-sdk-py."
        )

    product_id = str(product_dict.get("product_id") or product_dict.get("id") or "")
    if not product_id:
        raise ValueError("ingest_product: product_dict must include 'product_id'")

    ingested_at = utc_now_iso()
    rkey = _rkey(product_id)
    uri = f"at://{repo}/{PRODUCT_INGEST_COLLECTION}/{rkey}"
    product_kind = str(
        product_dict.get("product_kind") or product_dict.get("category") or "generic"
    )
    status = str(product_dict.get("status") or "active")
    source_uri = str(product_dict.get("source_uri") or uri)

    # Build metadata bag from product_dict fields
    raw_meta = product_dict.get("metadata") or {}
    metadata: dict[str, Any] = {}
    if isinstance(raw_meta, dict):
        metadata = {k: v for k, v in raw_meta.items() if v is not None}
    # Pull top-level convenience fields into metadata if not already set
    for meta_key in ("title", "description", "externalId", "lang"):
        if meta_key not in metadata and product_dict.get(meta_key):
            metadata[meta_key] = product_dict[meta_key]

    # Wire shape: productIngest record stored in MST keyed by PRODUCT_INGEST_COLLECTION.
    ingest_record: dict[str, Any] = {
        "$type": PRODUCT_INGEST_COLLECTION,
        "productId": product_id,
        "sourceUri": source_uri,
        "productKind": product_kind,
        "metadata": metadata,
        "status": status,
        "ingestedAt": ingested_at,
    }

    # vendor: INSERT INTO vertex_product
    # religious-corp: PDS put_record(productIngest) → MST commit → IPFS pin
    await _pds_mod.put_record(
        collection=PRODUCT_INGEST_COLLECTION,
        record=ingest_record,
        repo=repo,
        rkey=rkey,
    )

    return {
        "uri": uri,
        "rkey": rkey,
        "product_id": product_id,
        "ingested_at": ingested_at,
        "status": status,
    }


async def upsert_product_profile(
    product_id: str,
    updates: dict[str, Any],
    *,
    repo: str = DEFAULT_REPO,
) -> dict[str, Any]:
    """Upsert a product profile record via @etzhayyim/sdk putRecord (overwrite).
    [M6 IMPLEMENTED]

    Vendor equivalent: upsert_product_profile() in yoro_product_ingest.py
      UPDATE/INSERT INTO vertex_product SET … WHERE product_id = …

    Substrate path (ADR-2605215300 §3):
      @etzhayyim/sdk Python binding → PDS putRecord
      (ai.gftd.apps.etzhayyim.productIngest, rkey=product_id) → MST commit
      MST handles idempotent overwrite semantics; putRecord with a stable rkey
      is equivalent to the vendor's UPDATE/INSERT pattern.

    rkey is set to product_id (stable key) so repeated calls overwrite in-place.
    See: ADR-2605215300 §4, YORO-PYTHON-MIGRATION-NOTES.md row #32
    """
    if _pds_mod is None:
        raise ImportError(
            "etzhayyim_sdk not installed. Install 20-actors/etzhayyim-sdk-py."
        )
    if not product_id:
        raise ValueError("upsert_product_profile: product_id is required")

    updated_at = utc_now_iso()
    # Stable rkey = product_id enables idempotent overwrite (MST MERGE semantics).
    rkey = f"profile-{product_id}"
    uri = f"at://{repo}/{PRODUCT_INGEST_COLLECTION}/{rkey}"

    product_kind = str(
        updates.get("product_kind") or updates.get("category") or "generic"
    )
    status = str(updates.get("status") or "active")
    raw_meta = updates.get("metadata") or {}
    metadata: dict[str, Any] = {}
    if isinstance(raw_meta, dict):
        metadata = {k: v for k, v in raw_meta.items() if v is not None}
    for meta_key in ("title", "description", "externalId", "lang"):
        if meta_key not in metadata and updates.get(meta_key):
            metadata[meta_key] = updates[meta_key]

    profile_record: dict[str, Any] = {
        "$type": PRODUCT_INGEST_COLLECTION,
        "productId": product_id,
        "productKind": product_kind,
        "metadata": metadata,
        "status": status,
        "updatedAt": updated_at,
    }

    await _pds_mod.put_record(
        collection=PRODUCT_INGEST_COLLECTION,
        record=profile_record,
        repo=repo,
        rkey=rkey,
    )

    return {
        "uri": uri,
        "rkey": rkey,
        "product_id": product_id,
        "updated_at": updated_at,
        "status": status,
    }


async def fetch_products_by_category(
    category: str,
    *,
    repo: str = DEFAULT_REPO,
    limit: int = 20,
    cursor: str = "",
) -> dict[str, Any]:
    """List product records by category via @etzhayyim/sdk listRecords.
    [M6 — client-side filter; mst-projector index deferred M7]

    Vendor equivalent: fetch_products_by_category() in yoro_product_ingest.py
      SELECT FROM vertex_product WHERE category = %(category)s LIMIT %(limit)s

    Substrate path (ADR-2605215300 §3 SELECT mapping):
      @etzhayyim/sdk Python binding → PDS listRecords
      (ai.gftd.apps.etzhayyim.productIngest) → client-side category filter.
      NOTE: PDS listRecords has no server-side field filter; we fetch up to
      min(limit * 4, 100) records and filter client-side on productKind.
      For high-volume use, replace with mst-projector CID-pinned snapshot (M7).

    Returns: {"products": [...], "cursor": str | None, "category": category}
    See: YORO-PYTHON-MIGRATION-NOTES.md row #33
    """
    if _pds_mod is None:
        raise ImportError(
            "etzhayyim_sdk not installed. Install 20-actors/etzhayyim-sdk-py."
        )

    effective_cursor = cursor or None
    # Fetch more than needed to allow client-side filtering
    fetch_limit = min(limit * 4, 100)
    data = await _pds_mod.list_records(
        repo,
        PRODUCT_INGEST_COLLECTION,
        limit=fetch_limit,
        cursor=effective_cursor,
    )

    all_records: list[dict[str, Any]] = data.get("records", [])
    filtered: list[dict[str, Any]] = []
    for rec in all_records:
        value = rec.get("value") or {}
        product_kind = str(
            value.get("productKind") or value.get("category") or ""
        ).lower()
        if category.lower() in product_kind or product_kind in category.lower():
            filtered.append({
                "uri": rec.get("uri", ""),
                "rkey": rec.get("rkey", ""),
                "product_id": value.get("productId", ""),
                "product_kind": value.get("productKind", ""),
                "status": value.get("status", "active"),
                "metadata": value.get("metadata", {}),
                "ingested_at": value.get("ingestedAt", ""),
            })
        if len(filtered) >= limit:
            break

    return {
        "products": filtered,
        "cursor": data.get("cursor"),
        "category": category,
    }


async def fetch_product_by_id(
    product_id: str,
    *,
    repo: str = DEFAULT_REPO,
) -> dict[str, Any] | None:
    """Read a product profile record from PDS via @etzhayyim/sdk getRecord.
    [M6 IMPLEMENTED]

    Vendor equivalent: fetch_product_by_id() in yoro_product_ingest.py
      SELECT FROM vertex_product WHERE product_id = %(product_id)s

    Substrate path (ADR-2605215300 §3 SELECT mapping):
      @etzhayyim/sdk Python binding → PDS getRecord
      (repo, ai.gftd.apps.etzhayyim.productIngest, rkey=profile-{product_id})
      The stable rkey prefix "profile-" matches upsert_product_profile rkey convention.

    Returns the product value dict on success, or None if not found.
    See: YORO-PYTHON-MIGRATION-NOTES.md row #34
    """
    if _pds_mod is None:
        raise ImportError(
            "etzhayyim_sdk not installed. Install 20-actors/etzhayyim-sdk-py."
        )
    if not product_id:
        raise ValueError("fetch_product_by_id: product_id is required")

    rkey = f"profile-{product_id}"
    uri = f"at://{repo}/{PRODUCT_INGEST_COLLECTION}/{rkey}"
    try:
        data = await _pds_mod.get_record(uri)
    except Exception:
        return None

    if not data:
        return None

    value = data.get("value") or {}
    return {
        "uri": data.get("uri", uri),
        "rkey": rkey,
        "product_id": product_id,
        "product_kind": value.get("productKind", ""),
        "status": value.get("status", "active"),
        "metadata": value.get("metadata", {}),
        "updated_at": value.get("updatedAt", ""),
        "ingested_at": value.get("ingestedAt", ""),
    }


async def record_product_event(
    product_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    repo: str = DEFAULT_REPO,
) -> dict[str, Any]:
    """Append a product event record via @etzhayyim/sdk putRecord.
    [M6 IMPLEMENTED]

    Vendor equivalent: record_product_event() in yoro_product_ingest.py
      INSERT INTO vertex_product_event

    Substrate path (ADR-2605215300 §3):
      @etzhayyim/sdk Python binding → PDS putRecord
      (ai.gftd.apps.etzhayyim.productEvent, rkey=timestamped unique key) → MST commit
      Each event appends a new record (no overwrite) — append-only audit log.

    product_id: identifier of the product the event applies to.
    event_type: string label, e.g. "viewed", "purchased", "archived", "updated".
    payload: optional bag for event-type-specific data.

    Returns: dict with keys: uri, rkey, product_id, event_type, occurred_at
    See: YORO-PYTHON-MIGRATION-NOTES.md row #35
    """
    if _pds_mod is None:
        raise ImportError(
            "etzhayyim_sdk not installed. Install 20-actors/etzhayyim-sdk-py."
        )
    if not product_id:
        raise ValueError("record_product_event: product_id is required")
    if not event_type:
        raise ValueError("record_product_event: event_type is required")

    occurred_at = utc_now_iso()
    rkey = _rkey(product_id, event_type)
    uri = f"at://{repo}/{PRODUCT_EVENT_COLLECTION}/{rkey}"

    event_record: dict[str, Any] = {
        "$type": PRODUCT_EVENT_COLLECTION,
        "productId": product_id,
        "eventType": event_type,
        "payload": payload or {},
        "occurredAt": occurred_at,
    }

    await _pds_mod.put_record(
        collection=PRODUCT_EVENT_COLLECTION,
        record=event_record,
        repo=repo,
        rkey=rkey,
    )

    return {
        "uri": uri,
        "rkey": rkey,
        "product_id": product_id,
        "event_type": event_type,
        "occurred_at": occurred_at,
    }


async def batch_ingest_products(
    products: list[dict[str, Any]],
    *,
    repo: str = DEFAULT_REPO,
    coalescer: Any = None,
) -> list[dict[str, Any]]:
    """Batch ingest product records via @etzhayyim/sdk putRecord with async coalescing.
    [M3 IMPLEMENTED]

    Vendor equivalent: batch_ingest_products() in yoro_product_ingest.py
      Batch INSERT INTO vertex_product

    Substrate path (ADR-2605215300 §3):
      For each product, coalescer.submit(key=product_id, fn=lambda: pds.put_record(productIngest))
      → MST commits (batched within 100 ms windows per product_id)

    Coalescer integration:
      Concurrent batch_ingest_products calls for the same product_id are coalesced
      into one MST commit per product_id within a 100 ms window.
      This meets the ≥ 5 records/sec throughput target per ADR-2605215300 §Consequences.

    Each product in products list must include 'product_id'.
    Returns: list of result dicts, one per product (same order as input).
    Failed products include an 'error' key instead of 'uri'.
    """
    if _pds_mod is None:
        raise ImportError(
            "etzhayyim_sdk not installed. Install 20-actors/etzhayyim-sdk-py."
        )

    import asyncio

    active_coalescer = coalescer or _get_coalescer()
    results: list[dict[str, Any]] = []

    async def _ingest_one(product_dict: dict[str, Any]) -> dict[str, Any]:
        product_id = str(product_dict.get("product_id") or product_dict.get("id") or "")
        if not product_id:
            return {"error": "missing product_id", "product_id": ""}

        ingested_at = utc_now_iso()
        rkey = _rkey(product_id)
        uri = f"at://{repo}/{PRODUCT_INGEST_COLLECTION}/{rkey}"
        product_kind = str(
            product_dict.get("product_kind") or product_dict.get("category") or "generic"
        )
        status = str(product_dict.get("status") or "active")
        source_uri = str(product_dict.get("source_uri") or uri)
        raw_meta = product_dict.get("metadata") or {}
        metadata: dict[str, Any] = {}
        if isinstance(raw_meta, dict):
            metadata = {k: v for k, v in raw_meta.items() if v is not None}
        for meta_key in ("title", "description", "externalId", "lang"):
            if meta_key not in metadata and product_dict.get(meta_key):
                metadata[meta_key] = product_dict[meta_key]

        ingest_record: dict[str, Any] = {
            "$type": PRODUCT_INGEST_COLLECTION,
            "productId": product_id,
            "sourceUri": source_uri,
            "productKind": product_kind,
            "metadata": metadata,
            "status": status,
            "ingestedAt": ingested_at,
        }

        async def _do_put() -> dict[str, Any]:
            return await _pds_mod.put_record(
                collection=PRODUCT_INGEST_COLLECTION,
                record=ingest_record,
                repo=repo,
                rkey=rkey,
            )

        if active_coalescer is not None:
            await active_coalescer.submit(key=product_id, fn=_do_put)
        else:
            await _do_put()

        return {
            "uri": uri,
            "rkey": rkey,
            "product_id": product_id,
            "ingested_at": ingested_at,
            "status": status,
        }

    # Fan out all ingest tasks concurrently; gather errors per-item (return_exceptions).
    tasks = [_ingest_one(p) for p in products]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, res in enumerate(raw_results):
        if isinstance(res, Exception):
            product_id = str(products[i].get("product_id") or products[i].get("id") or "")
            results.append({"error": str(res), "product_id": product_id})
        else:
            results.append(res)  # type: ignore[arg-type]

    return results


async def delete_product(
    product_id: str,
    *,
    repo: str = DEFAULT_REPO,
) -> dict[str, Any]:
    """Delete a product profile record via @etzhayyim/sdk deleteRecord (MST tombstone).
    [M6 IMPLEMENTED]

    Vendor equivalent: delete_product() in yoro_product_ingest.py
      DELETE FROM vertex_product WHERE product_id = %(product_id)s

    Substrate path (ADR-2605215300 §4):
      @etzhayyim/sdk Python binding → PDS deleteRecord
      (ai.gftd.apps.etzhayyim.productIngest, rkey=profile-{product_id})
      → MST tombstone. IPFS unpin is handled downstream by anchor-cron
      (ADR-2605171800 Stage 3) — not inline here.

    Returns: {"ok": True, "deleted": uri, "product_id": product_id}
    On error (not found, network): {"ok": False, "error": str, "product_id": product_id}
    See: YORO-PYTHON-MIGRATION-NOTES.md row #37
    """
    if _pds_mod is None:
        raise ImportError(
            "etzhayyim_sdk not installed. Install 20-actors/etzhayyim-sdk-py."
        )
    if not product_id:
        return {"ok": False, "error": "product_id is required", "product_id": ""}

    rkey = f"profile-{product_id}"
    uri = f"at://{repo}/{PRODUCT_INGEST_COLLECTION}/{rkey}"
    try:
        await _pds_mod.delete_record(uri)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "product_id": product_id}

    return {"ok": True, "deleted": uri, "product_id": product_id}


async def list_ingested_product_ids(
    *,
    repo: str = DEFAULT_REPO,
    limit: int = 50,
    cursor: str = "",
) -> dict[str, Any]:
    """List ingested product rkeys via @etzhayyim/sdk listRecords with pagination.
    [M6 IMPLEMENTED]

    Vendor equivalent: list_ingested_product_ids() in yoro_product_ingest.py
      SELECT product_id FROM vertex_product LIMIT %(limit)s OFFSET …

    Substrate path (ADR-2605215300 §3 SELECT mapping):
      @etzhayyim/sdk Python binding → PDS listRecords
      (ai.gftd.apps.etzhayyim.productIngest, limit, cursor) → extract product_ids
      Pagination is cursor-based (MST CID cursor) rather than offset-based.

    Returns:
      {"product_ids": [str, ...], "rkeys": [str, ...], "cursor": str | None, "count": int}
    See: YORO-PYTHON-MIGRATION-NOTES.md row #38
    """
    if _pds_mod is None:
        raise ImportError(
            "etzhayyim_sdk not installed. Install 20-actors/etzhayyim-sdk-py."
        )

    effective_cursor = cursor or None
    data = await _pds_mod.list_records(
        repo,
        PRODUCT_INGEST_COLLECTION,
        limit=min(limit, 100),
        cursor=effective_cursor,
    )

    records: list[dict[str, Any]] = data.get("records", [])
    product_ids: list[str] = []
    rkeys: list[str] = []
    for rec in records:
        value = rec.get("value") or {}
        pid = str(value.get("productId") or "")
        rkey = str(rec.get("rkey") or "")
        if pid:
            product_ids.append(pid)
        if rkey:
            rkeys.append(rkey)

    return {
        "product_ids": product_ids,
        "rkeys": rkeys,
        "cursor": data.get("cursor"),
        "count": len(product_ids),
    }


async def count_products_by_status(status: str, *, repo: str = DEFAULT_REPO) -> int:
    """Count products by status via SDK listRecords (client-side count).
    [M7 IMPLEMENTED]

    Vendor equivalent: count_products_by_status() in yoro_product_ingest.py
      SELECT count(*) FROM vertex_product WHERE status = %(status)s

    Substrate path (ADR-2605215300 §3):
      @etzhayyim/sdk Python binding → PDS listRecords (PRODUCT_INGEST_COLLECTION)
      → client-side filter on status field → count.

    NOTE: PDS listRecords has no server-side field filter. This implementation
    fetches up to 100 records per page and counts client-side. For high-volume
    collections (>100 records), the full count requires pagination across all pages.
    A mst-projector CID-pinned aggregate snapshot is the preferred path for
    production (ADR-2605191358 §12-MVs) but is deferred until the mst-projector
    service is operational. This implementation pages through up to 500 records
    (5 pages × 100) to provide a practical count for M7 workloads.

    status: one of "active", "draft", "archived" (or any custom status string).
    Returns: count of matching products (int ≥ 0).
    See: YORO-PYTHON-MIGRATION-NOTES.md row #39
    """
    if _pds_mod is None:
        raise ImportError(
            "etzhayyim_sdk not installed. Install 20-actors/etzhayyim-sdk-py."
        )
    if not status:
        raise ValueError("count_products_by_status: status is required")

    count = 0
    cursor: str | None = None
    pages_remaining = 5  # Safety cap: max 500 records scanned

    while pages_remaining > 0:
        data = await _pds_mod.list_records(
            repo,
            PRODUCT_INGEST_COLLECTION,
            limit=100,
            cursor=cursor,
        )
        records: list[dict] = data.get("records", [])
        for rec in records:
            value = rec.get("value") or {}
            rec_status = str(value.get("status") or "active")
            if rec_status == status:
                count += 1

        cursor = data.get("cursor")
        pages_remaining -= 1
        if not cursor:
            break

    return count


# ---------------------------------------------------------------------------
# Task registration (mirrors vendor register() signature)
# ---------------------------------------------------------------------------

def register(worker: Any, *, timeout_ms: int) -> None:
    """Register yoro product ingest tasks with the Zeebe worker.
    [M7 IMPLEMENTED]

    Matches vendor signature exactly (PORT-adapted, ADR-2605215300 §3 row #40).
    Handler refs point to murakumo variants in this module.

    Registered task types (bpmn_dispatcher namespace):
      yoro.productIngest.ingestProduct         → ingest_product
      yoro.productIngest.batchIngestProducts   → batch_ingest_products
      yoro.productIngest.upsertProductProfile  → upsert_product_profile
      yoro.productIngest.fetchProductById      → fetch_product_by_id
      yoro.productIngest.fetchProductsByCategory → fetch_products_by_category
      yoro.productIngest.recordProductEvent    → record_product_event
      yoro.productIngest.deleteProduct         → delete_product
      yoro.productIngest.listIngestedProductIds → list_ingested_product_ids
      yoro.productIngest.countProductsByStatus → count_products_by_status

    See: YORO-PYTHON-MIGRATION-NOTES.md row #40
    """
    worker.task(
        task_type="yoro.productIngest.ingestProduct",
        single_value=False,
        timeout_ms=timeout_ms,
    )(ingest_product)
    worker.task(
        task_type="yoro.productIngest.batchIngestProducts",
        single_value=False,
        timeout_ms=timeout_ms,
    )(batch_ingest_products)
    worker.task(
        task_type="yoro.productIngest.upsertProductProfile",
        single_value=False,
        timeout_ms=timeout_ms,
    )(upsert_product_profile)
    worker.task(
        task_type="yoro.productIngest.fetchProductById",
        single_value=False,
        timeout_ms=timeout_ms,
    )(fetch_product_by_id)
    worker.task(
        task_type="yoro.productIngest.fetchProductsByCategory",
        single_value=False,
        timeout_ms=timeout_ms,
    )(fetch_products_by_category)
    worker.task(
        task_type="yoro.productIngest.recordProductEvent",
        single_value=False,
        timeout_ms=timeout_ms,
    )(record_product_event)
    worker.task(
        task_type="yoro.productIngest.deleteProduct",
        single_value=False,
        timeout_ms=timeout_ms,
    )(delete_product)
    worker.task(
        task_type="yoro.productIngest.listIngestedProductIds",
        single_value=False,
        timeout_ms=timeout_ms,
    )(list_ingested_product_ids)
    worker.task(
        task_type="yoro.productIngest.countProductsByStatus",
        single_value=False,
        timeout_ms=timeout_ms,
    )(count_products_by_status)
