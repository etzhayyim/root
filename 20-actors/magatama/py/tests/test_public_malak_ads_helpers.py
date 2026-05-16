"""Tests for pure helper functions in public_malak_ads.py."""

from __future__ import annotations

import sys
from pathlib import Path

_py_src = Path(__file__).resolve().parents[1] / "src"
if str(_py_src) not in sys.path:
    sys.path.insert(0, str(_py_src))

from pymagatama.primitives import public_malak_ads as PM


# ─── _sha ────────────────────────────────────────────────────────────────────

def test_sha_starts_with_prefix() -> None:
    result = PM._sha("run", "part1", "part2")
    assert result.startswith("run-")


def test_sha_deterministic() -> None:
    a = PM._sha("run", "part1", "part2")
    b = PM._sha("run", "part1", "part2")
    assert a == b


def test_sha_varies_with_parts() -> None:
    a = PM._sha("x", "abc")
    b = PM._sha("x", "xyz")
    assert a != b


def test_sha_hash_length() -> None:
    result = PM._sha("prefix", "val")
    # "prefix-" (7) + 24 hex chars
    hex_part = result[len("prefix-"):]
    assert len(hex_part) == 24


def test_sha_none_parts_handled() -> None:
    result = PM._sha("run", None, None)
    assert result.startswith("run-")


# ─── Artifact helpers ────────────────────────────────────────────────────────

def test_html_artifact_cid_matches_snapshot_hash_behavior() -> None:
    text = "x" * 5000
    assert PM._html_artifact_cid(text) == PM._sha("html", text[:4096])


def test_html_artifact_cid_empty_returns_none() -> None:
    assert PM._html_artifact_cid("") is None


def test_bytes_artifact_cid_uses_kind_prefix() -> None:
    cid = PM._bytes_artifact_cid("har", b'{"ok":true}')
    assert cid is not None
    assert cid.startswith("har-")


def test_artifact_key_uses_public_malak_prefix(monkeypatch) -> None:
    monkeypatch.setattr(PM, "ARTIFACT_PREFIX", "artifacts/public-malak")
    assert PM._artifact_key("html", "html-abc", ".html") == "artifacts/public-malak/html/html-abc.html"


def test_artifact_key_without_prefix(monkeypatch) -> None:
    monkeypatch.setattr(PM, "ARTIFACT_PREFIX", "")
    assert PM._artifact_key("html", "html-abc", ".html") == "html/html-abc.html"


def test_s3_put_artifact_missing_config_returns_none(monkeypatch) -> None:
    monkeypatch.setattr(PM, "ARTIFACT_BUCKET", "")
    monkeypatch.setattr(PM, "ARTIFACT_S3_ENDPOINT", "")
    monkeypatch.setattr(PM, "ARTIFACT_S3_ACCESS_KEY_ID", "")
    monkeypatch.setattr(PM, "ARTIFACT_S3_SECRET_ACCESS_KEY", "")
    assert PM._s3_put_artifact("artifacts/public-malak/html/html-abc.html", b"<html></html>", "text/html") is None


def test_har_lite_doc_records_response_metadata() -> None:
    doc = PM._har_lite_doc(
        source_url="https://example.test/ads",
        fetch_result={
            "httpStatus": 200,
            "statusText": "OK",
            "headers": {"Content-Type": "text/html", "X-Test": "yes"},
            "finalUrl": "https://example.test/ads",
            "elapsedMs": 123,
            "text": "<html>ad</html>",
            "error": "",
        },
        html_cid="html-abc",
        scraped_at="2026-05-07T00:00:00Z",
    )
    entry = doc["log"]["entries"][0]
    assert entry["time"] == 123
    assert entry["response"]["status"] == 200
    assert entry["response"]["content"]["htmlCid"] == "html-abc"
    assert {"name": "X-Test", "value": "yes"} in entry["response"]["headers"]


def test_har_artifact_cid_is_deterministic() -> None:
    doc = {"log": {"entries": [{"response": {"status": 200}}]}}
    assert PM._har_artifact_cid(doc) == PM._har_artifact_cid(doc)
    assert str(PM._har_artifact_cid(doc)).startswith("har-")


# ─── _run_vid ────────────────────────────────────────────────────────────────

def test_run_vid_format() -> None:
    vid = PM._run_vid("run-001")
    assert "at://" in vid
    assert "ai.gftd.apps.publicMalak.adScraperRun" in vid
    assert "run-001" in vid


def test_run_vid_deterministic() -> None:
    assert PM._run_vid("x") == PM._run_vid("x")


# ─── _advertiser_vid ─────────────────────────────────────────────────────────

def test_advertiser_vid_format() -> None:
    vid = PM._advertiser_vid("meta", "12345")
    assert "ai.gftd.apps.publicMalak.adAdvertiser" in vid
    assert "meta-12345" in vid


def test_advertiser_vid_varies_by_platform() -> None:
    a = PM._advertiser_vid("meta", "123")
    b = PM._advertiser_vid("google", "123")
    assert a != b


# ─── _creative_vid ───────────────────────────────────────────────────────────

def test_creative_vid_format() -> None:
    vid = PM._creative_vid("tiktok", "ad-99")
    assert "ai.gftd.apps.publicMalak.adCreative" in vid
    assert "tiktok-ad-99" in vid


# ─── _snapshot_vid ───────────────────────────────────────────────────────────

def test_snapshot_vid_format() -> None:
    vid = PM._snapshot_vid("google", "ad-1", "run-2")
    assert "ai.gftd.apps.publicMalak.adSnapshot" in vid
    assert "google-ad-1-run-2" in vid


# ─── _clean_text ─────────────────────────────────────────────────────────────

def test_clean_text_strips_html_tags() -> None:
    result = PM._clean_text("<b>Hello</b> <i>world</i>")
    assert "<b>" not in result
    assert "Hello" in result
    assert "world" in result


def test_clean_text_removes_script_tags() -> None:
    result = PM._clean_text("<script>alert('x')</script>clean text")
    assert "alert" not in result
    assert "clean text" in result


def test_clean_text_removes_style_tags() -> None:
    result = PM._clean_text("<style>.x { color: red }</style>visible")
    assert "color" not in result
    assert "visible" in result


def test_clean_text_collapses_whitespace() -> None:
    result = PM._clean_text("a   b\tc")
    assert "   " not in result
    assert "a" in result and "b" in result


def test_clean_text_truncates_at_limit() -> None:
    long_text = "x" * 2000
    result = PM._clean_text(long_text, limit=100)
    assert len(result) <= 100


def test_clean_text_none_returns_empty() -> None:
    result = PM._clean_text(None)
    assert result == ""


def test_clean_text_html_entities_unescaped() -> None:
    result = PM._clean_text("&amp; &lt; &gt;")
    assert "&amp;" not in result
    assert "&" in result


# ─── _extract_title ──────────────────────────────────────────────────────────

def test_extract_title_from_title_tag() -> None:
    html = "<html><head><title>Page Title</title></head></html>"
    assert PM._extract_title(html) == "Page Title"


def test_extract_title_falls_back_to_h1() -> None:
    html = "<html><body><h1>Main Heading</h1></body></html>"
    assert PM._extract_title(html) == "Main Heading"


def test_extract_title_no_tag_returns_empty() -> None:
    html = "<html><body><p>no title</p></body></html>"
    assert PM._extract_title(html) == ""


def test_extract_title_prefers_title_over_h1() -> None:
    html = "<html><head><title>Title Tag</title></head><body><h1>H1 Tag</h1></body></html>"
    assert PM._extract_title(html) == "Title Tag"


# ─── _ads_library_url ────────────────────────────────────────────────────────

def test_ads_library_url_meta() -> None:
    url = PM._ads_library_url("meta", "test query", "US")
    assert "facebook.com" in url
    assert "US" in url


def test_ads_library_url_facebook() -> None:
    url = PM._ads_library_url("facebook", "test query", "US")
    assert "facebook.com" in url
    assert "publisher_platforms" in url
    assert "facebook" in url


def test_ads_library_url_instagram() -> None:
    url = PM._ads_library_url("instagram", "brand", "JP")
    assert "facebook.com" in url
    assert "instagram" in url


def test_ads_library_url_whatsup_alias() -> None:
    url = PM._ads_library_url("whatsup", "brand", "JP")
    assert "facebook.com" in url
    assert "whatsapp" in url


def test_ads_library_url_google() -> None:
    url = PM._ads_library_url("google", "brand", "JP")
    assert "adstransparency.google.com" in url
    assert "JP" in url


def test_ads_library_url_linkedin() -> None:
    url = PM._ads_library_url("linkedin", "company", "ALL")
    assert "linkedin.com" in url


def test_ads_library_url_tiktok() -> None:
    url = PM._ads_library_url("tiktok", "keyword", "US")
    assert "tiktok.com" in url


def test_ads_library_url_x() -> None:
    url = PM._ads_library_url("x", "brand", "US")
    assert "ads.x.com" in url


def test_ads_library_url_line() -> None:
    url = PM._ads_library_url("line", "brand", "JP")
    assert "lycbiz.com" in url


def test_ads_library_url_telegram() -> None:
    url = PM._ads_library_url("telegram", "brand", "US")
    assert "ads.telegram.org" in url


def test_ads_library_url_unknown_platform_returns_empty() -> None:
    url = PM._ads_library_url("unknown", "q", "US")
    assert url == ""


def test_ads_library_url_country_uppercased() -> None:
    url = PM._ads_library_url("meta", "q", "us")
    assert "US" in url
