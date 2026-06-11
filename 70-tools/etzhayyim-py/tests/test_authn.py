"""Unit tests for authn commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main


def _write_auth(tmp_path: Path, data: dict) -> Path:
    auth_file = tmp_path / ".etzhayyim" / "auth.json"
    auth_file.parent.mkdir(parents=True, exist_ok=True)
    auth_file.write_text(json.dumps(data))
    return auth_file


# ── authn token ────────────────────────────────────────────────────────────────

def test_authn_token_not_signed_in(tmp_path):
    runner = CliRunner()
    auth_file = tmp_path / ".etzhayyim" / "auth.json"
    with patch("etzhayyim.authn._AUTH_FILE", auth_file):
        result = runner.invoke(main, ["authn", "token"])
    assert result.exit_code != 0


def test_authn_token_outputs_token(tmp_path):
    auth_file = _write_auth(tmp_path, {"accessJwt": "tok123"})
    runner = CliRunner()
    with patch("etzhayyim.authn._AUTH_FILE", auth_file):
        result = runner.invoke(main, ["authn", "token"])
    assert result.exit_code == 0
    assert "tok123" in result.output


def test_authn_token_access_token_key(tmp_path):
    auth_file = _write_auth(tmp_path, {"access_token": "bearer_xyz"})
    runner = CliRunner()
    with patch("etzhayyim.authn._AUTH_FILE", auth_file):
        result = runner.invoke(main, ["authn", "token"])
    assert result.exit_code == 0
    assert "bearer_xyz" in result.output


# ── authn whoami ───────────────────────────────────────────────────────────────

def test_authn_whoami_not_signed_in(tmp_path):
    runner = CliRunner()
    auth_file = tmp_path / ".etzhayyim" / "auth.json"
    with patch("etzhayyim.authn._AUTH_FILE", auth_file):
        result = runner.invoke(main, ["authn", "whoami"])
    assert result.exit_code != 0


def test_authn_whoami_shows_did(tmp_path):
    auth_file = _write_auth(tmp_path, {
        "did": "did:plc:abc123",
        "handle": "test.bsky.social",
        "accessJwt": "tok",
    })
    runner = CliRunner()
    with patch("etzhayyim.authn._AUTH_FILE", auth_file):
        result = runner.invoke(main, ["authn", "whoami"])
    assert result.exit_code == 0
    assert "did:plc:abc123" in result.output
    assert "test.bsky.social" in result.output


def test_authn_whoami_json(tmp_path):
    auth_file = _write_auth(tmp_path, {"did": "did:plc:abc", "accessJwt": "tok"})
    runner = CliRunner()
    with patch("etzhayyim.authn._AUTH_FILE", auth_file):
        result = runner.invoke(main, ["authn", "whoami", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["did"] == "did:plc:abc"


# ── authn signout ──────────────────────────────────────────────────────────────

def test_authn_signout_not_signed_in(tmp_path):
    runner = CliRunner()
    auth_file = tmp_path / ".etzhayyim" / "auth.json"
    with patch("etzhayyim.authn._AUTH_FILE", auth_file):
        result = runner.invoke(main, ["authn", "signout"])
    assert result.exit_code == 0
    assert "not signed in" in result.output


def test_authn_signout_removes_file(tmp_path):
    auth_file = _write_auth(tmp_path, {"accessJwt": "tok"})
    assert auth_file.exists()
    runner = CliRunner()
    with patch("etzhayyim.authn._AUTH_FILE", auth_file):
        result = runner.invoke(main, ["authn", "signout"])
    assert result.exit_code == 0
    assert "signed out" in result.output
    assert not auth_file.exists()


# ── authn signin (stub) ────────────────────────────────────────────────────────

def test_authn_signin_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(main, ["authn", "signin"])
    assert result.exit_code != 0


# ── CLI help ───────────────────────────────────────────────────────────────────

def test_authn_help():
    runner = CliRunner()
    result = runner.invoke(main, ["authn", "--help"])
    assert result.exit_code == 0
    assert "authn" in result.output.lower() or "auth" in result.output.lower()
