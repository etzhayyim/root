#!/usr/bin/env python3
"""maps — kotoba-native reverse-geocode tests (ADR-2606064500 R2). stdlib unittest.

haversine is pure (always tested). The cell+ring e2e against the kotoba stand-in needs h3
(run under the project venv) — it ingests cell-stamped features then resolves the nearest.

Run: python3 test_reverse.py   (e2e auto-skips if h3 is absent)
"""
from __future__ import annotations
import json, threading, unittest, urllib.request

import reverse

TOKEN = "member-did"
# Tokyo Station vicinity + Haneda (~14 km south).
FEATS = [
    ("f.station.tokyo", ":station", "Tokyo Station", 35.6812, 139.7671),
    ("f.bldg.marunouchi", ":building", "Marunouchi Building", 35.6809, 139.7644),
    ("f.bldg.shinmaru", ":building", "Shin-Marunouchi", 35.6820, 139.7639),
    ("f.airport.haneda", ":airport", "Tokyo Haneda", 35.5494, 139.7798),
]


class TestHaversine(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(reverse.haversine_m(35.0, 139.0, 35.0, 139.0), 0.0)

    def test_known_distance_tokyo_haneda(self):
        d = reverse.haversine_m(35.6812, 139.7671, 35.5494, 139.7798)  # ~14.7 km
        self.assertAlmostEqual(d, 14_700, delta=500)

    def test_one_degree_lat(self):
        d = reverse.haversine_m(0.0, 0.0, 1.0, 0.0)  # ~111.2 km
        self.assertAlmostEqual(d, 111_195, delta=200)

    def test_monotonic(self):
        near = reverse.haversine_m(35.6812, 139.7671, 35.6809, 139.7644)
        far = reverse.haversine_m(35.6812, 139.7671, 35.5494, 139.7798)
        self.assertLess(near, far)

    def test_no_h3_returns_empty(self):
        # reverse_geocode degrades to [] without h3 (or endpoint down); ranker stays pure
        import importlib
        try:
            import h3  # noqa: F401
            self.skipTest("h3 present — covered by the e2e suite")
        except Exception:
            self.assertEqual(reverse.reverse_geocode("http://127.0.0.1:1", 35.68, 139.77), [])


try:
    import h3 as _h3
    _HAS_H3 = True
except Exception:
    _HAS_H3 = False


def _post(url, body, token=None):
    h = {"content-type": "application/json"}
    if token:
        h["authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


@unittest.skipUnless(_HAS_H3, "h3 not installed (run under the project venv for the e2e suite)")
class TestReverseE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from kotoba_local_server import serve
        cls.httpd = serve(0, TOKEN)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        # ingest cell-stamped features (res 2..12 like production)
        ents = []
        for fid, label, name, lat, lon in FEATS:
            claims = [{"pred": "feature/label", "value": label},
                      {"pred": "feature/name", "value": name},
                      {"pred": "feature/lat", "value": str(lat)},
                      {"pred": "feature/lon", "value": str(lon)}]
            for r in (2, 4, 6, 8, 10, 12):
                claims.append({"pred": f"feature.cell/r{r}", "value": _h3.latlng_to_cell(lat, lon, r)})
            ents.append({"id": fid, "type": "maps-feature", "claims": claims})
        _post(f"{cls.base}/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch", {"entities": ents}, TOKEN)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close()

    def test_nearest_is_tokyo_station(self):
        # query a point ~30 m from Tokyo Station
        rows = reverse.reverse_geocode(self.base, 35.6813, 139.7672, res=10, ring=2)
        self.assertTrue(rows)
        self.assertEqual(rows[0]["id"], "f.station.tokyo")
        self.assertLess(rows[0]["distanceM"], 60)
        # results are sorted nearest-first
        self.assertEqual([r["distanceM"] for r in rows], sorted(r["distanceM"] for r in rows))

    def test_label_filter(self):
        rows = reverse.reverse_geocode(self.base, 35.6812, 139.7660, res=10, ring=3, labels=["building"])
        self.assertTrue(rows)
        self.assertTrue(all(r["label"] == ":building" for r in rows))
        self.assertIn(rows[0]["id"], {"f.bldg.marunouchi", "f.bldg.shinmaru"})

    def test_limit(self):
        rows = reverse.reverse_geocode(self.base, 35.6812, 139.7660, res=8, ring=3, limit=1)
        self.assertEqual(len(rows), 1)

    def test_far_point_excludes_distant_haneda(self):
        # a tight ring around Tokyo Station must NOT pull in Haneda (~14 km away)
        rows = reverse.reverse_geocode(self.base, 35.6812, 139.7671, res=10, ring=2)
        self.assertNotIn("f.airport.haneda", {r["id"] for r in rows})

    def test_ocean_empty(self):
        self.assertEqual(reverse.reverse_geocode(self.base, 0.0, -150.0, res=10, ring=2), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
