"""
shosha.tradeBookRecompute — LangGraph StateGraph port (ADR-2605080600 Phase 5).

Replaces the Zeebe timer-start BPMN `shosha_trade_book_recompute` (R/PT4H).
Triggered by K8s CronJob (every 4 hours) via POST /runs.

Graph:
  START → recompute_exposure → recompute_pnl → emit_audit → END

State:
  exposureRows    int   snapshot rows written (output)
  pnlRows         int   PnL daily recompute rows (output)
  ok              bool  overall success flag (output)
  error           str   error message if ok=False (output)
"""

from __future__ import annotations

import asyncio
import uuid
import time as _time
from typing import Any, TypedDict

from pymagatama.db_sync import sync_cursor


# ── State ──────────────────────────────────────────────────────────────

class ShoshaTradeBookState(TypedDict, total=False):
    exposureRows: int
    pnlRows: int
    ok: bool
    error: str | None


# ── Nodes ─────────────────────────────────────────────────────────────

def recompute_exposure(state: ShoshaTradeBookState) -> dict:
    """Recompute exposure snapshots from open trades."""
    from pymagatama.primitives.shosha import task_shosha_exposure_recompute

    try:
        result = asyncio.run(task_shosha_exposure_recompute())
        return {"exposureRows": result.get("rows", 0)}
    except Exception as e:
        return {"exposureRows": 0, "ok": False, "error": str(e)}


def recompute_pnl(state: ShoshaTradeBookState) -> dict:
    """Recompute daily PnL for open and recently-closed trades."""
    from pymagatama.primitives.shosha import task_shosha_pnl_daily_recompute

    try:
        result = asyncio.run(task_shosha_pnl_daily_recompute())
        return {"pnlRows": result.get("rows", 0), "ok": True}
    except Exception as e:
        return {"pnlRows": 0, "ok": False, "error": str(e)}


def emit_audit(state: ShoshaTradeBookState) -> dict:
    """Write OCEL audit row (non-fatal)."""
    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_repo_commit
                  (vertex_id, repo, collection, rkey, action, ts_ms, record_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid.uuid4()),
                    "did:web:shosha.etzhayyim.com",
                    "ai.gftd.apps.shosha.tradeBookRecompute",
                    f"lg-{int(_time.time() * 1000)}",
                    "create",
                    int(_time.time() * 1000),
                    f'{{"exposureRows":{state.get("exposureRows",0)},'
                    f'"pnlRows":{state.get("pnlRows",0)},'
                    f'"ok":{str(state.get("ok",True)).lower()}}}',
                ),
            )
    except Exception:
        pass
    return {}


# ── Graph factory ──────────────────────────────────────────────────────

def build_graph():
    """Build and compile the shosha tradeBookRecompute StateGraph."""
    from langgraph.graph import END, StateGraph

    builder = StateGraph(ShoshaTradeBookState)
    builder.add_node("recompute_exposure", recompute_exposure)
    builder.add_node("recompute_pnl", recompute_pnl)
    builder.add_node("emit_audit", emit_audit)

    builder.set_entry_point("recompute_exposure")
    builder.add_edge("recompute_exposure", "recompute_pnl")
    builder.add_edge("recompute_pnl", "emit_audit")
    builder.add_edge("emit_audit", END)

    return builder.compile()
