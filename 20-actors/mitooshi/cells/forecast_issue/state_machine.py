"""Phase state machine for the mitooshi forecast_issue (見通し) cell.

The G1/G2 structural-invariant gate. A forecast is ISSUED into the Datom log ONLY if:
  G1 — point_asserted is False (a deterministic single-future is unrepresentable, 非終末論);
  G2 — use ∈ {resilience, planning, nowcast, early-warning, research} (a forecast made to
       place a trade / bet / hold a position is unrepresentable — mitooshi never speculates);
  well-formed distribution — gaussian needs sd > 0, quantile/categorical need a non-empty
       map; every forecast carries info-as-of (the leak boundary G5 will later enforce).

REFUSAL gate (like precursor_safety): an illegal forecast is refused, never coerced.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ALLOWED_USE = ("resilience", "planning", "nowcast", "early-warning", "research")
DIST_KINDS = ("gaussian", "quantile", "categorical", "ensemble")


class IssuePhase(Enum):
    INIT = "init"
    ISSUED = "issued"
    REFUSED = "refused"


@dataclass
class IssueState:
    phase: str = IssuePhase.INIT.value
    forecast_id: str = ""
    series_id: str = ""
    dist_kind: str = "gaussian"
    use: str = "resilience"
    point_asserted: bool = False
    info_as_of: int = 0
    horizon: int = 1
    mean: float = 0.0
    sd: float = 1.0
    quantiles: dict = field(default_factory=dict)
    probs: dict = field(default_factory=dict)
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> IssueState:
    return IssueState(**d.get("cell_state", {}))


def _norm(v: str | None) -> str:
    return (v or "").lstrip(":")


def issue(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.forecast_id = state.get("forecast_id", cs.forecast_id)
    cs.series_id = state.get("series_id", cs.series_id)
    cs.dist_kind = _norm(state.get("dist_kind", cs.dist_kind))
    cs.use = _norm(state.get("use", cs.use))
    cs.point_asserted = bool(state.get("point_asserted", cs.point_asserted))
    cs.info_as_of = int(state.get("info_as_of", cs.info_as_of))
    cs.horizon = int(state.get("horizon", cs.horizon))
    cs.mean = float(state.get("mean", cs.mean))
    cs.sd = float(state.get("sd", cs.sd))
    cs.quantiles = dict(state.get("quantiles", cs.quantiles))
    cs.probs = dict(state.get("probs", cs.probs))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = IssuePhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    # G1 — distribution-only.
    if cs.point_asserted:
        return refuse(f"G1: forecast {cs.forecast_id!r} asserts a deterministic point; unrepresentable (非終末論)")
    # G2 — non-speculative use.
    if cs.use not in ALLOWED_USE:
        return refuse(f"G2: use {cs.use!r} not in the non-speculative set {ALLOWED_USE}; mitooshi never trades")
    if cs.dist_kind not in DIST_KINDS:
        return refuse(f"unknown dist-kind {cs.dist_kind!r}")
    # well-formedness per distribution kind
    if cs.dist_kind == "gaussian" and not cs.sd > 0:
        return refuse(f"gaussian forecast {cs.forecast_id!r} needs sd > 0 (a degenerate spike is a point assertion)")
    if cs.dist_kind == "quantile" and not cs.quantiles:
        return refuse(f"quantile forecast {cs.forecast_id!r} has no quantiles")
    if cs.dist_kind == "categorical":
        if not cs.probs:
            return refuse(f"categorical forecast {cs.forecast_id!r} has no class probabilities")
        s = sum(cs.probs.values())
        if abs(s - 1.0) > 1e-6:
            return refuse(f"categorical forecast {cs.forecast_id!r} probabilities sum to {s:.4f}, not 1")

    cs.payload = {
        "forecastId": cs.forecast_id,
        "seriesId": cs.series_id,
        "distKind": cs.dist_kind,
        "use": cs.use,
        "pointAsserted": False,
        "infoAsOf": cs.info_as_of,
        "targetAt": cs.info_as_of + cs.horizon,
        "horizon": cs.horizon,
        "issued": True,
    }
    cs.refusal = ""
    cs.phase = IssuePhase.ISSUED.value
    return {"cell_state": cs.__dict__}
