"""Phase state machine for the 助 (tasuke) evidence_preservation cell — the G6 membrane.

Each evidence item is PRESERVED (refused if it carries plaintext PII, or lacks an encrypted
envelope-ref) then INDEXED with a chain-of-custody sha256 so the victim can later prove it is
unchanged. REFUSAL gate, not a clamp.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EvidencePhase(Enum):
    INIT = "init"
    PRESERVED = "preserved"
    REFUSED = "refused"


@dataclass
class EvidenceState:
    phase: str = EvidencePhase.INIT.value
    case_id: str = ""
    count: int = 0
    refusal: str = ""
    rows: list = field(default_factory=list)


def _state(d: dict[str, Any]) -> EvidenceState:
    return EvidenceState(**d.get("cell_state", {}))


def preserve(state: dict[str, Any]) -> dict[str, Any]:
    from evidence import index

    cs = _state(state)
    cs.case_id = state.get("case_id", cs.case_id)
    items = state.get("items", [])
    try:
        cs.rows = index(items)
    except ValueError as exc:
        cs.refusal = str(exc)
        cs.phase = EvidencePhase.REFUSED.value
        return {"cell_state": cs.__dict__}
    cs.count = len(cs.rows)
    cs.refusal = ""
    cs.phase = EvidencePhase.PRESERVED.value
    return {"cell_state": cs.__dict__}
