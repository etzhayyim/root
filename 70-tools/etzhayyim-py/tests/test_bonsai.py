"""Unit tests for bonsai growth/prune analysis."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main
from etzhayyim.bonsai import scan_workspace, PRUNE_TIERS, BonsaiReport


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# ── scan_workspace ─────────────────────────────────────────────────────────────

def test_scan_empty(tmp_path):
    r = scan_workspace(tmp_path)
    assert r.total_files == 0
    assert r.total_lines == 0
    assert r.prune_candidates == []
    assert r.growth_score == 100


def test_scan_single_ts_file(tmp_path):
    _write(tmp_path / "src" / "app.ts", "const x = 1;\nconst y = 2;\n")
    r = scan_workspace(tmp_path)
    assert r.total_files >= 1
    assert r.total_lines >= 2


def test_scan_detects_todo(tmp_path):
    _write(tmp_path / "src" / "app.ts", "// TODO: fix this\nconst x = 1;\n")
    r = scan_workspace(tmp_path, prune_threshold=1)
    assert any(n.prune_score > 0 for n in r.prune_candidates)


def test_scan_empty_file_flagged(tmp_path):
    _write(tmp_path / "src" / "empty.ts", "")
    r = scan_workspace(tmp_path, prune_threshold=1)
    assert any("empty" in " ".join(n.signals) for n in r.prune_candidates)


def test_scan_skip_node_modules(tmp_path):
    _write(tmp_path / "node_modules" / "pkg" / "index.ts",
           "// TODO: lots of todos\n" * 10)
    r = scan_workspace(tmp_path)
    assert r.total_files == 0


def test_scan_growth_score_clean(tmp_path):
    _write(tmp_path / "src" / "app.ts", "const x = 1;\n")
    r = scan_workspace(tmp_path)
    assert r.growth_score == 100


def test_scan_report_to_dict(tmp_path):
    r = scan_workspace(tmp_path)
    d = r.to_dict()
    assert "evaluated_at" in d
    assert "total_files" in d
    assert "tier_counts" in d
    assert "prune_candidates" in d
    assert "growth_score" in d


def test_scan_legacy_named_file(tmp_path):
    _write(tmp_path / "src" / "old_payments.ts", "const x = 1;\n")
    r = scan_workspace(tmp_path, prune_threshold=1)
    assert any("legacy name" in " ".join(n.signals) for n in r.prune_candidates)


def test_scan_tier_counts_has_all_tiers(tmp_path):
    r = scan_workspace(tmp_path)
    for tier in PRUNE_TIERS:
        assert tier in r.tier_counts


# ── CLI ────────────────────────────────────────────────────────────────────────

def test_cli_bonsai_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["bonsai", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "bonsai" in result.output


def test_cli_bonsai_json_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["bonsai", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "total_files" in data
    assert "growth_score" in data


def test_cli_bonsai_scan(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["bonsai", "scan", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "total_files" in data


def test_cli_bonsai_prune_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["bonsai", "prune", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "no prune candidates" in result.output


def test_cli_bonsai_prune_with_todo(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "x.ts").write_text("// TODO: fix\n// TODO: also fix\n" * 5)
    runner = CliRunner()
    result = runner.invoke(main, ["bonsai", "prune", "--threshold", "1",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0


def test_cli_bonsai_status_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["bonsai", "status", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "health" in data
    assert "growth_score" in data
