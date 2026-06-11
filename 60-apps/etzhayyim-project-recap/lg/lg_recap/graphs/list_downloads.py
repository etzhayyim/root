"""recap `listDownloads` graph -- paginated download history.

NSID: com.etzhayyim.apps.recap.listDownloads
"""
from __future__ import annotations

import logging
import os
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

_log = logging.getLogger(__name__)
_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")


class _ListDownloadsState(TypedDict, total=False):
    platform: str | None
    status: str | None
    limit: int
    offset: int
    items: list[dict[str, Any]]
    error: str | None


async def _node_query(state: _ListDownloadsState) -> dict[str, Any]:
    if not _RW_URL:
        return {"items": [], "error": "RW_URL not set"}
    limit = max(1, min(200, int(state.get("limit") or 50)))
    offset = max(0, int(state.get("offset") or 0))
    where = []
    params: list[Any] = []
    if state.get("platform"):
        where.append("platform = %s")
        params.append(state["platform"])
    if state.get("status"):
        where.append("status = %s")
        params.append(state["status"])
    where_sql = "WHERE " + " AND ".join(where) if where else ""
    params.extend([limit, offset])
    try:
        import psycopg

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                f"""
                SELECT vertex_id, source_url, platform, title, duration_sec,
                       blob_key, blob_size_bytes, status, scope, created_at
                  FROM vertex_recap_download
                  {where_sql}
                 ORDER BY created_at DESC
                 LIMIT %s OFFSET %s
                """,
                params,
            )
            rows = await cur.fetchall()
        finally:
            await conn.close()
    except Exception as exc:
        _log.exception("list_downloads failed")
        return {"items": [], "error": str(exc)[:300]}
    return {
        "items": [
            {
                "uri": r[0],
                "url": r[1],
                "platform": r[2],
                "title": r[3],
                "durationSec": r[4],
                "blobKey": r[5],
                "blobSizeBytes": r[6],
                "status": r[7],
                "scope": r[8],
                "createdAt": r[9],
            }
            for r in rows
        ],
        "limit": limit,
        "offset": offset,
    }


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_ListDownloadsState)
    g.add_node("query", _node_query,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=1.5))
    g.add_edge(START, "query")
    g.add_edge("query", END)
    return g


GRAPH = _build().compile(name="list_downloads")
