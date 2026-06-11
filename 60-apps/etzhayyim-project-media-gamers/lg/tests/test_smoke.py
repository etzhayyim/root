"""Local smoke tests for lg-media-gamers OSS server.

Run from `60-apps/etzhayyim-project-media-gamers/lg/`:
    uv venv --python 3.11 .venv
    uv pip install --python .venv/bin/python \
        'fastapi>=0.115' 'httpx>=0.27' 'pytest>=8' \
        'langgraph>=0.2.50' 'langchain-core>=0.3.0'
    .venv/bin/pytest tests/ -v

CI gate: wire into existing pytest config so it runs on every PR
touching `60-apps/etzhayyim-project-media-gamers/lg/**`.
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

_EXPECTED_GRAPHS = {"health", "ingest_charts", "guide_generator", "autopilot", "pokopia_research"}

_EXPECTED_NSID_MAP = {
    "com.etzhayyim.apps.media_gamers.health":           "health",
    "com.etzhayyim.apps.media_gamers.ingestCharts":     "ingest_charts",
    "com.etzhayyim.apps.media_gamers.generateGuide":    "guide_generator",
    "com.etzhayyim.apps.media_gamers.autopilot":        "autopilot",
    "com.etzhayyim.apps.media_gamers.researchPokopia":  "pokopia_research",
}


def test_server_module_imports():
    from lg_media_gamers.server import GRAPHS, _NSID_TO_ASSISTANT, app
    assert app is not None
    assert isinstance(GRAPHS, dict)
    assert isinstance(_NSID_TO_ASSISTANT, dict)


def test_graphs_match_expected_set():
    from lg_media_gamers.server import GRAPHS
    assert set(GRAPHS.keys()) == _EXPECTED_GRAPHS, (
        f"GRAPHS keys mismatch.\n"
        f"  extra:   {set(GRAPHS.keys()) - _EXPECTED_GRAPHS}\n"
        f"  missing: {_EXPECTED_GRAPHS - set(GRAPHS.keys())}"
    )


def test_nsid_map_completeness():
    from lg_media_gamers.server import _NSID_TO_ASSISTANT
    assert _NSID_TO_ASSISTANT == _EXPECTED_NSID_MAP


def test_nsid_map_references_known_graphs():
    from lg_media_gamers.server import GRAPHS, _NSID_TO_ASSISTANT
    for nsid, graph_name in _NSID_TO_ASSISTANT.items():
        assert graph_name in GRAPHS, (
            f"_NSID_TO_ASSISTANT[{nsid!r}] → {graph_name!r} not in GRAPHS"
        )


def test_langgraph_json_graphs_match_server():
    cfg = json.loads((_LG_DIR / "langgraph.json").read_text())
    declared_keys = set(cfg["graphs"].keys())
    from lg_media_gamers.server import GRAPHS
    assert declared_keys == set(GRAPHS.keys()), (
        f"drift: langgraph.json={declared_keys} server={set(GRAPHS.keys())}"
    )


def test_langgraph_json_has_crons_for_scheduled_graphs():
    cfg = json.loads((_LG_DIR / "langgraph.json").read_text())
    cron_graphs = {c["graph"] for c in cfg.get("crons", [])}
    assert "autopilot" in cron_graphs, "autopilot must have a cron"
    assert "ingest_charts" in cron_graphs, "ingest_charts must have a cron"


def test_all_graphs_are_invocable():
    from lg_media_gamers.server import GRAPHS
    for name, graph in GRAPHS.items():
        assert hasattr(graph, "ainvoke"), f"GRAPHS[{name!r}] missing .ainvoke"


@pytest.fixture
def client(monkeypatch):
    from contextlib import asynccontextmanager
    from lg_media_gamers import server as srv

    @asynccontextmanager
    async def _fake_cp_ctx():
        yield object()

    async def _fake_stop_cron(s):
        return None

    monkeypatch.setattr(srv, "build_checkpointer", _fake_cp_ctx)
    monkeypatch.setattr(srv, "start_cron", lambda graphs: None)
    monkeypatch.setattr(srv, "stop_cron", _fake_stop_cron)

    with TestClient(srv.app) as c:
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
    assert set(body["graphs"]) == _EXPECTED_GRAPHS, (
        f"graphs mismatch.\n"
        f"  extra:   {set(body['graphs']) - _EXPECTED_GRAPHS}\n"
        f"  missing: {_EXPECTED_GRAPHS - set(body['graphs'])}"
    )


def test_unknown_nsid_xrpc_404(client):
    r = client.post("/xrpc/com.etzhayyim.apps.media_gamers.unknownMethod", json={})
    assert r.status_code == 404
