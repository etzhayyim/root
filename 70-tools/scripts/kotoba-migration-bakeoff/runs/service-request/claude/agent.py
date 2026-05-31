"""service_request_kotoba — ServiceRequestCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API so it
compiles to a kotoba-node component.

Build:
    ../../scripts/build-pywasm.sh agent.py -o agent.wasm
"""

from __future__ import annotations
from typing import Any, TypedDict
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401


class ServiceRequestStateDict(TypedDict, total=False):
    projectId: str
    utility_state: dict[str, Any]
    next_node: str


def _init(state: ServiceRequestStateDict) -> ServiceRequestStateDict:
    return {
        "utility_state": {
            "phase": "init",
            "projectId": state.get("projectId", "unknown"),
            "completionPct": 0,
        },
        "next_node": "process",
    }


def _process(state: ServiceRequestStateDict) -> ServiceRequestStateDict:
    return {
        "utility_state": {
            **state.get("utility_state", {}),
            "phase": "complete",
            "completionPct": 100,
        },
        "next_node": "end",
    }


_g = StateGraph(ServiceRequestStateDict)
_g.add_node("init", _init)
_g.add_node("process", _process)
_g.add_edge(START, "init")
_g.add_edge("init", "process")
_g.add_edge("process", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())


class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
