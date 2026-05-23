"""yatabase — Business Operating ReAct graph (ADR-2605220100).

Minimal stub: pymagatama.langgraph_graphs.bo_react_agent does not exist yet.
This prevents server.py import from crashing the pod.
Replace with a full ReAct implementation once bo_react_agent is available.

NSID: ai.gftd.apps.yata.lg.businessOperatingReact.run
Graph ID: business_operating_react
Cron: daily 21:00 UTC (06:00 JST)
"""

from __future__ import annotations

import time
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class _BOReactState(TypedDict, total=False):
    product_id: str
    ok: bool
    ts: int
    note: str


def _stub(state: _BOReactState) -> _BOReactState:
    # bo_react_agent pending; returns a no-op result so cron does not fail.
    return {
        "ok": True,
        "ts": int(time.time() * 1000),
        "note": "bo_react_agent not yet available — stub pass-through",
    }


_g: StateGraph = StateGraph(_BOReactState)
_g.add_node("run", _stub)
_g.add_edge(START, "run")
_g.add_edge("run", END)
GRAPH = _g.compile()
