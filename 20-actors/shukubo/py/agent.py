#!/usr/bin/env python3
"""shukubo 宿坊 — pilgrim-lodging commons langgraph actor (kotoba WASM cell).

ADR-2606071600. The Airbnb/Hotels inversion. Three concentric rings (commons → internal →
external), mirroring okaimono's shape for lodging. Handlers over one kotoba EAVT graph:

  list_stay          register a lodging offer (no commission/surge/person-score fields exist)
  discover_stays     stay need → commons-first ranked stays (G4 Ring ordering)
  book               consent → reservation; Ring0 free/cost-share | Ring1 member-signed settle | Ring2 self-book handoff
  build_settlement_intent / authorize_settlement   Ring1 USDC + TitheRouter 10% (G7), member-signed (G8)

Hard invariants encoded so they are structurally unrepresentable, not policy:
  - no commission (G2): no commission/take-rate field; Ring1 gross = tithe + hostNet exactly;
    Ring2 booking is a handoff to the operator's OWN page — shukubo is never merchant-of-record.
  - no surge (G13): a stay's cost is flat/cost-share; there is no demand/dynamic-price field.
  - hospitality-dignity (G12): no guest/host score field exists; only the SPACE's habitability
    + safety is attested. Pilgrim-welcome default.
  - privacy (G14/G9): noSurveil ≡ True (no in-stay cameras/biometrics as a feature); booking
    PII via com.etzhayyim.encrypted.*.

LLM (need parsing) is Murakumo-only (G5). R0 ships bounded :representative seed; live external
OTA ingest + real external booking are Council Lv7+ gated (G11); Ring1 settlement intent-only.
"""
from __future__ import annotations

from typing import TypedDict

try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000  # 10% TitheRouter auto-split (G7), basis points

# Ring ordering is constitutional (G4): covenantal hospitality before internal before external.
RING_ORDER = ["commons", "internal", "external"]


# --------------------------------------------------------------------------- #
# list_stay (G2/G12/G13/G14 — no commission/score/surge fields; privacy invariant)
# --------------------------------------------------------------------------- #
class Stay(TypedDict, total=False):
    stayId: str
    ring: str
    kind: str
    hostDid: str
    title: str
    capacity: int
    costMode: str
    costMinor: int
    habitability: str
    operatorUrl: str
    availability: str


def list_stay(host_did: str, ring: str, kind: str, *, title: str, capacity: int = 1,
              cost_mode: str = "cost-share", cost_minor: int = 0,
              habitability: str = "water+heat+egress", operator_url: str = "",
              availability: str = "available", sourcing: str = "authoritative") -> Stay:
    """Register a lodging offer. Note the field set: there is NO commission, NO surge/dynamic
    price, and NO guest/host score — only the SPACE's habitability is attested (G12). `noSurveil`
    is a constant invariant (G14)."""
    if ring not in RING_ORDER:
        raise ValueError(f"unknown ring {ring!r}")
    return {
        "stayId": f"shukubo.{kind}.{abs(hash(host_did + title)) & 0xFFFF:04x}",
        "ring": ring,
        "kind": kind,
        "hostDid": host_did,
        "title": title,
        "capacity": int(capacity),
        "costMode": cost_mode,        # free | cost-share | fixed — never demand-priced (G13)
        "costMinor": int(cost_minor),
        "habitability": habitability,  # the SPACE is attested, never the person (G12)
        "noSurveil": True,             # G14 invariant — no in-stay cameras/biometrics
        "operatorUrl": operator_url,   # external ring only: operator's OWN booking page
        "availability": availability,
        "sourcing": sourcing,          # G10 honesty
    }


# --------------------------------------------------------------------------- #
# discover (G4 commons-first)
# --------------------------------------------------------------------------- #
def discover_stays(need_text: str, stays: list) -> dict:
    """need → Ring 0 commons → Ring 1 internal → Ring 2 external. Returns the first ring with
    candidates as `resolved_ring` (commons-first, G4), but carries the full set so the member
    sees the covenantal/cost-share alternatives even when an outer ring is chosen."""
    by_ring = {r: [s for s in stays if s.get("ring") == r] for r in RING_ORDER}
    # within a ring, cheaper/cost-share first (sufficiency, not yield) — never paid placement
    for r in RING_ORDER:
        by_ring[r].sort(key=lambda s: int(s.get("costMinor", 0)))
    resolved = next((r for r in RING_ORDER if by_ring[r]), "unresolved")
    ordered = [s for r in RING_ORDER for s in by_ring[r]]
    return {"resolved_ring": resolved, "candidates": ordered}


# --------------------------------------------------------------------------- #
# settlement (Ring 1 only) — G2 no-commission, G7 tithe, G8 no-server-key
# --------------------------------------------------------------------------- #
def build_settlement_intent(gross_minor: int, host_did: str,
                            operator_ref: str | None = None) -> dict:
    """Ring-1 stay settlement. gross = flat cost-share; tithe 10% (G7); hostNet = gross − tithe;
    NO platform commission (G2: gross = tithe + hostNet exactly). INTENT only at R0 (G11)."""
    gross = int(gross_minor)
    tithe = (gross * TITHE_BPS) // 10_000
    host_net = gross - tithe
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross,
        "commissionMinor": 0,          # G2: structural zero — shukubo takes nothing
        "titheMinor": tithe,
        "hostNetMinor": host_net,
        "hostDid": host_did,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        "serverHeldKey": False,        # G8 invariant
        "state": "executed" if operator_ref else "intent",
        "operatorRef": operator_ref,
        "signed": False,
    }


def authorize_settlement(settlement: dict, signature: dict) -> dict:
    """Only a member-origin signature authorizes (G8 no-server-key); server signature refused."""
    if signature.get("origin") != "member":
        return {**settlement, "signed": False, "refused": True,
                "reason": "only a member passkey/wallet signature authorizes (G8 no-server-key)"}
    if settlement.get("serverHeldKey"):
        return {**settlement, "signed": False, "refused": True,
                "reason": "settlement carries a server-held key — invariant violation (G8)"}
    return {**settlement, "signed": True, "signatureRef": signature.get("ref")}


# --------------------------------------------------------------------------- #
# book — Ring-routed reservation (G1 consent, G2 boundary)
# --------------------------------------------------------------------------- #
def dates_overlap(in1: str, out1: str, in2: str, out2: str) -> bool:
    """Half-open date-interval overlap [checkIn, checkOut). Adjacent stays (one's checkout ==
    the next's checkin) do NOT overlap. ISO date strings compare lexically."""
    return in1 < out2 and in2 < out1


def stay_available(stay_id: str, check_in: str, check_out: str, confirmed_bookings: list) -> bool:
    """True iff no CONFIRMED booking for this stay overlaps the requested dates (no-double-book).
    The lodging analogue of yotei's slot guard (G2 hospitality / G13 honest availability)."""
    for b in confirmed_bookings:
        if b.get("stayId") != stay_id:
            continue
        if b.get("state") not in ("confirmed", "settle-intent"):
            continue
        if dates_overlap(check_in, check_out, b.get("checkIn", ""), b.get("checkOut", "")):
            return False
    return True


def book(stay: Stay, guest_did: str, check_in: str, check_out: str, consent_ref: str,
         sbt_registry: dict, confirmed_bookings: list | None = None) -> dict:
    """Route a reservation by ring:
      Ring 0 (commons)  — covenantal/cost-share; no platform settlement.
      Ring 1 (internal) — SBT↔SBT; member-signed settlement intent (G7/G8); zero commission (G2).
      Ring 2 (external) — self-book HANDOFF to the operator's own page; shukubo is never the
                          merchant-of-record and takes no inflow (G2); no tithe.
    Requires consent (G1). For commons/internal stays (shukubo-held inventory), refuses a date
    range that overlaps a confirmed booking (no-double-book); external-mirror stays are not
    shukubo's inventory so availability is the operator's to assert."""
    if not consent_ref:
        return {"state": "refused", "reason": "missing DID-signed consent (G1)"}
    ring = stay.get("ring")
    if ring in ("commons", "internal") and confirmed_bookings:
        if not stay_available(stay["stayId"], check_in, check_out, confirmed_bookings):
            return {"state": "refused", "reason": "stay already booked for those dates (no-double-book)"}
    common = {
        "bookingId": f"{stay['stayId']}.bk.{abs(hash(guest_did + check_in)) & 0xFFFF:04x}",
        "stayId": stay["stayId"],
        "guestDid": guest_did,
        "ring": ring,
        "checkIn": check_in,
        "checkOut": check_out,
        "consentRef": consent_ref,
        "recordEnc": True,             # G9: booking PII encrypted
    }
    if ring == "commons":
        return {**common, "state": "confirmed", "costShareMinor": int(stay.get("costMinor", 0)),
                "settlement": "commons-none", "titheMinor": 0}
    if ring == "internal":
        if not sbt_registry.get(guest_did, False):
            return {**common, "state": "refused", "reason": "guest not an active Adherent SBT holder (§3)"}
        settlement = build_settlement_intent(int(stay.get("costMinor", 0)), stay["hostDid"])
        return {**common, "state": "settle-intent", "settlement": settlement,
                "titheMinor": settlement["titheMinor"]}
    if ring == "external":
        # member transacts directly with the operator; shukubo never charges (G2)
        return {**common, "state": "self-book-handoff", "principal": "member",
                "handoffUrl": stay.get("operatorUrl", ""), "settlement": "external-none",
                "titheMinor": 0}
    return {**common, "state": "refused", "reason": f"unknown ring {ring!r}"}


# --------------------------------------------------------------------------- #
# host registration (G12 hospitality-dignity, G14 privacy)
# --------------------------------------------------------------------------- #
_REQUIRED_HABITABILITY = ("water", "heat", "egress")


def register_host(host_did: str, stay: Stay) -> dict:
    """Register a stay's host. Attests the SPACE's habitability (G12 — the space, never the
    person) and enforces the privacy invariant (G14 — noSurveil). A stay that advertises
    in-stay surveillance, or that lacks the minimum habitability attestation, is refused.
    There is no host/guest score field to set (G12 — persons are never rated)."""
    if stay.get("noSurveil") is not True:
        return {"state": "refused", "reason": "in-stay surveillance not permitted as a feature (G14)"}
    habit = (stay.get("habitability") or "").lower()
    missing = [h for h in _REQUIRED_HABITABILITY if h not in habit]
    if missing:
        return {"state": "refused", "reason": f"habitability attestation missing {missing} (G12)"}
    return {
        "state": "registered",
        "hostDid": host_did,
        "stayId": stay["stayId"],
        "ring": stay.get("ring"),
        "habitability": stay.get("habitability"),
        "noSurveil": True,
        # NOTE: deliberately no host/guest score, rating, or rank field (G12)
    }
