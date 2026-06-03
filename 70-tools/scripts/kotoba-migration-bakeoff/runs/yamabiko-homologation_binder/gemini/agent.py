"""HomologationBinderCell — yamabiko R0 Pregel cell (L5c terminal).

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock constants/classes from state_machine to make it standalone
class HomologationPhase:
    class INIT: value = "init"
    class COLLECTED: value = "records_collected"
    class SERIAL: value = "serial_assigned"
    class DID: value = "trainset_did_issued"
    class AUTHORITY: value = "authority_review"
    class ANCHORED: value = "kotoba-datomic_anchored"
    class EMITTED: value = "record_emitted"

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"homologation_state": {
        "phase": HomologationPhase.INIT.value,
        "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
        "completionPct": 0,
    }}

def _collect(s):
    ss = s.get("homologation_state", {})
    return {"homologation_state": {**ss, "phase": HomologationPhase.COLLECTED.value, "completionPct": 20}}

def _serial(s):
    ss = s.get("homologation_state", {})
    return {"homologation_state": {**ss, "phase": HomologationPhase.SERIAL.value, "completionPct": 40}}

def _did(s):
    ss = s.get("homologation_state", {})
    return {"homologation_state": {**ss, "phase": HomologationPhase.DID.value, "completionPct": 60}}

def _authority(s):
    ss = s.get("homologation_state", {})
    return {"homologation_state": {**ss, "phase": HomologationPhase.AUTHORITY.value, "completionPct": 80}}

def _anchor(s):
    ss = s.get("homologation_state", {})
    return {"homologation_state": {**ss, "phase": HomologationPhase.ANCHORED.value, "completionPct": 90}}

def _record(s):
    ss = s.get("homologation_state", {})
    return {"homologation_state": {**ss, "phase": HomologationPhase.EMITTED.value, "completionPct": 100}}

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("collect", _collect)
_g.add_node("serial", _serial)
_g.add_node("did", _did)
_g.add_node("authority", _authority)
_g.add_node("anchor", _anchor)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "collect")
_g.add_edge("collect", "serial")
_g.add_edge("serial", "did")
_g.add_edge("did", "authority")
_g.add_edge("authority", "anchor")
_g.add_edge("anchor", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
