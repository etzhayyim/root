#!/usr/bin/env python3
"""omise 御店 — test harness (stdlib unittest; no kotoba host needed).

Verifies the structural invariants of ADR-2606071400:
  G2 zero commission       — commissionMinor ≡ 0; gross = tithe + sellerNet exactly
  G3 seller-gating         — only producing-actor / active-SBT-member opens a storefront
  G7 tithe                 — TitheRouter 10% auto-split
  G11 okaimono coherence   — listing maps onto okaimono product shape with no glue
  G12 no-server-key        — only a member-origin signature authorizes settlement
  G5 wellbecoming ordering — ranking is sufficiency-based, not paid placement
  G13 order trajectory     — caps at :in-use, never terminal
"""
import unittest

import agent


SBT = {
    "did:web:etzhayyim.com:mitsuho": True,         # producing actor (also gated by name)
    "did:plc:buyer-alice": True,                   # active SBT member buyer
    "did:plc:seller-bob": True,                    # active SBT member seller
    "did:plc:lapsed": False,                       # inactive
}


def _open_actor_storefront():
    return agent.open_storefront("did:web:etzhayyim.com:mitsuho", "Mitsuho Rice", SBT)


class SellerGating(unittest.TestCase):
    def test_producing_actor_opens(self):
        sf = _open_actor_storefront()
        self.assertEqual(sf["state"], "open")
        self.assertEqual(sf["sellerKind"], "producing-actor")

    def test_sbt_member_opens(self):
        sf = agent.open_storefront("did:plc:seller-bob", "Bob's Goods", SBT)
        self.assertEqual(sf["state"], "open")
        self.assertEqual(sf["sellerKind"], "sbt-member")

    def test_non_member_refused(self):
        sf = agent.open_storefront("did:plc:stranger", "Random Shop", SBT)
        self.assertEqual(sf["state"], "refused")
        self.assertIn("G3", sf["reason"])

    def test_lapsed_member_refused(self):
        sf = agent.open_storefront("did:plc:lapsed", "Lapsed", SBT)
        self.assertEqual(sf["state"], "refused")

    def test_no_subscription_fee(self):
        self.assertEqual(_open_actor_storefront()["subscriptionMinor"], 0)


class Listing(unittest.TestCase):
    def setUp(self):
        self.sf = _open_actor_storefront()
        self.listing = agent.create_listing(
            self.sf, "Koshihikari 5kg", 8_000_000, inventory=40,
            durability_years=1.0, repairability=0, labor_provenance="etzhayyim-dignity",
            carbon_kg=2.1, lifecycle_route="commons-return", item_class="road",
        )

    def test_ring_is_internal_const(self):
        self.assertEqual(self.listing["ring"], "internal")

    def test_no_commission_field(self):
        # G2: a commission/take-rate field must not exist on a listing
        for k in self.listing:
            self.assertNotIn("commission", k.lower())
            self.assertNotIn("takerate", k.lower().replace("_", ""))

    def test_no_sponsored_field(self):
        # G4/G5: no paid-placement / boost / sponsored field
        for k in self.listing:
            self.assertNotIn("sponsor", k.lower())
            self.assertNotIn("boost", k.lower())

    def test_fulfilment_is_non_gig_actor(self):
        self.assertEqual(self.listing["fulfilmentActor"], "todoke")

    def test_okaimono_coherence_shape(self):
        # G11: maps onto okaimono product shape with no glue — exact key set
        prod = agent.to_okaimono_product(self.listing)
        expected = {
            "productId", "title", "ring", "unspsc", "makerActor", "source",
            "priceMinor", "currency", "durabilityYears", "repairability",
            "laborProvenance", "carbonKg", "lifecycleRoute", "sourcing",
        }
        self.assertEqual(set(prod), expected)
        self.assertEqual(prod["ring"], "internal")
        self.assertEqual(prod["source"], "internal-actor")
        self.assertEqual(prod["makerActor"], "mitsuho")
        self.assertEqual(prod["priceMinor"], 8_000_000)


class Ordering(unittest.TestCase):
    def test_wellbecoming_not_price(self):
        # a durable, repairable, dignified-labor item outranks a cheap throwaway
        durable = {"durabilityYears": 10, "repairability": 9, "laborProvenance": "etzhayyim-dignity",
                   "carbonKg": 5, "priceMinor": 20_000_000}
        throwaway = {"durabilityYears": 0.5, "repairability": 0, "laborProvenance": "unknown",
                     "carbonKg": 8, "priceMinor": 2_000_000}
        ranked = agent.storefront_ordering([throwaway, durable])
        self.assertIs(ranked[0], durable)


class Settlement(unittest.TestCase):
    def test_zero_commission_and_exact_split(self):
        s = agent.build_settlement_intent(10_000_000, "did:web:etzhayyim.com:mitsuho")
        self.assertEqual(s["commissionMinor"], 0)                       # G2
        self.assertEqual(s["titheMinor"], 1_000_000)                    # G7 10%
        self.assertEqual(s["sellerNetMinor"], 9_000_000)
        # gross = tithe + sellerNet EXACTLY (platform takes nothing)
        self.assertEqual(s["grossMinor"], s["titheMinor"] + s["sellerNetMinor"])
        self.assertEqual(s["state"], "intent")                         # R0 not broadcast

    def test_remainder_absorbed_no_loss(self):
        # odd gross: tithe rounds down, sellerNet absorbs remainder, sum stays exact
        s = agent.build_settlement_intent(10_000_007, "did:plc:seller-bob")
        self.assertEqual(s["grossMinor"], s["titheMinor"] + s["sellerNetMinor"])

    def test_broadcast_needs_operator(self):
        s = agent.build_settlement_intent(1_000_000, "did:plc:seller-bob", operator_ref="op-ref-1")
        self.assertEqual(s["state"], "executed")

    def test_no_server_key_invariant(self):
        s = agent.build_settlement_intent(1_000_000, "did:plc:seller-bob")
        self.assertFalse(s["serverHeldKey"])

    def test_only_member_signature_authorizes(self):
        s = agent.build_settlement_intent(1_000_000, "did:plc:seller-bob")
        server = agent.authorize_settlement(s, {"origin": "server", "ref": "x"})
        self.assertTrue(server.get("refused"))
        self.assertIn("G12", server["reason"])
        member = agent.authorize_settlement(s, {"origin": "member", "ref": "sig-123"})
        self.assertTrue(member["signed"])
        self.assertEqual(member["signatureRef"], "sig-123")


class OrderFlow(unittest.TestCase):
    def setUp(self):
        self.sf = _open_actor_storefront()
        self.listing = agent.create_listing(self.sf, "Koshihikari 5kg", 8_000_000, inventory=40)

    def test_happy_path_settle_intent(self):
        o = agent.place_order("did:plc:buyer-alice", self.listing, 2, "consent-abc", SBT)
        self.assertEqual(o["state"], "settle-intent")
        self.assertEqual(o["subtotalMinor"], 16_000_000)
        self.assertEqual(o["settlement"]["commissionMinor"], 0)         # G2
        self.assertEqual(o["fulfilmentActor"], "todoke")               # G8
        self.assertTrue(o["recordEnc"])                                 # G9

    def test_consent_required(self):
        o = agent.place_order("did:plc:buyer-alice", self.listing, 1, "", SBT)
        self.assertEqual(o["state"], "refused")
        self.assertIn("G1", o["reason"])

    def test_buyer_must_be_sbt(self):
        o = agent.place_order("did:plc:stranger", self.listing, 1, "consent-abc", SBT)
        self.assertEqual(o["state"], "refused")
        self.assertIn("G3", o["reason"])

    def test_inventory_enforced(self):
        o = agent.place_order("did:plc:buyer-alice", self.listing, 999, "consent-abc", SBT)
        self.assertEqual(o["state"], "refused")
        self.assertIn("inventory", o["reason"])

    def test_trajectory_caps_at_in_use(self):
        o = agent.place_order("did:plc:buyer-alice", self.listing, 1, "consent-abc", SBT)
        for _ in range(10):
            o = agent.advance_order(o)
        self.assertEqual(o["state"], "in-use")                         # G13: never terminal


class NoOversell(unittest.TestCase):
    def setUp(self):
        self.sf = _open_actor_storefront()
        self.listing = agent.create_listing(self.sf, "Koshihikari 5kg", 8_000_000, inventory=3)

    def test_available_minus_active_reservations(self):
        orders = [{"listingId": self.listing["listingId"], "qty": 2, "state": "settle-intent"}]
        self.assertEqual(agent.available_inventory(self.listing, orders), 1)

    def test_cancelled_order_releases_inventory(self):
        orders = [{"listingId": self.listing["listingId"], "qty": 3, "state": "cancelled"}]
        self.assertEqual(agent.available_inventory(self.listing, orders), 3)

    def test_oversell_refused(self):
        # 3 on hand, 2 already reserved → only 1 available; ordering 2 is refused
        existing = [{"listingId": self.listing["listingId"], "qty": 2, "state": "settle-intent"}]
        out = agent.place_order("did:plc:buyer-alice", self.listing, 2, "c", SBT, open_orders=existing)
        self.assertEqual(out["state"], "refused")
        self.assertIn("oversell", out["reason"])

    def test_order_within_available_ok(self):
        existing = [{"listingId": self.listing["listingId"], "qty": 2, "state": "settle-intent"}]
        out = agent.place_order("did:plc:buyer-alice", self.listing, 1, "c", SBT, open_orders=existing)
        self.assertEqual(out["state"], "settle-intent")

    def test_cancel_then_reorder(self):
        cancelled = [{"listingId": self.listing["listingId"], "qty": 3, "state": "cancelled"}]
        out = agent.place_order("did:plc:buyer-alice", self.listing, 3, "c", SBT, open_orders=cancelled)
        self.assertEqual(out["state"], "settle-intent")


class OrderCancel(unittest.TestCase):
    def test_cancel_sets_state(self):
        out = agent.cancel_order({"state": "settle-intent", "orderId": "o1"})
        self.assertEqual(out["state"], "cancelled")

    def test_cannot_cancel_delivered(self):
        out = agent.cancel_order({"state": "delivered", "orderId": "o1"})
        self.assertTrue(out["refused"])


class Fulfilment(unittest.TestCase):
    def test_non_gig_handoff(self):
        f = agent.build_fulfilment({"orderId": "o1", "fulfilmentActor": "todoke"})
        self.assertEqual(f["fulfilmentActor"], "todoke")
        self.assertFalse(f["gig"])            # G8
        self.assertFalse(f["serverSigned"])   # G12
        self.assertEqual(f["state"], "handed-off")


if __name__ == "__main__":
    unittest.main(verbosity=2)
