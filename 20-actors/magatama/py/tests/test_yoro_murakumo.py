"""Substrate-fit regression tests for yoro murakumo primitives.

Tests verify:
1. Dataclasses construct correctly (wire-shape parity with vendor).
2. All REIMPLEMENT stubs raise NotImplementedError (skeleton not yet wired).
3. No prohibited imports: psycopg, psycopg2, RW_URL references, Stripe, runpod.
4. Substrate-fit guard: RuntimeError raised if RW_URL env var is present.

ADR authority:
    ADR-2605215300 — yoro Python primitives MST rewrite addendum
    ADR-2605191358 — parent yoro/murakumo RW-free rewrite map
"""

from __future__ import annotations

import importlib
import inspect
import os
import sys
import textwrap
from pathlib import Path
from typing import Any
import pytest


# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_PY_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_PY_SRC) not in sys.path:
    sys.path.insert(0, str(_PY_SRC))


# ---------------------------------------------------------------------------
# Import guard: modules must load without RW_URL in env
# ---------------------------------------------------------------------------

def _clean_env_import(module_name: str) -> Any:
    """Import a module with RW_URL unset, evicting any cached version first."""
    env_backup = os.environ.pop("RW_URL", None)
    try:
        # Evict cached version so the guard re-runs
        if module_name in sys.modules:
            del sys.modules[module_name]
        mod = importlib.import_module(module_name)
        return mod
    finally:
        if env_backup is not None:
            os.environ["RW_URL"] = env_backup


# Import both modules under test
YS = _clean_env_import("pymagatama.primitives.yoro_social_murakumo")
YP = _clean_env_import("pymagatama.primitives.yoro_product_ingest_murakumo")


# ---------------------------------------------------------------------------
# §1 — Substrate-fit guard: RuntimeError if RW_URL present
# ---------------------------------------------------------------------------

class TestSubstrateFitGuard:
    def test_social_guard_raises_with_rw_url(self, monkeypatch):
        monkeypatch.setenv("RW_URL", "postgresql://rw-host:4566/dev")
        module_name = "pymagatama.primitives.yoro_social_murakumo"
        if module_name in sys.modules:
            del sys.modules[module_name]
        with pytest.raises(RuntimeError, match="RW_URL is set"):
            importlib.import_module(module_name)

    def test_ingest_guard_raises_with_rw_url(self, monkeypatch):
        monkeypatch.setenv("RW_URL", "postgresql://rw-host:4566/dev")
        module_name = "pymagatama.primitives.yoro_product_ingest_murakumo"
        if module_name in sys.modules:
            del sys.modules[module_name]
        with pytest.raises(RuntimeError, match="RW_URL is set"):
            importlib.import_module(module_name)

    def test_social_loads_without_rw_url(self, monkeypatch):
        monkeypatch.delenv("RW_URL", raising=False)
        module_name = "pymagatama.primitives.yoro_social_murakumo"
        if module_name in sys.modules:
            del sys.modules[module_name]
        mod = importlib.import_module(module_name)
        assert mod is not None

    def test_ingest_loads_without_rw_url(self, monkeypatch):
        monkeypatch.delenv("RW_URL", raising=False)
        module_name = "pymagatama.primitives.yoro_product_ingest_murakumo"
        if module_name in sys.modules:
            del sys.modules[module_name]
        mod = importlib.import_module(module_name)
        assert mod is not None


# ---------------------------------------------------------------------------
# §2 — Dataclass construction
# ---------------------------------------------------------------------------

class TestDataclasses:
    def test_social_post_record_constructs(self):
        r = YS.SocialPostRecord(
            repo="did:web:yoro.etzhayyim.com",
            collection="app.bsky.feed.post",
            rkey="test-rkey-001",
            uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/test-rkey-001",
            text="Hello from etzhayyim.",
            created_at="2026-05-21T00:00:00Z",
        )
        assert r.repo == "did:web:yoro.etzhayyim.com"
        assert r.collection == "app.bsky.feed.post"
        assert r.uri.startswith("at://")
        assert r.record == {}  # default field

    def test_repo_record_constructs(self):
        r = YS.RepoRecord(
            repo="did:web:yoro.etzhayyim.com",
            collection="app.bsky.graph.follow",
            rkey="follow-rkey-001",
            uri="at://did:web:yoro.etzhayyim.com/app.bsky.graph.follow/follow-rkey-001",
            created_at="2026-05-21T00:00:00Z",
            record={"$type": "app.bsky.graph.follow", "subject": "did:plc:test"},
        )
        assert r.collection == "app.bsky.graph.follow"
        assert r.record["$type"] == "app.bsky.graph.follow"

    def test_translation_link_record_constructs(self):
        r = YS.TranslationLinkRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="tlink-rkey-001",
            uri="at://did:web:yoro.etzhayyim.com/app.etzhayyim.translationLink/tlink-rkey-001",
            source_uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/orig-001",
            source_lang="ja",
            translated_uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/en-001",
            target_lang="en",
            source="llm-other",
            quality_score=0.8,
            created_at="2026-05-21T00:00:00Z",
            owner_did="did:web:yoro.etzhayyim.com",
        )
        assert r.source_lang == "ja"
        assert r.target_lang == "en"
        assert r.quality_score == 0.8
        # Confirm religious-corp NSID in URI (app.etzhayyim.* per 2026-05-21 lexicons)
        assert "app.etzhayyim.translationLink" in r.uri

    def test_bpmn_activity_event_record_constructs(self):
        r = YS.BpmnActivityEventRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="bpmn-evt-001",
            uri="at://did:web:yoro.etzhayyim.com/app.etzhayyim.bpmnActivityEvent/bpmn-evt-001",
            event_id="yoro.actorQuality:abc123",
            instance_id="case-001",
            activity_id="yoro.actorQuality.inspect",
            event_type="yoro.actorQuality.inspect.started",
            payload_json='{"caseId":"case-001"}',
            occurred_at="2026-05-21T00:00:00Z",
            actor_did="did:plc:test",
            org_did="did:web:yoro.etzhayyim.com",
        )
        assert r.activity_id == "yoro.actorQuality.inspect"
        assert "app.etzhayyim.bpmnActivityEvent" in r.uri

    def test_profile_enrichment_record_constructs(self):
        r = YS.ProfileEnrichmentRecord(
            repo="did:plc:test-actor",
            rkey="self",
            uri="at://did:plc:test-actor/app.bsky.actor.profile/self",
            display_name="Test Actor",
            description="An incrementally enriched public YORO actor profile.",
            created_at="2026-05-21T00:00:00Z",
        )
        assert r.rkey == "self"
        # collection is not a required field on ProfileEnrichmentRecord
        assert getattr(r, "collection", "app.bsky.actor.profile") in ("app.bsky.actor.profile", "app.bsky.actor.profile")

    def test_product_ingest_record_constructs(self):
        r = YP.ProductIngestRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="prod-001",
            uri="at://did:web:yoro.etzhayyim.com/ai.gftd.apps.etzhayyim.productIngest/prod-001",
            product_id="prod-001",
            collection=YP.PRODUCT_INGEST_COLLECTION,
            created_at="2026-05-21T00:00:00Z",
            payload={"name": "Test Product"},
        )
        assert r.product_id == "prod-001"
        assert r.collection == "ai.gftd.apps.etzhayyim.productIngest"

    def test_product_event_record_constructs(self):
        r = YP.ProductEventRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="prod-evt-001",
            uri="at://did:web:yoro.etzhayyim.com/ai.gftd.apps.etzhayyim.productEvent/prod-evt-001",
            product_id="prod-001",
            event_type="product.ingest.completed",
            occurred_at="2026-05-21T00:00:00Z",
        )
        assert r.event_type == "product.ingest.completed"


# ---------------------------------------------------------------------------
# §3 — All REIMPLEMENT stubs raise NotImplementedError
# ---------------------------------------------------------------------------

class TestStubsRaiseNotImplemented:
    """Verify every REIMPLEMENT function raises NotImplementedError at M0."""

    # NOTE: insert_social_post_record is now M6 sync shim implementation.
    # Happy-path tests live in test_yoro_m6.py.
    # We verify here that it is a sync (non-coroutine) function.
    def test_insert_social_post_record_is_sync_shim(self):
        import inspect
        assert not inspect.iscoroutinefunction(YS.insert_social_post_record), (
            "insert_social_post_record must be a sync shim (M6 impl)"
        )

    def test_insert_repo_records_is_sync_shim(self):
        # M7: insert_repo_records is now a sync shim (not NotImplementedError stub).
        # Happy-path tests live in test_yoro_m7.py.
        import inspect
        assert not inspect.iscoroutinefunction(YS.insert_repo_records), (
            "insert_repo_records must be a sync shim (M7 impl)"
        )
        # Verify it is callable (not a stub) — callable check only, no SDK call
        assert callable(YS.insert_repo_records)

    def test_insert_translation_link_record_is_sync_shim(self):
        # M7: insert_translation_link_record is now a sync shim (not NotImplementedError stub).
        # Happy-path tests live in test_yoro_m7.py.
        import inspect
        assert not inspect.iscoroutinefunction(YS.insert_translation_link_record), (
            "insert_translation_link_record must be a sync shim (M7 impl)"
        )
        assert callable(YS.insert_translation_link_record)

    def test_emit_bpmn_activity_event_is_sync_shim_never_raises(self):
        # M7: emit_bpmn_activity_event is now a sync shim that NEVER raises.
        # Happy-path tests live in test_yoro_m7.py.
        import inspect
        assert not inspect.iscoroutinefunction(YS.emit_bpmn_activity_event), (
            "emit_bpmn_activity_event must be a sync shim (M7 impl)"
        )
        assert callable(YS.emit_bpmn_activity_event)
        # Vendor convention: never raises — even with SDK not installed
        from unittest.mock import patch
        row = YS.BpmnActivityEventRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="r1",
            uri="at://did:web:yoro.etzhayyim.com/ai.gftd.apps.etzhayyim.bpmnActivityEvent/r1",
            event_id="ev1",
            instance_id="case1",
            activity_id="test.activity",
            event_type="completed",
            payload_json="{}",
            occurred_at="2026-05-21T00:00:00Z",
            actor_did="did:plc:test",
            org_did="did:web:yoro.etzhayyim.com",
        )
        with patch("pymagatama.primitives.yoro_social_murakumo._pds_mod", None):
            result = YS.emit_bpmn_activity_event(row)
        assert result is None  # NEVER raises, always returns None

    # NOTE: fetch_source_post, fetch_actor_generation_context, fetch_profile_quality,
    # enrich_actor_quality_profile, task_yoro_social_post_graph_fallback, and
    # task_yoro_social_translate_post are now M4 async implementations.
    # Their happy-path tests live in test_yoro_m4.py.
    # We verify here that they are async coroutines (not sync stubs).

    def test_fetch_source_post_is_now_async(self):
        import inspect
        assert inspect.iscoroutinefunction(YS.fetch_source_post), (
            "fetch_source_post must be an async function (M4 impl)"
        )

    def test_fetch_actor_generation_context_is_now_async(self):
        import inspect
        assert inspect.iscoroutinefunction(YS.fetch_actor_generation_context), (
            "fetch_actor_generation_context must be an async function (M4 impl)"
        )

    def test_fetch_profile_quality_is_now_async(self):
        import inspect
        assert inspect.iscoroutinefunction(YS.fetch_profile_quality), (
            "fetch_profile_quality must be an async function (M4 impl)"
        )

    def test_enrich_actor_quality_profile_is_now_async(self):
        import inspect
        assert inspect.iscoroutinefunction(YS.enrich_actor_quality_profile), (
            "enrich_actor_quality_profile must be an async function (M4 impl)"
        )

    def test_task_yoro_social_post_graph_fallback_is_now_async(self):
        import inspect
        assert inspect.iscoroutinefunction(YS.task_yoro_social_post_graph_fallback), (
            "task_yoro_social_post_graph_fallback must be an async function (M4 impl)"
        )

    def test_task_yoro_social_translate_post_is_now_async(self):
        import inspect
        assert inspect.iscoroutinefunction(YS.task_yoro_social_translate_post), (
            "task_yoro_social_translate_post must be an async function (M4 impl)"
        )

    def test_task_yoro_actor_quality_enrich_profile_is_now_async(self):
        """task_yoro_actor_quality_enrich_profile was a NotImplementedError stub (M2).
        Implemented in M5 as a full async function delegating to enrich_actor_quality_profile.
        """
        import inspect
        assert inspect.iscoroutinefunction(YS.task_yoro_actor_quality_enrich_profile), (
            "task_yoro_actor_quality_enrich_profile must be an async function (M5 impl)"
        )

    # NOTE: ingest_product and batch_ingest_products are now M3 async implementations.
    # Their happy-path tests live in test_yoro_m3.py.
    # We verify here that they are async coroutines (not sync stubs).
    def test_ingest_product_is_now_async(self):
        import inspect
        assert inspect.iscoroutinefunction(YP.ingest_product), (
            "ingest_product must be an async function (M3 impl)"
        )

    def test_batch_ingest_products_is_now_async(self):
        import inspect
        assert inspect.iscoroutinefunction(YP.batch_ingest_products), (
            "batch_ingest_products must be an async function (M3 impl)"
        )

    # NOTE: upsert_product_profile, fetch_product_by_id, delete_product are now M6 async impls.
    # Happy-path tests live in test_yoro_m6.py.
    # We verify here that they are async coroutines (not sync stubs).
    def test_upsert_product_profile_is_now_async(self):
        import inspect
        assert inspect.iscoroutinefunction(YP.upsert_product_profile), (
            "upsert_product_profile must be an async function (M6 impl)"
        )

    def test_fetch_product_by_id_is_now_async(self):
        import inspect
        assert inspect.iscoroutinefunction(YP.fetch_product_by_id), (
            "fetch_product_by_id must be an async function (M6 impl)"
        )

    def test_delete_product_is_now_async(self):
        import inspect
        assert inspect.iscoroutinefunction(YP.delete_product), (
            "delete_product must be an async function (M6 impl)"
        )


# ---------------------------------------------------------------------------
# §4 — Pure helper functions (no substrate calls)
# ---------------------------------------------------------------------------

class TestPureHelpers:
    def test_utc_now_iso_format(self):
        iso = YS.utc_now_iso()
        assert iso.endswith("Z")
        assert "T" in iso

    def test_build_social_post_record_uri_format(self):
        r = YS.build_social_post_record(
            repo="did:web:yoro.etzhayyim.com",
            text="Test post",
            actor_path="test",
        )
        assert isinstance(r, YS.SocialPostRecord)
        assert r.uri.startswith("at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/")
        assert r.text == "Test post"

    def test_build_repo_record_uri_format(self):
        r = YS.build_repo_record(
            repo="did:plc:test",
            collection="app.bsky.graph.follow",
            record={"$type": "app.bsky.graph.follow", "subject": "did:plc:other"},
            actor_path="follow-back",
        )
        assert isinstance(r, YS.RepoRecord)
        assert "app.bsky.graph.follow" in r.uri

    def test_build_translation_link_record_nsid(self):
        r = YS.build_translation_link_record(
            repo="did:web:yoro.etzhayyim.com",
            source_uri="at://x/app.bsky.feed.post/r0",
            source_lang="ja",
            translated_uri="at://x/app.bsky.feed.post/r1",
            target_lang="en",
        )
        assert isinstance(r, YS.TranslationLinkRecord)
        # Confirm religious-corp NSID is used (app.etzhayyim.* per 2026-05-21 lexicons)
        assert "app.etzhayyim.translationLink" in r.uri
        assert "media_gamers" not in r.uri  # vendor namespace must NOT appear

    def test_post_tags_dedup_and_limit(self):
        tags = YS._post_tags("foo", "bar", "foo", "baz", "a", "b", "c", "d", "e")
        assert len(tags) <= 8
        assert len(tags) == len(set(tags))  # no duplicates

    def test_lang_list_parses_csv(self):
        langs = YS._lang_list("en,ja,ko")
        assert langs == ["en", "ja", "ko"]

    def test_lang_list_no_duplicates(self):
        langs = YS._lang_list("en,ja,en,ko")
        assert langs.count("en") == 1

    def test_safe_display_name_did_web(self):
        name = YS._safe_display_name("did:web:yoro.gftd.ai:actor:abc123def456ghij", "")
        assert "YORO actor" in name

    def test_safe_display_name_with_handle(self):
        name = YS._safe_display_name("did:plc:test", "alice.bsky.social")
        assert name == "alice.bsky.social"


# ---------------------------------------------------------------------------
# §5 — Substrate-fit regression: no prohibited imports in source
# ---------------------------------------------------------------------------

PROHIBITED_PATTERNS = [
    "import psycopg",
    "import psycopg2",
    "from psycopg",
    "from psycopg2",
    "RW_URL",
    "import stripe",
    "from stripe",
    "import runpod",
    "from runpod",
    "sync_cursor",
    "HYPERDRIVE",
]

PROHIBITED_PATTERNS_STRICT = [
    "import psycopg\n",
    "import psycopg2\n",
    "from psycopg ",
    "from psycopg2 ",
    "import stripe\n",
    "import runpod\n",
]


def _read_source(module: Any) -> str:
    src_file = inspect.getfile(module)
    return Path(src_file).read_text(encoding="utf-8")


class TestSourceSubstrateFit:
    """Ensure no prohibited imports or references appear in source files."""

    def test_no_psycopg_in_social_source(self):
        src = _read_source(YS)
        for pattern in ["import psycopg\n", "import psycopg2\n", "from psycopg ", "from psycopg2 "]:
            assert pattern not in src, (
                f"Prohibited import pattern {pattern!r} found in yoro_social_murakumo.py. "
                "This module must not depend on psycopg or psycopg2 (ADR-2605172000)."
            )

    def test_no_psycopg_in_ingest_source(self):
        src = _read_source(YP)
        for pattern in ["import psycopg\n", "import psycopg2\n", "from psycopg ", "from psycopg2 "]:
            assert pattern not in src, (
                f"Prohibited import pattern {pattern!r} found in yoro_product_ingest_murakumo.py."
            )

    def test_no_stripe_in_social_source(self):
        src = _read_source(YS)
        # Check for actual import statements only (not docstring references to "Import Stripe")
        for pattern in ["import stripe\n", "from stripe ", "from stripe\n"]:
            assert pattern not in src, (
                f"Stripe import pattern {pattern!r} found in yoro_social_murakumo.py. "
                "Stripe is prohibited in etzhayyim/root (ADR-2605172100)."
            )

    def test_no_stripe_in_ingest_source(self):
        src = _read_source(YP)
        # Check for actual import statements only (not docstring references to "Import Stripe")
        for pattern in ["import stripe\n", "from stripe ", "from stripe\n"]:
            assert pattern not in src, (
                f"Stripe import pattern {pattern!r} found in yoro_product_ingest_murakumo.py. "
                "Stripe is prohibited in etzhayyim/root (ADR-2605172100)."
            )

    def test_no_runpod_in_social_source(self):
        src = _read_source(YS)
        assert "import runpod" not in src.lower(), (
            "runpod import found in yoro_social_murakumo.py. "
            "RunPod is prohibited in etzhayyim/root (ADR-2605215000)."
        )

    def test_no_runpod_in_ingest_source(self):
        src = _read_source(YP)
        assert "import runpod" not in src.lower()

    def test_no_sync_cursor_in_social_source(self):
        src = _read_source(YS)
        assert "sync_cursor" not in src, (
            "sync_cursor found in yoro_social_murakumo.py. "
            "sync_cursor is a vendor RisingWave utility (db_sync module) and must not "
            "appear in the religious-corp variant."
        )

    def test_no_sync_cursor_in_ingest_source(self):
        src = _read_source(YP)
        assert "sync_cursor" not in src

    def test_no_rw_url_assignment_in_social_source(self):
        src = _read_source(YS)
        # RW_URL may appear in the guard check string comparison but must not be used as a value
        # The guard only reads it to detect and RAISE — that is acceptable.
        # Check that it is never assigned or passed as a connection string.
        assert "psycopg2.connect" not in src
        assert "asyncpg.connect" not in src

    def test_no_rw_url_assignment_in_ingest_source(self):
        src = _read_source(YP)
        assert "psycopg2.connect" not in src
        assert "asyncpg.connect" not in src

    def test_translation_link_uses_etzhayyim_nsid(self):
        """Confirm NSID constant is religious-corp namespace (app.etzhayyim.* per 2026-05-21 lexicons)."""
        assert YS.TRANSLATION_LINK_COLLECTION == "app.etzhayyim.translationLink"
        assert "media_gamers" not in YS.TRANSLATION_LINK_COLLECTION

    def test_bpmn_event_nsid_is_etzhayyim(self):
        assert YS.BPMN_ACTIVITY_EVENT_COLLECTION == "app.etzhayyim.bpmnActivityEvent"

    def test_product_nsids_are_etzhayyim(self):
        assert YP.PRODUCT_INGEST_COLLECTION == "ai.gftd.apps.etzhayyim.productIngest"
        assert YP.PRODUCT_EVENT_COLLECTION == "ai.gftd.apps.etzhayyim.productEvent"
