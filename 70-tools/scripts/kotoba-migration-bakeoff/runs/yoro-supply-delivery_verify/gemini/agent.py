"""agent.py — SupplyCell compiled to WASM.

Port of original_cell.py onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"supply_state": {"phase": "init", "projectId": state.get("projectId", "unknown"), "completionPct": 0}, "next_node": "process"}

def _process(state: dict[str, Any]) -> dict[str, Any]:
    return {"supply_state": {**state.get("supply_state", {}), "phase": "complete", "completionPct": 100}, "next_node": "end"}

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("process", _process)
_g.add_edge(START, "init")
_g.add_edge("init", "process")
_g.add_edge("process", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
