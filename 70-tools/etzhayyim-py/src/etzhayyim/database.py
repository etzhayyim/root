"""database — Database management commands (RisingWave / Kysely).

DDL migrations shell out to the Kysely TS runner in 30-graph/graph-schema/.
SSoT: 30-graph/graph-schema/migrations/*.ts
Runner: 30-graph/graph-schema/scripts/migrate.ts
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds

_GRAPH_SCHEMA_REL = "30-graph/graph-schema"

_RW_LOCAL_URL = "postgres://root@127.0.0.1:14566/dev?sslmode=disable"
_RW_PROD_URL = "REDACTED_USE_DATABASE_URL_ENV"

_VALID_SUBCOMMANDS = {"latest", "up", "down", "list", "to"}


def _auth_headers() -> dict[str, str]:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _resolve_db_url(url_flag: str, env_name: str) -> str:
    if url_flag:
        return url_flag
    env_val = os.environ.get("DATABASE_URL", "")
    if env_val:
        return env_val
    if env_name == "local":
        return _RW_LOCAL_URL
    if env_name == "prod":
        return _RW_PROD_URL
    raise click.ClickException(
        f"unknown --env {env_name!r} (want: local, prod) — or pass --url / $DATABASE_URL"
    )


def _redact_url(url: str) -> str:
    """Strip password from postgres URL for logging."""
    scheme_end = url.find("://")
    if scheme_end < 0:
        return url
    scheme_end += 3
    at = url.find("@", scheme_end)
    if at < 0:
        return url
    colon = url.find(":", scheme_end)
    if colon < 0 or colon > at:
        return url
    return url[:colon] + url[at:]


def _find_git_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        raise click.ClickException(
            "etzhayyim database must be run inside the etzhayyim monorepo (no git root found)"
        )


def _validate_migrator_args(args: list[str]) -> None:
    if not args:
        return
    cmd = args[0]
    if cmd in ("latest", "up", "down", "list"):
        if len(args) > 1:
            raise click.ClickException(f"{cmd!r} takes no arguments, got {args[1:]}")
    elif cmd == "to":
        if len(args) < 2:
            raise click.ClickException("'to' requires a migration name (e.g. 'to 0005_vertex_gitrepo')")
    else:
        raise click.ClickException(
            f"unknown migrator subcommand {cmd!r} (want: latest, up, down, to <name>, list)"
        )


def _run_kysely_migrate(schema_dir: Path, db_url: str, migrator_args: list[str]) -> None:
    _validate_migrator_args(migrator_args)
    migrate_script = schema_dir / "scripts" / "migrate.ts"
    if not migrate_script.exists():
        raise click.ClickException(
            f"Kysely migrate runner not found at {migrate_script}"
        )
    node_args = ["node", "--loader=ts-node/esm", "scripts/migrate.ts"] + migrator_args
    env = {**os.environ, "DATABASE_URL": db_url}
    click.echo(f"etzhayyim database: {migrator_args[0] if migrator_args else 'latest'} → {_redact_url(db_url)}", err=True)
    result = subprocess.run(node_args, cwd=schema_dir, env=env)
    if result.returncode != 0:
        sys.exit(result.returncode)


def _list_graph_schema_migrations(schema_dir: Path) -> list[str]:
    migrations_dir = schema_dir / "migrations"
    if not migrations_dir.exists():
        return []
    names = [
        f.stem
        for f in sorted(migrations_dir.iterdir())
        if f.is_file() and f.suffix == ".ts"
    ]
    return sorted(names)


@click.group("database")
def database() -> None:
    """Database management (RisingWave). SSoT: 30-graph/graph-schema/migrations/*.ts"""


@database.command("status")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def db_status(pds: str | None, json_out: bool) -> None:
    """Database health (RisingWave + asyncpg)."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.database.getStatus",
            headers=_auth_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"database: {data.get('status', 'unknown')}")
            for k, v in data.items():
                if k != "status":
                    click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@database.command("tables")
@click.option("--pds", default=None)
@click.option("--schema", default="graphar", show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
def db_tables(pds: str | None, schema: str, json_out: bool) -> None:
    """List tables in a schema."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.database.listTables",
            params={"schema": schema},
            headers=_auth_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            tables = data if isinstance(data, list) else data.get("tables", [])
            for t in tables:
                name = t.get("name", t) if isinstance(t, dict) else str(t)
                click.echo(f"  {schema}.{name}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@database.command("migrate")
@click.argument("subcommand", default="latest")
@click.argument("migration_name", default="", required=False)
@click.option("--env", "env_name", default="local", show_default=True,
              help="Target environment: local or prod")
@click.option("--url", "url_flag", default="", help="Explicit PostgreSQL URL")
def db_migrate(subcommand: str, migration_name: str, env_name: str, url_flag: str) -> None:
    """Run Kysely migrations (shells out to 30-graph/graph-schema/scripts/migrate.ts).

    SUBCOMMAND: latest (default) | up | down | list | to <name>
    """
    db_url = _resolve_db_url(url_flag, env_name)
    migrator_args = [subcommand]
    if subcommand == "to":
        if not migration_name:
            raise click.ClickException("'to' requires a migration name")
        migrator_args.append(migration_name)
    elif migration_name:
        raise click.ClickException(f"{subcommand!r} takes no arguments")
    git_root = _find_git_root()
    schema_dir = git_root / _GRAPH_SCHEMA_REL
    _run_kysely_migrate(schema_dir, db_url, migrator_args)


@database.command("up")
@click.option("--env", "env_name", default="local", show_default=True,
              help="Target environment: local or prod")
@click.option("--url", "url_flag", default="", help="Explicit PostgreSQL URL")
def db_up(env_name: str, url_flag: str) -> None:
    """Bootstrap: migrate to latest (equivalent to: migrate latest)."""
    db_url = _resolve_db_url(url_flag, env_name)
    git_root = _find_git_root()
    schema_dir = git_root / _GRAPH_SCHEMA_REL
    _run_kysely_migrate(schema_dir, db_url, ["latest"])


@database.command("repair-order")
@click.option("--env", "env_name", default="local", show_default=True,
              help="Target environment: local or prod")
@click.option("--url", "url_flag", default="", help="Explicit PostgreSQL URL")
@click.option("--apply", is_flag=True, default=False,
              help="Apply repair (rewrite kysely_migration timestamps)")
@click.option("--json", "json_out", is_flag=True, default=False)
def db_repair_order(env_name: str, url_flag: str, apply: bool, json_out: bool) -> None:
    """Detect and repair out-of-order applied migrations / timestamp drift."""
    import psycopg
    db_url = _resolve_db_url(url_flag, env_name)
    git_root = _find_git_root()
    schema_dir = git_root / _GRAPH_SCHEMA_REL
    file_migrations = _list_graph_schema_migrations(schema_dir)

    try:
        with psycopg.connect(db_url, autocommit=True) as conn:
            conn.execute("SET RW_IMPLICIT_FLUSH = true")
            conn.execute("FLUSH")
            rows = conn.execute(
                "SELECT name, timestamp FROM kysely_migration ORDER BY timestamp, name"
            ).fetchall()
    except Exception as e:
        raise click.ClickException(f"DB connection failed: {e}")

    applied = [{"name": r[0].strip(), "timestamp": str(r[1]).strip()} for r in rows]
    if not applied:
        msg = {"status": "empty", "message": "kysely_migration is empty; nothing to repair"}
        if json_out:
            click.echo(json.dumps(msg))
        else:
            click.echo("kysely_migration is empty; nothing to repair")
        return

    applied_by_name = {r["name"]: r for r in applied}
    actual_applied = [r["name"] for r in applied]

    expected_applied = [n for n in file_migrations if n in applied_by_name]
    highest_applied_idx = max(
        (i for i, n in enumerate(file_migrations) if n in applied_by_name),
        default=-1,
    )
    missing_prefix = [
        n for n in file_migrations[:max(0, highest_applied_idx)]
        if n not in applied_by_name
    ]
    order_mismatch = expected_applied != actual_applied

    report: dict[str, Any] = {
        "db": _redact_url(db_url),
        "applied_count": len(applied),
        "highest_applied": actual_applied[-1] if actual_applied else "",
        "missing_prefix": missing_prefix,
        "order_mismatch": order_mismatch,
        "topology": "aligned" if not missing_prefix and not order_mismatch else "needs_repair",
    }

    if json_out:
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        click.echo(f"database topology check: {_redact_url(db_url)}")
        click.echo(f"  applied_count: {len(applied)}")
        click.echo(f"  highest_applied: {actual_applied[-1] if actual_applied else 'none'}")
        if missing_prefix:
            click.echo(f"  missing_prefix: {', '.join(missing_prefix)}")
        if order_mismatch:
            click.echo("  timestamp_order_mismatch: yes")

    if not missing_prefix and not order_mismatch:
        if not json_out:
            click.echo("  topology: already aligned")
        return

    if not apply:
        if not json_out:
            click.echo("  action: rerun with --apply to repair migration topology")
        return

    # Rewrite timestamps to canonical order
    import datetime
    try:
        base_ts = datetime.datetime(2026, 4, 13, tzinfo=datetime.timezone.utc)
        if applied:
            try:
                ts_str = applied_by_name.get(file_migrations[0], {}).get("timestamp", "")
                if ts_str:
                    base_ts = datetime.datetime.fromisoformat(ts_str)
            except Exception:
                pass

        all_applied = {**applied_by_name}
        for name in missing_prefix:
            all_applied[name] = {"name": name, "timestamp": ""}

        with psycopg.connect(db_url, autocommit=False) as conn:
            conn.execute("SET RW_IMPLICIT_FLUSH = true")
            idx = 0
            for name in file_migrations:
                if name not in all_applied:
                    continue
                ts = (base_ts + datetime.timedelta(seconds=idx)).isoformat()
                if name in missing_prefix:
                    conn.execute(
                        'INSERT INTO kysely_migration ("name", "timestamp") VALUES (%s, %s)',
                        (name, ts),
                    )
                    click.echo(f"  direct-apply: {name}")
                else:
                    conn.execute(
                        'UPDATE kysely_migration SET "timestamp" = %s WHERE "name" = %s',
                        (ts, name),
                    )
                idx += 1
            conn.commit()
            conn.execute("FLUSH")
    except Exception as e:
        raise click.ClickException(f"repair failed: {e}")

    click.echo("  topology: repaired")


@database.command("query")
@click.argument("sql")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def db_query(sql: str, pds: str | None, json_out: bool) -> None:
    """Run a read-only SQL query via XRPC."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.database.query",
            json={"sql": sql, "readOnly": True},
            headers=_auth_headers(),
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            rows = data if isinstance(data, list) else data.get("rows", [])
            for row in rows:
                click.echo(f"  {row}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")
