"""stowage_planning state machine — ADR-2606082000 (L1 compute bay/row/tier stow plan (weight/rotation/reefer/hazmat) + work sequence).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606082015.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StowagePlanningPhase(Enum):
    INIT = "init"
    PLAN_COMPUTED = "plan_computed"
    SEQUENCE_ORDERED = "sequence_ordered"
    NO_REHANDLE_VERIFIED = "no_rehandle_verified"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CellState:
    phase: str = StowagePlanningPhase.INIT.value
    moveId: str = "NIYAKU-MOVE-0001"
    vesselId: str = "MV-DEMO-0001"
    terminalId: str = "JPYOK-T1"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def transition_to_plan_computed(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> PLAN_COMPUTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = StowagePlanningPhase.PLAN_COMPUTED.value
    cs.completionPct = 25
    return {"cell_state": cs.__dict__, "next_node": "sequence_ordered"}
def transition_to_sequence_ordered(state: dict[str, Any]) -> dict[str, Any]:
    """PLAN_COMPUTED -> SEQUENCE_ORDERED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = StowagePlanningPhase.SEQUENCE_ORDERED.value
    cs.completionPct = 50
    return {"cell_state": cs.__dict__, "next_node": "no_rehandle_verified"}
def transition_to_no_rehandle_verified(state: dict[str, Any]) -> dict[str, Any]:
    """SEQUENCE_ORDERED -> NO_REHANDLE_VERIFIED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = StowagePlanningPhase.NO_REHANDLE_VERIFIED.value
    cs.completionPct = 75
    return {"cell_state": cs.__dict__, "next_node": "attestation_emitted"}
def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """NO_REHANDLE_VERIFIED -> ATTESTATION_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = StowagePlanningPhase.ATTESTATION_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
