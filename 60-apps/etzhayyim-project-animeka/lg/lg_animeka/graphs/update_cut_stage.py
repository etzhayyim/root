"""animeka `updateCutStage` graph — update pipeline stage status on a cut.

NSID: com.etzhayyim.animeka.updateCutStage
Mutates vertex_animeka.stage_status (JSON map) for the given stage key.
Assignees map is also patched if assigneeDid is supplied.
"""
from __future__ import annotations

import json
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


class _UpdateCutStageState(TypedDict, total=False):
    cut_id: str
    stage: str
    status: str | None
    assignee_did: str | None
    # output
    result_cut_id: str | None
    result_stage: str | None
    result_status: str | None
    derived_count: int
    error: str | None


async def _node_update(state: _UpdateCutStageState) -> dict[str, Any]:
    if not _RW_URL:
        return {"error": "RW_URL not set"}
    cut_id = state.get("cut_id") or ""
    stage = state.get("stage") or ""
    if not cut_id or not stage:
        return {"error": "cut_id and stage are required"}

    cut_rkey = _rkey_from_id(cut_id)
    new_status = state.get("status") or "in_progress"
    assignee_did = state.get("assignee_did")

    try:
        import psycopg  # type: ignore

        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True)
        try:
            cur = conn.cursor()

            # Fetch current stage_status and assignees
            await cur.execute(
                """SELECT vertex_id, stage_status, assignees FROM vertex_animeka
                   WHERE collection='com.etzhayyim.animeka.cut' AND rkey=%s LIMIT 1""",
                [cut_rkey],
            )
            row = await cur.fetchone()
            if not row:
                return {"error": f"cut not found: {cut_rkey}"}

            vertex_id, stage_status_json, assignees_json = row

            # Patch stage_status
            try:
                stage_status: dict[str, str] = json.loads(stage_status_json or "{}")
            except (json.JSONDecodeError, TypeError):
                stage_status = {}
            stage_status[stage] = new_status

            # Patch assignees
            try:
                assignees: dict[str, str] = json.loads(assignees_json or "{}")
            except (json.JSONDecodeError, TypeError):
                assignees = {}
            if assignee_did:
                assignees[stage] = assignee_did

            # Derive overall cut status from stage statuses
            all_statuses = list(stage_status.values())
            if any(s == "retake" for s in all_statuses):
                cut_priority = "retake"
            elif all(s == "approved" for s in all_statuses):
                cut_priority = "approved"
            else:
                cut_priority = "normal"

            await cur.execute(
                """
                UPDATE vertex_animeka
                SET stage_status = %s, assignees = %s, priority = %s
                WHERE vertex_id = %s
                """,
                [
                    json.dumps(stage_status),
                    json.dumps(assignees),
                    cut_priority,
                    vertex_id,
                ],
            )

        finally:
            await conn.close()

    except Exception as exc:  # noqa: BLE001
        _log.exception("update_cut_stage update failed")
        return {"error": f"update: {exc!s}"[:300]}

    return {
        "result_cut_id": cut_rkey,
        "result_stage": stage,
        "result_status": new_status,
        "derived_count": 0,
    }


async def _node_emit_audit(state: _UpdateCutStageState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="animeka.updateCutStage",
        object_id=f"updateCutStage:{state.get('cut_id', '')}:{int(time.time())}",
        object_type="animeka.cut",
        attributes={
            "cutId": state.get("cut_id") or "",
            "stage": state.get("stage") or "",
            "status": state.get("result_status") or "",
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_UpdateCutStageState)
    g.add_node("update", _node_update,
               retry_policy=RetryPolicy(max_attempts=2, backoff_factor=2.0))
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "update")
    g.add_edge("update", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="update_cut_stage")
