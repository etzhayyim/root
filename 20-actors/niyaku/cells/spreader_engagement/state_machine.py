"""spreader_engagement state machine — ADR-2606074000 (L2 align + engage the twistlock spreader on the target container).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606074015.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SpreaderEngagementPhase(Enum):
    INIT = "init"
    SPREADER_ALIGNED = "spreader_aligned"
    TWISTLOCKS_ENGAGED = "twistlocks_engaged"
    LOAD_VERIFIED = "load_verified"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CellState:
    phase: str = SpreaderEngagementPhase.INIT.value
    moveId: str = "NIYAKU-MOVE-0001"
    vesselId: str = "MV-DEMO-0001"
    terminalId: str = "JPYOK-T1"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def transition_to_spreader_aligned(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> SPREADER_ALIGNED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = SpreaderEngagementPhase.SPREADER_ALIGNED.value
    cs.completionPct = 25
    return {"cell_state": cs.__dict__, "next_node": "twistlocks_engaged"}
def transition_to_twistlocks_engaged(state: dict[str, Any]) -> dict[str, Any]:
    """SPREADER_ALIGNED -> TWISTLOCKS_ENGAGED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = SpreaderEngagementPhase.TWISTLOCKS_ENGAGED.value
    cs.completionPct = 50
    return {"cell_state": cs.__dict__, "next_node": "load_verified"}
def transition_to_load_verified(state: dict[str, Any]) -> dict[str, Any]:
    """TWISTLOCKS_ENGAGED -> LOAD_VERIFIED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = SpreaderEngagementPhase.LOAD_VERIFIED.value
    cs.completionPct = 75
    return {"cell_state": cs.__dict__, "next_node": "attestation_emitted"}
def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """LOAD_VERIFIED -> ATTESTATION_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = SpreaderEngagementPhase.ATTESTATION_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
