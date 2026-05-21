"""yukkuri `listVideos` graph — read-only DB query.

NSID: ai.gftd.apps.yukkuri.listVideos
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_yukkuri.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_APP_DID = os.environ.get("YUKKURI_APP_DID", "did:web:yukkuri.gftd.ai")


class _State(TypedDict, total=False):
    owner_did: str | None
    status: str | None      # optional filter (queued/script/assembled/...)
    limit: int
    offset: int
    videos: list[dict[str, Any]]
    total: int
    error: str | None


async def _node_query(state: _State) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set", "videos": []}
    limit = max(1, min(200, int(state.get("limit") or 50)))
    offset = max(0, int(state.get("offset") or 0))
    owner = state.get("owner_did")
    status_filter = state.get("status")
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            params: list[Any] = []
            where_parts = []
            if owner:
                where_parts.append("owner_did = %s")
                params.append(owner)
            if status_filter:
                where_parts.append("status = %s")
                params.append(status_filter)
            where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
            await cur.execute(
                f"""
                SELECT video_id, owner_did, topic, status, render_url, created_at
                FROM vertex_yukkuri_video
                {where}
                ORDER BY created_at DESC
                LIMIT {int(limit)} OFFSET {int(offset)}
                """,
                params,
            )
            rows = await cur.fetchall()
        finally:
            await conn.close()
    except Exception as exc:  # noqa: BLE001
        _log.exception("list_videos query failed")
        return {"error": f"query: {exc!s}"[:300], "videos": []}

    videos = [
        {
            "videoId": row[0],
            "ownerDid": row[1],
            "topic": row[2],
            "status": row[3],
            "renderUrl": row[4],
            "createdAt": str(row[5] or ""),
        }
        for row in rows
    ]
    return {"videos": videos, "total": len(videos)}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="yukkuri.listVideos",
        object_id=f"listVideos:{int(time.time())}",
        object_type="yukkuri.video",
        attributes={"returned": int(state.get("total", 0))},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("query", _node_query, retry_policy=RetryPolicy(max_attempts=3, backoff_factor=1.5))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "query")
    g.add_edge("query", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="list_videos")
