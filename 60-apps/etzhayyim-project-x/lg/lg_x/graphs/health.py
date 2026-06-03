"""x `health` graph — simplest possible end-to-end probe.

Replaces BPMN `x_health` (NSID: com.etzhayyim.apps.x.health).
Confirms the server can:
  1. Compile a graph
  2. Reach RW (SELECT 1)
  3. Emit audit (fire-and-forget)

Used as the primary smoke endpoint by the deploy runbook.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from lg_x.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_DEFAULT_APP_DID = os.environ.get("X_APP_DID", "did:web:x.etzhayyim.com")


class _HealthState(TypedDict, total=False):
    ok: bool
    rw_ok: bool
    rw_latency_ms: int
    server_now: str
    error: str | None


async def _node_check_rw(state: _HealthState) -> dict[str, Any]:
    if not _RW_URL:
        return {"rw_ok": False, "error": "RW_URL not set"}
    try:
        import psycopg  # type: ignore
        started = time.monotonic()
        conn = await psycopg.AsyncConnection.connect(_RW_URL, autocommit=True, connect_timeout=5)
        try:
            cur = conn.cursor()
            await cur.execute("SELECT 1")
            await cur.fetchone()
        finally:
            await conn.close()
        return {
            "rw_ok": True,
            "rw_latency_ms": int((time.monotonic() - started) * 1000),
        }
    except Exception as exc:  # noqa: BLE001
        return {"rw_ok": False, "error": f"rw: {exc!s}"[:200]}


async def _node_summarize(state: _HealthState) -> dict[str, Any]:
    return {
        "ok": bool(state.get("rw_ok")),
        "server_now": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


async def _node_emit_audit(state: _HealthState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_DEFAULT_APP_DID,
        activity="x.health.check",
        object_id=f"health:{int(time.time())}",
        object_type="x.health",
        attributes={
            "ok": state.get("ok", False),
            "rwOk": state.get("rw_ok", False),
            "rwLatencyMs": state.get("rw_latency_ms", 0),
        },
    )
    return {}


def _build():
    g: StateGraph = StateGraph(_HealthState)
    g.add_node("check_rw", _node_check_rw,
               retry_policy=RetryPolicy(max_attempts=2))
    g.add_node("summarize", _node_summarize)
    g.add_node("emit_audit", _node_emit_audit)
    g.add_edge(START, "check_rw")
    g.add_edge("check_rw", "summarize")
    g.add_edge("summarize", "emit_audit")
    g.add_edge("emit_audit", END)
    return g


GRAPH = _build().compile(name="health")
