"""workspace — Workspace-level utilities.

sync: rsync workspace to a remote host over SSH.
"""

from __future__ import annotations

import subprocess
import sys

import click

from .shannon import _resolve_root


@click.group("workspace")
def workspace() -> None:
    """Workspace-level utilities (sync, status)."""


@workspace.command("sync")
@click.option("--remote", required=True, help="user@host:/path target")
@click.option("--workspace-dir", default=None)
@click.option("--exclude", multiple=True, default=("node_modules", ".git", "__pycache__",
                                                     ".venv", "dist", "build"),
              show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--delete", is_flag=True, default=False, help="Delete remote files not in local")
def workspace_sync(remote: str, workspace_dir: str | None, exclude: tuple[str, ...],
                   dry_run: bool, delete: bool) -> None:
    """Sync workspace to remote host via rsync over SSH."""
    ws = _resolve_root(workspace_dir)
    cmd = ["rsync", "-avz", "--progress"]
    for ex in exclude:
        cmd += ["--exclude", ex]
    if dry_run:
        cmd.append("--dry-run")
    if delete:
        cmd.append("--delete")
    cmd += [str(ws) + "/", remote]
    click.echo(f"rsync: {ws} → {remote}" + (" (dry-run)" if dry_run else ""))
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except FileNotFoundError:
        raise click.ClickException("rsync not found — install rsync")


@workspace.command("status")
@click.option("--workspace-dir", default=None)
def workspace_status(workspace_dir: str | None) -> None:
    """Show workspace root and basic stats."""
    ws = _resolve_root(workspace_dir)
    apps_dir = ws / "60-apps"
    actor_count = len(list(apps_dir.rglob("kotodama.jsonld"))) if apps_dir.exists() else 0
    click.echo(f"workspace: {ws}")
    click.echo(f"  actors: {actor_count}")
