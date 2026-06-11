"""etzhayyim agent-token — port of agent_token.go (ADR-2605151500).

Fetches a scoped service-auth JWT from the PDS for a given LXM.
"""

import time

import click
import httpx

from .auth import auth_headers, resolve_pds


@click.command("agent-token")
@click.option("--lxm", required=True, help="Lexicon method NSID to scope the token to.")
@click.option("--aud", default=None, help="Audience DID (default: inferred from PDS).")
@click.option("--pds", "pds_url", default=None, help="PDS base URL (overrides etzhayyim_PDS_URL).")
@click.option("--ttl", default=60, show_default=True, help="Token lifetime in seconds.")
@click.option("--sub", "sub_did", default=None, help="Subject DID override.")
@click.option("-v", "--verbose", is_flag=True)
def agent_token(lxm: str, aud: str | None, pds_url: str | None, ttl: int, sub_did: str | None, verbose: bool) -> None:
    """Fetch a scoped service-auth JWT (com.atproto.server.getServiceAuth)."""
    base = (pds_url or resolve_pds()).rstrip("/")
    exp = int(time.time()) + ttl

    payload: dict = {"lxm": lxm, "exp": exp}
    if aud:
        payload["aud"] = aud

    headers = auth_headers()
    if sub_did:
        headers["X-Active-DID"] = sub_did

    url = f"{base}/xrpc/com.atproto.server.getServiceAuth"
    if verbose:
        click.echo(f"POST {url}  payload={payload}", err=True)

    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=15)
    except httpx.RequestError as exc:
        raise click.ClickException(f"Request failed: {exc}") from exc

    if resp.status_code != 200:
        raise click.ClickException(f"PDS returned {resp.status_code}: {resp.text}")

    data = resp.json()
    token = data.get("token")
    if not token:
        raise click.ClickException(f"No token in response: {data}")

    click.echo(token)
