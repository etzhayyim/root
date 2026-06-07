"""Phase state machine for the 系図 (keizu) money_graph cell.

Aggregates disclosed money flows into per-payee shares + HHI (aggregate, factual; G2/G4).
Self-contained.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MoneyPhase(Enum):
    INIT = "init"
    AGGREGATED = "aggregated"
    REFUSED = "refused"


@dataclass
class MoneyState:
    phase: str = MoneyPhase.INIT.value
    money: list = field(default_factory=list)
    total: float = 0.0
    hhi: float = 0.0
    shares: list = field(default_factory=list)
    refusal: str = ""


def _state(d: dict[str, Any]) -> MoneyState:
    return MoneyState(**d.get("cell_state", {}))


def transition_to_aggregated(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.money = state.get("money", cs.money)
    if not cs.money:
        cs.refusal = "no money flows to aggregate"
        cs.phase = MoneyPhase.REFUSED.value
        return {"cell_state": cs.__dict__}
    by_payee: dict[str, float] = {}
    for m in cs.money:
        by_payee[m.get("payee")] = by_payee.get(m.get("payee"), 0.0) + float(m.get("amount", 0.0))
    cs.total = sum(by_payee.values())
    shares = {p: (v / cs.total if cs.total else 0.0) for p, v in by_payee.items()}
    cs.hhi = round(sum(s * s for s in shares.values()), 4)
    cs.shares = sorted(([p, round(s, 4)] for p, s in shares.items()), key=lambda x: -x[1])
    cs.phase = MoneyPhase.AGGREGATED.value
    return {"cell_state": cs.__dict__}
