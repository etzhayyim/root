"""Smoke tests for lg-mangaka LangGraph server."""
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

_LANGGRAPH_JSON = Path(__file__).parent.parent / "langgraph.json"

_EXPECTED_NSID_MAP = {
    "com.etzhayyim.mangaka.health":              "health",
    "com.etzhayyim.mangaka.chat":                "agent_chat",
    "com.etzhayyim.mangaka.pipelineChat":        "agent_chat",
    "com.etzhayyim.mangaka.projectChat":         "agent_chat",
    "com.etzhayyim.mangaka.saveDocument":        "save_document",
    "com.etzhayyim.mangaka.loadDocument":        "load_document",
    "com.etzhayyim.mangaka.listDocuments":       "list_documents",
    "com.etzhayyim.mangaka.importGhosthacker":       "import_ghosthacker",
    "com.etzhayyim.mangaka.analyzeCharacterGraph":   "analyze_character_graph",
    "com.etzhayyim.mangaka.enrichCharacters":        "enrich_characters",
    "com.etzhayyim.mangaka.enrichOrganizations":     "enrich_organizations",
    "com.etzhayyim.mangaka.enrichEnvironments":      "enrich_environments",
    "com.etzhayyim.mangaka.deriveChapterIncidents":  "derive_chapter_incidents",
    "com.etzhayyim.mangaka.importChatHistory":       "import_chat_history",
    "com.etzhayyim.mangaka.backfillMangakaEdges":    "backfill_mangaka_edges",
    "com.etzhayyim.mangaka.recordOpLog":             "record_op_log",
    "com.etzhayyim.mangaka.debugCanvasState":        "debug_canvas_state",
    "com.etzhayyim.mangaka.detectFaces":             "detect_faces",
    "com.etzhayyim.mangaka.scoreEmotion":            "score_emotion",
}


@pytest.fixture
def client(monkeypatch):
    mock_cp = MagicMock()
    cp_ctx = MagicMock()
    cp_ctx.__aenter__ = AsyncMock(return_value=mock_cp)
    cp_ctx.__aexit__ = AsyncMock(return_value=False)

    monkeypatch.setattr("lg_mangaka.server.build_checkpointer", lambda: cp_ctx)
    monkeypatch.setattr("lg_mangaka.server.start_cron", lambda bound: MagicMock())
    monkeypatch.setattr("lg_mangaka.server.stop_cron", AsyncMock())
    monkeypatch.setattr(
        "lg_mangaka.server._maybe_load_topology_graphs", AsyncMock()
    )

    from lg_mangaka.server import app

    with TestClient(app) as c:
        yield c


def test_ok_endpoint_lists_graphs(client: TestClient) -> None:
    r = client.get("/ok")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    graphs = data["graphs"]
    from lg_mangaka.server import GRAPHS
    assert set(graphs) == set(GRAPHS.keys())


def test_langgraph_json_drift() -> None:
    from lg_mangaka.server import GRAPHS
    lg = json.loads(_LANGGRAPH_JSON.read_text())
    assert set(GRAPHS.keys()) == set(lg["graphs"].keys()), (
        f"server GRAPHS and langgraph.json drift.\n"
        f"server only: {set(GRAPHS) - set(lg['graphs'])}\n"
        f"json only:   {set(lg['graphs']) - set(GRAPHS)}"
    )


def test_nsid_map_completeness() -> None:
    from lg_mangaka.server import _NSID_TO_ASSISTANT, GRAPHS
    mapped_graphs = set(_NSID_TO_ASSISTANT.values())
    non_health_graphs = {k for k in GRAPHS if k != "health"}
    assert non_health_graphs <= mapped_graphs, (
        f"graphs without any NSID mapping: {non_health_graphs - mapped_graphs}"
    )
    assert _NSID_TO_ASSISTANT == _EXPECTED_NSID_MAP, (
        f"_NSID_TO_ASSISTANT changed.\n"
        f"expected: {_EXPECTED_NSID_MAP}\n"
        f"actual:   {_NSID_TO_ASSISTANT}"
    )


def test_all_graphs_have_ainvoke() -> None:
    from lg_mangaka.server import GRAPHS
    for name, graph in GRAPHS.items():
        assert hasattr(graph, "ainvoke"), f"graph {name!r} missing .ainvoke"


def test_langgraph_json_crons_empty() -> None:
    lg = json.loads(_LANGGRAPH_JSON.read_text())
    assert lg.get("crons", []) == [], "mangaka crons should be empty"


def test_unknown_nsid_xrpc_404(client: TestClient) -> None:
    r = client.post("/xrpc/com.etzhayyim.mangaka.unknownMethod", json={})
    assert r.status_code == 404
