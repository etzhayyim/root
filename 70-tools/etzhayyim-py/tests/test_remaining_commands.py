"""Tests for remaining commands: authz, dodaf, kashika, systemofsystem, kagami,
dns-sync, database, murakumo, training, agent, agent-runtime, organism, cohort.

Network-dependent commands are tested for CLI structure only (no live PDS calls).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from etzhayyim.cli import main


# ── authz ──────────────────────────────────────────────────────────────────────

def test_authz_help():
    runner = CliRunner()
    result = runner.invoke(main, ["authz", "--help"])
    assert result.exit_code == 0


def test_authz_dids_not_signed_in(tmp_path):
    auth_file = tmp_path / ".etzhayyim" / "auth.json"
    with patch("etzhayyim.authz._AUTH_FILE", auth_file), \
         patch("etzhayyim.authn._AUTH_FILE", auth_file):
        runner = CliRunner()
        result = runner.invoke(main, ["authz", "dids"])
    assert result.exit_code != 0


def test_authz_dids_with_auth(tmp_path):
    auth_file = tmp_path / ".etzhayyim" / "auth.json"
    auth_file.parent.mkdir(parents=True)
    auth_file.write_text(json.dumps({"did": "did:plc:abc", "accessJwt": "tok"}))
    with patch("etzhayyim.authz._AUTH_FILE", auth_file), \
         patch("etzhayyim.authn._AUTH_FILE", auth_file):
        runner = CliRunner()
        result = runner.invoke(main, ["authz", "dids", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "dids" in data
    assert "did:plc:abc" in data["dids"]


def test_authz_switch_not_signed_in(tmp_path):
    auth_file = tmp_path / ".etzhayyim" / "missing.json"
    with patch("etzhayyim.authz._AUTH_FILE", auth_file):
        runner = CliRunner()
        result = runner.invoke(main, ["authz", "switch", "did:plc:new"])
    assert result.exit_code != 0


def test_authz_switch_updates_did(tmp_path):
    auth_file = tmp_path / ".etzhayyim" / "auth.json"
    auth_file.parent.mkdir()
    auth_file.write_text(json.dumps({"did": "did:plc:old", "accessJwt": "tok"}))
    with patch("etzhayyim.authz._AUTH_FILE", auth_file), \
         patch("etzhayyim.authn._AUTH_FILE", auth_file):
        runner = CliRunner()
        result = runner.invoke(main, ["authz", "switch", "did:plc:new"])
    assert result.exit_code == 0
    data = json.loads(auth_file.read_text())
    assert data["did"] == "did:plc:new"


# ── dodaf ──────────────────────────────────────────────────────────────────────

def test_dodaf_help():
    runner = CliRunner()
    result = runner.invoke(main, ["dodaf", "--help"])
    assert result.exit_code == 0


def test_dodaf_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["dodaf", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "dodaf" in result.output


def test_dodaf_json_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["dodaf", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "total" in data


def test_dodaf_scan_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["dodaf", "scan", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.output) == []


def test_dodaf_scan_with_actors(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "appview" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "magatama.jsonld").write_text(json.dumps({
        "nanoid": "abc", "name": "test", "performerType": "actor"
    }))
    runner = CliRunner()
    result = runner.invoke(main, ["dodaf", "scan", "--json", "--type", "actor",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) >= 1


def test_dodaf_viewpoints_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["dodaf", "viewpoints", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0


def test_dodaf_generate_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(main, ["dodaf", "generate"])
    assert result.exit_code != 0


# ── kashika ────────────────────────────────────────────────────────────────────

def test_kashika_help():
    runner = CliRunner()
    result = runner.invoke(main, ["kashika", "--help"])
    assert result.exit_code == 0


def test_kashika_mermaid_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kashika", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "graph LR" in result.output


def test_kashika_dot_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kashika", "--format", "dot", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "digraph" in result.output


def test_kashika_json_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kashika", "--format", "json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "apps" in data
    assert "edges" in data


def test_kashika_mermaid_subcommand(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kashika", "mermaid", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0


def test_kashika_dot_subcommand(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kashika", "dot", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0


def test_kashika_json_subcommand(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kashika", "json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "apps" in data


def test_kashika_output_file(tmp_path):
    out = tmp_path / "diagram.mmd"
    runner = CliRunner()
    result = runner.invoke(main, ["kashika", "mermaid", "--output", str(out),
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert out.exists()
    assert "graph LR" in out.read_text()


# ── systemofsystem ─────────────────────────────────────────────────────────────

def test_sos_help():
    runner = CliRunner()
    result = runner.invoke(main, ["systemofsystem", "--help"])
    assert result.exit_code == 0


def test_sos_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["systemofsystem", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0


def test_sos_json_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["systemofsystem", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)


def test_sos_clusters_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["systemofsystem", "clusters", "--json",
                                   "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.output) == []


def test_sos_coupling_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["systemofsystem", "coupling", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0


# ── kagami ─────────────────────────────────────────────────────────────────────

def test_kagami_help():
    runner = CliRunner()
    result = runner.invoke(main, ["kagami", "--help"])
    assert result.exit_code == 0


def test_kagami_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kagami", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "kagami" in result.output


def test_kagami_local_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["kagami", "local", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.output) == []


def test_kagami_local_with_actors(tmp_path):
    app_dir = tmp_path / "60-apps" / "proj" / "appview" / "app"
    app_dir.mkdir(parents=True)
    (app_dir / "magatama.jsonld").write_text(json.dumps({
        "nanoid": "abc123", "name": "billing", "performerType": "actor"
    }))
    runner = CliRunner()
    result = runner.invoke(main, ["kagami", "local", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["nanoid"] == "abc123"


def test_kagami_diff_not_signed_in(tmp_path):
    auth_file = tmp_path / ".etzhayyim" / "auth.json"
    with patch("etzhayyim.kagami._load_auth", return_value={}):
        runner = CliRunner()
        result = runner.invoke(main, ["kagami", "diff", "--workspace-dir", str(tmp_path)])
    assert result.exit_code != 0


# ── dns-sync ───────────────────────────────────────────────────────────────────

def test_dns_sync_help():
    runner = CliRunner()
    result = runner.invoke(main, ["dns-sync", "--help"])
    assert result.exit_code == 0


def test_dns_sync_offline_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["dns-sync", "--no-cf", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "offline" in result.output


def test_dns_sync_offline_json_empty(tmp_path):
    runner = CliRunner()
    result = runner.invoke(main, ["dns-sync", "--no-cf", "--json", "--workspace-dir", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["mode"] == "offline"
    assert "desired" in data


def test_dns_sync_no_token_fails(tmp_path):
    from unittest.mock import patch
    with patch("etzhayyim.dns_sync._resolve_cf_token", return_value=("", "")):
        runner = CliRunner()
        result = runner.invoke(main, ["dns-sync", "--workspace-dir", str(tmp_path)])
    assert result.exit_code != 0


# ── stub commands help ─────────────────────────────────────────────────────────

def test_database_help():
    runner = CliRunner()
    result = runner.invoke(main, ["database", "--help"])
    assert result.exit_code == 0


def test_murakumo_help():
    runner = CliRunner()
    result = runner.invoke(main, ["murakumo", "--help"])
    assert result.exit_code == 0


def test_training_help():
    runner = CliRunner()
    result = runner.invoke(main, ["training", "--help"])
    assert result.exit_code == 0


def test_agent_help():
    runner = CliRunner()
    result = runner.invoke(main, ["agent", "--help"])
    assert result.exit_code == 0


def test_agent_run_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(main, ["agent", "run", "--prompt", "hello"])
    assert result.exit_code != 0


def test_agent_runtime_help():
    runner = CliRunner()
    result = runner.invoke(main, ["agent-runtime", "--help"])
    assert result.exit_code == 0


def test_agent_runtime_restart_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(main, ["agent-runtime", "restart"])
    assert result.exit_code != 0


def test_organism_help():
    runner = CliRunner()
    result = runner.invoke(main, ["organism", "--help"])
    assert result.exit_code == 0


def test_cohort_help():
    runner = CliRunner()
    result = runner.invoke(main, ["cohort", "--help"])
    assert result.exit_code == 0
