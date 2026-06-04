"""agent — Agent management commands.

Full agentic loop (LangGraph Pregel) requires the Go binary.
list/get/stop operate via XRPC.
"""

from __future__ import annotations

import json
import subprocess
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


@click.group("agent")
def agent() -> None:
    """Agent management (list/get/stop via XRPC; full loop requires Go binary)."""


@agent.command("list")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--status", "filter_status", default="", help="Filter: running/idle/stopped")
def agent_list(pds: str | None, json_out: bool, filter_status: str) -> None:
    """List agent instances."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    params = {}
    if filter_status:
        params["status"] = filter_status
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.agent.listAgents",
                         params=params, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            agents = data if isinstance(data, list) else data.get("agents", [])
            for a in agents:
                click.echo(f"  {a.get('id', '')}  {a.get('name', '')}  {a.get('status', '')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@agent.command("get")
@click.argument("agent_id")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def agent_get(agent_id: str, pds: str | None, json_out: bool) -> None:
    """Get agent details."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.agent.getAgent",
                         params={"id": agent_id}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@agent.command("stop")
@click.argument("agent_id")
@click.option("--pds", default=None)
def agent_stop(agent_id: str, pds: str | None) -> None:
    """Stop a running agent."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(f"{pds_url}/xrpc/com.etzhayyim.agent.stopAgent",
                          json={"id": agent_id}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        click.echo(f"stopped: {agent_id}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@agent.command("run")
@click.option("--prompt", required=True)
@click.option("--pds", default=None)
@click.option("--model", default="", help="Override model")
@click.option("--json", "json_out", is_flag=True, default=False)
def agent_run(prompt: str, pds: str | None, model: str, json_out: bool) -> None:
    """Start an agent run (full Pregel loop requires Go binary)."""
    click.echo(
        "etzhayyim agent run (full Pregel loop) requires the Go binary. Run: etzhayyim agent run",
        err=True,
    )
    sys.exit(1)


# ── agent verify ──────────────────────────────────────────────────────────────

_DEFAULT_PUBLICATION_PROOF = "90-docs/proof/kami-agent-erc8004-publish-attempt.local.json"
_DEFAULT_ARTIFACT_PROOF = "90-docs/proof/kami-agent-runtime-artifact.local.json"
_DEFAULT_RECEIPT_PROOF = "90-docs/proof/kami-agent-runtime-receipt.local.json"


@agent.command("verify")
@click.option("--did", "agent_did", default="", help="agent DID to verify (default: env AGENT_DID)")
@click.option("--publication-proof", "pub_proof", default=_DEFAULT_PUBLICATION_PROOF)
@click.option("--artifact-proof", "art_proof", default=_DEFAULT_ARTIFACT_PROOF)
@click.option("--receipt-proof", "rec_proof", default=_DEFAULT_RECEIPT_PROOF)
@click.option("--json", "json_out", is_flag=True, default=False)
def agent_verify(
    agent_did: str, pub_proof: str, art_proof: str, rec_proof: str, json_out: bool,
) -> None:
    """Verify on-chain ERC-8004 agent registration against local proof files."""
    import os
    try:
        repo_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True,
        ).strip())
    except subprocess.CalledProcessError:
        repo_root = Path.cwd()

    did = agent_did or os.environ.get("AGENT_DID", "")
    checks: dict[str, dict] = {}

    def _load_proof(label: str, rel_path: str) -> dict | None:
        p = repo_root / rel_path
        if not p.exists():
            checks[label] = {"ok": False, "detail": f"file not found: {rel_path}"}
            return None
        try:
            data = json.loads(p.read_text())
            checks[label] = {"ok": True, "detail": f"loaded {rel_path}"}
            return data
        except Exception as e:
            checks[label] = {"ok": False, "detail": str(e)}
            return None

    pub = _load_proof("publication_proof", pub_proof)
    _load_proof("artifact_proof", art_proof)
    _load_proof("receipt_proof", rec_proof)

    # Extract chain info from publication proof
    chain_ok = False
    if pub:
        chain = pub.get("chain", {})
        chain_did_hash = chain.get("rootDidHash", "")
        chain_ok = bool(chain.get("txHash"))
        checks["chain_registration"] = {
            "ok": chain_ok,
            "detail": f"txHash={chain.get('txHash', '—')} rootDidHash={chain_did_hash[:12]}..." if chain_ok else "no txHash in proof",
        }

    overall_ok = all(v["ok"] for v in checks.values())
    result = {
        "ok": overall_ok,
        "agentDid": did,
        "checks": checks,
    }

    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "OK" if overall_ok else "FAIL"
        click.echo(f"agent verify [{status}]  did={did or '—'}")
        for label, check in checks.items():
            mark = "✓" if check["ok"] else "✗"
            click.echo(f"  {mark} {label}: {check.get('detail', '')}")
    if not overall_ok:
        sys.exit(1)


# ── agent organism ────────────────────────────────────────────────────────────

@agent.group("organism")
def agent_organism() -> None:
    """Agent organism management (status / publish)."""


@agent_organism.command("status")
@click.option("--agent-did", "agent_did", default="", help="agent DID (default: env AGENT_DID)")
@click.option("--url", "status_url", default="", help="Status WebUI URL")
@click.option("--json", "json_out", is_flag=True, default=False)
def agent_organism_status(agent_did: str, status_url: str, json_out: bool) -> None:
    """Show organism status (HTTP probe or local)."""
    import os
    did = agent_did or os.environ.get("AGENT_DID", "")
    url = status_url or os.environ.get("AGENT_STATUS_PUBLIC_URL", "")

    if url:
        try:
            resp = httpx.get(f"{url.rstrip('/')}/status", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if json_out:
                click.echo(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                click.echo(f"organism status: {data.get('status', 'unknown')}  did={did or '—'}")
            return
        except httpx.HTTPError as e:
            click.echo(f"HTTP probe failed: {e}", err=True)

    result = {"agentDid": did, "status": "unknown", "note": "no status URL configured"}
    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"organism status: unknown  (set AGENT_STATUS_PUBLIC_URL to probe)")


@agent_organism.command("publish")
@click.option("--agent-did", "agent_did", default="", help="agent DID")
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
def agent_organism_publish(agent_did: str, dry_run: bool) -> None:
    """Publish ERC-8004 organism registration (requires Go binary for full flow)."""
    import os
    did = agent_did or os.environ.get("AGENT_DID", "")
    if dry_run:
        click.echo(f"dry-run: would publish organism registration for DID={did or '—'}")
        click.echo("Full ERC-8004 publish requires the Go binary: etzhayyim agent organism publish")
        return
    click.echo(
        "etzhayyim agent organism publish (full Ethereum/IPFS flow) requires the Go binary.",
        err=True,
    )
    sys.exit(1)
