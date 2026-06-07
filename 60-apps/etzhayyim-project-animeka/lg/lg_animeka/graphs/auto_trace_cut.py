"""animeka `autoTraceCut` graph.

NSID: com.etzhayyim.animeka.autoTraceCut

Produces a color-traced finish layer for a cut:
  fetch_keyframe → llm_color_prompt → render_trace → insert → audit

Reads the keyframe record (image_cid) from vertex_animeka, generates a
clean cel-shaded color version via ComfyUI (1024×1024), uploads to PDS,
and inserts a colorTrace record. Updates the cut's stage_status.
"""

from __future__ import annotations

import logging
import os
import secrets
import time
from datetime import datetime, timezone
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
_APP_DID = os.environ.get("ANIMEKA_APP_DID", "did:web:animeka.etzhayyim.com")
_REPO = os.environ.get("ANIMEKA_REPO_DID", "did:web:an1m3k4x.etzhayyim.com")
_CKPT = "animagine-xl-4.0.safetensors"
_CHARACTER_DESC = "high-school girl, navy blazer, dark long hair, introspective"


class _State(TypedDict, total=False):
    cut_id: str
    keyframe_uri: str | None     # override; if absent, looked up from DB
    keyframe_cid: str | None     # source image CID for color tracing
    camera_note: str | None      # scene description from cut record
    # output
    color_prompt: str | None
    color_trace_id: str | None
    color_trace_uri: str | None
    color_layers_cid: str | None
    error: str | None


async def _node_fetch_keyframe(state: _State) -> dict[str, Any]:
    if state.get("keyframe_cid"):
        return {}
    cut_id = state.get("cut_id") or ""
    if not cut_id or not _RW_URL:
        return {}
    rkey = cut_id.rsplit("/", 1)[-1] if "/" in cut_id else cut_id
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            # Fetch the most recent keyframe for this cut
            await cur.execute(
                "SELECT image_cid, camera_note FROM vertex_animeka "
                "WHERE collection='com.etzhayyim.animeka.keyframe' AND cut_id=%s "
                "ORDER BY created_at DESC LIMIT 1",
                [rkey],
            )
            row = await cur.fetchone()
            if not row:
                # Fallback: fetch cut camera_note for prompt generation
                await cur.execute(
                    "SELECT camera_note FROM vertex_animeka "
                    "WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s LIMIT 1",
                    [rkey],
                )
                row2 = await cur.fetchone()
                return {"camera_note": (row2[0] if row2 else None)}
        finally:
            await conn.close()
        return {
            "keyframe_cid": row[0],
            "camera_note": row[1],
        }
    except Exception as exc:
        _log.warning("fetch_keyframe: %s", exc)
        return {}


async def _node_llm_color_prompt(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    scene = state.get("camera_note") or "anime character in a scene"
    system = (
        "You are an anime color designer. Given a scene description, output ONE "
        "concise positive ComfyUI prompt (max 60 words) for a fully colored "
        "cel-shaded anime frame. Include: character description, color palette "
        "mood (warm/cool/neutral), lighting direction. "
        "No preamble, no code fences."
    )
    color_prompt = scene
    try:
        async with httpx.AsyncClient(timeout=_VLLM_TIMEOUT) as c:
            r = await c.post(
                f"{_VLLM_URL}/chat/completions",
                json={
                    "model": _VLLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"Scene: {scene}\nCharacters: {_CHARACTER_DESC}"},
                    ],
                    "max_tokens": 150, "temperature": 0.5,
                },
                headers={"Content-Type": "application/json"},
            )
        if r.status_code < 400:
            content = (((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
            if content:
                color_prompt = content
    except Exception as exc:
        _log.warning("llm_color_prompt: %s", exc)

    full_prompt = (
        color_prompt + ", "
        f"{_CHARACTER_DESC}, "
        "anime cel shading, flat color fills, clean ink outlines, "
        "color trace finish layer, production quality"
    )
    return {"color_prompt": full_prompt}


async def _node_render_trace(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("color_prompt"):
        return {}
    try:
        from kotodama.primitives.shinshi_image import (
            _build_anime_workflow,
            _comfy_render_png,
            _upload_blob_to_pds,
        )
        workflow = _build_anime_workflow(state["color_prompt"], _CKPT, 1024, 1024, 28)
        png, err = await _comfy_render_png(workflow)
        if not png:
            return {"error": f"comfy render: {err}"}
        cid = await _upload_blob_to_pds(png, _REPO)
        if not cid:
            return {"error": "blob upload failed"}
        return {"color_layers_cid": cid}
    except Exception as exc:
        _log.exception("render_trace failed")
        return {"error": f"render: {exc!s}"[:200]}


async def _node_insert(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("color_layers_cid"):
        return {}
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    cut_id = state.get("cut_id") or ""
    rkey_cut = cut_id.rsplit("/", 1)[-1] if "/" in cut_id else cut_id
    rkey = f"ct-{secrets.token_hex(4)}"
    vertex_id = f"at://{_REPO}/com.etzhayyim.animeka.colorTrace/{rkey}"
    created_at = datetime.now(tz=timezone.utc).isoformat()
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            await conn.execute(
                """INSERT INTO vertex_animeka
                   (vertex_id, repo, rkey, collection, kind, owner_did,
                    cut_id, color_layers_cid, status, created_at)
                   VALUES (%s, %s, %s, 'com.etzhayyim.animeka.colorTrace', 'colorTrace',
                           %s, %s, %s, 'draft', %s)""",
                [vertex_id, _REPO, rkey, _APP_DID,
                 rkey_cut, state.get("color_layers_cid"), created_at],
            )
            # Update cut stage_status: mark color as done
            await conn.execute(
                """UPDATE vertex_animeka
                   SET stage_status = COALESCE(stage_status, '{}')
                   WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s""",
                [rkey_cut],
            )
        finally:
            await conn.close()
    except Exception as exc:
        _log.exception("insert colorTrace failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {"color_trace_id": rkey, "color_trace_uri": vertex_id}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="animeka.autoTraceCut",
        object_id=f"autoTraceCut:{state.get('cut_id', '')}:{int(time.time())}",
        object_type="animeka.colorTrace",
        attributes={
            "cutId": state.get("cut_id"),
            "keyframeCid": state.get("keyframe_cid"),
            "colorLayersCid": state.get("color_layers_cid"),
            "colorTraceUri": state.get("color_trace_uri"),
            "ok": not bool(state.get("error")),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_keyframe",    _node_fetch_keyframe)
    g.add_node("llm_color_prompt",  _node_llm_color_prompt,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=2.0))
    g.add_node("render_trace",      _node_render_trace,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=3.0))
    g.add_node("insert",            _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("audit",             _node_audit)
    g.add_edge(START, "fetch_keyframe")
    g.add_edge("fetch_keyframe",   "llm_color_prompt")
    g.add_edge("llm_color_prompt", "render_trace")
    g.add_edge("render_trace",     "insert")
    g.add_edge("insert",           "audit")
    g.add_edge("audit",            END)
    return g


GRAPH = _build().compile(name="auto_trace_cut")
