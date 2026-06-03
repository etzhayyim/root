"""animeka `listEpisodes` graph — list episodes by work.

NSID: com.etzhayyim.animeka.listEpisodes
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


def _rkey_from_id(val: str) -> str:
    if val.startswith("at://"):
        return val.rstrip("/").rsplit("/", 1)[-1]
    return val


class _ListEpisodesState(TypedDict, total=False):
    work_id: str
    status: str | None
    limit: int
    offset: int
    items: list[dict[str, Any]]
    total: int
    error: str | None


async def _node_query(state: _ListEpisodesState) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set", "items": [], "total": 0}
    work_id = state.get("work_id") or ""
    if not work_id:
        return {"error": "work_id is required", "items": [], "total": 0}

    work_rkey = _rkey_from_id(work_id)
    limit = max(1, min(200, int(state.get("limit") or 50)))
    offset = max(0, int(state.get("offset") or 0))
    status_filter = state.get("status")

    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()

            # Resolve work vertex_id from rkey
            await cur.execute(
                """
                SELECT vertex_id FROM vertex_animeka
                WHERE collection = 'com.etzhayyim.animeka.work' AND rkey = %s
                LIMIT 1
                """,
                [work_rkey],
            )
            work_row = await cur.fetchone()
            work_vertex_id = work_row[0] if work_row else work_rkey

            params: list[Any] = [work_vertex_id]
            where = "work_id = %s AND collection = 'com.etzhayyim.animeka.episode'"
            if status_filter:
                where += " AND status = %s"
                params.append(status_filter)

            await cur.execute(
                f"""
                SELECT vertex_id, rkey, episode_num, title, status,
                       duration_sec, fps, thumb_cid, created_at
                FROM vertex_animeka
                WHERE {where}
                ORDER BY COALESCE(episode_num, 0) ASC
                LIMIT {int(limit)} OFFSET {int(offset)}
                """,
                params,
            )
            rows = await cur.fetchall()

            # Count cut progress per episode in one pass
            if rows:
                ep_vertex_ids = [r[0] for r in rows]
                placeholders = ", ".join(["%s"] * len(ep_vertex_ids))
                await cur.execute(
                    f"""
                    SELECT episode_id, COUNT(*) AS cut_count
                    FROM vertex_animeka
                    WHERE collection = 'com.etzhayyim.animeka.cut'
                      AND episode_id IN ({placeholders})
                    GROUP BY episode_id
                    LIMIT 200
                    """,
                    ep_vertex_ids,
                )
                cut_count_rows = await cur.fetchall()
                cut_counts = {r[0]: int(r[1]) for r in cut_count_rows}
            else:
                cut_counts = {}

        finally:
            await conn.close()

    except Exception as exc:  # noqa: BLE001
        _log.exception("list_episodes query failed")
        return {"error": f"query: {exc!s}"[:300], "items": [], "total": 0}

    items: list[dict[str, Any]] = []
    for row in rows:
        vertex_id, rkey, ep_num, title, st, dur, fps, thumb, created_at = row
        items.append({
            "uri": vertex_id,
            "rkey": rkey,
            "episodeNum": int(ep_num) if ep_num is not None else None,
            "titleJP": title,
            "status": st,
            "durationSec": float(dur) if dur is not None else None,
            "fps": int(fps) if fps is not None else None,
            "thumbCid": thumb,
            "cutCount": cut_counts.get(vertex_id, 0),
            "createdAt": created_at,
        })

    return {"items": items, "total": len(items)}


async def _node_emit_audit(state: _ListEpisodesState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.listEpisodes",
        object_id=f"listEpisodes:{int(time.time())}",
        object_type="animeka.episode",
        attributes={
            "workId": state.get("work_id") or "",
            "limit": int(state.get("limit") or 50),
            "offset": int(state.get("offset") or 0),
            "returned": int(state.get("total", 0)),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_ListEpisodesState)
    g.add_node("query", _node_query,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=1.5))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "query")
    g.add_edge("query", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="list_episodes")
