"""Phase state machine for the hotaru commons_readiness (蛍) cell.

Aggregates per-stage open-publication coverage into a commonsReadinessReport routed to
the ADR-2605265500 §2 R4+ gate evaluation. The heavy lifting (parsing the graph, the
per-stage coverage) lives in methods/analyze.py; this cell assembles the *report record*
and STRUCTURALLY enforces non-adjudication.

Invariants enforced:
  G3 — non-adjudicating: the report carries `fabricationProhibited` forced True and
       `r4GateSatisfiable` as a COMPUTED fact about the commons; it can NEVER carry a
       "fabrication opened / permitted / decided" field. Any attempt to mark the gate
       as decided/opened here raises ValueError — opening the gate is Council Lv7+, never
       this actor (ADR-2605265500 §2).

Maturity scoring (substrate stages only): open-mature=1.0, open-emerging=0.5, gap=0.0,
averaged over the 4 substrate stages → a single 0..1 commons-maturity score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SUBSTRATE_STAGES = ("synthesis", "bulk-growth", "wafering", "surface-prep")
_STAGE_WEIGHT = {"open-mature": 1.0, "open-emerging": 0.5, "gap": 0.0, "absent": 0.0}
# Fields that would turn a report into an adjudication — forbidden (G3).
FORBIDDEN_KEYS = ("fabricationOpened", "fabricationPermitted", "gateDecided", "gateOpened")


class ReadinessPhase(Enum):
    INIT = "init"
    ASSESSED = "assessed"
    REPORTED = "reported"


@dataclass
class ReadinessState:
    phase: str = ReadinessPhase.INIT.value
    # per_stage: {stage: best-maturity-string} for the 4 substrate stages
    per_stage: dict = field(default_factory=dict)
    epitaxy_open_mature: bool = False
    stages_covered: int = 0
    substrate_commons_ready: bool = False
    r4_gate_satisfiable: bool = False
    maturity_score: float = 0.0
    conflict_flagged: int = 0
    sourcing: str = "derived"
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> ReadinessState:
    return ReadinessState(**d.get("cell_state", {}))


def _norm(v: str | None) -> str:
    return (v or "").lstrip(":")


def transition_to_assessed(state: dict[str, Any]) -> dict[str, Any]:
    """Compute coverage + maturity score. G3: reject any adjudicating input key."""
    cs = _state(state)

    for k in FORBIDDEN_KEYS:
        if k in state:
            raise ValueError(
                f"G3 violation: commons_readiness is non-adjudicating; it cannot carry "
                f"{k!r}. Opening the ADR-2605265500 §2 R4+ gate is Council Lv7+ only — "
                f"this cell reports the commons, it never decides fabrication."
            )

    # per_stage maps each substrate stage to its best maturity string (default 'absent')
    raw = state.get("per_stage", cs.per_stage) or {}
    cs.per_stage = {_norm(k): _norm(v) for k, v in raw.items()}
    cs.epitaxy_open_mature = bool(state.get("epitaxy_open_mature", cs.epitaxy_open_mature))
    cs.conflict_flagged = int(state.get("conflict_flagged", cs.conflict_flagged))

    covered = 0
    score_sum = 0.0
    for st in SUBSTRATE_STAGES:
        m = cs.per_stage.get(st, "absent")
        if m not in _STAGE_WEIGHT:
            raise ValueError(f"unknown maturity {m!r} for stage {st!r}")
        score_sum += _STAGE_WEIGHT[m]
        if m == "open-mature":
            covered += 1
    cs.stages_covered = covered
    cs.maturity_score = round(score_sum / len(SUBSTRATE_STAGES), 4)
    cs.substrate_commons_ready = covered == len(SUBSTRATE_STAGES)
    # R4+ gate is satisfiable from the commons only if the WHOLE chain incl. epitaxy is
    # open-mature. Reported, NOT decided (G3).
    cs.r4_gate_satisfiable = cs.substrate_commons_ready and cs.epitaxy_open_mature
    cs.phase = ReadinessPhase.ASSESSED.value
    return {"cell_state": cs.__dict__}


def transition_to_reported(state: dict[str, Any]) -> dict[str, Any]:
    """Materialize the commonsReadinessReport record (non-adjudicating, G3)."""
    cs = _state(state)
    if cs.phase != ReadinessPhase.ASSESSED.value:
        raise ValueError("report requires an assessment first")
    cs.payload = {
        "stagesCovered": cs.stages_covered,
        "stagesTotal": len(SUBSTRATE_STAGES),
        "substrateCommonsReady": cs.substrate_commons_ready,
        "epitaxyOpenMature": cs.epitaxy_open_mature,
        "r4GateSatisfiable": cs.r4_gate_satisfiable,
        "maturityScore": cs.maturity_score,
        "conflictFlagged": cs.conflict_flagged,
        "fabricationProhibited": True,  # G3 — invariant, this report never opens fabrication
        "sourcing": "derived",
    }
    cs.phase = ReadinessPhase.REPORTED.value
    return {"cell_state": cs.__dict__}
