"""MassBalanceBinderCell — kanayama R0 Pregel cell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.

Build:
    bash /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/scripts/build-pywasm.sh agent.py agent.wasm
"""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocks for .state_machine ---

class BalancePhase:
    INIT = type('Enum', (), {'value': 'init'})
    RECORDS_COLLECTED = type('Enum', (), {'value': 'records_collected'})
    MASS_BALANCE_COMPUTED = type('Enum', (), {'value': 'mass_balance_computed'})
    KOTOBA_DATOMIC_ANCHORED = type('Enum', (), {'value': 'kotoba-datomic_anchored'})
    RECORD_EMITTED = type('Enum', (), {'value': 'record_emitted'})

def transition_to_records_collected(state: dict[str, Any]) -> dict[str, Any]:
    return {"balance_state": {**state.get("balance_state", {}), "phase": BalancePhase.RECORDS_COLLECTED.value, "completionPct": 25}}

def transition_to_mass_balance_computed(state: dict[str, Any]) -> dict[str, Any]:
    return {"balance_state": {**state.get("balance_state", {}), "phase": BalancePhase.MASS_BALANCE_COMPUTED.value, "completionPct": 50}}

def transition_to_kotoba-datomic_anchored(state: dict[str, Any]) -> dict[str, Any]:
    return {"balance_state": {**state.get("balance_state", {}), "phase": BalancePhase.KOTOBA_DATOMIC_ANCHORED.value, "completionPct": 75}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    return {"balance_state": {**state.get("balance_state", {}), "phase": BalancePhase.RECORD_EMITTED.value, "completionPct": 100}, "final_record": {"lotId": state.get("balance_state", {}).get("lotId"), "status": "emitted"}}

# --- Node Functions ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"balance_state": {
        "phase": BalancePhase.INIT.value,
        "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
        "completionPct": 0,
    }}

def _collect(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_records_collected(s)

def _compute(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_mass_balance_computed(s)

def _anchor(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_kotoba-datomic_anchored(s)

def _record(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_record_emitted(s)

# --- Graph Definition ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("collect", _collect)
_g.add_node("compute", _compute)
_g.add_node("anchor", _anchor)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "collect")
_g.add_edge("collect", "compute")
_g.add_edge("compute", "anchor")
_g.add_edge("anchor", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
