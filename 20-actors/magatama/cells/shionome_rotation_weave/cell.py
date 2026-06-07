"""
shionome_rotation_weave — top rotation pair どこからどこへ (shionome).
Resident in Kotoba WASM. Per ADR-2606072200. Aggregate, edge-primary (G4); no per-asset score.
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
from shionome_core import top_rotation  # noqa: E402

_r0_marker = True


class WeaveState(TypedDict, total=False):
    context: dict
    flows: list
    rotation: dict


def _weave(state: WeaveState) -> dict:
    flows = state.get("flows") or (state.get("context", {}) or {}).get("flows", [])
    return {"rotation": top_rotation(flows) or {}}


_g = StateGraph(WeaveState)
_g.add_node("weave", _weave)
_g.add_edge(START, "weave")
_g.add_edge("weave", END)
compiled = _g.compile(checkpointer=KotobaCheckpointer())

if wit_world:
    class WitWorld(wit_world.WitWorld):
        def run(self, ctx_cbor: bytes) -> bytes:
            return handle_invoke(ctx_cbor, compiled)
