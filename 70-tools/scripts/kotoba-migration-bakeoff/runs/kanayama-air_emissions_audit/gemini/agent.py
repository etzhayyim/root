"""AirEmissionsAuditCell — kanayama R0 Pregel cell (cross-cutting). G8 enforcement. R0 scaffold.

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
class EmissionsPhase:
    INIT = "init"
    PFC_SCANNED = "pfc_scanned"
    SO2_NOX_SCANNED = "so2_nox_scanned"
    PARTICULATE_DIOXIN_SCANNED = "particulate_dioxin_scanned"
    LEACHATE_TESTED = "leachate_tested"
    RECORD_EMITTED = "record_emitted"

def transition_to_pfc_scanned(state: dict[str, Any]) -> dict[str, Any]:
    es = state.get("emissions_state", {})
    return {"emissions_state": {**es, "phase": EmissionsPhase.PFC_SCANNED, "completionPct": 20}}

def transition_to_so2_nox_scanned(state: dict[str, Any]) -> dict[str, Any]:
    es = state.get("emissions_state", {})
    return {"emissions_state": {**es, "phase": EmissionsPhase.SO2_NOX_SCANNED, "completionPct": 40}}

def transition_to_particulate_dioxin_scanned(state: dict[str, Any]) -> dict[str, Any]:
    es = state.get("emissions_state", {})
    return {"emissions_state": {**es, "phase": EmissionsPhase.PARTICULATE_DIOXIN_SCANNED, "completionPct": 60}}

def transition_to_leachate_tested(state: dict[str, Any]) -> dict[str, Any]:
    es = state.get("emissions_state", {})
    return {"emissions_state": {**es, "phase": EmissionsPhase.LEACHATE_TESTED, "completionPct": 80}}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    es = state.get("emissions_state", {})
    return {"emissions_state": {**es, "phase": EmissionsPhase.RECORD_EMITTED, "completionPct": 100}}

# --- Node Functions ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"emissions_state": {
        "phase": EmissionsPhase.INIT,
        "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
        "completionPct": 0,
    }}

def _pfc(s: dict[str, Any]) -> dict[str, Any]: return transition_to_pfc_scanned(s)
def _so2_nox(s: dict[str, Any]) -> dict[str, Any]: return transition_to_so2_nox_scanned(s)
def _particulate(s: dict[str, Any]) -> dict[str, Any]: return transition_to_particulate_dioxin_scanned(s)
def _leachate(s: dict[str, Any]) -> dict[str, Any]: return transition_to_leachate_tested(s)
def _record(s: dict[str, Any]) -> dict[str, Any]: return transition_to_record_emitted(s)

# --- Graph Builder ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("pfc", _pfc)
_g.add_node("so2_nox", _so2_nox)
_g.add_node("particulate", _particulate)
_g.add_node("leachate", _leachate)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "pfc")
_g.add_edge("pfc", "so2_nox")
_g.add_edge("so2_nox", "particulate")
_g.add_edge("particulate", "leachate")
_g.add_edge("leachate", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
