"""StructuralAssemblyCell compiled to WASM.

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

# Mocking relative imports and types
class StructuralPhase:
    INIT = "INIT"
    BIM_LOADED = "BIM_LOADED"
    FOUNDATION_VALIDATED = "FOUNDATION_VALIDATED"
    ROBOT_COORDINATED = "ROBOT_COORDINATED"
    EXECUTION = "EXECUTION"
    METROLOGY_CHECK = "METROLOGY_CHECK"
    WITNESS_WAIT = "WITNESS_WAIT"
    COMPLETE = "COMPLETE"
    ANOMALY_HALT = "ANOMALY_HALT"

class StructuralState:
    def __init__(self, phase: str, projectId: str, completionPct: int):
        self.phase = phase
        self.projectId = projectId
        self.completionPct = completionPct

def transition_to_bim_loaded(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("structural_state", {})
    return {"structural_state": {**s, "phase": StructuralPhase.BIM_LOADED, "completionPct": 10}, "next_node": "validate"}

def transition_to_foundation_validated(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("structural_state", {})
    return {"structural_state": {**s, "phase": StructuralPhase.FOUNDATION_VALIDATED, "completionPct": 20}, "next_node": "coordinate"}

def transition_to_robot_coordinated(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("structural_state", {})
    return {"structural_state": {**s, "phase": StructuralPhase.ROBOT_COORDINATED, "completionPct": 30}, "next_node": "execute"}

def transition_to_execution(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("structural_state", {})
    return {"structural_state": {**s, "phase": StructuralPhase.EXECUTION, "completionPct": 70}, "next_node": "metrology"}

def transition_to_metrology_check(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("structural_state", {})
    # Mocking metrology check logic: always pass to witness for now
    return {"structural_state": {**s, "phase": StructuralPhase.METROLOGY_CHECK, "completionPct": 85}, "next_node": "witness"}

def transition_to_witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("structural_state", {})
    mock_sigs = [{"robot": "Giemon", "sig": "sig1"}, {"robot": "Otete", "sig": "sig2"}]
    return {"structural_state": {**s, "phase": StructuralPhase.WITNESS_WAIT, "signatures": mock_sigs, "completionPct": 95}, "next_node": "emit"}

def emit_structural_auth_record(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("structural_state", {})
    record = {"projectId": s.get("projectId"), "status": "authorized", "signatures": s.get("signatures")}
    return {"structural_state": {**s, "phase": StructuralPhase.COMPLETE, "completionPct": 100}, "structuralAuthRecord": record, "next_node": "end"}

def halt_on_metrology_anomaly(state: dict[str, Any]) -> dict[str, Any]:
    s = state.get("structural_state", {})
    return {"structural_state": {**s, "phase": StructuralPhase.ANOMALY_HALT}, "next_node": "end"}

# Node functions
def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    projectId = state.get("projectId", "unknown")
    init_state = StructuralState(
        phase=StructuralPhase.INIT,
        projectId=projectId,
        completionPct=0,
    )
    return {"structural_state": init_state.__dict__, "next_node": "load_bim"}

def _load_bim_model(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_bim_loaded(state)

def _validate_foundations(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_foundation_validated(state)

def _coordinate_robots(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_robot_coordinated(state)

def _execute_assembly(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_execution(state)

def _metrology_check(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_metrology_check(state)

def _witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_witness_attestation(state)

def _emit_record(state: dict[str, Any]) -> dict[str, Any]:
    return emit_structural_auth_record(state)

def _halt(state: dict[str, Any]) -> dict[str, Any]:
    return halt_on_metrology_anomaly(state)

def route_metrology(state: dict[str, Any]) -> str:
    return state.get("next_node", "witness")

# Graph construction
_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("load_bim", _load_bim_model)
_g.add_node("validate", _validate_foundations)
_g.add_node("coordinate", _coordinate_robots)
_g.add_node("execute", _execute_assembly)
_g.add_node("metrology", _metrology_check)
_g.add_node("witness", _witness_attestation)
_g.add_node("emit", _emit_record)
_g.add_node("halt", _halt)

_g.add_edge(START, "init")
_g.add_edge("init", "load_bim")
_g.add_edge("load_bim", "validate")
_g.add_edge("validate", "coordinate")
_g.add_edge("coordinate", "execute")
_g.add_edge("execute", "metrology")

_g.add_conditional_edges("metrology", route_metrology, {"witness": "witness", "halt": "halt"})

_g.add_edge("witness", "emit")
_g.add_edge("emit", END)
_g.add_edge("halt", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
