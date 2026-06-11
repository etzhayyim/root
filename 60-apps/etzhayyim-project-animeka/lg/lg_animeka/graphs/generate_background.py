"""animeka `generateBackground` graph — LLM bg prompt + ComfyUI 1344×768 background painting.

NSID: com.etzhayyim.animeka.generateBackground

Takes a cut_id and optional lighting_mood. Uses LLM to write an
environment description, renders a widescreen background painting
via ComfyUI SDXL (no characters), and inserts into vertex_animeka.
"""

from __future__ import annotations

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


class _State(TypedDict, total=False):
    cut_id: str
    lighting_mood: str | None
    scene_summary: str | None
    # output
    background_id: str | None
    background_uri: str | None
    blob_cid: str | None
    bg_prompt: str | None
    error: str | None


async def _node_fetch_context(state: _State) -> dict[str, Any]:
    cut_id = state.get("cut_id") or ""
    if not cut_id or not _RW_URL:
        return {}
    if state.get("lighting_mood") and state.get("scene_summary"):
        return {}
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            # Try layout for bg_mood, cut for camera_note
            await cur.execute(
                """SELECT lighting_mood FROM vertex_animeka
                   WHERE collection='com.etzhayyim.animeka.layout' AND cut_id=%s
                   ORDER BY created_at DESC LIMIT 1""",
                [cut_id],
            )
            row = await cur.fetchone()
            bg_mood = (row[0] if row else None) or state.get("lighting_mood") or "soft warm light"

            rkey = cut_id.rsplit("/", 1)[-1] if "/" in cut_id else cut_id
            await cur.execute(
                "SELECT camera_note FROM vertex_animeka WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s LIMIT 1",
                [rkey],
            )
            crow = await cur.fetchone()
        finally:
            await conn.close()
        out: dict[str, Any] = {"lighting_mood": bg_mood}
        if crow and crow[0]:
            out["scene_summary"] = str(crow[0])
        return out
    except Exception as exc:
        _log.warning("fetch_context: %s", exc)
    return {}


async def _node_llm_bg(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    scene_summary = state.get("scene_summary") or "a peaceful scene"
    bg_mood = state.get("lighting_mood") or "soft warm light"
    system = (
        "You are an anime background artist. Output a SINGLE evocative environment "
        "description (max 50 words) for a widescreen background painting with "
        "NO characters. Focus on setting, lighting, and atmosphere."
    )
    user = f"Scene: {scene_summary}\nLighting mood: {bg_mood}"
    bg_prompt = f"anime background, {bg_mood}, no characters"
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
                    "max_tokens": 200, "temperature": 0.6,
                },
                headers={"Content-Type": "application/json"},
            )
        if r.status_code < 400:
            content = ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            if content.strip():
                bg_prompt = content.strip()
    except Exception as exc:
        _log.warning("llm_bg: %s", exc)

    full_prompt = bg_prompt + ", anime background painting, painterly, no characters, widescreen cinematic"
    return {"bg_prompt": full_prompt}


async def _node_render(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("bg_prompt"):
        return {}
    try:
        from kotodama.primitives.shinshi_image import (
            _build_anime_workflow,
            _comfy_render_png,
            _upload_blob_to_pds,
        )
        workflow = _build_anime_workflow(state["bg_prompt"], _CKPT, 1344, 768, 28)
        png, err = await _comfy_render_png(workflow)
        if not png:
            return {"error": f"comfy render: {err}"}
        blob_cid = await _upload_blob_to_pds(png, _REPO)
        if not blob_cid:
            return {"error": "blob upload failed"}
        return {"blob_cid": blob_cid}
    except Exception as exc:
        _log.exception("render background failed")
        return {"error": f"render: {exc!s}"[:200]}


async def _node_insert(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("blob_cid"):
        return {}
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    import secrets
    from datetime import datetime, timezone
    cut_id = state.get("cut_id") or ""
    rkey = f"bg-{secrets.token_hex(4)}"
    vertex_id = f"at://{_REPO}/com.etzhayyim.animeka.background/{rkey}"
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            await conn.execute(
                """INSERT INTO vertex_animeka
                   (vertex_id, repo, rkey, collection, kind, owner_did,
                    cut_id, bg_cid, lighting_mood, status, created_at)
                   VALUES (%s, %s, %s, 'com.etzhayyim.animeka.background', 'background',
                           %s, %s, %s, %s, 'draft', %s)""",
                [vertex_id, _REPO, rkey, _DEFAULT_APP_DID,
                 cut_id, state.get("blob_cid"), state.get("lighting_mood"),
                 datetime.now(tz=timezone.utc).isoformat()],
            )
        finally:
            await conn.close()
    except Exception as exc:
        _log.exception("insert background failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {"background_id": rkey, "background_uri": vertex_id}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.generateBackground",
        object_id=f"bg:{state.get('background_id', '')}:{int(time.time())}",
        object_type="animeka.background",
        attributes={"cutId": state.get("cut_id"), "blobCid": state.get("blob_cid"),
                    "ok": not bool(state.get("error"))},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_context", _node_fetch_context)
    g.add_node("llm_bg", _node_llm_bg,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=2.0))
    g.add_node("render", _node_render,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=3.0))
    g.add_node("insert", _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_context")
    g.add_edge("fetch_context", "llm_bg")
    g.add_edge("llm_bg", "render")
    g.add_edge("render", "insert")
    g.add_edge("insert", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="generate_background")
