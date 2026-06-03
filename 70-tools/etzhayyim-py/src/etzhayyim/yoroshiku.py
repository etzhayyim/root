"""yoroshiku (よろしく) — Onboarding and workspace welcome commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds
from .shannon import _resolve_root


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@click.group("yoroshiku", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def yoroshiku(ctx: click.Context, workspace_dir: str | None, json_out: bool) -> None:
    """Onboarding (よろしく): workspace welcome, readiness check."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    checks = _run_readiness(ws)
    passing = sum(1 for c in checks if c["ok"])
    if json_out:
        click.echo(json.dumps({"passing": passing, "total": len(checks), "checks": checks},
                              ensure_ascii=False, indent=2))
    else:
        click.echo(f"yoroshiku (よろしく): {passing}/{len(checks)} checks passing")
        for c in checks:
            status = "OK  " if c["ok"] else "WARN"
            click.echo(f"  [{status}] {c['name']}  {c['detail']}")


def _run_readiness(ws: Path) -> list[dict]:
    checks = []

    # Check deps.toml
    checks.append({
        "name": "deps.toml",
        "ok": (ws / "deps.toml").exists(),
        "detail": "deps.toml found" if (ws / "deps.toml").exists() else "deps.toml missing",
    })

    # Check CLAUDE.md
    checks.append({
        "name": "CLAUDE.md",
        "ok": (ws / "CLAUDE.md").exists(),
        "detail": "CLAUDE.md found" if (ws / "CLAUDE.md").exists() else "CLAUDE.md missing",
    })

    # Check 60-apps directory
    apps_dir = ws / "60-apps"
    checks.append({
        "name": "60-apps",
        "ok": apps_dir.exists(),
        "detail": f"{len(list(apps_dir.rglob('magatama.jsonld')))} apps" if apps_dir.exists() else "missing",
    })

    # Check auth
    auth_file = Path.home() / ".etzhayyim" / "auth.json"
    checks.append({
        "name": "authn",
        "ok": auth_file.exists(),
        "detail": "signed in" if auth_file.exists() else "not signed in",
    })

    return checks


@yoroshiku.command("check")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def yoroshiku_check(workspace_dir: str | None, json_out: bool) -> None:
    """Run workspace readiness checks."""
    ws = _resolve_root(workspace_dir)
    checks = _run_readiness(ws)
    if json_out:
        click.echo(json.dumps(checks, ensure_ascii=False, indent=2))
    else:
        for c in checks:
            status = "OK  " if c["ok"] else "WARN"
            click.echo(f"  [{status}] {c['name']}  {c['detail']}")


@yoroshiku.command("register")
@click.option("--pds", default=None)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def yoroshiku_register(pds: str | None, workspace_dir: str | None, json_out: bool) -> None:
    """Register this workspace with the platform."""
    ws = _resolve_root(workspace_dir)
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.yoroshiku.registerWorkspace",
            json={"workspace": str(ws)},
            headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"registered workspace: {data.get('id', '')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")
