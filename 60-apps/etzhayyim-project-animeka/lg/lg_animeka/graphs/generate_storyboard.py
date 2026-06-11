"""animeka `generateStoryboard` graph — LLM prompt + ComfyUI 512×512 storyboard sketch.

NSID: com.etzhayyim.animeka.generateStoryboard

Takes a cut_id, generates a visual prompt via LLM, renders a monochrome
storyboard sketch via ComfyUI, uploads to PDS, and inserts a storyboard
record into vertex_animeka.
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
_CHARACTER_DESC = "high-school girl, navy blazer, dark long hair, introspective"


class _State(TypedDict, total=False):
    cut_id: str
    cut_summary: str | None    # override; if absent read from DB
    # output
    storyboard_id: str | None
    storyboard_uri: str | None
    blob_cid: str | None
    visual_prompt: str | None
    error: str | None


async def _node_fetch_cut(state: _State) -> dict[str, Any]:
    if state.get("cut_summary"):
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
            await cur.execute(
                "SELECT camera_note FROM vertex_animeka WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s LIMIT 1",
                [rkey],
            )
            row = await cur.fetchone()
        finally:
            await conn.close()
        if row and row[0]:
            return {"cut_summary": row[0]}
    except Exception as exc:
        _log.warning("fetch_cut: %s", exc)
    return {}


async def _node_llm_prompt(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    cut_summary = state.get("cut_summary") or "An anime scene with characters in an evocative setting."
    system = (
        "You are a storyboard artist for a moody anime short. "
        "Given a scene description, output ONE concise visual prompt (max 60 words) "
        "for a monochrome storyboard sketch. Describe composition, camera angle, "
        "and character pose. No dialogue, no preamble."
    )
    try:
        async with httpx.AsyncClient(timeout=_VLLM_TIMEOUT) as client:
            r = await client.post(
                f"{_VLLM_URL}/chat/completions",
                json={
                    "model": _VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"Scene: {cut_summary}\nCharacters: {_CHARACTER_DESC}"},
                    ],
                    "max_tokens": 200, "temperature": 0.7,
                },
                headers={"Content-Type": "application/json"},
            )
        if r.status_code >= 400:
            return {"error": f"vllm {r.status_code}"}
        content = ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    except Exception as exc:
        return {"error": f"vllm: {exc!s}"[:200]}

    prompt = content.strip() + ", storyboard sketch, monochrome pencil lineart, loose confident strokes, story panel"
    return {"visual_prompt": prompt}


async def _node_render(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("visual_prompt"):
        return {}
    try:
        from kotodama.primitives.shinshi_image import (
            _build_anime_workflow,
            _comfy_render_png,
            _upload_blob_to_pds,
        )
        workflow = _build_anime_workflow(state["visual_prompt"], _CKPT, 512, 512, 22)
        png, err = await _comfy_render_png(workflow)
        if not png:
            return {"error": f"comfy render: {err}"}
        blob_cid = await _upload_blob_to_pds(png, _REPO)
        if not blob_cid:
            return {"error": "blob upload failed"}
        return {"blob_cid": blob_cid}
    except Exception as exc:
        _log.exception("render storyboard failed")
        return {"error": f"render: {exc!s}"[:200]}


async def _node_insert(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("blob_cid"):
        return {}
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    import secrets
    from datetime import datetime, timezone
    cut_id = state.get("cut_id") or ""
    rkey = f"sb-{secrets.token_hex(4)}"
    vertex_id = f"at://{_REPO}/com.etzhayyim.animeka.storyboard/{rkey}"
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            await conn.execute(
                """INSERT INTO vertex_animeka
                   (vertex_id, repo, rkey, collection, kind, owner_did,
                    cut_id, thumb_cid, camera_note, status, created_at)
                   VALUES (%s, %s, %s, 'com.etzhayyim.animeka.storyboard', 'storyboard',
                           %s, %s, %s, %s, 'draft', %s)""",
                [vertex_id, _REPO, rkey, _DEFAULT_APP_DID,
                 cut_id, state.get("blob_cid"), state.get("visual_prompt"),
                 datetime.now(tz=timezone.utc).isoformat()],
            )
        finally:
            await conn.close()
    except Exception as exc:
        _log.exception("insert storyboard failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {"storyboard_id": rkey, "storyboard_uri": vertex_id}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.generateStoryboard",
        object_id=f"sb:{state.get('storyboard_id', '')}:{int(time.time())}",
        object_type="animeka.storyboard",
        attributes={"cutId": state.get("cut_id"), "blobCid": state.get("blob_cid"),
                    "ok": not bool(state.get("error"))},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_cut", _node_fetch_cut)
    g.add_node("llm_prompt", _node_llm_prompt,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=2.0))
    g.add_node("render", _node_render,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=3.0))
    g.add_node("insert", _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_cut")
    g.add_edge("fetch_cut", "llm_prompt")
    g.add_edge("llm_prompt", "render")
    g.add_edge("render", "insert")
    g.add_edge("insert", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="generate_storyboard")
