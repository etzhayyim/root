"""lashing_twistlock state machine — ADR-2606082000 (L6 secure/lash the loaded box for sea passage).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606082015.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LashingTwistlockPhase(Enum):
    INIT = "init"
    LASHING_APPLIED = "lashing_applied"
    TENSION_VERIFIED = "tension_verified"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CellState:
    phase: str = LashingTwistlockPhase.INIT.value
    moveId: str = "NIYAKU-MOVE-0001"
    vesselId: str = "MV-DEMO-0001"
    terminalId: str = "JPYOK-T1"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def transition_to_lashing_applied(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> LASHING_APPLIED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = LashingTwistlockPhase.LASHING_APPLIED.value
    cs.completionPct = 33
    return {"cell_state": cs.__dict__, "next_node": "tension_verified"}
def transition_to_tension_verified(state: dict[str, Any]) -> dict[str, Any]:
    """LASHING_APPLIED -> TENSION_VERIFIED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = LashingTwistlockPhase.TENSION_VERIFIED.value
    cs.completionPct = 67
    return {"cell_state": cs.__dict__, "next_node": "attestation_emitted"}
def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """TENSION_VERIFIED -> ATTESTATION_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = LashingTwistlockPhase.ATTESTATION_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
