"""Wafer processing agent - Kotoba WASM port.

Port of `original_cell.py` onto the WASM-native `kotoba_langgraph` API.
"""

from __future__ import annotations
from typing import Any
from enum import Enum
import wit_world

from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke
import kotoba_langgraph._cbor  # noqa: F401
import kotoba_langgraph._entry  # noqa: F401

# --- Mocked state_machine.py constants and helpers ---

class WaferPhase(Enum):
    INIT = "init"
    DEPOSITION_COMPLETE = "deposition_complete"
    ETCHING_COMPLETE = "etching_complete"
    IMPLANTATION_COMPLETE = "implantation_complete"
    CMP_COMPLETE = "cmp_complete"
    WAFER_VERIFIED = "wafer_verified"

class WaferState:
    def __init__(self, **kwargs):
        self.phase = kwargs.get("phase")
        self.lotId = kwargs.get("lotId")
        self.completionPct = kwargs.get("completionPct", 0)
        self.depositionData = kwargs.get("depositionData")
        self.etchingData = kwargs.get("etchingData")
        self.implantData = kwargs.get("implantData")
        self.cmpData = kwargs.get("cmpData")
        self.metrologyScan = kwargs.get("metrologyScan")
        self.anomalyFlags = kwargs.get("anomalyFlags")
        self.robotSignatures = kwargs.get("robotSignatures")

def transition_to_deposition_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = WaferState(**state.get("wafer_state", {}))
    mock_deposition = {
        "material": "SiO2",
        "thickness_nm": 180,
        "deposition_method": "PECVD",
        "growth_rate_nm_min": 3.2,
        "uniformity_pct": 97.8,
        "refractive_index": 1.46,
    }
    ws.phase = WaferPhase.DEPOSITION_COMPLETE
    ws.depositionData = mock_deposition
    ws.completionPct = 20
    return {"wafer_state": ws.__dict__, "next_node": "etch"}

def transition_to_etching_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = WaferState(**state.get("wafer_state", {}))
    mock_etching = {
        "etch_process": "plasma_dry_etch",
        "etchant_gas": "C4F6_O2_Ar",
        "etch_depth_nm": 175,
        "selectivity_ratio": 8.2,
        "line_edge_roughness_nm": 2.1,
        "etch_uniformity_pct": 96.5,
        "undercut_nm": 0.5,
    }
    ws.phase = WaferPhase.ETCHING_COMPLETE
    ws.etchingData = mock_etching
    ws.completionPct = 40
    return {"wafer_state": ws.__dict__, "next_node": "implant"}

def transition_to_implantation_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = WaferState(**state.get("wafer_state", {}))
    mock_implant = {
        "dopant_species": "B+",
        "implant_energy_kev": 20,
        "implant_dose_cm2": 1e13,
        "junction_depth_nm": 85,
        "sheet_resistance_ohm_sq": 450,
        "doping_uniformity_pct": 98.1,
    }
    ws.phase = WaferPhase.IMPLANTATION_COMPLETE
    ws.implantData = mock_implant
    ws.completionPct = 60
    return {"wafer_state": ws.__dict__, "next_node": "cmp"}

def transition_to_cmp_complete(state: dict[str, Any]) -> dict[str, Any]:
    ws = WaferState(**state.get("wafer_state", {}))
    mock_cmp = {
        "cmp_process": "chemical_mechanical_polish",
        "polish_pad": "IC1000_mm",
        "slurry_type": "colloidal_silica",
        "removal_rate_nm_min": 45,
        "within_wafer_uniformity_pct": 98.3,
        "polish_time_minutes": 3.8,
        "residual_thickness_nm": 5,
    }
    ws.phase = WaferPhase.CMP_COMPLETE
    ws.cmpData = mock_cmp
    ws.completionPct = 80
    return {"wafer_state": ws.__dict__, "next_node": "verify_wafer"}

def transition_to_wafer_verified(state: dict[str, Any]) -> dict[str, Any]:
    ws = WaferState(**state.get("wafer_state", {}))
    mock_metrology = {
        "thickness_nm": 5.2,
        "thickness_uniformity_pct": 98.5,
        "defect_count": 0,
        "defect_density_per_cm2": 0,
        "layer_stackup_correct": True,
        "wafer_release_approved": True,
    }
    mock_sigs = [
        {
            "robotDid": "did:web:etzhayyim.com:mimi-unit-2",
            "role": "wafer_metrology",
            "timestamp": "2026-05-26T15:45:30Z",
            "signature": "xX1yY2zZ3aA4bB5c...",
        },
        {
            "robotDid": "did:web:etzhayyim.com:otete-unit-3",
            "role": "process_handler",
            "timestamp": "2026-05-26T15:45:35Z",
            "signature": "dD6eE7fF8gG9hH0i...",
        },
    ]
    ws.phase = WaferPhase.WAFER_VERIFIED
    ws.metrologyScan = mock_metrology
    ws.robotSignatures = mock_sigs
    ws.completionPct = 100
    return {
        "wafer_state": ws.__dict__,
        "wafer_processing_record": {
            "lotId": ws.lotId,
            "deposition": ws.depositionData,
            "etching": ws.etchingData,
            "implantation": ws.implantData,
            "cmp": ws.cmpData,
            "metrology": ws.metrologyScan,
            "attestingRobots": mock_sigs,
        },
        "next_node": "end",
    }

# --- Node functions ---

def _initialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "wafer_state": {
            "phase": WaferPhase.INIT.value,
            "lotId": state.get("lotId", "LOT-7NM-2026-0001"),
            "completionPct": 0,
        }
    }

def _deposition(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_deposition_complete(state)

def _etch(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_etching_complete(state)

def _implant(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_implantation_complete(state)

def _cmp(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_cmp_complete(state)

def _verify_wafer(state: dict[str, Any]) -> dict[str, Any]:
    return transition_to_wafer_verified(state)

# --- Graph construction ---

_g = StateGraph(dict)
_g.add_node("init", _initialize_state)
_g.add_node("deposition", _deposition)
_g.add_node("etch", _etch)
_g.add_node("implant", _implant)
_g.add_node("cmp", _cmp)
_g.add_node("verify_wafer", _verify_wafer)

_g.add_edge(START, "init")
_g.add_edge("init", "deposition")
_g.add_edge("deposition", "etch")
_g.add_edge("etch", "implant")
_g.add_edge("implant", "cmp")
_g.add_edge("cmp", "verify_wafer")
_g.add_edge("verify_wafer", END)

compiled = _g.compile(checkpointer=KotobaCheckpointer())

class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
