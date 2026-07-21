"""Tests for logs arch and cohort subcommands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main


# ── logs arch ─────────────────────────────────────────────────────────────────

def test_logs_arch_help():
    runner = CliRunner()
    result = runner.invoke(main, ["logs", "arch", "--help"])
    assert result.exit_code == 0


def test_logs_arch_empty_repo(tmp_path):
    """logs arch on empty git repo produces a valid report."""
    import subprocess
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"],
                   cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(tmp_path), capture_output=True)

    runner = CliRunner()
    result = runner.invoke(main, ["logs", "arch", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "arch log report" in result.output


def test_logs_arch_json_empty_repo(tmp_path):
    """logs arch --json on empty repo emits valid JSON."""
    import subprocess
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"],
                   cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(tmp_path), capture_output=True)

    runner = CliRunner()
    result = runner.invoke(main, ["logs", "arch", "--json", "--root", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "total_events" in data
    assert "by_layer" in data
    assert "events" in data


def test_logs_arch_json_with_commits(tmp_path):
    """logs arch parses commits and classifies layers."""
    import subprocess
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"],
                   cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(tmp_path), capture_output=True)
    # Create a file in a known layer path
    infra_dir = tmp_path / "50-infra" / "vultr"
    infra_dir.mkdir(parents=True)
    f = infra_dir / "values.yaml"
    f.write_text("key: val\n")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "commit", "-m", "test: add infra file"],
                   cwd=str(tmp_path), capture_output=True)

    runner = CliRunner()
    result = runner.invoke(main, ["logs", "arch", "--json", "--root", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_events"] == 1
    assert "infra" in data["by_layer"]


def test_logs_arch_layer_classifier():
    """Layer classification matches repo directory conventions."""
    from etzhayyim.logs import _classify_layer
    cases = [
        ("60-apps/proj/app.ts", "projects"),
        ("50-infra/k8s/values.yaml", "infra"),
        ("40-engine/kotoba/crates/kotoba-kotodama/py/foo.py", "actors"),
        ("90-docs/adr/foo.md", "docs"),
        ("orgs/etzhayyim/com-etzhayyim-svelte-design-system/src/foo.ts", "actors"),
        ("30-graph/schema/foo.sql", "graph"),
        ("00-contracts/lexicons/foo.json", "contracts"),
        ("70-tools/etzhayyim-py/bar.py", "tools"),
        ("CLAUDE.md", "root"),
        ("deps.toml", "root"),
    ]
    for path, expected in cases:
        assert _classify_layer(path) == expected, f"{path} → {_classify_layer(path)} != {expected}"


def test_logs_arch_deploy_state(tmp_path):
    """logs arch includes deploy_state from .deploy-state.json if present."""
    import subprocess
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"],
                   cwd=str(tmp_path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=str(tmp_path), capture_output=True)
    (tmp_path / ".deploy-state.json").write_text(json.dumps({"last_deploy": "2026-05-15"}))

    runner = CliRunner()
    result = runner.invoke(main, ["logs", "arch", "--json", "--root", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["deploy_state"] == {"last_deploy": "2026-05-15"}


# ── cohort subcommands ─────────────────────────────────────────────────────────

def test_cohort_seed_help():
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "seed", "--help"])
    assert result.exit_code == 0


def test_cohort_gen_dry_run():
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "gen",
                                   "--pcf-l1", "finance",
                                   "--role", "analyst",
                                   "--dry-run"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["pcfL1"] == "finance"
    assert data["role"] == "analyst"


def test_cohort_fission_dry_run():
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "fission",
                                   "--did", "did:plc:abc",
                                   "--dry-run"])
    assert result.exit_code == 0
    assert "dry-run" in result.output


def test_cohort_bootstrap_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "bootstrap"])
    assert result.exit_code != 0


def test_cohort_dashboard_not_signed_in(tmp_path):
    auth_file = tmp_path / "auth.json"
    with patch("etzhayyim.cohort._load_auth", return_value={}):
        runner = CliRunner()
        result = runner.invoke(main, ["cohort", "dashboard"])
    assert result.exit_code != 0


def test_cohort_snapshot_saves_file(tmp_path):
    """cohort snapshot saves JSON without network call."""
    out_dir = tmp_path / "snapshots"
    with patch("etzhayyim.cohort._auth_headers", return_value={}), \
         patch("httpx.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "cohorts": [
                {"did": "did:plc:a", "pcfL1": "finance", "role": "analyst",
                 "industry": "banking", "seniority": "mid"},
                {"did": "did:plc:b", "pcfL1": "tech", "role": "engineer",
                 "industry": "saas", "seniority": "senior"},
            ]
        }
        mock_get.return_value = mock_resp
        runner = CliRunner()
        result = runner.invoke(main, ["cohort", "snapshot",
                                       "--out-dir", str(out_dir)])
    assert result.exit_code == 0
    files = list(out_dir.glob("*.json"))
    assert len(files) == 1
    snap = json.loads(files[0].read_text())
    assert snap["total"] == 2


def test_cohort_diff(tmp_path):
    """cohort diff computes total_delta between two snapshots."""
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(json.dumps({"ts": "2026-05-01T00:00:00Z", "total": 10, "aggregate": []}))
    b.write_text(json.dumps({"ts": "2026-05-15T00:00:00Z", "total": 25, "aggregate": []}))
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "diff", str(a), str(b), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_delta"] == 15


def test_cohort_drift_too_few_snapshots(tmp_path):
    """cohort drift emits error with fewer than 2 snapshots."""
    snap_dir = tmp_path / "snaps"
    snap_dir.mkdir()
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "drift", "--dir", str(snap_dir)])
    assert result.exit_code == 0  # graceful, not exception


def test_cohort_coverage_help():
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "coverage", "--help"])
    assert result.exit_code == 0


def test_cohort_gap_help():
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "gap", "--help"])
    assert result.exit_code == 0


def test_cohort_evidence_help():
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "evidence", "--help"])
    assert result.exit_code == 0


def test_cohort_forest_help():
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "forest", "--help"])
    assert result.exit_code == 0


def test_cohort_lineage_help():
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "lineage", "--help"])
    assert result.exit_code == 0
