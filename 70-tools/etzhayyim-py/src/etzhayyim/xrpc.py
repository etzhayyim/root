"""etzhayyim xrpc — port of xrpc.go (ADR-2605151500).

Invoke any XRPC endpoint on an App or PDS.
Auto-routes com.etzhayyim.apps.{slug}.* NSIDs to the correct nanoid worker.
Scoped-JWT auto-wrap: uses com.atproto.server.getServiceAuth for each NSID call.
"""

import json as _json_mod
import sys

import click
import httpx

from .auth import auth_headers, scoped_auth_headers, resolve_pds

_KNOWN_APPS: dict[str, str] = {
    "media_gamers": "a7m8oocs",
    "media_anime": "animegr01",
    "autorace": "q7v8yed1k",
    "keirin": "k31r1njp",
    "kyotei": "qv8yed1k",
    "handotai": "dtyy44cr",
    "hanrei": "h4nr31jp",
    "kakaku": "k4k4kux1",
    "gtin": "gt1n4k7m",
}

_APP_HOST_TEMPLATE = "https://{nanoid}.com.etzhayyim.com"


def _resolve_base(nsid: str, app: str | None, url: str | None) -> str:
    if url:
        return url.rstrip("/")
    if app:
        return _APP_HOST_TEMPLATE.format(nanoid=app)
    # NSID inference: com.etzhayyim.apps.<slug>.*
    parts = nsid.split(".")
    if len(parts) >= 4 and parts[:3] == ["com", "etzhayyim", "apps"]:
        slug = parts[3]
        if nanoid := _KNOWN_APPS.get(slug):
            return _APP_HOST_TEMPLATE.format(nanoid=nanoid)
    return resolve_pds()


@click.command("xrpc")
@click.argument("nsid")
@click.option("-d", "--data", "data_json", default=None, help="JSON body (POST) or query params (GET).")
@click.option("--app", default=None, help="Nanoid of target App Worker (overrides NSID inference).")
@click.option("--url", "base_url", default=None, help="Full base URL (overrides --app and inference).")
@click.option("-X", "--method", "http_method", default=None, type=click.Choice(["GET", "POST"], case_sensitive=False),
              help="HTTP method. Default: POST if -d given, else GET.")
@click.option("--json", "output_json", is_flag=True, help="Pretty-print JSON response.")
@click.option("-v", "--verbose", is_flag=True)
def xrpc(nsid: str, data_json: str | None, app: str | None, base_url: str | None,
         http_method: str | None, output_json: bool, verbose: bool) -> None:
    """Invoke an XRPC endpoint. NSID is the method name (e.g. com.atproto.server.describeServer)."""
    base = _resolve_base(nsid, app, base_url)
    url = f"{base}/xrpc/{nsid}"

    payload = None
    if data_json:
        try:
            payload = _json_mod.loads(data_json)
        except _json_mod.JSONDecodeError as exc:
            raise click.ClickException(f"Invalid JSON for -d: {exc}") from exc

    method = (http_method or ("POST" if payload is not None else "GET")).upper()
    headers = scoped_auth_headers(nsid)

    if verbose:
        click.echo(f"{method} {url}", err=True)
        if payload:
            click.echo(f"  body: {payload}", err=True)

    try:
        if method == "POST":
            resp = httpx.post(url, json=payload, headers=headers, timeout=30)
        else:
            params = payload if isinstance(payload, dict) else None
            resp = httpx.get(url, params=params, headers=headers, timeout=30)
    except httpx.RequestError as exc:
        raise click.ClickException(f"Request failed: {exc}") from exc

    if resp.status_code < 200 or resp.status_code >= 300:
        raise click.ClickException(f"XRPC {resp.status_code}: {resp.text}")

    body = resp.text
    if output_json:
        try:
            body = _json_mod.dumps(resp.json(), ensure_ascii=False, indent=2)
        except _json_mod.JSONDecodeError:
            pass

    click.echo(body)
