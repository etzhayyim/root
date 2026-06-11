"""Local smoke tests for lg-open-jpn-mynumber OSS server.

Run from `60-apps/etzhayyim-project-open-jpn-mynumber/lg/`:
    uv venv --python 3.11 .venv
    uv pip install --python .venv/bin/python \
        'fastapi>=0.115' 'httpx>=0.27' 'pytest>=8' \
        'langgraph>=0.2.50' 'langchain-core>=0.3.0'
    .venv/bin/pytest tests/ -v

CI gate: wire into existing pytest config so it runs on every PR
touching `60-apps/etzhayyim-project-open-jpn-mynumber/lg/**`.
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

_LG_DIR = Path(__file__).resolve().parents[1]

_HEALTH_NSID = "com.etzhayyim.apps.openJpnMynumber.health"


def test_server_module_imports():
    from lg_open_jpn_mynumber.server import GRAPHS, _NSID_TO_ASSISTANT, app
    assert app is not None
    assert isinstance(GRAPHS, dict)
    assert isinstance(_NSID_TO_ASSISTANT, dict)


def test_health_graph_present():
    from lg_open_jpn_mynumber.server import GRAPHS
    assert "health" in GRAPHS, "GRAPHS must contain 'health'"


def test_health_nsid_in_nsid_map():
    from lg_open_jpn_mynumber.server import _NSID_TO_ASSISTANT
    assert _HEALTH_NSID in _NSID_TO_ASSISTANT
    assert _NSID_TO_ASSISTANT[_HEALTH_NSID] == "health"


def test_nsid_map_references_known_graphs():
    from lg_open_jpn_mynumber.server import GRAPHS, _NSID_TO_ASSISTANT
    for nsid, graph_name in _NSID_TO_ASSISTANT.items():
        assert graph_name in GRAPHS, (
            f"_NSID_TO_ASSISTANT[{nsid!r}] → {graph_name!r} not in GRAPHS"
        )


def test_langgraph_json_graphs_match_server():
    cfg = json.loads((_LG_DIR / "langgraph.json").read_text())
    declared_keys = set(cfg["graphs"].keys())
    from lg_open_jpn_mynumber.server import GRAPHS
    assert declared_keys == set(GRAPHS.keys()), (
        f"drift: langgraph.json={declared_keys} server={set(GRAPHS.keys())}"
    )


def test_langgraph_json_has_no_crons():
    cfg = json.loads((_LG_DIR / "langgraph.json").read_text())
    assert cfg.get("crons", []) == [], "Unexpected cron entries in langgraph.json"


def test_all_graphs_are_invocable():
    from lg_open_jpn_mynumber.server import GRAPHS
    for name, graph in GRAPHS.items():
        assert hasattr(graph, "ainvoke"), f"GRAPHS[{name!r}] missing .ainvoke"


@pytest.fixture
def client():
    from lg_open_jpn_mynumber.server import app
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_unknown_assistant_404(client):
    r = client.post("/runs", json={"assistant_id": "nope", "input": {}})
    assert r.status_code == 404


def test_unknown_nsid_xrpc_404(client):
    r = client.post("/xrpc/com.etzhayyim.apps.openJpnMynumber.unknownMethod", json={})
    assert r.status_code == 404
