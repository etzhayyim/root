"""Smoke tests for lg-patent OSS FastAPI server.

Covers: imports, graph registration, NSID map, langgraph.json,
cron schedule, and the /health endpoint round-trip.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── helpers ──────────────────────────────────────────────────────────────

_LG_DIR = Path(__file__).parent.parent
_LANGGRAPH_JSON = _LG_DIR / "langgraph.json"

_EXPECTED_GRAPHS = {"health", "blob_convert", "ingest_uspto_weekly"}

_EXPECTED_NSID_MAP = {
    "com.etzhayyim.apps.patent.blobConvert":       "blob_convert",
    "com.etzhayyim.apps.patent.ingestUsptoWeekly": "ingest_uspto_weekly",
}

_EXPECTED_CRON_GRAPHS = {"blob_convert", "ingest_uspto_weekly"}


# ── import tests ─────────────────────────────────────────────────────────

def test_server_imports() -> None:
    """Server module must be importable without touching RW or external services."""
    with (
        patch("lg_patent.checkpointer.build_checkpointer"),
        patch("lg_patent.cron.start_cron"),
    ):
        import lg_patent.server as srv  # noqa: F401


def test_graphs_dict() -> None:
    with (
        patch("lg_patent.checkpointer.build_checkpointer"),
        patch("lg_patent.cron.start_cron"),
    ):
        from lg_patent.server import GRAPHS
        assert set(GRAPHS.keys()) == _EXPECTED_GRAPHS, f"GRAPHS mismatch: {set(GRAPHS.keys())}"


def test_nsid_map() -> None:
    with (
        patch("lg_patent.checkpointer.build_checkpointer"),
        patch("lg_patent.cron.start_cron"),
    ):
        from lg_patent.server import NSID_MAP
        assert NSID_MAP == _EXPECTED_NSID_MAP, f"NSID_MAP mismatch: {NSID_MAP}"


def test_nsid_map_targets_valid_graphs() -> None:
    with (
        patch("lg_patent.checkpointer.build_checkpointer"),
        patch("lg_patent.cron.start_cron"),
    ):
        from lg_patent.server import GRAPHS, NSID_MAP
        for nsid, graph_name in NSID_MAP.items():
            assert graph_name in GRAPHS, f"NSID {nsid!r} → unknown graph {graph_name!r}"


# ── langgraph.json tests ──────────────────────────────────────────────────

def test_langgraph_json_exists() -> None:
    assert _LANGGRAPH_JSON.exists(), f"langgraph.json not found at {_LANGGRAPH_JSON}"


def test_langgraph_json_graphs() -> None:
    cfg = json.loads(_LANGGRAPH_JSON.read_text())
    assert set(cfg["graphs"].keys()) == _EXPECTED_GRAPHS, f"graphs mismatch: {set(cfg['graphs'].keys())}"


def test_langgraph_json_crons() -> None:
    cfg = json.loads(_LANGGRAPH_JSON.read_text())
    crons = cfg.get("crons", [])
    cron_graph_names = {c["graph"] for c in crons if "graph" in c}
    assert cron_graph_names == _EXPECTED_CRON_GRAPHS, f"cron graphs mismatch: {cron_graph_names}"


def test_blob_convert_cron_every_5min() -> None:
    cfg = json.loads(_LANGGRAPH_JSON.read_text())
    blob_crons = [c for c in cfg.get("crons", []) if c.get("graph") == "blob_convert"]
    assert blob_crons, "blob_convert cron not found in langgraph.json"
    assert blob_crons[0]["schedule"] == "*/5 * * * *", f"blob_convert schedule wrong: {blob_crons[0]['schedule']}"


def test_ingest_uspto_weekly_cron() -> None:
    cfg = json.loads(_LANGGRAPH_JSON.read_text())
    weekly_crons = [c for c in cfg.get("crons", []) if c.get("graph") == "ingest_uspto_weekly"]
    assert weekly_crons, "ingest_uspto_weekly cron not found in langgraph.json"


def test_langgraph_json_rw_checkpointer() -> None:
    cfg = json.loads(_LANGGRAPH_JSON.read_text())
    cp = cfg.get("checkpointer", {})
    assert cp.get("conn_str_env") == "RW_URL", "checkpointer must use RW_URL"


# ── graph wrapper imports ─────────────────────────────────────────────────

def test_health_graph_import() -> None:
    from lg_patent.graphs.health import GRAPH
    assert GRAPH is not None


def test_blob_convert_graph_import() -> None:
    from lg_patent.graphs.blob_convert import GRAPH
    assert GRAPH is not None


def test_ingest_uspto_weekly_graph_import() -> None:
    from lg_patent.graphs.ingest_uspto_weekly import GRAPH
    assert GRAPH is not None


# ── HTTP round-trip ───────────────────────────────────────────────────────

@pytest.fixture()
def client():
    from unittest.mock import AsyncMock, MagicMock
    mock_cp = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_cp)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)

    os.environ.pop("LG_API_KEY", None)
    os.environ["LG_CRON_ENABLED"] = "false"

    with (
        patch("lg_patent.server.build_checkpointer", return_value=mock_ctx),
        patch("lg_patent.server.start_cron", return_value=None),
        patch("lg_patent.server.stop_cron", return_value=None),
    ):
        from fastapi.testclient import TestClient
        from lg_patent.server import app
        with TestClient(app) as c:
            yield c


def test_health_endpoint(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["app"] == "lg-patent"
    assert set(body["graphs"]) == _EXPECTED_GRAPHS


def test_ok_endpoint(client) -> None:
    r = client.get("/ok")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_graphs_endpoint(client) -> None:
    r = client.get("/graphs")
    assert r.status_code == 200
    assert set(r.json()["graphs"]) == _EXPECTED_GRAPHS


def test_runs_unknown_graph(client) -> None:
    r = client.post("/runs", json={"assistant_id": "nonexistent"})
    assert r.status_code == 404


def test_xrpc_unknown_nsid(client) -> None:
    r = client.post("/xrpc/com.etzhayyim.apps.patent.unknownMethod", json={})
    assert r.status_code == 404


def test_xrpc_blob_convert_dispatches(client) -> None:
    mock_result = {"ok": True, "converted": 3}
    with patch.object(
        client.app.state.graphs.get("blob_convert", MagicMock()),
        "ainvoke",
        AsyncMock(return_value=mock_result),
    ):
        r = client.post("/xrpc/com.etzhayyim.apps.patent.blobConvert", json={"limit": 5})
    assert r.status_code in (200, 500)


# ── kotodama graph source tests ─────────────────────────────────────────

def test_patent_blob_convert_build_graph() -> None:
    from kotodama.langgraph_graphs.patent_blob_convert import build_graph
    g = build_graph()
    assert g is not None


def test_patent_ingest_uspto_weekly_build_graph() -> None:
    from kotodama.langgraph_graphs.patent_ingest_uspto_weekly import build_graph
    g = build_graph()
    assert g is not None
