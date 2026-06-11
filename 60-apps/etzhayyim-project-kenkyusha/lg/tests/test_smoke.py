"""Local smoke tests for lg-kenkyusha OSS server.

Run from `60-apps/etzhayyim-project-kenkyusha/lg/`:
    uv venv --python 3.11 .venv
    uv pip install --python .venv/bin/python \
        'fastapi>=0.115' 'httpx>=0.27' 'pytest>=8' \
        'langgraph>=0.2.50' 'langchain-core>=0.3.0'
    .venv/bin/pytest tests/ -v

CI gate: wire into existing pytest config so it runs on every PR
touching `60-apps/etzhayyim-project-kenkyusha/lg/**`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("RW_URL", "postgresql://stub@localhost/none")
os.environ.setdefault("LG_AUDIT_DISABLED", "1")
os.environ.setdefault("LG_CRON_ENABLED", "false")
os.environ.setdefault("LG_KENKYUSHA_API_KEY", "")

_LG_DIR = Path(__file__).resolve().parents[1]

_EXPECTED_GRAPHS = {"kenkyusha_research_loop"}


def test_server_module_imports():
    from lg_kenkyusha.server import GRAPHS, app
    assert app is not None
    assert isinstance(GRAPHS, dict)


def test_graphs_match_expected_set():
    from lg_kenkyusha.server import GRAPHS
    assert set(GRAPHS.keys()) == _EXPECTED_GRAPHS, (
        f"GRAPHS keys mismatch.\n"
        f"  extra:   {set(GRAPHS.keys()) - _EXPECTED_GRAPHS}\n"
        f"  missing: {_EXPECTED_GRAPHS - set(GRAPHS.keys())}"
    )


def test_langgraph_json_graphs_match_server():
    cfg = json.loads((_LG_DIR / "langgraph.json").read_text())
    declared_keys = set(cfg["graphs"].keys())
    from lg_kenkyusha.server import GRAPHS
    assert declared_keys == set(GRAPHS.keys()), (
        f"drift: langgraph.json={declared_keys} server={set(GRAPHS.keys())}"
    )


def test_langgraph_json_has_cron_for_research_loop():
    cfg = json.loads((_LG_DIR / "langgraph.json").read_text())
    cron_graph_ids = {c.get("graph_id") or c.get("graph") for c in cfg.get("crons", [])}
    assert "kenkyusha_research_loop" in cron_graph_ids, (
        "kenkyusha_research_loop must have a scheduled cron"
    )


def test_all_graphs_are_invocable():
    from lg_kenkyusha.server import GRAPHS
    for name, graph in GRAPHS.items():
        assert hasattr(graph, "ainvoke"), f"GRAPHS[{name!r}] missing .ainvoke"


@pytest.fixture
def client():
    from lg_kenkyusha.server import app
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_ok_endpoint_lists_graphs(client):
    r = client.get("/ok")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert set(body["graphs"]) == _EXPECTED_GRAPHS


def test_unknown_graph_404(client):
    r = client.post("/runs", json={"assistant_id": "nope", "input": {}})
    assert r.status_code == 404


def test_unknown_nsid_xrpc_404(client):
    r = client.post("/xrpc/com.etzhayyim.apps.kenkyusha.unknownMethod", json={})
    assert r.status_code == 404
