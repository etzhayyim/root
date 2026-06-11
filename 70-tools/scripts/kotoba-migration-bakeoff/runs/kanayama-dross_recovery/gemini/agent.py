"""DrossRecoveryCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mocked DrossPhase and transitions from .state_machine
class DrossPhase(Enum):
    INIT = "init"
    COLLECTED = "collected"
    SALT_CAKE_PROCESSED = "salt_cake_processed"
    SECONDARY_AL_RECOVERED = "secondary_al_recovered"
    K_SALT_RECYCLED = "k_salt_recycled"
    RECORD_EMITTED = "record_emitted"

def transition_to_dross_collected(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("dross_state", {})
    return {"dross_state": {**ds, "phase": DrossPhase.COLLECTED.value, "completionPct": 20}}

def transition_to_salt_cake_processed(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("dross_state", {})
    return {"dross_state": {**ds, "phase": DrossPhase.SALT_CAKE_PROCESSED.value, "completionPct": 40}}

def transition_to_secondary_al_recovered(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("dross_state", {})
    return {"dross_state": {**ds, "phase": DrossPhase.SECONDARY_AL_RECOVERED.value, "completionPct": 60}}

def transition_to_k_salt_recycled(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("dross_state", {})
    return {"dross_state": {**ds, "phase": DrossPhase.K_SALT_RECYCLED.value, "completionPct": 80}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    ds = state.get("dross_state", {})
    return {
        "dross_state": {**ds, "phase": DrossPhase.RECORD_EMITTED.value, "completionPct": 100},
        "recovery_record": {"lotId": ds.get("lotId", "unknown"), "finalized": True}
    }

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"dross_state": {
        "phase": DrossPhase.INIT.value,
        "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
        "completionPct": 0,
    }}

def _collect(s: dict[str, Any]) -> dict[str, Any]: return transition_to_dross_collected(s)
def _salt_cake(s: dict[str, Any]) -> dict[str, Any]: return transition_to_salt_cake_processed(s)
def _al(s: dict[str, Any]) -> dict[str, Any]: return transition_to_secondary_al_recovered(s)
def _k_salt(s: dict[str, Any]) -> dict[str, Any]: return transition_to_k_salt_recycled(s)
def _record(s: dict[str, Any]) -> dict[str, Any]: return transition_to_record_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("collect", _collect)
_g.add_node("salt_cake", _salt_cake)
_g.add_node("al", _al)
_g.add_node("k_salt", _k_salt)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "collect")
_g.add_edge("collect", "salt_cake")
_g.add_edge("salt_cake", "al")
_g.add_edge("al", "k_salt")
_g.add_edge("k_salt", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
