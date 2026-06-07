"""Unit tests for coverage commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main
from etzhayyim.coverage import _check_actor_completeness, _scan_actors, _heal_one, _run_heal, _build_heal_prompt


# ── _check_actor_completeness ──────────────────────────────────────────────────

def test_check_completeness_empty():
    c = _check_actor_completeness({})
    assert c["nanoid"] is False
    assert c["did"] is False


def test_check_completeness_full():
    data = {
        "nanoid": "abc123",
        "did": "did:web:x",
        "name": "billing",
        "performerType": "actor",
        "uiType": "wasm",
        "runtimeType": "ts-native",
    }
    c = _check_actor_completeness(data)
    assert c["nanoid"] is True
    assert c["did"] is True
    assert c["name"] is True
    assert c["performerType"] is True


# ── _scan_actors ───────────────────────────────────────────────────────────────

def test_scan_actors_empty(tmp_path):
    assert _scan_actors(tmp_path) == []


def test_scan_actors_single(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "appview" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "abc123",
        "did": "did:web:example.com",
        "name": "billing",
        "performerType": "actor",
    }))
    actors = _scan_actors(tmp_path)
    assert len(actors) == 1
    assert actors[0]["nanoid"] == "abc123"
    assert actors[0]["missing"] == []  # all required fields present


def test_scan_actors_missing_required(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "appview" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({"nanoid": "abc"}))
    actors = _scan_actors(tmp_path)
    assert len(actors) == 1
    assert "did" in actors[0]["missing"]
    assert "name" in actors[0]["missing"]


def test_scan_actors_score_range(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "appview" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "abc",
        "did": "did:web:x",
        "name": "x",
        "performerType": "actor",
    }))
    actors = _scan_actors(tmp_path)
    assert 0 <= actors[0]["score"] <= 100


# ── CLI coverage domain ────────────────────────────────────────────────────────

def test_cli_coverage_domain_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "domain", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_apps"] == 0


def test_cli_coverage_domain_text_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "domain", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "coverage domain" in result.output


def test_cli_coverage_domain_with_app(tmp_path):
    app_dir = tmp_path / "60-apps" / "etzhayyim-project-billing" / "appview" / "app-abc"
    (app_dir / "src").mkdir(parents=True)
    (app_dir / "src" / "app.ts").write_text(
        'MATCH (n:Invoice) RETURN n\ncom.etzhayyim.apps.billing.invoice\nfunction cmdPay() {}\n'
    )
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "domain", "--json", "--apps",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_apps"] == 1


def test_cli_coverage_domain_grade_filter(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "domain", "--json", "--grade", "S",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0


# ── CLI coverage actors ────────────────────────────────────────────────────────

def test_cli_coverage_actors_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "actors", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total"] == 0


def test_cli_coverage_actors_text(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "actors", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "coverage actors" in result.output


def test_cli_coverage_actors_with_actors(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "appview" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "abc123",
        "did": "did:web:x",
        "name": "x",
        "performerType": "actor",
    }))
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "actors", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total"] == 1


def test_cli_coverage_actors_missing_only(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "appview" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({"nanoid": "abc"}))
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "actors", "--json", "--missing-only",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    # actor is missing required fields so it should appear
    assert data["total"] >= 1


# ── CLI coverage test ──────────────────────────────────────────────────────────

def test_cli_coverage_test_no_suites(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "test", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "no test suites" in result.output


def test_cli_coverage_test_json_no_suites(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "test", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "no test suites" in result.output


def test_cli_coverage_test_runs_pytest(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_pass(): assert True\n")

    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "test", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert any(s["suite"] == "pytest" for s in data["suites"])


# ── heal unit tests ────────────────────────────────────────────────────────────

def test_build_heal_prompt_mentions_missing():
    actor = {"nanoid": "abc123", "name": "billing", "path": "60-apps/proj/app/kotodama.jsonld",
              "missing": ["did", "performerType"]}
    prompt = _build_heal_prompt(actor)
    assert "did" in prompt
    assert "performerType" in prompt
    assert "abc123" in prompt


def test_heal_one_no_missing(tmp_path):
    actor = {"nanoid": "abc", "name": "billing", "path": "kotodama.jsonld", "missing": []}
    result = _heal_one(actor, tmp_path, lambda p: '{"x": 1}', dry_run=True)
    assert result["fixed_fields"] == []
    assert result["error"] == ""


def test_heal_one_dry_run_no_write(tmp_path):
    jsonld_path = tmp_path / "kotodama.jsonld"
    jsonld_path.write_text(json.dumps({"nanoid": "abc123", "name": "billing"}))
    actor = {"nanoid": "abc123", "name": "billing",
             "path": "kotodama.jsonld", "missing": ["performerType"]}

    def mock_llm(prompt: str) -> str:
        return '{"performerType": "actor"}'

    result = _heal_one(actor, tmp_path, mock_llm, dry_run=True)
    assert "performerType" in result["fixed_fields"]
    # dry-run: file not modified
    data = json.loads(jsonld_path.read_text())
    assert "performerType" not in data


def test_heal_one_writes_back(tmp_path):
    jsonld_path = tmp_path / "kotodama.jsonld"
    jsonld_path.write_text(json.dumps({"nanoid": "abc123", "name": "billing"}))
    actor = {"nanoid": "abc123", "name": "billing",
             "path": "kotodama.jsonld", "missing": ["performerType"]}

    def mock_llm(prompt: str) -> str:
        return '{"performerType": "actor"}'

    result = _heal_one(actor, tmp_path, mock_llm, dry_run=False)
    assert "performerType" in result["fixed_fields"]
    data = json.loads(jsonld_path.read_text())
    assert data["performerType"] == "actor"


def test_heal_one_llm_error(tmp_path):
    actor = {"nanoid": "abc", "name": "x", "path": "x.jsonld", "missing": ["did"]}

    def bad_llm(prompt: str) -> str:
        raise RuntimeError("network error")

    result = _heal_one(actor, tmp_path, bad_llm, dry_run=True)
    assert result["error"] != ""
    assert result["fixed_fields"] == []


def test_heal_one_no_json_in_response(tmp_path):
    actor = {"nanoid": "abc", "name": "x", "path": "x.jsonld", "missing": ["did"]}
    result = _heal_one(actor, tmp_path, lambda p: "no JSON here", dry_run=True)
    assert "no JSON" in result["error"]


def test_run_heal_concurrent(tmp_path):
    for i in range(3):
        p = tmp_path / f"actor{i}.jsonld"
        p.write_text(json.dumps({"nanoid": f"a{i}", "name": f"actor{i}"}))

    actors = [
        {"nanoid": f"a{i}", "name": f"actor{i}",
         "path": f"actor{i}.jsonld", "missing": ["performerType"]}
        for i in range(3)
    ]

    def mock_llm(prompt: str) -> str:
        return '{"performerType": "worker"}'

    results = _run_heal(actors, tmp_path, mock_llm, dry_run=True, concurrency=2)
    assert len(results) == 3
    assert all("performerType" in r["fixed_fields"] for r in results)


# ── CLI coverage heal ──────────────────────────────────────────────────────────

def test_cli_coverage_heal_no_missing(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "abc123", "did": "did:plc:x", "name": "billing", "performerType": "actor",
    }))
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "heal", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "no actors" in result.output


def test_cli_coverage_heal_dry_run(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "app"
    app_dir.mkdir(parents=True)
    jsonld = app_dir / "kotodama.jsonld"
    jsonld.write_text(json.dumps({"nanoid": "abc123", "name": "billing"}))

    runner = CliRunner()
    with patch("etzhayyim.coverage._call_llm_sync", return_value='{"performerType": "actor", "did": "did:plc:x"}'):
        result = runner.invoke(main, [
            "coverage", "heal", "--dry-run", "--workspace-dir", str(tmp_path),
        ])
    assert result.exit_code == 0
    assert "heal" in result.output
    # File not modified in dry-run
    data = json.loads(jsonld.read_text())
    assert "performerType" not in data


def test_cli_coverage_heal_json_output(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({"nanoid": "abc123", "name": "billing"}))

    runner = CliRunner()
    with patch("etzhayyim.coverage._call_llm_sync", return_value='{"performerType": "actor", "did": "did:plc:x"}'):
        result = runner.invoke(main, [
            "coverage", "heal", "--dry-run", "--json", "--workspace-dir", str(tmp_path),
        ])
    assert result.exit_code == 0
    # Strip any progress lines (written to stderr, mixed in by CliRunner) before the JSON
    json_part = result.output[result.output.index("{"):]
    data = json.loads(json_part)
    assert "healed" in data
    assert data["dry_run"] is True
    assert isinstance(data["results"], list)


# ── CLI help ───────────────────────────────────────────────────────────────────

def test_cli_coverage_help():
    runner = CliRunner()
    result = runner.invoke(main, ["coverage", "--help"])
    assert result.exit_code == 0
    assert "heal" in result.output
