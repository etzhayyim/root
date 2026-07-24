"""ElvBodyShredCell — hodoki R0 Pregel cell (L4) compiled to WASM.

Port of `orgs/etzhayyim/com-etzhayyim-hodoki/cells/elv-body-shred/cell.py`
onto the WASM-native `kotoba_langgraph` API so it compiles to a kotoba-node component.

Build:
    ../../scripts/build-pywasm.sh agent.py -o agent.wasm
"""

from __future__ import annotations
from typing import Any, TypedDict
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401


# Inlined BodyShredPhase enum
class BodyShredPhase:
    INIT = "init"
    HULK_LOADED = "hulk_loaded"
    SHREDDED = "shredded"
    SORTED = "sorted"
    KANAYAMA_HANDOFF = "kanayama_handoff"
    SILICON_HANDOFF = "silicon_handoff"
    ATTESTATION_EMITTED = "attestation_emitted"


class ElvBodyShredStateDict(TypedDict, total=False):
    vehicleId: str
    body_shred_state: dict[str, Any]
    next_node: str
    kanayama_record: dict[str, Any]
    silicon_record: dict[str, Any]
    attestation_record: dict[str, Any]


def _initialize_state(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    return {
        "body_shred_state": {
            "phase": BodyShredPhase.INIT,
            "vehicleId": state.get("vehicleId", "HODOKI-VEHICLE-0001"),
            "completionPct": 0,
        },
        "next_node": "load",
    }


def _load(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    """Transition to hulk_loaded."""
    return {
        "body_shred_state": {
            **state.get("body_shred_state", {}),
            "phase": BodyShredPhase.HULK_LOADED,
            "completionPct": 15,
            "hulk_chassis": {
                "vehicleId": state.get("body_shred_state", {}).get("vehicleId", "HODOKI-VEHICLE-0001"),
                "mass_kg": 1200,
                "material_composition": {"steel": 0.65, "aluminum": 0.2, "other": 0.15},
            },
        },
        "next_node": "shred",
    }


def _shred(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    """Transition to shredded."""
    return {
        "body_shred_state": {
            **state.get("body_shred_state", {}),
            "phase": BodyShredPhase.SHREDDED,
            "completionPct": 40,
            "shred_fragments": {
                "fragment_count": 847,
                "avg_size_mm": 25.4,
                "fragmentation_timestamp": "2026-05-31T00:00:00Z",
            },
        },
        "next_node": "sort",
    }


def _sort(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    """Transition to sorted."""
    return {
        "body_shred_state": {
            **state.get("body_shred_state", {}),
            "phase": BodyShredPhase.SORTED,
            "completionPct": 60,
            "sorted_materials": {
                "steel_kg": 780,
                "aluminum_kg": 240,
                "other_kg": 180,
                "sort_timestamp": "2026-05-31T00:01:00Z",
            },
        },
        "next_node": "kanayama",
    }


def _kanayama(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    """Transition to kanayama handoff."""
    sorted_materials = state.get("body_shred_state", {}).get("sorted_materials", {})
    return {
        "body_shred_state": {
            **state.get("body_shred_state", {}),
            "phase": BodyShredPhase.KANAYAMA_HANDOFF,
            "completionPct": 75,
        },
        "kanayama_record": {
            "actor": "kanayama",
            "material_batch_id": f"hodoki-{state.get('body_shred_state', {}).get('vehicleId', 'UNKNOWN')}-2026-05-31",
            "steel_kg": sorted_materials.get("steel_kg", 0),
            "aluminum_kg": sorted_materials.get("aluminum_kg", 0),
            "handoff_timestamp": "2026-05-31T00:02:00Z",
        },
        "next_node": "silicon",
    }


def _silicon(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    """Transition to silicon handoff."""
    sorted_materials = state.get("body_shred_state", {}).get("sorted_materials", {})
    return {
        "body_shred_state": {
            **state.get("body_shred_state", {}),
            "phase": BodyShredPhase.SILICON_HANDOFF,
            "completionPct": 85,
        },
        "silicon_record": {
            "actor": "silicon",
            "material_batch_id": f"hodoki-{state.get('body_shred_state', {}).get('vehicleId', 'UNKNOWN')}-2026-05-31",
            "other_materials_kg": sorted_materials.get("other_kg", 0),
            "handoff_timestamp": "2026-05-31T00:03:00Z",
        },
        "next_node": "attestation",
    }


def _attestation(state: ElvBodyShredStateDict) -> ElvBodyShredStateDict:
    """Transition to attestation emitted."""
    return {
        "body_shred_state": {
            **state.get("body_shred_state", {}),
            "phase": BodyShredPhase.ATTESTATION_EMITTED,
            "completionPct": 100,
        },
        "attestation_record": {
            "vehicleId": state.get("body_shred_state", {}).get("vehicleId", "UNKNOWN"),
            "kanayama_handoff": state.get("kanayama_record", {}),
            "silicon_handoff": state.get("silicon_record", {}),
            "attestation_timestamp": "2026-05-31T00:04:00Z",
            "status": "complete",
        },
        "next_node": "end",
    }


_g = StateGraph(ElvBodyShredStateDict)
_g.add_node("init", _initialize_state)
_g.add_node("load", _load)
_g.add_node("shred", _shred)
_g.add_node("sort", _sort)
_g.add_node("kanayama", _kanayama)
_g.add_node("silicon", _silicon)
_g.add_node("attestation", _attestation)

_g.add_edge(START, "init")
_g.add_edge("init", "load")
_g.add_edge("load", "shred")
_g.add_edge("shred", "sort")
_g.add_edge("sort", "kanayama")
_g.add_edge("kanayama", "silicon")
_g.add_edge("silicon", "attestation")
_g.add_edge("attestation", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())


class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
