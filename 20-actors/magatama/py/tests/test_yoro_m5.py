"""M5 implementation tests for yoro murakumo primitives.

Tests verify happy-path and error-path behaviour for the 8 functions implemented in M5:

  Delete-path (symmetric with M3 create-path):
    1. delete_post              — PDS deleteRecord (feed.post MST tombstone)
    2. unfollow_actor           — PDS deleteRecord (graph.follow MST tombstone)
    3. unlike_post              — PDS deleteRecord (feed.like MST tombstone)

  Read-path completeness:
    4. fetch_followers          — PDS listRecords (graph.follow read)
    5. list_actor_records       — PDS listRecords (generic collection read)

  Quality system completeness (stuck stubs now implemented):
    6. task_yoro_actor_quality_enrich_profile — delegates to enrich_actor_quality_profile
    7. task_yoro_actor_quality_ensure_seed_post — idempotent seed-post guard
    8. task_yoro_social_platform_pulse_graph_fallback — pulse post + stub counts

Test strategy per function:
  - Happy path: mock SDK, call function, verify SDK call args + return value shape.
  - Error path: missing required args, invalid AT URI, SDK failure.
  - Substrate-fit regression: no psycopg2, no RW_URL, no Stripe, no runpod imports.

ADR authority:
    ADR-2605215300 — yoro Python primitives MST rewrite addendum (M5 milestone)
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
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

_SOCIAL_MOD = "pymagatama.primitives.yoro_social_murakumo"


def _ys() -> Any:
    """Always return the current sys.modules instance (safe after module evictions)."""
    return sys.modules[_SOCIAL_MOD]


# ---------------------------------------------------------------------------
# §1 — delete_post
# ---------------------------------------------------------------------------

class TestDeletePost:
    """Delete-path: PDS deleteRecord(feed.post) → MST tombstone.  M5 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_calls_delete_record(self):
        mock_delete = AsyncMock(return_value=None)
        uri = "at://did:plc:author/app.bsky.feed.post/abc123"
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.delete_record = mock_delete
            result = await _ys().delete_post(uri)

        mock_delete.assert_awaited_once_with(uri)
        assert result["ok"] is True
        assert result["deleted"] == uri

    @pytest.mark.asyncio
    async def test_missing_uri_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().delete_post("")
        assert result["ok"] is False
        assert "uri is required" in result["error"]

    @pytest.mark.asyncio
    async def test_non_at_uri_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().delete_post("https://example.com/post/123")
        assert result["ok"] is False
        assert "AT URI" in result["error"]

    @pytest.mark.asyncio
    async def test_sdk_not_installed_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError, match="etzhayyim_sdk not installed"):
                await _ys().delete_post("at://did:plc:x/app.bsky.feed.post/abc")

    def test_delete_post_is_coroutine(self):
        assert inspect.iscoroutinefunction(_ys().delete_post)


# ---------------------------------------------------------------------------
# §2 — unfollow_actor
# ---------------------------------------------------------------------------

class TestUnfollowActor:
    """Delete-path: PDS deleteRecord(graph.follow) → MST tombstone.  M5 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_calls_delete_record(self):
        mock_delete = AsyncMock(return_value=None)
        uri = "at://did:plc:author/app.bsky.graph.follow/followkey001"
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.delete_record = mock_delete
            result = await _ys().unfollow_actor(uri)

        mock_delete.assert_awaited_once_with(uri)
        assert result["ok"] is True
        assert result["deleted"] == uri

    @pytest.mark.asyncio
    async def test_missing_uri_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().unfollow_actor("")
        assert result["ok"] is False
        assert "uri is required" in result["error"]

    @pytest.mark.asyncio
    async def test_non_at_uri_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().unfollow_actor("did:plc:someone")
        assert result["ok"] is False
        assert "AT URI" in result["error"]

    @pytest.mark.asyncio
    async def test_sdk_not_installed_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError):
                await _ys().unfollow_actor("at://did:plc:x/app.bsky.graph.follow/k1")

    def test_unfollow_actor_is_coroutine(self):
        assert inspect.iscoroutinefunction(_ys().unfollow_actor)


# ---------------------------------------------------------------------------
# §3 — unlike_post
# ---------------------------------------------------------------------------

class TestUnlikePost:
    """Delete-path: PDS deleteRecord(feed.like) → MST tombstone.  M5 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_calls_delete_record(self):
        mock_delete = AsyncMock(return_value=None)
        uri = "at://did:plc:author/app.bsky.feed.like/likekey001"
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.delete_record = mock_delete
            result = await _ys().unlike_post(uri)

        mock_delete.assert_awaited_once_with(uri)
        assert result["ok"] is True
        assert result["deleted"] == uri

    @pytest.mark.asyncio
    async def test_missing_uri_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().unlike_post("")
        assert result["ok"] is False
        assert "uri is required" in result["error"]

    @pytest.mark.asyncio
    async def test_non_at_uri_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().unlike_post("feed.like/baduri")
        assert result["ok"] is False
        assert "AT URI" in result["error"]

    @pytest.mark.asyncio
    async def test_sdk_not_installed_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError):
                await _ys().unlike_post("at://did:plc:x/app.bsky.feed.like/k1")

    def test_unlike_post_is_coroutine(self):
        assert inspect.iscoroutinefunction(_ys().unlike_post)


# ---------------------------------------------------------------------------
# §4 — fetch_followers
# ---------------------------------------------------------------------------

class TestFetchFollowers:
    """Read-path: PDS listRecords(graph.follow) → follower list.  M5 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_follow_list(self):
        actor_did = "did:plc:actor001"
        mock_list = AsyncMock(return_value={
            "records": [
                {
                    "uri": f"at://{actor_did}/app.bsky.graph.follow/k1",
                    "cid": "bafyfollowcid001",
                    "value": {
                        "$type": "app.bsky.graph.follow",
                        "subject": "did:plc:target001",
                        "createdAt": "2026-05-21T00:00:00Z",
                    },
                },
                {
                    "uri": f"at://{actor_did}/app.bsky.graph.follow/k2",
                    "cid": "bafyfollowcid002",
                    "value": {
                        "$type": "app.bsky.graph.follow",
                        "subject": "did:plc:target002",
                        "createdAt": "2026-05-21T01:00:00Z",
                    },
                },
            ],
            "cursor": None,
        })
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.list_records = mock_list
            result = await _ys().fetch_followers(actor_did)

        mock_list.assert_awaited_once()
        call_args = mock_list.call_args
        assert call_args.args[0] == actor_did
        assert call_args.args[1] == "app.bsky.graph.follow"
        assert result["ok"] is True
        assert result["actorDid"] == actor_did
        assert result["count"] == 2
        assert result["follows"][0]["subject"] == "did:plc:target001"
        assert result["follows"][1]["subject"] == "did:plc:target002"
        assert result["cursor"] is None

    @pytest.mark.asyncio
    async def test_empty_follow_list_returns_ok(self):
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.list_records = mock_list
            result = await _ys().fetch_followers("did:plc:empty")

        assert result["ok"] is True
        assert result["count"] == 0
        assert result["follows"] == []

    @pytest.mark.asyncio
    async def test_missing_actor_did_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().fetch_followers("")
        assert result["ok"] is False
        assert "actor_did is required" in result["error"]

    @pytest.mark.asyncio
    async def test_sdk_failure_returns_error(self):
        mock_list = AsyncMock(side_effect=RuntimeError("PDS unavailable"))
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.list_records = mock_list
            result = await _ys().fetch_followers("did:plc:actor001")

        assert result["ok"] is False
        assert "PDS unavailable" in result["error"]
        assert result["follows"] == []

    @pytest.mark.asyncio
    async def test_cursor_pagination_passed_through(self):
        mock_list = AsyncMock(return_value={
            "records": [],
            "cursor": "next-page-cursor",
        })
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.list_records = mock_list
            result = await _ys().fetch_followers(
                "did:plc:actor001", limit=10, cursor="prev-cursor"
            )

        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs.get("cursor") == "prev-cursor"
        assert call_kwargs.get("limit") == 10

    @pytest.mark.asyncio
    async def test_sdk_not_installed_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError):
                await _ys().fetch_followers("did:plc:actor001")

    def test_fetch_followers_is_coroutine(self):
        assert inspect.iscoroutinefunction(_ys().fetch_followers)


# ---------------------------------------------------------------------------
# §5 — list_actor_records
# ---------------------------------------------------------------------------

class TestListActorRecords:
    """Read-path: PDS listRecords (generic collection).  M5 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_records(self):
        actor_did = "did:plc:actor001"
        collection = "app.bsky.feed.post"
        mock_list = AsyncMock(return_value={
            "records": [
                {
                    "uri": f"at://{actor_did}/{collection}/post001",
                    "cid": "bafypostcid001",
                    "value": {
                        "$type": collection,
                        "text": "Hello Yoro!",
                        "createdAt": "2026-05-21T00:00:00Z",
                    },
                },
            ],
            "cursor": "cursor-page-2",
        })
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.list_records = mock_list
            result = await _ys().list_actor_records(actor_did, collection)

        mock_list.assert_awaited_once()
        assert result["ok"] is True
        assert result["actorDid"] == actor_did
        assert result["collection"] == collection
        assert result["count"] == 1
        assert result["cursor"] == "cursor-page-2"

    @pytest.mark.asyncio
    async def test_missing_actor_did_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().list_actor_records("")
        assert result["ok"] is False
        assert "actor_did is required" in result["error"]

    @pytest.mark.asyncio
    async def test_sdk_failure_returns_error(self):
        mock_list = AsyncMock(side_effect=RuntimeError("network error"))
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.list_records = mock_list
            result = await _ys().list_actor_records("did:plc:a", "app.bsky.feed.post")
        assert result["ok"] is False
        assert "network error" in result["error"]
        assert result["records"] == []

    @pytest.mark.asyncio
    async def test_custom_collection_passed_to_sdk(self):
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        custom_col = "app.bsky.graph.follow"
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.list_records = mock_list
            result = await _ys().list_actor_records("did:plc:a", custom_col, limit=5)

        call_args = mock_list.call_args
        assert call_args.args[1] == custom_col
        assert call_args.kwargs.get("limit") == 5
        assert result["collection"] == custom_col

    @pytest.mark.asyncio
    async def test_sdk_not_installed_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError):
                await _ys().list_actor_records("did:plc:actor001")

    def test_list_actor_records_is_coroutine(self):
        assert inspect.iscoroutinefunction(_ys().list_actor_records)


# ---------------------------------------------------------------------------
# §6 — task_yoro_actor_quality_enrich_profile
# ---------------------------------------------------------------------------

class TestTaskActorQualityEnrichProfile:
    """Quality task: enrich profile → update_profile.  M5 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_enriches_profile(self):
        mock_put = AsyncMock(return_value="at://did:plc:actor/app.bsky.actor.profile/self")
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = mock_put
            result = await _ys().task_yoro_actor_quality_enrich_profile(
                actorDid="did:plc:actor001",
                handle="actor.bsky.social",
                sourceHint="yoro-graph",
            )

        assert result["ok"] is True
        assert result.get("profileChanged") is True
        assert "uri" in result

    @pytest.mark.asyncio
    async def test_dry_run_returns_without_write(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.put_record = AsyncMock()
            result = await _ys().task_yoro_actor_quality_enrich_profile(
                actorDid="did:plc:actor001",
                dryRun=True,
            )

        mock_pds.put_record.assert_not_awaited()
        assert result["ok"] is True
        assert result.get("dryRun") is True
        assert result.get("profileChanged") is False

    @pytest.mark.asyncio
    async def test_missing_actor_did_and_handle_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().task_yoro_actor_quality_enrich_profile()
        assert result["ok"] is False
        assert "actorDid or handle is required" in result["error"]

    @pytest.mark.asyncio
    async def test_sdk_not_installed_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError):
                await _ys().task_yoro_actor_quality_enrich_profile(actorDid="did:plc:x")

    def test_enrich_profile_is_coroutine(self):
        assert inspect.iscoroutinefunction(_ys().task_yoro_actor_quality_enrich_profile)


# ---------------------------------------------------------------------------
# §7 — task_yoro_actor_quality_ensure_seed_post
# ---------------------------------------------------------------------------

class TestTaskActorQualityEnsureSeedPost:
    """Quality task: ensure seed post — idempotent guard.  M5 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_no_existing_posts_creates_seed(self):
        mock_get = AsyncMock(return_value=None)  # no profile
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        mock_dispatch = AsyncMock(
            return_value="at://did:plc:actor001/app.bsky.feed.post/seedkey"
        )
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            mock_pds.dispatch = mock_dispatch
            result = await _ys().task_yoro_actor_quality_ensure_seed_post(
                actorDid="did:plc:actor001",
                handle="actor.bsky.social",
            )

        assert result["ok"] is True
        assert result.get("seedPosted") is True
        assert result.get("alreadyExists") is False
        assert "seedUri" in result
        assert "seedText" in result

    @pytest.mark.asyncio
    async def test_idempotent_actor_with_existing_posts(self):
        mock_get = AsyncMock(return_value={
            "value": {
                "$type": "app.bsky.actor.profile",
                "displayName": "Actor",
                "description": "desc",
                "createdAt": "2026-05-21T00:00:00Z",
            }
        })
        mock_list = AsyncMock(side_effect=[
            # first call: listRecords(profile) — used internally by fetch_profile_quality
            {"records": [{"uri": "at://did:plc:actor001/app.bsky.feed.post/p1", "cid": "c1", "value": {}}], "cursor": "more"},
        ])
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            mock_pds.dispatch = AsyncMock()
            result = await _ys().task_yoro_actor_quality_ensure_seed_post(
                actorDid="did:plc:actor001",
            )

        # dispatch should NOT be called since actor already has posts
        mock_pds.dispatch.assert_not_awaited()
        assert result["ok"] is True
        assert result.get("alreadyExists") is True
        assert result.get("seedPosted") is False

    @pytest.mark.asyncio
    async def test_dry_run_returns_without_write(self):
        mock_get = AsyncMock(return_value=None)
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            mock_pds.dispatch = AsyncMock()
            result = await _ys().task_yoro_actor_quality_ensure_seed_post(
                actorDid="did:plc:actor001",
                dryRun=True,
            )

        mock_pds.dispatch.assert_not_awaited()
        assert result["ok"] is True
        assert result.get("dryRun") is True
        assert result.get("seedPosted") is False

    @pytest.mark.asyncio
    async def test_custom_seed_text_used_when_provided(self):
        mock_get = AsyncMock(return_value=None)
        mock_list = AsyncMock(return_value={"records": [], "cursor": None})
        custom_text = "Custom seed post for testing."
        captured_text: list[str] = []

        async def _capture_dispatch(**kwargs: Any) -> str:
            captured_text.append(kwargs.get("record", {}).get("text", ""))
            return "at://did:plc:actor001/app.bsky.feed.post/seedkey"

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.get_record = mock_get
            mock_pds.list_records = mock_list
            mock_pds.dispatch = AsyncMock(side_effect=_capture_dispatch)
            result = await _ys().task_yoro_actor_quality_ensure_seed_post(
                actorDid="did:plc:actor001",
                seedPostText=custom_text,
            )

        assert result["ok"] is True
        assert result["seedText"] == custom_text

    @pytest.mark.asyncio
    async def test_missing_actor_returns_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod"):
            result = await _ys().task_yoro_actor_quality_ensure_seed_post()
        assert result["ok"] is False
        assert "actorDid or handle is required" in result["error"]

    @pytest.mark.asyncio
    async def test_sdk_not_installed_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError):
                await _ys().task_yoro_actor_quality_ensure_seed_post(actorDid="did:plc:x")

    def test_ensure_seed_post_is_coroutine(self):
        assert inspect.iscoroutinefunction(_ys().task_yoro_actor_quality_ensure_seed_post)


# ---------------------------------------------------------------------------
# §8 — task_yoro_social_platform_pulse_graph_fallback
# ---------------------------------------------------------------------------

class TestTaskPlatformPulseGraphFallback:
    """Zeebe task: platform pulse post → MST commit.  M5 IMPLEMENTED."""

    @pytest.mark.asyncio
    async def test_happy_path_posts_pulse_record(self):
        mock_dispatch = AsyncMock(
            return_value="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/pulsekey"
        )
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = await _ys().task_yoro_social_platform_pulse_graph_fallback(
                postRepo="did:web:yoro.etzhayyim.com",
            )

        assert result["ok"] is True
        assert "uri" in result
        assert "pulseAt" in result
        assert "postCount" in result
        assert "followerCount" in result
        assert "note" in result  # M6 TODO stub note

    @pytest.mark.asyncio
    async def test_default_repo_used_when_empty(self):
        mock_dispatch = AsyncMock(return_value="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/pk")
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = await _ys().task_yoro_social_platform_pulse_graph_fallback()

        assert result["ok"] is True
        assert result["repo"] == "did:web:yoro.etzhayyim.com"

    @pytest.mark.asyncio
    async def test_pulse_text_contains_timestamp_and_url(self):
        captured_records: list[dict] = []

        async def _capture(**kwargs: Any) -> str:
            captured_records.append(kwargs.get("record", {}))
            return "at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/pk"

        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = AsyncMock(side_effect=_capture)
            await _ys().task_yoro_social_platform_pulse_graph_fallback()

        assert captured_records, "dispatch should have been called"
        text = captured_records[0].get("text", "")
        assert "yoro.etzhayyim.com" in text
        assert "pulse" in text.lower() or "Yoro" in text

    @pytest.mark.asyncio
    async def test_flush_kwarg_is_ignored(self):
        """flush=True must not cause any error (MST no FLUSH)."""
        mock_dispatch = AsyncMock(return_value="at://did:web:yoro.etzhayyim.com/app.bsky.feed.post/pk")
        with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
            mock_pds.dispatch = mock_dispatch
            result = await _ys().task_yoro_social_platform_pulse_graph_fallback(flush=True)
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_sdk_not_installed_raises_import_error(self):
        with patch(f"{_SOCIAL_MOD}._pds_mod", None):
            with pytest.raises(ImportError):
                await _ys().task_yoro_social_platform_pulse_graph_fallback()

    def test_platform_pulse_is_coroutine(self):
        assert inspect.iscoroutinefunction(
            _ys().task_yoro_social_platform_pulse_graph_fallback
        )


# ---------------------------------------------------------------------------
# §9 — Substrate-fit regression (M5 additions)
# ---------------------------------------------------------------------------

class TestSubstrateFitRegressionM5:
    """Verify M5 code introduces no forbidden substrate imports."""

    def test_no_psycopg_import(self):
        """psycopg2/psycopg must not be imported (only mentioned in DO NOT docstrings)."""
        import pymagatama.primitives.yoro_social_murakumo as mod
        src_path = inspect.getfile(mod)
        src = Path(src_path).read_text(encoding="utf-8")
        # Check no actual import statements reference psycopg
        import_lines = [
            line.strip() for line in src.splitlines()
            if line.strip().startswith("import ") or line.strip().startswith("from ")
        ]
        for line in import_lines:
            assert "psycopg" not in line, f"Forbidden psycopg import: {line!r}"

    def test_no_rw_url_reference_in_source(self):
        """RW_URL must only appear in the substrate-fit guard (not in arbitrary code)."""
        import pymagatama.primitives.yoro_social_murakumo as mod
        src_path = inspect.getfile(mod)
        src = Path(src_path).read_text(encoding="utf-8")
        # RW_URL references are expected in guard + DO NOT docstrings — not in
        # raw SQL or connection-string literals.
        forbidden_patterns = ["RW_URL =", "os.environ['RW_URL']", 'os.environ["RW_URL"] =']
        for pattern in forbidden_patterns:
            assert pattern not in src, f"Forbidden RW_URL usage: {pattern!r}"

    def test_no_stripe_import(self):
        import pymagatama.primitives.yoro_social_murakumo as mod
        src = inspect.getsource(mod)
        assert "import stripe" not in src
        assert "from stripe" not in src

    def test_no_runpod_import(self):
        import pymagatama.primitives.yoro_social_murakumo as mod
        src = inspect.getsource(mod)
        assert "import runpod" not in src
        assert "from runpod" not in src

    def test_m5_functions_exist_on_module(self):
        mod = _ys()
        assert callable(mod.delete_post)
        assert callable(mod.unfollow_actor)
        assert callable(mod.unlike_post)
        assert callable(mod.fetch_followers)
        assert callable(mod.list_actor_records)
        assert callable(mod.task_yoro_actor_quality_enrich_profile)
        assert callable(mod.task_yoro_actor_quality_ensure_seed_post)
        assert callable(mod.task_yoro_social_platform_pulse_graph_fallback)

    def test_m5_functions_no_longer_raise_not_implemented(self):
        """Previously-stubbed tasks must not raise NotImplementedError on call."""
        mod = _ys()
        # Verify they are real coroutines, not stubs (stubs raise synchronously)
        for fn_name in (
            "task_yoro_actor_quality_enrich_profile",
            "task_yoro_actor_quality_ensure_seed_post",
            "task_yoro_social_platform_pulse_graph_fallback",
        ):
            fn = getattr(mod, fn_name)
            assert inspect.iscoroutinefunction(fn), f"{fn_name} must be a coroutine"
            # source must not contain 'raise NotImplementedError' in the function body
            src = inspect.getsource(fn)
            assert "raise NotImplementedError" not in src, (
                f"{fn_name} still has NotImplementedError stub body"
            )


# ---------------------------------------------------------------------------
# §10 — Symmetry tests (create/delete pairs)
# ---------------------------------------------------------------------------

class TestCreateDeleteSymmetry:
    """Verify create/delete pairs use matching collections (AT Protocol contract)."""

    def test_delete_post_documentation_references_feed_post(self):
        src = inspect.getsource(_ys().delete_post)
        assert "app.bsky.feed.post" in src

    def test_unfollow_actor_documentation_references_graph_follow(self):
        src = inspect.getsource(_ys().unfollow_actor)
        assert "app.bsky.graph.follow" in src

    def test_unlike_post_documentation_references_feed_like(self):
        src = inspect.getsource(_ys().unlike_post)
        assert "app.bsky.feed.like" in src

    @pytest.mark.asyncio
    async def test_delete_functions_all_use_delete_record(self):
        """All 3 delete ops must call pds.delete_record (not put_record or dispatch)."""
        for fn, uri in [
            (_ys().delete_post, "at://did:plc:x/app.bsky.feed.post/k"),
            (_ys().unfollow_actor, "at://did:plc:x/app.bsky.graph.follow/k"),
            (_ys().unlike_post, "at://did:plc:x/app.bsky.feed.like/k"),
        ]:
            mock_delete = AsyncMock(return_value=None)
            with patch(f"{_SOCIAL_MOD}._pds_mod") as mock_pds:
                mock_pds.delete_record = mock_delete
                mock_pds.put_record = AsyncMock()
                mock_pds.dispatch = AsyncMock()
                await fn(uri)

            mock_delete.assert_awaited_once()
            mock_pds.put_record.assert_not_awaited()
            mock_pds.dispatch.assert_not_awaited()
