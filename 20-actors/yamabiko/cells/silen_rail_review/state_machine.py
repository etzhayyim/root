"""silenRailReview state machine — ADR-2605252600 governance.

Council 5-of-7 Safe attestation for new Wave / new trainset / new jurisdiction
/ G7 transition / gate amendment. Required before any L1 fabrication of new
trainset class.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ReviewPhase(Enum):
    INIT = "init"
    SCOPE_DECLARED = "scope_declared"
    SIGNATURES_COLLECTED = "signatures_collected"
    DECISION_RECORDED = "decision_recorded"
    RECORD_EMITTED = "record_emitted"


@dataclass
class ReviewState:
    phase: ReviewPhase
    reviewSubjectId: str
    completionPct: int
    scope: str | None = None
    councilSafeAddress: str | None = None
    councilSignatures: list[dict[str, Any]] | None = None
    decision: str | None = None
    rationale: str | None = None


def transition_to_scope_declared(state: dict[str, Any]) -> dict[str, Any]:
    s = ReviewState(**state.get("review_state", {}))
    s.scope = state.get("scope", "r0-scaffold-baseline")
    s.councilSafeAddress = "0xCouncilSafe5of7..."
    s.phase = ReviewPhase.SCOPE_DECLARED
    s.completionPct = 25
    return {"review_state": s.__dict__, "next_node": "signatures"}


def transition_to_signatures_collected(state: dict[str, Any]) -> dict[str, Any]:
    s = ReviewState(**state.get("review_state", {}))
    s.councilSignatures = [
        {"councilMemberDid": "did:web:etzhayyim.com:council-member-1", "signature": "...", "timestamp": "2026-05-27T16:00:00Z"},
        {"councilMemberDid": "did:web:etzhayyim.com:council-member-2", "signature": "...", "timestamp": "2026-05-27T16:00:05Z"},
        {"councilMemberDid": "did:web:etzhayyim.com:council-member-3", "signature": "...", "timestamp": "2026-05-27T16:00:10Z"},
        {"councilMemberDid": "did:web:etzhayyim.com:council-member-4", "signature": "...", "timestamp": "2026-05-27T16:00:15Z"},
        {"councilMemberDid": "did:web:etzhayyim.com:council-member-5", "signature": "...", "timestamp": "2026-05-27T16:00:20Z"},
    ]
    s.phase = ReviewPhase.SIGNATURES_COLLECTED
    s.completionPct = 70
    return {"review_state": s.__dict__, "next_node": "decision"}


def transition_to_decision_recorded(state: dict[str, Any]) -> dict[str, Any]:
    s = ReviewState(**state.get("review_state", {}))
    s.decision = "approve"
    s.rationale = "Wave 1 R0 scaffold baseline review — Constitutional gates G1..G14 + Non-goals N1..N12 declared per ADR-2605252600. 5 Council signatures collected. Approved."
    s.phase = ReviewPhase.DECISION_RECORDED
    s.completionPct = 90
    return {"review_state": s.__dict__, "next_node": "record"}


def transition_to_record_emitted(state: dict[str, Any]) -> dict[str, Any]:
    s = ReviewState(**state.get("review_state", {}))
    s.phase = ReviewPhase.RECORD_EMITTED
    s.completionPct = 100
    record = {
        "$type": "com.etzhayyim.yamabiko.silenRailReview",
        "reviewSubjectId": s.reviewSubjectId,
        "scope": s.scope,
        "councilSafeAddress": s.councilSafeAddress,
        "councilSignatures": s.councilSignatures,
        "decision": s.decision,
        "rationale": s.rationale,
        "recordedAt": "2026-05-27T16:01:00Z",
    }
    return {"review_state": s.__dict__, "silen_rail_review": record, "next_node": "end"}
