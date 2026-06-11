"""Phase state machine for the 助 (tasuke) platform_abuse cell — bank/platform request membrane.

Generates a bank-freeze or platform request, member-authored (G3), to be sent BY THE MEMBER
(G2 — no 代理送付), free (G1), draft-only (G9). A request to send as an agent is REFUSED.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_REQUEST_KINDS = ("bank-freeze-request", "platform-request")


class RequestPhase(Enum):
    INIT = "init"
    GENERATED = "generated"
    REFUSED = "refused"


@dataclass
class RequestState:
    phase: str = RequestPhase.INIT.value
    case_id: str = ""
    kind: str = ""
    authored_by: str = ""
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> RequestState:
    return RequestState(**d.get("cell_state", {}))


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def generate(state: dict[str, Any]) -> dict[str, Any]:
    import report_gen as rg

    cs = _state(state)
    cs.case_id = state.get("case_id", cs.case_id)
    cs.kind = _kw(state.get("kind", cs.kind))
    cs.authored_by = _kw(state.get("authored_by", "member"))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = RequestPhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if cs.authored_by != "member":
        return refuse("G3: a request must be authored by 'member' (server/agent unrepresentable)")
    if cs.kind not in _REQUEST_KINDS:
        return refuse(f"unknown request kind {cs.kind!r}")

    case = state.get("case", {":case/id": cs.case_id})
    doc = (rg.bank_freeze_request(case) if cs.kind == "bank-freeze-request"
           else rg.platform_request(case, purpose=state.get("purpose", "凍結・復旧")))
    rg.assert_member_authored(doc)   # G1/G2/G3/G9 guard
    cs.payload = {
        "docId": doc[":doc/id"], "kind": cs.kind, "authoredBy": "member",
        "addressedTo": doc[":doc/addressed-to"], "needsMemberSignature": True,
        "supportCostJpy": 0, "published": False,
    }
    cs.refusal = ""
    cs.phase = RequestPhase.GENERATED.value
    return {"cell_state": cs.__dict__}
