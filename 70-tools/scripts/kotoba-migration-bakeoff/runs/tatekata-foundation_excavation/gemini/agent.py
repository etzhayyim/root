"""FoundationExcavationCell compiled to WASM.

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

# --- Mocks for state_machine.py ---

class FoundationPhase:
    INIT = "INIT"
    SURVEY = "SURVEY"
    PLANNING = "PLANNING"
    EXECUTION = "EXECUTION"
    WITNESS_WAIT = "WITNESS_WAIT"
    HALT = "HALT"
    COMPLETED = "COMPLETED"

class FoundationState:
    def __init__(self, phase: str, siteId: str, completionPct: int):
        self.phase = phase
        self.siteId = siteId
        self.completionPct = completionPct

def transition_to_survey(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("foundation_state", {})
    fs["phase"] = FoundationPhase.SURVEY
    fs["completionPct"] = 10
    return {"foundation_state": fs, "next_node": "plan"}

def transition_to_planning(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("foundation_state", {})
    fs["phase"] = FoundationPhase.PLANNING
    fs["completionPct"] = 30
    return {"foundation_state": fs, "next_node": "execute"}

def transition_to_execution(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("foundation_state", {})
    fs["phase"] = FoundationPhase.EXECUTION
    fs["completionPct"] = 60
    return {"foundation_state": fs, "next_node": "anomaly_check"}

def check_for_anomalies(state: dict[str, Any]) -> dict[str, Any]:
    # Mock: no anomalies found
    return {"next_node": "witness"}

def wait_for_witness_sigs(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("foundation_state", {})
    fs["phase"] = FoundationPhase.WITNESS_WAIT
    fs["completionPct"] = 90
    return {"foundation_state": fs, "next_node": "emit"}

def emit_progress_record(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("foundation_state", {})
    fs["phase"] = FoundationPhase.COMPLETED
    fs["completionPct"] = 100
    return {"foundation_state": fs, "next_node": "end"}

def halt_on_anomaly(state: dict[str, Any]) -> dict[str, Any]:
    fs = state.get("foundation_state", {})
    fs["phase"] = FoundationPhase.HALT
    return {"foundation_state": fs, "next_node": "end"}

# --- Node Functions ---

def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    """Initialize foundation state from input."""
    siteId = state.get("siteId", "unknown")
    init_state = FoundationState(
        phase=FoundationPhase.INIT,
        siteId=siteId,
        completionPct=0,
    )
    return {"foundation_state": init_state.__dict__, "next_node": "survey"}

def _survey_utilities(state: dict[str, Any]) -> dict[str, Any]:
    """SURVEY → PLANNING: Check existing utilities (power, water, gas)."""
    return state

def _giemon_excavation_plan(state: dict[str, Any]) -> dict[str, Any]:
    """SURVEY → PLANNING: Giemon trajectory synthesis (deterministic, replayable)."""
    return transition_to_planning(state)

def _giemon_execution(state: dict[str, Any]) -> dict[str, Any]:
    """PLANNING → EXECUTION: Giemon active excavation (mock 5 passes)."""
    return transition_to_execution(state)

def _anomaly_detection(state: dict[str, Any]) -> dict[str, Any]:
    """EXECUTION → WITNESS_WAIT or ANOMALY_HALT: Scan sensor data."""
    return check_for_anomalies(state)

def _witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    """WITNESS_WAIT (fixed-point): Collect ≥2 robot Ed25519 signatures."""
    return wait_for_witness_sigs(state)

def _emit_record(state: dict[str, Any]) -> dict[str, Any]:
    """PROGRESS_RECORD: Emit constructionProgressRecord to MST."""
    return emit_progress_record(state)

def _halt(state: dict[str, Any]) -> dict[str, Any]:
    """ANOMALY_HALT: Halt execution, emit alert."""
    return halt_on_anomaly(state)

# --- Graph Construction ---

_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("survey", _survey_utilities)
_g.add_node("plan", _giemon_excavation_plan)
_g.add_node("execute", _giemon_execution)
_g.add_node("anomaly_check", _anomaly_detection)
_g.add_node("witness", _witness_attestation)
_g.add_node("emit", _emit_record)
_g.add_node("halt", _halt)

_g.add_edge(START, "init")
_g.add_edge("init", "survey")
_g.add_edge("survey", "plan")
_g.add_edge("plan", "execute")
_g.add_edge("execute", "anomaly_check")

def route_anomaly(state: dict[str, Any]) -> str:
    return state.get("next_node", "witness")

_g.add_conditional_edges("anomaly_check", route_anomaly, {"witness": "witness", "halt": "halt"})

_g.add_edge("witness", "emit")
_g.add_edge("emit", END)
_g.add_edge("halt", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
