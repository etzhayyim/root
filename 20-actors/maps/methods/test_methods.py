#!/usr/bin/env python3
"""maps — kotoba-native methods tests (ADR-2606064500). stdlib unittest, no deps.

Run: python3 methods/test_methods.py
"""
from __future__ import annotations
import json, os, pathlib, tempfile, unittest

import analyze
import ingest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SEED = ROOT / "data" / "seed-spatial-graph.kotoba.edn"
SAMPLE = ROOT / "data" / "ingest" / "sample-vertex-spatial.json"


class TestAnalyze(unittest.TestCase):
    def setUp(self):
        rows = analyze.load_edn(SEED)
        self.features, self.rels, self.aliases = analyze.classify(rows)
        self.a = analyze.analyze(self.features, self.rels, self.aliases)

    def test_seed_classifies(self):
        self.assertGreaterEqual(len(self.features), 10)
        self.assertGreaterEqual(len(self.rels), 1)
        self.assertGreaterEqual(len(self.aliases), 1)

    def test_every_feature_has_sourcing(self):
        # G3 — sourcing honesty is mandatory on every feature
        for f in self.features.values():
            self.assertIn(":feature/sourcing", f, f.get(":feature/id"))

    def test_labels_collapsed(self):
        # the 51 legacy labels collapse onto :feature/label keywords
        self.assertIn(":building", self.a["label_count"])
        self.assertIn(":station", self.a["label_count"])

    def test_coverage_fraction_is_honest_and_tiny(self):
        # res-6 fraction must be a real (tiny) number, never fabricated as "covered"
        den = analyze._h3_cells_at_res(6)
        self.assertEqual(den, 14_117_882)
        self.assertGreater(len(self.a["cells_r6"]), 0)
        self.assertLess(len(self.a["cells_r6"]) / den, 1e-3)

    def test_bbox_and_anchor(self):
        self.assertIsNotNone(self.a["bbox"])
        self.assertIsNotNone(self.a["densest"])
        # anchor density hot spot is at Tokyo Station vicinity
        (la, lo), n = self.a["densest"]
        self.assertAlmostEqual(la, 35.68, delta=0.1)
        self.assertAlmostEqual(lo, 139.76, delta=0.1)

    def test_report_renders(self):
        rep = analyze.render_report(self.features, self.a)
        self.assertIn("coverage report", rep)
        self.assertIn("res-6", rep)
        dat = analyze.render_datoms(self.a)
        self.assertIn(":coverage/feature-count", dat)
        self.assertIn(":coverage/derived true", dat)


class TestIngest(unittest.TestCase):
    def setUp(self):
        self.export = json.loads(SAMPLE.read_text(encoding="utf-8"))

    def test_label_map(self):
        self.assertEqual(ingest._label("Building"), ":building")
        self.assertEqual(ingest._label("Station"), ":station")
        self.assertEqual(ingest._label("LegalEntity"), ":legal-entity")
        # unknown label degrades to a kebab keyword, never crashes
        self.assertEqual(ingest._label("WeirdThing"), ":weirdthing")

    def test_normalize_row(self):
        row = self.export["rows"][0]  # Marunouchi Building
        f = ingest.normalize_row(row)
        self.assertEqual(f[":feature/label"], ":building")
        self.assertEqual(f[":feature/height-m"], 179.0)
        self.assertEqual(f[":feature/levels"], 37)
        self.assertEqual(f[":feature/sourcing"], ":representative")  # G3
        self.assertIn(":feature/geometry", f)  # GeoJSON survives as JSON string
        json.loads(f[":feature/geometry"])     # and is valid JSON

    def test_props_bag_excludes_promoted_keys(self):
        row = self.export["rows"][0]
        f = ingest.normalize_row(row)
        # heightM/levels/geometry are promoted to first-class attrs, not left in the bag
        if ":feature/props" in f:
            bag = json.loads(f[":feature/props"])
            self.assertNotIn("heightM", bag)
            self.assertNotIn("levels", bag)
            self.assertNotIn("geometry", bag)

    def test_normalize_batch(self):
        feats, stamped, unstamped = ingest.normalize(self.export)
        self.assertEqual(len(feats), 4)
        # without h3 installed, lat/lon features await TS-adapter stamping (honest)
        self.assertEqual(stamped + unstamped, 4)

    def test_to_kg_batch_shape(self):
        feats, _, _ = ingest.normalize(self.export)
        batch = ingest.to_kg_batch(feats)
        self.assertIn("entities", batch)
        e = batch["entities"][0]
        for key in ("id", "type", "label_en", "claims", "relations"):
            self.assertIn(key, e)
        self.assertEqual(e["type"], "maps-feature")
        # :feature/id is the entity id, never duplicated into a claim
        self.assertFalse(any(c["pred"] == "feature/id" for c in e["claims"]))

    def test_push_gate_refuses_without_operator(self):
        # G7 — invoke ingest.main(--push) with the gate OFF and assert it sys.exit()s with the
        # G7 refusal BEFORE any network call (deleting the gate would fail this test).
        old = os.environ.pop("MAPS_OPERATOR_GATE", None)
        try:
            with self.assertRaises(SystemExit) as cm:
                ingest.main(["ingest.py", "--export", str(SAMPLE), "--push"])
            self.assertIn("G7", str(cm.exception))
        finally:
            if old is not None:
                os.environ["MAPS_OPERATOR_GATE"] = old

    def test_push_gate_refuses_without_auth_even_when_gated(self):
        # with the gate ON but no KOTOBA_AUTH/ENDPOINT, --push still refuses (G4 no-server-key)
        old_g = os.environ.get("MAPS_OPERATOR_GATE")
        old_a = os.environ.pop("KOTOBA_AUTH", None)
        old_e = os.environ.pop("KOTOBA_ENDPOINT", None)
        os.environ["MAPS_OPERATOR_GATE"] = "1"
        try:
            with self.assertRaises(SystemExit) as cm:
                ingest.main(["ingest.py", "--export", str(SAMPLE), "--push"])
            self.assertIn("no server key", str(cm.exception).lower())
        finally:
            if old_g is None:
                os.environ.pop("MAPS_OPERATOR_GATE", None)
            else:
                os.environ["MAPS_OPERATOR_GATE"] = old_g
            if old_a is not None:
                os.environ["KOTOBA_AUTH"] = old_a
            if old_e is not None:
                os.environ["KOTOBA_ENDPOINT"] = old_e


if __name__ == "__main__":
    unittest.main(verbosity=2)
