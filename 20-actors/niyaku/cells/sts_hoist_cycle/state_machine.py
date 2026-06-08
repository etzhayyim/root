"""sts_hoist_cycle state machine — ADR-2606074000 (L3 ship-to-shore hoist: raise the box clear of the cell guides).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606074015.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StsHoistCyclePhase(Enum):
    INIT = "init"
    HOIST_COMMANDED = "hoist_commanded"
    BOX_LIFTED = "box_lifted"
    CLEAR_OF_GUIDES = "clear_of_guides"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CellState:
    phase: str = StsHoistCyclePhase.INIT.value
    moveId: str = "NIYAKU-MOVE-0001"
    vesselId: str = "MV-DEMO-0001"
    terminalId: str = "JPYOK-T1"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def transition_to_hoist_commanded(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> HOIST_COMMANDED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = StsHoistCyclePhase.HOIST_COMMANDED.value
    cs.completionPct = 25
    return {"cell_state": cs.__dict__, "next_node": "box_lifted"}
def transition_to_box_lifted(state: dict[str, Any]) -> dict[str, Any]:
    """HOIST_COMMANDED -> BOX_LIFTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = StsHoistCyclePhase.BOX_LIFTED.value
    cs.completionPct = 50
    return {"cell_state": cs.__dict__, "next_node": "clear_of_guides"}
def transition_to_clear_of_guides(state: dict[str, Any]) -> dict[str, Any]:
    """BOX_LIFTED -> CLEAR_OF_GUIDES."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = StsHoistCyclePhase.CLEAR_OF_GUIDES.value
    cs.completionPct = 75
    return {"cell_state": cs.__dict__, "next_node": "attestation_emitted"}
def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """CLEAR_OF_GUIDES -> ATTESTATION_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = StsHoistCyclePhase.ATTESTATION_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
