"""agent.py — VinAttestationBinderCell compiled to WASM.

Port of VinAttestationBinderCell onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocked state_machine.py ---
class BinderPhase(Enum):
    INIT = "init"
    RECORDS_COLLECTED = "records_collected"
    VIN_ASSIGNED = "vin_assigned"
    VEHICLE_DID_ISSUED = "vehicle_did_issued"
    KOTOBA_DATOMIC_ANCHORED = "kotoba-datomic_anchored"
    RECORD_EMITTED = "record_emitted"

def transition_to_records_collected(state: dict[str, Any]) -> dict[str, Any]:
    return {"binder_state": {**state.get("binder_state", {}), "phase": BinderPhase.RECORDS_COLLECTED.value, "completionPct": 20}}

def transition_to_vin_assigned(state: dict[str, Any]) -> dict[str, Any]:
    return {"binder_state": {**state.get("binder_state", {}), "phase": BinderPhase.VIN_ASSIGNED.value, "completionPct": 40}}

def transition_to_vehicle_did_issued(state: dict[str, Any]) -> dict[str, Any]:
    return {"binder_state": {**state.get("binder_state", {}), "phase": BinderPhase.VEHICLE_DID_ISSUED.value, "completionPct": 60}}

def transition_to_kotoba-datomic_anchored(state: dict[str, Any]) -> dict[str, Any]:
    return {"binder_state": {**state.get("binder_state", {}), "phase": BinderPhase.KOTOBA_DATOMIC_ANCHORED.value, "completionPct": 80}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    binder_state = state.get("binder_state", {})
    return {
        "binder_state": {**binder_state, "phase": BinderPhase.RECORD_EMITTED.value, "completionPct": 100},
        "emitted_record": {
            "chassisId": binder_state.get("chassisId"),
            "vin": "VIN-MOCK-123456789",
            "vehicle_did": "did:kotoba-datomic:vehicle:mock",
            "anchored": True
        }
    }
# -------------------------------

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"binder_state": {
        "phase": BinderPhase.INIT.value,
        "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
        "completionPct": 0,
    }}

def _collect(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_records_collected(s)

def _vin(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_vin_assigned(s)

def _did(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_vehicle_did_issued(s)

def _anchor(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_kotoba-datomic_anchored(s)

def _record(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_record_emitted(s)

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("collect", _collect)
_g.add_node("vin", _vin)
_g.add_node("did", _did)
_g.add_node("anchor", _anchor)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "collect")
_g.add_edge("collect", "vin")
_g.add_edge("vin", "did")
_g.add_edge("did", "anchor")
_g.add_edge("anchor", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
