"""yukkuri `renderVideo` graph — timeline JSON → dougaka render pod → mp4.

NSID: com.etzhayyim.apps.yukkuri.renderVideo

Actor: did:web:yukkuri.etzhayyim.com:actor:renderer

Calls lg-dougaka (ComfyUI image-per-scene + ffmpeg mux render service).
  POST {DOUGAKA_XRPC_URL}/xrpc/com.etzhayyim.apps.dougaka.render
    {videoId: "...", timeline: {...}}
  → {blobKey: "...", blobUrl: "..."}

lg-dougaka: ComfyUI /v1/images/generations per scene → ffmpeg mp4 → B2 upload.

Advances video status → 'rendered'.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_yukkuri.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_DOUGAKA_XRPC_URL = os.environ.get(
    "DOUGAKA_XRPC_URL", "http://lg-dougaka.mitama-udf.svc.cluster.local:8000"
).rstrip("/")
_RENDER_TIMEOUT = float(os.environ.get("RENDER_TIMEOUT_SEC", "600"))
_APP_DID = os.environ.get("YUKKURI_APP_DID", "did:web:yukkuri.etzhayyim.com")
_RENDERER_DID = os.environ.get(
    "YUKKURI_RENDERER_DID", "did:web:yukkuri.etzhayyim.com:actor:renderer"
)


class _State(TypedDict, total=False):
    video_id: str
    # output
    timeline_json: str | None
    render_blob_key: str | None
    render_url: str | None
    error: str | None


async def _node_build_timeline(state: _State) -> dict[str, Any]:
    """Assemble timeline JSON from scenes + lines + assets in kotoba.

    RisingWave streaming INSERT may not be visible immediately; poll up to 60 s.
    """
    import asyncio

    video_id = state.get("video_id") or ""
    if not video_id:
        return {"error": "video_id required"}

    scenes: list[dict] = []
    lines: list[dict] = []
    assets: list[dict] = []

    deadline = time.monotonic() + 60.0
    while time.monotonic() < deadline:
        try:
            from kotodama.kotoba_datomic import get_kotoba_client
            client = get_kotoba_client()
            raw_scenes = await asyncio.to_thread(client.select_where, "vertex_yukkuri_scene", "video_id", video_id, limit=20)
            raw_scenes.sort(key=lambda r: int(r.get("scene_index") or 0))
            scenes = [{"index": int(r.get("scene_index") or 0), "location": r.get("location"), "action": r.get("action")} for r in raw_scenes]
            
            if scenes:
                raw_lines = await asyncio.to_thread(client.select_where, "vertex_yukkuri_line", "video_id", video_id, limit=500)
                raw_lines.sort(key=lambda r: (int(r.get("scene_index") or 0), int(r.get("line_index") or 0)))
                lines = [{"sceneIndex": int(r.get("scene_index") or 0), "lineIndex": int(r.get("line_index") or 0), "speaker": r.get("speaker"),
                          "text": r.get("text"), "emotion": r.get("emotion"), "voiceBlobKey": r.get("voice_blob_key")}
                         for r in raw_lines]
                
                raw_assets = await asyncio.to_thread(client.select_where, "vertex_yukkuri_asset", "video_id", video_id, limit=100)
                assets = []
                for r in raw_assets:
                    try:
                        meta = json.loads(r.get("meta_json") or "{}")
                    except Exception:
                        meta = {}
                    assets.append({"kind": r.get("kind"), "blobKey": r.get("blob_key"), "meta": meta})
        except Exception as exc:  # noqa: BLE001
            _log.warning("build_timeline query failed: %s", exc)

        if scenes:
            break
        _log.info("build_timeline: scenes not visible yet for %s, retrying…", video_id)
        await asyncio.sleep(5)

    if not scenes:
        return {"error": f"build_timeline: no scenes visible after 60 s for video_id={video_id}"}

    timeline = {
        "videoId": video_id,
        "scenes": scenes,
        "lines": lines,
        "assets": assets,
        "format": "mp4",
        "resolution": "1280x720",
        "fps": 30,
    }
    return {"timeline_json": json.dumps(timeline)}


async def _node_render(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("timeline_json"):
        return {}
    video_id = state.get("video_id") or ""
    try:
        async with httpx.AsyncClient(timeout=_RENDER_TIMEOUT) as client:
            r = await client.post(
                f"{_DOUGAKA_XRPC_URL}/xrpc/com.etzhayyim.apps.dougaka.render",
                json={"video_id": video_id, "timeline": json.loads(state["timeline_json"])},
                headers={"Content-Type": "application/json"},
            )
        if r.status_code >= 400:
            return {"error": f"dougaka render {r.status_code}: {r.text[:300]}"}
        data = r.json()
        blob_key = data.get("blob_key") or data.get("blobKey") or ""
        render_url = data.get("blob_url") or data.get("blobUrl") or data.get("url") or ""
        if not blob_key:
            return {"error": f"dougaka render returned no blobKey: {data}"}
        return {"render_blob_key": blob_key, "render_url": render_url}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"dougaka render: {exc!s}"[:300]}


async def _node_update_status(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("render_blob_key"):
        return {}
    video_id = state.get("video_id") or ""
    try:
        import asyncio
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        raw_rows = await asyncio.to_thread(client.select_where, "vertex_yukkuri_video", "video_id", video_id)
        if raw_rows:
            row = raw_rows[0]
            row["status"] = "rendered"
            row["render_blob_key"] = state["render_blob_key"]
            row["render_url"] = state.get("render_url")
            await asyncio.to_thread(client.insert_row, "vertex_yukkuri_video", row)
    except Exception as exc:  # noqa: BLE001
        _log.exception("update status rendered failed")
        return {"error": f"update: {exc!s}"[:300]}
    return {}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_RENDERER_DID,
        activity="yukkuri.renderVideo",
        object_id=f"render:{state.get('video_id', '')}:{int(time.time())}",
        object_type="yukkuri.render",
        attributes={
            "videoId": state.get("video_id"),
            "blobKey": state.get("render_blob_key"),
            "ok": not bool(state.get("error")),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("build_timeline", _node_build_timeline, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("render", _node_render, retry_policy=RetryPolicy(max_attempts=2, backoff_factor=5.0))
    g.add_node("update_status", _node_update_status, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "build_timeline")
    g.add_edge("build_timeline", "render")
    g.add_edge("render", "update_status")
    g.add_edge("update_status", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="render_video")
