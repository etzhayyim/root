"""Phase state machine for 扶持 (fuchi) routing_dispatch — the G3 in-kind rail decomposition.

Decomposes an assessed envelope into delivery RAILS over the existing producing actors. The
liquidity line becomes a MEMBER-PRINCIPAL warifu rail (扶持 never the creditor/payer). A cash
line is unrepresentable (cash≡0). REFUSAL gate, not a clamp.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

LINE_TO_RAIL = {
    "housing":   ("housing-commons", "commons-land"),
    "food":      ("food-mitsuho", "mitsuho"),
    "energy":    ("energy-hikari", "hikari"),
    "compute":   ("compute-murakumo", "murakumo"),
    "tooling":   ("tooling-okaimono", "okaimono"),
    "care":      ("care-iyashi", "iyashi"),
    "liquidity": ("liquidity-warifu", "warifu"),
}


class RoutePhase(Enum):
    INIT = "init"
    ROUTED = "routed"
    REFUSED = "refused"


@dataclass
class RouteState:
    phase: str = RoutePhase.INIT.value
    did: str = ""
    rails: list = field(default_factory=list)
    in_kind_coverage: float = 1.0
    refusal: str = ""


def _state(d: dict[str, Any]) -> RouteState:
    return RouteState(**d.get("cell_state", {}))


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def transition_to_routed(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.did = state.get("did", cs.did)
    lines = state.get("lines", [])

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = RoutePhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    rails = []
    total = 0
    in_kind = 0
    for ln in lines:
        kind = _kw(ln.get("line", ""))
        cash = int(ln.get("cash_usd_micros", 0))
        imputed = int(ln.get("imputed_usd_micros_yr", 0))
        if kind in ("cash", "stipend", "cash-disbursement") or cash != 0:
            return refuse("cash≡0: a cash rail is UNREPRESENTABLE (扶持 never pays cash)")
        if kind not in LINE_TO_RAIL:
            return refuse(f"G3: line {kind!r} has no in-kind rail")
        rail_kind, provider = LINE_TO_RAIL[kind]
        member_principal = (kind == "liquidity")
        rails.append({"allocId": cs.did, "kind": rail_kind, "providerActor": provider,
                      "imputedUsdMicrosYr": imputed, "memberPrincipal": member_principal})
        total += imputed
        if not member_principal:
            in_kind += imputed

    cs.rails = rails
    cs.in_kind_coverage = round(in_kind / total, 4) if total > 0 else 1.0
    cs.refusal = ""
    cs.phase = RoutePhase.ROUTED.value
    return {"cell_state": cs.__dict__}
