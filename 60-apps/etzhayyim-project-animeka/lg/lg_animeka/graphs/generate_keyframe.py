"""animeka `generateKeyframe` graph — ComfyUI 1024×1024 anime keyframe image.

NSID: com.etzhayyim.animeka.generateKeyframe

Takes a cut_id and optional frame_num (default 1). Reads the visual
description from the layout record (or cut description). Renders a
cel-shaded keyframe via ComfyUI and inserts into vertex_animeka.
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
_REPO = os.environ.get("ANIMEKA_REPO_DID", "did:web:an1m3k4x.etzhayyim.com")
_CKPT = "animagine-xl-4.0.safetensors"

# Anime style suffix for high-quality character rendering
_ANIME_STYLE = (
    ", anime production cel art, full color illustration, vibrant cel shading, "
    "detailed shading and highlights, character on-model, expressive face, "
    "detailed eyes with catchlights, perfect anatomy, sharp focus, "
    "masterpiece, best quality, very aesthetic, absurdres, highres, newest, "
    "1girl or 1boy, solo, looking at viewer"
)
_NEGATIVE = (
    "lowres, worst quality, low quality, bad anatomy, bad hands, missing fingers, "
    "extra digit, fewer digits, cropped, text, signature, watermark, username, blurry, "
    "jpeg artifacts, ugly, duplicate, mutated, deformed, normal quality, monochrome, "
    "gray background, placeholder, solid color background, sketch, lineart only, "
    "unfinished, rough sketch, wireframe"
)


class _State(TypedDict, total=False):
    cut_id: str
    frame_num: int | None      # default 1
    visual_prompt: str | None  # override
    # output
    keyframe_id: str | None
    keyframe_uri: str | None
    blob_cid: str | None
    error: str | None


async def _node_fetch_prompt(state: _State) -> dict[str, Any]:
    """Fetch visual description from layout.description or cut.description."""
    if state.get("visual_prompt"):
        return {}
    cut_id = state.get("cut_id") or ""
    if not cut_id or not _RW_URL:
        return {}
    try:
        import psycopg
        rkey = cut_id.rsplit("/", 1)[-1] if "/" in cut_id else cut_id
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            # Prefer layout description (rich visual prompt from generate_layout)
            await cur.execute(
                """SELECT description FROM vertex_animeka
                   WHERE collection='com.etzhayyim.animeka.layout' AND cut_id=%s
                   ORDER BY created_at DESC LIMIT 1""",
                [cut_id],
            )
            row = await cur.fetchone()
            if not row or not row[0]:
                # Fallback to cut description
                await cur.execute(
                    "SELECT description FROM vertex_animeka "
                    "WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s LIMIT 1",
                    [rkey],
                )
                row = await cur.fetchone()
            if not row or not row[0]:
                # Final fallback: autopilot cuts store scene text in camera_note
                await cur.execute(
                    "SELECT camera_note FROM vertex_animeka "
                    "WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s LIMIT 1",
                    [rkey],
                )
                row = await cur.fetchone()
        finally:
            await conn.close()
        if row and row[0]:
            return {"visual_prompt": str(row[0])}
    except Exception as exc:
        _log.warning("fetch_prompt: %s", exc)
    return {}


async def _node_render(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    base_prompt = state.get("visual_prompt") or "anime character in scenic environment"
    full_prompt = base_prompt + _ANIME_STYLE
    try:
        from kotodama.primitives.shinshi_image import (
            _build_anime_workflow,
            _comfy_render_png,
            _upload_blob_to_pds,
        )
        workflow = _build_anime_workflow(full_prompt, _CKPT, 1024, 1024, 35)
        # Override negative prompt and increase CFG for better character detail
        workflow["7"]["inputs"]["text"] = _NEGATIVE
        workflow["3"]["inputs"]["cfg"] = 7.0
        png, err = await _comfy_render_png(workflow)
        if not png:
            return {"error": f"comfy render: {err}"}
        blob_cid = await _upload_blob_to_pds(png, _REPO)
        if not blob_cid:
            return {"error": "blob upload failed"}
        return {"blob_cid": blob_cid}
    except Exception as exc:
        _log.exception("render keyframe failed")
        return {"error": f"render: {exc!s}"[:200]}


async def _node_insert(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("blob_cid"):
        return {}
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    import secrets
    from datetime import datetime, timezone
    cut_id = state.get("cut_id") or ""
    frame_num = int(state.get("frame_num") or 1)
    rkey = f"kf-{secrets.token_hex(4)}"
    vertex_id = f"at://{_REPO}/com.etzhayyim.animeka.keyframe/{rkey}"
    blob_cid = state.get("blob_cid", "")
    rkey_cut = cut_id.rsplit("/", 1)[-1] if "/" in cut_id else cut_id
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            await conn.execute(
                """INSERT INTO vertex_animeka
                   (vertex_id, repo, rkey, collection, kind, owner_did,
                    cut_id, image_cid, frame_num, status, created_at)
                   VALUES (%s, %s, %s, 'com.etzhayyim.animeka.keyframe', 'keyframe',
                           %s, %s, %s, %s, 'draft', %s)""",
                [vertex_id, _REPO, rkey, _DEFAULT_APP_DID,
                 cut_id, blob_cid, frame_num,
                 datetime.now(tz=timezone.utc).isoformat()],
            )
            # Also update the cut record's image_cid so kaizen_compositor picks it up
            await conn.execute(
                "UPDATE vertex_animeka SET image_cid=%s "
                "WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s",
                [blob_cid, rkey_cut],
            )
        finally:
            await conn.close()
    except Exception as exc:
        _log.exception("insert keyframe failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {"keyframe_id": rkey, "keyframe_uri": vertex_id}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.generateKeyframe",
        object_id=f"kf:{state.get('keyframe_id', '')}:{int(time.time())}",
        object_type="animeka.keyframe",
        attributes={"cutId": state.get("cut_id"), "frameNum": state.get("frame_num"),
                    "ok": not bool(state.get("error"))},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_prompt", _node_fetch_prompt)
    g.add_node("render", _node_render,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=3.0))
    g.add_node("insert", _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_prompt")
    g.add_edge("fetch_prompt", "render")
    g.add_edge("render", "insert")
    g.add_edge("insert", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="generate_keyframe")
