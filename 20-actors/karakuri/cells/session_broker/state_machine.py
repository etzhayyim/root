"""Phase state machine for the karakuri session_broker (絡繰) cell.

The defining karakuri skill: broker access to the MEMBER's OWN service session WITHOUT the platform
ever holding secret material, allow read ops freely, and route every mutating op to a member
signature. The gates are enforced here as pure, unit-tested transitions; the cell's .solve() raises
until Council activation.

Invariants enforced:
  G1 — member-principal / own-account-only: the principal AND the account owner are the member;
       a third-party account is refused. karakuri is never operating someone else's account.
  G3 — no-server-key: the grant carries serverHeldKey=false and an encrypted-envelope REFERENCE
       only (never plaintext credentials); a server signature is refused (ADR-2605231525).
  G5 — read-default / mutate-gated: :read ops are allowed at R0; any :create/:update/:delete op
       awaits a member signature before it can be authorized.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# G1: only the member's own account is operable.
MEMBER = "member"

# G3: a secret reference must be an encrypted-envelope ref, never inline plaintext.
ENCREF_PREFIX = "encref:"

# G5: read ops are allowed at R0; everything else awaits a member signature.
READ = "read"


class BrokerPhase(Enum):
    INIT = "init"
    VERIFIED_OWNER = "verified_owner"
    GRANT_BUILT = "grant_built"
    READ_ALLOWED = "read_allowed"
    AWAITING_MEMBER_SIG = "awaiting_member_sig"
    AUTHORIZED = "authorized"


@dataclass
class BrokerState:
    phase: str = BrokerPhase.INIT.value
    service: str = "squarespace"
    principal: str = MEMBER                 # G1: always the member
    account_owner: str = MEMBER             # G1: the member's OWN account
    server_held_key: bool = False           # G3: always false
    secret_ref: str = "encref:com.etzhayyim.encrypted/squarespace-session"
    op_safety: str = READ                   # :read / :create / :update / :delete
    member_sig: str = ""
    server_sig: str = ""                     # G3: must remain empty
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> BrokerState:
    return BrokerState(**d.get("cell_state", {}))


def transition_verify_owner(state: dict[str, Any]) -> dict[str, Any]:
    """G1: the principal and the account owner must both be the member; refuse a third-party account."""
    cs = _state(state)
    cs.principal = state.get("principal", cs.principal)
    cs.account_owner = state.get("account_owner", cs.account_owner)

    if cs.principal != MEMBER:
        raise ValueError("G1 violation: principal must be the member (member-principal)")
    if cs.account_owner != MEMBER:
        raise ValueError(
            "G1 violation: karakuri drives only the member's OWN account; "
            "third-party-account access is refused (N1 no scraping/surveillance)"
        )

    cs.phase = BrokerPhase.VERIFIED_OWNER.value
    return {"cell_state": cs.__dict__, "next_node": "grant_built"}


def transition_build_grant(state: dict[str, Any]) -> dict[str, Any]:
    """G3: build a server-keyless grant holding only an encrypted-envelope ref — never plaintext."""
    cs = _state(state)
    cs.secret_ref = state.get("secret_ref", cs.secret_ref)
    cs.server_held_key = False              # G3 invariant

    if not cs.secret_ref.startswith(ENCREF_PREFIX):
        raise ValueError(
            "G3 violation: the grant may carry only an encrypted-envelope ref "
            "(com.etzhayyim.encrypted.*); plaintext credentials are never stored"
        )

    cs.phase = BrokerPhase.GRANT_BUILT.value
    cs.payload["grant"] = {
        "service": cs.service,
        "principal": MEMBER,
        "accountOwner": MEMBER,
        "serverHeldKey": False,
        "secretRef": cs.secret_ref,
    }
    # G5: route based on the op's safety class.
    nxt = "read_allowed" if cs.op_safety == READ else "awaiting_member_sig"
    return {"cell_state": cs.__dict__, "next_node": nxt}


def transition_read_allowed(state: dict[str, Any]) -> dict[str, Any]:
    """G5: a :read op needs no signature; it is allowed at R0 (still dry-run / G6 downstream)."""
    cs = _state(state)
    if cs.op_safety != READ:
        raise ValueError("G5 violation: read_allowed reached for a mutating op")
    cs.phase = BrokerPhase.READ_ALLOWED.value
    cs.payload["mutateGate"] = "read-allowed"
    return {"cell_state": cs.__dict__, "next_node": "end"}


def transition_authorize_mutate(state: dict[str, Any]) -> dict[str, Any]:
    """G3/G5: authorize a mutating op on a MEMBER signature only; refuse any server signature."""
    cs = _state(state)
    cs.member_sig = state.get("member_sig", "")
    cs.server_sig = state.get("server_sig", "")

    if cs.op_safety == READ:
        raise ValueError("G5 violation: authorize_mutate reached for a read op")
    if cs.server_sig:
        raise ValueError("G3 violation: server signature refused (no-server-key, ADR-2605231525)")
    if not cs.member_sig:
        raise ValueError("G5 violation: member signature required to authorize a mutating op")

    cs.phase = BrokerPhase.AUTHORIZED.value
    cs.payload["mutateGate"] = "authorized"
    cs.payload["authorization"] = {
        "authorizedBy": MEMBER,
        "serverSigned": False,
        "outwardGated": True,   # G6: live execution still requires operator + Council Lv6+
    }
    return {"cell_state": cs.__dict__, "next_node": "end"}
