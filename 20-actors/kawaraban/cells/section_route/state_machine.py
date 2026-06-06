"""Phase state machine for kawaraban section_route — G2/G11 gate.

Routes an article into its 面 (section) and attaches its :news.mention edges. ROUTED only if:
  the 面 is a real news-media section (front/politics/economy/international/society/culture/
    science/sports/local/opinion);
  G2 — any provided rank signals are a subset of the public-good allowlist (paid-placement/
    sponsored/engagement/dwell-time are unrepresentable);
  G11 — mention roles are observational (subject/source/mentioned/affected/responding),
    never an accusation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

MEN = ("front", "politics", "economy", "international", "society",
       "culture", "science", "sports", "local", "opinion")
ALLOWED_RANK = ("recency", "section-fit", "source-diversity", "actor-relevance", "geo-proximity")
ROLES = ("subject", "source", "mentioned", "affected", "responding")


class Phase(Enum):
    INIT = "init"
    ROUTED = "routed"
    REFUSED = "refused"


@dataclass
class State:
    phase: str = Phase.INIT.value
    article_id: str = ""
    men: str = "front"
    rank_signals: list = field(default_factory=lambda: ["recency", "section-fit"])
    mentions: list = field(default_factory=list)  # [{target, targetKind, role}]
    refusal: str = ""
    payload: dict = None


def _norm(v: str | None) -> str:
    return (v or "").lstrip(":")


def route(state: dict[str, Any]) -> dict[str, Any]:
    cs = State(**state.get("cell_state", {}))
    cs.article_id = state.get("article_id", cs.article_id)
    cs.men = _norm(state.get("men", cs.men))
    cs.rank_signals = [_norm(s) for s in state.get("rank_signals", cs.rank_signals)]
    cs.mentions = list(state.get("mentions", cs.mentions))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal, cs.phase = msg, Phase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if cs.men not in MEN:
        return refuse(f"unknown 面 {cs.men!r}; not a real news-media section")
    for s in cs.rank_signals:
        if s not in ALLOWED_RANK:
            return refuse(f"G2: rank signal {s!r} not public-good; paid/engagement ranking unrepresentable")
    for m in cs.mentions:
        role = _norm(m.get("role"))
        if role not in ROLES:
            return refuse(f"G11: mention role {role!r} is not observational (subject/source/mentioned/affected/responding)")

    cs.payload = {"articleId": cs.article_id, "men": cs.men,
                  "rankSignals": cs.rank_signals, "mentionCount": len(cs.mentions)}
    cs.refusal, cs.phase = "", Phase.ROUTED.value
    return {"cell_state": cs.__dict__}
