"""Phase state machine for the 朱 (ake) review_vote cell — the community-consensus membrane.

An escalated proposal is decided by the mechanism its triage route selected:
  optimistic  — low-risk well-sourced edit; accepted on the fast path (no vote needed).
  sbt-vote    — 1 SBT = 1 vote with a timelock; accepted iff yes > no after the window.
  council-lv7 — invariant-adjacent; this cell returns :pending (Council attests separately, G7).
A server-signed tally is REFUSED (no-server-key). Mirrors Wikipedia discussion/RfC, on-chain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

DEFAULT_TIMELOCK_H = 48
_MECHANISMS = ("optimistic", "sbt-vote", "council-lv7")


class ReviewPhase(Enum):
    INIT = "init"
    TALLIED = "tallied"
    REFUSED = "refused"


@dataclass
class ReviewState:
    phase: str = ReviewPhase.INIT.value
    edit_id: str = ""
    mechanism: str = "sbt-vote"
    yes: int = 0
    no: int = 0
    timelock_h: int = DEFAULT_TIMELOCK_H
    signed_by: str = ""
    outcome: str = "pending"
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> ReviewState:
    return ReviewState(**d.get("cell_state", {}))


def tally(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.edit_id = state.get("edit_id", cs.edit_id)
    cs.mechanism = str(state.get("mechanism", cs.mechanism)).lstrip(":")
    cs.yes = int(state.get("yes", cs.yes))
    cs.no = int(state.get("no", cs.no))
    cs.timelock_h = int(state.get("timelock_h", cs.timelock_h))
    cs.signed_by = state.get("signed_by", cs.signed_by) or ""

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = ReviewPhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if cs.mechanism not in _MECHANISMS:
        return refuse(f"unknown review mechanism {cs.mechanism!r}")
    if cs.signed_by.lower().startswith("server"):
        return refuse("no-server-key: a tally cannot be server-signed (ADR-2605231525)")

    if cs.mechanism == "optimistic":
        cs.outcome = "accepted"
    elif cs.mechanism == "sbt-vote":
        cs.outcome = "accepted" if cs.yes > cs.no else "rejected"
    else:  # council-lv7
        cs.outcome = "pending"   # Council attests via councilEditReview (G7)

    cs.payload = {
        "editId": cs.edit_id, "mechanism": cs.mechanism,
        "yes": cs.yes, "no": cs.no, "timelockH": cs.timelock_h,
        "outcome": cs.outcome, "signedBy": cs.signed_by,
    }
    cs.refusal = ""
    cs.phase = ReviewPhase.TALLIED.value
    return {"cell_state": cs.__dict__}
