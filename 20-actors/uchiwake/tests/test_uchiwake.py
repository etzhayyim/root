#!/usr/bin/env python3
"""uchiwake 内訳 — invariant + correctness tests (stdlib unittest). ADR-2606081800."""
from __future__ import annotations
import os
import sys
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "methods"))

from uchiwake_edn import (  # noqa: E402
    load_edn, classify, normalize_gtin, gtin_check_digit_ok,
)
import analyze as A  # noqa: E402
import crosscheck as X  # noqa: E402

SEED = ROOT / "data" / "seed-products.kotoba.edn"
SCHEMA = ROOT.parent.parent / "00-contracts" / "schemas" / "product-bom-ontology.kotoba.edn"


class TestSeedLoads(unittest.TestCase):
    def setUp(self):
        self.rows = load_edn(SEED)
        self.g = classify(self.rows)

    def test_nonempty(self):
        self.assertTrue(self.g['products'])
        self.assertTrue(self.g['materials'])
        self.assertTrue(self.g['bom'])

    def test_schema_loads(self):
        s = load_edn(SCHEMA)
        self.assertIsInstance(s, dict)
        self.assertEqual(s.get(':schema/adr'), "2606081800")

    def test_every_node_has_sourcing(self):
        """G5: every node/edge carries an explicit :*/sourcing keyword."""
        for r in self.rows:
            if not isinstance(r, dict):
                continue
            srcing = [v for k, v in r.items() if k.endswith('/sourcing')]
            self.assertTrue(srcing, f"missing sourcing on {r}")
            for v in srcing:
                self.assertIn(v, (':authoritative', ':representative', ':synthesized'))


class TestGtin(unittest.TestCase):
    def test_normalize_pads_to_14(self):
        self.assertEqual(normalize_gtin("5449000000996"), "05449000000996")
        self.assertEqual(len(normalize_gtin("5449000000996")), 14)

    def test_real_gtin_check_digits_valid(self):
        # Coca-Cola 330ml + Nutella 750g — real public EAN-13s with valid check digits.
        self.assertTrue(gtin_check_digit_ok("5449000000996"))
        self.assertTrue(gtin_check_digit_ok("3017620422003"))

    def test_bad_check_digit_rejected(self):
        self.assertFalse(gtin_check_digit_ok("5449000000997"))

    def test_seed_gtins_valid(self):
        g = classify(load_edn(SEED))
        for pid, p in g['products'].items():
            gt = p.get(':product/gtin')
            if gt:
                self.assertTrue(gtin_check_digit_ok(gt), f"{pid} GTIN check digit invalid: {gt}")


class TestBomIntegrity(unittest.TestCase):
    def setUp(self):
        self.g = classify(load_edn(SEED))

    def test_bom_edges_reference_known_nodes(self):
        known = set(self.g['products']) | set(self.g['parts']) | set(self.g['materials'])
        for e in self.g['bom']:
            self.assertIn(e[':bom.edge/parent'], known, f"dangling parent {e}")
            self.assertIn(e[':bom.edge/child'], known, f"dangling child {e}")

    def test_criticality_bounded(self):
        for e in self.g['bom']:
            c = e.get(':bom.edge/criticality')
            if c is not None:
                self.assertGreaterEqual(c, 0.0)
                self.assertLessEqual(c, 1.0)

    def test_materials_reachable_from_products(self):
        """Every product must decompose down to at least one raw material (BOM closure)."""
        child_idx = A._bom_children_index(self.g['bom'])
        for pid in self.g['products']:
            mats = A._all_materials_reachable(pid, child_idx)
            self.assertTrue(mats, f"product {pid} reaches no raw material")


class TestOwnershipRollup(unittest.TestCase):
    def setUp(self):
        self.g = classify(load_edn(SEED))
        self.idx = {o[':company.ownership/child']: o[':company.ownership/parent']
                    for o in self.g['ownership']}

    def test_subsidiary_rolls_to_ultimate_parent(self):
        # sony-semicon → sony ; ferrero → ferrero-intl
        self.assertEqual(A._resolve_ultimate_parent("org.corp.jp.sony-semicon", self.idx),
                         "org.corp.jp.sony")
        self.assertEqual(A._resolve_ultimate_parent("org.corp.it.ferrero", self.idx),
                         "org.corp.lu.ferrero-intl")

    def test_unowned_company_is_its_own_parent(self):
        self.assertEqual(A._resolve_ultimate_parent("org.corp.tw.tsmc", self.idx),
                         "org.corp.tw.tsmc")

    def test_rollup_terminates_on_cycle(self):
        cyc = {"a": "b", "b": "a"}
        # must not infinite-loop; returns some node within depth guard
        self.assertIn(A._resolve_ultimate_parent("a", cyc), ("a", "b"))


class TestAnalyzeRuns(unittest.TestCase):
    def test_analyze_produces_report_and_derived(self):
        md, derived = A.analyze(SEED)
        self.assertIn("uchiwake", md)
        self.assertIn("Material dependence", md)
        self.assertTrue(derived)
        for d in derived:
            self.assertTrue(d.get(':concentration/derived'))  # G5: flagged derived

    def test_g2_no_target_framing(self):
        """G2: report is framed as resilience, never a target-list."""
        md, _ = A.analyze(SEED)
        self.assertIn("RESILIENCE", md)
        self.assertNotIn("target-list,", md.replace("never a target-list", ""))


class TestCrosscheck(unittest.TestCase):
    def setUp(self):
        self.s = X.crosscheck()

    def test_kabuto_seed_resolves(self):
        """The kabuto seed must be findable and non-trivial for the crosscheck to mean anything."""
        self.assertTrue(self.s['kabuto_available'])
        self.assertGreater(self.s['kabuto_company_count'], 1000)

    def test_linkage_is_measured_and_bounded(self):
        self.assertGreaterEqual(self.s['linkage_pct'], 0.0)
        self.assertLessEqual(self.s['linkage_pct'], 100.0)
        # real wiring exists: brand-owner/supplier/operator/carrier link to real kabuto ids
        self.assertGreater(self.s['distinct_resolved'], 0)

    def test_subsidiary_rollup_recovers_a_link(self):
        """G5/子会社: sony-semicon is absent from kabuto but its ultimate parent sony resolves."""
        recovered = {r['ref'] for r in self.s['rollup_recovered']}
        self.assertIn("org.corp.jp.sony-semicon", recovered)

    def test_unresolved_are_reported_not_hidden(self):
        # honest gap surfacing: Coca-Cola / Ferrero are not in the kabuto seed
        self.assertIn("org.corp.us.coca-cola", self.s['unresolved'])

    def test_reverse_coverage_is_measured_with_worklist(self):
        rev = self.s.get('reverse')
        self.assertIsNotNone(rev)
        # honest: product-BOM layer covers only a small fraction of kabuto's universe
        self.assertGreater(rev['kabuto_supply_companies'], 50)
        self.assertGreaterEqual(rev['reverse_pct'], 0.0)
        self.assertLess(rev['reverse_pct'], 100.0)
        # a worklist of uncovered high-centrality suppliers must be produced + sorted desc
        self.assertTrue(rev['worklist'])
        degs = [w['supply_out_degree'] for w in rev['worklist']]
        self.assertEqual(degs, sorted(degs, reverse=True))


class TestExpandedSeed(unittest.TestCase):
    def test_milk_powder_reachable_from_kitkat(self):
        g = classify(load_edn(SEED))
        idx = A._bom_children_index(g['bom'])
        mats = A._all_materials_reachable("gtin.07613035044289", idx)
        self.assertIn("mat.milk-powder", mats)


if __name__ == '__main__':
    unittest.main(verbosity=2)
