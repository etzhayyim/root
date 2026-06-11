"""animeka `listCuts` graph — list cuts by episode (or work).

NSID: com.etzhayyim.animeka.listCuts

Query params:
  episodeId  (optional) filter by episode rkey
  workId     (optional) filter by work rkey (returns all cuts across episodes)
  stage      (optional) filter by cut stage string
  limit      default 200, max 500
  offset     default 0
"""

from __future__ import annotations

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


class _State(TypedDict, total=False):
    episode_id: str | None
    work_id: str | None
    stage: str | None
    limit: int
    offset: int
    # output
    items: list[dict[str, Any]]
    total: int
    error: str | None


async def _node_query(state: _State) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set", "items": [], "total": 0}

    episode_id = state.get("episode_id") or ""
    work_id = state.get("work_id") or ""
    stage_filter = state.get("stage") or ""
    limit = max(1, min(500, int(state.get("limit") or 200)))
    offset = max(0, int(state.get("offset") or 0))

    try:
        import psycopg

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()

            where_parts = ["collection = 'com.etzhayyim.animeka.cut'"]
            params: list[Any] = []

            if episode_id:
                ep_rkey = _rkey_from_id(episode_id)
                # Match by episode_id column (stored as rkey OR vertex_id)
                where_parts.append("(episode_id = %s OR episode_id LIKE %s)")
                params += [ep_rkey, f"%/{ep_rkey}"]

            if work_id and not episode_id:
                work_rkey = _rkey_from_id(work_id)
                where_parts.append("(work_id = %s OR work_id LIKE %s)")
                params += [work_rkey, f"%/{work_rkey}"]

            if stage_filter:
                where_parts.append("stage = %s")
                params.append(stage_filter)

            where = " AND ".join(where_parts)

            await cur.execute(
                f"""
                SELECT vertex_id, rkey, cut_num, duration_frames, fps,
                       priority, camera_note, stage, stage_status,
                       episode_id, work_id, thumb_cid, image_cid, created_at
                FROM vertex_animeka
                WHERE {where}
                ORDER BY COALESCE(cut_num, 0) ASC
                LIMIT {int(limit)} OFFSET {int(offset)}
                """,
                params,
            )
            rows = await cur.fetchall()

        finally:
            await conn.close()

    except Exception as exc:
        _log.exception("list_cuts query failed")
        return {"error": f"query: {exc!s}"[:300], "items": [], "total": 0}

    items: list[dict[str, Any]] = []
    for row in rows:
        (vertex_id, rkey, cut_num, dur_frames, fps, priority,
         camera_note, stage, stage_status, ep_id, wk_id,
         thumb_cid, image_cid, created_at) = row
        items.append({
            "uri": vertex_id,
            "rkey": rkey,
            "cutNum": int(cut_num) if cut_num is not None else None,
            "cut_num": int(cut_num) if cut_num is not None else None,
            "durationFrames": int(dur_frames) if dur_frames is not None else None,
            "duration_frames": int(dur_frames) if dur_frames is not None else None,
            "fps": int(fps) if fps is not None else 24,
            "priority": priority,
            "dialogueSummary": camera_note,
            "dialogue_summary": camera_note,
            "stage": stage,
            "stageStatus": stage_status,
            "stage_status": stage_status,
            "episodeId": ep_id,
            "workId": wk_id,
            "thumbCid": thumb_cid,
            "imageCid": image_cid,
            "createdAt": created_at,
        })

    return {"items": items, "total": len(items)}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.listCuts",
        object_id=f"listCuts:{int(time.time())}",
        object_type="animeka.cut",
        attributes={
            "episodeId": state.get("episode_id") or "",
            "workId": state.get("work_id") or "",
            "limit": int(state.get("limit") or 200),
            "offset": int(state.get("offset") or 0),
            "returned": int(state.get("total") or 0),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("query", _node_query,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=1.5))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "query")
    g.add_edge("query", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="list_cuts")
