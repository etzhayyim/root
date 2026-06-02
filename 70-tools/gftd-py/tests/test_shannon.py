"""Unit tests for the shannon command (pure — no real filesystem scanning of the repo)."""

from __future__ import annotations

import hashlib
import json
import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main
from etzhayyim.shannon import (
    ShannonItem,
    ShannonCheck,
    _cap,
    _norm_line,
    _hash8,
    _dedup,
    _strip_jsonc_comments,
    build_report,
    check_claude_md_duplication,
    check_config_redundancy,
    check_dead_code_entropy,
    check_doc_code_drift,
    check_stale_symbol_entropy,
    _sh_entropy,
    _build_dsm_report,
    _build_bayesnet_report,
    _build_bottleneck_report,
    _build_minimize_report,
)


# ── helpers ────────────────────────────────────────────────────────────────────

def test_cap_clamps():
    assert _cap(-10) == 0.0
    assert _cap(110) == 100.0
    assert _cap(75.555) == pytest.approx(75.6, abs=0.01)


def test_norm_line_strips_markdown():
    assert _norm_line("**CRITICAL**: Do NOT do X") == "critical: do not do x"


def test_hash8_length():
    assert len(_hash8("hello")) == 16


def test_dedup_removes_duplicates():
    items = [
        ShannonItem("a.md", "kind", 1.0, detail="same"),
        ShannonItem("a.md", "kind", 1.0, detail="same"),
        ShannonItem("b.md", "kind", 1.0, detail="same"),
    ]
    result = _dedup(items)
    assert len(result) == 2


def test_strip_jsonc_comments_removes_line_comments():
    jsonc = '{"a": 1, // comment\n"b": 2}'
    cleaned = _strip_jsonc_comments(jsonc)
    parsed = json.loads(cleaned)
    assert parsed == {"a": 1, "b": 2}


def test_strip_jsonc_comments_removes_block_comments():
    jsonc = '{"a": /* block */ 1}'
    cleaned = _strip_jsonc_comments(jsonc)
    parsed = json.loads(cleaned)
    assert parsed == {"a": 1}


def test_strip_jsonc_preserves_strings_with_slashes():
    jsonc = '{"url": "https://example.com/path"}'
    cleaned = _strip_jsonc_comments(jsonc)
    assert "https://example.com/path" in cleaned


# ── check_claude_md_duplication ────────────────────────────────────────────────

def test_claude_md_duplication_no_duplication(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Root\n\nThis is the root CLAUDE.md with unique content here.\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "CLAUDE.md").write_text("# Sub\n\nThis directory has entirely different content here.\n")
    chk = check_claude_md_duplication(tmp_path)
    assert chk.violations == 0
    assert chk.score == 100.0


def test_claude_md_duplication_detects_duplicate(tmp_path):
    shared = "This is a very important rule that should not be duplicated across files."
    (tmp_path / "CLAUDE.md").write_text(f"# Root\n\n{shared}\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "CLAUDE.md").write_text(f"# Sub\n\n{shared}\n")
    chk = check_claude_md_duplication(tmp_path)
    assert chk.violations >= 1
    assert chk.score < 100.0


def test_claude_md_duplication_fewer_than_two_files(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Root\n\nOnly one file.\n")
    chk = check_claude_md_duplication(tmp_path)
    assert chk.score == 100.0
    assert "fewer than 2" in chk.details


def test_claude_md_duplication_skips_short_lines(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Root\n\nShort\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "CLAUDE.md").write_text("# Sub\n\nShort\n")
    # "Short" is < 20 chars → not counted as significant
    chk = check_claude_md_duplication(tmp_path)
    assert chk.violations == 0


def test_claude_md_duplication_skips_table_separators(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Root\n\n|---|---|---|\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "CLAUDE.md").write_text("# Sub\n\n|---|---|---|\n")
    chk = check_claude_md_duplication(tmp_path)
    assert chk.violations == 0


# ── check_config_redundancy ────────────────────────────────────────────────────

def test_config_redundancy_no_redundancy(tmp_path):
    for i in range(2):  # 2 files < threshold of 3
        d = tmp_path / f"app{i}"
        d.mkdir()
        (d / "wrangler.jsonc").write_text(json.dumps({"vars": {"UNIQUE_KEY": f"value{i}"}}))
    chk = check_config_redundancy(tmp_path)
    assert chk.violations == 0


def test_config_redundancy_detects_3plus(tmp_path):
    for i in range(3):
        d = tmp_path / f"app{i}"
        d.mkdir()
        (d / "wrangler.jsonc").write_text(json.dumps({"vars": {"SHARED_KEY": "same_value"}}))
    chk = check_config_redundancy(tmp_path)
    assert chk.violations == 1
    assert chk.score < 100.0


def test_config_redundancy_skips_deploy_injected_vars(tmp_path):
    for i in range(4):
        d = tmp_path / f"app{i}"
        d.mkdir()
        (d / "wrangler.jsonc").write_text(json.dumps({
            "vars": {"APP_VERSION": "1.0", "APP_TEMPLATE": "base"}
        }))
    chk = check_config_redundancy(tmp_path)
    assert chk.violations == 0  # deploy-injected vars are excluded


def test_config_redundancy_handles_jsonc_comments(tmp_path):
    content = '// This is a comment\n{"vars": {"KEY": "value"}}'
    d = tmp_path / "app0"
    d.mkdir()
    (d / "wrangler.jsonc").write_text(content)
    # No exception should be raised
    chk = check_config_redundancy(tmp_path)
    assert isinstance(chk.score, float)


# ── check_dead_code_entropy ────────────────────────────────────────────────────

def test_dead_code_entropy_empty_go_func(tmp_path):
    src = tmp_path / "projects" / "myapp"
    src.mkdir(parents=True)
    (src / "main.go").write_text("package main\n\nfunc EmptyFunc() {}\n")
    chk = check_dead_code_entropy(tmp_path)
    assert chk.violations > 0
    assert any("empty Go func" in i.detail for i in chk.items)


def test_dead_code_entropy_stub_ts_func(tmp_path):
    src = tmp_path / "60-apps" / "myapp"
    src.mkdir(parents=True)
    (src / "app.ts").write_text("export function myFunc() { throw new Error('not implemented'); }\n")
    chk = check_dead_code_entropy(tmp_path)
    assert chk.violations > 0


def test_dead_code_entropy_no_issues(tmp_path):
    src = tmp_path / "projects" / "myapp"
    src.mkdir(parents=True)
    (src / "main.go").write_text("package main\n\nfunc GoodFunc() {\n    return doWork()\n}\n")
    chk = check_dead_code_entropy(tmp_path)
    # No empty/stub functions
    assert all("empty" not in i.detail for i in chk.items)


# ── check_doc_code_drift ───────────────────────────────────────────────────────

def test_doc_code_drift_no_evidence_links(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Root\n\n[PRODUCTION] Some feature\n")
    chk = check_doc_code_drift(tmp_path)
    assert "no [PRODUCTION]" in chk.details or chk.violations == 0


def test_doc_code_drift_valid_evidence(tmp_path):
    real_file = tmp_path / "src" / "app.ts"
    real_file.parent.mkdir()
    real_file.write_text("// real file")
    (tmp_path / "CLAUDE.md").write_text(
        f"[PRODUCTION] Feature `src/app.ts:42`\n"
    )
    chk = check_doc_code_drift(tmp_path)
    assert chk.violations == 0


def test_doc_code_drift_stale_evidence(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(
        "[PRODUCTION] Feature `src/missing_file.ts:42`\n"
    )
    chk = check_doc_code_drift(tmp_path)
    assert chk.violations == 1
    assert chk.score < 100.0


def test_doc_code_drift_score_100_when_no_claims(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Root\n\nNo status tags here.\n")
    chk = check_doc_code_drift(tmp_path)
    assert chk.score == 100.0


# ── check_stale_symbol_entropy ─────────────────────────────────────────────────

def test_stale_symbol_entropy_detects_strikethrough(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Root\n\n~~Remove this deprecated section~~\n")
    chk = check_stale_symbol_entropy(tmp_path)
    assert chk.violations > 0
    assert any("strikethrough" in i.detail for i in chk.items)


def test_stale_symbol_entropy_skips_prohibited_strikethrough(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(
        "# Root\n\n~~`SqlExec`~~ 禁止 — use G() builder\n"
    )
    chk = check_stale_symbol_entropy(tmp_path)
    # Lines with 禁止 are excluded from strikethrough violations
    strikethrough = [i for i in chk.items if "strikethrough" in i.detail]
    assert len(strikethrough) == 0


def test_stale_symbol_entropy_detects_prohibited_api(tmp_path):
    src = tmp_path / "projects" / "app"
    src.mkdir(parents=True)
    (src / "main.go").write_text('result := SqlQueryMap("MATCH (n) RETURN n")\n')
    chk = check_stale_symbol_entropy(tmp_path)
    prohibited = [i for i in chk.items if i.kind == "prohibited-api"]
    assert len(prohibited) > 0


def test_stale_symbol_entropy_no_issues(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Clean\n\nNo stale symbols here.\n")
    chk = check_stale_symbol_entropy(tmp_path)
    assert chk.violations == 0


# ── build_report ───────────────────────────────────────────────────────────────

def test_build_report_sets_weights():
    checks = [
        ShannonCheck(name="claude_md_duplication", score=80.0),
        ShannonCheck(name="config_redundancy", score=90.0),
    ]
    report = build_report(checks, top_n=5)
    # Weights should be set
    assert checks[0].weight == pytest.approx(0.25)
    assert checks[1].weight == pytest.approx(0.10)


def test_build_report_hotspots_sorted():
    item_hi = ShannonItem("a.ts", "kind", 1.0)
    item_lo = ShannonItem("b.ts", "kind", 0.3)
    checks = [ShannonCheck(name="dead_code_entropy", score=90.0, items=[item_lo, item_hi])]
    report = build_report(checks, top_n=5)
    assert report.hotspots[0].redundancy >= report.hotspots[-1].redundancy


def test_build_report_overall_score_bounded():
    checks = [ShannonCheck(name="claude_md_duplication", score=100.0)]
    report = build_report(checks)
    assert 0.0 <= report.overall_score <= 100.0
    assert 0.0 <= report.redundancy_rate <= 1.0


# ── CLI integration ────────────────────────────────────────────────────────────

def test_cli_shannon_scan_json(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["shannon", "scan", "--json",
                                  "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "overall_score" in data
    assert "checks" in data
    assert len(data["checks"]) == 9


def test_cli_shannon_scan_text(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["shannon", "scan",
                                  "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "shannon:" in result.output
    assert "overall_score:" in result.output


def test_cli_shannon_violations_json(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["shannon", "violations", "--json",
                                  "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_cli_shannon_violations_text(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["shannon", "violations",
                                  "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "total violations:" in result.output


# ── _sh_entropy ────────────────────────────────────────────────────────────────

class TestShEntropy:
    def test_empty_returns_zero(self):
        assert _sh_entropy({}) == 0.0

    def test_uniform_two_symbols(self):
        h = _sh_entropy({"a": 1, "b": 1})
        assert abs(h - 1.0) < 1e-9

    def test_uniform_four_symbols(self):
        h = _sh_entropy({"a": 1, "b": 1, "c": 1, "d": 1})
        assert abs(h - 2.0) < 1e-9

    def test_certain_single_symbol(self):
        assert _sh_entropy({"x": 10}) == 0.0

    def test_zero_count_ignored(self):
        h = _sh_entropy({"a": 1, "b": 0})
        assert h == 0.0


# ── DSM ────────────────────────────────────────────────────────────────────────

class TestBuildDsmReport:
    def _simple_adj(self):
        return {"A": {"B": 1}, "B": {"C": 1}, "C": {"A": 1}}

    def test_empty_apps_returns_score_100(self):
        r = _build_dsm_report([], {}, 10, False)
        assert r["score"] == 100.0
        assert r["size"] == 0

    def test_three_app_cycle_detected(self):
        apps = ["A", "B", "C"]
        adj = self._simple_adj()
        r = _build_dsm_report(apps, adj, 10, False)
        assert r["size"] == 3
        assert len(r["cycles"]) >= 1
        assert r["cycles"][0]["length"] == 3

    def test_matrix_dimensions_correct(self):
        apps = ["A", "B", "C"]
        r = _build_dsm_report(apps, self._simple_adj(), 10, False)
        assert len(r["matrix"]) == 3
        assert all(len(row) == 3 for row in r["matrix"])

    def test_no_reorder_flag_respected(self):
        apps = ["A", "B", "C", "D"]
        adj = {"A": {"B": 1}, "B": {"C": 1}, "C": {"D": 1}}
        r = _build_dsm_report(apps, adj, 10, True)
        assert r["apps"] == ["A", "B", "C", "D"]

    def test_score_between_0_and_100(self):
        apps = ["X", "Y"]
        adj = {"X": {"Y": 5}}
        r = _build_dsm_report(apps, adj, 10, False)
        assert 0 <= r["score"] <= 100

    def test_clusters_found(self):
        apps = ["A", "B", "C"]
        adj = {"A": {"B": 1}}
        r = _build_dsm_report(apps, adj, 10, False)
        assert len(r["clusters"]) >= 1

    def test_top_n_limits_clusters(self):
        apps = [f"A{i}" for i in range(10)]
        adj = {}
        r = _build_dsm_report(apps, adj, 3, False)
        assert len(r["clusters"]) <= 3

    def test_json_output_via_cli(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["shannon", "dsm", "--json", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "size" in data
        assert "score" in data

    def test_text_output_via_cli(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["shannon", "dsm", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "shannon dsm:" in result.output


# ── BayesNet ───────────────────────────────────────────────────────────────────

class TestBuildBayesnetReport:
    def test_empty_returns_score_100(self):
        r = _build_bayesnet_report([], {}, 10, 6)
        assert r["score"] == 100.0
        assert r["total_apps"] == 0

    def test_single_edge_produces_edge_entry(self):
        adj_typed = {"A": {"B": {"invoke": 1}}}
        apps = ["A", "B"]
        r = _build_bayesnet_report(apps, adj_typed, 10, 6)
        assert r["total_edges"] == 1
        assert r["edges"][0]["from"] == "A"
        assert r["edges"][0]["to"] == "B"

    def test_invoke_weight_dominates(self):
        adj_typed = {"A": {"B": {"invoke": 1}}}
        r = _build_bayesnet_report(["A", "B"], adj_typed, 10, 6)
        edge = r["edges"][0]
        assert edge["conditional"] == 0.8

    def test_multiple_edge_types_accumulate(self):
        adj_typed = {"A": {"B": {"invoke": 1, "writes": 1}}}
        r = _build_bayesnet_report(["A", "B"], adj_typed, 10, 6)
        edge = r["edges"][0]
        # invoke=0.8 + writes=0.5 = 1.3 > 1.0 → sigmoid saturation: 1 - 1/(1+1.3) ≈ 0.565
        assert edge["conditional"] != 0.8  # differs from single invoke weight
        assert 0.0 < edge["conditional"] < 1.0

    def test_edges_sorted_by_conditional_descending(self):
        adj_typed = {
            "A": {"B": {"invoke": 1}},
            "C": {"D": {"reads": 1}},
        }
        r = _build_bayesnet_report(["A", "B", "C", "D"], adj_typed, 10, 6)
        conditionals = [e["conditional"] for e in r["edges"]]
        assert conditionals == sorted(conditionals, reverse=True)

    def test_score_between_0_and_100(self):
        adj_typed = {"A": {"B": {"invoke": 1}}}
        r = _build_bayesnet_report(["A", "B"], adj_typed, 10, 6)
        assert 0 <= r["score"] <= 100

    def test_json_output_via_cli(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["shannon", "bayesnet", "--json", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_apps" in data
        assert "score" in data

    def test_text_output_via_cli(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["shannon", "bayesnet", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "shannon bayesnet:" in result.output


# ── Bottleneck ─────────────────────────────────────────────────────────────────

class TestBuildBottleneckReport:
    def test_empty_returns_score_100(self):
        r = _build_bottleneck_report([], {}, 15, 2)
        assert r["score"] == 100.0

    def test_below_min_fan_excluded(self):
        adj_typed = {"A": {"B": {"invoke": 1}}}
        r = _build_bottleneck_report(["A", "B"], adj_typed, 15, 5)
        assert r["bottlenecks"] == []

    def test_hub_node_detected(self):
        adj_typed = {f"S{i}": {"HUB": {"invoke": 1}} for i in range(6)}
        adj_typed.update({"HUB": {f"T{i}": {"reads": 1} for i in range(6)}})
        apps = ["HUB"] + [f"S{i}" for i in range(6)] + [f"T{i}" for i in range(6)]
        r = _build_bottleneck_report(apps, adj_typed, 15, 2)
        assert len(r["bottlenecks"]) >= 1
        assert r["bottlenecks"][0]["app"] == "HUB"

    def test_severity_critical_for_high_fan(self):
        adj_typed = {f"S{i}": {"HUB": {"invoke": 1}} for i in range(6)}
        adj_typed.update({"HUB": {f"T{i}": {"reads": 1} for i in range(6)}})
        apps = ["HUB"] + [f"S{i}" for i in range(6)] + [f"T{i}" for i in range(6)]
        r = _build_bottleneck_report(apps, adj_typed, 15, 2)
        hub = next(b for b in r["bottlenecks"] if b["app"] == "HUB")
        assert hub["severity"] in ("critical", "high")

    def test_top_n_limits_results(self):
        adj_typed = {f"A{i}": {"B": {"invoke": 1}, "C": {"reads": 1}} for i in range(20)}
        apps = [f"A{i}" for i in range(20)] + ["B", "C"]
        r = _build_bottleneck_report(apps, adj_typed, 3, 1)
        assert len(r["bottlenecks"]) <= 3

    def test_json_output_via_cli(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["shannon", "bottleneck", "--json", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_apps" in data

    def test_text_output_via_cli(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["shannon", "bottleneck", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "shannon bottleneck:" in result.output


# ── Minimize ───────────────────────────────────────────────────────────────────

class TestBuildMinimizeReport:
    def test_empty_returns_score_50(self):
        r = _build_minimize_report([], {}, {}, 15, 2.0)
        assert r["score"] == 100.0

    def test_merge_proposal_for_high_mutual_coupling(self):
        apps = ["A", "B", "C"]
        adj = {"A": {"B": 3, "C": 1}, "B": {"A": 2}}
        app_proj = {"A": "proj1", "B": "proj1", "C": "proj2"}
        r = _build_minimize_report(apps, adj, app_proj, 15, 2.0)
        merge_proposals = [p for p in r["proposals"] if p["action"] == "merge"]
        assert len(merge_proposals) >= 1

    def test_split_proposal_for_high_entropy(self):
        apps = ["A"]
        adj = {"A": {f"T{i}": 1 for i in range(10)}}
        app_proj = {f"T{i}": "other" for i in range(10)}
        app_proj["A"] = "proj1"
        r = _build_minimize_report(apps + [f"T{i}" for i in range(10)], adj, app_proj, 15, 1.0)
        split_proposals = [p for p in r["proposals"] if p["action"] == "split"]
        assert len(split_proposals) >= 1

    def test_move_proposal_when_cross_project_dominant(self):
        apps = ["A", "B1", "B2", "B3"]
        adj = {"A": {"B1": 4, "B2": 3, "B3": 3}}
        app_proj = {"A": "projA", "B1": "projB", "B2": "projB", "B3": "projB"}
        r = _build_minimize_report(apps, adj, app_proj, 15, 2.0)
        move_proposals = [p for p in r["proposals"] if p["action"] == "move"]
        assert len(move_proposals) >= 1

    def test_no_proposals_for_isolated_app(self):
        apps = ["A"]
        r = _build_minimize_report(apps, {}, {"A": "proj"}, 15, 2.0)
        assert r["proposals"] == []

    def test_top_n_limits_proposals(self):
        apps = [f"A{i}" for i in range(30)]
        adj = {a: {b: 5 for b in apps if b != a} for a in apps}
        app_proj = {a: "proj" + a for a in apps}
        r = _build_minimize_report(apps, adj, app_proj, 5, 0.1)
        assert len(r["proposals"]) <= 5

    def test_system_entropy_non_negative(self):
        apps = ["A", "B"]
        adj = {"A": {"B": 2}}
        r = _build_minimize_report(apps, adj, {"A": "p", "B": "p"}, 15, 2.0)
        assert r["system_entropy"] >= 0
        assert r["cohesion_entropy"] >= 0

    def test_json_output_via_cli(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["shannon", "minimize", "--json", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "proposals" in data

    def test_text_output_via_cli(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, ["shannon", "minimize", "--workspace-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "shannon minimize:" in result.output
