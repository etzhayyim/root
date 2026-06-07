"""
shionome_regime_observer — FACTUAL cross-asset regime risk-on/off/mixed (shionome).
Resident in Kotoba WASM. Per ADR-2606072200. Descriptive, never advice (G2, トレードはしない).
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
from shionome_core import regime  # noqa: E402

_r0_marker = True


class RegimeState(TypedDict, total=False):
    context: dict
    net: list
    regime: dict


def _observe(state: RegimeState) -> dict:
    ctx = state.get("context", {}) or {}
    net = state.get("net") or ctx.get("net", [])
    risk_tags = ctx.get("risk_tags", {})
    return {"regime": regime(net, risk_tags)}


_g = StateGraph(RegimeState)
_g.add_node("observe", _observe)
_g.add_edge(START, "observe")
_g.add_edge("observe", END)
compiled = _g.compile(checkpointer=KotobaCheckpointer())

if wit_world:
    class WitWorld(wit_world.WitWorld):
        def run(self, ctx_cbor: bytes) -> bytes:
            return handle_invoke(ctx_cbor, compiled)
