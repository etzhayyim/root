"""
shionome_flow_graph — per-bucket net capital-flow index (shionome).
Resident in Kotoba WASM. Per ADR-2606072200. Capital-movement kinds only; edge-primary (G4).
"""
from typing import TypedDict
try:
    import wit_world
except ImportError:
    wit_world = None

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shionome_core import net_flow  # noqa: E402

_r0_marker = True


class GraphState(TypedDict, total=False):
    context: dict
    flows: list
    net: list


def _index(state: GraphState) -> dict:
    flows = state.get("flows") or (state.get("context", {}) or {}).get("flows", [])
    return {"net": net_flow(flows)}


_g = StateGraph(GraphState)
_g.add_node("index", _index)
_g.add_edge(START, "index")
_g.add_edge("index", END)
compiled = _g.compile(checkpointer=KotobaCheckpointer())

if wit_world:
    class WitWorld(wit_world.WitWorld):
        def run(self, ctx_cbor: bytes) -> bytes:
            return handle_invoke(ctx_cbor, compiled)
