"""Phase state machine for the 助 (tasuke) intake_triage cell — the G1/G4/G7 intake membrane.

A consenting victim enters here. The case is SCREENED (refused outright) unless:
  G7 — consent is true and server-held-key is false (no-server-key);
  G1 — the support cost is 0 (全て無料; a fee is unrepresentable).
A SCREENED case is then TRIAGED into a scam KIND + severity (G4 — a routing kind, never a verdict).
REFUSAL gate, not a clamp.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntakePhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    TRIAGED = "triaged"
    REFUSED = "refused"


@dataclass
class IntakeState:
    phase: str = IntakePhase.INIT.value
    case_id: str = ""
    subject: str = ""
    consent: bool = False
    support_cost_jpy: int = 0
    server_held_key: bool = False
    scam_kind: str = ""
    severity: str = ""
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> IntakeState:
    return IntakeState(**d.get("cell_state", {}))


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.case_id = state.get("case_id", cs.case_id)
    cs.subject = state.get("subject", cs.subject)
    cs.consent = bool(state.get("consent", cs.consent))
    cs.support_cost_jpy = int(state.get("support_cost_jpy", cs.support_cost_jpy) or 0)
    cs.server_held_key = bool(state.get("server_held_key", cs.server_held_key))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = IntakePhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if not cs.consent:
        return refuse("G7: a case is opened only with the victim's explicit consent")
    if cs.support_cost_jpy != 0:
        return refuse("G1 全て無料: support cost must be 0 (cash≡0)")
    if cs.server_held_key:
        return refuse("G7/no-server-key: server-held-key must be false (ADR-2605231525)")

    cs.refusal = ""
    cs.phase = IntakePhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_triaged(state: dict[str, Any]) -> dict[str, Any]:
    from triage import assess_severity, classify

    cs = _state(state)
    if cs.phase != IntakePhase.SCREENED.value:
        cs.refusal = "cannot triage a case that was not screened clean"
        cs.phase = IntakePhase.REFUSED.value
        return {"cell_state": cs.__dict__}
    intake = state.get("intake", {})
    cs.scam_kind = classify(intake)
    cs.severity = assess_severity(intake, cs.scam_kind)
    cs.payload = {
        "caseId": cs.case_id,
        "subject": cs.subject,
        "scamKind": cs.scam_kind,
        "severity": cs.severity,
        "consent": True,
        "supportCostJpy": 0,
        "serverHeldKey": False,
    }
    cs.phase = IntakePhase.TRIAGED.value
    return {"cell_state": cs.__dict__}
