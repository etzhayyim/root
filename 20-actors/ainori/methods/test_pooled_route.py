#!/usr/bin/env python3
"""test_pooled_route — pins ainori's pooled sequencing to the REUSED todoke route core.

The headline test (`test_parity_with_todoke`) is the proof of ADR-2606071500's reuse claim:
on a shared fixture, ainori's `sequence_stops` returns the SAME visiting order as todoke's
`plan_last_mile`. If anyone forks a second routing engine into ainori, this test breaks.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import pooled_route as pr  # noqa: E402

# the todoke core ainori reuses (same module object)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "todoke", "methods")))
import last_mile as todoke  # noqa: E402


def _fixture():
    # pedestrian-zone fixture so todoke.plan_last_mile's envelope accepts it
    return [
        todoke.Stop(0, 0.0, 0.0, "sidewalk"),
        todoke.Stop(1, 3.0, 0.0, "sidewalk"),
        todoke.Stop(2, 3.0, 3.0, "sidewalk"),
        todoke.Stop(3, 0.0, 3.0, "sidewalk"),
        todoke.Stop(4, 1.0, 1.0, "sidewalk"),
    ]


class Parity(unittest.TestCase):
    def test_parity_with_todoke(self):
        stops = _fixture()
        order_a, len_a = pr.sequence_stops(stops)
        order_t, len_t = todoke.plan_last_mile(stops, sae_level=4, commanded_mps=1.5)
        self.assertEqual(order_a, order_t)            # SAME engine, not a fork
        self.assertAlmostEqual(len_a, len_t, places=9)

    def test_reuses_todoke_primitives(self):
        # pooled_route imports the actual todoke Stop class (identity, not a copy)
        self.assertIs(pr.Stop, todoke.Stop)


class PooledRoute(unittest.TestCase):
    def test_origin_pinned_first(self):
        out = pr.pooled_route((0.0, 0.0), [
            {"id": 1, "x": 5.0, "y": 0.0}, {"id": 2, "x": 1.0, "y": 0.0}])
        self.assertEqual(out["order"][0], 0)          # carrier origin pinned
        self.assertEqual(out["occupancy"], 2)

    def test_vehicular_zone_sequences(self):
        # ainori uses road/arterial zones — sequencing works WITHOUT todoke's pedestrian envelope
        out = pr.pooled_route((0.0, 0.0), [
            {"id": 1, "x": 10.0, "y": 0.0, "zone": "expressway"},
            {"id": 2, "x": 2.0, "y": 0.0, "zone": "arterial"}])
        self.assertEqual(out["order"], [0, 2, 1])     # nearest-first sequencing
        self.assertGreater(out["lengthM"], 0)

    def test_empty(self):
        self.assertEqual(pr.sequence_stops([]), ([], 0.0))


class PlanPooledTrip(unittest.TestCase):
    def test_composes_route_and_cost_share(self):
        out = pr.plan_pooled_trip((0.0, 0.0), [
            {"id": 1, "x": 5.0, "y": 0.0}, {"id": 2, "x": 1.0, "y": 0.0}], 1_200_000)
        self.assertEqual(out["order"][0], 0)               # routing (todoke core)
        self.assertEqual(out["occupancy"], 2)
        self.assertEqual(out["costSharePerRiderMinor"], 600_000)   # cost_share split (no surge)

    def test_no_profit_invariant(self):
        # odd cost: per-rider rounds down; total collected ≤ real fuel/wear (carrier absorbs rest)
        out = pr.plan_pooled_trip((0.0, 0.0), [
            {"id": 1, "x": 5.0, "y": 0.0}, {"id": 2, "x": 1.0, "y": 0.0},
            {"id": 3, "x": 3.0, "y": 0.0}], 1_000_000)
        self.assertLessEqual(out["totalCollectedMinor"], out["fuelWearMinor"])

    def test_pooling_lowers_each_share(self):
        two = pr.plan_pooled_trip((0.0, 0.0), [{"id": 1, "x": 1.0, "y": 0.0},
                                               {"id": 2, "x": 2.0, "y": 0.0}], 1_200_000)
        three = pr.plan_pooled_trip((0.0, 0.0), [{"id": 1, "x": 1.0, "y": 0.0},
                                                 {"id": 2, "x": 2.0, "y": 0.0},
                                                 {"id": 3, "x": 3.0, "y": 0.0}], 1_200_000)
        self.assertLess(three["costSharePerRiderMinor"], two["costSharePerRiderMinor"])

    def test_uses_real_agent_cost_share(self):
        # composition, not duplication: pr.cost_share IS ainori agent's cost_share
        import agent as ainori_agent  # noqa: PLC0415
        self.assertIs(pr.cost_share, ainori_agent.cost_share)


if __name__ == "__main__":
    unittest.main(verbosity=2)
