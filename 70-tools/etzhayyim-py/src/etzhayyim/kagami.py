"""kagami (鏡) — Mirror/diff analysis between workspace state and deployed state.

Compares local magatama.jsonld definitions against the live PDS registry.
Shows drift between local and deployed actors.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import click
import httpx

from .authn import _load_auth
from .haisen import _read_jsonld
from .projector import resolve_pds
from .shannon import _resolve_root


@dataclass
class KagamiDiff:
    nanoid: str
    status: str  # added / removed / changed / ok
    local: dict = field(default_factory=dict)
    remote: dict = field(default_factory=dict)
    changes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nanoid": self.nanoid,
            "status": self.status,
            "changes": self.changes,
        }


def _load_local_actors(ws: Path) -> dict[str, dict]:
    projects_dir = ws / "60-apps"
    if not projects_dir.exists():
        projects_dir = ws / "projects"
    if not projects_dir.exists():
        return {}
    actors = {}
    for jsonld in projects_dir.rglob("magatama.jsonld"):
        data = _read_jsonld(jsonld)
        nanoid = data.get("nanoid", "")
        if nanoid:
            actors[nanoid] = data
    return actors


def _compare(local: dict, remote: dict) -> list[str]:
    changes = []
    for key in ("name", "did", "performerType", "uiType", "runtimeType"):
        lv = local.get(key, "")
        rv = remote.get(key, "")
        if lv != rv:
            changes.append(f"{key}: {lv!r} → {rv!r}")
    local_cols = set(local.get("collections", []))
    remote_cols = set(remote.get("collections", []))
    added = remote_cols - local_cols
    removed = local_cols - remote_cols
    if added:
        changes.append(f"collections +{len(added)}: {', '.join(sorted(added)[:3])}")
    if removed:
        changes.append(f"collections -{len(removed)}: {', '.join(sorted(removed)[:3])}")
    return changes


@click.group("kagami", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def kagami(ctx: click.Context, workspace_dir: str | None, pds: str | None, json_out: bool) -> None:
    """Mirror analysis: local vs deployed actor state."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    local = _load_local_actors(ws)
    click.echo(f"kagami (鏡): {len(local)} local actors")
    click.echo("  Use 'kagami diff' to compare with deployed state (requires auth)")


@kagami.command("diff")
@click.option("--workspace-dir", default=None)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def kagami_diff(workspace_dir: str | None, pds: str | None, json_out: bool) -> None:
    """Diff local actor definitions against the PDS registry."""
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)

    ws = _resolve_root(workspace_dir)
    local = _load_local_actors(ws)
    pds_url = (pds or resolve_pds()).rstrip("/")

    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.actor.listActors",
            params={"limit": 500},
            headers={"Authorization": f"Bearer {tok}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        remote_list = data if isinstance(data, list) else data.get("actors", [])
        remote = {a["nanoid"]: a for a in remote_list if a.get("nanoid")}
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")

    diffs: list[KagamiDiff] = []
    for nanoid, ldata in local.items():
        if nanoid not in remote:
            diffs.append(KagamiDiff(nanoid=nanoid, status="local-only", local=ldata))
        else:
            changes = _compare(ldata, remote[nanoid])
            status = "changed" if changes else "ok"
            diffs.append(KagamiDiff(nanoid=nanoid, status=status, local=ldata,
                                    remote=remote[nanoid], changes=changes))
    for nanoid, rdata in remote.items():
        if nanoid not in local:
            diffs.append(KagamiDiff(nanoid=nanoid, status="remote-only", remote=rdata))

    if json_out:
        click.echo(json.dumps([d.to_dict() for d in diffs], ensure_ascii=False, indent=2))
    else:
        changed = [d for d in diffs if d.status != "ok"]
        click.echo(f"kagami diff: {len(diffs)} actors  {len(changed)} with drift")
        for d in changed:
            click.echo(f"  [{d.status:12}] {d.nanoid}")
            for c in d.changes[:3]:
                click.echo(f"    {c}")


@kagami.command("local")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def kagami_local(workspace_dir: str | None, json_out: bool) -> None:
    """List local actor definitions."""
    ws = _resolve_root(workspace_dir)
    local = _load_local_actors(ws)
    if json_out:
        click.echo(json.dumps(list(local.values()), ensure_ascii=False, indent=2))
    else:
        for nanoid, data in sorted(local.items()):
            click.echo(f"  {nanoid}  {data.get('name', '')}  [{data.get('performerType', '')}]")
