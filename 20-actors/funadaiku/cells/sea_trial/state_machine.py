"""sea_trial state machine — ADR-2606013400 (L5c speed / endurance / autonomy (MASS) / COLREG trial).

R0 scaffold: phase transitions are structural placeholders. The cell's .solve()
raises RuntimeError until Council Lv6+ ratifies the R1 activation ADR-2606013415.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SeaTrialPhase(Enum):
    INIT = "init"
    SPEED_TRIAL = "speed_trial"
    ENDURANCE_TRIAL = "endurance_trial"
    MASS_AUTONOMY_TRIAL = "mass_autonomy_trial"
    COLREG_TRIAL = "colreg_trial"
    RECORD_EMITTED = "record_emitted"


@dataclass
class CellState:
    phase: str = SeaTrialPhase.INIT.value
    vesselId: str = "NAGI-COASTAL-0001"
    vesselClass: str = "Nagi 凪"
    completionPct: int = 0
    robotSignatures: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)

def transition_to_speed_trial(state: dict[str, Any]) -> dict[str, Any]:
    """INIT -> SPEED_TRIAL."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = SeaTrialPhase.SPEED_TRIAL.value
    cs.completionPct = 20
    return {"cell_state": cs.__dict__, "next_node": "endurance_trial"}
def transition_to_endurance_trial(state: dict[str, Any]) -> dict[str, Any]:
    """SPEED_TRIAL -> ENDURANCE_TRIAL."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = SeaTrialPhase.ENDURANCE_TRIAL.value
    cs.completionPct = 40
    return {"cell_state": cs.__dict__, "next_node": "mass_autonomy_trial"}
def transition_to_mass_autonomy_trial(state: dict[str, Any]) -> dict[str, Any]:
    """ENDURANCE_TRIAL -> MASS_AUTONOMY_TRIAL."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = SeaTrialPhase.MASS_AUTONOMY_TRIAL.value
    cs.completionPct = 60
    return {"cell_state": cs.__dict__, "next_node": "colreg_trial"}
def transition_to_colreg_trial(state: dict[str, Any]) -> dict[str, Any]:
    """MASS_AUTONOMY_TRIAL -> COLREG_TRIAL."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = SeaTrialPhase.COLREG_TRIAL.value
    cs.completionPct = 80
    return {"cell_state": cs.__dict__, "next_node": "record_emitted"}
def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    """COLREG_TRIAL -> RECORD_EMITTED."""
    cs = CellState(**state.get("cell_state", {}))
    cs.phase = SeaTrialPhase.RECORD_EMITTED.value
    cs.completionPct = 100
    return {"cell_state": cs.__dict__, "next_node": "end"}
