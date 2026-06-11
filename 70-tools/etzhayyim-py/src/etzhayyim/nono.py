"""nono — Nono capability worker lifecycle management.

Nono workers provide NSID-bound capability primitives.
Reads nono-manifest.jsonld files from workspace.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds
from .shannon import _resolve_root


@dataclass
class NonoManifest:
    nanoid: str
    name: str
    bindings: list[str] = field(default_factory=list)
    skills: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"nanoid": self.nanoid, "name": self.name,
                "bindings": self.bindings, "skills": self.skills}


def _load_manifests(ws: Path) -> list[NonoManifest]:
    manifests = []
    for p in ws.rglob("nono-manifest.jsonld"):
        try:
            data = json.loads(p.read_text(errors="replace"))
        except (OSError, json.JSONDecodeError):
            continue
        nanoid = data.get("nanoid", "")
        if nanoid:
            manifests.append(NonoManifest(
                nanoid=nanoid,
                name=data.get("name", ""),
                bindings=data.get("bindings", []),
                skills=data.get("skills", []),
            ))
    return manifests


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@click.group("nono", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def nono(ctx: click.Context, workspace_dir: str | None, json_out: bool) -> None:
    """Nono capability worker lifecycle management."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    manifests = _load_manifests(ws)
    if json_out:
        click.echo(json.dumps([m.to_dict() for m in manifests], ensure_ascii=False, indent=2))
    else:
        click.echo(f"nono workers: {len(manifests)}")
        for m in manifests:
            click.echo(f"  {m.nanoid}  {m.name}  skills={len(m.skills)}")


@nono.command("list")
@click.option("--workspace-dir", default=None)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def nono_list(workspace_dir: str | None, pds: str | None, json_out: bool) -> None:
    """List nono workers (local manifests + remote registry)."""
    ws = _resolve_root(workspace_dir)
    local = _load_manifests(ws)
    if json_out:
        click.echo(json.dumps([m.to_dict() for m in local], ensure_ascii=False, indent=2))
    else:
        for m in local:
            click.echo(f"  {m.nanoid}  {m.name}  bindings={','.join(m.bindings[:3])}")


@nono.command("inspect")
@click.argument("nanoid")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def nono_inspect(nanoid: str, workspace_dir: str | None, json_out: bool) -> None:
    """Inspect a nono worker manifest."""
    ws = _resolve_root(workspace_dir)
    manifests = _load_manifests(ws)
    found = next((m for m in manifests if m.nanoid == nanoid), None)
    if not found:
        raise click.ClickException(f"nono manifest not found: {nanoid}")
    if json_out:
        click.echo(json.dumps(found.to_dict(), ensure_ascii=False, indent=2))
    else:
        click.echo(f"nanoid: {found.nanoid}")
        click.echo(f"name: {found.name}")
        click.echo(f"bindings: {found.bindings}")
        for s in found.skills:
            click.echo(f"  skill: {s.get('nsid', '')}  {s.get('description', '')[:60]}")


@nono.command("build")
@click.argument("nanoid", required=False, default=None)
@click.option("--dir", "comp_dir", default=None,
              help="Component directory (default: search workspace for nanoid)")
@click.option("--workspace-dir", default=None)
@click.option("--dry-run", is_flag=True, default=False)
def nono_build(nanoid: str | None, comp_dir: str | None,
               workspace_dir: str | None, dry_run: bool) -> None:
    """Build a nono worker (esbuild + validation)."""
    import subprocess

    # Resolve component directory
    if comp_dir:
        target_dir = Path(comp_dir).resolve()
    elif nanoid:
        ws = _resolve_root(workspace_dir)
        target_dir = None
        for manifest_path in ws.rglob("nono-manifest.jsonld"):
            try:
                data = json.loads(manifest_path.read_text(errors="replace"))
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("nanoid") == nanoid:
                target_dir = manifest_path.parent
                break
        if target_dir is None:
            if dry_run:
                click.echo(f"[nono build] dry-run: {nanoid}  (nono not found in workspace)")
                return
            raise click.ClickException(
                f"nono not found: {nanoid}. Use --dir to specify the component directory.")
    else:
        target_dir = Path.cwd()

    wrangler_jsonc = target_dir / "wrangler.jsonc"
    pkg = target_dir / "package.json"

    if dry_run:
        click.echo(f"[nono build] dry-run: {nanoid or target_dir.name}")
        click.echo(f"  dir: {target_dir}")
        click.echo(f"  wrangler.jsonc: {'found' if wrangler_jsonc.exists() else 'missing'}")
        click.echo(f"  package.json: {'found' if pkg.exists() else 'missing'}")
        return

    click.echo(f"[nono build] Building {nanoid or target_dir.name}...")
    # Use npm/pnpm build if package.json exists, otherwise fall back to wrangler
    build_cmd = None
    if pkg.exists():
        pkg_data = json.loads(pkg.read_text(errors="replace"))
        if "build" in pkg_data.get("scripts", {}):
            build_cmd = ["pnpm", "run", "build"] if (target_dir / "pnpm-lock.yaml").exists() \
                        else ["npm", "run", "build"]
    if build_cmd is None and wrangler_jsonc.exists():
        build_cmd = ["npx", "wrangler", "deploy", "--dry-run", "--outdir", "dist"]
    if build_cmd is None:
        raise click.ClickException(
            f"no package.json scripts.build or wrangler.jsonc found in {target_dir}")

    r = subprocess.run(build_cmd, cwd=str(target_dir))
    if r.returncode != 0:
        raise click.ClickException(f"build failed (exit {r.returncode})")
    click.echo(f"[nono build] Complete: {target_dir.name}")


@nono.command("deploy")
@click.argument("nanoid")
@click.option("--dir", "comp_dir", default=None,
              help="Component directory (default: search workspace for nanoid)")
@click.option("--pds", default=None)
@click.option("--skip-skills", is_flag=True, default=False,
              help="Skip XRPC skill registration after deploy")
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
def nono_deploy(nanoid: str, comp_dir: str | None, pds: str | None,
                skip_skills: bool, dry_run: bool, workspace_dir: str | None) -> None:
    """Deploy a nono worker (wrangler deploy + XRPC skill registration)."""
    import subprocess

    # Resolve component directory
    if comp_dir:
        target_dir = Path(comp_dir).resolve()
    else:
        # Search workspace for wrangler.jsonc near a nono-manifest with matching nanoid
        ws = _resolve_root(workspace_dir)
        target_dir = None
        for manifest_path in ws.rglob("nono-manifest.jsonld"):
            try:
                data = json.loads(manifest_path.read_text(errors="replace"))
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("nanoid") == nanoid:
                target_dir = manifest_path.parent
                break
        if target_dir is None:
            # Fall back to searching by wrangler.jsonc dir that contains nanoid in name
            for wp in ws.rglob("wrangler.jsonc"):
                if nanoid in wp.parent.name:
                    target_dir = wp.parent
                    break
        if target_dir is None:
            if dry_run:
                click.echo(f"[nono deploy] dry-run: {nanoid}  (nono not found in workspace)")
                return
            raise click.ClickException(
                f"nono not found: {nanoid}. Use --dir to specify the component directory."
            )

    wrangler_jsonc = target_dir / "wrangler.jsonc"
    manifest_path = target_dir / "nono-manifest.jsonld"

    if dry_run:
        click.echo(f"[nono deploy] dry-run: {nanoid}")
        click.echo(f"  dir: {target_dir}")
        click.echo(f"  wrangler.jsonc: {'found' if wrangler_jsonc.exists() else 'missing'}")
        click.echo(f"  nono-manifest.jsonld: {'found' if manifest_path.exists() else 'missing'}")
        return

    # Phase 1: wrangler deploy
    click.echo(f"[nono deploy] Phase 1: Worker deploy  nanoid={nanoid}")
    if not wrangler_jsonc.exists():
        raise click.ClickException(f"wrangler.jsonc not found in {target_dir}")

    r = subprocess.run(["npx", "wrangler", "deploy"], cwd=str(target_dir))
    if r.returncode != 0:
        raise click.ClickException(f"wrangler deploy failed (exit {r.returncode})")

    if skip_skills:
        click.echo("\n[nono deploy] Skill registration skipped (--skip-skills)")
        return

    # Phase 2: XRPC skill registration
    click.echo("\n[nono deploy] Phase 2: Skill registration")
    if not manifest_path.exists():
        click.echo("  no nono-manifest.jsonld — skill registration skipped")
        click.echo("  skills are auto-discovered from sdk.app.command() via MCP tools/list")
        return

    try:
        nm_data = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        click.echo(f"  parse nono-manifest.jsonld failed: {e}", err=True)
        return

    auth = _load_auth()
    token = auth.get("accessJwt") or auth.get("access_token") or ""
    if not token:
        click.echo("  no auth token — skill registration requires authentication")
        return

    pds_url = (pds or resolve_pds()).rstrip("/")
    reg_body = {
        "@context": "https://etzhayyim.com/ns/nono/v1",
        "@id": nm_data.get("@id", ""),
        "name": nm_data.get("name", ""),
        "nanoid": nm_data.get("nanoid", nanoid),
        "type": "nono",
        "bindings": nm_data.get("bindings", []),
        "primitiveBackend": nm_data.get("primitiveBackend", []),
        "skills": nm_data.get("skills", []),
        "status": "active",
    }
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.actor.registerManifest",
            json=reg_body,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
        if resp.status_code >= 400:
            click.echo(f"  skill registration HTTP {resp.status_code}")
        else:
            bindings = nm_data.get("bindings", [])
            skills = nm_data.get("skills", [])
            click.echo(f"  ✓ nono registered: {nm_data.get('name', nanoid)} "
                       f"({len(bindings)} bindings, {len(skills)} skills)")
    except httpx.HTTPError as e:
        click.echo(f"  skill registration failed: {e}", err=True)

    click.echo(f"\n[nono deploy] Complete: {nm_data.get('name', nanoid)} deployed as capability Worker")


@nono.command("skills")
@click.argument("nanoid")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def nono_skills(nanoid: str, workspace_dir: str | None, json_out: bool) -> None:
    """List skills of a nono worker."""
    ws = _resolve_root(workspace_dir)
    manifests = _load_manifests(ws)
    found = next((m for m in manifests if m.nanoid == nanoid), None)
    if not found:
        raise click.ClickException(f"nono manifest not found: {nanoid}")
    if json_out:
        click.echo(json.dumps(found.skills, ensure_ascii=False, indent=2))
    else:
        for s in found.skills:
            click.echo(f"  {s.get('nsid', '')}  {s.get('description', '')[:60]}")
