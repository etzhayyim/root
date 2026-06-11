"""Local smoke tests for lg-yukkuri OSS server.

Run from `60-apps/etzhayyim-project-yukkuri/lg/`:
    uv venv --python 3.11 .venv
    uv pip install --python .venv/bin/python \
        'fastapi>=0.115' 'httpx>=0.27' 'pytest>=8' 'pytest-asyncio>=0.23' \
        'langgraph>=0.2.50' 'apscheduler>=3.10'
    .venv/bin/pytest tests/ -v

CI gate: wire into existing pytest config so it runs on every PR
touching `60-apps/etzhayyim-project-yukkuri/lg/**`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Make `lg_yukkuri` importable when pytest is invoked from this dir.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Disable the actual checkpointer connection during tests.
os.environ.setdefault("LG_CHECKPOINTER_URL", "postgresql://stub@localhost/none")
os.environ.setdefault("RW_URL", "postgresql://stub@localhost/none")
os.environ.setdefault("LG_AUDIT_DISABLED", "1")
os.environ.setdefault("LG_CRON_ENABLED", "false")


# ── module-level imports (graphs compile during these) ──────────────────

def test_state_types_import():
    from lg_yukkuri.state import VideoState, SceneState, LineState, AssetState
    assert VideoState.__name__ == "VideoState"
    assert SceneState.__name__ == "SceneState"
    assert LineState.__name__ == "LineState"
    assert AssetState.__name__ == "AssetState"


def test_audit_helpers_import():
    from lg_yukkuri.audit import emit_audit, emit_audit_bg
    assert callable(emit_audit)
    assert callable(emit_audit_bg)


def test_all_graphs_compile():
    from lg_yukkuri.graphs.health import GRAPH as G_health
    from lg_yukkuri.graphs.list_videos import GRAPH as G_list
    from lg_yukkuri.graphs.get_video import GRAPH as G_get
    from lg_yukkuri.graphs.compose import GRAPH as G_compose
    from lg_yukkuri.graphs.generate_script import GRAPH as G_script
    from lg_yukkuri.graphs.synthesize_voice import GRAPH as G_voice
    from lg_yukkuri.graphs.generate_visual import GRAPH as G_visual
    from lg_yukkuri.graphs.generate_bgm import GRAPH as G_bgm
    from lg_yukkuri.graphs.render_video import GRAPH as G_render
    from lg_yukkuri.graphs.review_video import GRAPH as G_review

    names = {g.name for g in (
        G_health, G_list, G_get, G_compose, G_script,
        G_voice, G_visual, G_bgm, G_render, G_review,
    )}
    assert names == {
        "health", "list_videos", "get_video", "compose", "generate_script",
        "synthesize_voice", "generate_visual", "generate_bgm",
        "render_video", "review_video",
    }


def test_health_graph_node_topology():
    """Catches accidental edge re-wiring or node renames."""
    from lg_yukkuri.graphs.health import GRAPH
    nodes = set(GRAPH.nodes.keys())
    assert "__start__" in nodes
    assert "check_rw" in nodes
    assert "summarize" in nodes
    assert "audit" in nodes


def test_compose_graph_node_topology():
    from lg_yukkuri.graphs.compose import GRAPH
    nodes = set(GRAPH.nodes.keys())
    assert "__start__" in nodes
    assert "validate" in nodes
    assert "insert" in nodes
    assert "audit" in nodes


def test_nsid_to_assistant_mapping():
    from lg_yukkuri.server import _NSID_TO_ASSISTANT
    assert _NSID_TO_ASSISTANT["com.etzhayyim.apps.yukkuri.health"] == "health"
    assert _NSID_TO_ASSISTANT["com.etzhayyim.apps.yukkuri.listVideos"] == "list_videos"
    assert _NSID_TO_ASSISTANT["com.etzhayyim.apps.yukkuri.getVideo"] == "get_video"
    assert _NSID_TO_ASSISTANT["com.etzhayyim.apps.yukkuri.compose"] == "compose"
    assert _NSID_TO_ASSISTANT["com.etzhayyim.apps.yukkuri.generateScript"] == "generate_script"
    assert _NSID_TO_ASSISTANT["com.etzhayyim.apps.yukkuri.synthesizeVoice"] == "synthesize_voice"
    assert _NSID_TO_ASSISTANT["com.etzhayyim.apps.yukkuri.generateVisual"] == "generate_visual"
    assert _NSID_TO_ASSISTANT["com.etzhayyim.apps.yukkuri.generateBgm"] == "generate_bgm"
    assert _NSID_TO_ASSISTANT["com.etzhayyim.apps.yukkuri.renderVideo"] == "render_video"
    assert _NSID_TO_ASSISTANT["com.etzhayyim.apps.yukkuri.reviewVideo"] == "review_video"
    assert len(_NSID_TO_ASSISTANT) == 10


def test_langgraph_json_graphs_match_server():
    """Catches drift between langgraph.json graphs and server GRAPHS dict."""
    import json
    cfg = json.loads(
        Path(__file__).resolve().parents[1].joinpath("langgraph.json").read_text()
    )
    declared = set(cfg["graphs"].keys())
    from lg_yukkuri.server import GRAPHS
    assert declared == set(GRAPHS.keys()), (
        f"drift: langgraph.json={declared} server={set(GRAPHS.keys())}"
    )


def test_langgraph_json_has_no_crons():
    """yukkuri has no scheduled crons — verify the config stays clean."""
    import json
    cfg = json.loads(
        Path(__file__).resolve().parents[1].joinpath("langgraph.json").read_text()
    )
    assert cfg.get("crons", []) == [], "Unexpected cron entries in langgraph.json"


# ── HTTP surface (sync TestClient — no real DB, lifespan stubs out) ────

@pytest.fixture
def client_no_lifespan(monkeypatch):
    """Build TestClient with the lifespan disabled (no real DB needed)."""
    from contextlib import asynccontextmanager
    from lg_yukkuri import server as srv

    @asynccontextmanager
    async def _fake_cp_ctx():
        yield object()  # dummy checkpointer

    async def _fake_stop_cron(s):
        return None

    monkeypatch.setattr(srv, "build_checkpointer", _fake_cp_ctx)
    monkeypatch.setattr(srv, "start_cron", lambda graphs: None)
    monkeypatch.setattr(srv, "stop_cron", _fake_stop_cron)

    with TestClient(srv.app) as client:
        yield client


def test_ok_endpoint(client_no_lifespan):
    r = client_no_lifespan.get("/ok")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert set(body["graphs"]) == {
        "health", "list_videos", "get_video", "compose", "generate_script",
        "synthesize_voice", "generate_visual", "generate_bgm",
        "render_video", "review_video",
    }


def test_health_endpoint(client_no_lifespan):
    r = client_no_lifespan.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_unknown_assistant_404(client_no_lifespan):
    r = client_no_lifespan.post(
        "/runs",
        json={"assistant_id": "nope", "input": {}},
    )
    assert r.status_code == 404


def test_unknown_nsid_xrpc_404(client_no_lifespan):
    r = client_no_lifespan.post(
        "/xrpc/com.etzhayyim.apps.yukkuri.unknownMethod",
        json={},
    )
    assert r.status_code == 404


def test_api_key_enforced_when_set(monkeypatch):
    """If LG_API_KEY env is set, requests without x-api-key header → 401."""
    monkeypatch.setenv("LG_API_KEY", "secret123")
    import importlib
    from lg_yukkuri import server as srv
    importlib.reload(srv)

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _fake_cp_ctx():
        yield object()

    async def _fake_stop_cron(s):
        return None

    monkeypatch.setattr(srv, "build_checkpointer", _fake_cp_ctx)
    monkeypatch.setattr(srv, "start_cron", lambda graphs: None)
    monkeypatch.setattr(srv, "stop_cron", _fake_stop_cron)

    with TestClient(srv.app) as client:
        # No header → 401
        r = client.post("/runs", json={"assistant_id": "health", "input": {}})
        assert r.status_code == 401
        # Wrong key → 401
        r = client.post(
            "/runs",
            headers={"x-api-key": "wrong"},
            json={"assistant_id": "health", "input": {}},
        )
        assert r.status_code == 401
        # Right key → invokes graph (stub returns result without DB)
        r = client.post(
            "/runs",
            headers={"x-api-key": "secret123"},
            json={"assistant_id": "health", "input": {}},
        )
        # 200 even if graph fails internally (error is JSON-wrapped)
        assert r.status_code == 200
