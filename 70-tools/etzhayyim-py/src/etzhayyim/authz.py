"""authz — Authorization commands: API keys, DIDs, role management.

API key operations call the PDS XRPC endpoint.
Local DID list and switch work via ~/.etzhayyim/auth.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds


_AUTH_FILE = Path.home() / ".etzhayyim" / "auth.json"


def _token() -> str:
    return _load_auth().get("accessJwt") or _load_auth().get("access_token") or ""


def _headers() -> dict:
    tok = _token()
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@click.group("authz")
def authz() -> None:
    """Authorization: API keys, DID list, role management."""


@authz.command("create-api-key")
@click.option("--pds", default=None)
@click.option("--name", default="default", help="key name")
@click.option("--label", default="", help="Human-readable label for this key")
@click.option("--scopes", default="read,write", show_default=True)
@click.option("--test", "is_test", is_flag=True, default=False, help="issue sk_test_ instead of sk_live_")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("-q", "quiet", is_flag=True, default=False, help="print key only (for scripting)")
def authz_create_api_key(
    pds: str | None, name: str, label: str, scopes: str, is_test: bool, json_out: bool, quiet: bool
) -> None:
    """Create a new API key."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    payload = {"name": name, "label": label, "scopes": scopes, "test": is_test}
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.auth.createApiKey",
            json=payload, headers=_headers(), timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        key = data.get("key", data.get("apiKey", ""))
        if quiet:
            click.echo(key)
        elif json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"api-key: {key}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@authz.command("list-api-keys")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def authz_list_api_keys(pds: str | None, json_out: bool) -> None:
    """List active API keys."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.authz.listApiKeys",
            headers=_headers(), timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            keys = data if isinstance(data, list) else data.get("keys", [])
            for k in keys:
                click.echo(f"  {k.get('id', '')}  {k.get('label', '')}  {k.get('scopes', '')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@authz.command("revoke-api-key")
@click.argument("key_id")
@click.option("--pds", default=None)
def authz_revoke_api_key(key_id: str, pds: str | None) -> None:
    """Revoke an API key by ID."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.authz.revokeApiKey",
            json={"id": key_id}, headers=_headers(), timeout=30,
        )
        resp.raise_for_status()
        click.echo(f"revoked: {key_id}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@authz.command("dids")
@click.option("--json", "json_out", is_flag=True, default=False)
def authz_dids(json_out: bool) -> None:
    """List DIDs controlled by the current auth identity."""
    auth = _load_auth()
    if not auth:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    dids: list[str] = auth.get("controlledDids") or []
    primary = auth.get("did", "")
    if primary and primary not in dids:
        dids = [primary] + dids
    if json_out:
        click.echo(json.dumps({"dids": dids}, ensure_ascii=False, indent=2))
    else:
        for d in dids:
            marker = " (active)" if d == primary else ""
            click.echo(f"  {d}{marker}")


@authz.command("switch")
@click.argument("did")
def authz_switch(did: str) -> None:
    """Switch the active DID in local auth state."""
    if not _AUTH_FILE.exists():
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    try:
        auth = json.loads(_AUTH_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        click.echo("corrupt auth file", err=True)
        sys.exit(1)
    auth["did"] = did
    _AUTH_FILE.write_text(json.dumps(auth, ensure_ascii=False, indent=2))
    click.echo(f"switched to: {did}")
