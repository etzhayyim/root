#!/usr/bin/env python3
"""shukubo 宿坊 — test harness (stdlib unittest; no kotoba host needed).

Verifies the structural invariants of ADR-2606071600:
  G2 no-commission      — no commission field on a stay; Ring1 gross = tithe + hostNet exactly;
                          Ring2 book is a handoff (shukubo never merchant-of-record)
  G4 commons-first      — discover resolves/orders commons → internal → external
  G7 tithe              — TitheRouter 10% split (Ring1)
  G8 no-server-key      — only a member-origin signature authorizes
  G12 hospitality-dignity — no guest/host score field; only space habitability
  G13 no-surge          — list_stay has no demand/dynamic-price field
  G14 privacy           — noSurveil ≡ True
"""
import unittest

import agent


SBT = {"did:plc:pilgrim": True, "did:plc:lapsed": False}


def _stay(ring, **kw):
    defaults = dict(host_did="did:plc:host", kind="member-room", title="Quiet room",
                    capacity=2, cost_mode="fixed", cost_minor=5_000_000)
    defaults.update(kw)
    return agent.list_stay(ring=ring, **defaults)


class ListStay(unittest.TestCase):
    def setUp(self):
        self.s = _stay("internal")

    def test_no_commission_field(self):
        for k in self.s:
            self.assertNotIn("commission", k.lower())

    def test_no_surge_field(self):
        for k in self.s:
            self.assertNotIn("surge", k.lower())
            self.assertNotIn("dynamic", k.lower())

    def test_no_person_score_field(self):
        # G12: persons are never scored; only the space's habitability is attested
        for k in self.s:
            self.assertNotIn("score", k.lower())
            self.assertNotIn("rating", k.lower())
        self.assertIn("habitability", self.s)

    def test_no_surveil_invariant(self):
        self.assertTrue(self.s["noSurveil"])   # G14


class Discover(unittest.TestCase):
    def test_commons_first(self):
        stays = [_stay("external", cost_minor=3_000_000), _stay("commons", cost_minor=0),
                 _stay("internal", cost_minor=5_000_000)]
        out = agent.discover_stays("need a bed", stays)
        self.assertEqual(out["resolved_ring"], "commons")
        self.assertEqual(out["candidates"][0]["ring"], "commons")    # G4 ordering
        self.assertEqual([c["ring"] for c in out["candidates"]],
                         ["commons", "internal", "external"])


class Settlement(unittest.TestCase):
    def test_zero_commission_exact_split(self):
        s = agent.build_settlement_intent(5_000_000, "did:plc:host")
        self.assertEqual(s["commissionMinor"], 0)                     # G2
        self.assertEqual(s["titheMinor"], 500_000)                   # G7
        self.assertEqual(s["hostNetMinor"], 4_500_000)
        self.assertEqual(s["grossMinor"], s["titheMinor"] + s["hostNetMinor"])

    def test_no_server_key(self):
        self.assertFalse(agent.build_settlement_intent(1, "h")["serverHeldKey"])

    def test_only_member_signature(self):
        s = agent.build_settlement_intent(1_000_000, "did:plc:host")
        srv = agent.authorize_settlement(s, {"origin": "server", "ref": "x"})
        self.assertTrue(srv.get("refused"))
        self.assertIn("G8", srv["reason"])
        mem = agent.authorize_settlement(s, {"origin": "member", "ref": "sig"})
        self.assertTrue(mem["signed"])


class Booking(unittest.TestCase):
    def test_consent_required(self):
        b = agent.book(_stay("internal"), "did:plc:pilgrim", "d1", "d2", "", SBT)
        self.assertEqual(b["state"], "refused")
        self.assertIn("G1", b["reason"])

    def test_commons_free_no_settlement(self):
        b = agent.book(_stay("commons", cost_mode="free", cost_minor=0),
                       "did:plc:anyone", "d1", "d2", "consent", SBT)
        self.assertEqual(b["state"], "confirmed")
        self.assertEqual(b["settlement"], "commons-none")
        self.assertEqual(b["titheMinor"], 0)

    def test_internal_requires_sbt_and_settles(self):
        ok = agent.book(_stay("internal"), "did:plc:pilgrim", "d1", "d2", "consent", SBT)
        self.assertEqual(ok["state"], "settle-intent")
        self.assertEqual(ok["settlement"]["commissionMinor"], 0)      # G2
        self.assertEqual(ok["titheMinor"], 500_000)                   # G7
        no = agent.book(_stay("internal"), "did:plc:lapsed", "d1", "d2", "consent", SBT)
        self.assertEqual(no["state"], "refused")

    def test_external_is_handoff_no_inflow(self):
        b = agent.book(_stay("external", operator_url="https://inn.example/book"),
                       "did:plc:pilgrim", "d1", "d2", "consent", SBT)
        self.assertEqual(b["state"], "self-book-handoff")
        self.assertEqual(b["principal"], "member")        # shukubo is NOT the buyer (G2)
        self.assertEqual(b["settlement"], "external-none")
        self.assertEqual(b["titheMinor"], 0)
        self.assertEqual(b["handoffUrl"], "https://inn.example/book")


class NoDoubleBook(unittest.TestCase):
    def test_dates_overlap(self):
        self.assertTrue(agent.dates_overlap("2026-06-01", "2026-06-05", "2026-06-03", "2026-06-08"))

    def test_adjacent_not_overlap(self):
        # checkout == next checkin → no overlap (half-open)
        self.assertFalse(agent.dates_overlap("2026-06-01", "2026-06-05", "2026-06-05", "2026-06-08"))

    def test_stay_available_when_no_conflict(self):
        confirmed = [{"stayId": "s1", "state": "confirmed", "checkIn": "2026-06-10", "checkOut": "2026-06-12"}]
        self.assertTrue(agent.stay_available("s1", "2026-06-01", "2026-06-05", confirmed))

    def test_internal_booking_refused_on_overlap(self):
        confirmed = [{"stayId": _stay("internal")["stayId"], "state": "confirmed",
                      "checkIn": "2026-06-01", "checkOut": "2026-06-05"}]
        out = agent.book(_stay("internal"), "did:plc:pilgrim", "2026-06-03", "2026-06-07",
                         "consent", SBT, confirmed_bookings=confirmed)
        self.assertEqual(out["state"], "refused")
        self.assertIn("no-double-book", out["reason"])

    def test_internal_booking_ok_when_free(self):
        confirmed = [{"stayId": _stay("internal")["stayId"], "state": "confirmed",
                      "checkIn": "2026-06-10", "checkOut": "2026-06-12"}]
        out = agent.book(_stay("internal"), "did:plc:pilgrim", "2026-06-01", "2026-06-05",
                         "consent", SBT, confirmed_bookings=confirmed)
        self.assertEqual(out["state"], "settle-intent")

    def test_external_not_blocked_by_availability(self):
        # external-mirror stays aren't shukubo inventory; availability is the operator's
        confirmed = [{"stayId": _stay("external")["stayId"], "state": "confirmed",
                      "checkIn": "2026-06-01", "checkOut": "2026-06-30"}]
        out = agent.book(_stay("external", operator_url="https://inn/x"), "did:plc:pilgrim",
                         "2026-06-02", "2026-06-04", "consent", SBT, confirmed_bookings=confirmed)
        self.assertEqual(out["state"], "self-book-handoff")


class HostRegistration(unittest.TestCase):
    def test_registers_with_habitability(self):
        out = agent.register_host("did:plc:host", _stay("internal", habitability="water+heat+egress"))
        self.assertEqual(out["state"], "registered")
        for k in out:
            self.assertNotIn("score", k.lower())   # G12 no person scoring
            self.assertNotIn("rating", k.lower())

    def test_missing_habitability_refused(self):
        out = agent.register_host("did:plc:host", _stay("internal", habitability="water"))
        self.assertEqual(out["state"], "refused")
        self.assertIn("G12", out["reason"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
