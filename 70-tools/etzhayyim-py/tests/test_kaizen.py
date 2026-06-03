"""Unit tests for kaizen domain coverage analysis."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main
from etzhayyim.kaizen import (
    DomainAppReport,
    KaizenGap,
    KaizenReport,
    _score_app,
    _check_governance,
    collect_and_score_domain_apps,
    build_kaizen_report,
)


# ── _score_app ─────────────────────────────────────────────────────────────────

def test_score_app_empty_returns_d():
    r = _score_app("", "", "", "empty")
    assert r.grade == "D"
    assert r.domain_score == 0


def test_score_app_detects_sql_labels():
    content = 'MATCH (n:Invoice) RETURN n; MATCH (n:LineItem) RETURN n'
    r = _score_app(content, "", "", "myapp")
    assert "Invoice" in r.sql_labels
    assert "LineItem" in r.sql_labels
    assert r.domain_score >= 20


def test_score_app_ignores_generic_labels():
    content = 'MATCH (n:Record) RETURN n'
    r = _score_app(content, "", "", "myapp")
    assert "Record" not in r.sql_labels


def test_score_app_detects_collection_kinds():
    content = 'com.etzhayyim.apps.myapp.invoice'
    r = _score_app(content, "", "", "myapp")
    assert "invoice" in r.collection_kinds


def test_score_app_ignores_generic_kinds():
    content = 'com.etzhayyim.apps.myapp.record'
    r = _score_app(content, "", "", "myapp")
    assert "record" not in r.collection_kinds


def test_score_app_detects_custom_commands():
    content = 'function cmdProcessPayment() {} function cmdGenerateInvoice() {}'
    r = _score_app(content, "", "", "myapp")
    assert len(r.custom_commands) >= 1


def test_score_app_grade_s_high_score():
    content = '\n'.join([
        'MATCH (n:Invoice) RETURN n',
        'MATCH (n:LineItem) RETURN n',
        'MATCH (n:Payment) RETURN n',
        'com.etzhayyim.apps.myapp.invoice',
        'com.etzhayyim.apps.myapp.payment',
        'function cmdProcessPayment() {}',
        'function cmdGenerateInvoice() {}',
        'function cmdVoidInvoice() {}',
        'if (amount > 0) { process(); }',
        'if (status === "paid") { notify(); }',
        'if (dueDate < now) { markOverdue(); }',
        'interface InvoiceRecord { id: string; amount: number; }',
        'const PAYMENT_METHODS = ["credit", "bank"];',
    ])
    r = _score_app(content, "abc123", "billing", "myapp")
    assert r.domain_score >= 50


def test_score_app_penalty_for_template_only():
    # No custom labels, kinds, or commands → penalty applies
    content = 'function cmdList_entity() {} function cmdGet_entity() {}'
    r = _score_app(content, "", "", "myapp")
    # Template-only apps get penalized
    assert "graph_labels" in r.missing
    assert "collection_kinds" in r.missing


def test_score_app_detects_did_paths():
    # DID paths + a label to avoid template-only penalty
    content = 'comAtprotoIdentityCreate("lawyer")\ncomAtprotoIdentityCreate("assistant")\nMATCH (n:Legal) RETURN n'
    r = _score_app(content, "", "", "myapp")
    assert "lawyer" in r.did_paths
    assert "assistant" in r.did_paths
    assert r.domain_score >= 5


def test_score_app_detects_business_rules():
    content = 'if (a > b) { x(); }\nif (c < d) { y(); }'
    r = _score_app(content, "", "", "myapp")
    assert r.business_rules >= 2


def test_score_app_score_capped_at_100():
    # Very feature-rich app should not exceed 100
    content = '\n'.join([
        'MATCH (n:A) RETURN n', 'MATCH (n:B) RETURN n', 'MATCH (n:C) RETURN n',
        'MATCH (n:D) RETURN n', 'MATCH (n:E) RETURN n',
        'com.etzhayyim.apps.myapp.a', 'com.etzhayyim.apps.myapp.b',
        'function cmdA() {}', 'function cmdB() {}', 'function cmdC() {}',
        'if (x) { a(); }', 'if (y) { b(); }', 'if (z) { c(); }',
        'interface IFoo { id: string; }', 'interface IBar { val: number; }',
        'comAtprotoIdentityCreate("type1")',
        'comAtprotoIdentityCreate("type2")',
        'WriterEntity',
    ])
    r = _score_app(content, "", "", "rich")
    assert r.domain_score <= 100


# ── _check_governance ──────────────────────────────────────────────────────────

def test_check_governance_no_file(tmp_path):
    nanoid, gov_unique = _check_governance(tmp_path / "missing.jsonld")
    assert nanoid == ""
    assert gov_unique is False


def test_check_governance_default_gov(tmp_path):
    cfg = {"nanoid": "abc123", "governance": {"raci": "responsible", "classification": "internal", "complianceFrameworks": []}}
    (tmp_path / "magatama.jsonld").write_text(json.dumps(cfg))
    nanoid, gov_unique = _check_governance(tmp_path / "magatama.jsonld")
    assert nanoid == "abc123"
    # default governance is not unique


def test_check_governance_unique_gov(tmp_path):
    cfg = {"nanoid": "abc123", "governance": {"roles": [{"role": "operator", "did": "did:plc:xxx"}]}}
    (tmp_path / "magatama.jsonld").write_text(json.dumps(cfg))
    nanoid, gov_unique = _check_governance(tmp_path / "magatama.jsonld")
    assert nanoid == "abc123"
    assert gov_unique is True


# ── collect_and_score_domain_apps ──────────────────────────────────────────────

def test_collect_empty_workspace(tmp_path):
    apps = collect_and_score_domain_apps(tmp_path)
    assert apps == []


def test_collect_single_app(tmp_path):
    project_dir = tmp_path / "60-apps" / "etzhayyim-project-billing"
    app_dir = project_dir / "appview" / "etzhayyim-wasm-billing-abc12345"
    (app_dir / "src").mkdir(parents=True)
    (app_dir / "src" / "app.ts").write_text(
        'MATCH (n:Invoice) RETURN n\ncom.etzhayyim.apps.billing.invoice\nfunction cmdProcessPayment() {}\n'
    )
    (app_dir / "magatama.jsonld").write_text(json.dumps({
        "nanoid": "abc12345",
        "governance": {"roles": [{"role": "operator", "did": "did:web:x"}]}
    }))
    apps = collect_and_score_domain_apps(tmp_path)
    assert len(apps) == 1
    assert apps[0].nanoid == "abc12345"
    assert "billing" in apps[0].project


def test_collect_infers_project_from_dir(tmp_path):
    project_dir = tmp_path / "60-apps" / "etzhayyim-project-invoicing" / "src"
    project_dir.mkdir(parents=True)
    (project_dir / "app.ts").write_text('// empty\n')
    apps = collect_and_score_domain_apps(tmp_path)
    assert any(a.project == "invoicing" for a in apps)


# ── build_kaizen_report ────────────────────────────────────────────────────────

def test_build_kaizen_report_empty():
    r = build_kaizen_report([])
    assert r.total_apps == 0
    assert r.avg_domain_score == 0.0
    assert r.gaps == []


def test_build_kaizen_report_grades():
    apps = [
        DomainAppReport("p", "a1", "", 80, "S", 10),
        DomainAppReport("p", "a2", "", 40, "B", 10, missing=["graph_labels"]),
        DomainAppReport("p", "a3", "", 20, "D", 10, missing=["graph_labels", "collection_kinds"]),
    ]
    r = build_kaizen_report(apps)
    assert r.grades["S"] == 1
    assert r.grades["B"] == 1
    assert r.grades["D"] == 1
    assert r.total_apps == 3
    assert any(g.feature == "graph_labels" for g in r.gaps)


def test_build_kaizen_report_to_dict():
    r = build_kaizen_report([DomainAppReport("p", "a", "", 75, "S", 10)])
    d = r.to_dict()
    assert "evaluated_at" in d
    assert "total_apps" in d
    assert "avg_domain_score" in d
    assert "grades" in d
    assert "gaps" in d


# ── CLI integration ────────────────────────────────────────────────────────────

def test_cli_kaizen_json(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kaizen", "--json",
                                  "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "total_apps" in data
    assert data["total_apps"] == 0


def test_cli_kaizen_text(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kaizen",
                                  "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "kaizen" in result.output


def test_cli_kaizen_fix_exits_nonzero_when_no_tools(tmp_path):
    with patch("shutil.which", return_value=None):
        runner = CliRunner()
        result = runner.invoke(main, ["kaizen", "--fix",
                                      "--workspace-dir", str(tmp_path)])
    assert result.exit_code != 0


def test_cli_kaizen_with_real_app(tmp_path):
    project_dir = tmp_path / "60-apps" / "etzhayyim-project-billing"
    app_dir = project_dir / "src"
    app_dir.mkdir(parents=True)
    (app_dir / "app.ts").write_text(
        'MATCH (n:Invoice)\ncom.etzhayyim.apps.billing.invoice\nfunction cmdPayBill() {}\nif (x > 0) { pay(); }\n'
    )
    runner = CliRunner()
    result = runner.invoke(main, ["kaizen", "--json", "--apps",
                                  "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_apps"] == 1
    assert len(data["apps"]) == 1
    assert data["apps"][0]["domain_score"] > 0


def test_cli_kaizen_filter_grade(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kaizen", "--json", "--grade", "S",
                                  "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["total_apps"] == 0  # empty workspace


def test_cli_kaizen_logs_exits_nonzero_no_auth(tmp_path):
    """kaizen logs without auth token must exit non-zero."""
    with patch("etzhayyim.kaizen._resolve_cf_token", return_value=""), \
         patch("etzhayyim.kaizen._resolve_etzhayyim_token", return_value=""):
        runner = CliRunner()
        result = runner.invoke(main, ["kaizen", "logs"])
    assert result.exit_code != 0


def test_kaizen_logs_percentile_empty():
    from etzhayyim.kaizen import _percentile
    assert _percentile([], 0.99) == 0.0


def test_kaizen_logs_percentile_single():
    from etzhayyim.kaizen import _percentile
    assert _percentile([100], 0.99) == 100.0


def test_kaizen_logs_percentile_multiple():
    from etzhayyim.kaizen import _percentile
    samples = list(range(1, 101))  # 1..100
    p50 = _percentile(samples, 0.50)
    p99 = _percentile(samples, 0.99)
    assert 49 <= p50 <= 51
    assert p99 >= 99


def test_kaizen_logs_aggregate_events():
    from etzhayyim.kaizen import _aggregate_events
    events = [
        {"method": "com.etzhayyim.foo.bar", "status": 200, "ms": 100},
        {"method": "com.etzhayyim.foo.bar", "status": 500, "ms": 2000},
        {"method": "com.etzhayyim.baz.qux", "status": 200, "ms": 50},
    ]
    stats = _aggregate_events(events)
    assert stats["com.etzhayyim.foo.bar"]["count"] == 2
    assert stats["com.etzhayyim.foo.bar"]["errors"] == 1
    assert stats["com.etzhayyim.baz.qux"]["count"] == 1
    assert stats["com.etzhayyim.baz.qux"]["errors"] == 0


def test_kaizen_logs_build_findings_slow():
    from etzhayyim.kaizen import _build_findings
    events = [
        {"method": "com.etzhayyim.slow.query", "status": 200, "ms": 1200},
        {"method": "com.etzhayyim.slow.query", "status": 200, "ms": 1500},
        {"method": "com.etzhayyim.fast.query", "status": 200, "ms": 50},
    ]
    findings = _build_findings(events, {}, top=5, p99_threshold=500,
                               err_rate_threshold=1.0, show_events=10)
    assert findings["total_requests"] == 3
    slow = findings["slow_queries"]
    assert any(q["method"] == "com.etzhayyim.slow.query" for q in slow)
    assert not any(q["method"] == "com.etzhayyim.fast.query" for q in slow)


def test_kaizen_logs_build_findings_errors():
    from etzhayyim.kaizen import _build_findings
    events = [
        {"method": "com.etzhayyim.broken", "status": 500, "ms": 100},
        {"method": "com.etzhayyim.broken", "status": 500, "ms": 100},
        {"method": "com.etzhayyim.ok", "status": 200, "ms": 100},
    ]
    findings = _build_findings(events, {}, top=5, p99_threshold=500,
                               err_rate_threshold=1.0, show_events=10)
    err_q = findings["error_queries"]
    assert any(q["method"] == "com.etzhayyim.broken" for q in err_q)
    broken = next(q for q in err_q if q["method"] == "com.etzhayyim.broken")
    assert broken["errRate"] == 100.0
    assert len(findings["recent_error_events"]) == 2


def test_kaizen_logs_with_mocked_ocel():
    """kaizen logs end-to-end with mocked OCEL data."""
    from etzhayyim.kaizen import _load_ocel
    mock_data = {
        "events": [
            {"method": "com.etzhayyim.apps.foo.bar", "status": 200, "ms": 120, "ts": "2026-05-15T00:00:00Z"},
            {"method": "com.etzhayyim.apps.foo.bar", "status": 500, "ms": 8000, "ts": "2026-05-15T00:00:01Z"},
            {"method": "com.etzhayyim.apps.baz.qux", "status": 200, "ms": 40, "ts": "2026-05-15T00:00:02Z"},
        ],
        "aggregates": {},
    }
    with patch("etzhayyim.kaizen._load_ocel", return_value=(mock_data, "test")):
        runner = CliRunner()
        from etzhayyim.cli import main
        result = runner.invoke(main, ["kaizen", "logs"])
    assert result.exit_code == 0
    assert "kaizen logs" in result.output


def test_kaizen_logs_json_with_mocked_ocel():
    """kaizen logs --json produces valid JSON."""
    mock_data = {
        "events": [
            {"method": "com.etzhayyim.apps.foo.bar", "status": 200, "ms": 600, "ts": "2026-05-15T00:00:00Z"},
        ],
        "aggregates": {},
    }
    with patch("etzhayyim.kaizen._load_ocel", return_value=(mock_data, "test")):
        runner = CliRunner()
        from etzhayyim.cli import main
        result = runner.invoke(main, ["kaizen", "logs", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "analyzed_at" in data
    assert "slow_queries" in data
    assert "error_queries" in data
    assert data["event_count"] == 1


def test_kaizen_logs_severity_classification():
    from etzhayyim.kaizen import _build_findings
    # critical: errRate >= 10
    events = [{"method": "m", "status": 500, "ms": 100}] * 10
    f = _build_findings(events, {}, 5, 500, 1.0, 10)
    m = next((q for q in f["error_queries"] if q["method"] == "m"), None)
    assert m is not None
    assert m["severity"] == "critical"


def test_cli_actors_shinka_help():
    runner = CliRunner()
    result = runner.invoke(main, ["actors", "shinka", "--help"])
    assert result.exit_code == 0
    assert "shinka" in result.output.lower() or "murakumo" in result.output.lower()


# ── kaizen --fix with mocked agent ────────────────────────────────────────────

def test_cli_kaizen_fix_uses_claude_when_available(tmp_path):
    mock_result = MagicMock()
    mock_result.returncode = 0

    with (
        patch("shutil.which", side_effect=lambda cmd: "/usr/local/bin/claude" if cmd == "claude" else None),
        patch("subprocess.run", return_value=mock_result) as mock_run,
        patch("sys.exit"),
    ):
        runner = CliRunner()
        runner.invoke(main, ["kaizen", "--fix", "--workspace-dir", str(tmp_path)])
    # Verify claude -p was called (not codex)
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "claude"
    assert call_args[1] == "-p"


def test_cli_kaizen_fix_falls_back_to_codex(tmp_path):
    mock_result = MagicMock()
    mock_result.returncode = 0

    with (
        patch("shutil.which", side_effect=lambda cmd: "/usr/local/bin/codex" if cmd == "codex" else None),
        patch("subprocess.run", return_value=mock_result) as mock_run,
        patch("sys.exit"),
    ):
        runner = CliRunner()
        runner.invoke(main, ["kaizen", "--fix", "--workspace-dir", str(tmp_path)])
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "codex"


# ── actors shinka (mocked async) ──────────────────────────────────────────────

def test_cli_actors_shinka_dry_run_mocked(tmp_path):
    import asyncio

    async def mock_run_shinka(**kwargs):
        pass  # no-op, avoids real LLM/PDS calls

    with patch("etzhayyim.actors._run_shinka", side_effect=mock_run_shinka):
        runner = CliRunner()
        result = runner.invoke(main, [
            "actors", "shinka",
            "--pds", "https://fake.pds.ai",
            "--dry-run",
            "--no-murakumo",
        ])
    # Should not crash (exit 0 because no actors fetched in mock)
    assert result.exit_code == 0


def test_parse_shinka_result_valid():
    from etzhayyim.actors import ActorInfo, _parse_result
    actor = ActorInfo(did="did:plc:abc", nanoid="abc123", handle="billing.etzhayyim.com")
    llm_text = json.dumps({
        "domain_summary": "Billing management actor.",
        "sub_dids": [{"path": "invoices", "display_name": "Invoices", "description": "Invoice ledger"}],
        "knowledge_edges": [{"from": "abc123", "relation": "PRODUCES", "to": "Invoice"}],
    })
    result = _parse_result(actor, llm_text)
    assert result.error == ""
    assert result.domain_summary == "Billing management actor."
    assert len(result.sub_dids) == 1
    assert result.sub_dids[0].path == "invoices"
    assert len(result.knowledge_edges) == 1


def test_parse_shinka_result_no_json():
    from etzhayyim.actors import ActorInfo, _parse_result
    actor = ActorInfo(did="did:plc:abc", nanoid="abc123")
    result = _parse_result(actor, "no json here")
    assert result.error != ""


def test_parse_shinka_result_strips_think_block():
    from etzhayyim.actors import ActorInfo, _parse_result, _RE_JSON_BLOCK
    actor = ActorInfo(did="did:plc:abc", nanoid="abc123", handle="test.etzhayyim.com")
    llm_text = (
        "<think>Let me reason about this...</think>\n"
        + json.dumps({
            "domain_summary": "Test.",
            "sub_dids": [],
            "knowledge_edges": [],
        })
    )
    result = _parse_result(actor, llm_text)
    assert result.domain_summary == "Test."
    assert result.error == ""
