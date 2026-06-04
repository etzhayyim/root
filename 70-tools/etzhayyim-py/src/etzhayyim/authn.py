"""authn — Authentication commands (Python port of auth.go).

signin: OAuth2 Auth Code + PKCE flow with localhost callback server.
Writes ~/.etzhayyim/auth.json; also tries to exchange for sk_live_* API key.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import click
import httpx

_AUTH_FILE = Path.home() / ".etzhayyim" / "auth.json"
_AUTHORIZE_URL = "https://authn.etzhayyim.com/oauth/authorize"
_TOKEN_URL = "https://authn.etzhayyim.com/oauth/token"
_CLIENT_ID = "etzhayyim-cli"
_CALLBACK_PORT = 9876
_DEFAULT_PDS = "https://atproto.etzhayyim.com"


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _parse_jwt_claims(token: str) -> tuple[str, str]:
    """Return (sub, email) from a JWT payload without verifying signature."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return "", ""
        pad = 4 - len(parts[1]) % 4
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * pad))
        return payload.get("sub", ""), payload.get("email", "")
    except Exception:
        return "", ""


def _exchange_for_api_key(session_jwt: str, pds_url: str) -> str:
    """Try to get a sk_live_* API key via com.etzhayyim.auth.createApiKey. Returns "" on failure."""
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.auth.createApiKey",
            json={"name": "etzhayyim-cli-login", "scopes": "read,write"},
            headers={"Authorization": f"Bearer {session_jwt}"},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("key", "")
    except Exception:
        pass
    return ""


def _run_signin(pds_url: str) -> None:
    code_verifier = _b64url(secrets.token_bytes(32))
    challenge_hash = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = _b64url(challenge_hash)
    state = _b64url(secrets.token_bytes(16))
    redirect_uri = f"http://127.0.0.1:{_CALLBACK_PORT}/callback"

    params = {
        "client_id": _CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = _AUTHORIZE_URL + "?" + urlencode(params)

    code_holder: list[str] = []
    error_holder: list[str] = []

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # silence access log

        def do_GET(self):
            if not self.path.startswith("/callback"):
                self.send_response(404)
                self.end_headers()
                return
            qs = parse_qs(urlparse(self.path).query)
            if qs.get("state", [""])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid state")
                error_holder.append("OAuth state mismatch")
                return
            if "error" in qs:
                msg = qs.get("error_description", qs["error"])[0]
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f"OAuth error: {msg}".encode())
                error_holder.append(msg)
                return
            code = qs.get("code", [""])[0]
            if not code:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"No code")
                error_holder.append("no authorization code received")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>\xe2\x9c\x93 etzhayyim authn signin successful</h2>"
                b"<p>You can close this tab.</p>"
                b"<script>window.close()</script></body></html>"
            )
            code_holder.append(code)

    server = HTTPServer(("127.0.0.1", _CALLBACK_PORT), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    click.echo("Opening browser for authentication...")
    click.echo(f"If browser doesn't open, visit:\n  {auth_url}\n")
    webbrowser.open(auth_url)

    deadline = time.time() + 120
    while not code_holder and not error_holder and time.time() < deadline:
        time.sleep(0.2)
    server.shutdown()

    if error_holder:
        raise click.ClickException(f"OAuth error: {error_holder[0]}")
    if not code_holder:
        raise click.ClickException("authentication timed out (120s)")

    code = code_holder[0]

    # Exchange code for tokens
    try:
        resp = httpx.post(
            _TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": _CLIENT_ID,
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
    except httpx.RequestError as exc:
        raise click.ClickException(f"token exchange: {exc}") from exc

    if resp.status_code != 200:
        raise click.ClickException(f"token exchange failed: {resp.status_code} {resp.text[:400]}")

    tok = resp.json()
    bearer = tok.get("id_token") or tok.get("access_token", "")
    sub, email = _parse_jwt_claims(bearer)

    api_key = tok.get("api_key", "")
    if not api_key and bearer:
        api_key = _exchange_for_api_key(bearer, pds_url)

    store: dict = {"sub": sub, "email": email}
    if api_key:
        store["api_key"] = api_key
    else:
        store["access_token"] = tok.get("access_token", "")
        store["id_token"] = tok.get("id_token", "")
        store["refresh_token"] = tok.get("refresh_token", "")
        expires_in = tok.get("expires_in", 0)
        if expires_in:
            store["expires_at"] = int(time.time()) + int(expires_in)

    _AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    _AUTH_FILE.write_text(json.dumps(store, indent=2) + "\n")
    _AUTH_FILE.chmod(0o600)

    display = email or sub or "unknown"
    click.echo(f"✓ Authenticated as {display} ({sub})")
    if api_key:
        click.echo(f"  API key issued and stored in {_AUTH_FILE}")
    else:
        click.echo(f"  Session token stored in {_AUTH_FILE}")


def _load_auth() -> dict:
    try:
        return json.loads(_AUTH_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


@click.group("authn")
def authn() -> None:
    """Authentication management."""


@authn.command("signin")
@click.option("--pds", default=None, help="PDS base URL (overrides etzhayyim_PDS_URL)")
def authn_signin(pds: str | None) -> None:
    """Sign in via OAuth2 Auth Code + PKCE (opens browser, stores token in ~/.etzhayyim/auth.json)."""
    import os
    pds_url = (pds or os.environ.get("etzhayyim_PDS_URL", _DEFAULT_PDS)).rstrip("/")
    _run_signin(pds_url)


@authn.command("token")
def authn_token() -> None:
    """Print the current access token to stdout."""
    auth = _load_auth()
    token = auth.get("accessJwt") or auth.get("access_token") or auth.get("token", "")
    if not token:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    click.echo(token)


@authn.command("whoami")
@click.option("--json", "json_out", is_flag=True, default=False)
def authn_whoami(json_out: bool) -> None:
    """Display current auth identity."""
    auth = _load_auth()
    if not auth:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    if json_out:
        click.echo(json.dumps(auth, ensure_ascii=False, indent=2))
    else:
        did = auth.get("did", auth.get("sub", ""))
        handle = auth.get("handle", "")
        pds = auth.get("pds", auth.get("service", ""))
        click.echo(f"did:    {did}")
        if handle:
            click.echo(f"handle: {handle}")
        if pds:
            click.echo(f"pds:    {pds}")


@authn.command("signout")
def authn_signout() -> None:
    """Remove local auth credentials."""
    if _AUTH_FILE.exists():
        _AUTH_FILE.unlink()
        click.echo("signed out")
    else:
        click.echo("not signed in")


@authn.command("login")
@click.option("--pds", default=None)
def authn_login(pds: str | None) -> None:
    """Alias for signin."""
    import os
    pds_url = (pds or os.environ.get("etzhayyim_PDS_URL", _DEFAULT_PDS)).rstrip("/")
    _run_signin(pds_url)


@authn.command("logout")
def authn_logout() -> None:
    """Alias for signout."""
    if _AUTH_FILE.exists():
        _AUTH_FILE.unlink()
        click.echo("signed out")
    else:
        click.echo("not signed in")


@authn.command("revoke")
@click.option("--token", "explicit_token", default="", help="revoke this specific token (JWT or sk_* key)")
@click.option("--pds", default=None)
@click.option("--keep-local", "keep_local", is_flag=True, default=False,
              help="do not delete ~/.etzhayyim/auth.json after server-side revoke")
@click.option("-q", "quiet", is_flag=True, default=False)
def authn_revoke(explicit_token: str, pds: str | None, keep_local: bool, quiet: bool) -> None:
    """Revoke stored OAuth2 session tokens via /oauth/revoke."""
    import os
    import urllib.parse
    import urllib.request

    pds_url = (pds or os.environ.get("etzhayyim_PDS_URL", _DEFAULT_PDS)).rstrip("/")
    revoke_url = pds_url + "/oauth/revoke"
    auth = _load_auth()

    targets = []
    if explicit_token:
        targets.append({"token": explicit_token, "hint": "", "label": "--token argument"})
    else:
        access = auth.get("accessJwt") or auth.get("access_token", "")
        refresh = auth.get("refreshJwt") or auth.get("refresh_token", "")
        id_tok = auth.get("id_token", "")
        api_key = auth.get("api_key", "")
        if access:
            targets.append({"token": access, "hint": "access_token", "label": "access_token"})
        if refresh:
            targets.append({"token": refresh, "hint": "refresh_token", "label": "refresh_token"})
        if id_tok and id_tok != access:
            targets.append({"token": id_tok, "hint": "access_token", "label": "id_token"})
        if not targets:
            if api_key:
                raise click.ClickException(
                    "local store has only an API key — use 'etzhayyim authz revoke-api-key'"
                )
            raise click.ClickException(
                "no stored credentials — run 'etzhayyim authn signin' or pass --token <jwt>"
            )

    errs = 0
    for t in targets:
        data = urllib.parse.urlencode(
            {"token": t["token"], **({"token_type_hint": t["hint"]} if t["hint"] else {})}
        ).encode()
        req = urllib.request.Request(revoke_url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            urllib.request.urlopen(req, timeout=15)
            if not quiet:
                click.echo(f"  revoked: {t['label']}")
        except Exception as e:
            click.echo(f"  warn: revoke {t['label']} failed: {e}", err=True)
            errs += 1

    if not keep_local and _AUTH_FILE.exists():
        _AUTH_FILE.unlink()
        if not quiet:
            click.echo(f"  removed: {_AUTH_FILE}")

    if errs:
        raise click.ClickException(f"{errs} revoke call(s) failed")


@authn.command("migrate")
@click.option("--name", default="etzhayyim-cli-migrated", show_default=True, help="API key name")
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
@click.option("--pds", default=None)
def authn_migrate(name: str, dry_run: bool, pds: str | None) -> None:
    """Migrate legacy session JWT → API key (sk_live_*) stored in ~/.etzhayyim/auth.json."""
    import os
    import json as _json
    pds_url = (pds or os.environ.get("etzhayyim_PDS_URL", _DEFAULT_PDS)).rstrip("/")
    auth = _load_auth()
    if auth.get("api_key", ""):
        click.echo("✓ Already migrated (api_key is set). No action needed.")
        return
    token = (auth.get("accessJwt") or auth.get("access_token") or
             auth.get("id_token") or os.environ.get("etzhayyim_TOKEN", ""))
    if not token:
        raise click.ClickException("no legacy session token found — run 'etzhayyim authn signin' first")

    if dry_run:
        click.echo(f"Would: POST {pds_url}/xrpc/com.etzhayyim.auth.createApiKey (name={name}) using session JWT.")
        click.echo(f"Would: overwrite {_AUTH_FILE} with api_key entry.")
        return

    import httpx as _httpx
    try:
        resp = _httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.auth.createApiKey",
            json={"name": name, "scopes": "read,write"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise click.ClickException(f"createApiKey: {e}")

    api_key = data.get("key", data.get("apiKey", ""))
    if not api_key:
        raise click.ClickException(f"unexpected response: {data}")

    new_auth = {
        "api_key": api_key,
        "sub": auth.get("sub", auth.get("did", "")),
        "email": auth.get("email", ""),
        "active_did": auth.get("activeDid", auth.get("active_did", "")),
    }
    _AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    _AUTH_FILE.write_text(_json.dumps(new_auth, indent=2))
    click.echo(f"✓ Migrated to API key ({api_key[:18]}...).")
    click.echo(f"  Legacy tokens cleared from {_AUTH_FILE}")
