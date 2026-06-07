#!/usr/bin/env python3
"""maps — kotoba-native name search tests (ADR-2606064500 R2). stdlib unittest.

Tokenizes feature names at ingest (:feature/name-token), ingests into the kotoba stand-in,
then searches by ASCII prefix + CJK bigram over HTTP — the name-search write→read loop, the
successor to vertex_spatial `name LIKE`.

Run: python3 test_search.py
"""
from __future__ import annotations
import json, threading, unittest, urllib.request

import ingest
import search
from kotoba_local_server import serve

TOKEN = "member-did"
FEATS = {
    "f.station.tokyo":  {":feature/id": "f.station.tokyo",  ":feature/label": ":station",  ":feature/name": "Tokyo Station",       ":feature/sourcing": ":representative"},
    "f.place.tokyotower": {":feature/id": "f.place.tokyotower", ":feature/label": ":place", ":feature/name": "Tokyo Tower",        ":feature/sourcing": ":representative"},
    "f.bldg.marunouchi": {":feature/id": "f.bldg.marunouchi", ":feature/label": ":building", ":feature/name": "Marunouchi Building", ":feature/sourcing": ":representative"},
    "f.station.tokyo-jp": {":feature/id": "f.station.tokyo-jp", ":feature/label": ":station", ":feature/name": "東京駅",            ":feature/sourcing": ":representative"},
    "f.station.shinjuku": {":feature/id": "f.station.shinjuku", ":feature/label": ":station", ":feature/name": "新宿駅",            ":feature/sourcing": ":representative"},
}


def _post(url, body, token=None):
    h = {"content-type": "application/json"}
    if token:
        h["authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


class TestTokenizer(unittest.TestCase):
    def test_ascii_prefixes_stored(self):
        toks = search.name_tokens("Tokyo")
        self.assertIn("to", toks)
        self.assertIn("tok", toks)
        self.assertIn("tokyo", toks)
        self.assertNotIn("t", toks)  # min length 2

    def test_query_probes_whole_word(self):
        self.assertEqual(search.query_tokens("Tok"), {"tok"})

    def test_cjk_bigrams(self):
        self.assertEqual(search.name_tokens("東京駅"), {"東京", "京駅"})
        self.assertEqual(search.query_tokens("東京"), {"東京"})

    def test_prefix_match_contract(self):
        # the load-bearing property: a query word is a stored prefix of a matching name
        self.assertTrue(search.query_tokens("tok") <= search.name_tokens("Tokyo Tower"))


class TestSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = serve(0, TOKEN)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        _post(f"{cls.base}/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch",
              ingest.to_kg_batch(FEATS), TOKEN)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close()

    def test_ascii_prefix_search(self):
        names = {r["name"] for r in search.search_places(self.base, "tok")}
        self.assertEqual(names, {"Tokyo Station", "Tokyo Tower"})

    def test_ranking_more_tokens_first(self):
        # "Tokyo Tower" overlaps the full query "tokyo tower" on more tokens than "Tokyo Station"
        rows = search.search_places(self.base, "tokyo tower")
        self.assertEqual(rows[0]["name"], "Tokyo Tower")
        self.assertGreater(rows[0]["score"], rows[-1]["score"])

    def test_label_filter(self):
        rows = search.search_places(self.base, "tokyo", labels=["station"])
        self.assertEqual({r["name"] for r in rows}, {"Tokyo Station"})

    def test_cjk_search(self):
        names = {r["name"] for r in search.search_places(self.base, "東京")}
        self.assertEqual(names, {"東京駅"})  # 京駅/新宿 not matched by 東京 bigram

    def test_other_word_matches_marunouchi(self):
        names = {r["name"] for r in search.search_places(self.base, "marun")}
        self.assertEqual(names, {"Marunouchi Building"})

    def test_unknown_query_empty(self):
        self.assertEqual(search.search_places(self.base, "zzqq"), [])

    def test_limit(self):
        self.assertEqual(len(search.search_places(self.base, "tok", limit=1)), 1)

    def test_endpoint_down_fails_soft(self):
        self.assertEqual(search.search_places("http://127.0.0.1:1", "tok"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
