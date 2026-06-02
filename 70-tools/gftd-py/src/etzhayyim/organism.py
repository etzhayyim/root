"""organism — Artificial Organism status (ADR public organism status worker)."""

from __future__ import annotations

import json
import sys

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds


def _headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    h = {"Content-Type": "application/json"}
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


@click.group("organism", invoke_without_command=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def organism(ctx: click.Context, pds: str | None, json_out: bool) -> None:
    """Artificial Organism public status."""
    if ctx.invoked_subcommand is not None:
        return
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.organism.getStatus",
                         headers=_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"organism: {data.get('status', 'unknown')}  "
                       f"actors={data.get('actorCount', '?')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@organism.command("status")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def organism_status(pds: str | None, json_out: bool) -> None:
    """Get organism status."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.organism.getStatus",
                         headers=_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"status: {data.get('status', 'unknown')}")
            for k, v in data.items():
                if k != "status":
                    click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@organism.command("list")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def organism_list(pds: str | None, json_out: bool) -> None:
    """List all organism actors."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.organism.listActors",
                         headers=_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            actors = data if isinstance(data, list) else data.get("actors", [])
            for a in actors:
                click.echo(f"  {a.get('nanoid', '')}  {a.get('name', '')}  {a.get('status', '')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")
