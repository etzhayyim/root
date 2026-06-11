"""CarbodyFabricationCell compiled to WASM.

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

# Mocking .state_machine imports
class CarbodyPhase:
    INIT = type('Enum', (), {'value': 'init'})
    EXTRUSION_VERIFIED = 'extrusion_verified'
    FSW_SEAMS_COMPLETE = 'fsw_seams_complete'
    SPOT_WELDS_COMPLETE = 'spot_welds_complete'
    DIMENSIONAL_QA_PASSED = 'dimensional_qa_passed'
    ATTESTATION_EMITTED = 'attestation_emitted'

def transition_to_extrusion_verified(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("carbody_state", {}).copy()
    cs.update({"phase": CarbodyPhase.EXTRUSION_VERIFIED, "completionPct": 20})
    return {"carbody_state": cs}

def transition_to_fsw_seams_complete(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("carbody_state", {}).copy()
    cs.update({"phase": CarbodyPhase.FSW_SEAMS_COMPLETE, "completionPct": 40})
    return {"carbody_state": cs}

def transition_to_spot_welds_complete(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("carbody_state", {}).copy()
    cs.update({"phase": CarbodyPhase.SPOT_WELDS_COMPLETE, "completionPct": 60})
    return {"carbody_state": cs}

def transition_to_dimensional_qa_passed(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("carbody_state", {}).copy()
    cs.update({"phase": CarbodyPhase.DIMENSIONAL_QA_PASSED, "completionPct": 80})
    return {"carbody_state": cs}

def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("carbody_state", {}).copy()
    cs.update({"phase": CarbodyPhase.ATTESTATION_EMITTED, "completionPct": 100})
    return {"carbody_state": cs, "attestation": {"verified": True}}

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"carbody_state": {
        "phase": CarbodyPhase.INIT.value,
        "trainsetId": state.get("trainsetId", "YAMABIKO-TRAINSET-0001"),
        "carIndex": state.get("carIndex", 0),
        "completionPct": 0,
    }}

def _extrusion(s): return transition_to_extrusion_verified(s)
def _fsw(s): return transition_to_fsw_seams_complete(s)
def _spot(s): return transition_to_spot_welds_complete(s)
def _qa(s): return transition_to_dimensional_qa_passed(s)
def _attestation(s): return transition_to_attestation_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("extrusion", _extrusion)
_g.add_node("fsw", _fsw)
_g.add_node("spot", _spot)
_g.add_node("qa", _qa)
_g.add_node("attestation", _attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "extrusion")
_g.add_edge("extrusion", "fsw")
_g.add_edge("fsw", "spot")
_g.add_edge("spot", "qa")
_g.add_edge("qa", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
