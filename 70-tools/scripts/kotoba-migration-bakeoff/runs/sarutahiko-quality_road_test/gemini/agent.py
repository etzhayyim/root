"""QualityRoadTestCell — QualityRoadTestCell compiled to WASM.

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
class RoadTestPhase:
    INIT = "INIT"
    DYNO_COMPLETE = "DYNO_COMPLETE"
    G12_KPI_VERIFIED = "G12_KPI_VERIFIED"
    PUBLIC_ROAD_COMPLETE = "PUBLIC_ROAD_COMPLETE"
    NORIMICHI_ATTESTATION = "NORIMICHI_ATTESTATION"
    RECORD_EMITTED = "RECORD_EMITTED"

    def __init__(self, value):
        self.value = value

RoadTestPhase.INIT = RoadTestPhase("INIT")
RoadTestPhase.DYNO_COMPLETE = RoadTestPhase("DYNO_COMPLETE")
RoadTestPhase.G12_KPI_VERIFIED = RoadTestPhase("G12_KPI_VERIFIED")
RoadTestPhase.PUBLIC_ROAD_COMPLETE = RoadTestPhase("PUBLIC_ROAD_COMPLETE")
RoadTestPhase.NORIMICHI_ATTESTATION = RoadTestPhase("NORIMICHI_ATTESTATION")
RoadTestPhase.RECORD_EMITTED = RoadTestPhase("RECORD_EMITTED")

def transition_to_dyno_run_complete(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("road_test_state", {}).copy()
    rs.update({"phase": RoadTestPhase.DYNO_COMPLETE.value, "completionPct": 20})
    return {"road_test_state": rs}

def transition_to_g12_kpi_verified(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("road_test_state", {}).copy()
    rs.update({"phase": RoadTestPhase.G12_KPI_VERIFIED.value, "completionPct": 40, "g12_kpi": "verified"})
    return {"road_test_state": rs}

def transition_to_public_road_test_complete(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("road_test_state", {}).copy()
    rs.update({"phase": RoadTestPhase.PUBLIC_ROAD_COMPLETE.value, "completionPct": 70})
    return {"road_test_state": rs}

def transition_to_norimichi_attestation(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("road_test_state", {}).copy()
    rs.update({"phase": RoadTestPhase.NORIMICHI_ATTESTATION.value, "completionPct": 90, "attestation": "norimichi_signed"})
    return {"road_test_state": rs}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    rs = state.get("road_test_state", {}).copy()
    rs.update({"phase": RoadTestPhase.RECORD_EMITTED.value, "completionPct": 100})
    return {"road_test_state": rs, "final_record": {"chassisId": rs.get("chassisId"), "status": "certified"}}

# --- Node Functions ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"road_test_state": {
        "phase": RoadTestPhase.INIT.value,
        "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
        "completionPct": 0,
    }}

def _dyno(s): return transition_to_dyno_run_complete(s)
def _g12(s): return transition_to_g12_kpi_verified(s)
def _road(s): return transition_to_public_road_test_complete(s)
def _norimichi(s): return transition_to_norimichi_attestation(s)
def _record(s): return transition_to_record_emitted(s)

# --- Graph Builder ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("dyno", _dyno)
_g.add_node("g12", _g12)
_g.add_node("road", _road)
_g.add_node("norimichi", _norimichi)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "dyno")
_g.add_edge("dyno", "g12")
_g.add_edge("g12", "road")
_g.add_edge("road", "norimichi")
_g.add_edge("norimichi", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
