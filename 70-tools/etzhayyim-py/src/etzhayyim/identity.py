"""identity — Identity management (DID, handle, migration paths)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

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


@click.group("identity")
def identity() -> None:
    """Identity management (DID resolution, handle updates, migration)."""


@identity.command("resolve")
@click.argument("handle_or_did")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def identity_resolve(handle_or_did: str, pds: str | None, json_out: bool) -> None:
    """Resolve a handle to a DID or inspect a DID document."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    if handle_or_did.startswith("did:"):
        endpoint = f"{pds_url}/xrpc/com.atproto.repo.describeRepo"
        params = {"repo": handle_or_did}
    else:
        endpoint = f"{pds_url}/xrpc/com.atproto.identity.resolveHandle"
        params = {"handle": handle_or_did}
    try:
        resp = httpx.get(endpoint, params=params,
                         headers=_auth_headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"resolve error: {e}")


@identity.command("update-handle")
@click.argument("new_handle")
@click.option("--pds", default=None)
def identity_update_handle(new_handle: str, pds: str | None) -> None:
    """Update the handle for the current DID."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.atproto.identity.updateHandle",
            json={"handle": new_handle},
            headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        click.echo(f"handle updated: {new_handle}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@identity.command("migrate")
@click.option("--from-pds", required=True, help="Source PDS URL")
@click.option("--to-pds", required=True, help="Target PDS URL")
@click.option("--dry-run", is_flag=True, default=False)
def identity_migrate(from_pds: str, to_pds: str, dry_run: bool) -> None:
    """Migrate identity between PDS instances (full migration requires Go binary)."""
    if not dry_run:
        click.echo(
            "etzhayyim identity migrate requires the Go binary. Run: etzhayyim identity migrate",
            err=True,
        )
        sys.exit(1)
    click.echo(f"identity migrate (dry-run): {from_pds} → {to_pds}")


@identity.command("migrate-paths")
@click.option("--source", default="legacy-nanoids",
              type=click.Choice(["legacy-nanoids"]), show_default=True,
              help="Source of DIDs to migrate")
@click.option("--apply", is_flag=True, default=False,
              help="Actually submit to PDS (default: dry-run)")
@click.option("--limit", default=0, type=int,
              help="Max entries to process (0 = all)")
@click.option("--filter", "name_filter", default="",
              help="Filter by actor name substring")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--deps", "deps_path", default="deps.toml")
def identity_migrate_paths(
    source: str, apply: bool, limit: int, name_filter: str,
    pds: str | None, json_out: bool, deps_path: str,
) -> None:
    """Migrate path DIDs (legacy-nanoids) to did:etzhayyim via PDS XRPC com.etzhayyim.identity.submitOp."""
    import subprocess
    import hashlib
    import base64

    pds_url = (pds or resolve_pds()).rstrip("/")

    # locate deps.toml — only fall back to git root if default path was requested
    deps_file = Path(deps_path)
    if not deps_file.exists() and deps_path == "deps.toml":
        try:
            root = Path(subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True,
            ).strip())
            deps_file = root / "deps.toml"
        except subprocess.CalledProcessError:
            pass

    entries: list[dict] = []
    if deps_file.exists():
        try:
            import tomllib  # type: ignore[import]
        except ImportError:
            try:
                import tomli as tomllib  # type: ignore[no-redef,import]
            except ImportError:
                tomllib = None  # type: ignore[assignment]

        if tomllib is not None:
            with open(deps_file, "rb") as fh:
                data = tomllib.load(fh)
            for item in data.get("legacy_nanoids", []):
                name = item.get("name", "")
                if name_filter and name_filter not in name:
                    continue
                entries.append(item)

    if not entries:
        click.echo("no legacy_nanoids entries found in deps.toml", err=True)
        sys.exit(1)

    if limit > 0:
        entries = entries[:limit]

    def _compute_path_did(nanoid: str) -> str:
        payload = json.dumps({"type": "path-did-genesis", "nanoid": nanoid}).encode()
        digest = hashlib.sha256(payload).digest()
        b32 = base64.b32encode(digest).decode().lower().rstrip("=")
        return f"did:etzhayyim:{b32[:24]}"

    results = []
    for entry in entries:
        nanoid = entry.get("nanoid", "")
        name = entry.get("name", "")
        path_did = _compute_path_did(nanoid)

        if not apply:
            results.append({"nanoid": nanoid, "name": name, "pathDid": path_did, "submitted": False})
            continue

        try:
            resp = httpx.post(
                f"{pds_url}/xrpc/com.etzhayyim.identity.submitOp",
                json={"nanoid": nanoid, "pathDid": path_did, "dryRun": False},
                headers=_auth_headers(),
                timeout=30,
            )
            resp.raise_for_status()
            results.append({"nanoid": nanoid, "name": name, "pathDid": path_did,
                            "submitted": True, "response": resp.json()})
        except httpx.HTTPError as e:
            results.append({"nanoid": nanoid, "name": name, "pathDid": path_did,
                            "submitted": False, "error": str(e)})

    if json_out:
        click.echo(json.dumps({"dryRun": not apply, "results": results}, indent=2))
    else:
        mode = "apply" if apply else "dry-run"
        click.echo(f"identity migrate-paths [{mode}]  entries={len(results)}")
        for r in results:
            status = "✓" if r.get("submitted") else ("!" if r.get("error") else "○")
            click.echo(f"  {status} {r['name']:<25} {r['nanoid']:<15} → {r['pathDid']}")


@identity.command("audit")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def identity_audit(pds: str | None, json_out: bool) -> None:
    """Audit all controlled identities for consistency."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.identity.auditIdentities",
            headers=_auth_headers(), timeout=60,
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
