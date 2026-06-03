"""animeka `breakdownScene` graph — LLM scene → numbered cut records.

NSID: com.etzhayyim.animeka.breakdownScene

Given a scene description (or script body) and an episode_id, uses LLM
to break the scene into N cuts with shot type, duration, and camera notes.
Creates cut records for each in vertex_animeka.

Output: list of created cut URIs + the LLM breakdown JSON.
"""

from __future__ import annotations

import json
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


class _CutSpec(TypedDict):
    cutNum: int
    shotType: str       # "WS" "MS" "CU" "ECU" "OTS" etc.
    durationFrames: int
    cameraNote: str     # brief description


class _State(TypedDict, total=False):
    episode_id: str
    scene_id: str | None
    scene_text: str                 # description or script body
    fps: int | None                 # default 24
    max_cuts: int | None            # default 8
    # output
    breakdown: list[_CutSpec] | None
    cut_ids: list[str] | None
    cut_uris: list[str] | None
    error: str | None


async def _node_llm_breakdown(state: _State) -> dict[str, Any]:
    scene_text = state.get("scene_text") or ""
    if not scene_text:
        return {"error": "scene_text required"}
    max_cuts = int(state.get("max_cuts") or 8)
    fps = int(state.get("fps") or 24)
    system = (
        f"You are an anime director breaking down a scene into cuts. "
        f"Output a JSON array of up to {max_cuts} objects, each with keys: "
        f"cutNum (integer, 1-based), shotType (string: WS/MS/CU/ECU/OTS/POV/INSERT), "
        f"durationFrames (integer, at {fps}fps; typical 24-96), "
        f"cameraNote (string, max 40 words: composition, character pose, action). "
        f"No code fences, no preamble, array only."
    )
    user = f"Scene:\n{scene_text[:1500]}"
    breakdown: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=_VLLM_TIMEOUT) as c:
            r = await c.post(
                f"{_VLLM_URL}/chat/completions",
                json={"model": _VLLM_MODEL,
                      "messages": [{"role": "system", "content": system},
                                   {"role": "user", "content": user}],
                      "max_tokens": 1200, "temperature": 0.4},
                headers={"Content-Type": "application/json"},
            )
        if r.status_code >= 400:
            return {"error": f"vllm {r.status_code}"}
        content = (((r.json().get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        breakdown = json.loads(content)
        if not isinstance(breakdown, list):
            breakdown = []
    except json.JSONDecodeError as exc:
        _log.warning("llm_breakdown JSON parse: %s | content: %r", exc, content[:200])
        # Fallback: single cut
        breakdown = [{
            "cutNum": 1, "shotType": "MS", "durationFrames": 48,
            "cameraNote": scene_text[:120],
        }]
    except Exception as exc:
        return {"error": f"vllm: {exc!s}"[:200]}

    return {"breakdown": breakdown[:max_cuts]}


async def _node_insert_cuts(state: _State) -> dict[str, Any]:
    if state.get("error") or not state.get("breakdown"):
        return {}
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    episode_id = state.get("episode_id") or ""
    scene_id = state.get("scene_id") or ""
    fps = int(state.get("fps") or 24)
    created_at = datetime.now(tz=timezone.utc).isoformat()
    cut_ids: list[str] = []
    cut_uris: list[str] = []
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            for spec in (state["breakdown"] or []):
                rkey = f"cut-{secrets.token_hex(4)}"
                vertex_id = f"at://{_REPO}/com.etzhayyim.animeka.cut/{rkey}"
                cut_num = int(spec.get("cutNum") or len(cut_ids) + 1)
                duration = int(spec.get("durationFrames") or 48)
                camera_note = str(spec.get("cameraNote") or "")[:255]
                shot_type = str(spec.get("shotType") or "MS")[:16]
                import json as _json
                stage_status = _json.dumps({
                    s: "pending" for s in [
                        "script", "storyboard", "layout", "keyAnim",
                        "inbetween", "colorDesign", "finish", "background",
                        "composite", "edit", "sound", "delivery",
                    ]
                })
                await conn.execute(
                    """INSERT INTO vertex_animeka (
                       vertex_id, repo, rkey, collection, kind, owner_did,
                       episode_id, scene_id, cut_num, duration_frames, fps,
                       camera_mode, camera_note, stage_status, status, created_at)
                       VALUES (%s,%s,%s,'com.etzhayyim.animeka.cut','cut',%s,
                               %s,%s,%s,%s,%s,%s,%s,%s,'pending',%s)""",
                    [vertex_id, _REPO, rkey, _APP_DID,
                     episode_id, scene_id, cut_num, duration, fps,
                     shot_type, camera_note, stage_status, created_at],
                )
                cut_ids.append(rkey)
                cut_uris.append(vertex_id)
        finally:
            await conn.close()
    except Exception as exc:
        _log.exception("insert_cuts failed")
        return {"error": f"insert: {exc!s}"[:300]}
    return {"cut_ids": cut_ids, "cut_uris": cut_uris}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="animeka.breakdownScene",
        object_id=f"breakdown:{state.get('episode_id','')},{state.get('scene_id','')}:{int(time.time())}",
        object_type="animeka.cut",
        attributes={
            "episodeId": state.get("episode_id"),
            "sceneId": state.get("scene_id"),
            "cutsCreated": len(state.get("cut_ids") or []),
            "ok": not bool(state.get("error")),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("llm_breakdown", _node_llm_breakdown,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=2.0))
    g.add_node("insert_cuts",  _node_insert_cuts,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("audit",        _node_audit)
    g.add_edge(START, "llm_breakdown")
    g.add_edge("llm_breakdown", "insert_cuts")
    g.add_edge("insert_cuts", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="breakdown_scene")
