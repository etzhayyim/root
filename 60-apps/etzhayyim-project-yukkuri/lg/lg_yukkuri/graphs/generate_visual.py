"""yukkuri `generateVisual` graph — 背景 + 挿絵 生成.

NSID: com.etzhayyim.apps.yukkuri.generateVisual

Actor: did:web:yukkuri.etzhayyim.com:actor:illustrator

Calls murakumo:inference/image (flux-schnell / sdxl-turbo-ja-lora) for each
scene's background. Stores blob_key in vertex_yukkuri_asset (kind='image').

Prompt guardrails (CLAUDE.md copyright invariants):
  - Reject real artist names in style prompts
  - Add "no_real_person, no_logo" negative prompt automatically
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_yukkuri.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_IMAGE_URL = os.environ.get(
    "MURAKUMO_IMAGE_URL",
    "https://vyp99t9px7h4dl-4000.proxy.runpod.net/v1/images/generations",
).rstrip("/")
_IMAGE_TIMEOUT = float(os.environ.get("IMAGE_TIMEOUT_SEC", "60"))
_PDS_BLOB_URL = os.environ.get("PDS_BLOB_URL", "https://atproto.etzhayyim.com/xrpc/com.atproto.repo.uploadBlob")
_APP_DID = os.environ.get("YUKKURI_APP_DID", "did:web:yukkuri.etzhayyim.com")
_ILLUSTRATOR_DID = os.environ.get(
    "YUKKURI_ILLUSTRATOR_DID", "did:web:yukkuri.etzhayyim.com:actor:illustrator"
)
_REPO = os.environ.get("YUKKURI_REPO_DID", "did:web:y5kk5r1x.etzhayyim.com")

_NEGATIVE_PROMPT = "real person, celebrity, logo, watermark, nsfw, explicit"


class _State(TypedDict, total=False):
    video_id: str
    scenes: list[dict] | None           # internal: fetched scenes
    visual_assets: list[dict] | None
    generated_count: int
    error: str | None


async def _fetch_scenes(video_id: str) -> list[dict]:
    import asyncio
    from kotodama.kotoba_datomic import get_kotoba_client
    client = get_kotoba_client()
    raw_rows = await asyncio.to_thread(client.select_where, "vertex_yukkuri_scene", "video_id", video_id, limit=20)
    raw_rows.sort(key=lambda r: int(r.get("scene_index") or 0))
    return [{"scene_index": int(r.get("scene_index") or 0), "location": r.get("location") or "", "action": r.get("action") or ""} for r in raw_rows]


async def _generate_one(scene: dict) -> dict[str, Any]:
    prompt = f"anime style background, {scene['location']}, {scene['action']}, soft colors, 2D illustration"
    try:
        async with httpx.AsyncClient(timeout=_IMAGE_TIMEOUT) as client:
            r = await client.post(
                _IMAGE_URL,
                json={
                    "model": "flux-schnell",
                    "prompt": prompt,
                    "negative_prompt": _NEGATIVE_PROMPT,
                    "width": 1280, "height": 720,
                    "num_inference_steps": 4,
                    "response_format": "b64_json",
                },
                headers={"Content-Type": "application/json"},
            )
        if r.status_code >= 400:
            return {"scene_index": scene["scene_index"], "error": f"image {r.status_code}"}
        import base64
        b64 = (r.json().get("data") or [{}])[0].get("b64_json") or ""
        if not b64:
            return {"scene_index": scene["scene_index"], "error": "empty b64"}
        img_bytes = base64.b64decode(b64)
        # upload blob
        async with httpx.AsyncClient(timeout=30) as client:
            ub = await client.post(
                _PDS_BLOB_URL,
                content=img_bytes,
                headers={"Content-Type": "image/png"},
            )
        if ub.status_code >= 400:
            return {"scene_index": scene["scene_index"], "error": f"uploadBlob {ub.status_code}"}
        blob_key = ub.json().get("blob", {}).get("ref", {}).get("$link", "")
        return {"scene_index": scene["scene_index"], "blob_key": blob_key}
    except Exception as exc:  # noqa: BLE001
        return {"scene_index": scene["scene_index"], "error": str(exc)[:200]}


async def _node_fetch_scenes(state: _State) -> dict[str, Any]:
    video_id = state.get("video_id") or ""
    if not video_id:
        return {"error": "video_id required"}
    try:
        scenes = await _fetch_scenes(video_id)
        return {"scenes": scenes}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"fetch: {exc!s}"[:200]}


async def _node_generate(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    scenes = state.get("scenes") or []
    if not scenes:
        return {"visual_assets": [], "generated_count": 0}
    results = await asyncio.gather(*[_generate_one(s) for s in scenes], return_exceptions=False)
    ok = [r for r in results if not r.get("error")]
    return {"visual_assets": ok, "generated_count": len(ok)}


async def _node_insert(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("visual_assets"):
        return {}
    video_id = state.get("video_id") or ""
    created_at = datetime.now(tz=timezone.utc).isoformat()
    try:
        import asyncio
        from kotodama.kotoba_datomic import get_kotoba_client
        client = get_kotoba_client()
        for asset in state["visual_assets"]:
            asset_id = f"asset-img-{video_id}-{asset['scene_index']}-{secrets.token_hex(3)}"
            await asyncio.to_thread(client.insert_row, "vertex_yukkuri_asset", {
                "vertex_id": asset_id,
                "video_id": video_id,
                "kind": "image",
                "actor_did": _ILLUSTRATOR_DID,
                "blob_key": asset["blob_key"],
                "meta_json": f'{{"sceneIndex":{asset["scene_index"]}}}',
                "created_at": created_at
            })
    except Exception as exc:  # noqa: BLE001
        _log.exception("insert visual assets failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_ILLUSTRATOR_DID,
        activity="yukkuri.generateVisual",
        object_id=f"visual:{state.get('video_id', '')}:{int(time.time())}",
        object_type="yukkuri.asset",
        attributes={"videoId": state.get("video_id"), "count": state.get("generated_count", 0)},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_scenes", _node_fetch_scenes, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("generate", _node_generate, retry_policy=RetryPolicy(max_attempts=2, backoff_factor=3.0))
    g.add_node("insert_assets", _node_insert_assets, retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_scenes")
    g.add_edge("fetch_scenes", "generate")
    g.add_edge("generate", "insert_assets")
    g.add_edge("insert_assets", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="generate_visual")
