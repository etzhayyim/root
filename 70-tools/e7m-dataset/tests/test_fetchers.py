"""Tests for the e7m-dataset fetchers (wikidata / geonames / osm).

All network access is mocked via httpx.MockTransport so the suite runs
in CI without hitting Wikidata / GeoNames / Geofabrik.
"""

from __future__ import annotations

import hashlib
import io
import json
import urllib.parse
import zipfile
from pathlib import Path

import httpx
import pytest

from e7m_dataset.fetchers import geonames, osm, wikidata


# ─── Wikidata ────────────────────────────────────────────────────────


def test_wikidata_canned_queries_present():
    assert "legal-entities-with-lei" in wikidata.CANNED_QUERIES
    assert "admin-areas" in wikidata.CANNED_QUERIES
    # Each query references the %(limit)d substitution.
    for name, q in wikidata.CANNED_QUERIES.items():
        assert "%(limit)d" in q, f"{name}: missing LIMIT substitution"


def test_wikidata_fetch_writes_jsonl_and_query_file(tmp_path):
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        body = req.content.decode("utf-8")
        captured["query"] = urllib.parse.parse_qs(body).get("query", [""])[0]
        return httpx.Response(
            200,
            json={
                "results": {
                    "bindings": [
                        {"entity": {"value": "http://www.wikidata.org/entity/Q1"}, "lei": {"value": "X" * 20}},
                        {"entity": {"value": "http://www.wikidata.org/entity/Q2"}, "lei": {"value": "Y" * 20}},
                    ]
                }
            },
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = wikidata.fetch(
            tmp_path,
            wikidata.WikidataFetchOpts(
                query_name="legal-entities-with-lei",
                limit=10,
                client=client,
            ),
        )

    assert result.name == "wikidata:legal-entities-with-lei"
    assert result.revision.startswith("sha256:")
    # 2 files: query.sparql + result.jsonl
    assert result.file_count == 2
    jsonl = (result.staging_path / "result.jsonl").read_text(encoding="utf-8")
    assert len(jsonl.strip().splitlines()) == 2
    sparql = (result.staging_path / "query.sparql").read_text(encoding="utf-8")
    assert "LIMIT 10" in sparql
    assert "wdt:P5305" in sparql  # LEI predicate
    # The captured request includes the substituted limit.
    assert "LIMIT 10" in captured["query"]


def test_wikidata_unknown_query_raises():
    with pytest.raises(KeyError, match="unknown query"):
        wikidata.fetch(
            Path("/tmp"),
            wikidata.WikidataFetchOpts(query_name="does-not-exist"),
        )


def test_wikidata_raw_query_override(tmp_path):
    def handler(req):
        return httpx.Response(200, json={"results": {"bindings": []}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = wikidata.fetch(
            tmp_path,
            wikidata.WikidataFetchOpts(
                query_name="custom",
                query_text="SELECT ?x WHERE { ?x ?y ?z } LIMIT %(limit)d",
                limit=5,
                client=client,
            ),
        )
    sparql = (result.staging_path / "query.sparql").read_text(encoding="utf-8")
    assert "?x ?y ?z" in sparql
    assert "LIMIT 5" in sparql


def test_wikidata_revision_is_deterministic_for_same_response(tmp_path):
    body = {"results": {"bindings": [{"a": {"value": "1"}}]}}
    handler = lambda req: httpx.Response(200, json=body)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        r1 = wikidata.fetch(tmp_path / "a", wikidata.WikidataFetchOpts(query_name="admin-areas", client=client))
        r2 = wikidata.fetch(tmp_path / "b", wikidata.WikidataFetchOpts(query_name="admin-areas", client=client))
    assert r1.revision == r2.revision


# ─── GeoNames ───────────────────────────────────────────────────────


def _make_geonames_zip() -> bytes:
    """Build a minimal GeoNames cities1000.zip payload."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        # GeoNames TSV: geonameid \t name \t asciiname \t altnames \t lat \t lng \t fcl ...
        sample = "1850147\tTokyo\tTokyo\t\t35.6895\t139.69171\tP\tPPLC\tJP\n"
        zf.writestr("cities1000.txt", sample)
    return buf.getvalue()


def test_geonames_fetch_extracts_txt_from_zip(tmp_path):
    zip_bytes = _make_geonames_zip()

    def handler(req):
        return httpx.Response(200, content=zip_bytes, headers={"content-type": "application/zip"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = geonames.fetch(
            tmp_path,
            geonames.GeonamesFetchOpts(dataset="cities1000", client=client),
        )

    assert result.name == "geonames:cities1000"
    assert result.revision.startswith("sha256:")
    # Both the zip and the extracted .txt should be present.
    files = sorted(p.name for p in result.staging_path.iterdir() if p.is_file())
    assert "cities1000.zip" in files
    assert "cities1000.txt" in files
    extracted = (result.staging_path / "cities1000.txt").read_text(encoding="utf-8")
    assert "Tokyo" in extracted


def test_geonames_unknown_dataset_raises():
    with pytest.raises(ValueError, match="unknown GeoNames dataset"):
        geonames.fetch(Path("/tmp"), geonames.GeonamesFetchOpts(dataset="not-a-thing"))


def test_geonames_revision_matches_zip_sha(tmp_path):
    zip_bytes = _make_geonames_zip()
    expected_sha = hashlib.sha256(zip_bytes).hexdigest()
    handler = lambda req: httpx.Response(200, content=zip_bytes)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = geonames.fetch(
            tmp_path,
            geonames.GeonamesFetchOpts(dataset="cities1000", client=client),
        )
    assert result.revision == f"sha256:{expected_sha}"


# ─── OSM (Geofabrik) ────────────────────────────────────────────────


def test_osm_region_alias_resolves():
    assert osm._resolve_region("japan") == "asia/japan"
    assert osm._resolve_region("germany") == "europe/germany"
    assert osm._resolve_region("asia/japan") == "asia/japan"  # explicit


def test_osm_unknown_region_raises():
    with pytest.raises(ValueError, match="unknown OSM region"):
        osm._resolve_region("middle-earth")


def test_osm_top_level_continent_resolves():
    # 'europe' is a top-level continent dump.
    assert osm._resolve_region("europe") == "europe"


def test_osm_fetch_downloads_pbf_and_md5(tmp_path):
    pbf_bytes = b"FAKE_PBF_CONTENT" * 100
    md5_hex = "abc123def456abc123def456abc123de"  # 32-char fake md5
    md5_text = f"{md5_hex}  japan-latest.osm.pbf\n"

    def handler(req: httpx.Request) -> httpx.Response:
        url = str(req.url)
        if url.endswith(".osm.pbf"):
            return httpx.Response(200, content=pbf_bytes)
        if url.endswith(".osm.pbf.md5"):
            return httpx.Response(200, text=md5_text)
        return httpx.Response(404)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = osm.fetch(
            tmp_path,
            osm.OsmFetchOpts(region="japan", client=client, fetch_md5=True),
        )

    assert result.name == "osm:asia/japan"
    assert result.revision == f"md5:{md5_hex}"
    pbf = result.staging_path / "asia-japan-latest.osm.pbf"
    assert pbf.exists()
    assert pbf.read_bytes() == pbf_bytes
    md5 = result.staging_path / "asia-japan-latest.osm.pbf.md5"
    assert md5.exists()
    assert md5.read_text() == md5_text


def test_osm_fetch_falls_back_to_sha256_when_no_md5(tmp_path):
    pbf_bytes = b"FAKE_PBF_NO_MD5"

    def handler(req):
        if str(req.url).endswith(".osm.pbf.md5"):
            return httpx.Response(404)
        return httpx.Response(200, content=pbf_bytes)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = osm.fetch(
            tmp_path,
            osm.OsmFetchOpts(region="japan", client=client, fetch_md5=True),
        )
    expected_sha = hashlib.sha256(pbf_bytes).hexdigest()
    assert result.revision == f"sha256:{expected_sha}"


def test_osm_fetch_no_md5_flag(tmp_path):
    pbf_bytes = b"FAKE_NO_MD5_FLAG"

    md5_calls = []

    def handler(req):
        url = str(req.url)
        if url.endswith(".osm.pbf.md5"):
            md5_calls.append(url)
            return httpx.Response(200, text="should-not-be-called")
        return httpx.Response(200, content=pbf_bytes)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = osm.fetch(
            tmp_path,
            osm.OsmFetchOpts(region="japan", client=client, fetch_md5=False),
        )
    assert md5_calls == []
    assert result.revision.startswith("sha256:")
