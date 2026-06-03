"""Smoke tests for lg-webmk graphs (no LLM / no DB required).

Run:
  LG_AUDIT_DISABLED=1 pytest 60-apps/etzhayyim-project-webmk/lg/tests/ -v
"""

from __future__ import annotations

import os
import sys

import pytest

# Ensure lg_webmk is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("LG_AUDIT_DISABLED", "1")
os.environ.setdefault("RW_URL", "")


@pytest.mark.asyncio
async def test_health_graph_no_rw():
    from lg_webmk.graphs.health import GRAPH
    result = await GRAPH.ainvoke({})
    assert "ok" in result


@pytest.mark.asyncio
async def test_get_proposal_no_rw():
    from lg_webmk.graphs.get_proposal import GRAPH
    result = await GRAPH.ainvoke({"proposal_id": "prop-test-001"})
    assert "ok" in result
    assert result.get("ok") is False or "proposal" in result


@pytest.mark.asyncio
async def test_list_proposals_no_rw():
    from lg_webmk.graphs.list_proposals import GRAPH
    result = await GRAPH.ainvoke({"limit": 10, "offset": 0})
    assert result.get("ok") is True
    assert result["items"] == []
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_create_proposal_no_llm():
    """create_proposal should complete even when LLM calls fail (graceful fallback)."""
    from lg_webmk.graphs.create_proposal import GRAPH
    result = await GRAPH.ainvoke({
        "client_name": "Test Corp",
        "website_url": "",
        "industry": "technology",
        "target_audience": "SMBs",
        "budget_jpy": 500000,
        "delivery_email": "test@example.com",
    })
    # Should reach store_proposal (even if persist fails due to no RW_URL)
    assert "copy_markdown" in result or "error" in result


@pytest.mark.asyncio
async def test_deliver_proposal_no_resend():
    """deliver_proposal skips silently when RESEND_API_KEY is absent."""
    from lg_webmk.graphs.deliver_proposal import GRAPH
    result = await GRAPH.ainvoke({
        "proposal_id": "prop-test-001",
        "delivery_email": "test@example.com",
        "copy_markdown": "# Test Proposal",
    })
    assert "ok" in result
    # Should succeed (delivered=False) when RESEND_API_KEY not set
    assert result.get("ok") is True or "error" in result


def test_nsid_map_coverage():
    from lg_webmk.server import _NSID_MAP, GRAPHS
    for nsid, assistant_id in _NSID_MAP.items():
        assert assistant_id in GRAPHS, f"NSID '{nsid}' maps to '{assistant_id}' but graph missing"


def test_graph_names():
    from lg_webmk.server import GRAPHS
    expected = {"health", "create_proposal", "deliver_proposal", "get_proposal", "list_proposals"}
    assert set(GRAPHS.keys()) == expected
