"""media-gamers `health` graph — simplest possible end-to-end probe.

NSID: com.etzhayyim.apps.media_gamers.health

Returns {"ok": True, "service": "lg-media-gamers", "version": "0.1.0"}
along with RW connectivity status.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_media_gamers.audit import emit_audit_bg

_log = logging.getLogger(__name__)

_RW_URL = os.environ.get("RW_URL") or os.environ.get("LG_CHECKPOINTER_URL", "")
_APP_DID = os.environ.get("MEDIA_GAMERS_APP_DID", "did:web:media-gamers.etzhayyim.com")


class _HealthState(TypedDict, total=False):
    ok: bool
    service: str
    version: str
    rw_ok: bool
    rw_latency_ms: int
    server_now: str
    error: str | None


async def _node_check(state: _HealthState) -> dict[str, Any]:
    result: dict[str, Any] = {
        "service": "lg-media-gamers",
        "version": "0.1.0",
        "server_now": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if not _RW_URL:
        return {**result, "ok": True, "rw_ok": False}
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
            **result,
            "ok": True,
            "rw_ok": True,
            "rw_latency_ms": int((time.monotonic() - started) * 1000),
        }
    except Exception as exc:  # noqa: BLE001
        return {**result, "ok": True, "rw_ok": False, "error": f"rw: {exc!s}"[:200]}


async def _node_audit(state: _HealthState) -> dict[str, Any]:
    emit_audit_bg(
        actor=_APP_DID,
        activity="media_gamers.health.check",
        object_id=f"health:{int(time.time())}",
        object_type="media_gamers.health",
        attributes={
            "ok": state.get("ok", True),
            "rwOk": state.get("rw_ok", False),
            "rwLatencyMs": state.get("rw_latency_ms", 0),
        },
    )
    return {}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_HealthState)
    g.add_node("check", _node_check)
    g.add_node("audit", _node_audit)
    g.add_edge(START, "check")
    g.add_edge("check", "audit")
    g.add_edge("audit", END)
    return g


GRAPH = _build().compile(name="health")
