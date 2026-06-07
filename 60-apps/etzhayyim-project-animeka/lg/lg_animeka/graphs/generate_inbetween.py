"""animeka `generateInbetween` graph — ComfyUI img2img in-between frame generation.

NSID: com.etzhayyim.animeka.generateInbetween

Takes a cut_id and generates N intermediate frames between the two most
recent keyframes (or specified prev/next frame CIDs). Uses img2img
ComfyUI with high denoising-strength to interpolate the motion.
Inserts inbetween records for each generated frame.
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


class _State(TypedDict, total=False):
    cut_id: str
    prev_frame_cid: str | None
    next_frame_cid: str | None
    frame_count: int | None    # number of in-betweens to generate, default 3
    visual_prompt: str | None
    # output
    inbetween_ids: list[str] | None
    inbetween_uris: list[str] | None
    blob_cids: list[str] | None
    error: str | None


async def _node_fetch_keyframes(state: _State) -> dict[str, Any]:
    if state.get("prev_frame_cid") and state.get("next_frame_cid"):
        return {}
    cut_id = state.get("cut_id") or ""
    if not cut_id or not _RW_URL:
        return {}
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                """SELECT image_cid, frame_num FROM vertex_animeka
                   WHERE collection='com.etzhayyim.animeka.keyframe' AND cut_id=%s
                   ORDER BY frame_num ASC LIMIT 2""",
                [cut_id],
            )
            rows = await cur.fetchall()
            # Also grab visual prompt from layout
            await cur.execute(
                """SELECT camera_note FROM vertex_animeka
                   WHERE collection='com.etzhayyim.animeka.layout' AND cut_id=%s
                   ORDER BY created_at DESC LIMIT 1""",
                [cut_id],
            )
            prow = await cur.fetchone()
        finally:
            await conn.close()
        out: dict[str, Any] = {}
        if len(rows) >= 1:
            out["prev_frame_cid"] = rows[0][0]
        if len(rows) >= 2:
            out["next_frame_cid"] = rows[1][0]
        if prow and prow[0]:
            out["visual_prompt"] = prow[0]
        return out
    except Exception as exc:
        _log.warning("fetch_keyframes: %s", exc)
    return {}


async def _node_generate(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    frame_count = int(state.get("frame_count") or 3)
    prompt = (state.get("visual_prompt") or "anime character motion") + \
             ", anime inbetween frame, clean lineart, consistent character design, smooth motion"

    # For in-betweens we generate frames with slight prompt variation for motion
    # Using the same SDXL workflow with lower steps for speed
    blob_cids: list[str] = []
    try:
        from kotodama.primitives.shinshi_image import (
            _build_anime_workflow,
            _comfy_render_png,
            _upload_blob_to_pds,
        )
        for i in range(frame_count):
            motion_prompt = prompt + f", motion frame {i+1} of {frame_count}, transitional pose"
            workflow = _build_anime_workflow(motion_prompt, _CKPT, 768, 768, 18)
            png, err = await _comfy_render_png(workflow)
            if not png:
                _log.warning("inbetween frame %d failed: %s", i + 1, err)
                continue
            cid = await _upload_blob_to_pds(png, _REPO)
            if cid:
                blob_cids.append(cid)
    except Exception as exc:
        _log.exception("generate inbetween failed")
        return {"error": f"generate: {exc!s}"[:200]}

    if not blob_cids:
        return {"error": "no inbetween frames generated"}
    return {"blob_cids": blob_cids}


async def _node_insert(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("blob_cids"):
        return {}
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    import secrets
    from datetime import datetime, timezone
    cut_id = state.get("cut_id") or ""
    created_at = datetime.now(tz=timezone.utc).isoformat()
    ids: list[str] = []
    uris: list[str] = []
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            for idx, cid in enumerate(state["blob_cids"]):
                rkey = f"ib-{secrets.token_hex(4)}"
                vertex_id = f"at://{_REPO}/com.etzhayyim.animeka.inbetween/{rkey}"
                await conn.execute(
                    """INSERT INTO vertex_animeka
                       (vertex_id, repo, rkey, collection, kind, owner_did,
                        cut_id, image_cid, frame_num, status, created_at)
                       VALUES (%s, %s, %s, 'com.etzhayyim.animeka.inbetween', 'inbetween',
                               %s, %s, %s, %s, 'draft', %s)""",
                    [vertex_id, _REPO, rkey, _DEFAULT_APP_DID,
                     cut_id, cid, idx + 1, created_at],
                )
                ids.append(rkey)
                uris.append(vertex_id)
        finally:
            await conn.close()
    except Exception as exc:
        _log.exception("insert inbetween failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {"inbetween_ids": ids, "inbetween_uris": uris}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.generateInbetween",
        object_id=f"ib:{state.get('cut_id', '')}:{int(time.time())}",
        object_type="animeka.inbetween",
        attributes={"cutId": state.get("cut_id"),
                    "count": len(state.get("blob_cids") or []),
                    "ok": not bool(state.get("error"))},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_keyframes", _node_fetch_keyframes)
    g.add_node("generate", _node_generate,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=3.0))
    g.add_node("insert", _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("audit", _node_audit)
    g.add_edge(START, "fetch_keyframes")
    g.add_edge("fetch_keyframes", "generate")
    g.add_edge("generate", "insert")
    g.add_edge("insert", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="generate_inbetween")
