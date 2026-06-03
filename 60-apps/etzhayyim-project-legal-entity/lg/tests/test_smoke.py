"""Local smoke tests for lg-legal-entity OSS server.

Covers the 17-graph legal entity collector dispatcher (GLEIF/EDGAR/registry).

Run from `60-apps/etzhayyim-project-legal-entity/lg/`:
    uv venv --python 3.11 .venv
    uv pip install --python .venv/bin/python \
        'fastapi>=0.115' 'httpx>=0.27' 'pytest>=8' \
        'langgraph>=0.2.50' 'langchain-core>=0.3.0'
    .venv/bin/pytest tests/ -v

CI gate: wire into existing pytest config so it runs on every PR
touching `60-apps/etzhayyim-project-legal-entity/lg/**`.
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

_LG_DIR = Path(__file__).resolve().parents[1]

_REGISTRY_SUFFIXES = ["Jpn", "Gbr", "Fra", "Nor", "Dnk", "Fin", "Est", "Cze", "Nzl", "Che", "Nld", "Isr"]

_EXPECTED_GRAPHS = (
    {"health", "gleifFetchPages", "gleifRegisterDids", "edgarCollectUsa", "edgarIngestSecDisclosure"}
    | {f"registryCollect{s}" for s in _REGISTRY_SUFFIXES}
)


def test_server_module_imports():
    from lg_legal_entity.server import GRAPHS, _NSID_TO_ASSISTANT, app
    assert app is not None
    assert isinstance(GRAPHS, dict)
    assert isinstance(_NSID_TO_ASSISTANT, dict)


def test_graphs_match_expected_set():
    from lg_legal_entity.server import GRAPHS
    assert set(GRAPHS.keys()) == _EXPECTED_GRAPHS, (
        f"GRAPHS keys mismatch.\n"
        f"  extra:   {set(GRAPHS.keys()) - _EXPECTED_GRAPHS}\n"
        f"  missing: {_EXPECTED_GRAPHS - set(GRAPHS.keys())}"
    )


def test_nsid_to_assistant_completeness():
    from lg_legal_entity.server import GRAPHS, _NSID_TO_ASSISTANT
    assistant_values = set(_NSID_TO_ASSISTANT.values())
    assert assistant_values <= set(GRAPHS.keys()), (
        f"_NSID_TO_ASSISTANT references unknown graph keys: "
        f"{assistant_values - set(GRAPHS.keys())}"
    )


def test_langgraph_json_graphs_match_server():
    """Catches drift between langgraph.json graphs and server GRAPHS dict."""
    cfg = json.loads((_LG_DIR / "langgraph.json").read_text())
    declared = set(cfg["graphs"].keys())
    from lg_legal_entity.server import GRAPHS
    assert declared == set(GRAPHS.keys()), (
        f"drift: langgraph.json={declared} server={set(GRAPHS.keys())}"
    )


def test_langgraph_json_has_no_crons():
    """legal-entity has no scheduled crons — all collectors are XRPC-triggered."""
    cfg = json.loads((_LG_DIR / "langgraph.json").read_text())
    assert cfg.get("crons", []) == [], "Unexpected cron entries in langgraph.json"


@pytest.fixture
def client():
    from lg_legal_entity.server import app
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True


def test_ok_endpoint_lists_graphs(client):
    r = client.get("/ok")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert set(body["graphs"]) == _EXPECTED_GRAPHS


def test_unknown_assistant_404(client):
    r = client.post("/runs", json={"assistant_id": "nope", "input": {}})
    assert r.status_code == 404


def test_unknown_xrpc_404(client):
    r = client.post("/xrpc/com.etzhayyim.legalEntity.unknownMethod", json={})
    assert r.status_code == 404


def test_all_graphs_are_invocable():
    """Each graph in GRAPHS must have .ainvoke (LangGraph compiled graph contract)."""
    from lg_legal_entity.server import GRAPHS
    for name, graph in GRAPHS.items():
        assert hasattr(graph, "ainvoke"), f"GRAPHS[{name!r}] missing .ainvoke"
