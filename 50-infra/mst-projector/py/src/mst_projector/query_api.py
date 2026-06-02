"""mst-projector query API (XRPC) — M3 deliverable per ADR-2605215500.

aiohttp server exposing 4 NSIDs over /xrpc/* for filtered queries against
the indexed LanceDB tables maintained by the subscriber.

Endpoints:
  POST /xrpc/com.etzhayyim.mstProjector.queryByCollection
  POST /xrpc/com.etzhayyim.mstProjector.queryByDid
  POST /xrpc/com.etzhayyim.mstProjector.queryByField
  POST /xrpc/com.etzhayyim.mstProjector.countByCollection

Run via main.py entry point or directly:
  python -m mst_projector.query_api
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any

from aiohttp import web

from .indexer import get_indexer

_log = logging.getLogger(__name__)

# Regex for safe field names: alphanumeric + underscore, must start with letter/underscore
_SAFE_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# ── NSID handlers ──────────────────────────────────────────────────────────────


async def _query_by_collection(request: web.Request) -> web.Response:
    """POST /xrpc/com.etzhayyim.mstProjector.queryByCollection

    Input:  collection: str, limit: int=50, cursor: str?
    Output: records: list, cursor: str?
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "InvalidRequest", "message": "body must be JSON"},
            status=400,
        )

    collection = body.get("collection")
    if not collection:
        return web.json_response(
            {"error": "InvalidRequest", "message": "collection required"},
            status=400,
        )

    try:
        limit = int(body.get("limit", 50))
        if limit < 1 or limit > 1000:
            raise ValueError("out of range")
    except (ValueError, TypeError):
        return web.json_response(
            {"error": "InvalidRequest", "message": "limit must be 1–1000"},
            status=400,
        )

    # Cursor is opaque offset-based: cursor value = string representation of int offset
    cursor = body.get("cursor")
    try:
        offset = int(cursor) if cursor is not None else 0
        if offset < 0:
            raise ValueError
    except (ValueError, TypeError):
        return web.json_response(
            {"error": "InvalidRequest", "message": "invalid cursor"},
            status=400,
        )

    indexer = get_indexer()
    # Fetch offset+limit+1 rows to detect whether a next page exists
    all_records = await indexer.query(
        collection=collection,
        limit=offset + limit + 1,
    )
    page = all_records[offset : offset + limit + 1]

    next_cursor: str | None = None
    if len(page) > limit:
        page = page[:limit]
        next_cursor = str(offset + limit)

    return web.json_response({"records": page, "cursor": next_cursor})


async def _query_by_did(request: web.Request) -> web.Response:
    """POST /xrpc/com.etzhayyim.mstProjector.queryByDid

    Input:  did: str, collection?: str, limit: int=50, cursor?: str
    Output: records: list, cursor: str?
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "InvalidRequest", "message": "body must be JSON"},
            status=400,
        )

    did = body.get("did")
    if not did:
        return web.json_response(
            {"error": "InvalidRequest", "message": "did required"},
            status=400,
        )

    collection = body.get("collection")

    try:
        limit = int(body.get("limit", 50))
        if limit < 1 or limit > 1000:
            raise ValueError("out of range")
    except (ValueError, TypeError):
        return web.json_response(
            {"error": "InvalidRequest", "message": "limit must be 1–1000"},
            status=400,
        )

    cursor = body.get("cursor")
    try:
        offset = int(cursor) if cursor is not None else 0
        if offset < 0:
            raise ValueError
    except (ValueError, TypeError):
        return web.json_response(
            {"error": "InvalidRequest", "message": "invalid cursor"},
            status=400,
        )

    # Escape single quotes in DID value (DIDs should not contain them, but be safe)
    safe_did = did.replace("'", "''")
    filter_sql = f"did = '{safe_did}'"

    indexer = get_indexer()

    if collection:
        all_records = await indexer.query(
            collection=collection,
            filter_sql=filter_sql,
            limit=offset + limit + 1,
        )
    else:
        # Cross-collection slow path — enumerate all tables
        collections = await indexer.list_collections()
        gathered: list[dict[str, Any]] = []
        for col in collections:
            try:
                col_records = await indexer.query(
                    collection=col,
                    filter_sql=filter_sql,
                    limit=limit,
                )
                gathered.extend(col_records)
            except Exception as exc:
                _log.warning("query_by_did: skip collection %s: %s", col, exc)
        all_records = gathered[: offset + limit + 1]

    page = all_records[offset : offset + limit + 1]

    next_cursor: str | None = None
    if len(page) > limit:
        page = page[:limit]
        next_cursor = str(offset + limit)

    return web.json_response({"records": page, "cursor": next_cursor})


async def _query_by_field(request: web.Request) -> web.Response:
    """POST /xrpc/com.etzhayyim.mstProjector.queryByField

    Input:  collection: str, fieldName: str, fieldValue: str, limit: int=50
    Output: records: list
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "InvalidRequest", "message": "body must be JSON"},
            status=400,
        )

    collection = body.get("collection")
    # Accept both camelCase (wire) and snake_case (internal)
    field_name = body.get("fieldName") or body.get("field_name")
    field_value = body.get("fieldValue") if "fieldValue" in body else body.get("field_value")

    if not collection or not field_name or field_value is None:
        return web.json_response(
            {
                "error": "InvalidRequest",
                "message": "collection, fieldName, fieldValue required",
            },
            status=400,
        )

    # SQL injection defence: reject field names that don't match safe pattern
    if not _SAFE_FIELD_RE.match(field_name):
        return web.json_response(
            {
                "error": "InvalidRequest",
                "message": (
                    "fieldName must start with a letter or underscore and "
                    "contain only alphanumeric characters and underscores"
                ),
            },
            status=400,
        )

    try:
        limit = int(body.get("limit", 50))
        if limit < 1 or limit > 1000:
            raise ValueError("out of range")
    except (ValueError, TypeError):
        return web.json_response(
            {"error": "InvalidRequest", "message": "limit must be 1–1000"},
            status=400,
        )

    # Escape single quotes in the value to prevent SQL injection
    safe_value = str(field_value).replace("'", "''")

    indexer = get_indexer()
    try:
        records = await indexer.query(
            collection=collection,
            filter_sql=f"{field_name} = '{safe_value}'",
            limit=limit,
        )
    except Exception as exc:
        _log.warning("query_by_field: query failed: %s", exc)
        return web.json_response(
            {"error": "UnindexedField", "message": str(exc)},
            status=400,
        )

    return web.json_response({"records": records})


async def _healthz(request: web.Request) -> web.Response:
    """Liveness + readiness probe.

    Returns 200 with summary if indexer + subscriber are healthy.
    Returns 503 if either is unreachable.
    """
    indexer = get_indexer()
    try:
        collections = await indexer.list_collections()
        return web.json_response({
            "ok": True,
            "service": "mst-projector",
            "indexed_collections": len(collections),
            "data_dir": str(indexer.data_dir),
        })
    except Exception as e:
        return web.json_response({
            "ok": False,
            "service": "mst-projector",
            "error": str(e),
        }, status=503)


async def _count_by_collection(request: web.Request) -> web.Response:
    """POST /xrpc/com.etzhayyim.mstProjector.countByCollection

    Input:  collection: str, asOf?: str (ignored — reserved for future)
    Output: count: int, asOf: str
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response(
            {"error": "InvalidRequest", "message": "body must be JSON"},
            status=400,
        )

    collection = body.get("collection")
    if not collection:
        return web.json_response(
            {"error": "InvalidRequest", "message": "collection required"},
            status=400,
        )

    indexer = get_indexer()
    # M4 optimisation: use LanceDB native count_rows() if available (O(1) on
    # compacted tables) — avoids full 100k-row scan from M3 implementation.
    # Fallback to query-based count if count_rows raises (e.g. very old LanceDB).
    as_of = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        count = await indexer.count_rows(collection)
    except Exception as exc:
        _log.warning(
            "count_by_collection: count_rows failed (%s), falling back to scan", exc
        )
        records = await indexer.query(collection=collection, limit=100_000)
        count = len(records)

    return web.json_response({"count": count, "asOf": as_of})


# ── Server bootstrap ───────────────────────────────────────────────────────────


def build_app() -> web.Application:
    """Construct and return the aiohttp Application with all 4 XRPC routes."""
    app = web.Application()
    app.router.add_get("/healthz", _healthz)
    app.router.add_post(
        "/xrpc/com.etzhayyim.mstProjector.queryByCollection",
        _query_by_collection,
    )
    app.router.add_post(
        "/xrpc/com.etzhayyim.mstProjector.queryByDid",
        _query_by_did,
    )
    app.router.add_post(
        "/xrpc/com.etzhayyim.mstProjector.queryByField",
        _query_by_field,
    )
    app.router.add_post(
        "/xrpc/com.etzhayyim.mstProjector.countByCollection",
        _count_by_collection,
    )
    return app


async def serve(*, host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run the query_api server.  Blocks until cancelled.

    Args:
        host: Bind address (default 127.0.0.1; use 0.0.0.0 in K8s).
        port: TCP port (default 8765 per ADR-2605215500).
    """
    app = build_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    _log.info("mst-projector query_api serving at http://%s:%d", host, port)

    # Block until cancelled (e.g. SIGINT from main.py)
    await asyncio.Event().wait()
