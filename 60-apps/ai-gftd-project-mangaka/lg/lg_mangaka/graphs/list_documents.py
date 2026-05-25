"""mangaka `list_documents` graph — listing for app.etzhayyim.mangaka.listDocuments.

Returns the catalog of mangaka documents stored in vertex_mangaka.
Optionally filter by convoId. Always returns offset/limit/total per
60-apps/CLAUDE.md pagination convention.

Input:
    convoId  str (optional)
    limit    int (default 50, max 200)
    offset   int (default 0)
Output:
    items    list[{ docId, name, vertexId, createdAt }]
    total    int
    offset   int
    limit    int
"""

from __future__ import annotations

import logging
import os
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

_log = logging.getLogger(__name__)

_APP_DID = os.environ.get("MANGAKA_APP_DID", "did:web:mangaka.etzhayyim.com")
_NSID = "app.etzhayyim.mangaka.document"
_RW_URL = os.environ.get("RW_URL", "")


class _ListState(TypedDict, total=False):
    convo_id: str
    convoId: str
    limit: int
    offset: int
    items: list[dict[str, Any]]
    total: int
    error: str | None


async def _node_list(state: _ListState) -> dict[str, Any]:
    if not _RW_URL:
        return {"items": [], "total": 0, "error": "RW_URL not configured"}

    limit = max(1, min(200, int(state.get("limit") or 50)))
    offset = max(0, int(state.get("offset") or 0))
    where = ["kind = 'document'", "collection = %s"]
    params: list[Any] = [_NSID]

    convo_id = (state.get("convo_id") or state.get("convoId") or "").strip()
    if convo_id:
        where.append("props LIKE %s")
        params.append(f'%"convoId":"{convo_id}"%')

    where_sql = " AND ".join(where)
    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                f"SELECT COUNT(*) FROM vertex_mangaka WHERE {where_sql}",
                tuple(params),
            )
            row = await cur.fetchone()
            total = int(row[0] or 0) if row else 0

            await cur.execute(
                f"""
                SELECT rkey, name, vertex_id, created_at
                FROM vertex_mangaka
                WHERE {where_sql}
                ORDER BY created_at DESC, rkey ASC
                LIMIT {limit} OFFSET {offset}
                """,
                tuple(params),
            )
            rows = await cur.fetchall()
        finally:
            await conn.close()
    except Exception as exc:  # noqa: BLE001
        _log.exception("list_documents query failed")
        return {"items": [], "total": 0, "error": f"{type(exc).__name__}: {exc!s}"[:300]}

    items = [
        {
            "docId": r[0],
            "name": r[1] or r[0],
            "vertexId": r[2],
            "createdAt": r[3] or "",
        }
        for r in rows
    ]
    return {"items": items, "total": total, "offset": offset, "limit": limit, "error": None}


def _build():
    g: StateGraph = StateGraph(_ListState)
    g.add_node("list", _node_list)
    g.add_edge(START, "list")
    g.add_edge("list", END)
    return g


GRAPH = _build().compile(name="list_documents")
