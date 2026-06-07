#!/usr/bin/env python3
"""yotei — kotoba-native scheduling commons langgraph actor (kotoba WASM cell).

ADR-2606072200 (Phase A of the substrate remediation wave, ADR-2606071800). Replaces the
legacy RisingWave/Cypher calendar graph with append-only bookings on the kotoba Datom log.
Handlers over one kotoba EAVT graph:

  generate_slots     availability window → free slot grid (minus confirmed bookings, G4)
  propose_booking    consent (G8) + no-double-book (G4) → proposed booking
  confirm_booking    re-check free at confirm time (race-safe) → member-signed confirm (G5)

Hard invariants encoded so they are structurally unrepresentable, not policy:
  - no-double-book (G4): a slot that overlaps any confirmed booking on the calendar is REFUSED;
    confirmation re-checks (a racing confirm cannot create an overlap).
  - no-server-key (G5): only a member signature confirms; a server signature is refused.
  - no-harvest (G2): booker contact lives only as an encrypted envelope ref; there is no
    profile/analytics field — the booking holds a slot, it does not feed a funnel.
  - append-only (G3): status transitions append; a confirmed booking is never overwritten.

Murakumo-only for NL command parsing (G7). R1 computes proposals/confirmations; social announce
+ on-chain anchoring are downstream.
"""
from __future__ import annotations

from typing import TypedDict

try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore


# --------------------------------------------------------------------------- #
# interval overlap (the core of no-double-book, G4)
# --------------------------------------------------------------------------- #
def _overlaps(a_start: int, a_dur: int, b_start: int, b_dur: int) -> bool:
    """Half-open interval overlap [start, start+dur). Touching ends do NOT overlap."""
    return a_start < b_start + b_dur and b_start < a_start + a_dur


def is_free(calendar_did: str, start_epoch_min: int, duration_min: int,
            confirmed_bookings: list) -> bool:
    """True iff the proposed slot overlaps no CONFIRMED booking on this calendar (G4)."""
    for b in confirmed_bookings:
        if b.get("status") != "confirmed":
            continue
        if b.get("calendarDid") != calendar_did:
            continue
        if _overlaps(start_epoch_min, duration_min,
                     int(b.get("startEpochMin", 0)), int(b.get("durationMin", 0))):
            return False
    return True


# --------------------------------------------------------------------------- #
# slot generation
# --------------------------------------------------------------------------- #
def generate_slots(availability: dict, day_start_epoch_min: int,
                   confirmed_bookings: list) -> list:
    """Enumerate free slots within an availability window for a given day (the day's midnight as
    epoch minutes). Honest availability only (G6): booked slots are simply absent — no count, no
    'almost gone'. Returns a list of {startEpochMin, durationMin}."""
    start = day_start_epoch_min + int(availability["startMin"])
    end = day_start_epoch_min + int(availability["endMin"])
    step = int(availability.get("slotMin", 30))
    cal = availability["calendarDid"]
    slots = []
    t = start
    while t + step <= end:
        if is_free(cal, t, step, confirmed_bookings):
            slots.append({"startEpochMin": t, "durationMin": step})
        t += step
    return slots


# --------------------------------------------------------------------------- #
# propose / confirm
# --------------------------------------------------------------------------- #
class BookingReq(TypedDict, total=False):
    bookingId: str
    calendarDid: str
    requesterDid: str
    responderDid: str
    startEpochMin: int
    durationMin: int
    consentRef: str
    contactRef: str


def propose_booking(req: BookingReq, confirmed_bookings: list) -> dict:
    """Propose a booking. Requires consent (G8); refuses if the slot overlaps a confirmed
    booking (G4). Booker contact is carried only as an encrypted envelope ref (G2). Returns a
    :proposed booking (unsigned) or a refusal."""
    if not req.get("consentRef"):
        return {"state": "refused", "reason": "missing DID-signed consent (G8)"}
    if not is_free(req["calendarDid"], int(req["startEpochMin"]), int(req["durationMin"]),
                   confirmed_bookings):
        return {"state": "refused", "reason": "slot overlaps a confirmed booking (G4 no-double-book)"}
    return {
        "state": "proposed",
        "bookingId": req["bookingId"],
        "calendarDid": req["calendarDid"],
        "requesterDid": req["requesterDid"],
        "responderDid": req.get("responderDid", ""),
        "startEpochMin": int(req["startEpochMin"]),
        "durationMin": int(req["durationMin"]),
        "consentRef": req["consentRef"],
        "contactRef": req.get("contactRef", ""),   # encrypted envelope only (G2)
        "status": "proposed",
        "confirmedSig": None,
        "appendOnly": True,
    }


def confirm_booking(booking: dict, signature: dict, confirmed_bookings: list) -> dict:
    """Confirm a proposed booking. Re-checks no-double-book at confirm time so a racing confirm
    cannot create an overlap (G4). ONLY a member-origin signature confirms (G5 no-server-key);
    a server signature is refused. Append-only (G3)."""
    if booking.get("state") != "proposed":
        return {**booking, "refused": True, "reason": "booking is not in :proposed state"}
    if signature.get("origin") != "member":
        return {**booking, "refused": True,
                "reason": "only a member passkey/wallet signature confirms (G5 no-server-key)"}
    # race-safe re-check (G4)
    if not is_free(booking["calendarDid"], int(booking["startEpochMin"]),
                   int(booking["durationMin"]), confirmed_bookings):
        return {**booking, "refused": True,
                "reason": "slot was taken before confirm — overlap refused (G4)"}
    return {**booking, "state": "confirmed", "status": "confirmed", "confirmedSig": signature.get("ref")}


# --------------------------------------------------------------------------- #
# cancel / reschedule (legacy /cancel /reschedule commands)
# --------------------------------------------------------------------------- #
def cancel_booking(booking: dict) -> dict:
    """Cancel a booking. A cancelled booking no longer blocks availability (is_free counts only
    :confirmed), so the slot is immediately re-bookable. Append-only state transition (G3)."""
    return {**booking, "state": "cancelled", "status": "cancelled"}


def reschedule_booking(booking: dict, new_start_epoch_min: int, new_duration_min: int,
                       confirmed_bookings: list, signature: dict) -> dict:
    """Move a confirmed booking to a new slot. Member-signed (G5). The new slot is re-checked for
    no-double-book (G4), EXCLUDING this booking's own current slot from the conflict set (moving a
    booking must not collide with itself). Refuses a non-confirmed booking or an occupied slot."""
    if booking.get("status") != "confirmed":
        return {**booking, "refused": True, "reason": "only a confirmed booking can be rescheduled"}
    if signature.get("origin") != "member":
        return {**booking, "refused": True,
                "reason": "only a member passkey/wallet signature reschedules (G5 no-server-key)"}
    others = [b for b in confirmed_bookings if b.get("bookingId") != booking.get("bookingId")]
    if not is_free(booking["calendarDid"], int(new_start_epoch_min), int(new_duration_min), others):
        return {**booking, "refused": True,
                "reason": "target slot overlaps another confirmed booking (G4 no-double-book)"}
    return {**booking, "startEpochMin": int(new_start_epoch_min),
            "durationMin": int(new_duration_min), "status": "confirmed", "rescheduled": True,
            "confirmedSig": signature.get("ref")}
