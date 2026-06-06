#!/usr/bin/env python3
"""maps bulk-ingest — kotoba substrate-writer tests (ADR-2606064500 R2). stdlib unittest.

Run: python3 test_kotoba_substrate.py
"""
from __future__ import annotations
import json, os, pathlib, threading, unittest, importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import _kotoba_feature as kf
import _etzhayyim_substrate as sub

HERE = pathlib.Path(__file__).resolve().parent
# repo root = .../<root>/60-apps/etzhayyim-project-maps/bulk-ingest/workers → up 4 (parents[3])
REPO = HERE.parents[3]
MAPS_INGEST = REPO / "20-actors" / "maps" / "methods" / "ingest.py"

ROWS = [
    {"vertex_id": "at://x/airport/hnd", "label": "Airport", "name": "Haneda",
     "lat": 35.5494, "lng": 139.7798, "source_did": "did:web:maps.etzhayyim.com:registry:openflights"},
    {"vertex_id": "at://x/airroute/hnd-itm", "label": "AirRoute", "name": "HND-ITM",
     "lat": 35.0, "lng": 135.0, "props": json.dumps({"airline": "NH", "stops": 0})},
    {"vertex_id": "at://x/adminarea/jp13", "label": "AdminArea", "name": "Tokyo",
     "lat": 35.68, "lng": 139.69},
    {"vertex_id": "at://x/building/marunouchi", "label": "Building", "name": "Marunouchi Bldg",
     "lat": 35.6809, "lng": 139.7644,
     "props": json.dumps({"heightM": 179, "levels": 37,
                          "geometry": {"type": "Point", "coordinates": [139.7644, 35.6809]}})},
]


class TestMapping(unittest.TestCase):
    def test_row_to_entity_shape(self):
        e = kf.row_to_entity(ROWS[0])
        self.assertEqual(e["id"], "at://x/airport/hnd")
        self.assertEqual(e["type"], "maps-feature")
        preds = {c["pred"]: c["value"] for c in e["claims"]}
        self.assertEqual(preds["feature/label"], ":airport")        # folded
        self.assertEqual(preds["feature/sourcing"], ":representative")  # G3
        self.assertEqual(preds["feature/name"], "Haneda")
        self.assertEqual(preds["feature/lat"], "35.5494")
        self.assertNotIn("feature/id", preds)                        # id is the entity id

    def test_multiword_label_folds(self):
        self.assertEqual(kf.fold_label("AirRoute"), ":air-route")
        self.assertEqual(kf.fold_label("AdminArea"), ":admin-area")
        self.assertEqual(kf.fold_label("LegalEntity"), ":legal-entity")
        self.assertEqual(kf.fold_label("LandRegistry"), ":registry")
        self.assertEqual(kf.fold_label("Weird Thing"), ":weird-thing")  # unknown → kebab

    def test_props_promotion_and_geometry(self):
        e = kf.row_to_entity(ROWS[3])
        preds = {c["pred"]: c["value"] for c in e["claims"]}
        self.assertEqual(preds["feature/height-m"], "179.0")
        self.assertEqual(preds["feature/levels"], "37")
        self.assertIn("feature/geometry", preds)
        json.loads(preds["feature/geometry"])  # valid JSON
        # promoted keys are NOT left in the props bag
        if "feature/props" in preds:
            bag = json.loads(preds["feature/props"])
            self.assertNotIn("heightM", bag)
            self.assertNotIn("geometry", bag)

    def test_rows_to_batch(self):
        batch = kf.rows_to_batch(ROWS)
        self.assertEqual(len(batch["entities"]), 4)

    def test_label_map_matches_canonical_maps_ingest(self):
        # the two write paths (maps Worker adapter / bulk dumpers) must agree on the keyword
        if not MAPS_INGEST.exists():
            self.skipTest("maps ingest.py not present in this checkout")
        spec = importlib.util.spec_from_file_location("_maps_ingest", MAPS_INGEST)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(kf._LABEL_MAP, mod._LABEL_MAP,
                         "bulk-ingest _LABEL_MAP drifted from 20-actors/maps/methods/ingest.py")

    def test_all_keywords_are_kebab(self):
        for kw in kf._LABEL_MAP.values():
            self.assertTrue(kw.startswith(":"), kw)
            self.assertEqual(kw, kw.lower(), kw)
            self.assertNotIn("_", kw)


class TestGate(unittest.TestCase):
    def _env(self, **kw):
        saved = {k: os.environ.get(k) for k in
                 ("ETZHAYYIM_SUBSTRATE_MODE", "MAPS_OPERATOR_GATE", "KOTOBA_ENDPOINT", "KOTOBA_AUTH")}
        for k in saved:
            os.environ.pop(k, None)
        os.environ["ETZHAYYIM_SUBSTRATE_MODE"] = "kotoba"
        os.environ.update(kw)
        return saved

    def _restore(self, saved):
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_gate_refuses_without_operator(self):
        saved = self._env()  # gate unset
        try:
            with self.assertRaises(RuntimeError) as cm:
                with sub.open_substrate_writer():
                    pass
            self.assertIn("MAPS_OPERATOR_GATE", str(cm.exception))
        finally:
            self._restore(saved)

    def test_gate_refuses_without_auth(self):
        saved = self._env(MAPS_OPERATOR_GATE="1")  # gate on, no endpoint/auth
        try:
            with self.assertRaises(RuntimeError) as cm:
                with sub.open_substrate_writer():
                    pass
            self.assertIn("no-server-key", str(cm.exception).lower())
        finally:
            self._restore(saved)


class _Recorder(BaseHTTPRequestHandler):
    received: list = []
    auth_seen: list = []
    def do_POST(self):
        n = int(self.headers.get("content-length", 0))
        _Recorder.received.append(json.loads(self.rfile.read(n) or b"{}"))
        _Recorder.auth_seen.append(self.headers.get("authorization"))
        body = b'{"ok":true}'
        self.send_response(200); self.send_header("content-length", str(len(body))); self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass


class TestE2E(unittest.TestCase):
    def test_writer_posts_kg_batch_member_signed(self):
        _Recorder.received.clear(); _Recorder.auth_seen.clear()
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Recorder)
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        saved = {k: os.environ.get(k) for k in
                 ("ETZHAYYIM_SUBSTRATE_MODE", "MAPS_OPERATOR_GATE", "KOTOBA_ENDPOINT", "KOTOBA_AUTH")}
        os.environ.update(ETZHAYYIM_SUBSTRATE_MODE="kotoba", MAPS_OPERATOR_GATE="1",
                          KOTOBA_ENDPOINT=f"http://127.0.0.1:{port}", KOTOBA_AUTH="member-did-bearer")
        try:
            with sub.open_substrate_writer() as w:
                n = w.upsert_vertex_spatial(ROWS)
            self.assertEqual(n, 4)
            self.assertEqual(len(_Recorder.received), 1)
            ents = _Recorder.received[0]["entities"]
            ids = {e["id"] for e in ents}
            self.assertIn("at://x/airport/hnd", ids)
            labels = {c["value"] for e in ents for c in e["claims"] if c["pred"] == "feature/label"}
            self.assertEqual(labels, {":airport", ":air-route", ":admin-area", ":building"})
            self.assertEqual(_Recorder.auth_seen[0], "Bearer member-did-bearer")  # no-server-key
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
            httpd.shutdown(); httpd.server_close()

    def test_unmapped_aux_table_raises_loudly(self):
        saved = {k: os.environ.get(k) for k in
                 ("ETZHAYYIM_SUBSTRATE_MODE", "MAPS_OPERATOR_GATE", "KOTOBA_ENDPOINT", "KOTOBA_AUTH")}
        os.environ.update(ETZHAYYIM_SUBSTRATE_MODE="kotoba", MAPS_OPERATOR_GATE="1",
                          KOTOBA_ENDPOINT="http://127.0.0.1:1", KOTOBA_AUTH="x")
        try:
            with sub.open_substrate_writer() as w:
                with self.assertRaises(NotImplementedError):  # gsplat registry has no schema yet
                    w.upsert_table("vertex_maps_gsplat_asset", [{"asset_id": "a"}])
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


TRIPS = [
    {"feed_id": "tokyo-metro", "trip_id": "T1", "route_id": "M", "service_id": "wd",
     "direction_id": 0, "headsign": "Ogikubo", "agency": "Tokyo Metro", "prefecture": "Tokyo"},
]
STOP_TIMES = [
    {"feed_id": "tokyo-metro", "trip_id": "T1", "stop_sequence": 1,
     "stop_id": "gtfsjp-tokyo-metro-S01", "arrival_time": "08:00:00", "departure_time": "08:00:30"},
    {"feed_id": "tokyo-metro", "trip_id": "T1", "stop_sequence": 2,
     "stop_id": "gtfsjp-tokyo-metro-S02", "departure_time": "08:02:00", "timepoint": 1},
]


class TestTransitAux(unittest.TestCase):
    def test_trip_row_to_entity(self):
        e = kf.trip_row_to_entity(TRIPS[0])
        self.assertEqual(e["id"], "trip.tokyo-metro.T1")
        self.assertEqual(e["type"], "transit-trip")
        preds = {c["pred"]: c["value"] for c in e["claims"]}
        self.assertEqual(preds["transit.trip/route"], "M")
        self.assertEqual(preds["transit.trip/direction"], "0")
        self.assertEqual(preds["transit.trip/sourcing"], ":representative")

    def test_stop_time_row_to_entity_and_index_key(self):
        e = kf.stop_time_row_to_entity(STOP_TIMES[0])
        self.assertEqual(e["id"], "stoptime.tokyo-metro.T1.1")
        preds = {c["pred"]: c["value"] for c in e["claims"]}
        # the "next departures at stop X" index key + sort key
        self.assertEqual(preds["transit.stop-time/stop"], "gtfsjp-tokyo-metro-S01")
        self.assertEqual(preds["transit.stop-time/departure-time"], "08:00:30")
        # ref to the parent trip (composite id)
        self.assertEqual(preds["transit.stop-time/trip"], "trip.tokyo-metro.T1")

    def test_missing_key_skipped(self):
        self.assertIsNone(kf.trip_row_to_entity({"feed_id": "f"}))         # no trip_id
        self.assertIsNone(kf.stop_time_row_to_entity({"feed_id": "f", "trip_id": "t"}))  # no seq

    def test_aux_rows_to_batch_dispatch(self):
        self.assertEqual(len(kf.aux_rows_to_batch("vertex_maps_trip", TRIPS)["entities"]), 1)
        self.assertEqual(len(kf.aux_rows_to_batch("vertex_maps_stop_time", STOP_TIMES)["entities"]), 2)
        self.assertIsNone(kf.aux_rows_to_batch("vertex_maps_gsplat_asset", [{"x": 1}]))  # unmapped

    def test_e2e_aux_writer_posts_transit_records(self):
        _Recorder.received.clear(); _Recorder.auth_seen.clear()
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Recorder)
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        saved = {k: os.environ.get(k) for k in
                 ("ETZHAYYIM_SUBSTRATE_MODE", "MAPS_OPERATOR_GATE", "KOTOBA_ENDPOINT", "KOTOBA_AUTH")}
        os.environ.update(ETZHAYYIM_SUBSTRATE_MODE="kotoba", MAPS_OPERATOR_GATE="1",
                          KOTOBA_ENDPOINT=f"http://127.0.0.1:{port}", KOTOBA_AUTH="member-did")
        try:
            with sub.open_substrate_writer() as w:
                n = w.upsert_table("vertex_maps_stop_time", STOP_TIMES)
            self.assertEqual(n, 2)
            ents = _Recorder.received[0]["entities"]
            stops = {c["value"] for e in ents for c in e["claims"]
                     if c["pred"] == "transit.stop-time/stop"}
            self.assertEqual(stops, {"gtfsjp-tokyo-metro-S01", "gtfsjp-tokyo-metro-S02"})
            self.assertEqual(_Recorder.auth_seen[0], "Bearer member-did")  # no-server-key
        finally:
            for k, v in saved.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
            httpd.shutdown(); httpd.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
