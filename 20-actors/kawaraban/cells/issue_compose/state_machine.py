"""Phase state machine for kawaraban issue_compose — G2/G7/G8/G10 gate.

Composes an EDITION (front-面 digest). COMPOSED only if:
  G2  — rank signals ⊆ public-good allowlist (paid/engagement ranking unrepresentable);
  G10 — final is False (no last edition; 非終末論);
  G7  — server_held_key is False (server never signs an edition).
PUBLISHED stays False unless member-signed AND operator-gated (G7/G8) — at R0 composition
yields an unsigned, unpublished, non-final edition.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ALLOWED_RANK = ("recency", "section-fit", "source-diversity", "actor-relevance", "geo-proximity")


class Phase(Enum):
    INIT = "init"
    COMPOSED = "composed"
    REFUSED = "refused"


@dataclass
class State:
    phase: str = Phase.INIT.value
    issue_id: str = ""
    rank_signals: list = field(default_factory=lambda: ["recency", "source-diversity", "actor-relevance"])
    lead_ids: list = field(default_factory=list)
    final: bool = False
    member_signed: bool = False
    operator_gated: bool = False
    server_held_key: bool = False
    published: bool = False
    refusal: str = ""
    payload: dict = None


def _norm(v: str | None) -> str:
    return (v or "").lstrip(":")


def compose(state: dict[str, Any]) -> dict[str, Any]:
    cs = State(**state.get("cell_state", {}))
    cs.issue_id = state.get("issue_id", cs.issue_id)
    cs.rank_signals = [_norm(s) for s in state.get("rank_signals", cs.rank_signals)]
    cs.lead_ids = list(state.get("lead_ids", cs.lead_ids))
    cs.final = bool(state.get("final", cs.final))
    cs.member_signed = bool(state.get("member_signed", cs.member_signed))
    cs.operator_gated = bool(state.get("operator_gated", cs.operator_gated))
    cs.server_held_key = bool(state.get("server_held_key", cs.server_held_key))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal, cs.phase = msg, Phase.REFUSED.value
        return {"cell_state": cs.__dict__}

    for s in cs.rank_signals:
        if s not in ALLOWED_RANK:
            return refuse(f"G2: rank signal {s!r} not public-good; paid/engagement ranking unrepresentable")
    if cs.final:
        return refuse("G10: an edition is never final (非終末論)")
    if cs.server_held_key:
        return refuse("G7: server never signs an edition (no-server-key)")

    # G7/G8 — publication requires member signature AND operator gate; otherwise composed-but-unpublished.
    cs.published = bool(cs.member_signed and cs.operator_gated)
    cs.payload = {"issueId": cs.issue_id, "rankSignals": cs.rank_signals,
                  "leadCount": len(cs.lead_ids), "final": False, "serverHeldKey": False,
                  "published": cs.published}
    cs.refusal, cs.phase = "", Phase.COMPOSED.value
    return {"cell_state": cs.__dict__}
