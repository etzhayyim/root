#!/usr/bin/env python3
"""maps — kotoba-native transit read tests (ADR-2606064500 R2 aux). stdlib unittest.

Ingests :transit.* records into the kotoba stand-in, then exercises the read methods
(next_departures_at_stop / trips_on_route) end-to-end over HTTP — proving the transit
write→read loop the GTFS migration depends on.

Run: python3 test_transit.py
"""
from __future__ import annotations
import json, threading, unittest, urllib.request

import transit
from kotoba_local_server import serve

TOKEN = "member-did"
# Two stops on one route; departures deliberately OUT OF ORDER + one before the `after` cutoff.
STOP_TIMES = [
    ("S1", "T1", 1, "08:05:00"), ("S1", "T2", 1, "08:01:00"), ("S1", "T3", 1, "07:30:00"),
    ("S1", "T4", 1, "25:10:00"),  # past-midnight (GTFS >24:00:00) — must sort AFTER 08:xx
    ("S2", "T1", 2, "08:09:00"),
]
TRIPS = ["T1", "T2", "T3", "T4"]


def _batch():
    ents = []
    for trip in TRIPS:
        ents.append({"id": f"trip.f.{trip}", "type": "transit-trip",
                     "claims": [{"pred": "transit.trip/route", "value": "ROUTE-M"},
                                {"pred": "transit.trip/headsign", "value": f"to {trip}"},
                                {"pred": "transit.trip/service", "value": "weekday"}]})
    for stop, trip, seq, dep in STOP_TIMES:
        ents.append({"id": f"stoptime.f.{trip}.{seq}.{stop}", "type": "transit-stop-time",
                     "claims": [{"pred": "transit.stop-time/stop", "value": stop},
                                {"pred": "transit.stop-time/trip", "value": f"trip.f.{trip}"},
                                {"pred": "transit.stop-time/departure-time", "value": dep},
                                {"pred": "transit.stop-time/sequence", "value": str(seq)},
                                {"pred": "transit.stop-time/headsign", "value": f"to {trip}"}]})
    return {"entities": ents}


def _post(url, body, token=None):
    h = {"content-type": "application/json"}
    if token:
        h["authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


class TestTransitRead(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = serve(0, TOKEN)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        _post(f"{cls.base}/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch", _batch(), TOKEN)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close()

    def test_sorted_earliest_first(self):
        deps = [r["departure"] for r in transit.next_departures_at_stop(self.base, "S1")]
        # 07:30 included (after default 00:00), 25:10 sorts last (text)
        self.assertEqual(deps, ["07:30:00", "08:01:00", "08:05:00", "25:10:00"])

    def test_after_cutoff_filters(self):
        deps = [r["departure"] for r in transit.next_departures_at_stop(self.base, "S1", after="08:00:00")]
        self.assertEqual(deps, ["08:01:00", "08:05:00", "25:10:00"])  # 07:30 dropped

    def test_limit(self):
        rows = transit.next_departures_at_stop(self.base, "S1", limit=2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["departure"], "07:30:00")

    def test_stop_isolation(self):
        # S2 has only T1's call — querying S2 must not return S1's stop-times
        rows = transit.next_departures_at_stop(self.base, "S2")
        self.assertEqual([r["departure"] for r in rows], ["08:09:00"])

    def test_unknown_stop_empty(self):
        self.assertEqual(transit.next_departures_at_stop(self.base, "NOPE"), [])

    def test_fields_present(self):
        r = transit.next_departures_at_stop(self.base, "S1", after="08:00:00")[0]
        self.assertEqual(r["trip"], "trip.f.T2")
        self.assertEqual(r["headsign"], "to T2")

    def test_trips_on_route(self):
        trips = {t["trip"] for t in transit.trips_on_route(self.base, "ROUTE-M")}
        self.assertEqual(trips, {"trip.f.T1", "trip.f.T2", "trip.f.T3", "trip.f.T4"})

    def test_endpoint_down_fails_soft(self):
        self.assertEqual(transit.next_departures_at_stop("http://127.0.0.1:1", "S1"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
