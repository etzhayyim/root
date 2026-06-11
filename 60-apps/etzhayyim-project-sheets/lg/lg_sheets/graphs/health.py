"""lg-sheets ``health`` graph — minimal liveness probe (langgraph dev)."""

from __future__ import annotations

import os
import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class _State(TypedDict, total=False):
    ok: bool
    ts: int
    version: str


def _probe(_state: _State) -> _State:
    return {
        "ok": True,
        "ts": int(time.time() * 1000),
        "version": os.environ.get("LG_SHEETS_VERSION", "0.1.0"),
    }


_g: StateGraph = StateGraph(_State)
_g.add_node("probe", _probe)
_g.add_edge(START, "probe")
_g.add_edge("probe", END)
GRAPH = _g.compile()
