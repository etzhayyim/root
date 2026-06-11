"""test_pipeline.py — danjo→kanae→yoro fiscal pipeline + charter-gate tests (stdlib unittest).

Run: python3 -m unittest 20-actors/kanae/methods/test_pipeline.py   (from repo root)
  or: cd 20-actors && python3 -m unittest kanae.methods.test_pipeline
"""

from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "20-actors"))

from danjo.methods.budget_ledger import build_ledger, load_seed, record_cid  # noqa: E402
from kanae.methods.assemble_flows import assemble, validate_edge, assert_non_adjudicating  # noqa: E402
from kanae.methods.project_yoro import project  # noqa: E402

SEED = os.path.join(ROOT, "20-actors", "danjo", "data", "gov-fiscal-seed.jp.json")
MEXT = "did:web:etzhayyim.com:actor:gov-jp-mext"


def _group(datoms, prefix):
    by_e = {}
    for d in datoms:
        if d["a"].startswith(prefix):
            import json
            by_e.setdefault(d["e"], {})[d["a"].split("/", 1)[1]] = json.loads(d["v_edn"])
    return list(by_e.values())


def _asof_ok(observed, asof):
    if not asof:
        return True
    if not observed:
        return True
    return str(observed) <= str(asof) + "T23:59:59.999Z"


class TestBudgetLedger(unittest.TestCase):
    def test_groups(self):
        ledger = build_ledger(load_seed(SEED))
        self.assertEqual(len(ledger["lines"]), 5)
        g24 = ledger["groups"]["JP-MEXT-EDUSCI|2024"]
        self.assertEqual(len(g24["appropriations"]), 1)
        self.assertEqual(len(g24["outlays"]), 2)

    def test_cid_deterministic(self):
        rec = {"recordId": "x", "fiscalYear": 2024, "sourceSensor": "jp_yosan", "amountLocal": 1}
        self.assertEqual(record_cid(rec), record_cid(dict(rec)))


class TestAssembleCharterGates(unittest.TestCase):
    def setUp(self):
        self.edges = assemble(build_ledger(load_seed(SEED)))

    def test_edges_assembled(self):
        self.assertEqual(len(self.edges), 5)

    def test_every_edge_valid(self):
        # G5 (≥2 CIDs), flowClass enum, required fields, G4 non-adjudicating — all enforced.
        for e in self.edges:
            validate_edge(e)
            self.assertGreaterEqual(len(e["sourceRecordCids"]), 2)
            self.assertIn(e["flowClass"], {"appropriation", "outlay"})

    def test_g10_aggregate_first_no_named_party(self):
        # No endpoint asserts a named private party (no publiclyNamedBasis fabricated).
        for e in self.edges:
            self.assertNotIn("publiclyNamedBasis", e["fromEndpoint"])
            self.assertNotIn("publiclyNamedBasis", e["toEndpoint"])

    def test_g4_verdict_token_rejected(self):
        poisoned = dict(self.edges[0])
        poisoned["fromEndpoint"] = dict(poisoned["fromEndpoint"], label="不正 appropriation")
        with self.assertRaises(ValueError):
            assert_non_adjudicating(poisoned)

    def test_g5_single_cid_rejected(self):
        bad = dict(self.edges[0], sourceRecordCids=["only-one"])
        with self.assertRaises(ValueError):
            validate_edge(bad)


class TestYoroProjection(unittest.TestCase):
    def setUp(self):
        self.datoms = project(assemble(build_ledger(load_seed(SEED))))

    def test_mext_incoming_outgoing(self):
        flows = _group(self.datoms, ":yoro.fiscal/")
        incoming = [f for f in flows if f["to"] == MEXT]
        outgoing = [f for f in flows if f["from"] == MEXT]
        # 2 appropriations into MEXT (FY2023 + FY2024); 3 outlays out (1 FY2023 + 2 FY2024)
        self.assertEqual(len(incoming), 2)
        self.assertEqual(len(outgoing), 3)

    def test_mext_has_profile(self):
        profiles = _group(self.datoms, ":yoro.profile/")
        self.assertTrue(any(p["did"] == MEXT for p in profiles))

    def test_asof_time_travel(self):
        flows = _group(self.datoms, ":yoro.fiscal/")
        # current: 2 in / 3 out
        cur_in = [f for f in flows if f["to"] == MEXT]
        self.assertEqual(len(cur_in), 2)
        # as-of 2023-12-31: only the FY2023 appropriation (observed 2023-03-28) is visible
        past_in = [f for f in flows if f["to"] == MEXT and _asof_ok(f.get("observedAt"), "2023-12-31")]
        self.assertEqual(len(past_in), 1)
        self.assertEqual(past_in[0]["fiscalYear"], 2023)
        # as-of 2022-01-01: nothing observed yet
        none_in = [f for f in flows if f["to"] == MEXT and _asof_ok(f.get("observedAt"), "2022-01-01")]
        self.assertEqual(len(none_in), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
