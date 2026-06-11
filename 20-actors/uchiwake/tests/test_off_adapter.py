#!/usr/bin/env python3
"""uchiwake 内訳 — Open Food Facts bulk-ingest adapter tests. ADR-2606081800."""
from __future__ import annotations
import json
import sys
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "methods"))
sys.path.insert(0, str(ROOT / "methods" / "adapters"))

import openfoodfacts as OFF  # noqa: E402
from uchiwake_edn import gtin_check_digit_ok  # noqa: E402

SAMPLE = ROOT / "data" / "ingest" / "openfoodfacts.sample.json"


class TestOffAdapter(unittest.TestCase):
    def setUp(self):
        self.records = json.loads(SAMPLE.read_text(encoding="utf-8"))
        self.datoms, self.stats = OFF.normalize_dataset(self.records)

    def test_bad_gtin_record_skipped(self):
        # 4 records in, 1 has a wrong check digit → 3 admitted, 1 skipped
        self.assertEqual(self.stats["products_ok"], 3)
        self.assertEqual(self.stats["skipped_bad_gtin"], 1)

    def test_products_keyed_on_normalized_gtin14(self):
        prods = [d for d in self.datoms if ":product/id" in d]
        self.assertEqual(len(prods), 3)
        for p in prods:
            self.assertEqual(len(p[":product/gtin"]), 14)
            self.assertTrue(gtin_check_digit_ok(p[":product/gtin"]))
            self.assertEqual(p[":product/sourcing"], ":representative")  # OFF is crowd-sourced

    def test_ingredients_become_bom_edges_with_mass(self):
        edges = [d for d in self.datoms if ":bom.edge/id" in d]
        self.assertTrue(edges)
        # Nutella sugar edge carries the 56% estimate
        sugar = [e for e in edges if e[":bom.edge/parent"] == "gtin.03017620422003"
                 and e[":bom.edge/child"] == "mat.sugar"]
        self.assertEqual(len(sugar), 1)
        self.assertAlmostEqual(sugar[0][":bom.edge/qty"], 56.0)
        self.assertEqual(sugar[0][":bom.edge/qty-unit"], "%mass")

    def test_known_ingredients_map_to_canonical_materials(self):
        mat_ids = {d[":material/id"] for d in self.datoms if ":material/id" in d}
        for canon in ("mat.sugar", "mat.cocoa", "mat.palm-oil", "mat.water", "mat.co2", "mat.milk-powder"):
            self.assertIn(canon, mat_ids)

    def test_materials_deduped_across_products(self):
        mats = [d for d in self.datoms if ":material/id" in d]
        ids = [d[":material/id"] for d in mats]
        self.assertEqual(len(ids), len(set(ids)))  # sugar appears in all 3, emitted once

    def test_output_is_valid_edn_loadable(self):
        from uchiwake_edn import _tokens, _parse  # noqa: E402
        edn = OFF._to_edn(self.datoms)
        parsed = _parse(_tokens(edn))
        self.assertIsInstance(parsed, list)
        self.assertEqual(len([r for r in parsed if isinstance(r, dict) and ":product/id" in r]), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
