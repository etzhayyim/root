"""Phase state machine for the nusa cultivation_license_plan (幣) cell.

Turns a low-THC fibre cultivar into an *unsigned, member-principal* 栽培者免許 design,
then authorizes it with a member signature only. Mirrors the yadori reservation pattern
(member-principal acquisition) for the cultivation-licence domain.

Invariants enforced:
  G1 — cultivar must be fibre/low-THC (re-screened here; defence in depth).
  G4 — member-principal / no-fiat-inflow: licensee-of-record + payer = the member
       (okaimono assisted-checkout); funding is member-okaimono, never the org treasury
       or a fiat processor. nusa is never the licensee/funder.
  G5 — no-server-key: serverHeldKey=false; authorization requires a member signature and
       REFUSES any server signature.
  G8 — outward-gated: outwardGated=true; live licence filing requires operator + Council Lv6+.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ALLOWED_THC_CLASSES = ("fiber", "low-thc")
ALLOWED_FUNDING = ("member-okaimono",)
PROHIBITED_FUNDING = ("org-treasury", "org-fiat", "stripe", "paypal", "card-on-file")
ALLOWED_PURPOSE = ("ritual-fiber", "industrial-fiber")


class LicensePhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    PLAN_BUILT = "plan_built"
    AUTHORIZED = "authorized"


@dataclass
class LicenseState:
    phase: str = LicensePhase.INIT.value
    license_id: str = ""
    cultivar: str = ""
    thc_class: str = "fiber"
    purpose: str = "ritual-fiber"
    licensee_principal: str = "member"   # G4: always the member
    funding_source: str = "member-okaimono"
    server_held_key: bool = False        # G5: always false
    outward_gated: bool = True           # G8: always true
    legal_basis: str = "大麻草の栽培の規制に関する法律 (栽培者免許; 要 primary-source 引用)"
    member_sig: str = ""
    server_sig: str = ""                  # G5: must remain empty
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> LicenseState:
    return LicenseState(**d.get("cell_state", {}))


def _norm(v: str | None) -> str:
    return (v or "").lstrip(":")


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    """G1: re-screen the cultivar's THC class (defence in depth)."""
    cs = _state(state)
    cs.cultivar = state.get("cultivar", cs.cultivar)
    cls = _norm(state.get("thc_class", cs.thc_class))
    if cls not in ALLOWED_THC_CLASSES:
        raise ValueError(
            f"G1 violation: cultivar {cs.cultivar!r} thc-class {cls!r} not in {ALLOWED_THC_CLASSES}; "
            f"no licence design for non-fibre/low-THC cultivars."
        )
    cs.thc_class = cls
    purpose = _norm(state.get("purpose", cs.purpose))
    if purpose not in ALLOWED_PURPOSE:
        raise ValueError(f"purpose {purpose!r} not in {ALLOWED_PURPOSE}")
    cs.purpose = purpose
    cs.phase = LicensePhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_plan_built(state: dict[str, Any]) -> dict[str, Any]:
    """G4/G5/G8: build the unsigned member-principal licence design."""
    cs = _state(state)
    funding = _norm(state.get("funding_source", cs.funding_source))
    if funding in PROHIBITED_FUNDING or funding not in ALLOWED_FUNDING:
        raise ValueError(
            f"G4 violation: funding_source {funding!r} must be member-okaimono; "
            f"licence fees never from org treasury / fiat processor; nusa is never the funder."
        )
    cs.funding_source = funding
    # G4: licensee is always the member; G5: no server key; G8: outward-gated.
    cs.licensee_principal = "member"
    cs.server_held_key = False
    cs.outward_gated = True
    cs.license_id = state.get("license_id", cs.license_id) or f"license.{cs.cultivar}"
    cs.phase = LicensePhase.PLAN_BUILT.value
    return {"cell_state": cs.__dict__}


def transition_to_authorized(state: dict[str, Any]) -> dict[str, Any]:
    """G5: authorize with a MEMBER signature only; refuse any server signature."""
    cs = _state(state)
    server_sig = state.get("server_sig", cs.server_sig)
    if server_sig:
        raise ValueError("G5 violation: server signature refused; the member signs the licence plan")
    member_sig = state.get("member_sig", cs.member_sig)
    if not member_sig:
        raise ValueError("authorization requires a member signature (G5)")
    cs.member_sig = member_sig
    cs.payload = {
        "licenseId": cs.license_id,
        "cultivar": cs.cultivar,
        "purpose": cs.purpose,
        "licenseePrincipal": "member",
        "fundingSource": cs.funding_source,
        "serverHeldKey": False,
        "outwardGated": True,
        "legalBasis": cs.legal_basis,
        "signed": True,
        "signedBy": "member",
    }
    cs.phase = LicensePhase.AUTHORIZED.value
    return {"cell_state": cs.__dict__}
