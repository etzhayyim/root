"""Unit tests for source-graph import analysis."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main
from etzhayyim.source_graph import scan_source_graph, SGReport, _parse_ts_imports, _parse_py_imports


# ── parsers ────────────────────────────────────────────────────────────────────

def test_parse_ts_imports_basic():
    content = "import { x } from './lib/x';\nimport y from '../utils';"
    imps = _parse_ts_imports(content)
    assert "./lib/x" in imps
    assert "../utils" in imps


def test_parse_ts_imports_skips_node():
    content = "import { path } from 'node:path';"
    imps = _parse_ts_imports(content)
    assert not any(i.startswith("node:") for i in imps)


def test_parse_ts_imports_skips_at_packages():
    content = "import { x } from '@etzhayyim/sdk';"
    imps = _parse_ts_imports(content)
    assert not any(i.startswith("@") for i in imps)


def test_parse_py_imports_basic():
    content = "import os\nfrom pathlib import Path\nfrom etzhayyim.kaizen import score"
    imps = _parse_py_imports(content)
    assert "os" in imps
    assert "pathlib" in imps
    assert "etzhayyim.kaizen" in imps


# ── scan_source_graph ──────────────────────────────────────────────────────────

def test_scan_empty(tmp_path):
    r = scan_source_graph(tmp_path)
    assert r.nodes == []
    assert r.edges == []


def test_scan_single_ts_file(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text("const x = 1;\n")
    r = scan_source_graph(tmp_path)
    assert any(n.lang == "typescript" for n in r.nodes)


def test_scan_ts_relative_import_edge(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "lib.ts").write_text("export const x = 1;\n")
    (src / "app.ts").write_text("import { x } from './lib';\n")
    r = scan_source_graph(tmp_path)
    assert any(e.target.endswith("lib.ts") for e in r.edges)


def test_scan_py_file(tmp_path):
    (tmp_path / "mod.py").write_text("import os\nfrom pathlib import Path\n")
    r = scan_source_graph(tmp_path)
    assert any(n.lang == "python" for n in r.nodes)
    node = next(n for n in r.nodes if n.lang == "python")
    assert "os" in node.imports


def test_scan_orphans_single_file(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text("const x = 1;\n")
    r = scan_source_graph(tmp_path)
    orphans = r.orphan_paths()
    # file with no imports and not imported — should be orphan
    assert "src/app.ts" in orphans or len(orphans) >= 1


def test_scan_cycles_empty(tmp_path):
    r = scan_source_graph(tmp_path)
    assert r.cycles() == []


def test_scan_skip_node_modules(tmp_path):
    (tmp_path / "node_modules" / "pkg").mkdir(parents=True)
    (tmp_path / "node_modules" / "pkg" / "index.ts").write_text("const x = 1;\n")
    r = scan_source_graph(tmp_path)
    assert all("node_modules" not in n.path for n in r.nodes)


def test_report_to_dict(tmp_path):
    r = scan_source_graph(tmp_path)
    d = r.to_dict()
    assert "nodes" in d
    assert "edges" in d


# ── CLI ────────────────────────────────────────────────────────────────────────

def test_cli_source_graph_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["source-graph", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "source-graph" in result.output


def test_cli_source_graph_json(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["source-graph", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "nodes" in data
    assert "edges" in data


def test_cli_source_graph_scan(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["source-graph", "scan", "--json",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.output) == []


def test_cli_source_graph_scan_with_ts(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text("const x = 1;\n")
    runner = CliRunner()
    result = runner.invoke(main, ["source-graph", "scan", "--json",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) >= 1


def test_cli_source_graph_orphans(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["source-graph", "orphans", "--json",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0


def test_cli_source_graph_cycles(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["source-graph", "cycles", "--json",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data == []


def test_cli_source_graph_deps_not_found(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["source-graph", "deps", "nonexistent.ts",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code != 0


def test_cli_source_graph_lang_filter(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.ts").write_text("const x = 1;\n")
    (tmp_path / "mod.py").write_text("import os\n")
    runner = CliRunner()
    result = runner.invoke(main, ["source-graph", "scan", "--json", "--lang", "python",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert all(n["lang"] == "python" for n in data)
