"""Phase state machine for the 系図 (keizu) ingest cell — the G1/G2/G3 intake membrane.

A public-source batch enters. Each record is SCREENED against the closed structural vocab:
  G1 — a node scope must be a public seat/organ (no private person);
  G2 — a relation/money kind must be factual (no verdict token);
  G3 — a relation/money flow must carry ≥2 public-source citations.
A clean batch is RECORDED (counts only at R0); any violation REFUSES the whole batch.
Self-contained (no methods import) so the cell suite runs standalone.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

NODE_SCOPES = ("public-office", "public-org", "public-committee", "public-role")
REL_KINDS = ("committee-membership", "appointment", "advisory-role", "co-membership",
             "revolving-door", "funding-tie", "statement-attribution", "procurement-award")
MONEY_KINDS = ("procurement-award", "subsidy", "grant", "political-donation", "budget-outlay")
VERDICT = ("corruption", "bribe", "kickback", "collusion", "guilt", "crime", "不正", "違法", "汚職", "賄賂")


class IngestPhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    RECORDED = "recorded"
    REFUSED = "refused"


@dataclass
class IngestState:
    phase: str = IngestPhase.INIT.value
    nodes: list = field(default_factory=list)
    rels: list = field(default_factory=list)
    money: list = field(default_factory=list)
    recorded: int = 0
    refusal: str = ""


def _state(d: dict[str, Any]) -> IngestState:
    return IngestState(**d.get("cell_state", {}))


def _kw(v: Any) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.nodes = state.get("nodes", cs.nodes)
    cs.rels = state.get("rels", cs.rels)
    cs.money = state.get("money", cs.money)

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = IngestPhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    for n in cs.nodes:
        if _kw(n.get("scope")) not in NODE_SCOPES:
            return refuse(f"G1: node scope {n.get('scope')!r} unrepresentable (no private person)")
    for r in cs.rels:
        k = _kw(r.get("kind"))
        if k in VERDICT:
            return refuse(f"G2: relation kind {k!r} is a verdict — unrepresentable")
        if k not in REL_KINDS:
            return refuse(f"G2: relation kind {k!r} not factual")
        if len(r.get("sources", [])) < 2:
            return refuse("G3: a relation needs ≥2 public sources")
    for m in cs.money:
        k = _kw(m.get("kind"))
        if k in VERDICT:
            return refuse(f"G2: money kind {k!r} is a verdict — unrepresentable")
        if k not in MONEY_KINDS:
            return refuse(f"G2: money kind {k!r} not factual")
        if len(m.get("sources", [])) < 2:
            return refuse("G3: a money flow needs ≥2 public sources")

    cs.refusal = ""
    cs.phase = IngestPhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_recorded(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    if cs.phase != IngestPhase.SCREENED.value:
        cs.refusal = "cannot record a batch that was not screened clean"
        cs.phase = IngestPhase.REFUSED.value
        return {"cell_state": cs.__dict__}
    cs.recorded = len(cs.nodes) + len(cs.rels) + len(cs.money)
    cs.phase = IngestPhase.RECORDED.value
    return {"cell_state": cs.__dict__}
