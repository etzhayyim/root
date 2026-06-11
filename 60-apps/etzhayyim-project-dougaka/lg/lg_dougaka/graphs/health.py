"""dougaka `health` graph — liveness check."""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class _HealthState(TypedDict, total=False):
    ok: bool


async def _node_ping(state: _HealthState) -> dict:
    return {"ok": True}


def _build() -> StateGraph:
    g: StateGraph = StateGraph(_HealthState)
    g.add_node("ping", _node_ping)
    g.add_edge(START, "ping")
    g.add_edge("ping", END)
    return g


GRAPH = _build().compile(name="health")
