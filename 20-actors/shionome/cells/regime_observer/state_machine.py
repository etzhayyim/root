"""Phase state machine for the 潮目 (shionome) regime_observer cell.

Derives the FACTUAL cross-asset regime (risk-on/off/mixed/indeterminate) from net flow into
risk vs safe buckets. DESCRIPTIVE, never advice (G2, トレードはしない). Self-contained.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RegimePhase(Enum):
    INIT = "init"
    OBSERVED = "observed"


@dataclass
class RegimeState:
    phase: str = RegimePhase.INIT.value
    net: dict = field(default_factory=dict)        # bucket -> net flow
    risk_tag: dict = field(default_factory=dict)   # bucket -> "risk"/"safe"/"neutral"
    regime: str = ""
    risk_net: float = 0.0
    safe_net: float = 0.0
    no_trade_notice: bool = True


def transition_to_observed(state: dict[str, Any]) -> dict[str, Any]:
    cs = RegimeState(**state.get("cell_state", {}))
    cs.net = state.get("net", cs.net)
    cs.risk_tag = state.get("risk_tag", cs.risk_tag)
    risk_net = sum(v for b, v in cs.net.items() if cs.risk_tag.get(b) == "risk")
    safe_net = sum(v for b, v in cs.net.items() if cs.risk_tag.get(b) == "safe")
    if risk_net == 0.0 and safe_net == 0.0:
        label = "indeterminate"
    elif risk_net > 0 and safe_net <= 0:
        label = "risk-on"
    elif risk_net < 0 and safe_net >= 0:
        label = "risk-off"
    else:
        label = "mixed"
    cs.risk_net, cs.safe_net, cs.regime = round(risk_net, 4), round(safe_net, 4), label
    cs.no_trade_notice = True
    cs.phase = RegimePhase.OBSERVED.value
    return {"cell_state": cs.__dict__}
