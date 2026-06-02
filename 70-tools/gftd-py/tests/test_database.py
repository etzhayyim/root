"""Unit tests for etzhayyim.database — migration runner and management commands.

No real DB connections are made. subprocess.run and psycopg are mocked.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
from click.testing import CliRunner

from etzhayyim.database import (
    _resolve_db_url,
    _redact_url,
    _validate_migrator_args,
    _list_graph_schema_migrations,
)
from etzhayyim.cli import main


# ─── _resolve_db_url ──────────────────────────────────────────────────────────

class TestResolveDbUrl:
    def test_url_flag_wins(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgres://env-host/db")
        url = _resolve_db_url("postgres://explicit/db", "local")
        assert url == "postgres://explicit/db"

    def test_env_wins_over_preset(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgres://env-host/db")
        url = _resolve_db_url("", "local")
        assert url == "postgres://env-host/db"

    def test_local_preset(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        url = _resolve_db_url("", "local")
        assert "127.0.0.1" in url or "localhost" in url

    def test_prod_preset(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        url = _resolve_db_url("", "prod")
        assert "4566" in url

    def test_unknown_env_raises(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        import click
        with pytest.raises(click.ClickException):
            _resolve_db_url("", "staging")


# ─── _redact_url ──────────────────────────────────────────────────────────────

class TestRedactUrl:
    def test_no_password(self):
        assert _redact_url("postgres://root@localhost:4566/dev") == "postgres://root@localhost:4566/dev"

    def test_redacts_password(self):
        result = _redact_url("postgres://root:secret@localhost:4566/dev")
        assert "secret" not in result
        assert "root@localhost" in result

    def test_no_scheme(self):
        assert _redact_url("not-a-url") == "not-a-url"


# ─── _validate_migrator_args ──────────────────────────────────────────────────

class TestValidateMigratorArgs:
    def test_empty_ok(self):
        _validate_migrator_args([])  # no exception

    def test_latest_ok(self):
        _validate_migrator_args(["latest"])

    def test_up_ok(self):
        _validate_migrator_args(["up"])

    def test_down_ok(self):
        _validate_migrator_args(["down"])

    def test_list_ok(self):
        _validate_migrator_args(["list"])

    def test_to_with_name_ok(self):
        _validate_migrator_args(["to", "0005_vertex_gitrepo"])

    def test_to_without_name_raises(self):
        import click
        with pytest.raises(click.ClickException):
            _validate_migrator_args(["to"])

    def test_latest_with_extra_raises(self):
        import click
        with pytest.raises(click.ClickException):
            _validate_migrator_args(["latest", "extra"])

    def test_unknown_subcommand_raises(self):
        import click
        with pytest.raises(click.ClickException):
            _validate_migrator_args(["unknown"])


# ─── _list_graph_schema_migrations ────────────────────────────────────────────

class TestListGraphSchemaMigrations:
    def test_empty_dir(self, tmp_path):
        (tmp_path / "migrations").mkdir()
        names = _list_graph_schema_migrations(tmp_path)
        assert names == []

    def test_returns_sorted_stems(self, tmp_path):
        mig = tmp_path / "migrations"
        mig.mkdir()
        (mig / "0003_table.ts").touch()
        (mig / "0001_init.ts").touch()
        (mig / "0002_vertex.ts").touch()
        names = _list_graph_schema_migrations(tmp_path)
        assert names == ["0001_init", "0002_vertex", "0003_table"]

    def test_non_ts_files_excluded(self, tmp_path):
        mig = tmp_path / "migrations"
        mig.mkdir()
        (mig / "0001_init.ts").touch()
        (mig / "README.md").touch()
        names = _list_graph_schema_migrations(tmp_path)
        assert names == ["0001_init"]

    def test_missing_migrations_dir(self, tmp_path):
        names = _list_graph_schema_migrations(tmp_path)
        assert names == []


# ─── CLI: migrate ─────────────────────────────────────────────────────────────

class TestDatabaseMigrateCLI:
    def _make_schema(self, tmp_path: Path) -> Path:
        schema = tmp_path / "30-graph" / "graph-schema"
        (schema / "scripts").mkdir(parents=True)
        (schema / "scripts" / "migrate.ts").write_text("// migrate")
        (schema / "migrations").mkdir()
        (schema / "migrations" / "0001_init.ts").write_text("")
        return schema

    def test_help(self):
        result = CliRunner().invoke(main, ["database", "migrate", "--help"])
        assert result.exit_code == 0

    def test_migrate_shells_out_to_node(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        schema = self._make_schema(tmp_path)

        captured: list[list[str]] = []

        def fake_run(args, **kwargs):
            captured.append(list(args))
            return MagicMock(returncode=0)

        with (
            patch("etzhayyim.database._find_git_root", return_value=tmp_path),
            patch("subprocess.run", side_effect=fake_run),
        ):
            result = CliRunner().invoke(main, ["database", "migrate"])
        assert result.exit_code == 0
        assert any("migrate.ts" in " ".join(args) for args in captured)

    def test_migrate_passes_latest_by_default(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        self._make_schema(tmp_path)

        captured: list[list[str]] = []

        def fake_run(args, **kwargs):
            captured.append(list(args))
            return MagicMock(returncode=0)

        with (
            patch("etzhayyim.database._find_git_root", return_value=tmp_path),
            patch("subprocess.run", side_effect=fake_run),
        ):
            CliRunner().invoke(main, ["database", "migrate"])

        assert any("latest" in args for args in captured)

    def test_migrate_to_named(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        self._make_schema(tmp_path)

        captured: list[list[str]] = []

        def fake_run(args, **kwargs):
            captured.append(list(args))
            return MagicMock(returncode=0)

        with (
            patch("etzhayyim.database._find_git_root", return_value=tmp_path),
            patch("subprocess.run", side_effect=fake_run),
        ):
            CliRunner().invoke(main, ["database", "migrate", "to", "0001_init"])

        assert any("to" in args and "0001_init" in args for args in captured)

    def test_migrate_invalid_subcommand(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        self._make_schema(tmp_path)

        with patch("etzhayyim.database._find_git_root", return_value=tmp_path):
            result = CliRunner().invoke(main, ["database", "migrate", "badcmd"])
        assert result.exit_code != 0

    def test_migrate_node_fail_propagates(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        self._make_schema(tmp_path)

        with (
            patch("etzhayyim.database._find_git_root", return_value=tmp_path),
            patch("subprocess.run", return_value=MagicMock(returncode=1)),
        ):
            result = CliRunner().invoke(main, ["database", "migrate"])
        assert result.exit_code != 0


# ─── CLI: up ──────────────────────────────────────────────────────────────────

class TestDatabaseUpCLI:
    def _make_schema(self, tmp_path: Path) -> None:
        schema = tmp_path / "30-graph" / "graph-schema"
        (schema / "scripts").mkdir(parents=True)
        (schema / "scripts" / "migrate.ts").write_text("")
        (schema / "migrations").mkdir()

    def test_up_runs_latest(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        self._make_schema(tmp_path)

        captured: list[list[str]] = []

        def fake_run(args, **kwargs):
            captured.append(list(args))
            return MagicMock(returncode=0)

        with (
            patch("etzhayyim.database._find_git_root", return_value=tmp_path),
            patch("subprocess.run", side_effect=fake_run),
        ):
            result = CliRunner().invoke(main, ["database", "up"])

        assert result.exit_code == 0
        assert any("latest" in args for args in captured)

    def test_up_with_env_prod(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        self._make_schema(tmp_path)

        env_received: list[dict] = []

        def fake_run(args, env=None, **kwargs):
            env_received.append(env or {})
            return MagicMock(returncode=0)

        with (
            patch("etzhayyim.database._find_git_root", return_value=tmp_path),
            patch("subprocess.run", side_effect=fake_run),
        ):
            CliRunner().invoke(main, ["database", "up", "--env", "prod"])

        assert any("<vendor-rw-host>" in e.get("DATABASE_URL", "") for e in env_received)


# ─── CLI: repair-order ────────────────────────────────────────────────────────

class TestDatabaseRepairOrderCLI:
    def _make_schema_with_migrations(self, tmp_path: Path) -> None:
        schema = tmp_path / "30-graph" / "graph-schema"
        mig = schema / "migrations"
        mig.mkdir(parents=True)
        (mig / "0001_init.ts").write_text("")
        (mig / "0002_vertex.ts").write_text("")

    def test_repair_order_aligned(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        self._make_schema_with_migrations(tmp_path)

        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = [
            ("0001_init", "2026-04-13T00:00:00+00:00"),
            ("0002_vertex", "2026-04-13T00:00:01+00:00"),
        ]

        with (
            patch("etzhayyim.database._find_git_root", return_value=tmp_path),
            patch("psycopg.connect", return_value=mock_conn),
        ):
            result = CliRunner().invoke(main, ["database", "repair-order"])

        assert result.exit_code == 0
        assert "aligned" in result.output

    def test_repair_order_empty_db(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        self._make_schema_with_migrations(tmp_path)

        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = []

        with (
            patch("etzhayyim.database._find_git_root", return_value=tmp_path),
            patch("psycopg.connect", return_value=mock_conn),
        ):
            result = CliRunner().invoke(main, ["database", "repair-order"])

        assert result.exit_code == 0
        assert "empty" in result.output

    def test_repair_order_json_output(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        self._make_schema_with_migrations(tmp_path)

        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchall.return_value = [
            ("0001_init", "2026-04-13T00:00:00+00:00"),
            ("0002_vertex", "2026-04-13T00:00:01+00:00"),
        ]

        with (
            patch("etzhayyim.database._find_git_root", return_value=tmp_path),
            patch("psycopg.connect", return_value=mock_conn),
        ):
            result = CliRunner().invoke(main, ["database", "repair-order", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "topology" in data
        assert "applied_count" in data


# ─── CLI: general structure ───────────────────────────────────────────────────

def test_database_help():
    result = CliRunner().invoke(main, ["database", "--help"])
    assert result.exit_code == 0


def test_database_has_migrate():
    result = CliRunner().invoke(main, ["database", "--help"])
    assert "migrate" in result.output


def test_database_has_up():
    result = CliRunner().invoke(main, ["database", "--help"])
    assert "up" in result.output


def test_database_has_repair_order():
    result = CliRunner().invoke(main, ["database", "--help"])
    assert "repair-order" in result.output


def test_database_has_status():
    result = CliRunner().invoke(main, ["database", "--help"])
    assert "status" in result.output
