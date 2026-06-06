"""Phase state machine for 扶持 (fuchi) governance_gate — the G7 non-adjudicating router.

Routes an allocation to the body that decides it. The route is a PURE FUNCTION of
(imputed-total, invariant-touch, Charter-Rider hit) — 扶持 computes + routes, it NEVER
decides accept/reject (the 1 SBT = 1 vote or Council decides, 非裁定, the ake pattern):

    rider hit                     → :refused      (no vote can promote it)
    touches a constitutional inv. → :council-lv7  (e.g. a new commons-land grant)
    above the optimistic ceiling  → :sbt-vote     (1 SBT = 1 vote, 48h timelock)
    else                          → :auto         (optimistic fast-path)

Then, given a tally (only consulted for :sbt-vote), the OUTCOME is appended. There is no
:decision attribute the cell can set on its own authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

OPTIMISTIC_CEILING_USD_MICROS_YR = 24_000_000_000
RIDER_FORBIDDEN = (
    "advertis", "affiliate", "adsense", "weapon", "munition", "fire-control",
    "surveillance", "biometric", "addictive", "dark-pattern", "広告", "兵器",
)
INVARIANT_TOUCH_TOKENS = (
    "commons-land", "land-grant", "new-land", "force", "license-change", "charter",
)


class GovPhase(Enum):
    INIT = "init"
    ROUTED = "routed"
    DECIDED = "decided"


@dataclass
class GovState:
    phase: str = GovPhase.INIT.value
    alloc_id: str = ""
    imputed_total: int = 0
    context: str = ""
    route: str = ""
    mechanism: str = ""
    outcome: str = ""


def _state(d: dict[str, Any]) -> GovState:
    return GovState(**d.get("cell_state", {}))


def _rider(text: str) -> str:
    t = (text or "").lower()
    for tok in RIDER_FORBIDDEN:
        if tok in t:
            return tok
    return ""


def _touches_invariant(text: str) -> bool:
    t = (text or "").lower()
    return any(tok in t for tok in INVARIANT_TOUCH_TOKENS)


def transition_to_routed(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.alloc_id = state.get("alloc_id", cs.alloc_id)
    cs.imputed_total = int(state.get("imputed_total", cs.imputed_total))
    cs.context = state.get("context", cs.context)

    if _rider(cs.context):
        cs.route, cs.mechanism = "refused", "council-lv7"
    elif _touches_invariant(cs.context):
        cs.route, cs.mechanism = "council-lv7", "council-lv7"
    elif cs.imputed_total > OPTIMISTIC_CEILING_USD_MICROS_YR:
        cs.route, cs.mechanism = "sbt-vote", "sbt-vote"
    else:
        cs.route, cs.mechanism = "auto", "optimistic"

    cs.phase = GovPhase.ROUTED.value
    return {"cell_state": cs.__dict__}


def transition_to_decided(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    if cs.phase != GovPhase.ROUTED.value:
        cs.outcome = "pending"
        cs.phase = GovPhase.DECIDED.value
        return {"cell_state": cs.__dict__}

    if cs.route == "auto":
        cs.outcome = "accepted"
    elif cs.route == "refused":
        cs.outcome = "refused"
    elif cs.route == "council-lv7":
        cs.outcome = "pending"            # Council decides out of band
    elif cs.route == "sbt-vote":
        yes = int(state.get("yes", 0))
        no = int(state.get("no", 0))
        cs.outcome = "accepted" if yes > no else "rejected"
    cs.phase = GovPhase.DECIDED.value
    return {"cell_state": cs.__dict__}
