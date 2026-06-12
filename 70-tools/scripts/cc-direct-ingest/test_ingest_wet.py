"""Unit tests for cc-direct-ingest (pure stdlib, no network / no server)."""

import gzip
import io
import unittest

import ingest_wet as iw


def make_warc(records) -> bytes:
    """Build a minimal WET-shaped WARC byte stream."""
    out = io.BytesIO()
    for headers, body in records:
        body_b = body.encode("utf-8")
        out.write(b"WARC/1.0\r\n")
        for k, v in headers.items():
            out.write(f"{k}: {v}\r\n".encode())
        out.write(f"Content-Length: {len(body_b)}\r\n".encode())
        out.write(b"\r\n")
        out.write(body_b)
        out.write(b"\r\n\r\n")
    return out.getvalue()


CONVERSION = {
    "WARC-Type": "conversion",
    "WARC-Target-URI": "https://example.com/a",
    "WARC-Identified-Content-Language": "jpn,eng",
}


class GraphCidTest(unittest.TestCase):
    def test_chunks_graph_cid_matches_live_server(self):
        # Verified against the running kotoba-server's cc.status output.
        self.assertEqual(
            iw.kotoba_graph_cid("cc:2026-12:chunks"),
            "bafyreifp2oe5yhpsy4p6pyu4jftphikzlxt6pkg3zygkc7ycxsdhzxgkmu",
        )

    def test_links_graph_cid_matches_live_server(self):
        self.assertEqual(
            iw.kotoba_graph_cid("cc:2026-12:links"),
            "bafyreidirvasxhxxh4pxc57xbvmct3xe2adfqkbubxtnqz6sacpcvgzedi",
        )


class WarcParseTest(unittest.TestCase):
    def test_yields_conversion_records_with_lang_mapping(self):
        text = "こんにちは世界。" * 20
        raw = make_warc([
            ({"WARC-Type": "warcinfo"}, "ignored"),
            (CONVERSION, text),
        ])
        recs = list(iw._parse_warc_stream(io.BufferedReader(io.BytesIO(raw))))
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0].url, "https://example.com/a")
        self.assertEqual(recs[0].lang, "ja")  # jpn → ja
        self.assertEqual(recs[0].text, text)

    def test_skips_non_conversion_and_missing_uri(self):
        raw = make_warc([
            ({"WARC-Type": "request"}, "x"),
            ({"WARC-Type": "conversion"}, "no uri"),
        ])
        recs = list(iw._parse_warc_stream(io.BufferedReader(io.BytesIO(raw))))
        self.assertEqual(recs, [])

    def test_unknown_lang_falls_back(self):
        hdrs = dict(CONVERSION)
        hdrs["WARC-Identified-Content-Language"] = "xyz"
        raw = make_warc([(hdrs, "body " * 30)])
        recs = list(iw._parse_warc_stream(io.BufferedReader(io.BytesIO(raw))))
        self.assertEqual(recs[0].lang, "xy")

    def test_gzip_stream_round_trip(self):
        raw = make_warc([(CONVERSION, "hello wet " * 30)])
        gz = gzip.compress(raw)
        stream = io.BufferedReader(iw._GzipHttpStream(io.BytesIO(gz)))
        recs = list(iw._parse_warc_stream(stream))
        self.assertEqual(len(recs), 1)
        self.assertIn("hello wet", recs[0].text)

    def test_multi_member_gzip_like_real_cc_wet(self):
        # CC compresses one gzip member PER RECORD; the decoder must cross
        # member boundaries instead of stopping at the first warcinfo record.
        m1 = gzip.compress(make_warc([({"WARC-Type": "warcinfo"}, "info")]))
        hdrs2 = dict(CONVERSION)
        hdrs2["WARC-Target-URI"] = "https://example.com/b"
        m2 = gzip.compress(make_warc([(CONVERSION, "first page " * 20)]))
        m3 = gzip.compress(make_warc([(hdrs2, "second page " * 20)]))
        stream = io.BufferedReader(iw._GzipHttpStream(io.BytesIO(m1 + m2 + m3)))
        recs = list(iw._parse_warc_stream(stream))
        self.assertEqual([r.url for r in recs],
                         ["https://example.com/a", "https://example.com/b"])


class ChunkTest(unittest.TestCase):
    def test_splits_near_target_on_line_boundaries(self):
        text = "\n".join(f"line {i} " + "x" * 90 for i in range(20))
        chunks = iw.chunk_text(text, target=300)
        self.assertGreater(len(chunks), 3)
        for c in chunks:
            self.assertLessEqual(len(c), 300 + 100)

    def test_drops_tiny_trailing_fragment(self):
        self.assertEqual(iw.chunk_text("short"), [])

    def test_keeps_cjk_text_intact(self):
        text = "縁起と産霊。" * 50
        chunks = iw.chunk_text(text, target=200)
        self.assertEqual(len(chunks), 1)  # single line → single chunk
        self.assertIn("縁起", chunks[0])


class EdnTest(unittest.TestCase):
    def test_escapes_quotes_backslashes_and_newlines(self):
        s = iw.edn_escape('say "hi"\\\nnow')
        self.assertEqual(s, 'say \\"hi\\"\\\\ now')

    def test_strips_control_chars(self):
        self.assertEqual(iw.edn_escape("a\x00b\x07c"), "abc")

    def test_chunk_datoms_edn_shape(self):
        edn = iw.chunk_datoms_edn("s1", "https://e.com/p", "e.com", "ja", "本文")
        self.assertIn('[:db/add "s1" "cc/chunk/text" "本文"]', edn)
        self.assertIn('"cc/chunk/url" "https://e.com/p"', edn)
        self.assertIn('"cc/chunk/domain" "e.com"', edn)
        self.assertIn('"cc/chunk/lang" "ja"', edn)

    def test_page_subject_prefix_deterministic(self):
        a = iw.page_subject_prefix("https://example.com/a")
        self.assertEqual(a, iw.page_subject_prefix("https://example.com/a"))
        self.assertTrue(a.startswith("cc-wet:"))
        self.assertNotEqual(a, iw.page_subject_prefix("https://example.com/b"))


class TokenTest(unittest.TestCase):
    def test_operator_token_carries_sub(self):
        import base64 as b64
        import json as js
        tok = iw.operator_token("did:key:zTest")
        payload = tok.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        claims = js.loads(b64.urlsafe_b64decode(payload))
        self.assertEqual(claims["sub"], "did:key:zTest")
        self.assertGreater(claims["exp"], 0)


if __name__ == "__main__":
    unittest.main()
