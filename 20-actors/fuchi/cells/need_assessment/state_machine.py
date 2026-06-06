"""Phase state machine for 扶持 (fuchi) need_assessment — the G2/G3 in-kind envelope.

A maintainer's sustenance NEED is assessed here as a set of in-kind lines. The membrane
REFUSES (not clamps) any line that:
  G2 — carries nonzero cash (cash≡0, Basic High Income in-kind);
  G3 — is not one of the covered in-kind lines (cash/stipend/disbursement unrepresentable).
A clean assessment yields :envelope/* lines whose cash is structurally 0.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_LINES = ("housing", "food", "energy", "compute", "tooling", "care", "liquidity")


class AssessPhase(Enum):
    INIT = "init"
    ASSESSED = "assessed"
    REFUSED = "refused"


@dataclass
class AssessState:
    phase: str = AssessPhase.INIT.value
    did: str = ""
    lines: list = field(default_factory=list)
    imputed_total: int = 0
    refusal: str = ""
    payload: list = field(default_factory=list)


def _state(d: dict[str, Any]) -> AssessState:
    return AssessState(**d.get("cell_state", {}))


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def transition_to_assessed(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.did = state.get("did", cs.did)
    raw = state.get("lines", cs.lines)

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = AssessPhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    out = []
    total = 0
    for ln in raw:
        kind = _kw(ln.get("line", ""))
        cash = int(ln.get("cash_usd_micros", 0))
        imputed = int(ln.get("imputed_usd_micros_yr", 0))
        if kind in ("cash", "stipend", "cash-disbursement"):
            return refuse(f"G3: line {kind!r} unrepresentable (cash≡0; 扶持 never pays cash)")
        if kind not in _LINES:
            return refuse(f"G3: line {kind!r} has no in-kind rail")
        if cash != 0:
            return refuse("G2/cash≡0: a sustenance line cannot carry cash")
        out.append({"maintainerDid": cs.did, "line": kind,
                    "imputedUsdMicrosYr": imputed, "cashUsdMicros": 0})
        total += imputed

    cs.payload = out
    cs.imputed_total = total
    cs.refusal = ""
    cs.phase = AssessPhase.ASSESSED.value
    return {"cell_state": cs.__dict__}
