"""PaintFinishingCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.

Build:
    bash /Users/junkawasaki/github/etzhayyim-root/40-engine/kotoba/scripts/build-pywasm.sh agent.py agent.wasm
"""

from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocks for state_machine ---
class PaintPhase(Enum):
    INIT = "INIT"
    PRETREATMENT_DONE = "PRETREATMENT_DONE"
    KTL_PRIMER_APPLIED = "KTL_PRIMER_APPLIED"
    BASE_COAT_APPLIED = "BASE_COAT_APPLIED"
    CLEAR_COAT_APPLIED = "CLEAR_COAT_APPLIED"
    CURED = "CURED"
    ATTESTATION_EMITTED = "ATTESTATION_EMITTED"

def transition_to_pretreatment_done(s):
    ps = s.get("paint_state", {}).copy()
    ps.update({"phase": PaintPhase.PRETREATMENT_DONE.value, "completionPct": 15})
    return {"paint_state": ps}

def transition_to_ktl_primer_applied(s):
    ps = s.get("paint_state", {}).copy()
    ps.update({"phase": PaintPhase.KTL_PRIMER_APPLIED.value, "completionPct": 30})
    return {"paint_state": ps}

def transition_to_base_coat_applied(s):
    ps = s.get("paint_state", {}).copy()
    ps.update({"phase": PaintPhase.BASE_COAT_APPLIED.value, "completionPct": 50})
    return {"paint_state": ps}

def transition_to_clear_coat_applied(s):
    ps = s.get("paint_state", {}).copy()
    ps.update({"phase": PaintPhase.CLEAR_COAT_APPLIED.value, "completionPct": 70})
    return {"paint_state": ps}

def transition_to_cured(s):
    ps = s.get("paint_state", {}).copy()
    ps.update({"phase": PaintPhase.CURED.value, "completionPct": 90})
    return {"paint_state": ps}

def transition_to_attestation_emitted(s):
    ps = s.get("paint_state", {}).copy()
    ps.update({"phase": PaintPhase.ATTESTATION_EMITTED.value, "completionPct": 100})
    return {
        "paint_state": ps,
        "attestation_record": {
            "chassisId": ps.get("chassisId"),
            "status": "certified"
        }
    }

# --- Node functions ---
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {"paint_state": {
        "phase": PaintPhase.INIT.value,
        "chassisId": state.get("chassisId", "SARUTAHIKO-CHASSIS-0001"),
        "completionPct": 0,
    }}

def _pretreat(s): return transition_to_pretreatment_done(s)
def _ktl(s): return transition_to_ktl_primer_applied(s)
def _base(s): return transition_to_base_coat_applied(s)
def _clear(s): return transition_to_clear_coat_applied(s)
def _cure(s): return transition_to_cured(s)
def _attestation(s): return transition_to_attestation_emitted(s)

# --- Graph construction ---
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("pretreat", _pretreat)
_g.add_node("ktl", _ktl)
_g.add_node("base", _base)
_g.add_node("clear", _clear)
_g.add_node("cure", _cure)
_g.add_node("attestation", _attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "pretreat")
_g.add_edge("pretreat", "ktl")
_g.add_edge("ktl", "base")
_g.add_edge("base", "clear")
_g.add_edge("clear", "cure")
_g.add_edge("cure", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
