"""outfitting state machine — ADR-2606013400 (L5a cargo systems + coatings + accommodation + autonomy sensors).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606013415.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OutfittingPhase(Enum):
    INIT = "init"
    CARGO_SYSTEMS_FITTED = "cargo_systems_fitted"
    COATINGS_APPLIED = "coatings_applied"
    ACCOMMODATION_FITTED = "accommodation_fitted"
    SENSOR_SUITE_INSTALLED = "sensor_suite_installed"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CellState:
    phase: str = OutfittingPhase.INIT.value
    vesselId: str = "NAGI-COASTAL-0001"
    vesselClass: str = "Nagi 凪"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)

def transition_to_cargo_systems_fitted(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> CARGO_SYSTEMS_FITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = OutfittingPhase.CARGO_SYSTEMS_FITTED.value
    cs.completionPct = 20
    return {"cell_state": cs.__dict__, "next_node": "coatings_applied"}
def transition_to_coatings_applied(state: dict[str, Any]) -> dict[str, Any]:
    """CARGO_SYSTEMS_FITTED -> COATINGS_APPLIED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = OutfittingPhase.COATINGS_APPLIED.value
    cs.completionPct = 40
    return {"cell_state": cs.__dict__, "next_node": "accommodation_fitted"}
def transition_to_accommodation_fitted(state: dict[str, Any]) -> dict[str, Any]:
    """COATINGS_APPLIED -> ACCOMMODATION_FITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = OutfittingPhase.ACCOMMODATION_FITTED.value
    cs.completionPct = 60
    return {"cell_state": cs.__dict__, "next_node": "sensor_suite_installed"}
def transition_to_sensor_suite_installed(state: dict[str, Any]) -> dict[str, Any]:
    """ACCOMMODATION_FITTED -> SENSOR_SUITE_INSTALLED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = OutfittingPhase.SENSOR_SUITE_INSTALLED.value
    cs.completionPct = 80
    return {"cell_state": cs.__dict__, "next_node": "attestation_emitted"}
def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """SENSOR_SUITE_INSTALLED -> ATTESTATION_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = OutfittingPhase.ATTESTATION_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
