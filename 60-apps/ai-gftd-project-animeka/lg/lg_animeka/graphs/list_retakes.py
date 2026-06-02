"""animeka `listRetakes` graph — list retakes with multi-axis filtering.

NSID: com.etzhayyim.animeka.listRetakes
"""
import logging
import os
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_animeka.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_DEFAULT_APP_DID = os.environ.get("ANIMEKA_APP_DID", "did:web:animeka.etzhayyim.com")


class _ListRetakesState(TypedDict, total=False):
    episode_id: str | None
    cut_id: str | None
    stage: str | None
    status: str | None
    assignee: str | None
    limit: int
    offset: int
    items: list[dict[str, Any]]
    total: int
    error: str | None


def _rkey_from_id(val: str) -> str:
    if val.startswith("at://"):
        return val.rstrip("/").rsplit("/", 1)[-1]
    return val


async def _node_query(state: _ListRetakesState) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set", "items": [], "total": 0}

    limit = max(1, min(200, int(state.get("limit") or 50)))
    offset = max(0, int(state.get("offset") or 0))

    episode_id = state.get("episode_id")
    cut_id = state.get("cut_id")
    stage = state.get("stage")
    status = state.get("status") or "open"
    assignee = state.get("assignee")

    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()

            params: list[Any] = ["com.etzhayyim.animeka.retake"]
            where_parts = ["collection = %s"]

            if episode_id:
                ep_rkey = _rkey_from_id(episode_id)
                # Resolve episode vertex_id
                await cur.execute(
                    """SELECT vertex_id FROM vertex_animeka
                       WHERE collection='com.etzhayyim.animeka.episode' AND rkey=%s LIMIT 1""",
                    [ep_rkey],
                )
                ep_row = await cur.fetchone()
                ep_vid = ep_row[0] if ep_row else ep_rkey
                where_parts.append("episode_id = %s")
                params.append(ep_vid)

            if cut_id:
                cut_rkey = _rkey_from_id(cut_id)
                await cur.execute(
                    """SELECT vertex_id FROM vertex_animeka
                       WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s LIMIT 1""",
                    [cut_rkey],
                )
                cut_row = await cur.fetchone()
                cut_vid = cut_row[0] if cut_row else cut_rkey
                where_parts.append("cut_id = %s")
                params.append(cut_vid)

            if stage:
                where_parts.append("stage = %s")
                params.append(stage)

            if status:
                where_parts.append("COALESCE(status, 'open') = %s")
                params.append(status)

            if assignee:
                where_parts.append("assignees LIKE %s")
                params.append(f"%{assignee}%")

            where = " AND ".join(where_parts)
            await cur.execute(
                f"""
                SELECT vertex_id, rkey, target_uri, cut_id,
                       stage, severity, COALESCE(status,'open'),
                       comment, timecode_frame, author, assignees,
                       created_at
                FROM vertex_animeka
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT {int(limit)} OFFSET {int(offset)}
                """,
                params,
            )
            rows = await cur.fetchall()

        finally:
            await conn.close()

    except Exception as exc:  # noqa: BLE001
        _log.exception("list_retakes query failed")
        return {"error": f"query: {exc!s}"[:300], "items": [], "total": 0}

    items: list[dict[str, Any]] = [
        {
            "uri": r[0], "rkey": r[1], "targetUri": r[2],
            "cutUri": r[3], "stage": r[4], "severity": r[5],
            "status": r[6], "comment": r[7],
            "timecodeFrame": int(r[8]) if r[8] is not None else None,
            "author": r[9], "assignee": r[10], "createdAt": r[11],
        }
        for r in rows
    ]
    return {"items": items, "total": len(items)}


async def _node_emit_audit(state: _ListRetakesState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.listRetakes",
        object_id=f"listRetakes:{int(time.time())}",
        object_type="animeka.retake",
        attributes={
            "cutId": state.get("cut_id") or "",
            "episodeId": state.get("episode_id") or "",
            "status": state.get("status") or "open",
            "returned": int(state.get("total", 0)),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_ListRetakesState)
    g.add_node("query", _node_query,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=1.5))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "query")
    g.add_edge("query", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="list_retakes")
