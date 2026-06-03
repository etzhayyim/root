"""ClassCertificationBinderCell compiled to WASM.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# Mocking state_machine imports
class CertificationPhase(Enum):
    INIT = "init"
    RECORDS_COLLECTED = "records_collected"
    SURVEYOR_REVIEW = "surveyor_review"
    KOTOBA_DATOMIC_ANCHORED = "kotoba-datomic_anchored"
    RECORD_EMITTED = "record_emitted"

def _init(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "certification_state": {
            "phase": CertificationPhase.INIT.value,
            "craftId": state.get("craftId", "WATATSUMI-RESEARCH-0001"),
            "completionPct": 0,
        }
    }

def _collect(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("certification_state", {})
    return {
        "certification_state": {
            **cs,
            "phase": CertificationPhase.RECORDS_COLLECTED.value,
            "completionPct": 25,
        }
    }

def _surveyor(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("certification_state", {})
    return {
        "certification_state": {
            **cs,
            "phase": CertificationPhase.SURVEYOR_REVIEW.value,
            "completionPct": 50,
        }
    }

def _anchor(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("certification_state", {})
    mock_anchor = {
        "anchor_id": f"yata:anchor:watatsumi:{cs.get('craftId', '0001')}:mock",
        "timestamp": "2026-05-31T00:00:00Z",
    }
    return {
        "certification_state": {
            **cs,
            "phase": CertificationPhase.KOTOBA_DATOMIC_ANCHORED.value,
            "anchor": mock_anchor,
            "completionPct": 75,
        }
    }

def _record(state: dict[str, Any]) -> dict[str, Any]:
    cs = state.get("certification_state", {})
    record = {
        "craftId": cs.get("craftId"),
        "status": "Certified",
        "anchor": cs.get("anchor", {}),
    }
    return {
        "certification_state": {
            **cs,
            "phase": CertificationPhase.RECORD_EMITTED.value,
            "completionPct": 100,
        },
        "class_certification_record": record
    }

_g = StateGraph(dict)
_g.add_node("init", _init)
_g.add_node("collect", _collect)
_g.add_node("surveyor", _surveyor)
_g.add_node("anchor", _anchor)
_g.add_node("record", _record)
_g.add_edge(START, "init")
_g.add_edge("init", "collect")
_g.add_edge("collect", "surveyor")
_g.add_edge("surveyor", "anchor")
_g.add_edge("anchor", "record")
_g.add_edge("record", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
