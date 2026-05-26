"""Smoke tests for lg-lawfirm-intake nodes (no LLM key, no network)."""

from __future__ import annotations

import asyncio
import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"


# ---------------------------------------------------------------------------
# triage_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_triage_node_fallback_no_key(monkeypatch):
    monkeypatch.setenv("etzhayyim_LLM_API_KEY", "")
    from lg_lawfirm_intake.nodes import triage_node  # type: ignore[import-untyped]
    state = {"summary_plain": "मेरा चेक बाउंस हो गया", "lang": "hi", "domain": "ni138"}
    result = await triage_node(state)
    assert result.get("triage_result") is not None
    tr = result["triage_result"]
    assert tr["domain"] == "ni138"
    assert tr["urgency"] == "routine"
    assert isinstance(tr["specializations"], list)


@pytest.mark.asyncio
async def test_triage_node_unknown_domain(monkeypatch):
    monkeypatch.setenv("etzhayyim_LLM_API_KEY", "")
    from lg_lawfirm_intake.nodes import triage_node  # type: ignore[import-untyped]
    state = {"summary_plain": "some complaint", "lang": "en", "domain": ""}
    result = await triage_node(state)
    tr = result["triage_result"]
    assert tr["domain"] == "other"


# ---------------------------------------------------------------------------
# summarize_node
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_summarize_node_encrypts():
    from lg_lawfirm_intake.nodes import summarize_node  # type: ignore[import-untyped]
    state = {
        "summary_plain": "Cheque bounced",
        "triage_result": {"summary_en": "Cheque bounce NI138"},
    }
    result = await summarize_node(state)
    cipher = result.get("summary_cipher", "")
    assert cipher.startswith("signal:v1:")
    import base64
    payload = cipher[len("signal:v1:"):]
    decoded = base64.b64decode(payload).decode("utf-8")
    assert "Cheque bounce" in decoded


@pytest.mark.asyncio
async def test_summarize_node_empty_summary():
    from lg_lawfirm_intake.nodes import summarize_node  # type: ignore[import-untyped]
    state = {"summary_plain": ""}
    result = await summarize_node(state)
    assert result == {}


# ---------------------------------------------------------------------------
# search_node (network mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_node_returns_empty_on_failure(monkeypatch):
    import urllib.error

    def _fail(*_a, **_kw):
        raise urllib.error.URLError("mock failure")

    monkeypatch.setattr("lg_lawfirm_intake.nodes._http_get", _fail)  # type: ignore[import-untyped]
    from lg_lawfirm_intake.nodes import search_node  # type: ignore[import-untyped]
    state = {"jurisdiction": "IND", "triage_result": {"specializations": ["criminal"]}}
    result = await search_node(state)
    assert result["lawyers"] == []


@pytest.mark.asyncio
async def test_search_node_returns_lawyers(monkeypatch):
    fake_lawyers = [{"did": "did:web:lawyer1.etzhayyim.com", "fullName": "Test Lawyer"}]

    def _mock_get(url, params=None):
        return {"lawyers": fake_lawyers, "total": 1, "offset": 0, "limit": 10}

    monkeypatch.setattr("lg_lawfirm_intake.nodes._http_get", _mock_get)  # type: ignore[import-untyped]
    from lg_lawfirm_intake.nodes import search_node  # type: ignore[import-untyped]
    state = {"jurisdiction": "IND", "triage_result": {"specializations": ["labor"]}}
    result = await search_node(state)
    assert len(result["lawyers"]) == 1
    assert result["lawyers"][0]["did"] == "did:web:lawyer1.etzhayyim.com"


# ---------------------------------------------------------------------------
# match_node (network mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_match_node_skips_when_no_case_did():
    from lg_lawfirm_intake.nodes import match_node  # type: ignore[import-untyped]
    state = {
        "lawyers": [{"did": "did:web:x.etzhayyim.com"}],
        "case_did": "",
    }
    result = await match_node(state)
    assert result["grants"] == []


@pytest.mark.asyncio
async def test_match_node_skips_when_no_lawyers():
    from lg_lawfirm_intake.nodes import match_node  # type: ignore[import-untyped]
    state = {"lawyers": [], "case_did": "did:web:lawfirm.etzhayyim.com:case:x"}
    result = await match_node(state)
    assert result["grants"] == []


@pytest.mark.asyncio
async def test_match_node_sends_invites(monkeypatch):
    def _mock_post(url, body, *, headers=None, timeout=15):
        return {
            "grantDid": f"did:web:lawfirm.etzhayyim.com:grant:{body['granteeDid']}",
            "grantUri": f"at://lawfirm.etzhayyim.com/grant/{body['granteeDid']}",
            "conflictCheckPassed": True,
        }

    monkeypatch.setattr("lg_lawfirm_intake.nodes._http_post", _mock_post)  # type: ignore[import-untyped]
    from lg_lawfirm_intake.nodes import match_node  # type: ignore[import-untyped]
    state = {
        "lawyers": [
            {"did": "did:web:l1.etzhayyim.com", "fullName": "Lawyer One"},
            {"did": "did:web:l2.etzhayyim.com", "fullName": "Lawyer Two"},
        ],
        "case_did": "did:web:lawfirm.etzhayyim.com:case:abc",
    }
    result = await match_node(state)
    assert len(result["grants"]) == 2
    assert result["grants"][0]["conflictCheckPassed"] is True
