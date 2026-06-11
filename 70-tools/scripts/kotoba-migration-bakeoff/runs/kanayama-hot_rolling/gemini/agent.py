"""agent.py — HotRollingCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.

Build:
    bash /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/scripts/build-pywasm.sh agent.py agent.wasm
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocked state_machine.py logic ---

class HotRollingPhase(Enum):
    INIT = "init"
    SLAB_REHEATED = "slab_reheated"
    ROUGH_ROLL_COMPLETE = "rough_roll_complete"
    FINISH_ROLL_COMPLETE = "finish_roll_complete"
    COILED = "coiled"
    RECORD_EMITTED = "record_emitted"

@dataclass
class HotRollingState:
    phase: HotRollingPhase
    lotId: str
    completionPct: int
    reheatTempC: int | None = None
    passes: list[dict[str, Any]] | None = None
    finalGaugeMm: float | None = None
    hotBandCoilId: str | None = None
    hotBandMassKg: float | None = None

def transition_to_slab_reheated(state: dict[str, Any]) -> dict[str, Any]:
    s = HotRollingState(**state.get("hot_rolling_state", {}))
    s.reheatTempC = 510
    s.phase = HotRollingPhase.SLAB_REHEATED
    s.completionPct = 15
    # Preserve original logic: state machine returns next_node hint
    return {"hot_rolling_state": s.__dict__, "next_node": "rough"}

def transition_to_rough_roll_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = HotRollingState(**state.get("hot_rolling_state", {}))
    s.passes = [
        {"pass": 1, "in_mm": 600, "out_mm": 400, "tempC": 510},
        {"pass": 2, "in_mm": 400, "out_mm": 250, "tempC": 495},
        {"pass": 3, "in_mm": 250, "out_mm": 120, "tempC": 480},
        {"pass": 4, "in_mm": 120, "out_mm": 60, "tempC": 470},
    ]
    s.phase = HotRollingPhase.ROUGH_ROLL_COMPLETE
    s.completionPct = 50
    return {"hot_rolling_state": s.__dict__, "next_node": "finish"}

def transition_to_finish_roll_complete(state: dict[str, Any]) -> dict[str, Any]:
    s = HotRollingState(**state.get("hot_rolling_state", {}))
    extra = [
        {"pass": 5, "in_mm": 60, "out_mm": 25, "tempC": 460},
        {"pass": 6, "in_mm": 25, "out_mm": 10, "tempC": 440},
        {"pass": 7, "in_mm": 10, "out_mm": 5, "tempC": 410},
        {"pass": 8, "in_mm": 5, "out_mm": 3, "tempC": 380},
    ]
    s.passes = (s.passes or []) + extra
    s.finalGaugeMm = 3.0
    s.phase = HotRollingPhase.FINISH_ROLL_COMPLETE
    s.completionPct = 75
    return {"hot_rolling_state": s.__dict__, "next_node": "coil"}

def transition_to_coiled(state: dict[str, Any]) -> dict[str, Any]:
    s = HotRollingState(**state.get("hot_rolling_state", {}))
    s.hotBandCoilId = "KANAYAMA-HBC-2026-05-26-0001"
    s.hotBandMassKg = 12700.0
    s.phase = HotRollingPhase.COILED
    s.completionPct = 90
    return {"hot_rolling_state": s.__dict__, "next_node": "record"}

def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = HotRollingState(**state.get("hot_rolling_state", {}))
    s.phase = HotRollingPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.kanayama.rollingAttestation",
        "lotId": s.lotId,
        "reheatTempC": s.reheatTempC,
        "passes": s.passes,
        "finalGaugeMm": s.finalGaugeMm,
        "hotBandCoilId": s.hotBandCoilId,
        "hotBandMassKg": s.hotBandMassKg,
        "rollingStage": "hot",
        "recordedAt": "2026-05-26T14:30:00Z",
    }
    return {"hot_rolling_state": s.__dict__, "rolling_attestation": record, "next_node": "end"}

# --- Graph Nodes ---

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"hot_rolling_state": {
        "phase": HotRollingPhase.INIT.value,
        "lotId": state.get("lotId", "KANAYAMA-UBC-LOT-0001"),
        "completionPct": 0,
    }}

def _reheat(s): return transition_to_slab_reheated(s)
def _rough(s): return transition_to_rough_roll_complete(s)
def _finish(s): return transition_to_finish_roll_complete(s)
def _coil(s): return transition_to_coiled(s)
def _record(s): return transition_to_record_emitted(s)

# --- Graph Construction ---

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("reheat", _reheat)
_g.add_node("rough", _rough)
_g.add_node("finish", _finish)
_g.add_node("coil", _coil)
_g.add_node("record", _record)

_g.add_edge(START, "init")
_g.add_edge("init", "reheat")
_g.add_edge("reheat", "rough")
_g.add_edge("rough", "finish")
_g.add_edge("finish", "coil")
_g.add_edge("coil", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
