"""Phase state machine for the 助 (tasuke) account_recovery cell — the G2 self-help membrane.

Generates a recovery plan whose :support-role is :self-submit (the member executes the steps;
助 never logs in as an agent). A request to act AS the member (represent/proxy/agent-file) is
REFUSED. Free (G1), member-authored (G3), draft-only (G9).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_ALLOWED_ROLES = ("guide", "draft-assist", "self-submit")


class RecoveryPhase(Enum):
    INIT = "init"
    PLANNED = "planned"
    REFUSED = "refused"


@dataclass
class RecoveryState:
    phase: str = RecoveryPhase.INIT.value
    case_id: str = ""
    service: str = ""
    role: str = "self-submit"
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> RecoveryState:
    return RecoveryState(**d.get("cell_state", {}))


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def plan(state: dict[str, Any]) -> dict[str, Any]:
    import report_gen as rg

    cs = _state(state)
    cs.case_id = state.get("case_id", cs.case_id)
    cs.service = state.get("service", cs.service) or "（サービス名）"
    cs.role = _kw(state.get("role", cs.role))

    if cs.role not in _ALLOWED_ROLES:
        cs.refusal = (f"G2: support-role {cs.role!r} unrepresentable — only "
                      "guide/draft-assist/self-submit (no 代理ログイン)")
        cs.phase = RecoveryPhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    case = state.get("case", {":case/id": cs.case_id})
    doc = rg.recovery_plan(case, service=cs.service)
    rg.assert_member_authored(doc)
    cs.payload = {
        "docId": doc[":doc/id"], "kind": "recovery-plan", "service": cs.service,
        "authoredBy": "member", "supportRole": ":self-submit",
        "steps": doc.get("steps", []), "supportCostJpy": 0, "published": False,
    }
    cs.refusal = ""
    cs.phase = RecoveryPhase.PLANNED.value
    return {"cell_state": cs.__dict__}
