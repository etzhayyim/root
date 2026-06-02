"""Smoke tests for lg-yatabase LangGraph server."""
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

_LANGGRAPH_JSON = Path(__file__).parent.parent / "langgraph.json"

_EXPECTED_GRAPHS = {"health", "marketing", "sales", "bmc_iteration"}
_EXPECTED_NSID_MAP = {
    "com.etzhayyim.apps.yata.lg.health": "health",
    "com.etzhayyim.apps.yata.lg.marketing.run": "marketing",
    "com.etzhayyim.apps.yata.lg.sales.run": "sales",
    "com.etzhayyim.apps.yata.lg.bmc.iterate": "bmc_iteration",
}
_CRON_GRAPHS = {"marketing", "sales", "bmc_iteration"}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        "lg_yatabase.bmc.db.get_pool", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(
        "lg_yatabase.bmc.db.close_pool", AsyncMock()
    )

    from lg_yatabase.server import app

    with TestClient(app) as c:
        yield c


def test_health_endpoint(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["app"] == "lg-yatabase"
    assert set(data["graphs"]) == _EXPECTED_GRAPHS


def test_ok_endpoint(client: TestClient) -> None:
    r = client.get("/ok")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True


def test_graphs_endpoint(client: TestClient) -> None:
    r = client.get("/graphs")
    assert r.status_code == 200
    data = r.json()
    assert set(data["graphs"]) == _EXPECTED_GRAPHS
    assert data["nsidMap"] == _EXPECTED_NSID_MAP


def test_langgraph_json_drift() -> None:
    from lg_yatabase.server import GRAPHS
    lg = json.loads(_LANGGRAPH_JSON.read_text())
    assert set(GRAPHS.keys()) == set(lg["graphs"].keys()), (
        f"server GRAPHS and langgraph.json drift.\n"
        f"server only: {set(GRAPHS) - set(lg['graphs'])}\n"
        f"json only:   {set(lg['graphs']) - set(GRAPHS)}"
    )


def test_langgraph_json_has_crons_for_scheduled_graphs() -> None:
    lg = json.loads(_LANGGRAPH_JSON.read_text())
    cron_graph_ids = {c.get("graph") or c.get("graph_id") for c in lg.get("crons", [])}
    assert _CRON_GRAPHS <= cron_graph_ids, (
        f"missing crons for: {_CRON_GRAPHS - cron_graph_ids}"
    )


def test_nsid_map_correctness() -> None:
    from lg_yatabase.server import NSID_TO_GRAPH
    assert NSID_TO_GRAPH == _EXPECTED_NSID_MAP


def test_all_graphs_have_ainvoke() -> None:
    from lg_yatabase.server import GRAPHS
    for name, graph in GRAPHS.items():
        assert hasattr(graph, "ainvoke") or hasattr(graph, "invoke"), (
            f"graph {name!r} missing .ainvoke/.invoke"
        )


def test_unknown_nsid_xrpc_404(client: TestClient) -> None:
    r = client.post("/xrpc/com.etzhayyim.apps.yata.unknownMethod", json={})
    assert r.status_code == 404
