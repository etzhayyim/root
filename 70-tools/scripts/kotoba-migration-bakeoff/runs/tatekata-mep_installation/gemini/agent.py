from __future__ import annotations
from typing import Any
import wit_world
from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mock Constants and Classes (replacing .state_machine) ---
class MepPhase:
    INIT = "INIT"
    DUCTWORK_ROUTED = "DUCTWORK_ROUTED"
    CONDUIT_ROUTED = "CONDUIT_ROUTED"
    PIPING_ROUTED = "PIPING_ROUTED"
    PRESSURE_TEST = "PRESSURE_TEST"
    WITNESS_WAIT = "WITNESS_WAIT"
    COMPLETE = "COMPLETE"
    TEST_FAIL = "TEST_FAIL"

class MepState:
    def __init__(self, phase: str, projectId: str, completionPct: int):
        self.phase = phase
        self.projectId = projectId
        self.completionPct = completionPct

def transition_to_ductwork_routed(state: dict) -> dict:
    s = state.get("mep_state", {}).copy()
    s["phase"] = MepPhase.DUCTWORK_ROUTED
    s["completionPct"] = 15
    return {"mep_state": s, "next_node": "conduit"}

def transition_to_conduit_routed(state: dict) -> dict:
    s = state.get("mep_state", {}).copy()
    s["phase"] = MepPhase.CONDUIT_ROUTED
    s["completionPct"] = 30
    return {"mep_state": s, "next_node": "piping"}

def transition_to_piping_routed(state: dict) -> dict:
    s = state.get("mep_state", {}).copy()
    s["phase"] = MepPhase.PIPING_ROUTED
    s["completionPct"] = 45
    return {"mep_state": s, "next_node": "test"}

def transition_to_pressure_test(state: dict) -> dict:
    s = state.get("mep_state", {}).copy()
    s["phase"] = MepPhase.PRESSURE_TEST
    s["completionPct"] = 60
    return {"mep_state": s, "next_node": "witness"}

def transition_to_witness_attestation(state: dict) -> dict:
    s = state.get("mep_state", {}).copy()
    s["phase"] = MepPhase.WITNESS_WAIT
    s["completionPct"] = 80
    return {"mep_state": s, "next_node": "emit"}

def emit_mep_signoff_record(state: dict) -> dict:
    s = state.get("mep_state", {}).copy()
    s["phase"] = MepPhase.COMPLETE
    s["completionPct"] = 100
    return {
        "mep_state": s,
        "mepSignoffRecord": {"projectId": s.get("projectId"), "status": "verified"},
        "next_node": "end"
    }

def halt_on_test_failure(state: dict) -> dict:
    s = state.get("mep_state", {}).copy()
    s["phase"] = MepPhase.TEST_FAIL
    return {"mep_state": s, "next_node": "end"}

# --- Node Functions ---
def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    projectId = state.get("projectId", "unknown")
    init_state = MepState(
        phase=MepPhase.INIT,
        projectId=projectId,
        completionPct=0,
    )
    return {"mep_state": init_state.__dict__, "next_node": "ductwork"}

def _route_ductwork(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_ductwork_routed(state)

def _route_conduit(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_conduit_routed(state)

def _route_piping(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_piping_routed(state)

def _pressure_test(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_pressure_test(state)

def _witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_witness_attestation(state)

def _emit_record(state: dict[str, Any]) -> dict[str, Any]:
    return emit_mep_signoff_record(state)

def _halt(state: dict[str, Any]) -> dict[str, Any]:
    return halt_on_test_failure(state)

# --- Graph Builder ---
_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("ductwork", _route_ductwork)
_g.add_node("conduit", _route_conduit)
_g.add_node("piping", _route_piping)
_g.add_node("test", _pressure_test)
_g.add_node("witness", _witness_attestation)
_g.add_node("emit", _emit_record)
_g.add_node("halt", _halt)

_g.add_edge(START, "init")
_g.add_edge("init", "ductwork")
_g.add_edge("ductwork", "conduit")
_g.add_edge("conduit", "piping")
_g.add_edge("piping", "test")

def route_test(state: dict[str, Any]) -> str:
    return state.get("next_node", "witness")

_g.add_conditional_edges("test", route_test, {"witness": "witness", "halt": "halt"})

_g.add_edge("witness", "emit")
_g.add_edge("emit", END)
_g.add_edge("halt", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
