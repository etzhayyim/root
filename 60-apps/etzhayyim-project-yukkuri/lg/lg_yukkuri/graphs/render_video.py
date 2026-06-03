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

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
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
    """Assemble timeline JSON from scenes + lines + assets in RW.

    RisingWave streaming INSERT may not be visible immediately; poll up to 60 s.
    """
    import asyncio

    video_id = state.get("video_id") or ""
    if not video_id:
        return {"error": "video_id required"}
    if not _RW_URL:
        return {"error": "RW_URL not set"}

    scenes: list[dict] = []
    lines: list[dict] = []
    assets: list[dict] = []

    deadline = time.monotonic() + 60.0
    while time.monotonic() < deadline:
        try:
            import psycopg
            conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
            try:
                cur = conn.cursor()
                await cur.execute(
                    "SELECT scene_index, location, action FROM vertex_yukkuri_scene "
                    "WHERE video_id = %s ORDER BY scene_index LIMIT 20",
                    [video_id],
                )
                scenes = [{"index": r[0], "location": r[1], "action": r[2]}
                          for r in await cur.fetchall()]
                if scenes:
                    # lines with voice blobs
                    await cur.execute(
                        "SELECT scene_index, line_index, speaker, text, emotion, voice_blob_key "
                        "FROM vertex_yukkuri_line WHERE video_id = %s "
                        "ORDER BY scene_index, line_index LIMIT 500",
                        [video_id],
                    )
                    lines = [{"sceneIndex": r[0], "lineIndex": r[1], "speaker": r[2],
                              "text": r[3], "emotion": r[4], "voiceBlobKey": r[5]}
                             for r in await cur.fetchall()]
                    # assets
                    await cur.execute(
                        "SELECT kind, blob_key, meta_json FROM vertex_yukkuri_asset "
                        "WHERE video_id = %s LIMIT 100",
                        [video_id],
                    )
                    assets = [{"kind": r[0], "blobKey": r[1],
                               "meta": json.loads(r[2] or "{}")}
                              for r in await cur.fetchall()]
            finally:
                await conn.close()
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
    if not _RW_URL:
        return {}
    video_id = state.get("video_id") or ""
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            await conn.execute(
                """UPDATE vertex_yukkuri_video
                   SET status = 'rendered', render_blob_key = %s, render_url = %s
                   WHERE video_id = %s""",
                [state["render_blob_key"], state.get("render_url"), video_id],
            )
        finally:
            await conn.close()
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
