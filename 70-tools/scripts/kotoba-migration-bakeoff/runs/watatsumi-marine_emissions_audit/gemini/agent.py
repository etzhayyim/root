"""agent.py — MarineEmissionsAuditCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mock state_machine.py ---
class EmissionsAuditPhase:
    class INIT: value = "init"
    class MARPOL: value = "marpol_scanned"
    class BWMC: value = "bwmc_scanned"
    class BIOFOULING: value = "biofouling_scanned"
    class RECORD: value = "record_emitted"

def transition_to_marpol_scan(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("emissions_audit_state", {})
    return {"emissions_audit_state": {**s, "phase": "marpol_scanned", "completionPct": 25}}

def transition_to_bwmc_scan(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("emissions_audit_state", {})
    return {"emissions_audit_state": {**s, "phase": "bwmc_scanned", "completionPct": 50}}

def transition_to_biofouling_scan(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("emissions_audit_state", {})
    return {"emissions_audit_state": {**s, "phase": "biofouling_scanned", "completionPct": 75}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("emissions_audit_state", {})
    return {
        "emissions_audit_state": {**s, "phase": "record_emitted", "completionPct": 100},
        "audit_finalized_record": {
            "craftId": s.get("craftId"),
            "status": "finalized",
            "audit_trail": "R0-mock"
        }
    }

# --- Node functions ---
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "emissions_audit_state": {
            "phase": EmissionsAuditPhase.INIT.value,
            "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
            "completionPct": 0,
        }
    }

def _marpol(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_marpol_scan(s)

def _bwmc(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_bwmc_scan(s)

def _biofouling(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_biofouling_scan(s)

def _record(s: dict[str, Any]) -> dict[str, Any]:
    return transition_to_record_emitted(s)

# --- Graph construction ---
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("marpol", _marpol)
_g.add_node("bwmc", _bwmc)
_g.add_node("biofouling", _biofouling)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "marpol")
_g.add_edge("marpol", "bwmc")
_g.add_edge("bwmc", "biofouling")
_g.add_edge("biofouling", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
