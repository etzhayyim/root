"""Phase state machine for the 系図 (keizu) committee_graph cell.

Given committee composition snapshots, derives cross-committee co-membership EDGES (a seat on
>1 committee) — edge-primary (G4), never a per-seat score. Self-contained.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CommitteePhase(Enum):
    INIT = "init"
    COMPOSED = "composed"
    REFUSED = "refused"


@dataclass
class CommitteeState:
    phase: str = CommitteePhase.INIT.value
    committees: list = field(default_factory=list)
    co_membership: list = field(default_factory=list)
    refusal: str = ""


def _state(d: dict[str, Any]) -> CommitteeState:
    return CommitteeState(**d.get("cell_state", {}))


def transition_to_composed(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.committees = state.get("committees", cs.committees)
    if not cs.committees:
        cs.refusal = "no committees to compose"
        cs.phase = CommitteePhase.REFUSED.value
        return {"cell_state": cs.__dict__}
    by_seat: dict[str, list] = {}
    for c in cs.committees:
        for seat in c.get("members", []):
            by_seat.setdefault(seat, []).append(c.get("id"))
    cs.co_membership = [
        {"seat": s, "committees": sorted(set(cl))}
        for s, cl in sorted(by_seat.items()) if len(set(cl)) > 1
    ]
    cs.phase = CommitteePhase.COMPOSED.value
    return {"cell_state": cs.__dict__}
