"""
shionome_ingest — cross-asset capital-flow intake membrane (shionome).
Resident in Kotoba WASM. Per ADR-2606072200.

Screens a public market-data batch from context (G1/G2/G3, トレードはしない) and emits the
validated flows downstream. Live market-data ingest into the substrate is Council Lv6+ + operator
gated (G8); this cell screens whatever batch is already in context (offline / substrate-resident).
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
from shionome_core import screen_flows  # noqa: E402

_r0_marker = True


class IngestState(TypedDict, total=False):
    context: dict
    flows: list
    refusal: str


def _screen(state: IngestState) -> dict:
    ctx = state.get("context", {}) or {}
    flows = ctx.get("market_batch", []) or []
    try:
        return {"flows": screen_flows(flows), "refusal": ""}
    except ValueError as e:
        # refuse the whole batch (G2/G3) — never silently ingest a trade-token / undersourced flow
        return {"flows": [], "refusal": str(e)}


_g = StateGraph(IngestState)
_g.add_node("screen", _screen)
_g.add_edge(START, "screen")
_g.add_edge("screen", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

if wit_world:
    class WitWorld(wit_world.WitWorld):
        def run(self, ctx_cbor: bytes) -> bytes:
            return handle_invoke(ctx_cbor, compiled)
