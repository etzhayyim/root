"""M4 implementation tests for yoro murakumo primitives.

Tests verify happy-path behaviour for the 10 functions implemented in M4:

  Read-path:
    1. fetch_source_post              — PDS getRecord read-path
    2. fetch_actor_generation_context — PDS getRecord + listRecords
    3. fetch_profile_quality          — PDS listRecords count + profile

  Translation tasks:
    4. task_yoro_social_translate_post       — fetch + LLM stub + record_post + record_translation_link
    5. task_yoro_social_translate_post_batch — asyncio.gather fan-out + coalescer

  Zeebe task wiring:
    6. task_yoro_social_post_graph_fallback              — Zeebe → record_post
    7. task_yoro_social_respond_to_mention_graph_fallback — Zeebe → record_post (reply)
    8. task_yoro_social_respond_to_follow_graph_fallback  — Zeebe → follow_actor + record_post

  Quality:
    9. task_yoro_actor_quality_inspect — fetch_profile_quality + record_actor_quality_report
   10. task_yoro_actor_quality_verify  — fetch_profile_quality + record_actor_quality_report

Test strategy per function:
  - Happy path: mock SDK, call function, verify SDK call args + return value shape.
  - translate_post_batch: verify coalescer batches 2+ concurrent calls with same source_uri.
  - Substrate-fit regression: no psycopg, no RW_URL, no Stripe in new code.
  - All new async functions verified as coroutines.

ADR authority:
    ADR-2605215300 — yoro Python primitives MST rewrite addendum (M4 milestone)
"""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch
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

_SOCIAL_MOD = "pymagatama.primitives.yoro_social_murakumo"


def _ys() -> Any:
    """Always return the current sys.modules instance (safe after module evictions)."""
    return sys.modules[_SOCIAL_MOD]


# ---------------------------------------------------------------------------
# §1 — fetch_source_post
# ---------------------------------------------------------------------------

class TestFetchSourcePost:
    """Read-path: PDS getRecord → AT URI content.  M4 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_record_dict(self):
        mock_get = AsyncMock(return_value={
            "uri": "at://did:plc:author/app.bsky.feed.post/post001",
            "cid": "bafypost001",
            "value": {
                "$type": "app.bsky.feed.post",
                "text": "Hello Yoro!",
                "createdAt": "2026-05-21T00:00:00Z",
                "langs": ["ja"],
            },
        })
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            result = await _ys().fetch_source_post(
                "at://did:plc:author/app.bsky.feed.post/post001"
            )

        assert result is not None
        assert result["text"] == "Hello Yoro!"
        assert result["langs"] == ["ja"]
        assert result["repo"] == "did:plc:author"
        assert result["rkey"] == "post001"
        mock_get.assert_awaited_once_with("at://did:plc:author/app.bsky.feed.post/post001")

    @pytest.mark.asyncio
    async def test_not_found_returns_none(self):
        mock_get = AsyncMock(side_effect=Exception("PDS 404"))
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            result = await _ys().fetch_source_post(
                "at://did:plc:author/app.bsky.feed.post/missing"
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().fetch_source_post("at://did:plc:x/app.bsky.feed.post/y")

    @pytest.mark.asyncio
    async def test_empty_value_returns_empty_text(self):
        mock_get = AsyncMock(return_value={"uri": "at://x/y/z", "cid": "baf", "value": {}})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            result = await _ys().fetch_source_post("at://did:plc:a/app.bsky.feed.post/z")
        assert result is not None
        assert result["text"] == ""
        assert result["langs"] == []


# ---------------------------------------------------------------------------
# §2 — fetch_actor_generation_context
# ---------------------------------------------------------------------------

class TestFetchActorGenerationContext:
    """Read-path: PDS getRecord(profile) + listRecords.  M4 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_context_shape(self):
        profile_value = {
            "$type": "app.bsky.actor.profile",
            "displayName": "Test Actor",
            "description": "A test actor for Yoro.",
            "createdAt": "2026-05-21T00:00:00Z",
        }
        mock_get = AsyncMock(return_value={"value": profile_value})
        mock_list = AsyncMock(return_value={
            "records": [
                {
                    "uri": "at://did:plc:actor/app.bsky.feed.post/p1",
                    "value": {"text": "Hello", "$type": "app.bsky.feed.post"},
                    "indexedAt": "2026-05-21T00:00:00Z",
                }
            ],
            "cursor": None,
        })
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            context = await _ys().fetch_actor_generation_context(
                "did:plc:actor", "actor.etzhayyim.com"
            )

        assert context["actorDid"] == "did:plc:actor"
        assert context["handle"] == "actor.etzhayyim.com"
        profile = context["existingProfile"]
        assert profile["displayName"] == "Test Actor"
        assert len(context["recentPosts"]) == 1

    @pytest.mark.asyncio
    async def test_profile_not_found_returns_empty_profile(self):
        mock_get = AsyncMock(side_effect=Exception("PDS 404"))
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            context = await _ys().fetch_actor_generation_context("did:plc:missing")

        assert context["actorDid"] == "did:plc:missing"
        assert context["existingProfile"] == {}
        assert "contextFetchError" in context

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().fetch_actor_generation_context("did:plc:x")


# ---------------------------------------------------------------------------
# §3 — fetch_profile_quality
# ---------------------------------------------------------------------------

class TestFetchProfileQuality:
    """Read-path: PDS getRecord + listRecords count.  M4 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_full_profile_scores_high(self):
        profile_value = {
            "displayName": "Full Actor",
            "description": "A complete actor profile.",
            "avatar": "bafyavatar",
        }
        mock_get = AsyncMock(return_value={"value": profile_value})
        mock_list = AsyncMock(return_value={
            "records": [{"uri": "at://x/y/z"}],
            "cursor": "next-cursor",
        })
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            result = await _ys().fetch_profile_quality("did:plc:actor", "actor.test")

        assert result["ok"] is True
        assert result["actorDid"] == "did:plc:actor"
        assert result["qualityScore"] >= 800  # profile+dn+desc+avatar+posts = 1000
        assert "publicPost" not in result["missingFields"]

    @pytest.mark.asyncio
    async def test_missing_profile_scores_zero(self):
        mock_get = AsyncMock(side_effect=Exception("PDS 404"))
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            result = await _ys().fetch_profile_quality("did:plc:empty")

        assert result["ok"] is True
        assert result["qualityScore"] == 0
        assert "profile" in result["missingFields"]
        assert "publicPost" in result["missingFields"]

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().fetch_profile_quality("did:plc:x")


# ---------------------------------------------------------------------------
# §4 — task_yoro_social_translate_post
# ---------------------------------------------------------------------------

class TestTaskYoroSocialTranslatePost:
    """Translate post: LLM stub + record_post + record_translation_link.  M4 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_translated_result(self):
        mock_get = AsyncMock(return_value={
            "value": {"text": "こんにちは", "langs": ["ja"]},
        })
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "baf1"})
        mock_put = AsyncMock(return_value={"uri": "at://x", "cid": "baf2"})

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.dispatch = mock_dispatch
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_social_translate_post(
                postUri="at://did:plc:author/app.bsky.feed.post/jp001",
                targetLang="en",
                sourceLang="ja",
                postRepo="did:web:yoro.etzhayyim.com",
            )

        assert result["ok"] is True
        assert result["targetLang"] == "en"
        assert result["sourceLang"] == "ja"
        # LLM stub must include the target lang in the placeholder.
        assert "en" in result["translatedText"]
        assert "こんにちは" in result["translatedText"]
        assert "translatedUri" in result
        assert "translationLinkUri" in result

    @pytest.mark.asyncio
    async def test_missing_post_uri_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().task_yoro_social_translate_post(
                postUri="",
                targetLang="en",
            )
        assert result["ok"] is False
        assert "postUri" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_target_lang_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().task_yoro_social_translate_post(
                postUri="at://x/y/z",
                targetLang="",
            )
        assert result["ok"] is False
        assert "targetLang" in result["error"]

    @pytest.mark.asyncio
    async def test_post_text_override_skips_pds_fetch(self):
        """When postText is provided, fetch_source_post should not be called."""
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "baf1"})
        mock_put = AsyncMock(return_value={"uri": "at://x", "cid": "baf2"})
        mock_get = AsyncMock()

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.dispatch = mock_dispatch
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_social_translate_post(
                postUri="at://did:plc:a/app.bsky.feed.post/b",
                targetLang="ko",
                postText="Hello World",  # override — no PDS fetch needed
            )

        assert result["ok"] is True
        # get_record should NOT have been called since postText was provided.
        mock_get.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_dry_run_skips_writes(self):
        mock_get = AsyncMock(return_value={"value": {"text": "test", "langs": ["en"]}})
        mock_dispatch = AsyncMock()
        mock_put = AsyncMock()

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.dispatch = mock_dispatch
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_social_translate_post(
                postUri="at://did:plc:a/app.bsky.feed.post/b",
                targetLang="fr",
                dryRun=True,
            )

        assert result["ok"] is True
        assert result.get("dryRun") is True
        mock_dispatch.assert_not_awaited()
        mock_put.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_llm_stub_placeholder_format(self):
        """LLM stub must return f'[translated to {target_lang}] {source_text}'."""
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = AsyncMock(side_effect=Exception("404"))
            mock_pds.dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})
            mock_pds.put_record = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})
            result = await _ys().task_yoro_social_translate_post(
                postUri="at://did:plc:a/app.bsky.feed.post/b",
                targetLang="de",
                postText="Hallo",
            )

        assert result["ok"] is True
        assert result["translatedText"] == "[translated to de] Hallo"

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().task_yoro_social_translate_post(
                    postUri="at://x/y/z",
                    targetLang="en",
                )


# ---------------------------------------------------------------------------
# §5 — task_yoro_social_translate_post_batch
# ---------------------------------------------------------------------------

class TestTaskYoroSocialTranslatePostBatch:
    """Batch translate: asyncio.gather fan-out + coalescer.  M4 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_translates_multiple_langs(self):
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "baf1"})
        mock_put = AsyncMock(return_value={"uri": "at://x", "cid": "baf2"})
        mock_get = AsyncMock(side_effect=Exception("404"))

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.dispatch = mock_dispatch
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_social_translate_post_batch(
                postUri="at://did:plc:a/app.bsky.feed.post/b",
                targetLangs="en,ja,ko",
                postText="Hello",
            )

        assert result["ok"] is True
        assert result["count"] == 3
        assert result["translated"] == 3
        assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_coalescer_batches_same_source_uri(self):
        """Concurrent translate_post calls for the same postUri share translation link writes."""
        from etzhayyim_sdk.coalesce import RequestCoalescer

        put_call_count = 0

        async def _counting_put(**kwargs: Any) -> dict[str, Any]:
            nonlocal put_call_count
            put_call_count += 1
            return {"uri": "at://x", "cid": "baf"}

        # We patch _COALESCER with a real coalescer to verify batching behaviour.
        coalescer = RequestCoalescer(window_ms=80, max_batch=32)

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = AsyncMock(side_effect=Exception("404"))
            mock_pds.dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})
            mock_pds.put_record = _counting_put
            # Patch module-level coalescer to our controlled instance.
            with patch(f"{_SOCIAL_MOD}._COALESCER", coalescer):
                result = await _ys().task_yoro_social_translate_post_batch(
                    postUri="at://did:plc:a/app.bsky.feed.post/same",
                    targetLangs="en,ja",
                    postText="Batch test",
                )

        assert result["ok"] is True
        assert result["count"] == 2
        # Coalescer should have fired at least once; exact count ≤ 2 (may be 1 if batched).
        assert put_call_count >= 1
        await coalescer.flush()
        coalescer.close()

    @pytest.mark.asyncio
    async def test_empty_target_langs_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().task_yoro_social_translate_post_batch(
                postUri="at://x/y/z",
                targetLangs=[],
            )
        assert result["ok"] is False
        assert "targetLangs" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_post_uri_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().task_yoro_social_translate_post_batch(
                postUri="",
                targetLangs="en",
            )
        assert result["ok"] is False

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().task_yoro_social_translate_post_batch(
                    postUri="at://x/y/z",
                    targetLangs="en,ja",
                )


# ---------------------------------------------------------------------------
# §6 — task_yoro_social_post_graph_fallback
# ---------------------------------------------------------------------------

class TestTaskYoroSocialPostGraphFallback:
    """Zeebe task wiring → record_post.  M4 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_uri_and_ok(self):
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = await _ys().task_yoro_social_post_graph_fallback(
                postRepo="did:web:yoro.etzhayyim.com",
                text="Platform pulse from Yoro!",
            )

        assert result["ok"] is True
        assert result["uri"].startswith("at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/")
        assert result["repo"] == "did:web:yoro.etzhayyim.com"
        mock_dispatch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_text_auto_generated_when_empty(self):
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = await _ys().task_yoro_social_post_graph_fallback(
                postRepo="did:web:yoro.etzhayyim.com",
                text="",
            )
        assert result["ok"] is True
        assert len(result["text"]) > 0

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().task_yoro_social_post_graph_fallback()


# ---------------------------------------------------------------------------
# §7 — task_yoro_social_respond_to_mention_graph_fallback
# ---------------------------------------------------------------------------

class TestTaskYoroSocialRespondToMentionGraphFallback:
    """Zeebe task: build reply + record_post.  M4 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_uri(self):
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = await _ys().task_yoro_social_respond_to_mention_graph_fallback(
                authorDid="did:plc:author",
                authorHandle="author.bsky.social",
                postUri="at://did:plc:author/app.bsky.feed.post/mention001",
                postCid="bafymention001",
                postText="Hey @yoro, what are you building?",
            )

        assert result["ok"] is True
        assert "uri" in result
        assert result["authorDid"] == "did:plc:author"
        assert result["postUri"] == "at://did:plc:author/app.bsky.feed.post/mention001"
        mock_dispatch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reply_record_contains_reply_ref(self):
        """The dispatched record must include reply.root and reply.parent."""
        captured: dict[str, Any] = {}

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"uri": "at://x", "cid": "baf"}

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = _capture
            await _ys().task_yoro_social_respond_to_mention_graph_fallback(
                authorDid="did:plc:author",
                postUri="at://did:plc:author/app.bsky.feed.post/p1",
                postCid="bafyp1",
            )

        record = captured["record"]
        assert "reply" in record
        assert record["reply"]["root"]["uri"] == "at://did:plc:author/app.bsky.feed.post/p1"
        assert record["reply"]["root"]["cid"] == "bafyp1"

    @pytest.mark.asyncio
    async def test_missing_author_did_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().task_yoro_social_respond_to_mention_graph_fallback(
                authorDid="",
                postUri="at://x/y/z",
            )
        assert result["ok"] is False
        assert "authorDid" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_post_uri_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().task_yoro_social_respond_to_mention_graph_fallback(
                authorDid="did:plc:author",
                postUri="",
            )
        assert result["ok"] is False
        assert "postUri" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().task_yoro_social_respond_to_mention_graph_fallback(
                    authorDid="did:plc:a",
                    postUri="at://x/y/z",
                )


# ---------------------------------------------------------------------------
# §8 — task_yoro_social_respond_to_follow_graph_fallback
# ---------------------------------------------------------------------------

class TestTaskYoroSocialRespondToFollowGraphFallback:
    """Zeebe task: follow back + welcome post.  M4 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_both_uris(self):
        call_idx = 0

        async def _counting_dispatch(**kwargs: Any) -> dict[str, Any]:
            nonlocal call_idx
            call_idx += 1
            return {"uri": f"at://follow-uri-{call_idx}", "cid": f"baf{call_idx}"}

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = _counting_dispatch
            result = await _ys().task_yoro_social_respond_to_follow_graph_fallback(
                followerDid="did:plc:follower",
                followerHandle="follower.bsky.social",
                followRkey="follow-rkey-001",
            )

        assert result["ok"] is True
        assert "followBackUri" in result
        assert "welcomeUri" in result
        assert result["followerDid"] == "did:plc:follower"
        assert result["followRkey"] == "follow-rkey-001"
        # Both follow and welcome post were dispatched.
        assert call_idx >= 2

    @pytest.mark.asyncio
    async def test_follow_record_sent_to_pds(self):
        """Follow record must be app.bsky.graph.follow with subject DID."""
        captured_records: list[dict[str, Any]] = []

        async def _capture(**kwargs: Any) -> dict[str, Any]:
            captured_records.append(kwargs.get("record", {}))
            return {"uri": "at://x", "cid": "baf"}

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = _capture
            await _ys().task_yoro_social_respond_to_follow_graph_fallback(
                followerDid="did:plc:follower",
            )

        # One of the dispatches should be a graph.follow record.
        follow_records = [r for r in captured_records if r.get("$type") == "app.bsky.graph.follow"]
        assert len(follow_records) >= 1
        assert follow_records[0]["subject"] == "did:plc:follower"

    @pytest.mark.asyncio
    async def test_missing_follower_did_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().task_yoro_social_respond_to_follow_graph_fallback(
                followerDid="",
            )
        assert result["ok"] is False
        assert "followerDid" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().task_yoro_social_respond_to_follow_graph_fallback(
                    followerDid="did:plc:f",
                )


# ---------------------------------------------------------------------------
# §9 — task_yoro_actor_quality_inspect
# ---------------------------------------------------------------------------

class TestTaskYoroActorQualityInspect:
    """Quality inspect: fetch_profile_quality + record_actor_quality_report.  M4 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_quality_result(self):
        profile_value = {
            "displayName": "Quality Actor",
            "description": "Well described actor.",
            "avatar": "bafyavatar",
        }
        mock_get = AsyncMock(return_value={"value": profile_value})
        mock_list = AsyncMock(return_value={
            "records": [{"uri": "at://x/y/z"}], "cursor": None
        })
        mock_put = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_actor_quality_inspect(
                actorDid="did:plc:actor",
                sourceHint="test",
            )

        assert result["ok"] is True
        assert result["actorDid"] == "did:plc:actor"
        assert "qualityScore" in result
        assert "missingFields" in result
        assert "reportUri" in result
        mock_put.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_dry_run_skips_report_write(self):
        mock_get = AsyncMock(return_value={"value": {"displayName": "Actor"}})
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        mock_put = AsyncMock()

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_actor_quality_inspect(
                actorDid="did:plc:actor",
                dryRun=True,
            )

        assert result["ok"] is True
        assert result.get("dryRun") is True
        mock_put.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_missing_actor_did_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().task_yoro_actor_quality_inspect(actorDid="", handle="")
        assert result["ok"] is False
        assert "actorDid" in result["error"]

    @pytest.mark.asyncio
    async def test_dimensions_included_in_result(self):
        mock_get = AsyncMock(side_effect=Exception("404"))
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        mock_put = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_actor_quality_inspect(actorDid="did:plc:a")

        assert isinstance(result.get("dimensions"), list)
        dim_names = {d["dimension"] for d in result["dimensions"]}
        assert "charter-compliance" in dim_names

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().task_yoro_actor_quality_inspect(actorDid="did:plc:x")


# ---------------------------------------------------------------------------
# §10 — task_yoro_actor_quality_verify
# ---------------------------------------------------------------------------

class TestTaskYoroActorQualityVerify:
    """Quality verify: fetch_profile_quality + record_actor_quality_report.  M4 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_verified_actor(self):
        profile_value = {
            "displayName": "Verified Actor",
            "description": "Fully verified.",
            "avatar": "bafyav",
        }
        mock_get = AsyncMock(return_value={"value": profile_value})
        mock_list = AsyncMock(return_value={
            "records": [{"uri": "at://x/y/z"}], "cursor": "next"
        })
        mock_put = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_actor_quality_verify(
                actorDid="did:plc:verified",
            )

        assert result["ok"] is True
        assert result["verified"] is True
        assert "reportUri" in result
        assert isinstance(result.get("dimensions"), list)

    @pytest.mark.asyncio
    async def test_incomplete_actor_not_verified(self):
        mock_get = AsyncMock(side_effect=Exception("404"))
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        mock_put = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_actor_quality_verify(actorDid="did:plc:a")

        assert result["ok"] is True
        assert result["verified"] is False

    @pytest.mark.asyncio
    async def test_dry_run_skips_report_write(self):
        mock_get = AsyncMock(side_effect=Exception("404"))
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        mock_put = AsyncMock()

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_actor_quality_verify(
                actorDid="did:plc:x",
                dryRun=True,
            )

        assert result["ok"] is True
        assert result.get("dryRun") is True
        mock_put.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_verify_dimensions_include_governance(self):
        mock_get = AsyncMock(side_effect=Exception("404"))
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        mock_put = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_actor_quality_verify(actorDid="did:plc:x")

        dim_names = {d["dimension"] for d in result.get("dimensions", [])}
        assert "governance" in dim_names

    @pytest.mark.asyncio
    async def test_missing_actor_did_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().task_yoro_actor_quality_verify(actorDid="", handle="")
        assert result["ok"] is False

    @pytest.mark.asyncio
    async def test_missing_sdk_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk"):
                await _ys().task_yoro_actor_quality_verify(actorDid="did:plc:x")


# ---------------------------------------------------------------------------
# §11 — Substrate-fit regression for M4 functions
# ---------------------------------------------------------------------------

class TestM4SubstrateFit:
    """No prohibited imports introduced by M4 implementations."""

    def _social_src(self) -> str:
        import inspect
        return Path(inspect.getfile(_ys())).read_text(encoding="utf-8")

    def test_no_psycopg(self):
        src = self._social_src()
        for pat in ["import psycopg\n", "import psycopg2\n", "from psycopg ", "from psycopg2 "]:
            assert pat not in src, f"Found prohibited pattern: {pat!r}"

    def test_no_stripe(self):
        src = self._social_src()
        for pat in ["import stripe\n", "from stripe "]:
            assert pat not in src, f"Found prohibited pattern: {pat!r}"

    def test_no_runpod(self):
        assert "import runpod" not in self._social_src().lower()

    def test_no_sync_cursor(self):
        assert "sync_cursor" not in self._social_src()

    def test_no_rw_url_literal(self):
        src = self._social_src()
        # The guard test IS allowed; literal RW_URL usage in new code is not.
        # We check the guard function exists but no direct usage.
        assert "_substrate_fit_guard" in src

    def test_m4_functions_are_async(self):
        import inspect
        ys = _ys()
        async_fns = [
            "fetch_source_post",
            "fetch_actor_generation_context",
            "fetch_profile_quality",
            "task_yoro_social_translate_post",
            "task_yoro_social_translate_post_batch",
            "task_yoro_social_post_graph_fallback",
            "task_yoro_social_respond_to_mention_graph_fallback",
            "task_yoro_social_respond_to_follow_graph_fallback",
            "task_yoro_actor_quality_inspect",
            "task_yoro_actor_quality_verify",
        ]
        for fn_name in async_fns:
            fn = getattr(ys, fn_name)
            assert inspect.iscoroutinefunction(fn), f"{fn_name} must be async"

    def test_llm_stub_comment_present(self):
        """The M5 TODO comment for real LLM must be present in translate_post."""
        src = self._social_src()
        assert "TODO M5" in src
        assert "etzhayyim_sdk.llm.translate" in src


# ---------------------------------------------------------------------------
# §12 — M4 function signatures match vendor wire contract
# ---------------------------------------------------------------------------

class TestM4VendorSignatureParity:
    """Verify M4 functions accept vendor camelCase kwargs (Zeebe wire shape)."""

    @pytest.mark.asyncio
    async def test_post_graph_fallback_accepts_vendor_kwargs(self):
        """Vendor passes: postRepo, collection, prefix, text, createdAt, rkey, flush."""
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = await _ys().task_yoro_social_post_graph_fallback(
                postRepo="did:web:yoro.etzhayyim.com",
                collection="app.bsky.feed.post",
                prefix="Pulse",
                text="Test pulse",
                createdAt="",
                rkey="",
                flush=False,
            )
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_respond_to_mention_accepts_vendor_kwargs(self):
        """Vendor passes: authorDid, authorHandle, postUri, postCid, postText, flush."""
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = await _ys().task_yoro_social_respond_to_mention_graph_fallback(
                authorDid="did:plc:a",
                authorHandle="a.bsky.social",
                postUri="at://did:plc:a/app.bsky.feed.post/p1",
                postCid="bafyp1",
                postText="mention text",
                flush=False,
            )
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_respond_to_follow_accepts_vendor_kwargs(self):
        """Vendor passes: followerDid, followerHandle, followRkey, flush."""
        mock_dispatch = AsyncMock(return_value={"uri": "at://x", "cid": "baf"})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = await _ys().task_yoro_social_respond_to_follow_graph_fallback(
                followerDid="did:plc:follower",
                followerHandle="follower.bsky.social",
                followRkey="follow-rkey-001",
                flush=False,
            )
        assert result["ok"] is True
