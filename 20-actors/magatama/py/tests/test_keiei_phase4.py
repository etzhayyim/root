"""Phase 4 coverage for keiei C-suite AI residency (ADR 2605101200).

- Leader election: factory picks LocalLeader when not in k8s.
- ledger_append: raises NotLeaderError when leader.is_leader() is False.
- mailer.run_once: returns status="follower" when not leader; no XRPC call.
- LSP dispatcher: surfaces not-leader as a structured result with the
  leader's identity (no exception propagation).
- HTTP transport: /health surfaces leader identity; /jsonrpc enforces
  bearer auth when KEIEI_HTTP_BEARER is set; not-leader → HTTP 503 +
  X-Keiei-Leader response header.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from pymagatama.keiei import by_id, ROLES
from pymagatama.keiei import leader as leader_mod
from pymagatama.keiei import lsp_server as lsp_mod
from pymagatama.keiei import mailer as mailer_mod
from pymagatama.keiei.leader import LocalLeader, get_leader, reset_leader_for_tests, set_leader_for_tests


# ---------------------------------------------------------------------------
# Test fixtures: deterministic leader injection.
# ---------------------------------------------------------------------------

class _StubLeader:
    def __init__(self, leader: bool, identity: str = "stub-pod-0") -> None:
        self._is_leader = leader
        self._identity = identity

    def is_leader(self) -> bool:
        return self._is_leader

    def identity(self) -> str:
        return self._identity

    def stop(self) -> None:
        return None


@pytest.fixture(autouse=True)
def _isolate_leader():
    reset_leader_for_tests()
    yield
    reset_leader_for_tests()


# ---------------------------------------------------------------------------
# Leader factory.
# ---------------------------------------------------------------------------

class TestLeaderFactory:
    def test_local_leader_when_no_k8s_env(self, monkeypatch):
        monkeypatch.delenv("KUBERNETES_SERVICE_HOST", raising=False)
        monkeypatch.delenv("KEIEI_LEADER_ENABLED", raising=False)
        leader = leader_mod._build_leader()
        assert isinstance(leader, LocalLeader)
        assert leader.is_leader() is True

    def test_local_leader_when_enabled_flag_off(self, monkeypatch):
        monkeypatch.setenv("KUBERNETES_SERVICE_HOST", "10.0.0.1")
        monkeypatch.delenv("KEIEI_LEADER_ENABLED", raising=False)
        # KUBERNETES_SERVICE_HOST alone is not enough — must opt in via
        # KEIEI_LEADER_ENABLED=1 to avoid surprising prod tests.
        leader = leader_mod._build_leader()
        assert isinstance(leader, LocalLeader)

    def test_local_leader_identity_falls_back_to_hostname(self, monkeypatch):
        monkeypatch.setenv("HOSTNAME", "lab-mac")
        leader = LocalLeader()
        assert leader.identity() == "lab-mac"
        assert leader.is_leader() is True


# ---------------------------------------------------------------------------
# ledger_append leader gate.
# ---------------------------------------------------------------------------

class TestLedgerLeaderGate:
    def test_local_leader_writes_row(self, tmp_path, monkeypatch):
        set_leader_for_tests(_StubLeader(True))
        ledger = tmp_path / "ledger.md"
        monkeypatch.setattr(lsp_mod, "LEDGER_PATH", ledger)
        seq = lsp_mod.ledger_append(
            role="cto", decision_class="C",
            summary="phase4 smoke", decided_by="AI-CTO (test)",
        )
        assert seq == 1
        assert ledger.exists()
        assert "| 1 |" in ledger.read_text()

    def test_follower_raises_not_leader(self, tmp_path, monkeypatch):
        set_leader_for_tests(_StubLeader(False, identity="keiei-lsp-other"))
        ledger = tmp_path / "ledger.md"
        monkeypatch.setattr(lsp_mod, "LEDGER_PATH", ledger)
        with pytest.raises(lsp_mod.NotLeaderError) as ei:
            lsp_mod.ledger_append(
                role="cto", decision_class="C",
                summary="should not write", decided_by="AI-CTO (test)",
            )
        assert ei.value.identity == "keiei-lsp-other"
        # Ledger file MUST NOT be created by a follower.
        assert not ledger.exists()


# ---------------------------------------------------------------------------
# KeieiServer dispatcher surfaces not-leader.
# ---------------------------------------------------------------------------

class TestDispatcherNotLeaderSurfacing:
    @pytest.mark.asyncio
    async def test_decide_follower_returns_not_leader(self, tmp_path, monkeypatch):
        set_leader_for_tests(_StubLeader(False, identity="keiei-lsp-follower"))
        monkeypatch.setattr(lsp_mod, "LEDGER_PATH", tmp_path / "ledger.md")

        srv = lsp_mod.KeieiServer()
        result = await srv._decide(by_id("cto"), {
            "class": "C", "actionKind": "memo",
            "summary": "phase4 follower check", "artefact": "—",
        })
        assert result["status"] == "not-leader"
        assert result["leaderIdentity"] == "keiei-lsp-follower"
        assert "retryHint" in result

    @pytest.mark.asyncio
    async def test_escalate_follower_returns_not_leader(self, tmp_path, monkeypatch):
        set_leader_for_tests(_StubLeader(False, identity="keiei-lsp-x"))
        monkeypatch.setattr(lsp_mod, "LEDGER_PATH", tmp_path / "ledger.md")
        srv = lsp_mod.KeieiServer()
        result = srv._escalate(by_id("cto"), {
            "class": "A", "summary": "phase4 escalate follower",
        })
        assert result["status"] == "not-leader"
        assert result["leaderIdentity"] == "keiei-lsp-x"


# ---------------------------------------------------------------------------
# Mailer leader gate.
# ---------------------------------------------------------------------------

_PRIMARY_B_LEDGER = """# CXO-LEDGER

| seq | date | role | class | summary | decided_by | escalated_to | artefact |
|---|---|---|---|---|---|---|---|
| 1 | 2026-05-14 | cto | B | primary B should be disclosed | AI-CTO | — | — |
"""


def test_mailer_follower_does_not_send(tmp_path, monkeypatch):
    set_leader_for_tests(_StubLeader(False, identity="keiei-lsp-2"))
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_PRIMARY_B_LEDGER)
    state = tmp_path / "state.json"
    sent_calls = []

    def fake_send(**kwargs):
        sent_calls.append(kwargs)
        return {"status": "sent", "fromUpn": "x", "recipientCount": 1}

    monkeypatch.setattr(mailer_mod, "send_via_xrpc", fake_send)

    result = mailer_mod.run_once(
        ledger_path=ledger, state_path=state, token="tok",
    )
    assert result.status == "follower"
    assert result.sent is False
    assert sent_calls == []
    # State file MUST NOT be created (no watermark advance).
    assert not state.exists()


def test_mailer_leader_sends(tmp_path, monkeypatch):
    set_leader_for_tests(_StubLeader(True))
    ledger = tmp_path / "ledger.md"
    ledger.write_text(_PRIMARY_B_LEDGER)
    state = tmp_path / "state.json"
    sent = []

    monkeypatch.setattr(
        mailer_mod, "send_via_xrpc",
        lambda **kw: (sent.append(kw) or {"status": "sent", "fromUpn": "x", "recipientCount": 1}),
    )

    result = mailer_mod.run_once(
        ledger_path=ledger, state_path=state, token="tok",
        now_iso="2026-05-14T10:00:00Z",
    )
    assert result.status == "sent"
    assert result.new_watermark == 1
    assert len(sent) == 1


# ---------------------------------------------------------------------------
# HTTP transport.
# ---------------------------------------------------------------------------

@pytest.fixture()
def http_client(monkeypatch):
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from pymagatama.keiei import http_server as hs

    set_leader_for_tests(_StubLeader(True, identity="keiei-test-pod"))
    # Build a fresh app so the stub is captured into its dispatcher.
    app = hs.create_app()
    return TestClient(app)


class TestHttpTransport:
    def test_health_reports_leader(self, http_client):
        r = http_client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["service"] == "keiei-lsp"
        assert body["isLeader"] is True
        assert body["identity"] == "keiei-test-pod"

    def test_leader_endpoint(self, http_client):
        r = http_client.get("/leader")
        assert r.status_code == 200
        assert r.json()["isLeader"] is True

    def test_jsonrpc_list_roles(self, http_client):
        r = http_client.post("/jsonrpc", json={
            "jsonrpc": "2.0", "id": 1, "method": "cxo/listRoles",
        })
        assert r.status_code == 200
        body = r.json()
        assert body["jsonrpc"] == "2.0"
        assert body["id"] == 1
        assert isinstance(body["result"], list)
        # All declared ROLES come through.
        assert {row["id"] for row in body["result"]} == {r.id for r in ROLES}

    def test_jsonrpc_bearer_required_when_env_set(self, http_client, monkeypatch):
        monkeypatch.setenv("KEIEI_HTTP_BEARER", "secret-abc")
        r = http_client.post("/jsonrpc", json={
            "jsonrpc": "2.0", "id": 2, "method": "cxo/listRoles",
        })
        assert r.status_code == 401
        # Correct bearer passes.
        r2 = http_client.post(
            "/jsonrpc",
            json={"jsonrpc": "2.0", "id": 3, "method": "cxo/listRoles"},
            headers={"Authorization": "Bearer secret-abc"},
        )
        assert r2.status_code == 200

    def test_jsonrpc_follower_returns_503_with_leader_header(self, monkeypatch):
        fastapi = pytest.importorskip("fastapi")
        from fastapi.testclient import TestClient
        from pymagatama.keiei import http_server as hs

        set_leader_for_tests(_StubLeader(False, identity="keiei-lsp-leader-elsewhere"))
        app = hs.create_app()
        c = TestClient(app)
        r = c.post("/jsonrpc", json={
            "jsonrpc": "2.0", "id": 4, "method": "cxo/cto/decide",
            "params": {"class": "C", "summary": "follower smoke"},
        })
        assert r.status_code == 503
        assert r.headers.get("X-Keiei-Leader") == "keiei-lsp-leader-elsewhere"
        body = r.json()
        assert body["result"]["status"] == "not-leader"
        assert body["result"]["leaderIdentity"] == "keiei-lsp-leader-elsewhere"

    def test_jsonrpc_bad_method_returns_jsonrpc_error(self, http_client):
        r = http_client.post("/jsonrpc", json={
            "jsonrpc": "2.0", "id": 5, "method": "cxo/cto/nonexistent",
        })
        assert r.status_code == 200
        body = r.json()
        assert "error" in body
        assert body["error"]["code"] == -32601
