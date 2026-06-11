"""animeka `generateLayout` graph — LLM layout plan + ComfyUI 1024×1024 layout drawing.

NSID: com.etzhayyim.animeka.generateLayout

Takes a cut_id and optional storyboard_cid, generates a layout plan
JSON via LLM (camera angle, character blocking, bg mood), renders a
production layout drawing via ComfyUI, and inserts into vertex_animeka.
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

from lg_animeka.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_VLLM_URL = os.environ.get("VLLM_URL", "https://vyp99t9px7h4dl-4000.proxy.runpod.net/v1").rstrip("/")
_VLLM_MODEL = os.environ.get("VLLM_MODEL", "tier0-general")
_VLLM_TIMEOUT = float(os.environ.get("VLLM_TIMEOUT_SEC", "60"))
_DEFAULT_APP_DID = os.environ.get("ANIMEKA_APP_DID", "did:web:animeka.etzhayyim.com")
_REPO = os.environ.get("ANIMEKA_REPO_DID", "did:web:an1m3k4x.etzhayyim.com")
_CKPT = "animagine-xl-4.0.safetensors"
_CHARACTER_DESC = "high-school girl, navy blazer, dark long hair, introspective"


class _State(TypedDict, total=False):
    cut_id: str
    visual_prompt: str | None
    storyboard_cid: str | None
    # output
    layout_id: str | None
    layout_uri: str | None
    blob_cid: str | None
    bg_mood: str | None
    layout_prompt: str | None
    error: str | None


async def _node_fetch_context(state: _State) -> dict[str, Any]:
    cut_id = state.get("cut_id") or ""
    if not cut_id or not _RW_URL or state.get("visual_prompt"):
        return {}
    try:
        import psycopg
        rkey = cut_id.rsplit("/", 1)[-1] if "/" in cut_id else cut_id
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            # Try to find storyboard visual_prompt for this cut
            await cur.execute(
                "SELECT camera_note, thumb_cid FROM vertex_animeka WHERE collection='com.etzhayyim.animeka.storyboard' AND cut_id=%s ORDER BY created_at DESC LIMIT 1",
                [cut_id],
            )
            row = await cur.fetchone()
        finally:
            await conn.close()
        if row:
            return {"visual_prompt": row[0] or "", "storyboard_cid": row[1] or ""}
    except Exception as exc:
        _log.warning("fetch_context: %s", exc)
    return {}


async def _node_llm_plan(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    visual_prompt = state.get("visual_prompt") or "anime scene with characters"
    system = (
        "You are an anime layout artist. Output ONE JSON object with exactly these keys: "
        "prompt (string, positive ComfyUI prompt for the full-colour layout drawing), "
        "bgMood (string, one short phrase for background atmosphere). "
        "No code fences, no extra keys, no preamble."
    )
    user = (
        f"Storyboard concept: {visual_prompt}\n"
        f"Characters: {_CHARACTER_DESC}"
    )
    layout_prompt = visual_prompt
    bg_mood = "soft warm light"
    try:
        async with httpx.AsyncClient(timeout=_VLLM_TIMEOUT) as client:
            r = await client.post(
                f"{_VLLM_URL}/chat/completions",
                json={
                    "model": _VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 400, "temperature": 0.3,
                },
                headers={"Content-Type": "application/json"},
            )
        if r.status_code < 400:
            content = ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            try:
                plan = json.loads(content.strip())
                layout_prompt = plan.get("prompt", visual_prompt)
                bg_mood = plan.get("bgMood", "soft warm light")
            except json.JSONDecodeError:
                pass
    except Exception as exc:
        _log.warning("llm_plan: %s", exc)

    full_prompt = layout_prompt + ", anime layout paper, production key drawing, clean linework, flat colour"
    return {"layout_prompt": full_prompt, "bg_mood": bg_mood}


async def _node_render(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("layout_prompt"):
        return {}
    try:
        from kotodama.primitives.shinshi_image import (
            _build_anime_workflow,
            _comfy_render_png,
            _upload_blob_to_pds,
        )
        workflow = _build_anime_workflow(state["layout_prompt"], _CKPT, 1024, 1024, 28)
        png, err = await _comfy_render_png(workflow)
        if not png:
            return {"error": f"comfy render: {err}"}
        blob_cid = await _upload_blob_to_pds(png, _REPO)
        if not blob_cid:
            return {"error": "blob upload failed"}
        return {"blob_cid": blob_cid}
    except Exception as exc:
        _log.exception("render layout failed")
        return {"error": f"render: {exc!s}"[:200]}


async def _node_insert(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("blob_cid"):
        return {}
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    import secrets
    from datetime import datetime, timezone
    cut_id = state.get("cut_id") or ""
    rkey = f"ly-{secrets.token_hex(4)}"
    vertex_id = f"at://{_REPO}/com.etzhayyim.animeka.layout/{rkey}"
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            await conn.execute(
                """INSERT INTO vertex_animeka
                   (vertex_id, repo, rkey, collection, kind, owner_did,
                    cut_id, image_cid, lighting_mood, status, created_at)
                   VALUES (%s, %s, %s, 'com.etzhayyim.animeka.layout', 'layout',
                           %s, %s, %s, %s, 'draft', %s)""",
                [vertex_id, _REPO, rkey, _DEFAULT_APP_DID,
                 cut_id, state.get("blob_cid"), state.get("bg_mood"),
                 datetime.now(tz=timezone.utc).isoformat()],
            )
        finally:
            await conn.close()
    except Exception as exc:
        _log.exception("insert layout failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {"layout_id": rkey, "layout_uri": vertex_id}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.generateLayout",
        object_id=f"ly:{state.get('layout_id', '')}:{int(time.time())}",
        object_type="animeka.layout",
        attributes={"cutId": state.get("cut_id"), "blobCid": state.get("blob_cid"),
                    "ok": not bool(state.get("error"))},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_context", _node_fetch_context)
    g.add_node("llm_plan", _node_llm_plan,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=2.0))
    g.add_node("render", _node_render,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=3.0))
    g.add_node("insert", _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_context")
    g.add_edge("fetch_context", "llm_plan")
    g.add_edge("llm_plan", "render")
    g.add_edge("render", "insert")
    g.add_edge("insert", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="generate_layout")
