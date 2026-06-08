"""trolley_traverse state machine — ADR-2606082000 (L4 anti-sway trolley traverse ship<->shore (crane_dynamics / Isaac-Sim verified)).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606082015.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TrolleyTraversePhase(Enum):
    INIT = "init"
    TRAVERSE_COMMANDED = "traverse_commanded"
    ANTI_SWAY_SETTLED = "anti_sway_settled"
    OVER_TARGET_SLOT = "over_target_slot"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CellState:
    phase: str = TrolleyTraversePhase.INIT.value
    moveId: str = "NIYAKU-MOVE-0001"
    vesselId: str = "MV-DEMO-0001"
    terminalId: str = "JPYOK-T1"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def transition_to_traverse_commanded(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> TRAVERSE_COMMANDED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = TrolleyTraversePhase.TRAVERSE_COMMANDED.value
    cs.completionPct = 25
    return {"cell_state": cs.__dict__, "next_node": "anti_sway_settled"}
def transition_to_anti_sway_settled(state: dict[str, Any]) -> dict[str, Any]:
    """TRAVERSE_COMMANDED -> ANTI_SWAY_SETTLED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = TrolleyTraversePhase.ANTI_SWAY_SETTLED.value
    cs.completionPct = 50
    return {"cell_state": cs.__dict__, "next_node": "over_target_slot"}
def transition_to_over_target_slot(state: dict[str, Any]) -> dict[str, Any]:
    """ANTI_SWAY_SETTLED -> OVER_TARGET_SLOT."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = TrolleyTraversePhase.OVER_TARGET_SLOT.value
    cs.completionPct = 75
    return {"cell_state": cs.__dict__, "next_node": "attestation_emitted"}
def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """OVER_TARGET_SLOT -> ATTESTATION_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = TrolleyTraversePhase.ATTESTATION_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
