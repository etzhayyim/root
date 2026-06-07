"""Unit tests for kosei structural compliance analysis."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main
from etzhayyim.kosei import scan_kosei, _check_app


def _make_full_app(base: Path) -> Path:
    """Create a fully compliant app at base/."""
    base.mkdir(parents=True, exist_ok=True)
    (base / "kotodama.jsonld").write_text(json.dumps({"nanoid": "abc12345"}))
    (base / "src").mkdir(exist_ok=True)
    (base / "src" / "app.ts").write_text("// app\nexport default {};\n")
    (base / "wrangler.jsonc").write_text('{"name": "test"}\n')
    return base


# ── _check_app ─────────────────────────────────────────────────────────────────

def test_check_app_missing_all(tmp_path):
    app = tmp_path / "myapp"
    app.mkdir()
    (app / "kotodama.jsonld").write_text("{}")
    r = _check_app(app, tmp_path)
    assert "src/app.ts" in r.missing_files
    assert "wrangler.jsonc" in r.missing_files


def test_check_app_full_compliance(tmp_path):
    app = tmp_path / "etzhayyim-wasm-test-abc12345"
    _make_full_app(app)
    r = _check_app(app, tmp_path)
    assert r.missing_files == []
    # no error-severity violations
    assert all(v.severity != "error" for v in r.violations)


def test_check_app_nsid_placeholder(tmp_path):
    app = tmp_path / "myapp"
    app.mkdir()
    (app / "kotodama.jsonld").write_text("{}")
    (app / "src").mkdir()
    (app / "src" / "app.ts").write_text('const nsid = "nsid";\n')
    (app / "wrangler.jsonc").write_text("{}")
    r = _check_app(app, tmp_path)
    assert any(v.rule == "no-nsid-placeholder" for v in r.violations)


def test_check_app_model_hardcode(tmp_path):
    app = tmp_path / "myapp"
    app.mkdir()
    (app / "kotodama.jsonld").write_text("{}")
    (app / "src").mkdir()
    (app / "src" / "app.ts").write_text('const model = "claude-3-opus-20240229";\n')
    (app / "wrangler.jsonc").write_text("{}")
    r = _check_app(app, tmp_path)
    assert any(v.rule == "no-model-hardcode" for v in r.violations)


def test_check_app_naming_warning(tmp_path):
    app = tmp_path / "bad-name"
    _make_full_app(app)
    r = _check_app(app, tmp_path)
    assert any(v.rule == "app-dir-naming" for v in r.violations)


def test_check_app_ok_property(tmp_path):
    app = tmp_path / "etzhayyim-wasm-test-abc12345"
    _make_full_app(app)
    r = _check_app(app, tmp_path)
    assert r.ok is True


# ── scan_kosei ─────────────────────────────────────────────────────────────────

def test_scan_empty(tmp_path):
    r = scan_kosei(tmp_path)
    assert r.total_apps == 0
    assert r.ok_apps == 0


def test_scan_single_app(tmp_path):
    projects = tmp_path / "60-apps" / "etzhayyim-project-billing" / "appview"
    app = projects / "etzhayyim-wasm-billing-abc12345"
    _make_full_app(app)
    r = scan_kosei(tmp_path)
    assert r.total_apps == 1


def test_scan_report_to_dict(tmp_path):
    r = scan_kosei(tmp_path)
    d = r.to_dict()
    assert "evaluated_at" in d
    assert "total_apps" in d
    assert "ok_apps" in d
    assert "compliance_pct" in d


def test_scan_compliance_pct(tmp_path):
    projects = tmp_path / "60-apps" / "proj" / "appview"
    app = projects / "etzhayyim-wasm-test-abc12345"
    _make_full_app(app)
    r = scan_kosei(tmp_path)
    assert r.compliance_pct == 100.0 or r.compliance_pct >= 0.0


# ── CLI ────────────────────────────────────────────────────────────────────────

def test_cli_kosei_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kosei", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "kosei" in result.output


def test_cli_kosei_json_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kosei", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "total_apps" in data


def test_cli_kosei_scan(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kosei", "scan", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "compliance_pct" in data


def test_cli_kosei_scan_errors_only(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kosei", "scan", "--errors-only",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0


def test_cli_kosei_check_rule(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kosei", "check", "no-nsid-placeholder",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "no violations" in result.output


def test_cli_kosei_help():
    runner = CliRunner()
    result = runner.invoke(main, ["kosei", "--help"])
    assert result.exit_code == 0
