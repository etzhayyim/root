"""Unit tests for the projector command (pure — no real HTTP)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main
from etzhayyim.projector import _mcp_call, _agent_token, _mcp_headers


# ── _agent_token ───────────────────────────────────────────────────────────────

def test_agent_token_from_env(monkeypatch):
    monkeypatch.setenv("etzhayyim_AGENT_TOKEN", "tok-abc")
    assert _agent_token() == "tok-abc"


def test_agent_token_missing(monkeypatch):
    monkeypatch.delenv("etzhayyim_AGENT_TOKEN", raising=False)
    assert _agent_token() is None


# ── _mcp_headers ───────────────────────────────────────────────────────────────

def test_mcp_headers_with_token(monkeypatch):
    monkeypatch.setenv("etzhayyim_AGENT_TOKEN", "tok-xyz")
    h = _mcp_headers()
    assert h["Authorization"] == "Bearer tok-xyz"
    assert h["Content-Type"] == "application/json"


def test_mcp_headers_without_token(monkeypatch):
    monkeypatch.delenv("etzhayyim_AGENT_TOKEN", raising=False)
    h = _mcp_headers()
    assert "Authorization" not in h
    assert h["Content-Type"] == "application/json"


# ── _mcp_call ──────────────────────────────────────────────────────────────────

def _mock_response(payload: dict, status: int = 200):
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = payload
    mock.raise_for_status = MagicMock()
    return mock


def _mcp_envelope(tool_result: dict) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"content": [{"type": "text", "text": json.dumps(tool_result)}]},
    }


def test_mcp_call_unwraps_content_text():
    expected = {"projectId": "proj-123", "ok": True}
    with patch("etzhayyim.projector.httpx.post", return_value=_mock_response(_mcp_envelope(expected))):
        result = _mcp_call("projector.create_project", {"name": "Test"})
    assert result == expected


def test_mcp_call_raises_on_rpc_error():
    error_resp = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {"code": -32600, "message": "Invalid request"},
    }
    with patch("etzhayyim.projector.httpx.post", return_value=_mock_response(error_resp)):
        import click
        with pytest.raises(click.ClickException, match="Invalid request"):
            _mcp_call("projector.create_project", {"name": "Test"})


def test_mcp_call_sends_correct_payload():
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured["json"] = json
        captured["url"] = url
        return _mock_response(_mcp_envelope({"ok": True}))

    with patch("etzhayyim.projector.httpx.post", side_effect=fake_post):
        _mcp_call("projector.create_project", {"name": "Foo"})

    assert captured["json"]["method"] == "tools/call"
    assert captured["json"]["params"]["name"] == "projector.create_project"
    assert captured["json"]["params"]["arguments"] == {"name": "Foo"}
    assert captured["json"]["jsonrpc"] == "2.0"
    assert "/mcp" in captured["url"]


# ── CLI: projector create ──────────────────────────────────────────────────────

def test_cli_projector_create_minimal():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"projectId": "p1", "ok": True}) as mock_call:
        result = runner.invoke(main, ["projector", "create", "My Project"])
    assert result.exit_code == 0
    mock_call.assert_called_once_with("projector.create_project", {"name": "My Project"})


def test_cli_projector_create_with_options():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"projectId": "p2"}) as mock_call:
        result = runner.invoke(main, [
            "projector", "create", "My Project",
            "--org-id", "did:plc:abc123",
            "--description", "A test project",
            "--target-date", "2026-12-31",
        ])
    assert result.exit_code == 0
    args = mock_call.call_args[0][1]
    assert args["orgId"] == "did:plc:abc123"
    assert args["description"] == "A test project"
    assert args["targetDate"] == "2026-12-31"


# ── CLI: projector status / get ────────────────────────────────────────────────

def test_cli_projector_status():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"projectId": "p1", "status": "active"}) as mock_call:
        result = runner.invoke(main, ["projector", "status", "p1"])
    assert result.exit_code == 0
    mock_call.assert_called_once_with("projector.get_status", {"projectId": "p1", "summarize": True})


def test_cli_projector_get_is_alias_for_status():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"projectId": "p1"}) as mock_call:
        result = runner.invoke(main, ["projector", "get", "p1", "--no-summarize"])
    assert result.exit_code == 0
    mock_call.assert_called_once_with("projector.get_status", {"projectId": "p1", "summarize": False})


# ── CLI: projector update ──────────────────────────────────────────────────────

def test_cli_projector_update_progress():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"ok": True}) as mock_call:
        result = runner.invoke(main, ["projector", "update", "p1", "--progress", "500"])
    assert result.exit_code == 0
    args = mock_call.call_args[0][1]
    assert args["progressPermille"] == 500
    assert args["projectId"] == "p1"


def test_cli_projector_update_state():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"ok": True}) as mock_call:
        result = runner.invoke(main, ["projector", "update", "p1", "--state", "completed"])
    assert result.exit_code == 0
    args = mock_call.call_args[0][1]
    assert args["lifecycleState"] == "completed"


# ── CLI: projector list ────────────────────────────────────────────────────────

def test_cli_projector_list_default():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"projects": []}) as mock_call:
        result = runner.invoke(main, ["projector", "list"])
    assert result.exit_code == 0
    args = mock_call.call_args[0][1]
    assert args["limit"] == 20


def test_cli_projector_list_with_filters():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"projects": []}) as mock_call:
        result = runner.invoke(main, ["projector", "list", "--org-id", "did:plc:abc", "--state", "active", "--limit", "5"])
    assert result.exit_code == 0
    args = mock_call.call_args[0][1]
    assert args["orgId"] == "did:plc:abc"
    assert args["lifecycleState"] == "active"
    assert args["limit"] == 5


# ── CLI: projector blocker ─────────────────────────────────────────────────────

def test_cli_projector_blocker_add():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"blockerId": "b1"}) as mock_call:
        result = runner.invoke(main, [
            "projector", "blocker", "add", "p1", "CI pipeline broken",
            "--type", "technical",
            "--severity", "high",
            "--description", "Build fails on main",
        ])
    assert result.exit_code == 0
    args = mock_call.call_args[0][1]
    assert args["projectId"] == "p1"
    assert args["title"] == "CI pipeline broken"
    assert args["blockerType"] == "technical"
    assert args["severity"] == "high"
    assert args["description"] == "Build fails on main"


def test_cli_projector_blocker_add_minimal():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"blockerId": "b2"}) as mock_call:
        result = runner.invoke(main, ["projector", "blocker", "add", "p1", "Budget freeze"])
    assert result.exit_code == 0
    args = mock_call.call_args[0][1]
    assert args["blockerType"] == "technical"  # default
    assert args["severity"] == "medium"         # default
    assert "description" not in args


def test_cli_projector_blocker_resolve():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"ok": True}) as mock_call:
        result = runner.invoke(main, ["projector", "blocker", "resolve", "b1", "--resolution", "Fixed in PR #42"])
    assert result.exit_code == 0
    args = mock_call.call_args[0][1]
    assert args["blockerId"] == "b1"
    assert args["resolution"] == "Fixed in PR #42"


def test_cli_projector_blocker_resolve_minimal():
    runner = CliRunner()
    with patch("etzhayyim.projector._mcp_call", return_value={"ok": True}) as mock_call:
        result = runner.invoke(main, ["projector", "blocker", "resolve", "b99"])
    assert result.exit_code == 0
    args = mock_call.call_args[0][1]
    assert "resolution" not in args


# ── output is valid JSON ───────────────────────────────────────────────────────

def test_cli_output_is_valid_json():
    runner = CliRunner()
    payload = {"projectId": "p1", "name": "My Project", "ok": True}
    with patch("etzhayyim.projector._mcp_call", return_value=payload):
        result = runner.invoke(main, ["projector", "status", "p1"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed == payload
