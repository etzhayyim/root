"""Phase state machine for the 系図 (keizu) social_post cell — the G2/G5/G7/G8 publication membrane.

A finding enters; it is DRAFTED into a dry-run post ONLY if:
  G3 — ≥2 public-source citations are present;
  G5 — the post is a mirror (isMirror), opening with the accountability disclaimer;
  G7 — server-held-key is false (the member signs, the server never does);
  G8 — the status is dry-run (a 'published' request REFUSES — live needs Council Lv6+ + operator).
Self-contained.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

DISCLAIMER = "【観測ミラー / accountability map — non-adjudicating】"


class PostPhase(Enum):
    INIT = "init"
    DRAFTED = "drafted"
    REFUSED = "refused"


@dataclass
class PostState:
    phase: str = PostPhase.INIT.value
    subject: str = ""
    sources: list = field(default_factory=list)
    requested_status: str = "dry-run"
    server_held_key: bool = False
    payload: dict = field(default_factory=dict)
    refusal: str = ""


def _state(d: dict[str, Any]) -> PostState:
    return PostState(**d.get("cell_state", {}))


def transition_to_drafted(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.subject = state.get("subject", cs.subject)
    cs.sources = state.get("sources", cs.sources)
    cs.requested_status = str(state.get("requested_status", cs.requested_status)).lstrip(":")
    cs.server_held_key = bool(state.get("server_held_key", cs.server_held_key))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal = msg
        cs.phase = PostPhase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if len(cs.sources) < 2:
        return refuse("G3: a post needs ≥2 public-source citations")
    if cs.server_held_key:
        return refuse("G7/no-server-key: server-held-key must be false (ADR-2605231525)")
    if cs.requested_status != "dry-run":
        return refuse("G8: only dry-run posts at R0; live publication is Council Lv6+ + operator gated")

    cs.payload = {
        ":post/subject": cs.subject,
        ":post/body": f"{DISCLAIMER} {cs.subject}",
        ":post/status": ":dry-run",
        ":post/is-mirror": True,
        ":post/non-adjudicating-notice": True,
        ":post/server-held-key": False,
        ":post/sources": cs.sources,
    }
    cs.refusal = ""
    cs.phase = PostPhase.DRAFTED.value
    return {"cell_state": cs.__dict__}
