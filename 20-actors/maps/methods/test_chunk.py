#!/usr/bin/env python3
"""maps — kotoba-native chunk read + cross-read integration tests (ADR-2606064500). unittest.

Proves get_chunk over HTTP, and that all FOUR kotoba-native reads (chunk / search / reverse /
transit) compose over ONE ingested kotoba graph — the integration the per-read suites didn't
cover (each ingested its own dataset). Needs h3 (run under the project venv).

Run: python3 test_chunk.py   (auto-skips if h3 is absent)
"""
from __future__ import annotations
import json, threading, unittest, urllib.request

import chunk

try:
    import h3 as _h3
    _HAS_H3 = True
except Exception:
    _HAS_H3 = False

TOKEN = "member-did"
# Tokyo-anchor features.
FEATS = [
    ("f.station.tokyo", ":station", "Tokyo Station", 35.6812, 139.7671),
    ("f.bldg.marunouchi", ":building", "Marunouchi Building", 35.6809, 139.7644),
    ("f.bldg.shinmaru", ":building", "Shin-Marunouchi", 35.6820, 139.7639),
    ("f.airport.haneda", ":airport", "Tokyo Haneda", 35.5494, 139.7798),
]


def _post(url, body, token=None):
    h = {"content-type": "application/json"}
    if token:
        h["authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def _build_entities():
    import search
    ents = []
    for fid, label, name, lat, lon in FEATS:
        claims = [{"pred": "feature/label", "value": label},
                  {"pred": "feature/name", "value": name},
                  {"pred": "feature/lat", "value": str(lat)},
                  {"pred": "feature/lon", "value": str(lon)}]
        for r in (2, 4, 6, 8, 10, 12):
            claims.append({"pred": f"feature.cell/r{r}", "value": _h3.latlng_to_cell(lat, lon, r)})
        for t in sorted(search.name_tokens(name)):
            claims.append({"pred": "feature/name-token", "value": t})
        ents.append({"id": fid, "type": "maps-feature", "claims": claims})
    # one transit trip + two stop-times at Tokyo Station
    ents.append({"id": "trip.f.T1", "type": "transit-trip",
                 "claims": [{"pred": "transit.trip/route", "value": "ROUTE-M"},
                            {"pred": "transit.trip/headsign", "value": "Ogikubo"}]})
    for seq, dep in ((1, "08:00:30"), (2, "08:02:00")):
        ents.append({"id": f"stoptime.f.T1.{seq}", "type": "transit-stop-time",
                     "claims": [{"pred": "transit.stop-time/stop", "value": "f.station.tokyo"},
                                {"pred": "transit.stop-time/trip", "value": "trip.f.T1"},
                                {"pred": "transit.stop-time/departure-time", "value": dep},
                                {"pred": "transit.stop-time/sequence", "value": str(seq)}]})
    return {"entities": ents}


@unittest.skipUnless(_HAS_H3, "h3 not installed (run under the project venv)")
class TestChunk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from kotoba_local_server import serve
        cls.httpd = serve(0, TOKEN)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        _post(f"{cls.base}/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch", _build_entities(), TOKEN)
        cls.cells10 = [_h3.latlng_to_cell(lat, lon, 10) for _, _, _, lat, lon in FEATS]

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close()

    def test_chunk_groups_by_cell_and_label(self):
        res = chunk.get_chunk(self.base, self.cells10, lod=10)
        self.assertEqual(res["total"], 4)
        # each feature sits under the r10 cell it actually belongs to, keyed by its label
        for _, _, _, lat, lon in FEATS:
            cell = _h3.latlng_to_cell(lat, lon, 10)
            self.assertIn(cell, res["chunks"])
        tokyo_cell = _h3.latlng_to_cell(35.6812, 139.7671, 10)
        ids = {f["properties"]["id"] for f in res["chunks"][tokyo_cell].get(":station", [])}
        self.assertIn("f.station.tokyo", ids)

    def test_chunk_label_filter(self):
        res = chunk.get_chunk(self.base, self.cells10, lod=10, labels=["Building"])
        labels = {lab for by in res["chunks"].values() for lab in by}
        self.assertTrue(labels <= {":building"}, labels)
        self.assertGreaterEqual(res["total"], 2)

    def test_chunk_geometry_is_point_from_latlon(self):
        res = chunk.get_chunk(self.base, self.cells10, lod=10, labels=["Station"])
        cell = _h3.latlng_to_cell(35.6812, 139.7671, 10)
        feat = res["chunks"][cell][":station"][0]
        self.assertEqual(feat["geometry"]["type"], "Point")

    def test_chunk_coarse_lod_aggregates(self):
        cells8 = list({_h3.latlng_to_cell(lat, lon, 8) for _, _, _, lat, lon in FEATS})
        res = chunk.get_chunk(self.base, cells8, lod=8)
        self.assertEqual(res["total"], 4)

    def test_chunk_empty_cell(self):
        ocean = _h3.latlng_to_cell(0.0, -150.0, 10)
        res = chunk.get_chunk(self.base, [ocean], lod=10)
        self.assertEqual(res["total"], 0)

    def test_all_four_reads_compose_over_one_graph(self):
        import search, reverse, transit
        # 1. chunk — the cell read
        ch = chunk.get_chunk(self.base, self.cells10, lod=10)
        self.assertEqual(ch["total"], 4)
        # 2. name search — "tok" → the two Tokyo features
        names = {r["name"] for r in search.search_places(self.base, "tok")}
        self.assertEqual(names, {"Tokyo Station", "Tokyo Haneda"})
        # 3. reverse geocode — nearest to a point by Tokyo Station
        rg = reverse.reverse_geocode(self.base, 35.6813, 139.7672, res=10, ring=2)
        self.assertEqual(rg[0]["id"], "f.station.tokyo")
        # 4. transit — next departures at Tokyo Station
        deps = [d["departure"] for d in transit.next_departures_at_stop(self.base, "f.station.tokyo")]
        self.assertEqual(deps, ["08:00:30", "08:02:00"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
