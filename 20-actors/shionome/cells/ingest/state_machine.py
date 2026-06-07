"""Phase state machine for the 潮目 (shionome) ingest cell — the G1/G2/G3 intake membrane.

A public market-data batch enters. Each record is SCREENED against the closed structural vocab:
  G1 — a bucket scope must be a public capital bucket (no person / account / portfolio);
  G2 — a flow kind must be a factual observation (no trade/advisory token — トレードはしない);
  G3 — a flow must carry ≥2 public-source citations.
A clean batch is RECORDED (counts only at R0); any violation REFUSES the whole batch.
Self-contained (no methods import) so the cell suite runs standalone.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

BUCKET_SCOPES = ("asset-class", "sector", "region", "theme")
FLOW_KINDS = ("rotation", "fund-inflow", "fund-outflow", "price-move",
              "cross-correlation", "volume-shift", "yield-shift", "fx-flow")
TRADE_TOKENS = ("buy", "sell", "long", "short", "overweight", "underweight", "recommend",
                "target price", "target-price", "推奨", "買い", "売り", "目標株価", "空売り")


class IngestPhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    RECORDED = "recorded"
    REFUSED = "refused"


@dataclass
class IngestState:
    phase: str = IngestPhase.INIT.value
    buckets: list = field(default_factory=list)
    flows: list = field(default_factory=list)
    snapshots: list = field(default_factory=list)
    recorded: int = 0
    refusal: str = ""


def _state(d: dict[str, Any]) -> IngestState:
    return IngestState(**d.get("cell_state", {}))


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def _trade_token(text: str) -> str:
    blob = str(text or "").lower()
    for t in TRADE_TOKENS:
        if t in blob:
            return t
    return ""


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.buckets = state.get("buckets", cs.buckets)
    cs.flows = state.get("flows", cs.flows)
    cs.snapshots = state.get("snapshots", cs.snapshots)

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = IngestPhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    for b in cs.buckets:
        if _kw(b.get("scope")) not in BUCKET_SCOPES:
            return refuse(f"G1: bucket scope {b.get('scope')!r} unrepresentable (no person/account)")
    for f in cs.flows:
        k = _kw(f.get("kind"))
        if (t := _trade_token(k)):
            return refuse(f"G2: flow kind contains trade token {t!r} — unrepresentable (トレードはしない)")
        if k not in FLOW_KINDS:
            return refuse(f"G2: flow kind {k!r} not a factual observation")
        if len(f.get("sources", [])) < 2:
            return refuse("G3: a flow needs ≥2 public sources")

    cs.refusal = ""
    cs.phase = IngestPhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_recorded(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    if cs.phase != IngestPhase.SCREENED.value:
        cs.refusal = "cannot record a batch that was not screened clean"
        cs.phase = IngestPhase.REFUSED.value
        return {"cell_state": cs.__dict__}
    cs.recorded = len(cs.buckets) + len(cs.flows) + len(cs.snapshots)
    cs.phase = IngestPhase.RECORDED.value
    return {"cell_state": cs.__dict__}
