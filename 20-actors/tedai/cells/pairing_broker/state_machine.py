"""Phase state machine for the tedai pairing_broker (手代) cell.

The defining tedai skill: broker access to the MEMBER's OWN paired device WITHOUT the platform ever
holding a pairing key, allow read ops freely, route every mutating op to a member signature, and
hold every :outward op (effect leaves the device) at the outward gate even WITH a member signature.
The gates are enforced here as pure, unit-tested transitions; the cell's .solve() raises until
Council activation.

Invariants enforced:
  G1 — member-principal / own-device-only: the principal AND the device owner are the member, and
       the device is physically paired; a third-party or unpaired device is refused (N3: not a RAT).
  G3 — no-server-key: the grant carries serverHeldKey=false and an encrypted-envelope REFERENCE
       only (never a plaintext pairing key); a server signature is refused (ADR-2605231525).
  G5 — read-default / mutate-gated / outward-held: :read ops are allowed at R0; :create/:update/
       :delete await a member signature; :outward ops are NOT authorizable at R0 — a member
       signature moves them only to the outward gate (Council-level), never to authorized.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# G1: only the member's own, physically paired device is operable.
MEMBER = "member"

# G3: a pairing reference must be an encrypted-envelope ref, never inline key material.
ENCREF_PREFIX = "encref:"

# G5 safety classes the broker routes on.
READ = "read"
OUTWARD = "outward"


class BrokerPhase(Enum):
    INIT = "init"
    VERIFIED_OWNER = "verified_owner"
    GRANT_BUILT = "grant_built"
    READ_ALLOWED = "read_allowed"
    AWAITING_MEMBER_SIG = "awaiting_member_sig"
    AWAITING_OUTWARD_GATE = "awaiting_outward_gate"
    AUTHORIZED = "authorized"


@dataclass
class BrokerState:
    phase: str = BrokerPhase.INIT.value
    device: str = "member-laptop"
    principal: str = MEMBER                 # G1: always the member
    device_owner: str = MEMBER              # G1: the member's OWN device
    paired: bool = True                     # G1: physical pairing ceremony completed
    server_held_key: bool = False           # G3: always false
    pairing_ref: str = "encref:com.etzhayyim.encrypted/member-laptop-pairing"
    op_safety: str = READ                   # :read / :create / :update / :delete / :outward
    member_sig: str = ""
    server_sig: str = ""                     # G3: must remain empty
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> BrokerState:
    return BrokerState(**d.get("cell_state", {}))


def transition_verify_owner(state: dict[str, Any]) -> dict[str, Any]:
    """G1: principal + device owner must both be the member, on a physically paired device."""
    cs = _state(state)
    cs.principal = state.get("principal", cs.principal)
    cs.device_owner = state.get("device_owner", cs.device_owner)
    cs.paired = state.get("paired", cs.paired)

    if cs.principal != MEMBER:
        raise ValueError("G1 violation: principal must be the member (member-principal)")
    if cs.device_owner != MEMBER:
        raise ValueError(
            "G1 violation: tedai operates only the member's OWN device; "
            "third-party-device control is refused (N3: structurally not a RAT)"
        )
    if not cs.paired:
        raise ValueError(
            "G1 violation: the device must be physically paired (consent ceremony); "
            "an unpaired device is refused"
        )

    cs.phase = BrokerPhase.VERIFIED_OWNER.value
    return {"cell_state": cs.__dict__, "next_node": "grant_built"}


def transition_build_grant(state: dict[str, Any]) -> dict[str, Any]:
    """G3: build a server-keyless grant holding only an encrypted-envelope ref — never key material."""
    cs = _state(state)
    cs.pairing_ref = state.get("pairing_ref", cs.pairing_ref)
    cs.server_held_key = False              # G3 invariant

    if not cs.pairing_ref.startswith(ENCREF_PREFIX):
        raise ValueError(
            "G3 violation: the grant may carry only an encrypted-envelope ref "
            "(com.etzhayyim.encrypted.*); a plaintext pairing key is never stored"
        )

    cs.phase = BrokerPhase.GRANT_BUILT.value
    cs.payload["grant"] = {
        "device": cs.device,
        "principal": MEMBER,
        "deviceOwner": MEMBER,
        "paired": True,
        "serverHeldKey": False,
        "pairingRef": cs.pairing_ref,
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
    """G3/G5: authorize a mutating op on a MEMBER signature only; refuse any server signature.
    An :outward op is never authorized here — a member signature moves it only to the outward gate."""
    cs = _state(state)
    cs.member_sig = state.get("member_sig", "")
    cs.server_sig = state.get("server_sig", "")

    if cs.op_safety == READ:
        raise ValueError("G5 violation: authorize_mutate reached for a read op")
    if cs.server_sig:
        raise ValueError("G3 violation: server signature refused (no-server-key, ADR-2605231525)")
    if not cs.member_sig:
        raise ValueError("G5 violation: member signature required to authorize a mutating op")

    if cs.op_safety == OUTWARD:
        # G5: the effect leaves the device; the member signature is necessary but NOT sufficient.
        cs.phase = BrokerPhase.AWAITING_OUTWARD_GATE.value
        cs.payload["mutateGate"] = "awaiting-member-sig-and-outward-gate"
        cs.payload["outwardGate"] = {
            "memberSigned": True,
            "authorized": False,
            "requires": "council-outward-gate",
        }
        return {"cell_state": cs.__dict__, "next_node": "end"}

    cs.phase = BrokerPhase.AUTHORIZED.value
    cs.payload["mutateGate"] = "authorized"
    cs.payload["authorization"] = {
        "authorizedBy": MEMBER,
        "serverSigned": False,
        "actuationGated": True,   # G6: live input injection still requires operator + Council Lv6+
    }
    return {"cell_state": cs.__dict__, "next_node": "end"}
