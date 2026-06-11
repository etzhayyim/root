"""Unit tests for the mokuteki command (pure — no real filesystem scanning)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main
from etzhayyim.mokuteki import (
    MokutekiRank,
    MokutekiComponent,
    MokutekiLayer,
    MokutekiAxis,
    MokutekiReport,
    RANK_LADDER,
    resolve_rank,
    next_rank,
    _weighted_score,
    _scan_app_meta,
    eval_layer_a,
    eval_layer_b_stub,
    eval_layer_c_stub,
    eval_layer_d,
    derive_axes,
    build_mokuteki_report,
)


# ── rank ladder ────────────────────────────────────────────────────────────────

def test_rank_ladder_has_16_entries():
    assert len(RANK_LADDER) == 16


def test_resolve_rank_dan10():
    r = resolve_rank(12000)
    assert r.name == "Dan 10"


def test_resolve_rank_kyu6():
    r = resolve_rank(0)
    assert r.name == "Kyu 6"


def test_resolve_rank_kyu3():
    r = resolve_rank(600)
    assert r.name == "Kyu 3"


def test_resolve_rank_intermediate():
    r = resolve_rank(1200)
    assert r.name == "Kyu 2"


def test_next_rank_from_zero():
    name, pts = next_rank(0)
    assert name == "Kyu 5"
    assert pts == 100


def test_next_rank_already_dan10():
    name, pts = next_rank(12000)
    assert name == ""
    assert pts == 0


def test_next_rank_kyu1():
    name, pts = next_rank(1500)
    assert name == "Dan 1"
    assert pts == 500


# ── data types ─────────────────────────────────────────────────────────────────

def test_mokuteki_rank_to_dict():
    r = MokutekiRank("Dan 5", "#000000", 7000)
    d = r.to_dict()
    assert d["name"] == "Dan 5"
    assert d["min_score"] == 7000


def test_mokuteki_component_to_dict():
    c = MokutekiComponent("Test", score=80.0, weight=0.3, details="info")
    d = c.to_dict()
    assert d["score"] == 80.0
    assert d["weight"] == 0.3


def test_mokuteki_layer_to_dict():
    c = MokutekiComponent("C", score=90.0, weight=1.0)
    l = MokutekiLayer("A", "Structure", "構造", 0.30, 90.0, 1000, components=[c])
    d = l.to_dict()
    assert d["id"] == "A"
    assert len(d["components"]) == 1


# ── weighted score ─────────────────────────────────────────────────────────────

def test_weighted_score_simple():
    comps = [
        MokutekiComponent("a", score=80.0, weight=0.5),
        MokutekiComponent("b", score=60.0, weight=0.5),
    ]
    assert _weighted_score(comps) == pytest.approx(70.0)


def test_weighted_score_all_100():
    comps = [MokutekiComponent("a", score=100.0, weight=1.0)]
    assert _weighted_score(comps) == pytest.approx(100.0)


# ── _scan_app_meta ─────────────────────────────────────────────────────────────

def test_scan_app_meta_empty(tmp_path):
    result = _scan_app_meta(tmp_path)
    assert result == {}


def test_scan_app_meta_single_app(tmp_path):
    app_dir = tmp_path / "60-apps" / "myapp"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "app123",
        "did": "did:plc:abc",
        "displayName": "My App",
        "collections": ["com.etzhayyim.apps.myapp.item"],
        "witImports": [],
        "witExports": ["ai:etzhayyim/myapp-types"],
    }))
    result = _scan_app_meta(tmp_path)
    assert "app123" in result
    m = result["app123"]
    assert m["did"] == "did:plc:abc"
    assert m["display_name"] == "My App"
    assert m["collections"] == ["com.etzhayyim.apps.myapp.item"]
    assert m["wit_exports"] == ["ai:etzhayyim/myapp-types"]


def test_scan_app_meta_no_nanoid_skipped(tmp_path):
    app_dir = tmp_path / "60-apps" / "myapp"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({
        "displayName": "No Nanoid App",
    }))
    result = _scan_app_meta(tmp_path)
    assert result == {}


def test_scan_app_meta_invalid_json_skipped(tmp_path):
    app_dir = tmp_path / "60-apps" / "myapp"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text("{not valid json")
    result = _scan_app_meta(tmp_path)
    assert result == {}


# ── Layer B/C stubs ─────────────────────────────────────────────────────────────

def test_layer_b_stub_score():
    layer = eval_layer_b_stub()
    assert layer.id == "B"
    assert layer.score == 50.0
    assert layer.points == int(50.0 * 0.25 * 120)


def test_layer_c_stub_score():
    layer = eval_layer_c_stub()
    assert layer.id == "C"
    assert layer.score == 50.0
    assert layer.points == int(50.0 * 0.20 * 120)


# ── Layer A ─────────────────────────────────────────────────────────────────────

def test_eval_layer_a_empty_workspace(tmp_path):
    layer = eval_layer_a(tmp_path)
    assert layer.id == "A"
    assert 0.0 <= layer.score <= 100.0
    assert layer.weight == pytest.approx(0.30)


def test_eval_layer_a_with_app(tmp_path):
    app_dir = tmp_path / "60-apps" / "app1"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "app1",
        "did": "did:plc:x",
        "displayName": "App 1",
        "collections": ["com.etzhayyim.apps.app1.item"],
        "witExports": ["ai:etzhayyim/app1-types"],
    }))
    layer = eval_layer_a(tmp_path)
    assert layer.score > 0.0
    assert len(layer.components) == 4


# ── Layer D ─────────────────────────────────────────────────────────────────────

def test_eval_layer_d_empty_workspace(tmp_path):
    layer = eval_layer_d(tmp_path)
    assert layer.id == "D"
    assert layer.score == pytest.approx(0.0)  # no apps → 0% (nothing attested)


def test_eval_layer_d_with_attested_app(tmp_path):
    app_dir = tmp_path / "60-apps" / "app1"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "app1",
        "did": "did:plc:x",
        "displayName": "App 1",
        "collections": ["com.etzhayyim.apps.app1.item"],
        "witExports": ["ai:etzhayyim/app1-types"],
    }))
    (tmp_path / "CLAUDE.md").write_text("# Policy")
    layer = eval_layer_d(tmp_path)
    assert layer.score > 0.0
    assert any(c.name.startswith("Attestation") for c in layer.components)


# ── derive_axes ────────────────────────────────────────────────────────────────

def test_derive_axes_returns_5():
    a = MokutekiLayer("A", "Structure",     "構造",   0.30, 80.0, 1000)
    b = MokutekiLayer("B", "Uncertainty",   "不確実性", 0.25, 50.0,  500)
    c = MokutekiLayer("C", "Control",       "制御",   0.20, 50.0,  400)
    d = MokutekiLayer("D", "Implementation","実装",   0.25, 70.0,  700)
    axes = derive_axes(a, b, c, d)
    assert len(axes) == 5


def test_derive_axes_engagement():
    a = MokutekiLayer("A", "Structure",     "構造",   0.30, 80.0, 1000)
    b = MokutekiLayer("B", "Uncertainty",   "不確実性", 0.25, 50.0,  500)
    c = MokutekiLayer("C", "Control",       "制御",   0.20, 50.0,  400)
    d = MokutekiLayer("D", "Implementation","実装",   0.25, 60.0,  600)
    axes = derive_axes(a, b, c, d)
    engagement = next(ax for ax in axes if "Engagement" in ax.name)
    assert engagement.score == pytest.approx(80.0 * 0.5 + 60.0 * 0.5)


def test_derive_axes_scores_bounded():
    a = MokutekiLayer("A", "Structure",     "構造",   0.30, 100.0, 1000)
    b = MokutekiLayer("B", "Uncertainty",   "不確実性", 0.25, 100.0,  500)
    c = MokutekiLayer("C", "Control",       "制御",   0.20, 100.0,  400)
    d = MokutekiLayer("D", "Implementation","実装",   0.25, 100.0,  700)
    axes = derive_axes(a, b, c, d)
    for ax in axes:
        assert 0.0 <= ax.score <= 100.0


# ── build_mokuteki_report ──────────────────────────────────────────────────────

def test_build_mokuteki_report_structure(tmp_path):
    report = build_mokuteki_report(tmp_path)
    assert len(report.layers) == 4
    assert len(report.axes) == 5
    assert isinstance(report.total_score, int)
    assert report.max_score == 12000
    assert isinstance(report.rank, MokutekiRank)
    assert isinstance(report.diagnosis, list)


def test_build_mokuteki_report_score_bounded(tmp_path):
    report = build_mokuteki_report(tmp_path)
    assert 0 <= report.total_score <= 12000


def test_build_mokuteki_report_to_dict(tmp_path):
    report = build_mokuteki_report(tmp_path)
    d = report.to_dict()
    assert "layers" in d
    assert "axes" in d
    assert "total_score" in d
    assert "rank" in d
    assert "diagnosis" in d


def test_build_mokuteki_report_has_generated_at(tmp_path):
    report = build_mokuteki_report(tmp_path)
    assert "T" in report.generated_at


# ── CLI integration ────────────────────────────────────────────────────────────

def test_cli_mokuteki_json(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["mokuteki", "--json",
                                  "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "total_score" in data
    assert "rank" in data
    assert "layers" in data
    assert len(data["layers"]) == 4


def test_cli_mokuteki_text(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["mokuteki",
                                  "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "mokuteki" in result.output
    assert "RANK:" in result.output


def test_cli_mokuteki_kashika_html(tmp_path):
    out_file = tmp_path / "out.html"
    runner = CliRunner()
    result = runner.invoke(main, [
        "mokuteki", "kashika",
        "--workspace-dir", str(tmp_path),
        "--format", "html",
        "--output", str(out_file),
        "--no-open",
    ])
    assert result.exit_code == 0, result.output
    assert out_file.exists()
    content = out_file.read_text()
    assert "Mokuteki" in content
    assert "DATA" in content


def test_cli_mokuteki_kashika_json(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, [
        "mokuteki", "kashika",
        "--workspace-dir", str(tmp_path),
        "--format", "json",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "total_score" in data
    assert "rank" in data


def test_cli_mokuteki_kashika_dot(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, [
        "mokuteki", "kashika",
        "--workspace-dir", str(tmp_path),
        "--format", "dot",
    ])
    assert result.exit_code == 0, result.output
    assert "digraph" in result.output


def test_cli_mokuteki_history_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, [
        "mokuteki", "history",
        "--workspace-dir", str(tmp_path),
        "--data-dir", str(tmp_path / "data"),
    ])
    assert result.exit_code == 0, result.output
    assert "no snapshots" in result.output


def test_cli_mokuteki_history_json_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, [
        "mokuteki", "history",
        "--workspace-dir", str(tmp_path),
        "--data-dir", str(tmp_path / "data"),
        "--json",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["total"] == 0
    assert data["snapshots"] == []


def test_cli_mokuteki_store_calls_duckdb(tmp_path):
    from unittest.mock import patch, MagicMock
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    with patch("etzhayyim.mokuteki.subprocess.run", return_value=mock_result) as mock_run:
        runner = CliRunner()
        result = runner.invoke(main, [
            "mokuteki", "store",
            "--workspace-dir", str(tmp_path),
            "--data-dir", str(tmp_path / "data"),
        ])
    assert result.exit_code == 0, result.output
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "duckdb"
    catalog = (tmp_path / "data" / "catalog.json")
    assert catalog.exists()
    cat = json.loads(catalog.read_text())
    assert len(cat["snapshots"]) == 1


def test_cli_mokuteki_query_calls_duckdb(tmp_path):
    from unittest.mock import patch, MagicMock
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "generated_at\ttotal_score\n2026-01-01\t100\n"
    mock_result.stderr = ""
    with patch("etzhayyim.mokuteki.subprocess.run", return_value=mock_result) as mock_run:
        runner = CliRunner()
        result = runner.invoke(main, [
            "mokuteki", "query",
            "--workspace-dir", str(tmp_path),
            "--data-dir", str(tmp_path / "data"),
        ])
    assert result.exit_code == 0, result.output
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "duckdb"
