"""animeka `submitRetake` graph — file a retake against a cut layer.

NSID: com.etzhayyim.animeka.submitRetake
Inserts an animeka.retake record and marks the parent cut stage as 'retake'.
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


def _rkey_from_id(val: str) -> str:
    if val.startswith("at://"):
        return val.rstrip("/").rsplit("/", 1)[-1]
    return val


def _gen_rkey(prefix: str = "rt") -> str:
    return f"{prefix}-{secrets.token_hex(4)}"


def _cid_stub(vertex_id: str) -> str:
    return hashlib.sha256(vertex_id.encode()).hexdigest()[:32]


class _SubmitRetakeState(TypedDict, total=False):
    target_uri: str
    cut_id: str | None
    stage: str
    comment: str
    severity: str | None
    timecode_frame: int | None
    assignee: str | None
    region_x: float | None
    region_y: float | None
    region_w: float | None
    region_h: float | None
    # output
    result_uri: str | None
    result_cid: str | None
    error: str | None


async def _node_insert(state: _SubmitRetakeState) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    target_uri = state.get("target_uri") or ""
    stage = state.get("stage") or ""
    comment = state.get("comment") or ""
    if not target_uri or not stage or not comment:
        return {"error": "targetUri, stage and comment are required"}

    owner_did = _DEFAULT_APP_DID
    collection = "com.etzhayyim.animeka.retake"
    rkey = _gen_rkey("rt")
    vertex_id = f"at://{owner_did}/{collection}/{rkey}"
    created_at = datetime.now(tz=timezone.utc).isoformat()

    # Resolve cut_id: explicit or derive from targetUri (assume targetUri IS the cut or a child of cut)
    cut_id_input = state.get("cut_id") or target_uri
    cut_rkey = _rkey_from_id(cut_id_input)

    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()

            # Resolve cut vertex_id
            await cur.execute(
                """SELECT vertex_id, stage_status FROM vertex_animeka
                   WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s LIMIT 1""",
                [cut_rkey],
            )
            cut_row = await cur.fetchone()
            cut_vertex_id = cut_row[0] if cut_row else f"at://{owner_did}/com.etzhayyim.animeka.cut/{cut_rkey}"

            # Insert retake record
            await cur.execute(
                """
                INSERT INTO vertex_animeka (
                    vertex_id, repo, rkey, collection, kind,
                    owner_did, target_uri, cut_id,
                    stage, severity, status, comment,
                    timecode_frame, x, y, w, h,
                    assignees, author, created_at
                ) VALUES (
                    %s, %s, %s, %s, 'retake',
                    %s, %s, %s,
                    %s, %s, 'open', %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
                """,
                [
                    vertex_id, owner_did, rkey, collection,
                    owner_did, target_uri, cut_vertex_id,
                    stage, state.get("severity") or "minor", comment,
                    state.get("timecode_frame"),
                    state.get("region_x"), state.get("region_y"),
                    state.get("region_w"), state.get("region_h"),
                    state.get("assignee"), owner_did,
                    created_at,
                ],
            )

            # Flip cut priority to 'retake' and update stage status
            if cut_row:
                try:
                    stage_status: dict[str, str] = json.loads(cut_row[1] or "{}")
                except (json.JSONDecodeError, TypeError):
                    stage_status = {}
                stage_status[stage] = "retake"
                await cur.execute(
                    """UPDATE vertex_animeka
                       SET stage_status=%s, priority='retake'
                       WHERE vertex_id=%s""",
                    [json.dumps(stage_status), cut_vertex_id],
                )

        finally:
            await conn.close()

    except Exception as exc:  # noqa: BLE001
        _log.exception("submit_retake insert failed")
        return {"error": f"insert: {exc!s}"[:300]}

    cid = _cid_stub(vertex_id)
    return {"result_uri": vertex_id, "result_cid": cid}


async def _node_emit_audit(state: _SubmitRetakeState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.submitRetake",
        object_id=f"submitRetake:{state.get('result_uri', '')}:{int(time.time())}",
        object_type="animeka.retake",
        attributes={
            "targetUri": state.get("target_uri") or "",
            "stage": state.get("stage") or "",
            "severity": state.get("severity") or "minor",
            "uri": state.get("result_uri") or "",
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_SubmitRetakeState)
    g.add_node("insert", _node_insert,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "insert")
    g.add_edge("insert", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="submit_retake")
