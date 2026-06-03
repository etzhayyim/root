"""animeka `cutRunner` graph.

NSID: com.etzhayyim.animeka.cutRunner

Orchestrates the full cut production pipeline for one existing cut:
  fetch_cut → storyboard → layout → keyframe → background → update_cut → audit

Each stage delegates to the compiled sub-graph (generate_storyboard etc.)
so retry / audit / DB insert semantics are inherited without duplication.
stage_status JSON in vertex_animeka is updated at completion.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_animeka.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_APP_DID = os.environ.get("ANIMEKA_APP_DID", "did:web:animeka.etzhayyim.com")
_REPO = os.environ.get("ANIMEKA_REPO_DID", "did:web:an1m3k4x.etzhayyim.com")


class _State(TypedDict, total=False):
    cut_id: str
    camera_note: str | None
    # sub-graph outputs (blob CIDs + record URIs)
    storyboard_uri: str | None
    storyboard_cid: str | None
    layout_uri: str | None
    layout_cid: str | None
    keyframe_uri: str | None
    keyframe_cid: str | None
    background_uri: str | None
    background_cid: str | None
    status: str | None
    error: str | None


async def _node_fetch_cut(state: _State) -> dict[str, Any]:
    cut_id = state.get("cut_id") or ""
    if not cut_id:
        return {"error": "cut_id required"}
    if not _RW_URL:
        return {"status": "running"}
    try:
        import psycopg
        rkey = cut_id.rsplit("/", 1)[-1] if "/" in cut_id else cut_id
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                "SELECT camera_note, status FROM vertex_animeka "
                "WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s LIMIT 1",
                [rkey],
            )
            row = await cur.fetchone()
        finally:
            await conn.close()
        if not row:
            return {"error": f"cut not found: {rkey}"}
        return {"camera_note": row[0], "status": "running"}
    except Exception as exc:
        _log.warning("fetch_cut: %s", exc)
        return {"status": "running"}


async def _node_storyboard(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    try:
        from lg_animeka.graphs.generate_storyboard import GRAPH as SB
        out = await SB.ainvoke({
            "cut_id": state["cut_id"],
            "cut_summary": state.get("camera_note"),
        })
        return {
            "storyboard_uri": out.get("storyboard_uri"),
            "storyboard_cid": out.get("blob_cid"),
        }
    except Exception as exc:
        _log.warning("storyboard sub-graph: %s", exc)
        return {}


async def _node_layout(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    try:
        from lg_animeka.graphs.generate_layout import GRAPH as LY
        out = await LY.ainvoke({
            "cut_id": state["cut_id"],
            "visual_prompt": state.get("camera_note"),
            "storyboard_cid": state.get("storyboard_cid"),
        })
        return {
            "layout_uri": out.get("layout_uri"),
            "layout_cid": out.get("blob_cid"),
        }
    except Exception as exc:
        _log.warning("layout sub-graph: %s", exc)
        return {}


async def _node_keyframe(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    try:
        from lg_animeka.graphs.generate_keyframe import GRAPH as KF
        out = await KF.ainvoke({
            "cut_id": state["cut_id"],
            "visual_prompt": state.get("camera_note"),
        })
        return {
            "keyframe_uri": out.get("keyframe_uri"),
            "keyframe_cid": out.get("blob_cid"),
        }
    except Exception as exc:
        _log.warning("keyframe sub-graph: %s", exc)
        return {}


async def _node_background(state: _State) -> dict[str, Any]:
    if state.get("error"):
        return {}
    try:
        from lg_animeka.graphs.generate_background import GRAPH as BG
        out = await BG.ainvoke({
            "cut_id": state["cut_id"],
            "scene_description": state.get("camera_note"),
        })
        return {
            "background_uri": out.get("background_uri"),
            "background_cid": out.get("blob_cid"),
        }
    except Exception as exc:
        _log.warning("background sub-graph: %s", exc)
        return {}


async def _node_update_cut(state: _State) -> dict[str, Any]:
    if not _RW_URL:
        return {"status": "ready_for_review"}
    cut_id = state.get("cut_id") or ""
    rkey = cut_id.rsplit("/", 1)[-1] if "/" in cut_id else cut_id
    stage_status = json.dumps({
        "storyboard": "done" if state.get("storyboard_uri") else "error",
        "layout":     "done" if state.get("layout_uri") else "error",
        "keyframe":   "done" if state.get("keyframe_uri") else "error",
        "background": "done" if state.get("background_uri") else "error",
    })
    try:
        import psycopg
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            await conn.execute(
                "UPDATE vertex_animeka SET stage_status=%s, status='ready_for_review' "
                "WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s",
                [stage_status, rkey],
            )
        finally:
            await conn.close()
    except Exception as exc:
        _log.warning("update_cut: %s", exc)
    return {"status": "ready_for_review"}


async def _node_audit(state: _State) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="animeka.cutRunner",
        object_id=f"cutRunner:{state.get('cut_id', '')}:{int(time.time())}",
        object_type="animeka.cut",
        attributes={
            "cutId": state.get("cut_id"),
            "storyboardUri": state.get("storyboard_uri"),
            "layoutUri": state.get("layout_uri"),
            "keyframeUri": state.get("keyframe_uri"),
            "backgroundUri": state.get("background_uri"),
            "ok": not bool(state.get("error")),
            "status": state.get("status"),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_State)
    g.add_node("fetch_cut",   _node_fetch_cut)
    g.add_node("storyboard",  _node_storyboard)
    g.add_node("layout",      _node_layout)
    g.add_node("keyframe",    _node_keyframe)
    g.add_node("background",  _node_background)
    g.add_node("update_cut",  _node_update_cut)
    g.add_node("audit",       _node_audit)
    g.add_edge(START, "fetch_cut")
    g.add_edge("fetch_cut",  "storyboard")
    g.add_edge("storyboard", "layout")
    g.add_edge("layout",     "keyframe")
    g.add_edge("keyframe",   "background")
    g.add_edge("background", "update_cut")
    g.add_edge("update_cut", "audit")
    g.add_edge("audit",      END)
    return g


GRAPH = _build().compile(name="cut_runner")
