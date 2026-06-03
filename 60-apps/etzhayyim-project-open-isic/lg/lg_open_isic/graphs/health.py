"""Health-check graph — returns server liveness immediately."""
from __future__ import annotations
from typing import TypedDict
from langgraph.graph import StateGraph, END

class HealthState(TypedDict):
    ok: bool

def _check(state: HealthState) -> dict:
    return {"ok": True}

_b = StateGraph(HealthState)
_b.add_node("check", _check)
_b.set_entry_point("check")
_b.add_edge("check", END)
GRAPH = _b.compile()
