"""dougaka `render` graph — timeline JSON → video_compose SDK → mp4 → B2.

NSID: com.etzhayyim.apps.dougaka.render

Pipeline (video_compose SDK, replaces ComfyUI):
  1. render         — video_compose.render_video(): TTS + image gen + PIL compositor + ffmpeg
  2. upload_video   — boto3 PUT to B2 under renders/{videoId}/output.mp4
  3. write_record   — psycopg INSERT vertex_dougaka_render
  4. cleanup        — remove temp files
  5. audit          — fire-and-forget OCEL event

Env vars:
  MURAKUMO_TTS_URL        kokoro TTS endpoint (default RunPod pod)
  MURAKUMO_IMAGE_URL      flux-schnell image gen endpoint (default RunPod pod)
  B2_ENDPOINT_URL         https://s3.us-west-004.backblazeb2.com
  B2_BUCKET_MEDIA         etzhayyim-nats
  B2_KEY_ID / B2_APPLICATION_KEY
  BLOB_REPO               defaults to yukkuri.etzhayyim.com
  RW_URL                  psycopg DSN for RisingWave
  RENDER_TIMEOUT_SEC      defaults to 600
  DOUGAKA_APP_DID         defaults to did:web:dougaka.etzhayyim.com
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import tempfile
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_dougaka.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_MURAKUMO_TTS_URL = os.environ.get(
    "MURAKUMO_TTS_URL",
    "https://vyp99t9px7h4dl-4000.proxy.runpod.net/v1/audio/speech",
)
_MURAKUMO_IMAGE_URL = os.environ.get(
    "MURAKUMO_IMAGE_URL",
    "https://vyp99t9px7h4dl-4000.proxy.runpod.net/v1/images/generations",
)
_B2_ENDPOINT_URL = os.environ.get("B2_ENDPOINT_URL", "https://s3.us-west-004.backblazeb2.com")
_B2_BUCKET = os.environ.get("B2_BUCKET_MEDIA", "etzhayyim-nats")
_B2_KEY_ID = os.environ.get("B2_KEY_ID", "")
_B2_APP_KEY = os.environ.get("B2_APPLICATION_KEY", "")
_BLOB_REPO = os.environ.get("BLOB_REPO", "yukkuri.etzhayyim.com")
_RENDER_TIMEOUT = float(os.environ.get("RENDER_TIMEOUT_SEC", "600"))
_APP_DID = os.environ.get("DOUGAKA_APP_DID", "did:web:dougaka.etzhayyim.com")


class _State(TypedDict, total=False):
    video_id: str
    timeline: dict[str, Any]
    temp_dir: str | None
    output_mp4: str | None
    blob_key: str | None
    blob_url: str | None
    error: str | None


def _b2_client():
    import boto3
    from botocore.config import Config
    return boto3.client(
        "s3",
        endpoint_url=_B2_ENDPOINT_URL,
        aws_access_key_id=_B2_KEY_ID,
        aws_secret_access_key=_B2_APP_KEY,
        config=Config(signature_version="s3v4"),
    )


def _build_scenes_for_compose(timeline: dict[str, Any]) -> list[dict[str, Any]]:
    """Reconstruct nested scene+lines structure for video_compose.render_video."""
    raw_scenes = timeline.get("scenes") or []
    raw_lines = timeline.get("lines") or []

    # group lines by scene_index
    lines_by_scene: dict[int, list[dict]] = {}
    for line in raw_lines:
        si = line.get("scene_index") or line.get("sceneIndex") or 0
        lines_by_scene.setdefault(si, []).append(line)

    scenes = []
    for scene in raw_scenes:
        idx = scene.get("index") or scene.get("scene_index") or 0
        scene_lines = sorted(
            lines_by_scene.get(idx, []),
            key=lambda l: l.get("line_index") or l.get("lineIndex") or 0,
        )
        composed_lines = [
            {
                "speaker": l.get("speaker", "left"),
                "text": l.get("text", ""),
                "emotion": l.get("emotion", "normal"),
            }
            for l in scene_lines
        ]
        scenes.append({
            "location": scene.get("location", ""),
            "action": scene.get("action", ""),
            "lines": composed_lines,
        })
    return scenes


async def _node_render(state: _State) -> dict[str, Any]:
    """Use video_compose SDK: TTS + image gen + PIL compositor + ffmpeg → mp4."""
    if state.get("error"):
        return {}
    timeline = state.get("timeline") or {}
    if not timeline:
        return {"error": "timeline is empty"}

    temp_dir = tempfile.mkdtemp(prefix="dougaka_")
    output_mp4 = os.path.join(temp_dir, "output.mp4")

    scenes = _build_scenes_for_compose(timeline)
    if not scenes:
        return {"error": "no scenes in timeline", "temp_dir": temp_dir}

    try:
        from kotodama.video_compose.renderer import render_video
        await render_video(
            scenes,
            output_mp4,
            tts_url=_MURAKUMO_TTS_URL,
            image_url=_MURAKUMO_IMAGE_URL,
        )
    except Exception as exc:
        _log.exception("render_video failed")
        return {"error": f"render: {exc!s}"[:400], "temp_dir": temp_dir}

    if not os.path.exists(output_mp4):
        return {"error": "render produced no output file", "temp_dir": temp_dir}

    _log.info("render_video done: %s (%d KB)", output_mp4, os.path.getsize(output_mp4) // 1024)
    return {"temp_dir": temp_dir, "output_mp4": output_mp4}


async def _node_upload_video(state: _State) -> dict[str, Any]:
    """Upload output.mp4 to B2 under renders/{video_id}/output.mp4."""
    if state.get("error") or not state.get("output_mp4"):
        return {}
    if not (_B2_KEY_ID and _B2_APP_KEY):
        _log.warning("B2 credentials not set — skipping upload")
        return {"blob_key": "", "blob_url": ""}

    video_id = state.get("video_id") or "unknown"
    mp4_path = state["output_mp4"]
    b2_key = f"renders/{video_id}/output.mp4"

    try:
        sha256 = hashlib.sha256()
        with open(mp4_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)

        import asyncio
        import concurrent.futures
        loop = asyncio.get_running_loop()
        s3 = _b2_client()

        def _upload():
            s3.upload_file(mp4_path, _B2_BUCKET, b2_key, ExtraArgs={"ContentType": "video/mp4"})
            return s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": _B2_BUCKET, "Key": b2_key},
                ExpiresIn=604800,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            presigned_url = await loop.run_in_executor(pool, _upload)

        blob_url = presigned_url or f"{_B2_ENDPOINT_URL}/{_B2_BUCKET}/{b2_key}"
        _log.info("uploaded %s → %s (sha256=%s)", mp4_path, b2_key, sha256.hexdigest()[:16])
        return {"blob_key": b2_key, "blob_url": blob_url}
    except Exception as exc:
        _log.exception("upload_video failed")
        return {"error": f"upload: {exc!s}"[:300]}


async def _node_write_record(state: _State) -> dict[str, Any]:
    """INSERT vertex_dougaka_render row in kotoba."""
    video_id = state.get("video_id") or ""
    blob_key = state.get("blob_key") or ""
    blob_url = state.get("blob_url") or ""
    status = "error" if state.get("error") else "done"
    error_msg = state.get("error") or ""
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    vertex_id = f"at://dougaka.etzhayyim.com/com.etzhayyim.apps.dougaka.render/{video_id}"

    try:
        from kotodama.kotoba_datomic import get_kotoba_client
        import asyncio
        client = get_kotoba_client()
        await asyncio.to_thread(client.insert_row, "vertex_dougaka_render", {
            "vertex_id": vertex_id,
            "video_id": video_id,
            "actor_did": _APP_DID,
            "org_did": "anon",
            "blob_key": blob_key,
            "blob_url": blob_url,
            "status": status,
            "error_msg": error_msg[:500] if error_msg else "",
            "created_at": created_at
        })
    except Exception as exc:
        _log.warning("write_record non-fatal: %s", exc)
    return {}


async def _node_cleanup(state: _State) -> dict[str, Any]:
    """Remove temp directory."""
    temp_dir = state.get("temp_dir")
    if temp_dir and os.path.isdir(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except Exception as exc:
            _log.warning("cleanup temp_dir failed: %s", exc)
    return {}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="dougaka.render",
        object_id=f"render:{state.get('video_id', '')}:{int(time.time())}",
        object_type="dougaka.render",
        attributes={
            "videoId": state.get("video_id"),
            "blobKey": state.get("blob_key"),
            "ok": not bool(state.get("error")),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("render", _node_render, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("upload_video", _node_upload_video, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("write_record", _node_write_record, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("cleanup", _node_cleanup)
    g.add_node("audit", _node_audit)
    g.add_edge(START, "render")
    g.add_edge("render", "upload_video")
    g.add_edge("upload_video", "write_record")
    g.add_edge("write_record", "cleanup")
    g.add_edge("cleanup", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="render")
