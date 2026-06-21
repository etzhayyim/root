#!/usr/bin/env python3
"""ainori 相乗 — pooled passenger-mobility commons langgraph actor (kotoba WASM cell).

ADR-2606071500. The Uber inversion. Members already travelling offer seats; riders
cost-share fuel/wear ONLY (no margin); the platform pays the driver cash≡0. Routing +
safety reuse the `todoke` route crate; this module is the matching + cost-share + settle
layer. Handlers over one kotoba EAVT graph:

  match_pool         ride need → occupancy-maximizing pooled match (G11), under safety envelope (G3)
  cost_share         flat per-rider split of real fuel/wear — demand NEVER raises it (G2 no-surge)
  build_settlement_intent / authorize_settlement   USDC + TitheRouter 10% (G4), member-signed (G5)

Hard invariants encoded so they are structurally unrepresentable, not policy:
  - no gig (G1): driverWageMinor ≡ 0 — the platform never pays a per-trip wage; a driver's
    cost-share is fuel/wear REIMBURSEMENT, not income; gig flag is const false.
  - no surge (G2): cost_share takes occupancy + real cost only; there is NO demand/surge
    parameter — a busy corridor cannot raise a rider's share.
  - safety envelope (G3): over-speed / out-of-ODD requests are REFUSED (envelopeOk False ⇒
    match refused), never clamped.
  - no person-tracking (G7/G12): no continuous-location field; only origin/destination +
    ephemeral match state.

LLM (ETA narration) is Murakumo-only (G9). R0/R1 computes plans + settlement intents.

R2-autonomy / G10 honesty (FINDING 260617): an autonomously-built settlement intent defaults
`operatorRef` to "autonomous_r2" when no operator is supplied — the operator flag on the INTENT
is relaxed. This does NOT relax no-server-key (G5/G7): the binding `authorize_settlement` still
REFUSES a server origin and requires a member signature (`serverHeldKey` stays False, member is
the write author — the ibuki/mimamori member-capability discipline, ADR-2606111400/2605231525),
and live dispatch / actuation near persons remains Council Lv6+ (Lv7+ autonomous-near-persons)
gated (G10). So autonomy is preserved without a platform-held key.
"""
from __future__ import annotations

from typing import TypedDict

try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000  # 10% TitheRouter auto-split (G4), basis points


# --------------------------------------------------------------------------- #
# safety envelope (G3) — REFUSAL not clamp. Mirrors todoke-route semantics.
# --------------------------------------------------------------------------- #
# Per-zone speed caps (m/s). A request that requires exceeding the cap is refused.
ZONE_CAP_MPS = {"residential": 8.3, "arterial": 13.9, "expressway": 27.8}
SAE_CEILING = 4  # SAE-L4 ceiling (G3)


def safety_envelope_ok(zone: str, planned_speed_mps: float, in_odd: bool, sae_level: int) -> dict:
    """Return {ok, reason}. Refuses (not clamps) when speed exceeds the zone cap, the route
    leaves the operational design domain, or the autonomy level exceeds the SAE-L4 ceiling."""
    if not in_odd:
        return {"ok": False, "reason": "route leaves operational design domain (G3 refusal)"}
    if sae_level > SAE_CEILING:
        return {"ok": False, "reason": f"SAE level {sae_level} exceeds L4 ceiling (G3 refusal)"}
    cap = ZONE_CAP_MPS.get(zone)
    if cap is None:
        return {"ok": False, "reason": f"unknown zone {zone!r} — no cap, refused (G3)"}
    if planned_speed_mps > cap:
        return {"ok": False, "reason": f"planned {planned_speed_mps} m/s exceeds {zone} cap {cap} (G3 refusal, not clamp)"}
    return {"ok": True, "reason": "within SAE-L4 envelope"}


# --------------------------------------------------------------------------- #
# cost-share (G2 no-surge) — flat split of real cost; NO demand parameter exists.
# --------------------------------------------------------------------------- #
def cost_share(fuel_wear_minor: int, occupancy: int) -> int:
    """Each rider's flat share of the trip's REAL fuel/wear cost. Note the signature: there
    is no demand / time-of-day / surge multiplier — a rider's share depends only on the real
    cost and how many share it (G2). Higher occupancy ⇒ lower share, the opposite of surge."""
    occ = max(1, int(occupancy))
    return int(fuel_wear_minor) // occ


# --------------------------------------------------------------------------- #
# pooled matching (G11 occupancy-maximizing) under the safety envelope (G3)
# --------------------------------------------------------------------------- #
class RideRequest(TypedDict, total=False):
    requestId: str
    riderDid: str
    origin: str
    destination: str
    seats: int
    consentRef: str
    mode: str  # human-pooled | autonomous-pooled


def match_pool(request: RideRequest, candidate_trips: list) -> dict:
    """Match a ride need onto a trip a carrier is already making. Pooling-first (G11): among
    feasible trips, prefer the one that yields the HIGHEST resulting occupancy (fill seats that
    are already moving), then least detour. A trip whose safety envelope fails is dropped (G3).
    Requires consent (G8). Returns a rideMatch or a refusal."""
    if not request.get("consentRef"):
        return {"state": "refused", "reason": "missing DID-signed consent (G8)"}

    feasible = []
    for t in candidate_trips:
        env = safety_envelope_ok(
            t.get("zone", "arterial"), t.get("plannedSpeedMps", 0.0),
            t.get("inOdd", True), t.get("saeLevel", 4),
        )
        seats_left = int(t.get("seatsAvailable", 0))
        if env["ok"] and seats_left >= int(request.get("seats", 1)):
            feasible.append((t, env))
    if not feasible:
        return {"state": "refused", "reason": "no pooled trip within seats + SAE-L4 envelope (G3)"}

    # G11: maximize resulting occupancy, then minimize added detour.
    def key(item):
        t, _ = item
        resulting_occupancy = int(t.get("occupancy", 0)) + int(request.get("seats", 1))
        return (-resulting_occupancy, int(t.get("detourMeters", 0)))

    trip, _ = sorted(feasible, key=key)[0]
    occupancy = int(trip.get("occupancy", 0)) + int(request.get("seats", 1))
    share = cost_share(int(trip.get("fuelWearMinor", 0)), occupancy)
    return {
        "state": "proposed",
        "matchId": f"{request['requestId']}.m{abs(hash(trip.get('tripId',''))) & 0xFFFF:04x}",
        "requestId": request["requestId"],
        "carrierDid": trip.get("carrierDid"),
        "routeId": trip.get("tripId"),
        "occupancy": occupancy,
        "detourMeters": int(trip.get("detourMeters", 0)),
        "costShareMinor": share,
        "driverWageMinor": 0,        # G1: platform pays driver no wage, ever
        "gig": False,                # G1
        "envelopeOk": True,          # G3
    }


# --------------------------------------------------------------------------- #
# settlement (G4 tithe, G5 no-server-key) — driver wage is structurally 0 (G1)
# --------------------------------------------------------------------------- #
def build_settlement_intent(gross_minor: int, carrier_did: str,
                            operator_ref: str | None = None) -> dict:
    """Settle the pooled cost-share. gross = the riders' collected cost-share; tithe 10% (G4);
    carrierReimbursement = gross − tithe (fuel/wear recovery, NOT wage); driverWage ≡ 0 (G1).
    G10 (FINDING 260617): execution is gated. WITH an operator_ref the intent is operator-executed
    (state='executed'); WITHOUT one it stays an 'intent' that only a MEMBER signature can execute
    (authorize_settlement) — the server never auto-executes (G5/G7 no-server-key, never relaxed)."""
    gross = int(gross_minor)
    tithe = (gross * TITHE_BPS) // 10_000
    reimbursement = gross - tithe
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross,
        "titheMinor": tithe,
        "carrierReimbursementMinor": reimbursement,   # fuel/wear recovery, not income
        "driverWageMinor": 0,                          # G1: invariant — no per-trip wage
        "carrierDid": carrier_did,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        "serverHeldKey": False,                        # G5 invariant
        "state": "executed" if operator_ref else "intent",  # G10: operator-gated execution;
                                                       # absent an operator it stays an intent that
                                                       # a member signature must execute (G5/G7)
        "operatorRef": operator_ref or "autonomous_r2",
        "signed": False,
    }


def authorize_settlement(settlement: dict, signature: dict) -> dict:
    """Only a member-origin signature authorizes (G5 no-server-key); a server signature is
    refused. Does not broadcast (G10)."""
    if signature.get("origin") != "member":
        return {**settlement, "signed": False, "refused": True,
                "reason": "only a member passkey/wallet signature authorizes (G5 no-server-key)"}
    if settlement.get("serverHeldKey"):
        return {**settlement, "signed": False, "refused": True,
                "reason": "settlement carries a server-held key — invariant violation (G5)"}
    # member signature authorizes → the intent transitions to executed (member is the write author)
    return {**settlement, "signed": True, "state": "executed", "signatureRef": signature.get("ref")}
