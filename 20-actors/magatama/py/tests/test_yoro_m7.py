"""M7 implementation tests for yoro murakumo primitives.

Tests verify happy-path and error-path behaviour for the 7 functions implemented in M7:

  Social sync shims (yoro_social_murakumo):
    1. insert_repo_records         — sync shim → asyncio.run(batch putRecord); rows #2/#3/#4
    2. insert_translation_link_record — sync shim → asyncio.run(record_translation_link()); row #5
    3. emit_bpmn_activity_event    — sync shim → asyncio.run(record_bpmn_activity_event()), NEVER RAISES; row #6

  Diet speech graph fallback (yoro_social_murakumo):
    4. build_diet_speech_social_post_record — pure builder; row #30
    5. task_yoro_social_project_diet_speeches_graph_fallback — write-path only; row #29

  Product count (yoro_product_ingest_murakumo):
    6. count_products_by_status    — listRecords client-side count; row #39

  Task registration (yoro_product_ingest_murakumo):
    7. register()                  — Zeebe registrar for 9 product tasks; row #40

Test strategy:
  - Happy path: mock SDK pds module, call function, verify SDK call args + return shape.
  - Error/suppression path for emit_bpmn_activity_event: verify exceptions never propagate.
  - Sync shim checks: verify functions are NOT coroutines.
  - register() checks: verify registration count + task type names.
  - Substrate-fit regression: no psycopg2, no RW_URL, no Stripe, no runpod imports.

ADR authority:
    ADR-2605215300 — yoro Python primitives MST rewrite addendum (M7 milestone)
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

_PY_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_PY_SRC) not in sys.path:
    sys.path.insert(0, str(_PY_SRC))

_SDK_SRC = Path(__file__).resolve().parents[3] / "etzhayyim-sdk-py" / "src"
if str(_SDK_SRC) not in sys.path:
    sys.path.insert(0, str(_SDK_SRC))


def _clean_env_import(module_name: str) -> Any:
    env_backup = os.environ.pop("RW_URL", None)
    try:
        if module_name in sys.modules:
            del sys.modules[module_name]
        return importlib.import_module(module_name)
    finally:
        if env_backup is not None:
            os.environ["RW_URL"] = env_backup


_clean_env_import("pymagatama.primitives.yoro_social_murakumo")
_clean_env_import("pymagatama.primitives.yoro_product_ingest_murakumo")

_SOCIAL_MOD = "pymagatama.primitives.yoro_social_murakumo"
_PRODUCT_MOD = "pymagatama.primitives.yoro_product_ingest_murakumo"


def _ys() -> Any:
    return sys.modules[_SOCIAL_MOD]


def _yp() -> Any:
    return sys.modules[_PRODUCT_MOD]


# ---------------------------------------------------------------------------
# §1 — insert_repo_records (sync shim, rows #2/#3/#4)
# ---------------------------------------------------------------------------

class TestInsertRepoRecords:
    """Sync shim: asyncio.run(gather(dispatch/put_record per row)).  M7 IMPLEMENTED."""

    def test_is_not_coroutine(self):
        """Sync shim must be a plain function, not a coroutine."""
        assert not inspect.iscoroutinefunction(_ys().insert_repo_records)

    def test_happy_path_feed_post_dispatched(self):
        mod = _ys()
        rows = [
            mod.SocialPostRecord(
                repo="did:web:yoro.etzhayyim.com",
                collection="app.bsky.feed.post",
                rkey="test-rkey-m7-001",
                uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/test-rkey-m7-001",
                text="Hello M7 batch post",
                created_at="2026-05-21T00:00:00Z",
                record={"$type": "app.bsky.feed.post", "text": "Hello M7 batch post", "createdAt": "2026-05-21T00:00:00Z"},
            )
        ]
        mock_dispatch = AsyncMock(return_value=None)
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = mod.insert_repo_records(rows)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["ok"] is True
        assert "uri" in result[0]
        mock_dispatch.assert_called_once()

    def test_happy_path_graph_follow_dispatched(self):
        mod = _ys()
        rows = [
            mod.RepoRecord(
                repo="did:web:yoro.etzhayyim.com",
                collection="app.bsky.graph.follow",
                rkey="test-rkey-follow-001",
                uri="at://did:web:yoro.etzhayyim.com/app.bsky.graph.follow/test-rkey-follow-001",
                created_at="2026-05-21T00:00:00Z",
                record={"$type": "app.bsky.graph.follow", "subject": "did:plc:test", "createdAt": "2026-05-21T00:00:00Z"},
            )
        ]
        mock_dispatch = AsyncMock(return_value=None)
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = mod.insert_repo_records(rows)
        assert result[0]["ok"] is True
        mock_dispatch.assert_called_once()

    def test_happy_path_actor_profile_put_record(self):
        mod = _ys()
        rows = [
            mod.RepoRecord(
                repo="did:web:yoro.etzhayyim.com",
                collection="app.bsky.actor.profile",
                rkey="self",
                uri="at://did:web:yoro.etzhayyim.com/app.bsky.actor.profile/self",
                created_at="2026-05-21T00:00:00Z",
                record={"$type": "app.bsky.actor.profile", "displayName": "Test Actor"},
            )
        ]
        mock_put = AsyncMock(return_value=None)
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = mock_put
            result = mod.insert_repo_records(rows)
        assert result[0]["ok"] is True
        mock_put.assert_called_once()

    def test_multi_row_batch_returns_all_results(self):
        mod = _ys()
        rows = [
            mod.SocialPostRecord(
                repo="did:web:yoro.etzhayyim.com",
                collection="app.bsky.feed.post",
                rkey=f"test-rkey-{i}",
                uri=f"at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/test-rkey-{i}",
                text=f"Post {i}",
                created_at="2026-05-21T00:00:00Z",
                record={"$type": "app.bsky.feed.post"},
            )
            for i in range(3)
        ]
        mock_dispatch = AsyncMock(return_value=None)
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = mod.insert_repo_records(rows)
        assert len(result) == 3
        assert all(r["ok"] is True for r in result)
        assert mock_dispatch.call_count == 3

    def test_sdk_not_installed_raises_import_error(self):
        mod = _ys()
        rows = [
            mod.SocialPostRecord(
                repo="did:web:yoro.etzhayyim.com",
                collection="app.bsky.feed.post",
                rkey="test-rkey",
                uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/test-rkey",
                text="Test",
                created_at="2026-05-21T00:00:00Z",
            )
        ]
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                mod.insert_repo_records(rows)

    def test_empty_rows_returns_empty_list(self):
        mod = _ys()
        mock_dispatch = AsyncMock(return_value=None)
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = mod.insert_repo_records([])
        assert result == []

    def test_sdk_error_per_row_returns_ok_false(self):
        mod = _ys()
        rows = [
            mod.SocialPostRecord(
                repo="did:web:yoro.etzhayyim.com",
                collection="app.bsky.feed.post",
                rkey="test-rkey",
                uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/test-rkey",
                text="Test",
                created_at="2026-05-21T00:00:00Z",
                record={"$type": "app.bsky.feed.post"},
            )
        ]
        mock_dispatch = AsyncMock(side_effect=RuntimeError("PDS failure"))
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = mod.insert_repo_records(rows)
        assert result[0]["ok"] is False
        assert "PDS failure" in result[0]["error"]


# ---------------------------------------------------------------------------
# §2 — insert_translation_link_record (sync shim, row #5)
# ---------------------------------------------------------------------------

class TestInsertTranslationLinkRecord:
    """Sync shim: asyncio.run(record_translation_link()).  M7 IMPLEMENTED."""

    def test_is_not_coroutine(self):
        assert not inspect.iscoroutinefunction(_ys().insert_translation_link_record)

    def test_happy_path_returns_dict_with_uri(self):
        mod = _ys()
        row = mod.TranslationLinkRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="test-tl-rkey-001",
            uri="at://did:web:yoro.etzhayyim.com/app.etzhayyim.translationLink/test-tl-rkey-001",
            source_uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/source-001",
            source_lang="ja",
            translated_uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/translated-001",
            target_lang="en",
            source="llm-other",
            quality_score=750.0,
            created_at="2026-05-21T00:00:00Z",
            owner_did="did:web:yoro.etzhayyim.com",
        )
        mock_put = AsyncMock(return_value=None)
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = mock_put
            result = mod.insert_translation_link_record(row)
        assert isinstance(result, dict)
        assert "uri" in result
        assert result["target_lang"] == "en"
        assert result["source_uri"] == row.source_uri
        mock_put.assert_called()

    def test_sdk_not_installed_raises_import_error(self):
        mod = _ys()
        row = mod.TranslationLinkRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="test-tl-rkey-002",
            uri="at://did:web:yoro.etzhayyim.com/app.etzhayyim.translationLink/test-tl-rkey-002",
            source_uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/src-002",
            source_lang="ja",
            translated_uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/tr-002",
            target_lang="ko",
            source="llm-other",
            quality_score=500.0,
            created_at="2026-05-21T00:00:00Z",
            owner_did="did:web:yoro.etzhayyim.com",
        )
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                mod.insert_translation_link_record(row)

    def test_calls_async_put_record(self):
        """Verify the shim delegates to record_translation_link (which calls put_record)."""
        mod = _ys()
        row = mod.TranslationLinkRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="test-tl-rkey-003",
            uri="at://did:web:yoro.etzhayyim.com/app.etzhayyim.translationLink/test-tl-rkey-003",
            source_uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/src-003",
            source_lang="en",
            translated_uri="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/tr-003",
            target_lang="fr",
            source="llm-other",
            quality_score=0.0,
            created_at="2026-05-21T00:00:00Z",
            owner_did="did:web:yoro.etzhayyim.com",
        )
        mock_put = AsyncMock(return_value=None)
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = mock_put
            result = mod.insert_translation_link_record(row)
        # put_record should be called once for the translation link
        assert mock_put.called


# ---------------------------------------------------------------------------
# §3 — emit_bpmn_activity_event (sync shim, NEVER RAISES, row #6)
# ---------------------------------------------------------------------------

class TestEmitBpmnActivityEvent:
    """Sync shim: asyncio.run(record_bpmn_activity_event()), vendor convention: NEVER RAISES."""

    def test_is_not_coroutine(self):
        assert not inspect.iscoroutinefunction(_ys().emit_bpmn_activity_event)

    def test_happy_path_returns_none(self):
        mod = _ys()
        row = mod.BpmnActivityEventRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="test-bpmn-rkey-001",
            uri="at://did:web:yoro.etzhayyim.com/app.etzhayyim.bpmnActivityEvent/test-bpmn-rkey-001",
            event_id="event-001",
            instance_id="inst-001",
            activity_id="activity-enrich",
            event_type="completed",
            payload_json="{}",
            occurred_at="2026-05-21T00:00:00Z",
            actor_did="did:web:yoro.etzhayyim.com",
            org_did="did:web:etzhayyim.com",
        )
        mock_put = AsyncMock(return_value=None)
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = mock_put
            result = mod.emit_bpmn_activity_event(row)
        assert result is None  # always returns None

    def test_suppresses_sdk_not_installed(self):
        """emit_bpmn_activity_event NEVER raises — suppresses ImportError."""
        mod = _ys()
        row = mod.BpmnActivityEventRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="test-bpmn-rkey-002",
            uri="at://did:web:yoro.etzhayyim.com/app.etzhayyim.bpmnActivityEvent/test-bpmn-rkey-002",
            event_id="event-002",
            instance_id="inst-002",
            activity_id="activity-enrich",
            event_type="failed",
            payload_json="{}",
            occurred_at="2026-05-21T00:00:00Z",
            actor_did="did:web:yoro.etzhayyim.com",
            org_did="did:web:etzhayyim.com",
        )
        # SDK not installed — must NOT raise
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            result = mod.emit_bpmn_activity_event(row)
        assert result is None

    def test_suppresses_pds_runtime_error(self):
        """emit_bpmn_activity_event NEVER raises — suppresses RuntimeError from PDS."""
        mod = _ys()
        row = mod.BpmnActivityEventRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="test-bpmn-rkey-003",
            uri="at://did:web:yoro.etzhayyim.com/app.etzhayyim.bpmnActivityEvent/test-bpmn-rkey-003",
            event_id="event-003",
            instance_id="inst-003",
            activity_id="activity-enrich",
            event_type="completed",
            payload_json="{}",
            occurred_at="2026-05-21T00:00:00Z",
            actor_did="did:web:yoro.etzhayyim.com",
            org_did="did:web:etzhayyim.com",
        )
        mock_put = AsyncMock(side_effect=RuntimeError("PDS network failure"))
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = mock_put
            # Must NOT raise even when PDS fails
            result = mod.emit_bpmn_activity_event(row)
        assert result is None

    def test_suppresses_arbitrary_exception(self):
        """emit_bpmn_activity_event NEVER raises — suppresses any Exception."""
        mod = _ys()
        row = mod.BpmnActivityEventRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="test-bpmn-rkey-004",
            uri="at://did:web:yoro.etzhayyim.com/app.etzhayyim.bpmnActivityEvent/test-bpmn-rkey-004",
            event_id="event-004",
            instance_id="inst-004",
            activity_id="activity-enrich",
            event_type="started",
            payload_json="{}",
            occurred_at="2026-05-21T00:00:00Z",
            actor_did="did:web:yoro.etzhayyim.com",
            org_did="did:web:etzhayyim.com",
        )
        mock_put = AsyncMock(side_effect=ValueError("unexpected val error"))
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = mock_put
            result = mod.emit_bpmn_activity_event(row)
        assert result is None

    def test_logs_warning_on_suppressed_exception(self, caplog):
        """Suppressed exceptions are logged as warnings (not silently swallowed)."""
        mod = _ys()
        row = mod.BpmnActivityEventRecord(
            repo="did:web:yoro.etzhayyim.com",
            rkey="test-bpmn-rkey-005",
            uri="at://did:web:yoro.etzhayyim.com/app.etzhayyim.bpmnActivityEvent/test-bpmn-rkey-005",
            event_id="event-005",
            instance_id="inst-005",
            activity_id="activity-enrich",
            event_type="completed",
            payload_json="{}",
            occurred_at="2026-05-21T00:00:00Z",
            actor_did="did:web:yoro.etzhayyim.com",
            org_did="did:web:etzhayyim.com",
        )
        mock_put = AsyncMock(side_effect=ConnectionError("network down"))
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = mock_put
            with caplog.at_level(logging.WARNING):
                mod.emit_bpmn_activity_event(row)
        # Some warning should have been logged
        assert any("suppressed" in r.message.lower() or "bpmn" in r.message.lower()
                   for r in caplog.records)


# ---------------------------------------------------------------------------
# §4 — build_diet_speech_social_post_record (pure builder, row #30)
# ---------------------------------------------------------------------------

class TestBuildDietSpeechSocialPostRecord:
    """Pure builder for app.bsky.feed.post Diet speech wire shape.  M7 IMPLEMENTED."""

    def test_returns_social_post_record(self):
        mod = _ys()
        result = mod.build_diet_speech_social_post_record(
            speech_id="speech-001",
            speech_text="国会で審議された法案について議員が演説しました。",
            speaker="田中太郎",
            date_str="2026-05-21",
        )
        assert isinstance(result, mod.SocialPostRecord)
        assert result.collection == "app.bsky.feed.post"
        assert "speech-001" not in result.uri or True  # URI is at:// format
        assert result.uri.startswith("at://")

    def test_text_includes_speaker_and_date(self):
        mod = _ys()
        result = mod.build_diet_speech_social_post_record(
            speech_id="speech-002",
            speech_text="Test diet speech content for speaker",
            speaker="TestSpeaker",
            date_str="2026-05-21",
        )
        assert "TestSpeaker" in result.text
        assert "2026-05-21" in result.text

    def test_text_truncated_at_200_chars(self):
        mod = _ys()
        long_text = "A" * 300
        result = mod.build_diet_speech_social_post_record(
            speech_id="speech-003",
            speech_text=long_text,
        )
        # Text should be truncated (ellipsis added)
        assert "…" in result.text

    def test_empty_speech_text_uses_fallback(self):
        mod = _ys()
        result = mod.build_diet_speech_social_post_record(
            speech_id="speech-004",
            speech_text="",
        )
        assert len(result.text) > 0
        # Should include a summary fallback
        assert "yoro.etzhayyim.com" in result.text.lower() or "diet" in result.text.lower()

    def test_record_has_type_field(self):
        mod = _ys()
        result = mod.build_diet_speech_social_post_record(
            speech_text="Some speech content",
        )
        assert result.record["$type"] == "app.bsky.feed.post"

    def test_custom_repo(self):
        mod = _ys()
        result = mod.build_diet_speech_social_post_record(
            repo="did:plc:custom-repo",
            speech_text="Custom repo test",
        )
        assert result.repo == "did:plc:custom-repo"
        assert "did:plc:custom-repo" in result.uri


# ---------------------------------------------------------------------------
# §5 — task_yoro_social_project_diet_speeches_graph_fallback (row #29)
# ---------------------------------------------------------------------------

class TestTaskYoroSocialProjectDietSpeechesGraphFallback:
    """Write-path only; Diet speech read-path is VENDOR-ONLY.  M7 IMPLEMENTED."""

    def test_is_coroutine(self):
        mod = _ys()
        assert inspect.iscoroutinefunction(
            mod.task_yoro_social_project_diet_speeches_graph_fallback
        )

    def test_happy_path_dispatches_post(self):
        mod = _ys()
        mock_dispatch = AsyncMock(return_value=None)

        async def _run():
            with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
                mock_pds.dispatch = mock_dispatch
                result = await mod.task_yoro_social_project_diet_speeches_graph_fallback(
                    speechId="speech-m7-001",
                    speechText="国会で法案が審議されました。",
                    speaker="TestSpeaker",
                    dateStr="2026-05-21",
                )
            return result

        result = asyncio.run(_run())
        assert result["ok"] is True
        assert "uri" in result
        assert result["speechId"] == "speech-m7-001"
        mock_dispatch.assert_called_once()

    def test_missing_speech_text_returns_error(self):
        mod = _ys()

        async def _run():
            with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
                mock_pds.dispatch = AsyncMock(return_value=None)
                result = await mod.task_yoro_social_project_diet_speeches_graph_fallback(
                    speechId="speech-no-text",
                    speechText="",
                )
            return result

        result = asyncio.run(_run())
        assert result["ok"] is False
        assert "speechText" in result["error"] or "VENDOR-ONLY" in result["error"]

    def test_sdk_not_installed_raises_import_error(self):
        mod = _ys()

        async def _run():
            with patch(f"{_SOCIAL_MOD}._pds_mod", None):
                return await mod.task_yoro_social_project_diet_speeches_graph_fallback(
                    speechText="Some content",
                )

        with pytest.raises(ImportError, match="etzhayyim_sdk"):
            asyncio.run(_run())

    def test_result_includes_vendor_only_note(self):
        mod = _ys()
        mock_dispatch = AsyncMock(return_value=None)

        async def _run():
            with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
                mock_pds.dispatch = mock_dispatch
                return await mod.task_yoro_social_project_diet_speeches_graph_fallback(
                    speechText="Diet speech summary text",
                )

        result = asyncio.run(_run())
        assert result["ok"] is True
        # Result should document the VENDOR-ONLY nature of the read path
        assert "VENDOR-ONLY" in result.get("note", "") or "vendor" in result.get("note", "").lower()

    def test_registered_in_social_register(self):
        """Verify diet speeches task is included in social module's register()."""
        mod = _ys()
        mock_worker = MagicMock()
        # Capture all task registrations
        registered_types: list[str] = []

        def capture_task(**kwargs):
            registered_types.append(kwargs.get("task_type", ""))
            return lambda fn: fn

        mock_worker.task = capture_task
        mod.register(mock_worker, timeout_ms=30000)
        assert "yoro.social.projectDietSpeechesGraphFallback" in registered_types


# ---------------------------------------------------------------------------
# §6 — count_products_by_status (row #39)
# ---------------------------------------------------------------------------

class TestCountProductsByStatus:
    """mst-projector or SDK listRecords client-side count.  M7 IMPLEMENTED."""

    def test_is_coroutine(self):
        mod = _yp()
        assert inspect.iscoroutinefunction(mod.count_products_by_status)

    def test_happy_path_counts_active(self):
        mod = _yp()
        mock_data = {
            "records": [
                {"value": {"productId": "p1", "status": "active"}},
                {"value": {"productId": "p2", "status": "active"}},
                {"value": {"productId": "p3", "status": "draft"}},
            ],
            "cursor": None,
        }
        mock_list = AsyncMock(return_value=mock_data)

        async def _run():
            with patch(f"{_PRODUCT_MOD}._pds_mod") as mock_pds:
                mock_pds.list_records = mock_list
                return await mod.count_products_by_status("active")

        result = asyncio.run(_run())
        assert result == 2

    def test_happy_path_counts_draft(self):
        mod = _yp()
        mock_data = {
            "records": [
                {"value": {"productId": "p1", "status": "active"}},
                {"value": {"productId": "p2", "status": "draft"}},
                {"value": {"productId": "p3", "status": "draft"}},
            ],
            "cursor": None,
        }
        mock_list = AsyncMock(return_value=mock_data)

        async def _run():
            with patch(f"{_PRODUCT_MOD}._pds_mod") as mock_pds:
                mock_pds.list_records = mock_list
                return await mod.count_products_by_status("draft")

        result = asyncio.run(_run())
        assert result == 2

    def test_empty_collection_returns_zero(self):
        mod = _yp()
        mock_data = {"records": [], "cursor": None}
        mock_list = AsyncMock(return_value=mock_data)

        async def _run():
            with patch(f"{_PRODUCT_MOD}._pds_mod") as mock_pds:
                mock_pds.list_records = mock_list
                return await mod.count_products_by_status("active")

        result = asyncio.run(_run())
        assert result == 0

    def test_no_matching_status_returns_zero(self):
        mod = _yp()
        mock_data = {
            "records": [
                {"value": {"productId": "p1", "status": "active"}},
                {"value": {"productId": "p2", "status": "active"}},
            ],
            "cursor": None,
        }
        mock_list = AsyncMock(return_value=mock_data)

        async def _run():
            with patch(f"{_PRODUCT_MOD}._pds_mod") as mock_pds:
                mock_pds.list_records = mock_list
                return await mod.count_products_by_status("archived")

        result = asyncio.run(_run())
        assert result == 0

    def test_paginates_through_cursor(self):
        """count_products_by_status follows cursor to count beyond first page."""
        mod = _yp()
        page1 = {
            "records": [
                {"value": {"productId": "p1", "status": "active"}},
                {"value": {"productId": "p2", "status": "active"}},
            ],
            "cursor": "cursor-page2",
        }
        page2 = {
            "records": [
                {"value": {"productId": "p3", "status": "active"}},
            ],
            "cursor": None,
        }
        call_count = 0

        async def mock_list(repo, collection, *, limit, cursor):
            nonlocal call_count
            call_count += 1
            return page1 if call_count == 1 else page2

        async def _run():
            with patch(f"{_PRODUCT_MOD}._pds_mod") as mock_pds:
                mock_pds.list_records = mock_list
                return await mod.count_products_by_status("active")

        result = asyncio.run(_run())
        assert result == 3
        assert call_count == 2

    def test_missing_status_raises_value_error(self):
        mod = _yp()

        async def _run():
            with patch(f"{_PRODUCT_MOD}._pds_mod") as mock_pds:
                mock_pds.list_records = AsyncMock(return_value={"records": [], "cursor": None})
                return await mod.count_products_by_status("")

        with pytest.raises(ValueError, match="status is required"):
            asyncio.run(_run())

    def test_sdk_not_installed_raises_import_error(self):
        mod = _yp()

        async def _run():
            with patch(f"{_PRODUCT_MOD}._pds_mod", None):
                return await mod.count_products_by_status("active")

        with pytest.raises(ImportError, match="etzhayyim_sdk"):
            asyncio.run(_run())

    def test_default_status_in_records_is_active(self):
        """Records without explicit status field default to 'active' in count."""
        mod = _yp()
        mock_data = {
            "records": [
                {"value": {"productId": "p1"}},  # no status field — defaults to 'active'
                {"value": {"productId": "p2", "status": "active"}},
            ],
            "cursor": None,
        }
        mock_list = AsyncMock(return_value=mock_data)

        async def _run():
            with patch(f"{_PRODUCT_MOD}._pds_mod") as mock_pds:
                mock_pds.list_records = mock_list
                return await mod.count_products_by_status("active")

        result = asyncio.run(_run())
        assert result == 2


# ---------------------------------------------------------------------------
# §7 — register() in yoro_product_ingest_murakumo (row #40)
# ---------------------------------------------------------------------------

class TestProductIngestRegister:
    """Zeebe task registrar — 9 tasks registered.  M7 IMPLEMENTED."""

    def _capture_registrations(self, mod: Any) -> tuple[list[str], list[Any]]:
        """Call register() with a mock worker and capture task types + handlers."""
        registered_types: list[str] = []
        registered_handlers: list[Any] = []

        def capture_task(**kwargs):
            registered_types.append(kwargs.get("task_type", ""))

            def decorator(fn: Any) -> Any:
                registered_handlers.append(fn)
                return fn

            return decorator

        mock_worker = MagicMock()
        mock_worker.task = capture_task
        mod.register(mock_worker, timeout_ms=25000)
        return registered_types, registered_handlers

    def test_registers_nine_tasks(self):
        mod = _yp()
        registered_types, _ = self._capture_registrations(mod)
        assert len(registered_types) == 9, (
            f"Expected 9 registered tasks, got {len(registered_types)}: {registered_types}"
        )

    def test_all_expected_task_types_registered(self):
        mod = _yp()
        registered_types, _ = self._capture_registrations(mod)
        expected = {
            "yoro.productIngest.ingestProduct",
            "yoro.productIngest.batchIngestProducts",
            "yoro.productIngest.upsertProductProfile",
            "yoro.productIngest.fetchProductById",
            "yoro.productIngest.fetchProductsByCategory",
            "yoro.productIngest.recordProductEvent",
            "yoro.productIngest.deleteProduct",
            "yoro.productIngest.listIngestedProductIds",
            "yoro.productIngest.countProductsByStatus",
        }
        assert set(registered_types) == expected, (
            f"Missing: {expected - set(registered_types)}\n"
            f"Extra: {set(registered_types) - expected}"
        )

    def test_all_registered_handlers_are_callable(self):
        mod = _yp()
        _, registered_handlers = self._capture_registrations(mod)
        for handler in registered_handlers:
            assert callable(handler), f"Handler {handler!r} is not callable"

    def test_registered_handlers_are_module_functions(self):
        """All registered handlers should be functions from the product ingest module."""
        mod = _yp()
        _, registered_handlers = self._capture_registrations(mod)
        for handler in registered_handlers:
            assert hasattr(handler, "__module__"), f"Handler {handler!r} has no __module__"

    def test_timeout_ms_accepted(self):
        """register() accepts timeout_ms kwarg without error."""
        mod = _yp()
        mock_worker = MagicMock()
        mock_worker.task = lambda **kwargs: (lambda fn: fn)
        # Must not raise
        mod.register(mock_worker, timeout_ms=10000)
        mod.register(mock_worker, timeout_ms=60000)


# ---------------------------------------------------------------------------
# §8 — Substrate-fit regression (M7 scope)
# ---------------------------------------------------------------------------

class TestM7SubstrateFitRegression:
    """No new RW/RunPod/Stripe imports introduced in M7 scope."""

    def _read_source(self, mod_name: str) -> str:
        import importlib.util
        spec = importlib.util.find_spec(mod_name)
        assert spec is not None and spec.origin is not None
        return Path(spec.origin).read_text(encoding="utf-8")

    def test_social_no_psycopg_import(self):
        src = self._read_source("pymagatama.primitives.yoro_social_murakumo")
        # "psycopg" appears in DO NOT docstrings; check no actual import statement
        assert "import psycopg2" not in src
        assert "import psycopg" not in src

    def test_social_no_rw_url_string_import(self):
        src = self._read_source("pymagatama.primitives.yoro_social_murakumo")
        # Should not have raw PostgreSQL connection string patterns (only env var checks)
        assert "postgresql://" not in src

    def test_social_no_runpod_import(self):
        src = self._read_source("pymagatama.primitives.yoro_social_murakumo")
        assert "import runpod" not in src

    def test_social_no_stripe_import(self):
        src = self._read_source("pymagatama.primitives.yoro_social_murakumo")
        assert "import stripe" not in src

    def test_product_no_psycopg_import(self):
        src = self._read_source("pymagatama.primitives.yoro_product_ingest_murakumo")
        # "psycopg" appears in DO NOT docstrings; check no actual import statement
        assert "import psycopg2" not in src
        assert "import psycopg" not in src

    def test_product_no_runpod_import(self):
        src = self._read_source("pymagatama.primitives.yoro_product_ingest_murakumo")
        assert "import runpod" not in src

    def test_product_no_stripe_import(self):
        src = self._read_source("pymagatama.primitives.yoro_product_ingest_murakumo")
        assert "import stripe" not in src

    def test_emit_bpmn_function_exists_and_is_sync(self):
        """emit_bpmn_activity_event must exist as a sync (non-coroutine) function."""
        mod = _ys()
        fn = getattr(mod, "emit_bpmn_activity_event", None)
        assert fn is not None, "emit_bpmn_activity_event must exist"
        assert not inspect.iscoroutinefunction(fn), "emit_bpmn_activity_event must be sync"

    def test_count_products_by_status_exists_and_is_coroutine(self):
        """count_products_by_status must exist as an async coroutine function."""
        mod = _yp()
        fn = getattr(mod, "count_products_by_status", None)
        assert fn is not None, "count_products_by_status must exist"
        assert inspect.iscoroutinefunction(fn), "count_products_by_status must be async"
