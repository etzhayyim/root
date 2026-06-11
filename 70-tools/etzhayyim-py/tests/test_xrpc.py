"""Unit tests for etzhayyim.xrpc — NSID routing and _resolve_base logic.

Tests only the pure routing logic (_resolve_base).
No real HTTP calls are made.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from etzhayyim.xrpc import _KNOWN_APPS, _APP_HOST_TEMPLATE, _resolve_base
from etzhayyim.cli import main


# ─── _resolve_base ────────────────────────────────────────────────────────────

class TestResolveBase:
    def test_url_wins_over_app_and_nsid(self):
        base = _resolve_base("com.etzhayyim.apps.media_gamers.foo", app="a7m8oocs", url="https://custom.example.com")
        assert base == "https://custom.example.com"

    def test_url_strips_trailing_slash(self):
        base = _resolve_base("any.nsid", app=None, url="https://custom.example.com/")
        assert base == "https://custom.example.com"

    def test_app_nanoid_wins_over_nsid_inference(self):
        base = _resolve_base("com.etzhayyim.apps.unknown.foo", app="mynanoid", url=None)
        assert base == _APP_HOST_TEMPLATE.format(nanoid="mynanoid")

    def test_known_slug_inferred_from_nsid(self):
        base = _resolve_base("com.etzhayyim.apps.media_gamers.listGames", app=None, url=None)
        expected = _APP_HOST_TEMPLATE.format(nanoid=_KNOWN_APPS["media_gamers"])
        assert base == expected

    def test_known_slug_handotai_inferred(self):
        base = _resolve_base("com.etzhayyim.apps.handotai.createArticle", app=None, url=None)
        expected = _APP_HOST_TEMPLATE.format(nanoid=_KNOWN_APPS["handotai"])
        assert base == expected

    def test_unknown_slug_falls_back_to_pds(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_PDS_URL", raising=False)
        base = _resolve_base("com.etzhayyim.apps.unknown_slug.foo", app=None, url=None)
        assert base == "https://atproto.etzhayyim.com"

    def test_non_ai_etzhayyim_apps_nsid_falls_back_to_pds(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_PDS_URL", raising=False)
        base = _resolve_base("com.atproto.server.describeServer", app=None, url=None)
        assert base == "https://atproto.etzhayyim.com"

    def test_fallback_uses_etzhayyim_pds_url_env(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_PDS_URL", "https://custom-pds.example.com")
        base = _resolve_base("com.atproto.server.describeServer", app=None, url=None)
        assert base == "https://custom-pds.example.com"

    def test_short_nsid_three_parts_falls_back_to_pds(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_PDS_URL", raising=False)
        base = _resolve_base("com.etzhayyim.apps", app=None, url=None)
        assert base == "https://atproto.etzhayyim.com"

    def test_known_apps_dict_contains_expected_slugs(self):
        assert "media_gamers" in _KNOWN_APPS
        assert "handotai" in _KNOWN_APPS
        assert "gtin" in _KNOWN_APPS

    def test_app_host_template_uses_nanoid(self):
        result = _APP_HOST_TEMPLATE.format(nanoid="abc123")
        assert "abc123" in result
        assert result.startswith("https://")


# ─── xrpc uses scoped_auth_headers ───────────────────────────────────────────

class TestXrpcUsedScopedAuth:
    def test_xrpc_calls_scoped_auth_headers_with_nsid(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_PDS_URL", "https://atproto.etzhayyim.com")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"ok": true}'
        mock_resp.json.return_value = {"ok": True}

        captured_nsid = []

        def fake_scoped_auth_headers(nsid: str) -> dict:
            captured_nsid.append(nsid)
            return {"Authorization": "Bearer scoped-tok"}

        with (
            patch("etzhayyim.xrpc.scoped_auth_headers", side_effect=fake_scoped_auth_headers),
            patch("httpx.get", return_value=mock_resp),
        ):
            runner = CliRunner()
            result = runner.invoke(main, ["xrpc", "com.atproto.server.describeServer"])

        assert result.exit_code == 0
        assert captured_nsid == ["com.atproto.server.describeServer"]
