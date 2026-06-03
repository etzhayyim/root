"""animeka `addEpisode` graph — insert episode record.

NSID: com.etzhayyim.animeka.addEpisode
"""
from __future__ import annotations

import hashlib
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


def _rkey_from_id(val: str) -> str:
    if val.startswith("at://"):
        return val.rstrip("/").rsplit("/", 1)[-1]
    return val


def _gen_rkey(prefix: str = "ep") -> str:
    return f"{prefix}-{secrets.token_hex(4)}"


def _cid_stub(vertex_id: str) -> str:
    return hashlib.sha256(vertex_id.encode()).hexdigest()[:32]


class _AddEpisodeState(TypedDict, total=False):
    work_id: str
    id: str | None
    episode_num: int
    title_jp: str
    title_en: str | None
    duration_sec: int | None
    fps: int | None
    air_date: str | None
    thumb_cid: str | None
    # output
    result_uri: str | None
    result_cid: str | None
    result_convo_id: str | None
    error: str | None


async def _node_insert(state: _AddEpisodeState) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    work_id = state.get("work_id") or ""
    if not work_id:
        return {"error": "work_id is required"}
    title_jp = state.get("title_jp") or ""
    if not title_jp:
        return {"error": "title_jp is required"}
    episode_num = state.get("episode_num")
    if episode_num is None:
        return {"error": "episode_num is required"}

    work_rkey = _rkey_from_id(work_id)
    owner_did = _DEFAULT_APP_DID
    collection = "com.etzhayyim.animeka.episode"
    rkey = state.get("id") or _gen_rkey("ep")
    created_at = datetime.now(tz=timezone.utc).isoformat()

    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()

            # Resolve work vertex_id
            await cur.execute(
                """SELECT vertex_id, fps FROM vertex_animeka
                   WHERE collection='com.etzhayyim.animeka.work' AND rkey=%s LIMIT 1""",
                [work_rkey],
            )
            work_row = await cur.fetchone()
            work_vertex_id = work_row[0] if work_row else f"at://{owner_did}/com.etzhayyim.animeka.work/{work_rkey}"
            inherited_fps = (work_row[1] if work_row else None) or 24

            vertex_id = f"at://{owner_did}/{collection}/{rkey}"
            fps = state.get("fps") or inherited_fps
            # convoId = rkey for simplicity (episode IS the project scope)
            convo_id = rkey

            await cur.execute(
                """
                INSERT INTO vertex_animeka (
                    vertex_id, repo, rkey, collection, kind,
                    owner_did, work_id, episode_num, title, fps,
                    duration_sec, thumb_cid, convo_id, status, created_at
                ) VALUES (
                    %s, %s, %s, %s, 'episode',
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, 'planning', %s
                )
                """,
                [
                    vertex_id, owner_did, rkey, collection,
                    owner_did, work_vertex_id, int(episode_num), title_jp, int(fps),
                    state.get("duration_sec"),
                    state.get("thumb_cid"),
                    convo_id,
                    created_at,
                ],
            )

        finally:
            await conn.close()

    except Exception as exc:  # noqa: BLE001
        _log.exception("add_episode insert failed")
        return {"error": f"insert: {exc!s}"[:300]}

    cid = _cid_stub(f"at://{owner_did}/{collection}/{rkey}")
    return {
        "result_uri": f"at://{owner_did}/{collection}/{rkey}",
        "result_cid": cid,
        "result_convo_id": convo_id,
    }


async def _node_emit_audit(state: _AddEpisodeState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.addEpisode",
        object_id=f"addEpisode:{state.get('result_convo_id', '')}:{int(time.time())}",
        object_type="animeka.episode",
        attributes={
            "workId": state.get("work_id") or "",
            "episodeNum": state.get("episode_num"),
            "uri": state.get("result_uri") or "",
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_AddEpisodeState)
    g.add_node("insert", _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "insert")
    g.add_edge("insert", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="add_episode")
