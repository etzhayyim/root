"""yard_transfer state machine — ADR-2606082000 (L5 AGV/straddle transfer quay apron -> yard stack tier).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606082015.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class YardTransferPhase(Enum):
    INIT = "init"
    AGV_DISPATCHED = "agv_dispatched"
    BOX_LANDED = "box_landed"
    STACK_UPDATED = "stack_updated"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CellState:
    phase: str = YardTransferPhase.INIT.value
    moveId: str = "NIYAKU-MOVE-0001"
    vesselId: str = "MV-DEMO-0001"
    terminalId: str = "JPYOK-T1"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def transition_to_agv_dispatched(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> AGV_DISPATCHED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = YardTransferPhase.AGV_DISPATCHED.value
    cs.completionPct = 25
    return {"cell_state": cs.__dict__, "next_node": "box_landed"}
def transition_to_box_landed(state: dict[str, Any]) -> dict[str, Any]:
    """AGV_DISPATCHED -> BOX_LANDED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = YardTransferPhase.BOX_LANDED.value
    cs.completionPct = 50
    return {"cell_state": cs.__dict__, "next_node": "stack_updated"}
def transition_to_stack_updated(state: dict[str, Any]) -> dict[str, Any]:
    """BOX_LANDED -> STACK_UPDATED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = YardTransferPhase.STACK_UPDATED.value
    cs.completionPct = 75
    return {"cell_state": cs.__dict__, "next_node": "attestation_emitted"}
def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """STACK_UPDATED -> ATTESTATION_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = YardTransferPhase.ATTESTATION_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
