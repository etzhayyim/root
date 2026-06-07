#!/usr/bin/env python3
"""tsubasa 翼 — test harness (stdlib unittest; no kotoba host needed).

Verifies the structural invariants of ADR-2606072800:
  G4 emissions-honest      — total cost includes baggage; co2Kg on every result; greenest first-class
  G1 no-affiliate-no-inflow — affiliate params stripped; handoff has no commission/tithe, member principal
  G3 anti-dark             — no urgency / price-will-rise field in any output
"""
import unittest

import agent


def _fare(fid, fare, bag=0, co2=100.0, dur=120, carrier="NH",
          url="https://nh.example/book?flt=1"):
    return {"fareId": fid, "origin": "HND", "destination": "ITM", "departDate": "2026-07-01",
            "carrier": carrier, "stops": 0, "durationMin": dur, "fareMinor": fare,
            "baggageMinor": bag, "currency": "JPY", "co2Kg": co2,
            "cabin": "economy", "bookUrl": url, "sourcing": "representative"}


class TotalCost(unittest.TestCase):
    def test_includes_baggage(self):
        self.assertEqual(agent.total_cost_minor(_fare("f", 10000, bag=2000)), 12000)


class Search(unittest.TestCase):
    def setUp(self):
        self.fares = [
            _fare("cheap-dirty", 8000, bag=0, co2=300, dur=130),
            _fare("pricey-green", 12000, bag=0, co2=90, dur=125),
            _fare("mid", 10000, bag=1000, co2=150, dur=120),
            _fare("other", 5000, co2=10, dur=60),  # different route below
        ]
        self.fares[-1]["destination"] = "CTS"  # not HND->ITM

    def test_filters_route_and_date(self):
        out = agent.search_fares("HND", "ITM", "2026-07-01", self.fares)
        self.assertEqual(len(out), 3)  # the CTS one excluded

    def test_every_result_has_emissions(self):
        out = agent.search_fares("HND", "ITM", "2026-07-01", self.fares)
        for r in out:
            self.assertIn("co2Kg", r)            # G4: emissions on EVERY option
            self.assertIn("totalMinor", r)

    def test_sort_total_default(self):
        out = agent.search_fares("HND", "ITM", "2026-07-01", self.fares)
        self.assertEqual(out[0]["fareId"], "cheap-dirty")   # 8000 total

    def test_sort_emissions(self):
        out = agent.search_fares("HND", "ITM", "2026-07-01", self.fares, sort="emissions")
        self.assertEqual(out[0]["fareId"], "pricey-green")  # 90 kg CO2 first

    def test_no_urgency_field(self):
        out = agent.search_fares("HND", "ITM", "2026-07-01", self.fares)
        for r in out:
            for k in r:
                self.assertNotIn("urgen", k.lower())
                self.assertNotIn("scarcit", k.lower())
                self.assertNotIn("willrise", k.lower().replace("_", ""))


class Compare(unittest.TestCase):
    def test_greenest_is_first_class(self):
        fares = [_fare("a", 8000, co2=300), _fare("b", 12000, co2=90), _fare("c", 9000, co2=150, dur=90)]
        out = agent.compare(fares)
        self.assertEqual(out["cheapest"]["fareId"], "a")
        self.assertEqual(out["greenest"]["fareId"], "b")   # emissions never hidden (G4)
        self.assertEqual(out["fastest"]["fareId"], "c")

    def test_empty(self):
        self.assertEqual(agent.compare([]), {"cheapest": None, "greenest": None, "fastest": None})


class Handoff(unittest.TestCase):
    def test_affiliate_stripped(self):
        f = _fare("f", 10000, url="https://nh.example/book?flt=1&aff=skyscanner&utm_source=meta&tag=x")
        out = agent.self_book_handoff(f)
        self.assertIn("flt=1", out["bookUrl"])
        self.assertNotIn("aff=", out["bookUrl"])
        self.assertNotIn("utm_source", out["bookUrl"])
        self.assertNotIn("tag=", out["bookUrl"])

    def test_no_commission_no_tithe_member_principal(self):
        out = agent.self_book_handoff(_fare("f", 10000))
        self.assertEqual(out["commissionMinor"], 0)   # G1
        self.assertEqual(out["titheMinor"], 0)
        self.assertEqual(out["principal"], "member")
        self.assertEqual(out["mode"], "self-book-handoff")


if __name__ == "__main__":
    unittest.main(verbosity=2)
