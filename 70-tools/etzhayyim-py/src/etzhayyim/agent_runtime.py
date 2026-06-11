"""agent-runtime — Agent runtime (LangGraph Server/Granian L3) management.

Pod management requires the Go binary / kubectl.
status/logs read via XRPC.
ERC-8004 manifest commands (render/publish/register/publish-agent/holochain-plan) ported from Go.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds

_AGENT_RUNTIME_SCHEMA = "https://etzhayyim.com/schemas/k8s-runtime-public/v1.json"
_DEFAULT_REGISTRY = "0x0000000000000000000000000000000000000001"
_DEFAULT_RPC = "http://10.0.0.1:8545"
_DEFAULT_CHAIN_ID = "1337"
_DEFAULT_IPFS = "https://ipfs.etzhayyim.com"


def _find_git_root() -> Path | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
        )
        return Path(out.decode().strip())
    except Exception:
        return None


def _render_runtime_public(cluster: str, manifests: list[str]) -> bytes:
    """Delegate to render-agent-runtime-public.py script (mirrors Go)."""
    root = _find_git_root()
    script = (root / "70-tools/scripts/contract/render-agent-runtime-public.py") if root else None
    if script and script.exists():
        result = subprocess.run(
            [sys.executable, str(script), "--cluster", cluster] + manifests,
            capture_output=True,
        )
        if result.returncode != 0:
            raise click.ClickException(
                f"render script failed: {result.stderr.decode()[:800]}"
            )
        return result.stdout
    # Fallback: assemble minimal JSON from manifests
    parts = []
    for mpath in manifests:
        p = Path(mpath)
        if p.exists():
            parts.append({"path": str(p), "content": p.read_text()})
    doc = {
        "$schema": _AGENT_RUNTIME_SCHEMA,
        "cluster": cluster,
        "kind": "k8s-runtime",
        "manifests": parts,
    }
    return json.dumps(doc, ensure_ascii=False, indent=2).encode()


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@click.group("agent-runtime")
def agent_runtime() -> None:
    """Agent runtime (LangGraph Server + Granian L3) management."""


@agent_runtime.command("status")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def ar_status(pds: str | None, json_out: bool) -> None:
    """Runtime health and active graphs."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.agentRuntime.getStatus",
                         headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"agent-runtime: {data.get('status', 'unknown')}")
            for k, v in data.items():
                if k != "status":
                    click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@agent_runtime.command("list")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def ar_list(pds: str | None, json_out: bool) -> None:
    """List active LangGraph runs."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.agentRuntime.listRuns",
                         headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            runs = data if isinstance(data, list) else data.get("runs", [])
            for r in runs:
                click.echo(f"  {r.get('id', '')}  {r.get('graph', '')}  {r.get('status', '')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@agent_runtime.command("logs")
@click.argument("run_id")
@click.option("--pds", default=None)
@click.option("--limit", default=100, type=int, show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
def ar_logs(run_id: str, pds: str | None, limit: int, json_out: bool) -> None:
    """Fetch logs for a LangGraph run."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.agentRuntime.getRunLogs",
                         params={"id": run_id, "limit": limit},
                         headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            logs = data if isinstance(data, list) else data.get("logs", [])
            for entry in logs:
                ts = entry.get("ts", "")
                msg = entry.get("msg", str(entry))
                click.echo(f"  {ts}  {msg}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@agent_runtime.command("restart")
@click.option("--pds", default=None)
def ar_restart(pds: str | None) -> None:
    """Restart the agent runtime pod (requires Go binary / kubectl)."""
    click.echo(
        "etzhayyim agent-runtime restart requires the Go binary or kubectl. "
        "Run: etzhayyim agent-runtime restart",
        err=True,
    )
    sys.exit(1)


# ── ERC-8004 manifest commands (ported from Go agent_runtime.go) ──────────────

@agent_runtime.command("render")
@click.option("--cluster", required=True, help="public cluster label")
@click.option("--out", "out_path", default="", help="output JSON path (default stdout)")
@click.argument("manifests", nargs=-1, required=True)
def ar_render(cluster: str, out_path: str, manifests: tuple) -> None:
    """Render k8s manifests into a public ERC-8004 runtime JSON."""
    rendered = _render_runtime_public(cluster, list(manifests))
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(rendered)
        click.echo(f"wrote {out_path} ({len(rendered)} bytes)")
    else:
        sys.stdout.buffer.write(rendered)


@agent_runtime.command("publish")
@click.option("--cluster", required=True, help="public cluster label")
@click.option("--out", "out_path", default="", help="optional output JSON path")
@click.option("--ipfs", "ipfs_base", default=_DEFAULT_IPFS, show_default=True,
              help="IPFS gateway/proxy base URL")
@click.option("--dry-run/--no-dry-run", default=True, show_default=True,
              help="render and hash without writing to IPFS")
@click.argument("manifests", nargs=-1, required=True)
def ar_publish(cluster: str, out_path: str, ipfs_base: str, dry_run: bool,
               manifests: tuple) -> None:
    """Render k8s manifests and optionally publish to IPFS."""
    rendered = _render_runtime_public(cluster, list(manifests))
    sha256 = "0x" + hashlib.sha256(rendered).hexdigest()
    result: dict = {
        "ok": True,
        "dryRun": dry_run,
        "sha256": sha256,
        "bytes": len(rendered),
        "schema": _AGENT_RUNTIME_SCHEMA,
        "kind": "k8s-runtime",
        "ipfsBase": ipfs_base.rstrip("/"),
        "published": False,
    }
    if not dry_run:
        raise click.ClickException(
            "Live IPFS publish requires the Go binary (needs macOS Keychain IPFS_HMAC). "
            "Run: etzhayyim agent-runtime publish --no-dry-run"
        )
    out_bytes = json.dumps(result, ensure_ascii=False, indent=2).encode() + b"\n"
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(out_bytes)
    sys.stdout.buffer.write(out_bytes)


@agent_runtime.command("register")
@click.option("--agent-uri", "agent_uri", required=True,
              help="published ERC-8004 agent registration URI (ipfs://...)")
@click.option("--registration", "registration_path", default="",
              help="ERC-8004 agent registration JSON path")
@click.option("--root-did", "root_did", default="",
              help="ERC-725 root DID (defaults to registration.rootIdentity.rootDid)")
@click.option("--owner", "agent_owner", default="",
              help="agent owner address (defaults to registration.rootIdentity.address)")
@click.option("--metadata-hash", "metadata_hash", default="",
              help="bytes32 metadata hash (defaults to sha256(registration JSON))")
@click.option("--registry", default=_DEFAULT_REGISTRY, show_default=True,
              help="etzhayyimAgentRegistry contract address")
@click.option("--rpc-url", "rpc_url", default=_DEFAULT_RPC, show_default=True)
@click.option("--chain-id", "chain_id", default=_DEFAULT_CHAIN_ID, show_default=True)
@click.option("--out", "out_path", default="")
@click.option("--dry-run/--no-dry-run", default=True, show_default=True)
def ar_register(agent_uri: str, registration_path: str, root_did: str, agent_owner: str,
                metadata_hash: str, registry: str, rpc_url: str, chain_id: str,
                out_path: str, dry_run: bool) -> None:
    """Register agent on-chain via ERC-8004 (dry-run: build tx; live: requires Go binary)."""
    reg_bytes = b""
    if registration_path:
        reg_bytes = Path(registration_path).read_bytes()
        reg = json.loads(reg_bytes)
        if not root_did:
            root_did = reg.get("rootIdentity", {}).get("rootDid", "")
        if not agent_owner:
            agent_owner = reg.get("rootIdentity", {}).get("address", "")
        if not metadata_hash:
            metadata_hash = "0x" + hashlib.sha256(reg_bytes).hexdigest()
    if not root_did:
        raise click.ClickException("--root-did is required when --registration does not provide rootIdentity.rootDid")
    if not agent_owner:
        raise click.ClickException("--owner is required when --registration does not provide a non-zero rootIdentity.address")
    if not metadata_hash:
        metadata_hash = "0x" + "0" * 64

    if not dry_run:
        raise click.ClickException(
            "Live on-chain registration requires the Go binary (EVM signing). "
            "Run: etzhayyim agent-runtime register --no-dry-run"
        )

    result = {
        "ok": True,
        "dryRun": dry_run,
        "chainId": chain_id,
        "rpcUrl": rpc_url,
        "registry": registry,
        "rootDid": root_did,
        "owner": agent_owner,
        "agentURI": agent_uri,
        "metadataHash": metadata_hash,
        "submitted": False,
    }
    out_bytes = json.dumps(result, ensure_ascii=False, indent=2).encode() + b"\n"
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(out_bytes)
    sys.stdout.buffer.write(out_bytes)


@agent_runtime.command("publish-agent")
@click.option("--registration", "registration_path", required=True,
              help="ERC-8004 agent registration JSON template path")
@click.option("--cluster", required=True, help="public cluster label")
@click.option("--root-did", "root_did", default="")
@click.option("--owner", "agent_owner", default="")
@click.option("--registry", default=_DEFAULT_REGISTRY, show_default=True)
@click.option("--rpc-url", "rpc_url", default=_DEFAULT_RPC, show_default=True)
@click.option("--chain-id", "chain_id", default=_DEFAULT_CHAIN_ID, show_default=True)
@click.option("--ipfs", "ipfs_base", default=_DEFAULT_IPFS, show_default=True)
@click.option("--out", "out_path", default="")
@click.option("--dry-run/--no-dry-run", default=True, show_default=True)
@click.argument("manifests", nargs=-1, required=False)
def ar_publish_agent(registration_path: str, cluster: str, root_did: str,
                     agent_owner: str, registry: str, rpc_url: str, chain_id: str,
                     ipfs_base: str, out_path: str, dry_run: bool,
                     manifests: tuple) -> None:
    """Render + publish to IPFS + register on-chain (dry-run: build all without submitting)."""
    if not dry_run:
        raise click.ClickException(
            "Live publish-agent requires the Go binary. Run: etzhayyim agent-runtime publish-agent --no-dry-run"
        )
    reg_bytes = Path(registration_path).read_bytes()
    reg = json.loads(reg_bytes)
    if not root_did:
        root_did = reg.get("rootIdentity", {}).get("rootDid", "")
    if not agent_owner:
        agent_owner = reg.get("rootIdentity", {}).get("address", "")
    metadata_hash = "0x" + hashlib.sha256(reg_bytes).hexdigest()

    rendered = _render_runtime_public(cluster, list(manifests)) if manifests else b"{}"
    sha256 = "0x" + hashlib.sha256(rendered).hexdigest()

    result = {
        "ok": True,
        "dryRun": True,
        "cluster": cluster,
        "renderSha256": sha256,
        "renderBytes": len(rendered),
        "metadataHash": metadata_hash,
        "rootDid": root_did,
        "owner": agent_owner,
        "registry": registry,
        "ipfsBase": ipfs_base.rstrip("/"),
        "published": False,
        "submitted": False,
    }
    out_bytes = json.dumps(result, ensure_ascii=False, indent=2).encode() + b"\n"
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(out_bytes)
    sys.stdout.buffer.write(out_bytes)


@agent_runtime.command("holochain-plan")
@click.option("--agent-did", "agent_did", required=True, help="agent DID bound to the Holochain cell")
@click.option("--happ-name", "happ_name", default="etzhayyim-agent-actor-runtime", show_default=True)
@click.option("--happ-uri", "happ_uri", required=True, help="published .happ URI (ipfs://... or https://...)")
@click.option("--happ-sha256", "happ_sha256", default="", help="optional .happ sha256 bytes32 hex")
@click.option("--dna-hash", "dna_hash", required=True, help="Holochain DNA hash for the actor runtime network")
@click.option("--role", "role_name", default="agent_actor_runtime", show_default=True)
@click.option("--zome", "zome_name", default="actor_runtime", show_default=True)
@click.option("--conductor-image", "conductor_image",
              default="ghcr.io/etzhayyim/holochain-agent-runtime:experimental", show_default=True)
@click.option("--cluster", default="local-dev", show_default=True)
@click.option("--namespace", default="agent-runtime-holochain", show_default=True)
@click.option("--workload", default="holochain-agent-runtime", show_default=True)
@click.option("--out", "out_path", default="")
def ar_holochain_plan(agent_did: str, happ_name: str, happ_uri: str, happ_sha256: str,
                      dna_hash: str, role_name: str, zome_name: str,
                      conductor_image: str, cluster: str, namespace: str,
                      workload: str, out_path: str) -> None:
    """Build a Holochain conductor k8s runtime plan JSON."""
    if namespace == "default":
        raise click.ClickException("--namespace must not be default")
    plan = {
        "schema": "https://etzhayyim.com/schemas/holochain-runtime-plan/v1.json",
        "agentDid": agent_did,
        "cluster": cluster,
        "hApp": {
            "name": happ_name,
            "uri": happ_uri,
            "sha256": happ_sha256,
            "roleName": role_name,
            "zomeName": zome_name,
            "dnaHash": dna_hash,
        },
        "k8s": {
            "namespace": namespace,
            "workload": workload,
            "conductorImage": conductor_image,
            "env": [
                {"name": "AGENT_DID", "value": agent_did},
                {"name": "HAPP_URI", "value": happ_uri},
                {"name": "DNA_HASH", "value": dna_hash},
                {"name": "ROLE_NAME", "value": role_name},
                {"name": "ZOME_NAME", "value": zome_name},
            ],
        },
    }
    out_bytes = json.dumps(plan, ensure_ascii=False, indent=2).encode() + b"\n"
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(out_bytes)
    sys.stdout.buffer.write(out_bytes)
