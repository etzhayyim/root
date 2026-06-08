"""manifest_attestation state machine — ADR-2606074000 (terminal per-move kotoba EAVT anchor + open move registry).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606074015.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ManifestAttestationPhase(Enum):
    INIT = "init"
    MOVE_RECORDED = "move_recorded"
    DATOM_ANCHORED = "datom_anchored"
    ATTESTATION_EMITTED = "attestation_emitted"


@dataclass
class CellState:
    phase: str = ManifestAttestationPhase.INIT.value
    moveId: str = "NIYAKU-MOVE-0001"
    vesselId: str = "MV-DEMO-0001"
    terminalId: str = "JPYOK-T1"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def transition_to_move_recorded(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> MOVE_RECORDED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = ManifestAttestationPhase.MOVE_RECORDED.value
    cs.completionPct = 33
    return {"cell_state": cs.__dict__, "next_node": "datom_anchored"}
def transition_to_datom_anchored(state: dict[str, Any]) -> dict[str, Any]:
    """MOVE_RECORDED -> DATOM_ANCHORED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = ManifestAttestationPhase.DATOM_ANCHORED.value
    cs.completionPct = 67
    return {"cell_state": cs.__dict__, "next_node": "attestation_emitted"}
def transition_to_attestation_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """DATOM_ANCHORED -> ATTESTATION_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = ManifestAttestationPhase.ATTESTATION_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
