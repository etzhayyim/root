"""Phase state machine for the yadori reservation (宿り) cell.

The defining yadori skill: turn an available domain into an *unsigned, member-principal*
reservation intent, then authorize it with a member signature only. The gates are enforced
here as pure, unit-tested transitions; the cell's .solve() raises until Council activation.

Invariants enforced:
  G2 — no-fiat-inflow / member-principal: the payer is the member (okaimono assisted-checkout),
       never the religious-corp / a fiat processor. yadori is never the buyer-of-record.
  G3 — cloudflare-registrar-default: Cloudflare is the default; any external registrar
       (e.g. GoDaddy) requires an explicit Council approval flag.
  G5 — no-server-key: the reservation intent is serverHeldKey=false; authorization requires a
       member signature and REFUSES any server signature.
  G6 — no-squatting: the requested name must clear a held-trademark/confusable screen, must not
       be flagged for speculation/resale/parking, and must pass the Charter-Rider scan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# G3: registrars yadori may select without a Council approval flag.
DEFAULT_REGISTRAR = "cloudflare"
COUNCIL_GATED_REGISTRARS = ("godaddy", "namecheap", "squarespace", "google", "porkbun")

# G2: funding sources. Only member-principal (okaimono assisted-checkout) is allowed.
ALLOWED_FUNDING = ("member-okaimono",)
PROHIBITED_FUNDING = ("org-fiat", "org-treasury", "stripe", "paypal", "card-on-file")

# G6: a :representative held-trademark / confusable screen list. Bounded seed (G8).
BLOCKED_NAMES = ("google", "amazon", "microsoft", "apple", "godaddy", "cloudflare", "meta")


class ReservationPhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    QUOTED = "quoted"
    INTENT_BUILT = "intent_built"
    AUTHORIZED = "authorized"


@dataclass
class ReservationState:
    phase: str = ReservationPhase.INIT.value
    fqdn: str = "example-newproject.org"
    sld: str = "example-newproject"           # second-level label (the part being claimed)
    registrar: str = DEFAULT_REGISTRAR
    council_approved_registrar: bool = False
    funding_source: str = "member-okaimono"
    payer: str = "member"                      # G2: always the member, never the org
    server_held_key: bool = False              # G5: always false
    member_sig: str = ""
    server_sig: str = ""                        # G5: must remain empty
    charter_clean: bool = True
    speculative: bool = False                   # G6: parking / resale / drop-catch intent
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> ReservationState:
    return ReservationState(**d.get("cell_state", {}))


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    """G6: no-squatting eligibility screen."""
    cs = _state(state)
    cs.sld = state.get("sld", cs.sld)
    cs.speculative = bool(state.get("speculative", False))
    cs.charter_clean = bool(state.get("charter_clean", True))

    if cs.sld.lower() in BLOCKED_NAMES:
        raise ValueError(f"G6 violation: '{cs.sld}' fails held-trademark/confusable screen")
    if cs.speculative:
        raise ValueError("G6 violation: speculation / resale / parking intent is prohibited (N1/N2)")
    if not cs.charter_clean:
        raise ValueError("G6 violation: name fails Charter-Rider §2(a)-(h) scan")

    cs.phase = ReservationPhase.SCREENED.value
    return {"cell_state": cs.__dict__, "next_node": "quote"}


def transition_to_quoted(state: dict[str, Any]) -> dict[str, Any]:
    """G3: registrar-default. G2: funding source must be member-principal."""
    cs = _state(state)
    cs.registrar = state.get("registrar", cs.registrar)
    cs.council_approved_registrar = bool(state.get("council_approved_registrar", False))
    cs.funding_source = state.get("funding_source", cs.funding_source)

    if cs.registrar in COUNCIL_GATED_REGISTRARS and not cs.council_approved_registrar:
        raise ValueError(
            f"G3 violation: registrar '{cs.registrar}' is Council-gated; "
            f"default is '{DEFAULT_REGISTRAR}' (at-cost, no markup)"
        )
    if cs.funding_source in PROHIBITED_FUNDING:
        raise ValueError(
            f"G2 violation: funding '{cs.funding_source}' forbidden; "
            "acquisition is member-principal (okaimono assisted-checkout)"
        )
    if cs.funding_source not in ALLOWED_FUNDING:
        raise ValueError(f"G2 violation: unknown funding '{cs.funding_source}'")

    cs.phase = ReservationPhase.QUOTED.value
    return {"cell_state": cs.__dict__, "next_node": "intent_built"}


def transition_to_intent_built(state: dict[str, Any]) -> dict[str, Any]:
    """G2/G5: unsigned, member-principal intent; serverHeldKey=false."""
    cs = _state(state)
    cs.payer = "member"               # G2 invariant — yadori is never the buyer
    cs.server_held_key = False        # G5 invariant
    cs.phase = ReservationPhase.INTENT_BUILT.value
    cs.payload["reservation_intent"] = {
        "fqdn": cs.fqdn,
        "registrar": cs.registrar,
        "registrantPrincipal": "member",
        "payer": "member",
        "fundingSource": cs.funding_source,
        "serverHeldKey": False,
        "signed": False,
    }
    return {"cell_state": cs.__dict__, "next_node": "authorized"}


def transition_to_authorized(state: dict[str, Any]) -> dict[str, Any]:
    """G5: authorize on a MEMBER signature only; refuse any server signature."""
    cs = _state(state)
    cs.member_sig = state.get("member_sig", "")
    cs.server_sig = state.get("server_sig", "")

    if cs.server_sig:
        raise ValueError("G5 violation: server signature refused (no-server-key, ADR-2605231525)")
    if not cs.member_sig:
        raise ValueError("G5 violation: member signature required to authorize a reservation")

    cs.phase = ReservationPhase.AUTHORIZED.value
    intent = cs.payload.get("reservation_intent", {})
    intent["signed"] = True
    intent["signedBy"] = "member"
    cs.payload["reservation_intent"] = intent
    cs.payload["authorization"] = {
        "authorizedBy": "member",
        "serverSigned": False,
        "outwardGated": True,   # G7: live registrar mutate still requires operator + Council
    }
    return {"cell_state": cs.__dict__, "next_node": "end"}
