"""animeka `designColorModel` graph — LLM palette JSON + ComfyUI character color sheet.

NSID: com.etzhayyim.animeka.designColorModel

Takes a character_name and optional style hints. LLM generates a
structured color palette (JSON: primary, secondary, hair, eyes, shadow).
ComfyUI renders a full-body character reference sheet. Both are saved to
vertex_animeka collection=com.etzhayyim.animeka.colorModel.
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


class _State(TypedDict, total=False):
    character_name: str
    description: str | None    # physical description override
    work_id: str | None
    # output
    color_model_id: str | None
    color_model_uri: str | None
    blob_cid: str | None
    palette: dict | None       # {primary, secondary, hair, eyes, shadow, highlight}
    render_prompt: str | None
    error: str | None


async def _node_llm_palette(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    character_name = state.get("character_name") or "anime character"
    description = state.get("description") or f"anime character named {character_name}"
    system = (
        "You are an anime color designer. Given a character description, output ONE JSON object with these keys: "
        "primary (hex, main costume color), secondary (hex, accent/trim), "
        "hair (hex, hair color), eyes (hex, eye color), "
        "shadow (hex, shadow tone for cel shading), highlight (hex), "
        "renderPrompt (string, 60-word ComfyUI prompt for a full-body color reference sheet). "
        "No code fences, no preamble."
    )
    user = f"Character: {character_name}\nDescription: {description}"
    palette: dict[str, Any] = {}
    render_prompt = f"{character_name}, anime character, full body, color reference sheet, front view, clean design"
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
                    "max_tokens": 500, "temperature": 0.4,
                },
                headers={"Content-Type": "application/json"},
            )
        if r.status_code < 400:
            content = ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            try:
                plan = json.loads(content.strip())
                palette = {k: plan[k] for k in ("primary", "secondary", "hair", "eyes", "shadow", "highlight") if k in plan}
                render_prompt = plan.get("renderPrompt", render_prompt)
            except json.JSONDecodeError:
                pass
    except Exception as exc:
        _log.warning("llm_palette: %s", exc)

    full_prompt = render_prompt + ", anime color model, turnaround sheet, flat cel colors, character design reference"
    return {"palette": palette, "render_prompt": full_prompt}


async def _node_render(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("render_prompt"):
        return {}
    try:
        from kotodama.primitives.shinshi_image import (
            _build_anime_workflow,
            _comfy_render_png,
            _upload_blob_to_pds,
        )
        workflow = _build_anime_workflow(state["render_prompt"], _CKPT, 768, 1024, 28)
        png, err = await _comfy_render_png(workflow)
        if not png:
            return {"error": f"comfy render: {err}"}
        blob_cid = await _upload_blob_to_pds(png, _REPO)
        if not blob_cid:
            return {"error": "blob upload failed"}
        return {"blob_cid": blob_cid}
    except Exception as exc:
        _log.exception("render color model failed")
        return {"error": f"render: {exc!s}"[:200]}


async def _node_insert(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    import secrets
    from datetime import datetime, timezone
    rkey = f"cm-{secrets.token_hex(4)}"
    vertex_id = f"at://{_REPO}/com.etzhayyim.animeka.colorModel/{rkey}"
    palette_json = json.dumps(state.get("palette") or {})
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            await conn.execute(
                """INSERT INTO vertex_animeka
                   (vertex_id, repo, rkey, collection, kind, owner_did,
                    name, ref_sheet_cid, props, work_id, status, created_at)
                   VALUES (%s, %s, %s, 'com.etzhayyim.animeka.colorModel', 'colorModel',
                           %s, %s, %s, %s, %s, 'draft', %s)""",
                [vertex_id, _REPO, rkey, _DEFAULT_APP_DID,
                 state.get("character_name"), state.get("blob_cid"),
                 palette_json, state.get("work_id"),
                 datetime.now(tz=timezone.utc).isoformat()],
            )
        finally:
            await conn.close()
    except Exception as exc:
        _log.exception("insert color_model failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {"color_model_id": rkey, "color_model_uri": vertex_id}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.designColorModel",
        object_id=f"cm:{state.get('color_model_id', '')}:{int(time.time())}",
        object_type="animeka.colorModel",
        attributes={"characterName": state.get("character_name"),
                    "blobCid": state.get("blob_cid"),
                    "ok": not bool(state.get("error"))},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("llm_palette", _node_llm_palette,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=2.0))
    g.add_node("render", _node_render,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=3.0))
    g.add_node("insert", _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "llm_palette")
    g.add_edge("llm_palette", "render")
    g.add_edge("render", "insert")
    g.add_edge("insert", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="design_color_model")
