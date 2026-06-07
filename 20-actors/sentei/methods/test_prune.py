"""test_prune.py — sentei 剪定 structural-invariant tests (stdlib unittest, ADR-2606072000).

Run: python3 -m unittest 20-actors/sentei/methods/test_prune.py
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from prune import (  # noqa: E402
    prune, regraft, apply_log, assert_no_verdict, to_datoms, PRUNE_ACTIONS,
)

AT = "2026-06-07T20:00:00.000Z"
COUNCIL = "did:web:etzhayyim.com:council#5of7"
MANIFESTED = {"id": "kanae.fundFlowEdge:jp-mext-2024-outlay", "manifested": True}
BUD = {"id": "kanae.fundFlowEdge:jp-mext-2025-draft", "manifested": False}


class TestG1NoPriorRestraint(unittest.TestCase):
    def test_cannot_prune_unmanifested_branch(self):
        # The core invariant: the Council cannot stop a branch before it grows.
        with self.assertRaises(ValueError):
            prune(BUD, "quarantine", "anything", COUNCIL, at=AT, council_level=7)

    def test_can_prune_after_it_manifests(self):
        p = prune(MANIFESTED, "quarantine", "G10 review", COUNCIL, at=AT, council_level=6)
        self.assertEqual(p["action"], "quarantine")
        self.assertEqual(apply_log([p]), {MANIFESTED["id"]: "quarantine"})


class TestG2AppendOnly(unittest.TestCase):
    def test_prune_appends_never_deletes(self):
        p = prune(MANIFESTED, "retract", "figure shown false", COUNCIL, at=AT, council_level=6)
        # the event is data; folding it yields state, the branch id still exists in history
        self.assertEqual(p["kind"], "prune")
        self.assertIn(MANIFESTED["id"], apply_log([p]))

    def test_as_of_time_travel_over_prune_history(self):
        p = prune(MANIFESTED, "quarantine", "g10", COUNCIL, at="2026-06-07T20:00:00.000Z", council_level=6)
        r = regraft(p, COUNCIL, at="2026-06-08T09:00:00.000Z")
        self.assertEqual(apply_log([p, r])[MANIFESTED["id"]], "live")              # current: healed
        self.assertEqual(apply_log([p, r], as_of="2026-06-07")[MANIFESTED["id"]], "quarantine")  # past: pruned
        self.assertEqual(apply_log([p, r], as_of="2026-06-05"), {})                # before: nothing yet


class TestG3GrowthUnstoppable(unittest.TestCase):
    def test_no_halt_or_delete_action(self):
        for bad in ("delete", "halt-organism", "prior-restraint", "verdict"):
            self.assertNotIn(bad, PRUNE_ACTIONS)
            with self.assertRaises(ValueError):
                prune(MANIFESTED, bad, "x", COUNCIL, at=AT, council_level=7)


class TestG4G7TransparentCare(unittest.TestCase):
    def test_verdict_token_rejected(self):
        with self.assertRaises(ValueError):
            assert_no_verdict("this branch is 違法 and the awardee is guilty")
        with self.assertRaises(ValueError):
            prune(MANIFESTED, "revoke", "punish the 犯罪", COUNCIL, at=AT, council_level=7)

    def test_basis_required(self):
        with self.assertRaises(ValueError):
            prune(MANIFESTED, "quarantine", "   ", COUNCIL, at=AT, council_level=6)

    def test_non_adjudicating_flag(self):
        p = prune(MANIFESTED, "quarantine", "g10 review", COUNCIL, at=AT, council_level=6)
        self.assertTrue(p["nonAdjudicating"])


class TestG5NoServerKey(unittest.TestCase):
    def test_server_cannot_sign_prune(self):
        with self.assertRaises(ValueError):
            prune(MANIFESTED, "quarantine", "g10", "server", at=AT, council_level=7)

    def test_prune_serverheldkey_false(self):
        p = prune(MANIFESTED, "quarantine", "g10", COUNCIL, at=AT, council_level=6)
        self.assertFalse(p["serverHeldKey"])


class TestCouncilFloorAndVote(unittest.TestCase):
    def test_invariant_adjacent_needs_lv7(self):
        with self.assertRaises(ValueError):
            prune(MANIFESTED, "rollback", "§2(a) hit", COUNCIL, at=AT, council_level=6, invariant_adjacent=True)
        ok = prune(MANIFESTED, "rollback", "§2(a) hit", COUNCIL, at=AT, council_level=7, invariant_adjacent=True)
        self.assertEqual(ok["councilLevel"], 7)

    def test_contested_prune_needs_majority(self):
        with self.assertRaises(ValueError):
            prune(MANIFESTED, "quarantine", "contested", COUNCIL, at=AT, council_level=6,
                  contested_vote={"yes": 2, "no": 5})
        ok = prune(MANIFESTED, "quarantine", "contested", COUNCIL, at=AT, council_level=6,
                   contested_vote={"yes": 6, "no": 1})
        self.assertEqual(ok["action"], "quarantine")


class TestG6Reversible(unittest.TestCase):
    def test_regraft_heals(self):
        p = prune(MANIFESTED, "quarantine", "mistaken cut", COUNCIL, at=AT, council_level=6)
        r = regraft(p, COUNCIL, at="2026-06-09T00:00:00.000Z")
        self.assertEqual(r["kind"], "regraft")
        self.assertEqual(apply_log([p, r])[MANIFESTED["id"]], "live")

    def test_server_cannot_regraft(self):
        p = prune(MANIFESTED, "quarantine", "x", COUNCIL, at=AT, council_level=6)
        with self.assertRaises(ValueError):
            regraft(p, "server", at=AT)


class TestDatomSerialization(unittest.TestCase):
    def test_to_datoms_namespace(self):
        p = prune(MANIFESTED, "quarantine", "g10", COUNCIL, at=AT, council_level=6)
        datoms = to_datoms(p)
        self.assertTrue(all(d["a"].startswith(":sentei.prune/") for d in datoms))
        self.assertTrue(any(d["a"] == ":sentei.prune/action" for d in datoms))


if __name__ == "__main__":
    unittest.main(verbosity=2)
