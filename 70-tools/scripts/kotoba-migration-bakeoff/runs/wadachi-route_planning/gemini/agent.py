"""agent — RoutePlanningCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocked state_machine.py components ---
class RoutePlanningPhase(Enum):
    INIT = "init"
    DESTINATION_VALIDATED = "destination_validated"
    OBSTACLES_MAPPED = "obstacles_mapped"
    PATH_COMPUTED = "path_computed"
    TRAJECTORY_PLANNED = "trajectory_planned"
    WITNESS_ATTESTED = "witness_attested"

def transition_to_destination_validated(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("route_state", {})
    return {"route_state": {**rs, "phase": "destination_validated", "completionPct": 20}}

def transition_to_obstacles_mapped(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("route_state", {})
    return {"route_state": {**rs, "phase": "obstacles_mapped", "completionPct": 40}}

def transition_to_path_computed(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("route_state", {})
    return {"route_state": {**rs, "phase": "path_computed", "completionPct": 60}}

def transition_to_trajectory_planned(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("route_state", {})
    return {"route_state": {**rs, "phase": "trajectory_planned", "completionPct": 80}}

def transition_to_witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("route_state", {})
    mock_witness = {"witness_id": "wadachi-witness-01", "signature": "sig-777", "attested_at": "2026-05-31T12:00:00Z"}
    return {"route_state": {**rs, "phase": "witness_attested", "witness": mock_witness, "completionPct": 100}}

# --- Node logic ---
def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_state": {
            "phase": RoutePlanningPhase.INIT.value,
            "missionId": state.get("missionId", "MISSION-2026-0001"),
            "completionPct": 0,
        }
    }

def _validate_destination(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_destination_validated(state)

def _map_obstacles(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_obstacles_mapped(state)

def _compute_path(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_path_computed(state)

def _plan_trajectory(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_trajectory_planned(state)

def _witness_attestation(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_witness_attestation(state)

# --- Graph construction ---
_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("validate_destination", _validate_destination)
_g.add_node("map_obstacles", _map_obstacles)
_g.add_node("compute_path", _compute_path)
_g.add_node("plan_trajectory", _plan_trajectory)
_g.add_node("witness", _witness_attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "validate_destination")
_g.add_edge("validate_destination", "map_obstacles")
_g.add_edge("map_obstacles", "compute_path")
_g.add_edge("compute_path", "plan_trajectory")
_g.add_edge("plan_trajectory", "witness")
_g.add_edge("witness", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
