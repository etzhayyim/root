"""Phase state machine for 扶持 (fuchi) covenant_intake — the G4/G5/G9 eligibility membrane.

A 信者 maintainer's covenant enters here. It is SCREENED (refused) unless:
  G4 — covenant ∈ {outreach, vowed} (anon/server unrepresentable, conversion-gated §1.16);
  G5 — owns-payoff is false (the work product is commons; payoff帰属 = etzhayyim);
  G9 — server-held-key is false (no-server-key; the covenant is member-signed).
A SCREENED covenant is RECORDED as a :maintainer/* record. REFUSAL gate, not a clamp.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_COVENANTS = ("outreach", "vowed")


class IntakePhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    RECORDED = "recorded"
    REFUSED = "refused"


@dataclass
class IntakeState:
    phase: str = IntakePhase.INIT.value
    did: str = ""
    covenant: str = ""
    tenure_months: int = 0
    hazard_permille: int = 1000
    owns_payoff: bool = False
    server_held_key: bool = False
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> IntakeState:
    return IntakeState(**d.get("cell_state", {}))


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.did = state.get("did", cs.did)
    cs.covenant = _kw(state.get("covenant", cs.covenant))
    cs.tenure_months = int(state.get("tenure_months", cs.tenure_months))
    cs.hazard_permille = int(state.get("hazard_permille", cs.hazard_permille))
    cs.owns_payoff = bool(state.get("owns_payoff", cs.owns_payoff))
    cs.server_held_key = bool(state.get("server_held_key", cs.server_held_key))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = IntakePhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if cs.covenant not in _COVENANTS:
        return refuse(f"G4: covenant {cs.covenant!r} unrepresentable (conversion-gated §1.16)")
    if cs.owns_payoff:
        return refuse("G5: owns-payoff must be false (work product is commons; payoff帰属=etzhayyim)")
    if cs.server_held_key:
        return refuse("G9/no-server-key: server-held-key must be false (ADR-2605231525)")
    if not (1000 <= cs.hazard_permille <= 2000):
        return refuse("hazard-permille out of [1000,2000]")

    cs.refusal = ""
    cs.phase = IntakePhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_recorded(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    if cs.phase != IntakePhase.SCREENED.value:
        cs.refusal = "cannot record a covenant that was not screened clean"
        cs.phase = IntakePhase.REFUSED.value
        return {"cell_state": cs.__dict__}
    cs.payload = {
        "maintainerDid": cs.did,
        "covenant": cs.covenant,
        "tenureMonths": cs.tenure_months,
        "hazardPermille": cs.hazard_permille,
        "ownsPayoff": False,
        "serverHeldKey": False,
    }
    cs.phase = IntakePhase.RECORDED.value
    return {"cell_state": cs.__dict__}
