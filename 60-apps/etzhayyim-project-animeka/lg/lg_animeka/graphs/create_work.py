"""animeka `createWork` graph — insert work record into vertex_animeka.

NSID: com.etzhayyim.animeka.createWork
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


def _gen_rkey(prefix: str = "work") -> str:
    return f"{prefix}-{secrets.token_hex(4)}"


def _cid_stub(vertex_id: str) -> str:
    return hashlib.sha256(vertex_id.encode()).hexdigest()[:32]


class _CreateWorkState(TypedDict, total=False):
    id: str | None
    title: str
    title_en: str | None
    slug: str | None
    genre: str | None
    status: str | None
    synopsis: str | None
    episode_count: int | None
    fps: int | None
    resolution: str | None
    cover_cid: str | None
    studio_name: str | None
    # output
    result_id: str | None
    result_did: str | None
    result_title: str | None
    result_status: str | None
    error: str | None


async def _node_insert(state: _CreateWorkState) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    title = state.get("title") or ""
    if not title:
        return {"error": "title is required"}

    rkey = state.get("id") or _gen_rkey("work")
    slug = state.get("slug") or rkey
    owner_did = _DEFAULT_APP_DID
    collection = "com.etzhayyim.animeka.work"
    vertex_id = f"at://{owner_did}/{collection}/{rkey}"
    created_at = datetime.now(tz=timezone.utc).isoformat()
    work_status = state.get("status") or "planning"
    work_did = f"did:web:animeka.etzhayyim.com:work:{slug}"

    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()
            await cur.execute(
                """
                INSERT INTO vertex_animeka (
                    vertex_id, repo, rkey, collection, kind,
                    owner_did, title, name, slug,
                    description, status, fps,
                    cover_cid, created_at
                ) VALUES (
                    %s, %s, %s, %s, 'work',
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s
                )
                """,
                [
                    vertex_id, owner_did, rkey, collection,
                    owner_did, title, title, slug,
                    state.get("synopsis"), work_status,
                    state.get("fps") or 24,
                    state.get("cover_cid"), created_at,
                ],
            )
        finally:
            await conn.close()

    except Exception as exc:  # noqa: BLE001
        _log.exception("create_work insert failed")
        return {"error": f"insert: {exc!s}"[:300]}

    return {
        "result_id": rkey,
        "result_did": work_did,
        "result_title": title,
        "result_status": work_status,
    }


async def _node_emit_audit(state: _CreateWorkState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.createWork",
        object_id=f"createWork:{state.get('result_id', '')}:{int(time.time())}",
        object_type="animeka.work",
        attributes={
            "workId": state.get("result_id") or "",
            "title": state.get("result_title") or "",
            "status": state.get("result_status") or "",
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_CreateWorkState)
    g.add_node("insert", _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "insert")
    g.add_edge("insert", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="create_work")
