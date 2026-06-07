"""Phase state machine for kawaraban actor_project — THE MEDIUM (G7/G9/G11 gate).

Projects a first-party etzhayyim actor's Datom as-of event into the matching 面 as
:article/kind 'actor-event' (feed-post membrane reuse). This is the connective core — it is
how actor news enters the medium and how actors get wired to one another. PROJECTED only if:
  G11 — kind == 'actor-event' with source_actor + source_tid (provenance to the canonical event);
  G7  — member-signed: server_held_key is False (the server NEVER signs a projection);
  G9  — no speak_as (kawaraban observes the actor's event, never speaks AS the actor).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Phase(Enum):
    INIT = "init"
    PROJECTED = "projected"
    REFUSED = "refused"


@dataclass
class State:
    phase: str = Phase.INIT.value
    article_id: str = ""
    source_actor: str = ""
    source_tid: str = ""
    men: str = "front"
    headline: str = ""
    member_signed: bool = False
    server_held_key: bool = False
    speak_as: bool = False
    mentions: list = field(default_factory=list)
    refusal: str = ""
    payload: dict = None


def project(state: dict[str, Any]) -> dict[str, Any]:
    cs = State(**state.get("cell_state", {}))
    for f in ("article_id", "source_actor", "source_tid", "men", "headline"):
        setattr(cs, f, state.get(f, getattr(cs, f)))
    cs.member_signed = bool(state.get("member_signed", cs.member_signed))
    cs.server_held_key = bool(state.get("server_held_key", cs.server_held_key))
    cs.speak_as = bool(state.get("speak_as", cs.speak_as))
    cs.mentions = list(state.get("mentions", cs.mentions))

    def refuse(msg: str) -> dict[str, Any]:
        cs.refusal, cs.phase = msg, Phase.REFUSED.value
        return {"cell_state": cs.__dict__}

    if not cs.source_actor or not cs.source_tid:
        return refuse("G11: an :actor-event needs source_actor + source_tid (provenance to the Datom)")
    if cs.server_held_key:
        return refuse("G7: server never signs a projection; member signature required (no-server-key)")
    if not cs.member_signed:
        return refuse("G7: projection not member-signed; refused (no-server-key)")
    if cs.speak_as:
        return refuse("G9: kawaraban observes the actor's event, never speaks AS the actor")

    cs.payload = {"articleId": cs.article_id, "kind": "actor-event", "men": cs.men,
                  "sourceActor": cs.source_actor, "sourceTid": cs.source_tid,
                  "headline": cs.headline, "serverHeldKey": False, "speakAs": False,
                  "wires": len(cs.mentions)}
    cs.refusal, cs.phase = "", Phase.PROJECTED.value
    return {"cell_state": cs.__dict__}
