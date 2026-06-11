"""berth_allocation state machine — ADR-2606082000 (L0 assign an arriving vessel to a berth + STS crane window).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606082015.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BerthAllocationPhase(Enum):
    INIT = "init"
    BERTH_ASSIGNED = "berth_assigned"
    CRANE_WINDOW_RESERVED = "crane_window_reserved"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CellState:
    phase: str = BerthAllocationPhase.INIT.value
    moveId: str = "NIYAKU-MOVE-0001"
    vesselId: str = "MV-DEMO-0001"
    terminalId: str = "JPYOK-T1"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def transition_to_berth_assigned(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> BERTH_ASSIGNED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = BerthAllocationPhase.BERTH_ASSIGNED.value
    cs.completionPct = 33
    return {"cell_state": cs.__dict__, "next_node": "crane_window_reserved"}
def transition_to_crane_window_reserved(state: dict[str, Any]) -> dict[str, Any]:
    """BERTH_ASSIGNED -> CRANE_WINDOW_RESERVED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = BerthAllocationPhase.CRANE_WINDOW_RESERVED.value
    cs.completionPct = 67
    return {"cell_state": cs.__dict__, "next_node": "attestation_emitted"}
def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """CRANE_WINDOW_RESERVED -> ATTESTATION_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = BerthAllocationPhase.ATTESTATION_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
