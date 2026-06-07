#!/usr/bin/env python3
"""maps — kotoba read-surface readiness verifier tests (ADR-2606064500 R1). unittest.

Ingests a known dataset into the kotoba stand-in, then asserts verify_reads reports all four
reads green — and that an empty/ocean probe reports not-ready. Needs h3 (project venv).

Run: python3 test_verify.py   (auto-skips if h3 is absent)
"""
from __future__ import annotations
import json, threading, unittest, urllib.request

import verify

try:
    import h3 as _h3
    _HAS_H3 = True
except Exception:
    _HAS_H3 = False

TOKEN = "member-did"
FEATS = [
    ("f.station.tokyo", ":station", "Tokyo Station", 35.6812, 139.7671),
    ("f.bldg.marunouchi", ":building", "Marunouchi Building", 35.6809, 139.7644),
    ("f.airport.haneda", ":airport", "Tokyo Haneda", 35.5494, 139.7798),
]


def _post(url, body, token=None):
    h = {"content-type": "application/json"}
    if token:
        h["authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def _entities():
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
    ents.append({"id": "trip.f.T1", "type": "transit-trip",
                 "claims": [{"pred": "transit.trip/route", "value": "R"}]})
    ents.append({"id": "stoptime.f.T1.1", "type": "transit-stop-time",
                 "claims": [{"pred": "transit.stop-time/stop", "value": "f.station.tokyo"},
                            {"pred": "transit.stop-time/trip", "value": "trip.f.T1"},
                            {"pred": "transit.stop-time/departure-time", "value": "08:00:30"},
                            {"pred": "transit.stop-time/sequence", "value": "1"}]})
    return {"entities": ents}


@unittest.skipUnless(_HAS_H3, "h3 not installed (run under the project venv)")
class TestVerify(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from kotoba_local_server import serve
        cls.httpd = serve(0, TOKEN)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        _post(f"{cls.base}/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch", _entities(), TOKEN)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close()

    def test_all_reads_ready(self):
        rep = verify.verify_reads(self.base, lat=35.6812, lon=139.7671, res=10, ring=2,
                                  query="tok", stop_id="f.station.tokyo")
        self.assertTrue(rep["allOk"], rep)
        self.assertTrue(rep["chunk"]["ok"])
        self.assertTrue(rep["search"]["ok"])
        self.assertEqual(rep["reverse"]["nearest"], "f.station.tokyo")
        self.assertTrue(rep["transit"]["ok"])

    def test_ocean_probe_not_ready(self):
        rep = verify.verify_reads(self.base, lat=0.0, lon=-150.0, res=10, ring=2,
                                  query="zzqq", stop_id="nope")
        self.assertFalse(rep["allOk"])
        self.assertFalse(rep["chunk"]["ok"])
        self.assertFalse(rep["reverse"]["ok"])

    def test_endpoint_down_not_ready(self):
        rep = verify.verify_reads("http://127.0.0.1:1", lat=35.68, lon=139.77,
                                  query="tok", stop_id="f.station.tokyo")
        self.assertFalse(rep["allOk"])  # every read fails soft, none raises

    def test_report_shape(self):
        rep = verify.verify_reads(self.base, lat=35.6812, lon=139.7671, query="tok",
                                  stop_id="f.station.tokyo")
        for k in ("chunk", "search", "reverse", "transit", "allOk"):
            self.assertIn(k, rep)
        json.dumps(rep)  # serializable (CLI prints it)


if __name__ == "__main__":
    unittest.main(verbosity=2)
