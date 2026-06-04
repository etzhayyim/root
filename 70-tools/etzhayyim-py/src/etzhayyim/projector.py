"""projector subcommands — Python port of Go etzhayyim/projector.go (ADR-2605151500).

Calls the projector MCP tool via JSON-RPC 2.0 over HTTPS.
Auth: etzhayyim_AGENT_TOKEN env var → Authorization: Bearer {token}.
MCP endpoint: POST {pds}/mcp
"""

from __future__ import annotations

import json
import os
import sys

import click
import httpx

from .auth import resolve_pds

_MCP_METHOD = "tools/call"
_JSONRPC = "2.0"
_REQ_ID = 1


def _agent_token() -> str | None:
    return os.environ.get("etzhayyim_AGENT_TOKEN")


def _mcp_headers() -> dict[str, str]:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if tok := _agent_token():
        headers["Authorization"] = f"Bearer {tok}"
    return headers


def _mcp_call(tool_name: str, arguments: dict) -> dict:
    """POST JSON-RPC 2.0 tools/call to {pds}/mcp and return the parsed result dict."""
    pds = resolve_pds()
    url = f"{pds}/mcp"
    payload = {
        "jsonrpc": _JSONRPC,
        "id": _REQ_ID,
        "method": _MCP_METHOD,
        "params": {"name": tool_name, "arguments": arguments},
    }
    resp = httpx.post(url, json=payload, headers=_mcp_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        err = data["error"]
        raise click.ClickException(f"MCP error {err.get('code')}: {err.get('message')}")
    result = data.get("result", {})
    # Unwrap content[0].text (MCP tool response envelope)
    content = result.get("content", [])
    if content and isinstance(content[0], dict):
        text = content[0].get("text", "")
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return {"text": text}
    return result


def _print_json(data: dict) -> None:
    click.echo(json.dumps(data, ensure_ascii=False, indent=2))


# ── CLI group ──────────────────────────────────────────────────────────────────

@click.group("projector")
def projector():
    """Manage projects via the projector MCP tool."""


# ── create ─────────────────────────────────────────────────────────────────────

@projector.command("create")
@click.argument("name")
@click.option("--org-id", envvar="etzhayyim_ORG_ID", default=None, help="Organization DID")
@click.option("--description", "-d", default=None)
@click.option("--parent-id", default=None)
@click.option("--target-date", default=None, help="ISO date e.g. 2026-12-31")
def create(name: str, org_id: str | None, description: str | None, parent_id: str | None, target_date: str | None):
    """Create a new project."""
    args: dict = {"name": name}
    if org_id:
        args["orgId"] = org_id
    if description:
        args["description"] = description
    if parent_id:
        args["parentId"] = parent_id
    if target_date:
        args["targetDate"] = target_date
    try:
        result = _mcp_call("projector.create_project", args)
        _print_json(result)
    except httpx.HTTPError as exc:
        raise click.ClickException(str(exc)) from exc


# ── status / get ───────────────────────────────────────────────────────────────

@projector.command("status")
@click.argument("project_id")
@click.option("--summarize/--no-summarize", default=True)
def status(project_id: str, summarize: bool):
    """Get project status."""
    try:
        result = _mcp_call("projector.get_status", {"projectId": project_id, "summarize": summarize})
        _print_json(result)
    except httpx.HTTPError as exc:
        raise click.ClickException(str(exc)) from exc


@projector.command("get")
@click.argument("project_id")
@click.option("--summarize/--no-summarize", default=True)
@click.pass_context
def get(ctx: click.Context, project_id: str, summarize: bool):
    """Alias for status."""
    ctx.invoke(status, project_id=project_id, summarize=summarize)


# ── update ─────────────────────────────────────────────────────────────────────

@projector.command("update")
@click.argument("project_id")
@click.option("--progress", type=int, default=None, help="Progress permille (0-1000)")
@click.option("--state", default=None, help="Lifecycle state")
@click.option("--target-date", default=None)
def update(project_id: str, progress: int | None, state: str | None, target_date: str | None):
    """Update project status."""
    args: dict = {"projectId": project_id}
    if progress is not None:
        args["progressPermille"] = progress
    if state:
        args["lifecycleState"] = state
    if target_date:
        args["targetDate"] = target_date
    try:
        result = _mcp_call("projector.update_status", args)
        _print_json(result)
    except httpx.HTTPError as exc:
        raise click.ClickException(str(exc)) from exc


# ── list ───────────────────────────────────────────────────────────────────────

@projector.command("list")
@click.option("--org-id", envvar="etzhayyim_ORG_ID", default=None)
@click.option("--state", default=None, help="Filter by lifecycle state")
@click.option("--limit", default=20, show_default=True)
def list_projects(org_id: str | None, state: str | None, limit: int):
    """List projects."""
    args: dict = {"limit": limit}
    if org_id:
        args["orgId"] = org_id
    if state:
        args["lifecycleState"] = state
    try:
        result = _mcp_call("projector.list_projects", args)
        _print_json(result)
    except httpx.HTTPError as exc:
        raise click.ClickException(str(exc)) from exc


# ── blocker ────────────────────────────────────────────────────────────────────

@projector.group("blocker")
def blocker():
    """Manage project blockers."""


@blocker.command("add")
@click.argument("project_id")
@click.argument("title")
@click.option("--type", "blocker_type", default="technical", show_default=True,
              help="Blocker type: technical|resource|external|process")
@click.option("--severity", default="medium", show_default=True,
              help="Severity: low|medium|high|critical")
@click.option("--description", "-d", default=None)
def blocker_add(project_id: str, title: str, blocker_type: str, severity: str, description: str | None):
    """Add a blocker to a project."""
    args: dict = {"projectId": project_id, "title": title, "blockerType": blocker_type, "severity": severity}
    if description:
        args["description"] = description
    try:
        result = _mcp_call("projector.add_blocker", args)
        _print_json(result)
    except httpx.HTTPError as exc:
        raise click.ClickException(str(exc)) from exc


@blocker.command("resolve")
@click.argument("blocker_id")
@click.option("--resolution", "-r", default=None)
def blocker_resolve(blocker_id: str, resolution: str | None):
    """Resolve a blocker."""
    args: dict = {"blockerId": blocker_id}
    if resolution:
        args["resolution"] = resolution
    try:
        result = _mcp_call("projector.resolve_blocker", args)
        _print_json(result)
    except httpx.HTTPError as exc:
        raise click.ClickException(str(exc)) from exc
