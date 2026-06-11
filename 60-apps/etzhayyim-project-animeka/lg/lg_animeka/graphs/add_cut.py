"""animeka `addCut` graph — create a cut under a scene.

NSID: com.etzhayyim.animeka.addCut
Auto-increments cutNum within the episode when not supplied.
Initializes stageStatus to all 'pending'.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_animeka.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_DEFAULT_APP_DID = os.environ.get("ANIMEKA_APP_DID", "did:web:animeka.etzhayyim.com")

_STAGES = [
    "script", "storyboard", "layout", "keyAnim",
    "inbetween", "colorDesign", "finish", "background",
    "composite", "edit", "sound", "delivery",
]
_DEFAULT_STAGE_STATUS = json.dumps({s: "pending" for s in _STAGES})


def _rkey_from_id(val: str) -> str:
    if val.startswith("at://"):
        return val.rstrip("/").rsplit("/", 1)[-1]
    return val


def _gen_rkey(prefix: str = "cut") -> str:
    return f"{prefix}-{secrets.token_hex(4)}"


def _cid_stub(vertex_id: str) -> str:
    return hashlib.sha256(vertex_id.encode()).hexdigest()[:32]


class _AddCutState(TypedDict, total=False):
    scene_id: str
    episode_id: str | None
    id: str | None
    cut_num: int | None
    duration_frames: int
    fps: int | None
    camera_mode: str | None
    camera_note: str | None
    # output
    result_uri: str | None
    result_cid: str | None
    result_did: str | None
    result_cut_num: int | None
    error: str | None


async def _node_insert(state: _AddCutState) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    scene_id = state.get("scene_id") or ""
    if not scene_id:
        return {"error": "scene_id is required"}
    duration_frames = state.get("duration_frames")
    if duration_frames is None:
        return {"error": "durationFrames is required"}

    scene_rkey = _rkey_from_id(scene_id)
    owner_did = _DEFAULT_APP_DID
    collection = "com.etzhayyim.animeka.cut"
    rkey = state.get("id") or _gen_rkey("cut")
    created_at = datetime.now(tz=timezone.utc).isoformat()

    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()

            # Resolve scene vertex_id and episode_id
            await cur.execute(
                """SELECT vertex_id, episode_id, fps FROM vertex_animeka
                   WHERE collection='com.etzhayyim.animeka.scene' AND rkey=%s LIMIT 1""",
                [scene_rkey],
            )
            scene_row = await cur.fetchone()
            scene_vertex_id = scene_row[0] if scene_row else f"at://{owner_did}/com.etzhayyim.animeka.scene/{scene_rkey}"
            scene_episode_id = (scene_row[1] if scene_row else None) or state.get("episode_id") or ""
            inherited_fps = (scene_row[2] if scene_row else None) or 24

            fps = state.get("fps") or int(inherited_fps)

            # Auto-increment cutNum if not supplied
            cut_num = state.get("cut_num")
            if cut_num is None and scene_episode_id:
                await cur.execute(
                    """
                    SELECT COALESCE(MAX(cut_num), 0) FROM vertex_animeka
                    WHERE collection='com.etzhayyim.animeka.cut'
                      AND episode_id = %s
                    """,
                    [scene_episode_id],
                )
                max_row = await cur.fetchone()
                cut_num = int(max_row[0] or 0) + 1 if max_row else 1

            vertex_id = f"at://{owner_did}/{collection}/{rkey}"
            cut_did = f"did:web:animeka.etzhayyim.com:cut:{rkey}"

            await cur.execute(
                """
                INSERT INTO vertex_animeka (
                    vertex_id, repo, rkey, collection, kind,
                    owner_did, scene_id, episode_id, cut_num,
                    duration_frames, fps, camera_mode, camera_note,
                    stage_status, status, priority, created_at
                ) VALUES (
                    %s, %s, %s, %s, 'cut',
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, 'pending', 'normal', %s
                )
                """,
                [
                    vertex_id, owner_did, rkey, collection,
                    owner_did, scene_vertex_id, scene_episode_id,
                    int(cut_num) if cut_num is not None else None,
                    int(duration_frames), int(fps),
                    state.get("camera_mode"),
                    state.get("camera_note"),
                    _DEFAULT_STAGE_STATUS,
                    created_at,
                ],
            )

        finally:
            await conn.close()

    except Exception as exc:  # noqa: BLE001
        _log.exception("add_cut insert failed")
        return {"error": f"insert: {exc!s}"[:300]}

    cid = _cid_stub(f"at://{owner_did}/{collection}/{rkey}")
    return {
        "result_uri": f"at://{owner_did}/{collection}/{rkey}",
        "result_cid": cid,
        "result_did": cut_did,
        "result_cut_num": cut_num,
    }


async def _node_emit_audit(state: _AddCutState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.addCut",
        object_id=f"addCut:{state.get('result_uri', '')}:{int(time.time())}",
        object_type="animeka.cut",
        attributes={
            "sceneId": state.get("scene_id") or "",
            "cutNum": state.get("result_cut_num"),
            "uri": state.get("result_uri") or "",
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_AddCutState)
    g.add_node("insert", _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "insert")
    g.add_edge("insert", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="add_cut")
