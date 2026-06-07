"""Phase state machine for the 潮目 (shionome) social_post cell.

Drafts a DRY-RUN post and REFUSES if the body carries a trade/advisory token (G2, トレードは
しない) or fewer than 2 sources (G3). status is dry-run only (G8). Self-contained.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

TRADE_TOKENS = ("buy", "sell", "long", "short", "overweight", "underweight", "recommend",
                "target price", "target-price", "推奨", "買い", "売り", "目標株価", "空売り")


class PostPhase(Enum):
    INIT = "init"
    DRAFTED = "drafted"
    REFUSED = "refused"


@dataclass
class PostState:
    phase: str = PostPhase.INIT.value
    body: str = ""
    sources: list = field(default_factory=list)
    status: str = ""
    refusal: str = ""


def _trade_token(text: str) -> str:
    blob = str(text or "").lower()
    for t in TRADE_TOKENS:
        if t in blob:
            return t
    return ""


def transition_to_drafted(state: dict[str, Any]) -> dict[str, Any]:
    cs = PostState(**state.get("cell_state", {}))
    cs.body = state.get("body", cs.body)
    cs.sources = state.get("sources", cs.sources)

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = PostPhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if (t := _trade_token(cs.body)):
        return refuse(f"G2: post body contains trade token {t!r} — refused (トレードはしない)")
    if len([s for s in cs.sources if str(s).strip()]) < 2:
        return refuse("G3: a post needs ≥2 public sources")
    cs.refusal = ""
    cs.status = "dry-run"   # G8 — dry-run only at R0
    cs.phase = PostPhase.DRAFTED.value
    return {"cell_state": cs.__dict__}
