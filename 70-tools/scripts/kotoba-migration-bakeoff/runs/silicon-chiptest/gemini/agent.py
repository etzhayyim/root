"""Chip testing cell - ADR-2605242500.

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

# --- Mocked state_machine.py constants and transitions ---

class ChiptestPhase(Enum):
    INIT = "init"
    CONTACT_PROBE_ENGAGED = "contact_probe_engaged"
    PARAMETRIC_TEST_COMPLETE = "parametric_test_complete"
    FUNCTIONAL_TEST_COMPLETE = "functional_test_complete"
    CHIP_GRADED = "chip_graded"

def transition_to_contact_probe_engaged(state: dict[str, Any]) -> dict[str, Any]:
    inner = state.get("chiptest_state", {}).copy()
    inner.update({
        "phase": ChiptestPhase.CONTACT_PROBE_ENGAGED.value,
        "completionPct": 20,
        "probe_status": "engaged"
    })
    return {"chiptest_state": inner}

def transition_to_parametric_test_complete(state: dict[str, Any]) -> dict[str, Any]:
    inner = state.get("chiptest_state", {}).copy()
    inner.update({
        "phase": ChiptestPhase.PARAMETRIC_TEST_COMPLETE.value,
        "completionPct": 50,
        "parametric_data": {"v_threshold": 0.7, "i_leakage": 1e-9}
    })
    return {"chiptest_state": inner}

def transition_to_functional_test_complete(state: dict[str, Any]) -> dict[str, Any]:
    inner = state.get("chiptest_state", {}).copy()
    inner.update({
        "phase": ChiptestPhase.FUNCTIONAL_TEST_COMPLETE.value,
        "completionPct": 80,
        "functional_pass": True
    })
    return {"chiptest_state": inner}

def transition_to_chip_graded(state: dict[str, Any]) -> dict[str, Any]:
    inner = state.get("chiptest_state", {}).copy()
    inner.update({
        "phase": ChiptestPhase.CHIP_GRADED.value,
        "completionPct": 100,
        "grade": "A1"
    })
    return {"chiptest_state": inner}

# --- Node functions ---

def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "chiptest_state": {
            "phase": ChiptestPhase.INIT.value,
            "dieId": state.get("dieId", "DIE-7NM-2026-0001"),
            "completionPct": 0,
        }
    }

def _engage_probe(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_contact_probe_engaged(state)

def _parametric_test(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_parametric_test_complete(state)

def _functional_test(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_functional_test_complete(state)

def _grade_chip(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_chip_graded(state)

# --- Graph construction ---

_g = StateGraph(dict)

_g.add_node("init", _initialize_state)
_g.add_node("engage_probe", _engage_probe)
_g.add_node("parametric_test", _parametric_test)
_g.add_node("functional_test", _functional_test)
_g.add_node("grade_chip", _grade_chip)

_g.add_edge(START, "init")
_g.add_edge("init", "engage_probe")
_g.add_edge("engage_probe", "parametric_test")
_g.add_edge("parametric_test", "functional_test")
_g.add_edge("functional_test", "grade_chip")
_g.add_edge("grade_chip", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
