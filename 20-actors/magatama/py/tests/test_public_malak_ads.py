"""Unit tests for public-malak ad-library Zeebe primitives."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path as _P

_py_src = _P(__file__).resolve().parents[1] / "src"
if str(_py_src) not in sys.path:
    sys.path.insert(0, str(_py_src))

from pymagatama.primitives import public_malak_ads as M  # noqa: E402


class _Cursor:
    def __init__(self, rows=None, cols=None):
        self.sqls = []
        self.params = []
        self._rows = rows or []
        self.description = [(c,) for c in (cols or [])]
        self.rowcount = 1

    def execute(self, sql, params=None, **kwargs):
        self.sqls.append(sql)
        self.params.append(params)

    def fetchall(self):
        return self._rows


class _SyncCursorFactory:
    def __init__(self, cursors):
        self.cursors = list(cursors)
        self.opened = []

    def __call__(self):
        factory = self

        class _Ctx:
            def __enter__(self):
                cur = factory.cursors.pop(0) if factory.cursors else _Cursor()
                factory.opened.append(cur)
                return cur

            def __exit__(self, exc_type, exc, tb):
                return False

        return _Ctx()


def _insert_params(cursor, key):
    return next(params for params in cursor.params if isinstance(params, dict) and key in params)


def test_queue_seed_runs_inserts_scraper_run(monkeypatch):
    factory = _SyncCursorFactory([_Cursor(), _Cursor()])
    monkeypatch.setattr(M, "sync_cursor", factory)
    monkeypatch.setattr(M, "_utc_now", lambda: "2026-04-26T12:00:00Z")

    out = M.queue_seed_runs(
        seeds=[{"platform": "google", "queryKind": "search", "queryValue": "security", "country": "US"}],
    )

    assert out["queued"] == 1
    row = _insert_params(factory.opened[0], "platform")
    assert row["platform"] == "google"
    assert row["query_kind"] == "search"
    assert row["status"] == "queued"


def test_queue_seed_runs_normalizes_new_platform_alias(monkeypatch):
    factory = _SyncCursorFactory([_Cursor()])
    monkeypatch.setattr(M, "sync_cursor", factory)
    monkeypatch.setattr(M, "_utc_now", lambda: "2026-04-26T12:00:00Z")

    out = M.queue_seed_runs(
        seeds=[{"platform": "whatsup", "queryKind": "search", "queryValue": "security", "country": "JP"}],
    )

    assert out["queued"] == 1
    row = _insert_params(factory.opened[0], "platform")
    assert row["platform"] == "whatsapp"


def test_process_queue_claims_and_writes_observation(monkeypatch):
    run = (
        "at://did:web:public-malak.gftd.ai/ai.gftd.apps.publicMalak.adScraperRun/run-1",
        "google",
        "search",
        "security",
        "US",
        "2026-04-26T12:00:00Z",
    )
    select_cursor = _Cursor(
        rows=[run],
        cols=["vertex_id", "platform", "query_kind", "query_value", "country", "started_at"],
    )
    factory = _SyncCursorFactory([select_cursor])
    monkeypatch.setattr(M, "sync_cursor", factory)
    monkeypatch.setattr(M, "_fetch", lambda _url, _timeout: {
        "httpStatus": 200,
        "text": "<html><title>Security Ad</title><body>Sponsored security offer</body></html>",
        "error": "",
    })

    out = M.process_queue(max_runs=1)

    assert out["processed"] == 1
    assert out["completed"] == 1
    executed = "\n".join(sql for cur in factory.opened for sql in cur.sqls)
    assert "UPDATE vertex_ads_scraper_run SET status = %(status)s" in executed
    assert "INSERT INTO vertex_ads_advertiser" in executed
    assert "INSERT INTO vertex_ads_creative" in executed
    assert "INSERT INTO vertex_ads_snapshot" in executed


def test_async_task_process_queue(monkeypatch):
    monkeypatch.setattr(M, "process_queue", lambda max_runs, timeout_sec, platform, reclaim_after_sec: {
        "processed": max_runs,
        "timeoutSec": timeout_sec,
        "platform": platform,
        "reclaimAfterSec": reclaim_after_sec,
    })

    out = asyncio.run(M.task_process_queue(maxRuns=2, timeoutSec=3, platform="whatsup", reclaimAfterSec=120))

    assert out == {"processed": 2, "timeoutSec": 3.0, "platform": "whatsup", "reclaimAfterSec": 120}


def test_claim_runs_filters_platform_and_reclaims_stale_running(monkeypatch):
    select_cursor = _Cursor(
        rows=[(
            "run-1",
            "line",
            "search",
            "security",
            "JP",
            "2026-04-26T12:00:00Z",
        )],
        cols=["vertex_id", "platform", "query_kind", "query_value", "country", "started_at"],
    )
    factory = _SyncCursorFactory([select_cursor, _Cursor()])
    monkeypatch.setattr(M, "sync_cursor", factory)

    rows = M._claim_runs(1, platform="line", reclaim_after_sec=120)

    assert rows[0]["platform"] == "line"
    assert "platform = %(platform)s" in select_cursor.sqls[0]
    assert select_cursor.params[0]["platform"] == "line"
    assert "status = 'running'" in select_cursor.sqls[0]


def test_meta_parser_extracts_structured_ad_fields():
    parsed = M._parse_observation_fields(
        platform="instagram",
        query_value="shopify",
        country="DE",
        source_url="https://www.facebook.com/ads/library/?q=shopify",
        http_status=200,
        text=(
            '<script>{"adArchiveID":"1234567890","pageID":"998877",'
            '"pageName":"Example Brand","title":"Spring sale",'
            '"bodyText":"Save 20% on checkout","ctaText":"Shop Now",'
            '"linkUrl":"https://example.test/sale","isActive":true}</script>'
        ),
    )

    assert parsed["advertiserId"] == "998877"
    assert parsed["advertiserName"] == "Example Brand"
    assert parsed["adId"] == "1234567890"
    assert parsed["headline"] == "Spring sale"
    assert parsed["bodyText"] == "Save 20% on checkout"
    assert parsed["ctaText"] == "Shop Now"
    assert parsed["landingUrl"] == "https://example.test/sale"
    assert parsed["displayUrl"] == "example.test"
    assert parsed["creativeType"] == "meta-library-ad"
    assert parsed["parserVersion"] == "meta-ad-library-v1"


def test_write_observation_uses_meta_parser_fields(monkeypatch):
    run = {
        "vertex_id": "at://did:web:public-malak.gftd.ai/ai.gftd.apps.publicMalak.adScraperRun/run-meta-1",
        "platform": "facebook",
        "query_kind": "search",
        "query_value": "shopify",
        "country": "DE",
    }
    factory = _SyncCursorFactory([])
    monkeypatch.setattr(M, "sync_cursor", factory)
    monkeypatch.setattr(M, "_utc_now", lambda: "2026-04-26T12:30:00Z")

    out = M._write_observation(run, {
        "httpStatus": 200,
        "error": "",
        "text": (
            '<script>{"adArchiveID":"ad-777","pageID":"page-42",'
            '"pageName":"Meta Shop","title":"Checkout faster",'
            '"bodyText":"A structured ad body","linkUrl":"https://shop.example/ad"}</script>'
        ),
    })

    assert out["parseOk"] is True
    advertiser_row = _insert_params(factory.opened[0], "platform_advertiser_id")
    creative_row = _insert_params(factory.opened[1], "platform_ad_id")
    snapshot_row = _insert_params(factory.opened[2], "parser_version")
    assert advertiser_row["platform_advertiser_id"] == "page-42"
    assert advertiser_row["name"] == "Meta Shop"
    assert creative_row["platform_ad_id"] == "ad-777"
    assert creative_row["advertiser_name"] == "Meta Shop"
    assert creative_row["creative_type"] == "meta-library-ad"
    assert creative_row["headline"] == "Checkout faster"
    assert creative_row["body_text"] == "A structured ad body"
    assert creative_row["landing_url"] == "https://shop.example/ad"
    assert snapshot_row["parser_version"] == "meta-ad-library-v1"


def test_non_meta_platform_parser_extracts_json_and_meta_fields():
    parsed = M._parse_observation_fields(
        platform="linkedin",
        query_value="cloud security",
        country="US",
        source_url="https://www.linkedin.com/ad-library/search?keyword=cloud%20security&countries=US",
        http_status=200,
        text=(
            '<html><head><meta property="og:description" content="Cloud posture campaign"></head>'
            '<script>{"creativeId":"li-creative-1","companyId":"company-7",'
            '"companyName":"LinkedIn Brand","headline":"Secure cloud",'
            '"destinationUrl":"https://example.test/cloud"}</script></html>'
        ),
    )

    assert parsed["advertiserId"] == "company-7"
    assert parsed["advertiserName"] == "LinkedIn Brand"
    assert parsed["adId"] == "li-creative-1"
    assert parsed["headline"] == "Secure cloud"
    assert parsed["bodyText"] == "Cloud posture campaign"
    assert parsed["landingUrl"] == "https://example.test/cloud"
    assert parsed["creativeType"] == "linkedin-library-ad"
    assert parsed["parserVersion"] == "linkedin-ad-library-v1"


def test_non_meta_platform_parser_variants():
    cases = [
        ("x", '{"promotedTweetId":"tw-1","accountName":"X Brand","text":"Promoted body","url":"https://x.example/ad"}', "x-ad-library-v1"),
        ("line", '{"campaignId":"line-1","orgName":"LINE Brand","description":"LINE body","websiteUrl":"https://line.example/ad"}', "line-ad-library-v1"),
        ("telegram", '{"adId":"tg-1","advertiserName":"Telegram Brand","message":"Telegram body","landingUrl":"https://tg.example/ad"}', "telegram-ad-library-v1"),
    ]
    for platform, text, parser_version in cases:
        parsed = M._parse_observation_fields(
            platform=platform,
            query_value="security",
            country="JP",
            source_url=f"https://example.test/{platform}",
            http_status=200,
            text=text,
        )
        assert parsed["parserVersion"] == parser_version
        assert parsed["adId"]
        assert parsed["advertiserName"]
        assert parsed["landingUrl"].startswith("https://")


def test_analyze_creative_writes_intel_row(monkeypatch):
    creative = (
        "creative-1",
        "instagram",
        "ad-1",
        "adv-1",
        "Example Advertiser",
        "image",
        "Limited crypto offer",
        "Verify your login for a guaranteed reward",
        "https://example.test",
        "example.test",
        None,
        None,
        None,
        None,
        None,
        None,
        True,
        True,
        "https://source.test",
        "2026-04-26T12:00:00Z",
    )
    select_cursor = _Cursor(
        rows=[creative],
        cols=[
            "vertex_id",
            "platform",
            "platform_ad_id",
            "advertiser_vertex_id",
            "advertiser_name",
            "creative_type",
            "headline",
            "body_text",
            "landing_url",
            "display_url",
            "impressions_min",
            "impressions_max",
            "spend_min",
            "spend_max",
            "reach_min",
            "reach_max",
            "is_political",
            "is_active",
            "source_url",
            "last_seen_at",
        ],
    )
    factory = _SyncCursorFactory([select_cursor, _Cursor()])
    monkeypatch.setattr(M, "sync_cursor", factory)
    monkeypatch.setattr(M, "_utc_now", lambda: "2026-04-26T12:30:00Z")

    out = M.analyze_creative("creative-1", analysis_kind="adversarial")

    assert out["status"] == "completed"
    assert out["riskScorePermille"] > 500
    executed = "\n".join(sql for cur in factory.opened for sql in cur.sqls)
    assert "INSERT INTO vertex_ads_analysis" in executed
    row = _insert_params(factory.opened[1], "creative_vertex_id")
    assert row["creative_vertex_id"] == "creative-1"
    assert row["analysis_kind"] == "adversarial"


def test_async_task_analyze_creative(monkeypatch):
    monkeypatch.setattr(M, "analyze_creative", lambda creative_vertex_id, analysis_kind, model_id: {
        "creativeVertexId": creative_vertex_id,
        "analysisKind": analysis_kind,
        "modelId": model_id,
    })

    out = asyncio.run(M.task_analyze_creative(creativeVertexId="c1", analysisKind="claim", modelId="m1"))

    assert out == {"creativeVertexId": "c1", "analysisKind": "claim", "modelId": "m1"}


def test_analyze_recent_batches_unanalyzed_creatives(monkeypatch):
    monkeypatch.setattr(M, "_list_creatives_for_analysis", lambda **kwargs: ["c1", "c2"])
    monkeypatch.setattr(M, "analyze_creative", lambda creative_id, analysis_kind, model_id: {
        "creativeVertexId": creative_id,
        "analysisKind": analysis_kind,
        "modelId": model_id,
        "status": "completed",
    })

    out = M.analyze_recent(limit=2, platform="whatsup", analysis_kind="targeting", model_id="m1")

    assert out["analyzed"] == 2
    assert out["failed"] == 0
    assert out["platform"] == "whatsapp"
    assert [row["creativeVertexId"] for row in out["results"]] == ["c1", "c2"]


def test_async_task_analyze_recent(monkeypatch):
    monkeypatch.setattr(M, "analyze_recent", lambda **kwargs: kwargs)

    out = asyncio.run(M.task_analyze_recent(limit=3, platform="line", analysisKind="claim", modelId="m2"))

    assert out == {"limit": 3, "platform": "line", "analysis_kind": "claim", "model_id": "m2"}


def test_campaign_cluster_helpers_are_stable():
    creative = {
        "platform": "whatsup",
        "advertiser_vertex_id": "adv-1",
        "headline": "Limited cloud security offer",
        "body_text": "Verify your cloud posture today",
        "landing_url": "https://www.Example.test/path?utm=1",
    }

    assert M._landing_domain(creative["landing_url"]) == "example.test"
    assert M._claim_token(creative["headline"], creative["body_text"]).startswith("limited-cloud-security")
    assert M._campaign_key(creative, "platform") == M._campaign_key({**creative, "platform": "whatsapp"}, "platform")
    assert M._campaign_key(creative, "platform") != M._campaign_key({**creative, "platform": "line"}, "platform")
    assert M._campaign_key(creative, "cross_platform") == M._campaign_key({**creative, "platform": "line"}, "cross_platform")


def test_cluster_recent_creates_campaign_and_edge(monkeypatch):
    factory = _SyncCursorFactory([])
    monkeypatch.setattr(M, "sync_cursor", factory)
    monkeypatch.setattr(M, "_utc_now", lambda: "2026-04-26T12:30:00Z")
    monkeypatch.setattr(M, "_list_creatives_for_clustering", lambda **kwargs: ["creative-1"])
    monkeypatch.setattr(M, "_fetch_creative", lambda creative_id: {
        "vertex_id": creative_id,
        "platform": "linkedin",
        "platform_ad_id": "li-1",
        "advertiser_vertex_id": "adv-1",
        "advertiser_name": "Example Advertiser",
        "headline": "Secure cloud",
        "body_text": "Cloud posture campaign",
        "landing_url": "https://example.test/cloud",
        "display_url": "example.test",
        "is_political": False,
        "is_active": True,
        "last_seen_at": "2026-04-26T12:00:00Z",
    })

    out = M.cluster_recent(limit=1, platform="linkedin", platform_scope="cross_platform")

    assert out["clustered"] == 1
    assert out["failed"] == 0
    assert out["platformScope"] == "cross_platform"
    executed = "\n".join(sql for cur in factory.opened for sql in cur.sqls)
    assert "INSERT INTO vertex_ads_campaign_cluster" in executed
    assert "INSERT INTO edge_ads_creative_in_campaign" in executed
    campaign_row = _insert_params(factory.opened[0], "campaign_key")
    edge_row = _insert_params(factory.opened[1], "src_vid")
    assert campaign_row["landing_domain"] == "example.test"
    assert campaign_row["platform_scope"] == "cross_platform"
    assert edge_row["src_vid"] == "creative-1"
    assert edge_row["platform"] == "linkedin"


def test_async_task_cluster_recent(monkeypatch):
    monkeypatch.setattr(M, "cluster_recent", lambda **kwargs: kwargs)

    out = asyncio.run(M.task_cluster_recent(limit=5, platform="x", platformScope="platform"))

    assert out == {"limit": 5, "platform": "x", "platform_scope": "platform"}
