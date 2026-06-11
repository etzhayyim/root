"""mitama — Actor manifest management (register, list, inspect, shinka).

Registers kotodama.jsonld to the graph via PDS Shared Executor.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import httpx

from .authn import _load_auth
from .haisen import _read_jsonld
from .projector import resolve_pds
from .shannon import _resolve_root


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@click.group("mitama", invoke_without_command=True)
@click.option("--dir", "app_dir", default=None, help="App dir with kotodama.jsonld")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def mitama(ctx: click.Context, app_dir: str | None, pds: str | None, json_out: bool) -> None:
    """Mitama actor manifest management (register, list, inspect, shinka)."""
    if ctx.invoked_subcommand is not None:
        return
    if app_dir is None:
        click.echo("Usage: etzhayyim mitama [--dir <path>] or etzhayyim mitama <subcommand>", err=True)
        sys.exit(1)
    _do_register(Path(app_dir), pds, json_out)


def _do_register(app_dir: Path, pds: str | None, json_out: bool) -> None:
    jsonld_path = app_dir / "kotodama.jsonld"
    if not jsonld_path.exists():
        raise click.ClickException(f"kotodama.jsonld not found in {app_dir}")
    data = _read_jsonld(jsonld_path)
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.actor.register",
            json=data, headers=_auth_headers(), timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        if json_out:
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            click.echo(f"registered: {data.get('nanoid', '')}  {data.get('name', '')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@mitama.command("register")
@click.option("--dir", "app_dir", default=".", help="App dir with kotodama.jsonld")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def mitama_register(app_dir: str, pds: str | None, json_out: bool) -> None:
    """Register actor manifest to the graph."""
    _do_register(Path(app_dir), pds, json_out)


@mitama.command("list")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--limit", default=100, type=int, show_default=True)
def mitama_list(pds: str | None, json_out: bool, limit: int) -> None:
    """List all T1 actors in the graph."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.actor.listActors",
            params={"limit": limit}, headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            actors = data if isinstance(data, list) else data.get("actors", [])
            for a in actors:
                click.echo(f"  {a.get('nanoid', '')}  {a.get('name', '')}  "
                           f"[{a.get('performerType', '')}]  {a.get('status', '')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@mitama.command("inspect")
@click.argument("did_or_nanoid")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def mitama_inspect(did_or_nanoid: str, pds: str | None, json_out: bool) -> None:
    """Inspect actor manifest."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.actor.getActor",
            params={"id": did_or_nanoid}, headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@mitama.command("dormant")
@click.argument("did_or_nanoid")
@click.option("--pds", default=None)
def mitama_dormant(did_or_nanoid: str, pds: str | None) -> None:
    """Set actor status to dormant."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.actor.setStatus",
            json={"id": did_or_nanoid, "status": "dormant"},
            headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        click.echo(f"dormant: {did_or_nanoid}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@mitama.command("revive")
@click.argument("did_or_nanoid")
@click.option("--pds", default=None)
def mitama_revive(did_or_nanoid: str, pds: str | None) -> None:
    """Set actor status to active."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.actor.setStatus",
            json={"id": did_or_nanoid, "status": "active"},
            headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        click.echo(f"revived: {did_or_nanoid}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@mitama.command("shinka")
@click.option("--pds", default=None)
@click.option("--model", default="", help="Override model")
@click.option("--json", "json_out", is_flag=True, default=False)
def mitama_shinka(pds: str | None, model: str, json_out: bool) -> None:
    """Run shinka (coverage gap fill + actor knowledge update)."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    payload: dict = {}
    if model:
        payload["model"] = model
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.actor.shinka",
            json=payload, headers=_auth_headers(), timeout=300,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"shinka: healed={data.get('healed', '?')}  total={data.get('total', '?')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@mitama.command("schema-status")
@click.option("--table", default="vertex_actor_manifest", show_default=True,
              help="table name filter")
@click.option("--all", "all_tables", is_flag=True, default=False,
              help="query all tables (can be slow)")
@click.option("--state", default="", help="state filter (e.g. RUNNING, FINISHED, CANCELLED)")
@click.option("--pds", default=None)
@click.option("--timeout", "timeout_sec", default=60, type=int, show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
def mitama_schema_status(table: str, all_tables: bool, state: str, pds: str | None,
                         timeout_sec: int, json_out: bool) -> None:
    """Show Kotoba/Datomic ALTER TABLE COLUMN status for graphar tables."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    stmt = "SHOW ALTER TABLE COLUMN FROM graphar"
    where_clauses: list[str] = []
    if not all_tables and table.strip():
        safe_table = table.strip().replace("'", "''")
        where_clauses.append(f"TableName = '{safe_table}'")
    if state.strip():
        safe_state = state.strip().upper().replace("'", "''")
        where_clauses.append(f"State = '{safe_state}'")
    if where_clauses:
        stmt += " WHERE " + " AND ".join(where_clauses)

    timeout_ms = max(1000, min(60000, timeout_sec * 1000))
    payload = {"statement": stmt, "params": {}, "timeoutMs": timeout_ms}
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.kagami.sql",
            json=payload, headers=_auth_headers(), timeout=timeout_sec,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            rows = data if isinstance(data, list) else data.get("rows", [data])
            click.echo(f"schema-status: {len(rows)} rows  stmt={stmt!r}")
            for row in rows[:50]:
                click.echo(f"  {row}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")
