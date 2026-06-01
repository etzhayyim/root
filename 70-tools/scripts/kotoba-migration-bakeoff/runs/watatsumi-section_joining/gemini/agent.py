from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mock constants/classes from .state_machine
class SectionJoiningPhase(Enum):
    INIT = "init"
    ALIGNED = "aligned"
    TIG_COMPLETE = "tig_complete"
    RT_PASSED = "rt_passed"
    PWHT_COMPLETE = "pwht_complete"
    ATTESTATION_EMITTED = "attestation_emitted"

def transition_to_sections_aligned(state: dict):
    s = state.get("section_joining_state", {})
    return {"section_joining_state": {**s, "phase": SectionJoiningPhase.ALIGNED.value, "completionPct": 20}}

def transition_to_multipass_tig_complete(state: dict):
    s = state.get("section_joining_state", {})
    return {"section_joining_state": {**s, "phase": SectionJoiningPhase.TIG_COMPLETE.value, "completionPct": 40}}

def transition_to_rt_100pct_passed(state: dict):
    s = state.get("section_joining_state", {})
    return {"section_joining_state": {**s, "phase": SectionJoiningPhase.RT_PASSED.value, "completionPct": 60}}

def transition_to_pwht_complete(state: dict):
    s = state.get("section_joining_state", {})
    return {"section_joining_state": {**s, "phase": SectionJoiningPhase.PWHT_COMPLETE.value, "completionPct": 80}}

def transition_to_attestation_emitted(state: dict):
    s = state.get("section_joining_state", {})
    return {"section_joining_state": {**s, "phase": SectionJoiningPhase.ATTESTATION_EMITTED.value, "completionPct": 100}}

# Node functions
def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "section_joining_state": {
            "phase": SectionJoiningPhase.INIT.value,
            "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
            "completionPct": 0,
        }
    }

def _align(s): return transition_to_sections_aligned(s)
def _tig(s): return transition_to_multipass_tig_complete(s)
def _rt(s): return transition_to_rt_100pct_passed(s)
def _pwht(s): return transition_to_pwht_complete(s)
def _attestation(s): return transition_to_attestation_emitted(s)

# Graph builder
_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("align", _align)
_g.add_node("tig", _tig)
_g.add_node("rt", _rt)
_g.add_node("pwht", _pwht)
_g.add_node("attestation", _attestation)
_g.add_edge(START, "init")
_g.add_edge("init", "align")
_g.add_edge("align", "tig")
_g.add_edge("tig", "rt")
_g.add_edge("rt", "pwht")
_g.add_edge("pwht", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
