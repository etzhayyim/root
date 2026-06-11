"""metrics — BI metrics and telemetry commands."""

from __future__ import annotations

import json
import sys

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@click.group("metrics", invoke_without_command=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def metrics(ctx: click.Context, pds: str | None, json_out: bool) -> None:
    """BI metrics and telemetry (latency, error rate, throughput)."""
    if ctx.invoked_subcommand is not None:
        return
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.metrics.getSummary",
                         headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@metrics.command("latency")
@click.option("--pds", default=None)
@click.option("--window", default="1h", show_default=True, help="Time window (1h/24h/7d)")
@click.option("--json", "json_out", is_flag=True, default=False)
def metrics_latency(pds: str | None, window: str, json_out: bool) -> None:
    """Latency percentiles (p50/p95/p99)."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.metrics.getLatency",
                         params={"window": window}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"latency ({window}):")
            for k, v in data.items():
                click.echo(f"  {k}: {v}ms")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@metrics.command("throughput")
@click.option("--pds", default=None)
@click.option("--window", default="1h", show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
def metrics_throughput(pds: str | None, window: str, json_out: bool) -> None:
    """Request throughput (RPS)."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.metrics.getThroughput",
                         params={"window": window}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@metrics.command("errors")
@click.option("--pds", default=None)
@click.option("--window", default="1h", show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
def metrics_errors(pds: str | None, window: str, json_out: bool) -> None:
    """Error rate and top error NSIDs."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.metrics.getErrorRate",
                         params={"window": window}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")
