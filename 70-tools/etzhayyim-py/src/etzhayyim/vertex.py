"""vertex — Graph vertex operations (emit, query, tier registry)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds
from .shannon import _resolve_root


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


_SECTION_RE = re.compile(r"^\[vertex_tier\.tier_([abc])\]\s*$")
_TABLE_RE = re.compile(r'^\s*"(vertex_[a-z0-9_]+)"\s*,?\s*$')


def _load_vertex_tier_registry(deps_path: str) -> dict:
    path = Path(deps_path)
    if not path.exists():
        raise click.ClickException(f"deps not found: {deps_path}")
    reg: dict = {"A": [], "B": [], "C": [], "M": {}}
    current_tier = ""
    in_tables = False
    for line in path.read_text().splitlines():
        trim = line.strip()
        m = _SECTION_RE.match(trim)
        if m:
            current_tier = m.group(1).upper()
            in_tables = False
            continue
        if trim.startswith("[") and not trim.startswith("[vertex_tier."):
            current_tier = ""
            in_tables = False
            continue
        if not current_tier:
            continue
        if trim.startswith("tables") and "[" in trim:
            in_tables = True
            continue
        if in_tables and trim.startswith("]"):
            in_tables = False
            continue
        if not in_tables:
            continue
        tm = _TABLE_RE.match(line)
        if tm:
            name = tm.group(1)
            reg["M"][name] = current_tier
            reg[current_tier].append(name)
    if not reg["M"]:
        raise click.ClickException(f"{deps_path}: no [vertex_tier.tier_*] entries parsed")
    return reg


def _resolve_graph_deps(override: str | None, workspace_dir: str | None) -> str:
    if override:
        return override
    ws = _resolve_root(workspace_dir)
    candidate = ws / "30-graph" / "deps.toml"
    if candidate.exists():
        return str(candidate)
    # Walk up looking for 30-graph/deps.toml
    for parent in ws.parents:
        c = parent / "30-graph" / "deps.toml"
        if c.exists():
            return str(c)
    raise click.ClickException("30-graph/deps.toml not found; use --deps to specify path")


@click.group("vertex")
def vertex() -> None:
    """Graph vertex operations (emit, query, list labels, tier registry)."""


@vertex.command("emit")
@click.option("--label", required=True, help="Vertex label (e.g. Invoice)")
@click.option("--data", default="{}", help="JSON data payload")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def vertex_emit(label: str, data: str, pds: str | None, json_out: bool) -> None:
    """Emit a vertex to the graph."""
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"invalid JSON data: {e}")
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.vertex.emit",
            json={"label": label, "data": payload},
            headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        if json_out:
            click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            click.echo(f"emitted: {label}  id={result.get('id', '?')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@vertex.command("query")
@click.option("--label", required=True)
@click.option("--filter", "filter_text", default="")
@click.option("--limit", default=50, type=int, show_default=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def vertex_query(label: str, filter_text: str, limit: int, pds: str | None, json_out: bool) -> None:
    """Query vertices by label."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.vertex.query",
            params={"label": label, "filter": filter_text, "limit": limit},
            headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            rows = data if isinstance(data, list) else data.get("rows", [])
            for r in rows:
                click.echo(f"  {r}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@vertex.command("labels")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def vertex_labels(pds: str | None, json_out: bool) -> None:
    """List all vertex labels in the graph."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.vertex.listLabels",
            headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            labels = data if isinstance(data, list) else data.get("labels", [])
            for l in labels:
                click.echo(f"  {l}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@vertex.command("tier")
@click.argument("table_name")
@click.option("--deps", "deps_path", default=None, help="Path to 30-graph/deps.toml")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def vertex_tier(table_name: str, deps_path: str | None,
                workspace_dir: str | None, json_out: bool) -> None:
    """Look up ADR-0040 tier for a vertex table."""
    dp = _resolve_graph_deps(deps_path, workspace_dir)
    reg = _load_vertex_tier_registry(dp)
    tier = reg["M"].get(table_name)
    if json_out:
        click.echo(json.dumps({"table": table_name, "tier": tier, "classified": tier is not None},
                              ensure_ascii=False))
        return
    if tier is None:
        click.echo(f"{table_name}: not classified (default tier = C per ADR-0040)", err=True)
        sys.exit(1)
    click.echo(f"{table_name}\t{tier}")


@vertex.command("list")
@click.option("--tier", "tier_filter", required=True,
              type=click.Choice(["A", "B", "C"]), help="Filter by tier")
@click.option("--deps", "deps_path", default=None, help="Path to 30-graph/deps.toml")
@click.option("--workspace-dir", default=None)
@click.option("--limit", default=0, type=int, help="Max rows (0 = no limit)")
@click.option("--json", "json_out", is_flag=True, default=False)
def vertex_list_tiers(tier_filter: str, deps_path: str | None, workspace_dir: str | None,
                      limit: int, json_out: bool) -> None:
    """List vertex tables at a given ADR-0040 tier."""
    dp = _resolve_graph_deps(deps_path, workspace_dir)
    reg = _load_vertex_tier_registry(dp)
    tables = sorted(reg[tier_filter])
    if limit > 0:
        tables = tables[:limit]
    if json_out:
        click.echo(json.dumps({"tier": tier_filter, "count": len(tables), "tables": tables},
                              ensure_ascii=False, indent=2))
    else:
        for t in tables:
            click.echo(t)


@vertex.command("stats")
@click.option("--deps", "deps_path", default=None, help="Path to 30-graph/deps.toml")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def vertex_stats(deps_path: str | None, workspace_dir: str | None, json_out: bool) -> None:
    """ADR-0040 vertex tier registry stats."""
    dp = _resolve_graph_deps(deps_path, workspace_dir)
    reg = _load_vertex_tier_registry(dp)
    total = len(reg["A"]) + len(reg["B"]) + len(reg["C"])
    if json_out:
        click.echo(json.dumps({"tier_a": len(reg["A"]), "tier_b": len(reg["B"]),
                               "tier_c": len(reg["C"]), "total": total,
                               "adr": "adr-0040-vertex-did-tier-policy"},
                              ensure_ascii=False))
    else:
        click.echo(f"ADR-0040 Vertex DID Tier registry ({dp})")
        click.echo(f"  Tier A (actor DID):         {len(reg['A']):4}")
        click.echo(f"  Tier B (sub-path did:etzhayyim): {len(reg['B']):4}")
        click.echo(f"  Tier C (no DID):            {len(reg['C']):4}")
        click.echo(f"  Total:                      {total:4}")
