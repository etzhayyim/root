"""Local smoke tests for lg-curpus2skill OSS server.

Run from `60-apps/etzhayyim-project-curpus2skill/lg/`:
    uv venv --python 3.11 .venv
    uv pip install --python .venv/bin/python \
        'fastapi>=0.115' 'httpx>=0.27' 'pytest>=8' \
        'langgraph>=0.2.50' 'langchain-core>=0.3.0'
    .venv/bin/pytest tests/ -v

CI gate: wire into existing pytest config so it runs on every PR
touching `60-apps/etzhayyim-project-curpus2skill/lg/**`.
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

_EXPECTED_GRAPHS = {"health", "extractEvidence"}

_EXPECTED_NSID_MAP = {
    "com.etzhayyim.apps.curpus2skill.health":          "health",
    "com.etzhayyim.apps.curpus2skill.extractEvidence": "extractEvidence",
}


def test_server_module_imports():
    from lg_curpus2skill.server import GRAPHS, _NSID_TO_ASSISTANT, app
    assert app is not None
    assert isinstance(GRAPHS, dict)
    assert isinstance(_NSID_TO_ASSISTANT, dict)


def test_graphs_match_expected_set():
    from lg_curpus2skill.server import GRAPHS
    assert set(GRAPHS.keys()) == _EXPECTED_GRAPHS, (
        f"GRAPHS keys mismatch.\n"
        f"  extra:   {set(GRAPHS.keys()) - _EXPECTED_GRAPHS}\n"
        f"  missing: {_EXPECTED_GRAPHS - set(GRAPHS.keys())}"
    )


def test_nsid_map_completeness():
    from lg_curpus2skill.server import _NSID_TO_ASSISTANT
    assert _NSID_TO_ASSISTANT == _EXPECTED_NSID_MAP


def test_nsid_map_references_known_graphs():
    from lg_curpus2skill.server import GRAPHS, _NSID_TO_ASSISTANT
    for nsid, graph_name in _NSID_TO_ASSISTANT.items():
        assert graph_name in GRAPHS, f"_NSID_TO_ASSISTANT[{nsid!r}] → {graph_name!r} not in GRAPHS"


def test_langgraph_json_graphs_match_server():
    cfg = json.loads((_LG_DIR / "langgraph.json").read_text())
    declared_keys = set(cfg["graphs"].keys())
    from lg_curpus2skill.server import GRAPHS
    assert declared_keys == set(GRAPHS.keys()), (
        f"drift: langgraph.json={declared_keys} server={set(GRAPHS.keys())}"
    )


def test_langgraph_json_has_no_crons():
    cfg = json.loads((_LG_DIR / "langgraph.json").read_text())
    assert cfg.get("crons", []) == [], "Unexpected cron entries in langgraph.json"


def test_all_graphs_are_invocable():
    from lg_curpus2skill.server import GRAPHS
    for name, graph in GRAPHS.items():
        assert hasattr(graph, "ainvoke"), f"GRAPHS[{name!r}] missing .ainvoke"


@pytest.fixture
def client():
    from lg_curpus2skill.server import app
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


def test_unknown_assistant_404(client):
    r = client.post("/runs", json={"assistant_id": "nope", "input": {}})
    assert r.status_code == 404


def test_unknown_nsid_xrpc_404(client):
    r = client.post("/xrpc/com.etzhayyim.apps.curpus2skill.unknownMethod", json={})
    assert r.status_code == 404
