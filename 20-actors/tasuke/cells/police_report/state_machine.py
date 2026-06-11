"""Phase state machine for the 助 (tasuke) police_report cell — the G3 generation membrane.

Generates a police-side document and GUARDS the invariants: it is authored BY THE MEMBER
(本人作成の申告書類, never police-authored — 公文書偽造を排除), requires the member's signature,
is free, and is draft-only at R0. A request to author a doc AS the police is REFUSED.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_POLICE_KINDS = ("damage-report", "incident-statement", "evidence-index", "damage-calculation")


class ReportPhase(Enum):
    INIT = "init"
    GENERATED = "generated"
    REFUSED = "refused"


@dataclass
class ReportState:
    phase: str = ReportPhase.INIT.value
    case_id: str = ""
    kind: str = ""
    authored_by: str = ""
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> ReportState:
    return ReportState(**d.get("cell_state", {}))


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
        cs.phase = ReportPhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if cs.authored_by != "member":
        return refuse("G3: a generated document must be authored by 'member' (公文書偽造を排除; "
                      "police/official/server unrepresentable)")
    if cs.kind not in _POLICE_KINDS:
        return refuse(f"unknown police doc kind {cs.kind!r}")

    case = state.get("case", {":case/id": cs.case_id})
    gen = {
        "damage-report": rg.damage_report,
        "incident-statement": rg.incident_statement,
        "damage-calculation": rg.damage_calculation,
    }
    if cs.kind == "evidence-index":
        doc = rg.evidence_index_doc(case, state.get("evidence", []))
    else:
        doc = gen[cs.kind](case)
    rg.assert_member_authored(doc)   # G1/G2/G3/G9 guard
    cs.payload = {
        "docId": doc[":doc/id"], "kind": cs.kind, "authoredBy": "member",
        "needsMemberSignature": True, "supportCostJpy": 0, "published": False,
    }
    cs.refusal = ""
    cs.phase = ReportPhase.GENERATED.value
    return {"cell_state": cs.__dict__}
