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
    try:
        import asyncio
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        raw_rows = await asyncio.to_thread(client.select_where, "vertex_yukkuri_video", "video_id", video_id, limit=1)
        if not raw_rows:
            return {"error": f"video not found: {video_id}"}
        r = raw_rows[0]
        video = {
            "videoId": r.get("video_id"), "ownerDid": r.get("owner_did"), "topic": r.get("topic"),
            "outline": r.get("outline"), "status": r.get("status"),
            "renderUrl": r.get("render_url"), "renderBlobKey": r.get("render_blob_key"), "createdAt": str(r.get("created_at") or ""),
        }
        return {"video": video}
    except Exception as exc:  # noqa: BLE001
        _log.exception("fetch_video failed")
        return {"error": f"fetch: {exc!s}"[:300]}


async def _node_fetch_scenes(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("video"):
        return {}
    video_id = state.get("video_id") or ""
    try:
        import asyncio
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        raw_rows = await asyncio.to_thread(client.select_where, "vertex_yukkuri_scene", "video_id", video_id, limit=100)
        raw_rows.sort(key=lambda r: int(r.get("scene_index") or 0))
        return {"scenes": [{"sceneIndex": int(r.get("scene_index") or 0), "location": r.get("location"), "action": r.get("action")} for r in raw_rows]}
    except Exception as exc:  # noqa: BLE001
        _log.warning("fetch_scenes failed: %s", exc)
        return {"scenes": []}


async def _node_fetch_lines(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("video"):
        return {}
    video_id = state.get("video_id") or ""
    try:
        import asyncio
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        raw_rows = await asyncio.to_thread(client.select_where, "vertex_yukkuri_line", "video_id", video_id, limit=500)
        raw_rows.sort(key=lambda r: (int(r.get("scene_index") or 0), int(r.get("line_index") or 0)))
        return {"lines": [
            {"sceneIndex": int(r.get("scene_index") or 0), "lineIndex": int(r.get("line_index") or 0), "speaker": r.get("speaker"),
             "text": r.get("text"), "emotion": r.get("emotion"), "voiceBlobKey": r.get("voice_blob_key")}
            for r in raw_rows
        ]}
    except Exception as exc:  # noqa: BLE001
        _log.warning("fetch_lines failed: %s", exc)
        return {"lines": []}


async def _node_fetch_assets(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("video"):
        return {}
    video_id = state.get("video_id") or ""
    try:
        import asyncio
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        raw_rows = await asyncio.to_thread(client.select_where, "vertex_yukkuri_asset", "video_id", video_id, limit=200)
        raw_rows.sort(key=lambda r: str(r.get("created_at") or ""))
        return {"assets": [
            {"kind": r.get("kind"), "actorDid": r.get("actor_did"), "blobKey": r.get("blob_key"), "createdAt": str(r.get("created_at") or "")}
            for r in raw_rows
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
