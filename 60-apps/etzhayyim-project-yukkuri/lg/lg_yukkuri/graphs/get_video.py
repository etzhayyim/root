"""yukkuri `getVideo` graph — video detail with scenes + lines + assets.

NSID: com.etzhayyim.apps.yukkuri.getVideo
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
_APP_DID = os.environ.get("YUKKURI_APP_DID", "did:web:yukkuri.etzhayyim.com")


class _State(TypedDict, total=False):
    video_id: str
    video: dict[str, Any] | None
    scenes: list[dict[str, Any]]
    lines: list[dict[str, Any]]
    assets: list[dict[str, Any]]
    error: str | None


async def _node_fetch_video(state: _State) -> dict[str, Any]:
    video_id = state.get("video_id") or ""
    if not video_id:
        return {"error": "video_id required"}
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                """SELECT video_id, owner_did, topic, outline, status,
                          render_url, render_blob_key, created_at
                   FROM vertex_yukkuri_video WHERE video_id = %s LIMIT 1""",
                [video_id],
            )
            row = await cur.fetchone()
        finally:
            await conn.close()
        if not row:
            return {"error": f"video not found: {video_id}"}
        video = {
            "videoId": row[0], "ownerDid": row[1], "topic": row[2],
            "outline": row[3], "status": row[4],
            "renderUrl": row[5], "renderBlobKey": row[6], "createdAt": str(row[7] or ""),
        }
        return {"video": video}
    except Exception as exc:  # noqa: BLE001
        _log.exception("fetch_video failed")
        return {"error": f"fetch: {exc!s}"[:300]}


async def _node_fetch_scenes(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("video"):
        return {}
    video_id = state.get("video_id") or ""
    if not _RW_URL:
        return {}
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                """SELECT scene_index, location, action
                   FROM vertex_yukkuri_scene
                   WHERE video_id = %s
                   ORDER BY scene_index
                   LIMIT 100""",
                [video_id],
            )
            rows = await cur.fetchall()
        finally:
            await conn.close()
        return {"scenes": [{"sceneIndex": r[0], "location": r[1], "action": r[2]} for r in rows]}
    except Exception as exc:  # noqa: BLE001
        _log.warning("fetch_scenes failed: %s", exc)
        return {"scenes": []}


async def _node_fetch_lines(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("video"):
        return {}
    video_id = state.get("video_id") or ""
    if not _RW_URL:
        return {}
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                """SELECT scene_index, line_index, speaker, text, emotion, voice_blob_key
                   FROM vertex_yukkuri_line
                   WHERE video_id = %s
                   ORDER BY scene_index, line_index
                   LIMIT 500""",
                [video_id],
            )
            rows = await cur.fetchall()
        finally:
            await conn.close()
        return {"lines": [
            {"sceneIndex": r[0], "lineIndex": r[1], "speaker": r[2],
             "text": r[3], "emotion": r[4], "voiceBlobKey": r[5]}
            for r in rows
        ]}
    except Exception as exc:  # noqa: BLE001
        _log.warning("fetch_lines failed: %s", exc)
        return {"lines": []}


async def _node_fetch_assets(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("video"):
        return {}
    video_id = state.get("video_id") or ""
    if not _RW_URL:
        return {}
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                """SELECT kind, actor_did, blob_key, created_at
                   FROM vertex_yukkuri_asset
                   WHERE video_id = %s
                   ORDER BY created_at
                   LIMIT 200""",
                [video_id],
            )
            rows = await cur.fetchall()
        finally:
            await conn.close()
        return {"assets": [
            {"kind": r[0], "actorDid": r[1], "blobKey": r[2], "createdAt": str(r[3] or "")}
            for r in rows
        ]}
    except Exception as exc:  # noqa: BLE001
        _log.warning("fetch_assets failed: %s", exc)
        return {"assets": []}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="yukkuri.getVideo",
        object_id=f"video:{state.get('video_id', '')}:{int(time.time())}",
        object_type="yukkuri.video",
        attributes={"videoId": state.get("video_id"), "found": state.get("video") is not None},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_video", _node_fetch_video, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("fetch_scenes", _node_fetch_scenes, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("fetch_lines", _node_fetch_lines, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("fetch_assets", _node_fetch_assets, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_video")
    g.add_edge("fetch_video", "fetch_scenes")
    g.add_edge("fetch_scenes", "fetch_lines")
    g.add_edge("fetch_lines", "fetch_assets")
    g.add_edge("fetch_assets", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="get_video")
