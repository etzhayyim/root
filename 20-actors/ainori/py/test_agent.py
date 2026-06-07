#!/usr/bin/env python3
"""ainori 相乗 — test harness (stdlib unittest; no kotoba host needed).

Verifies the structural invariants of ADR-2606071500:
  G1 no-gig        — driverWageMinor ≡ 0; gig ≡ False
  G2 no-surge      — cost_share depends only on real cost + occupancy; no demand multiplier
  G3 safety        — over-speed / out-of-ODD / >L4 requests are REFUSED, not clamped
  G4 tithe         — TitheRouter 10% split; gross = tithe + carrierReimbursement exactly
  G5 no-server-key — only a member-origin signature authorizes
  G11 pooling-first — match maximizes resulting occupancy
"""
import unittest

import agent


def _trip(**kw):
    base = dict(tripId="t1", carrierDid="did:plc:carrier", zone="arterial",
                plannedSpeedMps=12.0, inOdd=True, saeLevel=4, seatsAvailable=3,
                occupancy=1, detourMeters=200, fuelWearMinor=1_200_000)
    base.update(kw)
    return base


def _req(**kw):
    base = dict(requestId="r1", riderDid="did:plc:rider", origin="A", destination="B",
                seats=1, consentRef="consent-1", mode="human-pooled")
    base.update(kw)
    return base


class SafetyEnvelope(unittest.TestCase):
    def test_within_cap_ok(self):
        self.assertTrue(agent.safety_envelope_ok("arterial", 12.0, True, 4)["ok"])

    def test_over_speed_refused(self):
        v = agent.safety_envelope_ok("residential", 12.0, True, 4)  # cap 8.3
        self.assertFalse(v["ok"])
        self.assertIn("refusal", v["reason"])

    def test_out_of_odd_refused(self):
        self.assertFalse(agent.safety_envelope_ok("arterial", 5.0, False, 4)["ok"])

    def test_above_sae_l4_refused(self):
        self.assertFalse(agent.safety_envelope_ok("arterial", 5.0, True, 5)["ok"])


class NoSurge(unittest.TestCase):
    def test_flat_split_independent_of_demand(self):
        # The function has no demand/surge parameter at all; share depends only on cost+occupancy.
        self.assertEqual(agent.cost_share(1_200_000, 4), 300_000)

    def test_higher_occupancy_lowers_share(self):
        # opposite of surge: more riders ⇒ each pays LESS
        self.assertLess(agent.cost_share(1_200_000, 4), agent.cost_share(1_200_000, 2))

    def test_no_demand_kwarg(self):
        import inspect
        params = set(inspect.signature(agent.cost_share).parameters)
        self.assertEqual(params, {"fuel_wear_minor", "occupancy"})  # no surge/demand param


class Matching(unittest.TestCase):
    def test_consent_required(self):
        m = agent.match_pool(_req(consentRef=""), [_trip()])
        self.assertEqual(m["state"], "refused")
        self.assertIn("G8", m["reason"])

    def test_unsafe_trip_dropped(self):
        # only trip is over-speed for its zone ⇒ no feasible match
        m = agent.match_pool(_req(), [_trip(zone="residential", plannedSpeedMps=12.0)])
        self.assertEqual(m["state"], "refused")

    def test_pooling_first_maximizes_occupancy(self):
        low = _trip(tripId="low", occupancy=0, detourMeters=10)
        high = _trip(tripId="high", occupancy=2, detourMeters=500)
        m = agent.match_pool(_req(), [low, high])
        self.assertEqual(m["routeId"], "high")   # picks the fuller trip (G11), not the short detour
        self.assertEqual(m["occupancy"], 3)

    def test_no_gig_fields(self):
        m = agent.match_pool(_req(), [_trip()])
        self.assertEqual(m["driverWageMinor"], 0)   # G1
        self.assertFalse(m["gig"])                   # G1
        self.assertTrue(m["envelopeOk"])             # G3


class Settlement(unittest.TestCase):
    def test_driver_wage_zero_and_exact_split(self):
        s = agent.build_settlement_intent(1_000_000, "did:plc:carrier")
        self.assertEqual(s["driverWageMinor"], 0)                       # G1
        self.assertEqual(s["titheMinor"], 100_000)                      # G4 10%
        self.assertEqual(s["carrierReimbursementMinor"], 900_000)
        self.assertEqual(s["grossMinor"], s["titheMinor"] + s["carrierReimbursementMinor"])
        self.assertEqual(s["state"], "intent")

    def test_no_server_key(self):
        s = agent.build_settlement_intent(1_000_000, "did:plc:carrier")
        self.assertFalse(s["serverHeldKey"])

    def test_only_member_signature(self):
        s = agent.build_settlement_intent(1_000_000, "did:plc:carrier")
        srv = agent.authorize_settlement(s, {"origin": "server", "ref": "x"})
        self.assertTrue(srv.get("refused"))
        self.assertIn("G5", srv["reason"])
        mem = agent.authorize_settlement(s, {"origin": "member", "ref": "sig-9"})
        self.assertTrue(mem["signed"])

    def test_broadcast_needs_operator(self):
        s = agent.build_settlement_intent(1_000_000, "did:plc:carrier", operator_ref="op-1")
        self.assertEqual(s["state"], "executed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
