"""Phase state machine for 扶持 (fuchi) allocation_compute — the G1/G2/G5 allocator.

Computes a tenure-weighted in-kind allocation for a screened maintainer. The membrane
REFUSES any instrument that is an investment/return vehicle (G1) and structurally fixes
cash to 0 (G2) and owns-payoff to false (G5). Delegates the math to methods/allocate.py
(imported lazily so the cell tree has no hard dependency on the sibling methods package).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ALLOWED_INSTRUMENTS = ("in-kind-grant", "sustenance", "tooling-access", "compute-access")
FORBIDDEN_INSTRUMENTS = (
    "equity", "debt", "convertible", "revenue-share", "profit-claim",
    "carry", "dividend", "loan", "interest", "warrant", "option", "exit",
)
TENURE_CAP_YEARS = 40.0


class ComputePhase(Enum):
    INIT = "init"
    COMPUTED = "computed"
    REFUSED = "refused"


@dataclass
class ComputeState:
    phase: str = ComputePhase.INIT.value
    did: str = ""
    instrument: str = "sustenance"
    tenure_months: int = 0
    hazard_permille: int = 1000
    owns_payoff: bool = False
    weight: float = 0.0
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> ComputeState:
    return ComputeState(**d.get("cell_state", {}))


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def transition_to_computed(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.did = state.get("did", cs.did)
    cs.instrument = _kw(state.get("instrument", cs.instrument))
    cs.tenure_months = int(state.get("tenure_months", cs.tenure_months))
    cs.hazard_permille = int(state.get("hazard_permille", cs.hazard_permille))
    cs.owns_payoff = bool(state.get("owns_payoff", cs.owns_payoff))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = ComputePhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if cs.instrument in FORBIDDEN_INSTRUMENTS:
        return refuse(f"G1: instrument {cs.instrument!r} is an investment vehicle — UNREPRESENTABLE")
    if cs.instrument not in ALLOWED_INSTRUMENTS:
        return refuse(f"G1: instrument {cs.instrument!r} not a sustenance instrument")
    if cs.owns_payoff:
        return refuse("G5: a maintainer cannot own the payoff (work product is commons)")

    years = min(cs.tenure_months / 12.0, TENURE_CAP_YEARS)
    hazard = cs.hazard_permille / 1000.0
    cs.weight = round(math.log1p(years) * hazard, 6)
    cs.payload = {
        "maintainerDid": cs.did,
        "instrument": cs.instrument,
        "weight": cs.weight,
        "cashUsdMicros": 0,      # G2 — structural
        "serverHeldKey": False,  # G9 — structural
    }
    cs.refusal = ""
    cs.phase = ComputePhase.COMPUTED.value
    return {"cell_state": cs.__dict__}
