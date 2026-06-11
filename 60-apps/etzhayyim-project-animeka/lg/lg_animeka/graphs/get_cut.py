"""animeka `getCut` graph — fetch cut + full layer tree.

NSID: com.etzhayyim.animeka.getCut
"""
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

_CHILD_COLLECTIONS = [
    "com.etzhayyim.animeka.storyboard",
    "com.etzhayyim.animeka.layout",
    "com.etzhayyim.animeka.keyframe",
    "com.etzhayyim.animeka.inbetween",
    "com.etzhayyim.animeka.colorTrace",
    "com.etzhayyim.animeka.background",
    "com.etzhayyim.animeka.composite",
    "com.etzhayyim.animeka.soundCue",
    "com.etzhayyim.animeka.retake",
]

_COLL_TO_KEY = {
    "com.etzhayyim.animeka.storyboard":  "storyboards",
    "com.etzhayyim.animeka.layout":      "layouts",
    "com.etzhayyim.animeka.keyframe":    "keyframes",
    "com.etzhayyim.animeka.inbetween":   "inbetweens",
    "com.etzhayyim.animeka.colorTrace":  "colorTraces",
    "com.etzhayyim.animeka.background":  "backgrounds",
    "com.etzhayyim.animeka.composite":   "composites",
    "com.etzhayyim.animeka.soundCue":    "soundCues",
    "com.etzhayyim.animeka.retake":      "retakes",
}


def _rkey_from_id(cut_id: str) -> str:
    """Accept rkey or at-uri, return rkey."""
    if cut_id.startswith("at://"):
        return cut_id.rstrip("/").rsplit("/", 1)[-1]
    return cut_id


class _GetCutState(TypedDict, total=False):
    cut_id: str
    cut: dict[str, Any] | None
    storyboards: list[dict[str, Any]]
    layouts: list[dict[str, Any]]
    keyframes: list[dict[str, Any]]
    inbetweens: list[dict[str, Any]]
    color_traces: list[dict[str, Any]]
    backgrounds: list[dict[str, Any]]
    composites: list[dict[str, Any]]
    sound_cues: list[dict[str, Any]]
    retakes: list[dict[str, Any]]
    error: str | None


async def _node_query(state: _GetCutState) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set", "cut": None}
    cut_id = state.get("cut_id") or ""
    if not cut_id:
        return {"error": "cut_id is required", "cut": None}

    rkey = _rkey_from_id(cut_id)

    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            # Fetch the cut record
            await cur.execute(
                """
                SELECT vertex_id, repo, rkey, collection, title, cut_num,
                       duration_frames, fps, camera_mode, camera_note,
                       stage_status, assignees, priority, status,
                       episode_id, scene_id, created_at
                FROM vertex_animeka
                WHERE collection = 'com.etzhayyim.animeka.cut'
                  AND rkey = %s
                LIMIT 1
                """,
                [rkey],
            )
            row = await cur.fetchone()
            if not row:
                return {"error": f"cut not found: {rkey}", "cut": None}

            cut = {
                "uri": row[0], "repo": row[1], "rkey": row[2],
                "collection": row[3], "title": row[4],
                "cutNum": row[5], "durationFrames": row[6], "fps": row[7],
                "cameraMode": row[8], "cameraNote": row[9],
                "stageStatus": row[10], "assignees": row[11],
                "priority": row[12], "status": row[13],
                "episodeId": row[14], "sceneId": row[15],
                "createdAt": row[16],
            }

            cut_vertex_id = row[0]

            # Fetch all child records by cut_id column
            child_collections = list(_CHILD_COLLECTIONS)
            placeholders = ", ".join(["%s"] * len(child_collections))
            await cur.execute(
                f"""
                SELECT vertex_id, repo, rkey, collection,
                       frame_num, image_cid, thumb_cid, body_cid,
                       bg_cid, output_cid, asset_cid, color_layers_cid,
                       track_type, in_frame, out_frame,
                       target_uri, stage, severity, status, comment,
                       timecode_frame, author, assignees, created_at
                FROM vertex_animeka
                WHERE cut_id = %s
                  AND collection IN ({placeholders})
                ORDER BY collection, COALESCE(frame_num, 0) ASC
                LIMIT 500
                """,
                [cut_vertex_id] + child_collections,
            )
            child_rows = await cur.fetchall()

        finally:
            await conn.close()

    except Exception as exc:  # noqa: BLE001
        _log.exception("get_cut query failed")
        return {"error": f"query: {exc!s}"[:300], "cut": None}

    # Group children
    grouped: dict[str, list[dict[str, Any]]] = {k: [] for k in _COLL_TO_KEY.values()}
    for r in child_rows:
        coll = r[3]
        key = _COLL_TO_KEY.get(coll)
        if key:
            grouped[key].append({
                "uri": r[0], "rkey": r[2], "collection": coll,
                "frameNum": r[4], "imageCid": r[5], "thumbCid": r[6],
                "bodyCid": r[7], "bgCid": r[8], "outputCid": r[9],
                "assetCid": r[10], "colorLayersCid": r[11],
                "trackType": r[12], "inFrame": r[13], "outFrame": r[14],
                "targetUri": r[15], "stage": r[16], "severity": r[17],
                "status": r[18], "comment": r[19],
                "timecodeFrame": r[20], "author": r[21],
                "assignees": r[22], "createdAt": r[23],
            })

    return {
        "cut": cut,
        "storyboards": grouped["storyboards"],
        "layouts": grouped["layouts"],
        "keyframes": grouped["keyframes"],
        "inbetweens": grouped["inbetweens"],
        "color_traces": grouped["colorTraces"],
        "backgrounds": grouped["backgrounds"],
        "composites": grouped["composites"],
        "sound_cues": grouped["soundCues"],
        "retakes": grouped["retakes"],
    }


async def _node_emit_audit(state: _GetCutState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.getCut",
        object_id=f"getCut:{state.get('cut_id', '')}:{int(time.time())}",
        object_type="animeka.cut",
        attributes={"cutId": state.get("cut_id") or ""},
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_GetCutState)
    g.add_node("query", _node_query,
               retry_policy=RetryPolicy(max_attempts=3, backoff_factor=1.5))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "query")
    g.add_edge("query", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="get_cut")
