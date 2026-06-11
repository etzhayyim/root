"""Unit tests for etzhayyim.auth — token resolution and header helpers.

All external I/O (subprocess, filesystem) is mocked.
No keychain, no ~/.etzhayyim/auth.json reads.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from etzhayyim.auth import (
    auth_headers,
    mint_scoped_jwt,
    scoped_auth_headers,
    resolve_active_did,
    resolve_org_hint,
    resolve_pds,
    resolve_token,
    _scoped_jwt_cache,
    _scoped_jwt_lock,
)


# ─── resolve_pds ─────────────────────────────────────────────────────────────

class TestResolvePds:
    def test_returns_default_when_no_env(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_PDS_URL", raising=False)
        assert resolve_pds() == "https://atproto.etzhayyim.com"

    def test_returns_env_when_set(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_PDS_URL", "https://pds.example.com")
        assert resolve_pds() == "https://pds.example.com"

    def test_strips_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_PDS_URL", "https://pds.example.com/")
        assert resolve_pds() == "https://pds.example.com"


# ─── resolve_token ───────────────────────────────────────────────────────────

class TestResolveToken:
    def test_env_wins_over_keychain(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_TOKEN", "env-token-abc")
        token = resolve_token()
        assert token == "env-token-abc"

    def test_returns_none_when_no_sources(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_TOKEN", raising=False)
        with (
            patch("etzhayyim.auth._read_keychain", return_value=None),
            patch("etzhayyim.auth._load_auth_file", return_value={}),
        ):
            token = resolve_token()
        assert token is None

    def test_keychain_used_when_no_env(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_TOKEN", raising=False)
        with (
            patch("etzhayyim.auth._read_keychain", return_value="keychain-token"),
            patch("etzhayyim.auth._load_auth_file", return_value={}),
        ):
            token = resolve_token()
        assert token == "keychain-token"

    def test_auth_file_api_key_used_when_no_env_or_keychain(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_TOKEN", raising=False)
        with (
            patch("etzhayyim.auth._read_keychain", return_value=None),
            patch("etzhayyim.auth._load_auth_file", return_value={"api_key": "file-api-key"}),
        ):
            token = resolve_token()
        assert token == "file-api-key"

    def test_auth_file_id_token_fallback(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_TOKEN", raising=False)
        with (
            patch("etzhayyim.auth._read_keychain", return_value=None),
            patch("etzhayyim.auth._load_auth_file", return_value={"id_token": "id-tok-xyz"}),
        ):
            token = resolve_token()
        assert token == "id-tok-xyz"

    def test_auth_file_access_token_fallback(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_TOKEN", raising=False)
        with (
            patch("etzhayyim.auth._read_keychain", return_value=None),
            patch("etzhayyim.auth._load_auth_file", return_value={"access_token": "acc-tok-789"}),
        ):
            token = resolve_token()
        assert token == "acc-tok-789"

    def test_api_key_wins_over_id_token(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_TOKEN", raising=False)
        with (
            patch("etzhayyim.auth._read_keychain", return_value=None),
            patch("etzhayyim.auth._load_auth_file", return_value={
                "api_key": "api-key-wins",
                "id_token": "id-tok-loses",
            }),
        ):
            token = resolve_token()
        assert token == "api-key-wins"


# ─── resolve_active_did ──────────────────────────────────────────────────────

class TestResolveActiveDid:
    def test_returns_none_when_no_auth_file(self):
        with patch("etzhayyim.auth._load_auth_file", return_value={}):
            did = resolve_active_did()
        assert did is None

    def test_returns_active_did_from_file(self):
        with patch("etzhayyim.auth._load_auth_file", return_value={"active_did": "did:plc:abc123"}):
            did = resolve_active_did()
        assert did == "did:plc:abc123"

    def test_falls_back_to_sub(self):
        with patch("etzhayyim.auth._load_auth_file", return_value={"sub": "did:plc:sub456"}):
            did = resolve_active_did()
        assert did == "did:plc:sub456"

    def test_active_did_wins_over_sub(self):
        with patch("etzhayyim.auth._load_auth_file", return_value={
            "active_did": "did:plc:active",
            "sub": "did:plc:sub",
        }):
            did = resolve_active_did()
        assert did == "did:plc:active"


# ─── auth_headers ─────────────────────────────────────────────────────────────

class TestAuthHeaders:
    def test_no_token_no_did_returns_empty(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_TOKEN", raising=False)
        monkeypatch.delenv("etzhayyim_ORG_ID", raising=False)
        with (
            patch("etzhayyim.auth._read_keychain", return_value=None),
            patch("etzhayyim.auth._load_auth_file", return_value={}),
        ):
            headers = auth_headers()
        assert headers == {}

    def test_token_sets_authorization_header(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_TOKEN", "tok-xyz")
        with patch("etzhayyim.auth._load_auth_file", return_value={}):
            headers = auth_headers()
        assert headers["Authorization"] == "Bearer tok-xyz"

    def test_did_sets_x_active_did_header(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_TOKEN", raising=False)
        monkeypatch.delenv("etzhayyim_ORG_ID", raising=False)
        with (
            patch("etzhayyim.auth._read_keychain", return_value=None),
            patch("etzhayyim.auth._load_auth_file", return_value={"active_did": "did:plc:abc"}),
        ):
            headers = auth_headers()
        assert headers["X-Active-DID"] == "did:plc:abc"

    def test_org_env_sets_x_etzhayyim_org_id_header(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_ORG_ID", "org-123")
        monkeypatch.delenv("etzhayyim_TOKEN", raising=False)
        with (
            patch("etzhayyim.auth._read_keychain", return_value=None),
            patch("etzhayyim.auth._load_auth_file", return_value={}),
        ):
            headers = auth_headers()
        assert headers["X-etzhayyim-Org-Id"] == "org-123"

    def test_all_headers_present_when_all_sources_set(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_TOKEN", "tok-full")
        monkeypatch.setenv("etzhayyim_ORG_ID", "org-full")
        with patch("etzhayyim.auth._load_auth_file", return_value={"active_did": "did:plc:full"}):
            headers = auth_headers()
        assert "Authorization" in headers
        assert "X-Active-DID" in headers
        assert "X-etzhayyim-Org-Id" in headers


# ─── mint_scoped_jwt ──────────────────────────────────────────────────────────

class TestMintScopedJwt:
    def _clear_cache(self):
        with _scoped_jwt_lock:
            _scoped_jwt_cache.clear()

    def test_returns_empty_for_empty_token(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_SCOPED_AUTH", raising=False)
        assert mint_scoped_jwt("", "com.atproto.server.describeServer") == ""

    def test_returns_empty_for_empty_nsid(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_SCOPED_AUTH", raising=False)
        assert mint_scoped_jwt("sometoken", "") == ""

    def test_bootstrap_guard_skips_service_auth_nsid(self, monkeypatch):
        monkeypatch.delenv("etzhayyim_SCOPED_AUTH", raising=False)
        result = mint_scoped_jwt("sometoken", "com.atproto.server.getServiceAuth")
        assert result == ""

    def test_disabled_by_env_off(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_SCOPED_AUTH", "off")
        result = mint_scoped_jwt("mytoken", "com.etzhayyim.apps.billing.listInvoices")
        assert result == ""

    def test_disabled_by_env_zero(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_SCOPED_AUTH", "0")
        result = mint_scoped_jwt("mytoken", "com.etzhayyim.apps.billing.listInvoices")
        assert result == ""

    def test_disabled_by_env_false(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_SCOPED_AUTH", "false")
        result = mint_scoped_jwt("mytoken", "com.etzhayyim.apps.billing.listInvoices")
        assert result == ""

    def test_network_failure_returns_empty(self, monkeypatch):
        self._clear_cache()
        monkeypatch.delenv("etzhayyim_SCOPED_AUTH", raising=False)
        monkeypatch.setenv("etzhayyim_PDS_URL", "https://atproto.etzhayyim.com")

        import httpx
        with patch("httpx.post", side_effect=httpx.ConnectError("refused")):
            result = mint_scoped_jwt("mytoken", "com.etzhayyim.apps.billing.listInvoices")
        assert result == ""

    def test_http_error_returns_empty(self, monkeypatch):
        self._clear_cache()
        monkeypatch.delenv("etzhayyim_SCOPED_AUTH", raising=False)
        monkeypatch.setenv("etzhayyim_PDS_URL", "https://atproto.etzhayyim.com")

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        with patch("httpx.post", return_value=mock_resp):
            result = mint_scoped_jwt("mytoken", "com.etzhayyim.apps.billing.listInvoices")
        assert result == ""

    def test_successful_mint_returns_token(self, monkeypatch):
        self._clear_cache()
        monkeypatch.delenv("etzhayyim_SCOPED_AUTH", raising=False)
        monkeypatch.setenv("etzhayyim_PDS_URL", "https://atproto.etzhayyim.com")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"token": "scoped-jwt-xyz"}
        with patch("httpx.post", return_value=mock_resp):
            result = mint_scoped_jwt("mytoken", "com.etzhayyim.apps.billing.listInvoices")
        assert result == "scoped-jwt-xyz"

    def test_cache_hit_skips_http(self, monkeypatch):
        self._clear_cache()
        monkeypatch.delenv("etzhayyim_SCOPED_AUTH", raising=False)
        monkeypatch.setenv("etzhayyim_PDS_URL", "https://atproto.etzhayyim.com")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"token": "scoped-jwt-cached"}

        with patch("httpx.post", return_value=mock_resp) as mock_post:
            r1 = mint_scoped_jwt("mytoken", "com.etzhayyim.apps.billing.listInvoices")
            r2 = mint_scoped_jwt("mytoken", "com.etzhayyim.apps.billing.listInvoices")
        assert r1 == r2 == "scoped-jwt-cached"
        assert mock_post.call_count == 1

    def test_empty_token_in_response_returns_empty(self, monkeypatch):
        self._clear_cache()
        monkeypatch.delenv("etzhayyim_SCOPED_AUTH", raising=False)
        monkeypatch.setenv("etzhayyim_PDS_URL", "https://atproto.etzhayyim.com")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"token": ""}
        with patch("httpx.post", return_value=mock_resp):
            result = mint_scoped_jwt("mytoken", "com.etzhayyim.apps.billing.listInvoices")
        assert result == ""


# ─── scoped_auth_headers ──────────────────────────────────────────────────────

class TestScopedAuthHeaders:
    def test_falls_back_to_base_token_when_mint_fails(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_TOKEN", "base-tok")
        monkeypatch.setenv("etzhayyim_SCOPED_AUTH", "off")
        with patch("etzhayyim.auth._load_auth_file", return_value={}):
            headers = scoped_auth_headers("com.etzhayyim.apps.billing.listInvoices")
        assert headers["Authorization"] == "Bearer base-tok"

    def test_upgrades_to_scoped_token_when_available(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_TOKEN", "base-tok")
        monkeypatch.delenv("etzhayyim_SCOPED_AUTH", raising=False)
        with (
            patch("etzhayyim.auth._load_auth_file", return_value={}),
            patch("etzhayyim.auth.mint_scoped_jwt", return_value="scoped-tok"),
        ):
            headers = scoped_auth_headers("com.etzhayyim.apps.billing.listInvoices")
        assert headers["Authorization"] == "Bearer scoped-tok"

    def test_preserves_did_and_org_headers(self, monkeypatch):
        monkeypatch.setenv("etzhayyim_TOKEN", "base-tok")
        monkeypatch.setenv("etzhayyim_ORG_ID", "org-x")
        monkeypatch.setenv("etzhayyim_SCOPED_AUTH", "off")
        with patch("etzhayyim.auth._load_auth_file", return_value={"active_did": "did:plc:abc"}):
            headers = scoped_auth_headers("com.etzhayyim.apps.billing.listInvoices")
        assert "X-Active-DID" in headers
        assert "X-etzhayyim-Org-Id" in headers
