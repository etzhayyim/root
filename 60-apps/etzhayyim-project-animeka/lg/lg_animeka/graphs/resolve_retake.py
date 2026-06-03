"""animeka `resolveRetake` graph — mark retake resolved/acknowledged.

NSID: com.etzhayyim.animeka.resolveRetake
Updates retake.status and un-flips cut.priority if no open retakes remain.
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


def _rkey_from_id(val: str) -> str:
    if val.startswith("at://"):
        return val.rstrip("/").rsplit("/", 1)[-1]
    return val


class _ResolveRetakeState(TypedDict, total=False):
    retake_id: str
    status: str
    resolved_by_uri: str | None
    # output
    result_retake_id: str | None
    result_status: str | None
    result_cut_priority: str | None
    error: str | None


async def _node_update(state: _ResolveRetakeState) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    retake_id = state.get("retake_id") or ""
    new_status = state.get("status") or ""
    if not retake_id or not new_status:
        return {"error": "retakeId and status are required"}

    retake_rkey = _rkey_from_id(retake_id)

    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()

            # Fetch current retake to get cut_id
            await cur.execute(
                """SELECT vertex_id, cut_id FROM vertex_animeka
                   WHERE collection='com.etzhayyim.animeka.retake' AND rkey=%s LIMIT 1""",
                [retake_rkey],
            )
            row = await cur.fetchone()
            if not row:
                return {"error": f"retake not found: {retake_rkey}"}

            retake_vertex_id, cut_vertex_id = row

            # Update retake status (and optional resolvedByUri stored in target_uri)
            if state.get("resolved_by_uri"):
                await cur.execute(
                    """UPDATE vertex_animeka
                       SET status=%s, target_uri=%s
                       WHERE vertex_id=%s""",
                    [new_status, state["resolved_by_uri"], retake_vertex_id],
                )
            else:
                await cur.execute(
                    """UPDATE vertex_animeka SET status=%s WHERE vertex_id=%s""",
                    [new_status, retake_vertex_id],
                )

            # Check remaining open retakes for the cut
            cut_priority = "normal"
            if cut_vertex_id:
                await cur.execute(
                    """SELECT COUNT(*) FROM vertex_animeka
                       WHERE collection='com.etzhayyim.animeka.retake'
                         AND cut_id=%s
                         AND COALESCE(status,'open') IN ('open','acknowledged','inProgress')""",
                    [cut_vertex_id],
                )
                count_row = await cur.fetchone()
                open_count = int(count_row[0]) if count_row else 0

                if open_count == 0:
                    await cur.execute(
                        """UPDATE vertex_animeka SET priority='normal'
                           WHERE vertex_id=%s""",
                        [cut_vertex_id],
                    )
                else:
                    cut_priority = "retake"

        finally:
            await conn.close()

    except Exception as exc:  # noqa: BLE001
        _log.exception("resolve_retake update failed")
        return {"error": f"update: {exc!s}"[:300]}

    return {
        "result_retake_id": retake_rkey,
        "result_status": new_status,
        "result_cut_priority": cut_priority,
    }


async def _node_emit_audit(state: _ResolveRetakeState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.resolveRetake",
        object_id=f"resolveRetake:{state.get('retake_id', '')}:{int(time.time())}",
        object_type="animeka.retake",
        attributes={
            "retakeId": state.get("retake_id") or "",
            "status": state.get("result_status") or "",
            "cutPriority": state.get("result_cut_priority") or "",
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_ResolveRetakeState)
    g.add_node("update", _node_update,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "update")
    g.add_edge("update", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="resolve_retake")
