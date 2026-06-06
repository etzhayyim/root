#!/usr/bin/env python3
"""maps — end-to-end HTTP loop test against the kotoba stand-in (ADR-2606064500 R1). stdlib.

Proves the maps↔kotoba WIRE contract end-to-end over real HTTP, before any live endpoint is
wired: it starts kotoba_local_server, pushes features through ingest.py's REAL push path
(Bearer auth = no-server-key §4), and reads them back with the EXACT AVET cell query the TS
adapter (kotoba-spatial.ts queryByCells) issues. The only stand-in is the kotoba engine; the
request/response shapes, the auth gate, and the AVET cell semantics are the production ones.

Run: python3 test_e2e_http.py   (h3-independent — uses a deterministic mock cell stamp)
"""
from __future__ import annotations
import json, math, threading, unittest, urllib.request

import ingest
from kotoba_local_server import serve

TOKEN = "test-operator-did-bearer"
CELL_RES = (2, 4, 6, 8, 10, 12)
FEATURES = [
    ("feature.station.tokyo", ":station", "Tokyo Station", 35.6812, 139.7671),
    ("feature.building.marunouchi-bldg", ":building", "Marunouchi Building", 35.6809, 139.7644),
    ("feature.airport.haneda", ":airport", "Tokyo Haneda", 35.5494, 139.7798),
]


def _mock_cell(lat, lon, res):
    size = 10.0 / (3 ** res)
    return f"r{res}/{math.floor(lat / size)}/{math.floor(lon / size)}"


def _batch():
    entities = []
    for fid, label, name, lat, lon in FEATURES:
        claims = [{"pred": "feature/label", "value": label},
                  {"pred": "feature/name", "value": name},
                  {"pred": "feature/lat", "value": str(lat)},
                  {"pred": "feature/lon", "value": str(lon)},
                  {"pred": "feature/sourcing", "value": ":representative"}]
        for r in CELL_RES:
            claims.append({"pred": f"feature.cell/r{r}", "value": _mock_cell(lat, lon, r)})
        entities.append({"id": fid, "type": "maps-feature", "label_en": name,
                         "claims": claims, "relations": []})
    return {"entities": entities}


def _post(url, body, token=None):
    headers = {"content-type": "application/json"}
    if token:
        headers["authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


class TestE2EHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = serve(0, TOKEN)  # port 0 = ephemeral
        cls.port = cls.httpd.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.t = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.t.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_1_ingest_refused_without_bearer(self):
        # no-server-key (§4): a write with no member/operator Bearer is rejected
        code, body = _post(f"{self.base}/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch", _batch())
        self.assertEqual(code, 401)

    def test_2_ingest_via_real_ingest_push_path(self):
        # exercises ingest.py's ACTUAL push_batch() code over HTTP, member-signed
        status, body = ingest.push_batch(_batch(), TOKEN, self.base)
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["ok"])
        self.assertEqual(json.loads(body)["ingested"], len(FEATURES))

    def test_3_avet_cell_query_roundtrip(self):
        # the EXACT request shape kotoba-spatial.ts queryByCells issues
        cell = _mock_cell(35.6812, 139.7671, 12)
        code, body = _post(f"{self.base}/xrpc/com.etzhayyim.apps.kotoba.graph.sparql", {
            "index": "avet",
            "predicate": "feature.cell/r12",
            "objects": [cell],
            "filter": {"predicate": "feature/label", "in": [":station"]},
            "limit": 500,
        })
        self.assertEqual(code, 200)
        ids = [e["id"] for e in body["entities"]]
        self.assertEqual(ids, ["feature.station.tokyo"])
        # the returned entity carries the claims the adapter's entityToRow materializes
        claims = {c["pred"]: c["value"] for c in body["entities"][0]["claims"]}
        self.assertEqual(claims["feature/label"], ":station")
        self.assertEqual(claims["feature/name"], "Tokyo Station")

    def test_4_label_filter_excludes_other_labels(self):
        # the station + the Marunouchi building share a coarse r2 cell; filtering to building
        # must return the building and EXCLUDE the station (the ∩ AVET(label) leg)
        cell = _mock_cell(35.6809, 139.7644, 2)
        code, body = _post(f"{self.base}/xrpc/com.etzhayyim.apps.kotoba.graph.sparql", {
            "index": "avet", "predicate": "feature.cell/r2", "objects": [cell],
            "filter": {"predicate": "feature/label", "in": [":building"]}, "limit": 500,
        })
        ids = {e["id"] for e in body["entities"]}
        self.assertIn("feature.building.marunouchi-bldg", ids)
        self.assertNotIn("feature.station.tokyo", ids)
        labels = {c["value"] for e in body["entities"]
                  for c in e["claims"] if c["pred"] == "feature/label"}
        self.assertEqual(labels, {":building"})

    def test_5_kg_entity_point_lookup(self):
        req = urllib.request.Request(
            f"{self.base}/xrpc/com.etzhayyim.apps.kotobase.kg.entity?id=feature.station.tokyo")
        with urllib.request.urlopen(req, timeout=5) as r:
            ent = json.loads(r.read())["entity"]
        self.assertEqual(ent["id"], "feature.station.tokyo")
        self.assertTrue(any(c["pred"] == "feature/name" for c in ent["claims"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
