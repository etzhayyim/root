"""Unit tests for haisen actor wiring diagram."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main
from etzhayyim.haisen import (
    HaisenApp,
    HaisenEdge,
    HaisenReport,
    _app_from_jsonld,
    _read_jsonld,
    _scan_workspace,
)


# ── _read_jsonld ───────────────────────────────────────────────────────────────

def test_read_jsonld_missing(tmp_path):
    d = _read_jsonld(tmp_path / "missing.jsonld")
    assert d == {}


def test_read_jsonld_valid(tmp_path):
    p = tmp_path / "test.jsonld"
    p.write_text('{"nanoid": "abc"}')
    assert _read_jsonld(p) == {"nanoid": "abc"}


def test_read_jsonld_invalid_json(tmp_path):
    p = tmp_path / "bad.jsonld"
    p.write_text("not json")
    assert _read_jsonld(p) == {}


# ── _app_from_jsonld ───────────────────────────────────────────────────────────

def test_app_from_jsonld_no_nanoid():
    assert _app_from_jsonld({}) is None


def test_app_from_jsonld_minimal():
    app = _app_from_jsonld({"nanoid": "abc123"})
    assert app is not None
    assert app.nanoid == "abc123"
    assert app.did == ""
    assert app.collections == []


def test_app_from_jsonld_full():
    data = {
        "nanoid": "abc123",
        "did": "did:web:example.com",
        "name": "billing",
        "performerType": "actor",
        "uiType": "wasm",
        "runtimeType": "ts-native",
        "collections": ["com.etzhayyim.apps.billing.invoice"],
        "witImports": ["clock"],
        "witExports": ["billing-api"],
    }
    app = _app_from_jsonld(data)
    assert app.nanoid == "abc123"
    assert app.did == "did:web:example.com"
    assert app.collections == ["com.etzhayyim.apps.billing.invoice"]
    assert app.wit_imports == ["clock"]
    assert app.wit_exports == ["billing-api"]


# ── HaisenReport ──────────────────────────────────────────────────────────────

def test_haisen_report_orphans_empty():
    r = HaisenReport(apps=[], edges=[])
    assert r.orphans == []


def test_haisen_report_orphans_no_edges():
    apps = [
        HaisenApp("a1", "", "", "", "", ""),
        HaisenApp("a2", "", "", "", "", ""),
    ]
    r = HaisenReport(apps=apps, edges=[])
    assert len(r.orphans) == 2


def test_haisen_report_orphans_with_edges():
    apps = [
        HaisenApp("a1", "", "", "", "", ""),
        HaisenApp("a2", "", "", "", "", ""),
        HaisenApp("a3", "", "", "", "", ""),
    ]
    edges = [HaisenEdge("a1", "a2", "invoke")]
    r = HaisenReport(apps=apps, edges=edges)
    orphans = r.orphans
    assert len(orphans) == 1
    assert orphans[0].nanoid == "a3"


def test_haisen_report_coupling_empty():
    r = HaisenReport(apps=[], edges=[])
    assert r.coupling() == {}


def test_haisen_report_coupling_counts():
    edges = [
        HaisenEdge("a1", "hub", "invoke"),
        HaisenEdge("a2", "hub", "invoke"),
        HaisenEdge("a1", "leaf", "reads"),
    ]
    r = HaisenReport(apps=[], edges=edges)
    c = r.coupling()
    assert c["hub"] == 2
    assert c["leaf"] == 1


def test_haisen_report_to_dict():
    apps = [HaisenApp("a1", "did:web:x", "App1", "actor", "wasm", "ts-native")]
    edges = [HaisenEdge("a1", "a2", "subscribe")]
    r = HaisenReport(apps=apps, edges=edges)
    d = r.to_dict()
    assert len(d["apps"]) == 1
    assert len(d["edges"]) == 1
    assert d["edges"][0]["type"] == "subscribe"


# ── _scan_workspace ────────────────────────────────────────────────────────────

def test_scan_empty_workspace(tmp_path):
    r = _scan_workspace(tmp_path)
    assert r.apps == []
    assert r.edges == []


def test_scan_single_actor(tmp_path):
    app_dir = tmp_path / "60-apps" / "etzhayyim-project-billing" / "appview" / "app-abc"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "abc123",
        "did": "did:web:billing.etzhayyim.com",
        "name": "billing",
        "performerType": "actor",
        "collections": ["com.etzhayyim.apps.billing.invoice"],
    }))
    r = _scan_workspace(tmp_path)
    assert len(r.apps) == 1
    assert r.apps[0].nanoid == "abc123"


def test_scan_wasm_import_edges(tmp_path):
    """wasm-import edges from witImports/witExports cross-reference."""
    apps_dir = tmp_path / "60-apps"

    a_dir = apps_dir / "proj-a" / "appview" / "app-a"
    a_dir.mkdir(parents=True)
    (a_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "aaaa",
        "witExports": ["billing-api"],
    }))

    b_dir = apps_dir / "proj-b" / "appview" / "app-b"
    b_dir.mkdir(parents=True)
    (b_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "bbbb",
        "witImports": ["billing-api"],
    }))

    r = _scan_workspace(tmp_path)
    assert any(e.edge_type == "wasm-import" and e.from_nanoid == "bbbb" and e.to_nanoid == "aaaa"
               for e in r.edges)


def test_scan_dependency_edges(tmp_path):
    """Explicit dependencies[] in kotodama.jsonld create invoke edges."""
    apps_dir = tmp_path / "60-apps"

    hub = apps_dir / "proj-hub" / "appview" / "hub"
    hub.mkdir(parents=True)
    (hub / "kotodama.jsonld").write_text(json.dumps({"nanoid": "hub1"}))

    leaf = apps_dir / "proj-leaf" / "appview" / "leaf"
    leaf.mkdir(parents=True)
    (leaf / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "leaf1",
        "dependencies": ["hub1"],
    }))

    r = _scan_workspace(tmp_path)
    assert any(e.from_nanoid == "leaf1" and e.to_nanoid == "hub1" and e.edge_type == "invoke"
               for e in r.edges)


def test_scan_no_self_edges(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "appview" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "self1",
        "witExports": ["api"],
        "witImports": ["api"],
    }))
    r = _scan_workspace(tmp_path)
    assert all(e.from_nanoid != e.to_nanoid for e in r.edges)


# ── CLI integration ────────────────────────────────────────────────────────────

def test_cli_haisen_json_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["haisen", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "apps" in data
    assert "edges" in data
    assert data["apps"] == []


def test_cli_haisen_text_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["haisen", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "haisen" in result.output.lower()


def test_cli_haisen_scan(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "appview" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "kotodama.jsonld").write_text(json.dumps({
        "nanoid": "abc123",
        "name": "test",
    }))
    runner = CliRunner()
    result = runner.invoke(main, ["haisen", "scan", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["nanoid"] == "abc123"


def test_cli_haisen_edges(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["haisen", "edges", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.output) == []


def test_cli_haisen_orphans(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["haisen", "orphans", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "orphans" in result.output


def test_cli_haisen_coupling(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["haisen", "coupling", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.output) == []


def test_cli_haisen_edges_type_filter(tmp_path):
    apps_dir = tmp_path / "60-apps"
    a = apps_dir / "pa" / "appview" / "a"
    a.mkdir(parents=True)
    (a / "kotodama.jsonld").write_text(json.dumps({"nanoid": "aaaa", "witExports": ["x"]}))
    b = apps_dir / "pb" / "appview" / "b"
    b.mkdir(parents=True)
    (b / "kotodama.jsonld").write_text(json.dumps({"nanoid": "bbbb", "witImports": ["x"]}))

    runner = CliRunner()
    result = runner.invoke(main, ["haisen", "edges", "--json", "--type", "wasm-import",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert all(e["type"] == "wasm-import" for e in data)
