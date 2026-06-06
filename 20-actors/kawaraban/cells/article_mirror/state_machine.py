"""Phase state machine for kawaraban article_mirror — G1/G4/G9 gate.

Mirrors a REAL article as an observation. MIRRORED only if:
  G11 — kind == 'mirror' with outlet + url (link-out);
  G4  — no full_text; excerpt ≤ 280 chars (bounded fair-use);
  G1  — no verdict / truth_rating (kawaraban never rules truth);
  G9  — no speak_as (never posts AS the outlet).
An illegal article is REFUSED, never coerced.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Phase(Enum):
    INIT = "init"
    MIRRORED = "mirrored"
    REFUSED = "refused"


@dataclass
class State:
    phase: str = Phase.INIT.value
    article_id: str = ""
    section: str = ""
    outlet: str = ""
    url: str = ""
    headline: str = ""
    excerpt: str = ""
    verdict: bool = False
    truth_rating: int = 0
    full_text: bool = False
    speak_as: bool = False
    refusal: str = ""
    payload: dict = None


def mirror(state: dict[str, Any]) -> dict[str, Any]:
    cs = State(**state.get("cell_state", {}))
    for f in ("article_id", "section", "outlet", "url", "headline", "excerpt"):
        setattr(cs, f, state.get(f, getattr(cs, f)))
    cs.verdict = bool(state.get("verdict", cs.verdict))
    cs.truth_rating = int(state.get("truth_rating", cs.truth_rating))
    cs.full_text = bool(state.get("full_text", cs.full_text))
    cs.speak_as = bool(state.get("speak_as", cs.speak_as))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal, cs.phase = msg, Phase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if cs.verdict or cs.truth_rating:
        return refuse("G1: a mirrored article carries no verdict/truth-rating (ake/danjo boundary)")
    if cs.full_text:
        return refuse("G4: full body is unrepresentable; headline + link + excerpt only")
    if cs.speak_as:
        return refuse("G9: never post AS the outlet (mirror, not impersonation)")
    if not cs.outlet or not cs.url:
        return refuse("G4/G11: a :mirror article needs outlet + canonical url (link-out)")
    if len(cs.excerpt) > 280:
        return refuse(f"G4: excerpt {len(cs.excerpt)} chars > 280 (fair-use bound)")

    cs.payload = {"articleId": cs.article_id, "kind": "mirror", "section": cs.section,
                  "outlet": cs.outlet, "url": cs.url, "headline": cs.headline,
                  "excerpt": cs.excerpt, "verdict": False, "fullText": False, "speakAs": False}
    cs.refusal, cs.phase = "", Phase.MIRRORED.value
    return {"cell_state": cs.__dict__}
