"""Local smoke tests for lg-animeka OSS server.

Run from `60-apps/etzhayyim-project-animeka/lg/`:
    uv venv --python 3.11 .venv
    uv pip install --python .venv/bin/python \
        'fastapi>=0.115' 'httpx>=0.27' 'pytest>=8' 'pytest-asyncio>=0.23' \
        'langgraph>=0.2.50' 'apscheduler>=3.10' 'langchain-core>=0.3.0' \
        'langgraph-checkpoint>=2.0.0'
    .venv/bin/pytest tests/ -v
    # or: python3.11 -m pytest tests/ -v

CI gate: wire into existing pytest config so it runs on
every PR touching `60-apps/etzhayyim-project-animeka/lg/**`.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Make `lg_animeka` importable when pytest is invoked from this dir.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ── stub kotodama so the entire pipeline imports cleanly without
#    real ComfyUI / PDS / psycopg dependencies.  Graph nodes that
#    touch these stubs are never executed here; we only validate wiring.
_pmg = types.ModuleType("kotodama")
sys.modules["kotodama"] = _pmg

_pmg_p = types.ModuleType("kotodama.primitives")
sys.modules["kotodama.primitives"] = _pmg_p

_pmg_si = types.ModuleType("kotodama.primitives.shinshi_image")
for _n in (
    "_build_anime_workflow", "_comfy_render_png",
    "_upload_blob_to_pds", "_post_scene",
):
    setattr(_pmg_si, _n, lambda *a, **k: None)
sys.modules["kotodama.primitives.shinshi_image"] = _pmg_si

# Stub psycopg so graph-level `import psycopg` doesn't raise.
_psycopg = types.ModuleType("psycopg")


class _FakeConn:
    async def execute(self, *a, **k):
        pass

    async def close(self):
        pass

    cursor = lambda self: self  # noqa: E731
    fetchone = lambda self: None  # noqa: E731
    fetchall = lambda self: []  # noqa: E731

    @staticmethod
    async def connect(*a, **k):
        return _FakeConn()


_psycopg.AsyncConnection = _FakeConn
sys.modules["psycopg"] = _psycopg

# Disable real DB / audit during tests.
os.environ.setdefault("LG_CHECKPOINTER_URL", "postgresql://stub@localhost/none")
os.environ.setdefault("RW_URL", "postgresql://stub@localhost/none")
os.environ.setdefault("LG_AUDIT_DISABLED", "1")
os.environ.setdefault("LG_CRON_ENABLED", "false")


# ── helper constants ────────────────────────────────────────────────────

_ALL_GRAPH_NAMES = {
    "health", "list_works", "agent_chat",
    "get_cut", "list_cuts", "list_episodes", "list_retakes",
    "create_work", "add_episode", "add_cut",
    "update_cut_stage", "submit_retake", "resolve_retake",
    "generate_script", "generate_storyboard", "generate_layout",
    "generate_keyframe", "generate_inbetween", "generate_background",
    "design_color_model",
    "autopilot", "cut_runner", "auto_trace_cut", "breakdown_scene",
    "generate_audio", "assemble_episode",
}


# ── import + compile tests ──────────────────────────────────────────────

def test_audit_helpers_import():
    from lg_animeka.audit import emit_audit_bg
    assert callable(emit_audit_bg)


def test_all_26_graphs_compile():
    from lg_animeka.graphs.health import GRAPH as G1
    from lg_animeka.graphs.list_works import GRAPH as G2
    from lg_animeka.graphs.agent_chat import GRAPH as G3
    from lg_animeka.graphs.get_cut import GRAPH as G4
    from lg_animeka.graphs.list_episodes import GRAPH as G5
    from lg_animeka.graphs.list_retakes import GRAPH as G6
    from lg_animeka.graphs.create_work import GRAPH as G7
    from lg_animeka.graphs.add_episode import GRAPH as G8
    from lg_animeka.graphs.add_cut import GRAPH as G9
    from lg_animeka.graphs.update_cut_stage import GRAPH as G10
    from lg_animeka.graphs.submit_retake import GRAPH as G11
    from lg_animeka.graphs.resolve_retake import GRAPH as G12
    from lg_animeka.graphs.generate_script import GRAPH as G13
    from lg_animeka.graphs.generate_storyboard import GRAPH as G14
    from lg_animeka.graphs.generate_layout import GRAPH as G15
    from lg_animeka.graphs.generate_keyframe import GRAPH as G16
    from lg_animeka.graphs.generate_inbetween import GRAPH as G17
    from lg_animeka.graphs.generate_background import GRAPH as G18
    from lg_animeka.graphs.design_color_model import GRAPH as G19
    from lg_animeka.graphs.autopilot import GRAPH as G20
    from lg_animeka.graphs.cut_runner import GRAPH as G21
    from lg_animeka.graphs.auto_trace_cut import GRAPH as G22
    from lg_animeka.graphs.breakdown_scene import GRAPH as G23
    from lg_animeka.graphs.list_cuts import GRAPH as G24
    from lg_animeka.graphs.generate_audio import GRAPH as G25
    from lg_animeka.graphs.assemble_episode import GRAPH as G26
    names = {
        G1.name, G2.name, G3.name, G4.name, G5.name, G6.name,
        G7.name, G8.name, G9.name, G10.name, G11.name, G12.name,
        G13.name, G14.name, G15.name, G16.name, G17.name, G18.name,
        G19.name, G20.name, G21.name, G22.name, G23.name,
        G24.name, G25.name, G26.name,
    }
    assert names == _ALL_GRAPH_NAMES


def test_breakdown_scene_node_topology():
    """Catches accidental edge re-wiring in breakdownScene."""
    from lg_animeka.graphs.breakdown_scene import GRAPH
    nodes = set(GRAPH.nodes.keys())
    assert nodes == {"__start__", "llm_breakdown", "insert_cuts", "audit"}


def test_cut_runner_node_topology():
    """cutRunner must have all 7 nodes."""
    from lg_animeka.graphs.cut_runner import GRAPH
    nodes = set(GRAPH.nodes.keys())
    assert nodes == {
        "__start__", "fetch_cut", "storyboard", "layout",
        "keyframe", "background", "update_cut", "audit",
    }


def test_auto_trace_cut_node_topology():
    from lg_animeka.graphs.auto_trace_cut import GRAPH
    nodes = set(GRAPH.nodes.keys())
    assert nodes == {"__start__", "fetch_keyframes", "trace", "insert", "audit"}


def test_autopilot_has_storyboard_retry():
    """autopilot must include the conditional storyboard_retry node."""
    from lg_animeka.graphs.autopilot import GRAPH
    nodes = set(GRAPH.nodes.keys())
    assert "storyboard_retry" in nodes


def test_langgraph_json_graphs_complete():
    """langgraph.json must declare all 26 graphs and no extras."""
    import json
    cfg = json.loads(
        Path(__file__).resolve().parents[1].joinpath("langgraph.json").read_text()
    )
    assert set(cfg["graphs"].keys()) == _ALL_GRAPH_NAMES


def test_langgraph_json_crons_match_graphs():
    """cron graph refs must be a subset of declared graphs."""
    import json
    cfg = json.loads(
        Path(__file__).resolve().parents[1].joinpath("langgraph.json").read_text()
    )
    declared = set(cfg["graphs"].keys())
    cron_refs = {c["graph"] for c in cfg.get("crons", [])}
    assert cron_refs.issubset(declared), \
        f"cron refs unknown graphs: {cron_refs - declared}"


def test_autopilot_cron_registered():
    """autopilot must appear in crons with a 15-min schedule."""
    import json
    cfg = json.loads(
        Path(__file__).resolve().parents[1].joinpath("langgraph.json").read_text()
    )
    crons = cfg.get("crons", [])
    ap = [c for c in crons if c["graph"] == "autopilot"]
    assert ap, "autopilot cron not found"
    assert ap[0]["schedule"] == "*/15 * * * *"


def test_nsid_to_assistant_coverage():
    """_NSID_TO_ASSISTANT must map all 26 graph assistant_ids."""
    from lg_animeka.server import _NSID_TO_ASSISTANT
    mapped = set(_NSID_TO_ASSISTANT.values())
    assert mapped == _ALL_GRAPH_NAMES


# ── HTTP surface (sync TestClient — no real DB) ─────────────────────────

@pytest.fixture
def client_no_lifespan(monkeypatch):
    """TestClient with checkpointer + cron stubbed out."""
    from contextlib import asynccontextmanager
    from lg_animeka import server as srv

    @asynccontextmanager
    async def _fake_cp_ctx():
        yield object()

    async def _fake_stop_cron(s):
        return None

    monkeypatch.setattr(srv, "build_checkpointer", _fake_cp_ctx)
    monkeypatch.setattr(srv, "start_cron", lambda graphs: None)
    monkeypatch.setattr(srv, "stop_cron", _fake_stop_cron)

    with TestClient(srv.app) as client:
        yield client


def test_ok_endpoint_lists_all_26_graphs(client_no_lifespan):
    r = client_no_lifespan.get("/ok")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert set(body["graphs"]) == _ALL_GRAPH_NAMES


def test_health_endpoint(client_no_lifespan):
    r = client_no_lifespan.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_unknown_assistant_404(client_no_lifespan):
    r = client_no_lifespan.post(
        "/runs",
        json={"assistant_id": "does_not_exist", "input": {}},
    )
    assert r.status_code == 404


def test_unknown_xrpc_nsid_404(client_no_lifespan):
    r = client_no_lifespan.post(
        "/xrpc/com.etzhayyim.animeka.doesNotExist",
        json={},
    )
    assert r.status_code == 404


def test_api_key_enforced_when_set(monkeypatch):
    """LG_API_KEY set → /runs without x-api-key → 401."""
    monkeypatch.setenv("LG_API_KEY", "testkey999")
    import importlib
    from lg_animeka import server as srv
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
        r = client.post("/runs", json={"assistant_id": "health", "input": {}})
        assert r.status_code == 401

        r = client.post(
            "/runs",
            headers={"x-api-key": "wrong"},
            json={"assistant_id": "health", "input": {}},
        )
        assert r.status_code == 401

        r = client.post(
            "/runs",
            headers={"x-api-key": "testkey999"},
            json={"assistant_id": "health", "input": {}},
        )
        assert r.status_code == 200


# ── cron config parsing ─────────────────────────────────────────────────

def test_cron_specs_parse_from_langgraph_json(monkeypatch):
    monkeypatch.setenv(
        "LANGGRAPH_JSON",
        str(Path(__file__).resolve().parents[1] / "langgraph.json"),
    )
    import importlib
    from lg_animeka import cron as cr
    importlib.reload(cr)
    specs = cr._load_cron_specs()
    assert len(specs) >= 1, f"expected ≥1 cron spec, got {specs}"
    schedules = {s["schedule"] for s in specs}
    assert "*/15 * * * *" in schedules
