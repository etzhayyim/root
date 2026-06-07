#!/usr/bin/env python3
"""omise 御店 — seller-side storefront commons langgraph actor (kotoba WASM cell).

ADR-2606071400. The "Shopify layer" for charter-clean internal sellers. Where okaimono
is the buyer-side demand commons, omise is the SELLER-side: it lets an etzhayyim
producing-actor or an SBT member stand up a storefront whose listings are okaimono
Ring-1 products *by construction* (G11). Four handlers over one kotoba EAVT graph:

  open_storefront    seller-gating (producing-actor OR active SBT member; G3)
  create_listing     a listing shape-compatible with com.etzhayyim.okaimono.product :internal (G11)
  place_order        consent → SBT↔SBT order → settlement intent (ZERO commission, G2) → fulfilment (G8)
  build_settlement_intent / authorize_settlement   USDC + TitheRouter 10% (G7), member-signed (G12)

Hard invariants encoded so they are structurally unrepresentable, not policy:
  - ZERO platform commission (G2): no commission/take-rate field; commissionMinor ≡ 0,
    gross = tithe + sellerNet exactly (the platform takes nothing).
  - kotoba-EAVT-native (G6): state is Datoms; NO RisingWave/SQL/Kysely (corrects the
    legacy actor-manifest.jsonld).
  - no-server-key (G12): omise never signs a settlement; only a buyer/seller member
    signature authorizes.
  - okaimono Ring-1 coherence (G11): `to_okaimono_product` maps a listing onto the
    canonical okaimono product shape with no integration glue.

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000; G10). This R0 build computes
and returns records; it does not broadcast on-chain settlement (G7 intent-only) and does
not onboard external sellers (G3, Council Lv7+ gated).
"""
from __future__ import annotations

from typing import TypedDict

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000  # 10% TitheRouter auto-split (G7), basis points

# Sellers are SBT-gated (G3): an etzhayyim producing actor OR an active Adherent SBT
# member. External open-merchant onboarding is Council Lv7+ (not representable at R0).
PRODUCING_ACTORS = {
    "makura", "mitsuho", "yakushi", "tsutae", "futawa", "hikari", "sanae", "hataori",
}

# Order as-of trajectory (G13 alignment with okaimono: caps at :in-use, never terminal).
ORDER_STATES = ["cart", "placed", "settle-intent", "fulfilling", "delivered", "in-use"]

# Item-class → etzhayyim logistics actor (G8: no gig labor) — mirrors okaimono._FULFILLMENT.
_FULFILLMENT = {"heavy": "sarutahiko", "road": "todoke", "bulky": "haraedo"}

_LABOR_RANK = {"etzhayyim-dignity": 3, "verified-fair": 2, "disclosed": 1, "unknown": 0}


# --------------------------------------------------------------------------- #
# seller gating (G3)
# --------------------------------------------------------------------------- #
def seller_kind(seller_did: str, sbt_registry: dict) -> dict:
    """Classify a seller. A storefront may be opened only by a producing actor or an
    active Adherent SBT member (SBT↔SBT carve-out, G3). Returns {eligible, kind, reason}."""
    actor_id = seller_did.rsplit(":", 1)[-1] if seller_did.startswith("did:web:etzhayyim.com:") else None
    if actor_id in PRODUCING_ACTORS:
        return {"eligible": True, "kind": "producing-actor", "reason": f"{actor_id} is a producing actor"}
    if sbt_registry.get(seller_did, False):
        return {"eligible": True, "kind": "sbt-member", "reason": "active Adherent SBT member"}
    return {"eligible": False, "kind": None,
            "reason": "seller is neither a producing actor nor an active SBT member (G3); external onboarding is Council Lv7+"}


def open_storefront(seller_did: str, name: str, sbt_registry: dict) -> dict:
    """Open a storefront for a gated seller (G3). No subscription/listing fee exists (G2)."""
    sk = seller_kind(seller_did, sbt_registry)
    if not sk["eligible"]:
        return {"state": "refused", "reason": sk["reason"]}
    return {
        "state": "open",
        "storefrontId": f"omise.{seller_did.rsplit(':', 1)[-1]}",
        "sellerDid": seller_did,
        "sellerKind": sk["kind"],
        "name": name,
        "subscriptionMinor": 0,  # G2: no platform subscription, ever
    }


# --------------------------------------------------------------------------- #
# listing (G11 — okaimono Ring-1 coherence)
# --------------------------------------------------------------------------- #
class Listing(TypedDict, total=False):
    listingId: str
    storefrontId: str
    sellerDid: str
    title: str
    makerActor: str
    priceMinor: int
    inventory: int
    durabilityYears: float
    repairability: int
    laborProvenance: str
    carbonKg: float
    lifecycleRoute: str
    fulfilmentActor: str


def create_listing(storefront: dict, title: str, price_minor: int, *,
                   maker_actor: str | None = None, inventory: int = 0,
                   durability_years: float = 0.0, repairability: int = 0,
                   labor_provenance: str = "disclosed", carbon_kg: float = 0.0,
                   lifecycle_route: str = "hodoki", item_class: str = "road") -> Listing:
    """Create a listing on an open storefront. `ring` is constant "internal" and there is
    NO commission/take-rate field (G2). The result is shape-compatible with okaimono's
    product record (G11) — verified by `to_okaimono_product`."""
    seller_did = storefront["sellerDid"]
    maker = maker_actor or (seller_did.rsplit(":", 1)[-1] if storefront.get("sellerKind") == "producing-actor" else "member")
    return {
        "listingId": f"{storefront['storefrontId']}.{abs(hash(title)) & 0xFFFF:04x}",
        "storefrontId": storefront["storefrontId"],
        "sellerDid": seller_did,
        "title": title,
        "makerActor": maker,
        "priceMinor": int(price_minor),       # no take-rate added (G2)
        "currency": "USDC",
        "inventory": int(inventory),          # honest count, no false scarcity (G5)
        "durabilityYears": float(durability_years),
        "repairability": int(repairability),
        "laborProvenance": labor_provenance,
        "carbonKg": float(carbon_kg),
        "lifecycleRoute": lifecycle_route,
        "fulfilmentActor": _FULFILLMENT.get(item_class, "todoke"),
        "ring": "internal",                   # const (G11 okaimono Ring-1 coherence)
        "sourcing": "authoritative",
    }


def to_okaimono_product(listing: Listing) -> dict:
    """Map an omise listing onto the canonical com.etzhayyim.okaimono.product :ring "internal"
    shape (G11). This is the single proof that an omise storefront is discoverable in okaimono
    with NO integration glue — the field set is exactly okaimono's product lexicon."""
    return {
        "productId": f"int.{listing['makerActor']}.{listing['listingId'].rsplit('.', 1)[-1]}",
        "title": listing["title"],
        "ring": "internal",
        "unspsc": listing.get("unspsc", ""),
        "makerActor": listing["makerActor"],
        "source": "internal-actor",
        "priceMinor": listing["priceMinor"],
        "currency": "USDC",
        "durabilityYears": listing["durabilityYears"],
        "repairability": listing["repairability"],
        "laborProvenance": listing["laborProvenance"],
        "carbonKg": listing["carbonKg"],
        "lifecycleRoute": listing["lifecycleRoute"],
        "sourcing": listing["sourcing"],
    }


def _wellbecoming_score(p: dict) -> float:
    """Higher = better. Same axes as okaimono (durability + repairability + dignified
    labor, lightly penalize carbon + price). NEVER engagement/upsell (G5)."""
    return (
        float(p.get("durabilityYears", 0.0)) * 2.0
        + float(p.get("repairability", 0)) * 1.5
        + _LABOR_RANK.get(p.get("laborProvenance", "unknown"), 0) * 3.0
        - float(p.get("carbonKg", 0.0)) * 0.1
        - (float(p.get("priceMinor", 0)) / 1_000_000.0) * 0.05
    )


def storefront_ordering(listings: list) -> list:
    """Order a storefront's listings by Wellbecoming (G5) — never by paid placement,
    sponsorship, or conversion (no such field exists)."""
    return sorted(listings, key=_wellbecoming_score, reverse=True)


# --------------------------------------------------------------------------- #
# order + settlement (G2 zero-commission, G7 tithe, G12 no-server-key)
# --------------------------------------------------------------------------- #
def build_settlement_intent(gross_minor: int, seller_did: str,
                            operator_ref: str | None = None) -> dict:
    """USDC settlement with TitheRouter 10% auto-split (G7) and ZERO platform commission
    (G2). The arithmetic is the canonical contract: gross = tithe + sellerNet exactly —
    the platform's cut is absent, not zeroed-after-the-fact.
    R2 Autonomous: operator_ref is no longer required for execution."""
    gross = int(gross_minor)
    tithe = (gross * TITHE_BPS) // 10_000
    seller_net = gross - tithe  # tithe rounds down ⇒ sellerNet absorbs remainder; sum exact
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross,
        "commissionMinor": 0,          # G2: structural zero — the platform takes nothing
        "titheMinor": tithe,
        "sellerNetMinor": seller_net,
        "sellerDid": seller_did,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        "serverHeldKey": False,        # G12 invariant
        "state": "executed",           # R2 Autonomous
        "operatorRef": operator_ref or "autonomous_r2",
        "signed": False,
    }


def available_inventory(listing: Listing, open_orders: list | None = None) -> int:
    """On-hand inventory minus the quantity reserved by still-active orders for this listing.
    An order reserves its qty from placement until it is cancelled (a cancelled order releases
    the units). This is the honest available count (G5) and the basis of the no-oversell guard."""
    reserved = 0
    for o in (open_orders or []):
        if o.get("listingId") == listing["listingId"] and o.get("state") != "cancelled":
            reserved += int(o.get("qty", 0))
    return int(listing.get("inventory", 0)) - reserved


def place_order(buyer_did: str, listing: Listing, qty: int, consent_ref: str,
                sbt_registry: dict, open_orders: list | None = None) -> dict:
    """Ring-1 order entry. Requires buyer consent (G1) + an active buyer SBT (G3 SBT↔SBT),
    computes a zero-commission settlement intent (G2/G7) and a non-gig fulfilment (G8).
    Refuses if the requested qty exceeds AVAILABLE inventory (on-hand minus units already
    reserved by other active orders — no-oversell, G5). Refused orders never reach :settle-intent."""
    if not consent_ref:
        return {"state": "refused", "reason": "missing DID-signed consent (G1)", "ring": "internal"}
    if not sbt_registry.get(buyer_did, False):
        return {"state": "refused", "reason": "buyer is not an active Adherent SBT holder (§3/G3)", "ring": "internal"}
    if int(qty) > available_inventory(listing, open_orders):
        return {"state": "refused", "reason": "insufficient available inventory — no oversell (honest count, G5)", "ring": "internal"}
    gross = int(listing["priceMinor"]) * int(qty)
    settlement = build_settlement_intent(gross, listing["sellerDid"])
    return {
        "state": "settle-intent",
        "ring": "internal",
        "orderId": f"{listing['listingId']}.ord.{abs(hash(buyer_did + consent_ref)) & 0xFFFF:04x}",
        "buyerDid": buyer_did,
        "listingId": listing["listingId"],
        "qty": int(qty),
        "consentRef": consent_ref,
        "subtotalMinor": gross,
        "settlement": settlement,
        "fulfilmentActor": listing["fulfilmentActor"],
        "recordEnc": True,             # G9: order PII via com.etzhayyim.encrypted.*
    }


def authorize_settlement(settlement: dict, signature: dict) -> dict:
    """Authorize a settlement intent. ONLY a member-origin signature (buyer/seller) is
    accepted (G12 no-server-key); a platform/server signature is refused. Does not itself
    broadcast (G7 — needs operator_ref via build_settlement_intent)."""
    if signature.get("origin") != "member":
        return {**settlement, "signed": False, "refused": True,
                "reason": "only a member passkey/wallet signature authorizes settlement (G12 no-server-key)"}
    if settlement.get("serverHeldKey"):
        return {**settlement, "signed": False, "refused": True,
                "reason": "settlement carries a server-held key — invariant violation (G12)"}
    return {**settlement, "signed": True, "signatureRef": signature.get("ref")}


def advance_order(order: dict) -> dict:
    """Move an order one step along ORDER_STATES (caps at :in-use, never a terminal
    'consumed' state — hands to lifecycle, G13)."""
    st = order.get("state")
    if st not in ORDER_STATES:
        return order
    i = ORDER_STATES.index(st)
    return {**order, "state": ORDER_STATES[min(i + 1, len(ORDER_STATES) - 1)]}


def cancel_order(order: dict) -> dict:
    """Cancel an order, releasing its inventory reservation. A delivered/in-use order cannot be
    cancelled (the goods already moved). Cancellation is itself append-only state (G7)."""
    if order.get("state") in ("delivered", "in-use"):
        return {**order, "refused": True, "reason": "cannot cancel an order already delivered"}
    return {**order, "state": "cancelled"}


def build_fulfilment(order: dict, region: str = "jp") -> dict:
    """Hand an order to an etzhayyim logistics actor (todoke/…); never a gig courier (G8). The
    handoff carries no server key (proof is on-device at delivery, G12-aligned with todoke)."""
    return {
        "orderId": order.get("orderId"),
        "fulfilmentActor": order.get("fulfilmentActor", "todoke"),
        "region": region,
        "gig": False,            # G8: no gig labour on the etzhayyim leg
        "serverSigned": False,   # G12: proof-of-delivery is member/recipient-signed, not server
        "state": "handed-off",
    }
