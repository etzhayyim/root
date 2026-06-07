"""haisen — Actor wiring diagram (Python port of haisen.go).

Scans 60-apps/ workspace, reads kotodama.jsonld per app to build a graph of
invoke/write/read/subscribe/wasm-import edges between actors.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click

from .shannon import _resolve_root


# ── data types ─────────────────────────────────────────────────────────────────

@dataclass
class HaisenApp:
    nanoid: str
    did: str
    name: str
    performer_type: str
    ui_type: str
    runtime_type: str
    collections: list[str] = field(default_factory=list)
    wit_imports: list[str] = field(default_factory=list)
    wit_exports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nanoid": self.nanoid, "did": self.did, "name": self.name,
            "performer_type": self.performer_type, "ui_type": self.ui_type,
            "runtime_type": self.runtime_type, "collections": self.collections,
            "wit_imports": self.wit_imports, "wit_exports": self.wit_exports,
        }


@dataclass
class HaisenEdge:
    from_nanoid: str
    to_nanoid: str
    edge_type: str  # invoke, writes, reads, subscribe, wasm-import

    def to_dict(self) -> dict:
        return {"from": self.from_nanoid, "to": self.to_nanoid, "type": self.edge_type}


@dataclass
class HaisenReport:
    apps: list[HaisenApp]
    edges: list[HaisenEdge]

    @property
    def orphans(self) -> list[HaisenApp]:
        connected = {e.from_nanoid for e in self.edges} | {e.to_nanoid for e in self.edges}
        return [a for a in self.apps if a.nanoid not in connected]

    def coupling(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self.edges:
            counts[e.to_nanoid] = counts.get(e.to_nanoid, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def to_dict(self) -> dict:
        return {
            "apps": [a.to_dict() for a in self.apps],
            "edges": [e.to_dict() for e in self.edges],
        }


# ── regexes for source scan ────────────────────────────────────────────────────

_RE_INVOKE = re.compile(r'(?:invoke|hostImports\.invoke)\(\s*["\']([a-z][a-z0-9.]+)["\']')
_RE_WRITES = re.compile(r'createRecord\(\s*["\']([a-z][a-z0-9.]+)["\']')
_RE_READS  = re.compile(r'getRecord\(\s*["\']([a-z][a-z0-9.]+)["\']')


# ── scan helpers ───────────────────────────────────────────────────────────────

def _read_jsonld(path: Path) -> dict:
    try:
        return json.loads(path.read_text(errors="replace"))
    except (OSError, json.JSONDecodeError):
        return {}


def _app_from_jsonld(data: dict) -> HaisenApp | None:
    nanoid = data.get("nanoid", "")
    if not nanoid:
        return None
    return HaisenApp(
        nanoid=nanoid,
        did=data.get("did", ""),
        name=data.get("name", ""),
        performer_type=data.get("performerType", ""),
        ui_type=data.get("uiType", ""),
        runtime_type=data.get("runtimeType", ""),
        collections=data.get("collections", []),
        wit_imports=data.get("witImports", []),
        wit_exports=data.get("witExports", []),
    )


def _scan_workspace(ws: Path) -> HaisenReport:
    projects_dir = ws / "60-apps"
    if not projects_dir.exists():
        projects_dir = ws / "projects"
    if not projects_dir.exists():
        return HaisenReport(apps=[], edges=[])

    apps: list[HaisenApp] = []
    for jsonld_path in projects_dir.rglob("kotodama.jsonld"):
        data = _read_jsonld(jsonld_path)
        app = _app_from_jsonld(data)
        if app:
            apps.append(app)

    # Build collection → nanoid lookup for subscribe edges
    collection_owner: dict[str, str] = {}
    for app in apps:
        for col in app.collections:
            collection_owner[col] = app.nanoid

    # Build wit_export → nanoid lookup for wasm-import edges
    export_owner: dict[str, str] = {}
    for app in apps:
        for exp in app.wit_exports:
            export_owner[exp] = app.nanoid

    nanoid_set = {a.nanoid for a in apps}
    edges: list[HaisenEdge] = []
    seen: set[tuple[str, str, str]] = set()

    def _add_edge(frm: str, to: str, etype: str) -> None:
        key = (frm, to, etype)
        if key not in seen and frm != to:
            seen.add(key)
            edges.append(HaisenEdge(from_nanoid=frm, to_nanoid=to, edge_type=etype))

    for jsonld_path in projects_dir.rglob("kotodama.jsonld"):
        data = _read_jsonld(jsonld_path)
        nanoid = data.get("nanoid", "")
        if not nanoid:
            continue

        # Subscribe edges from collections declared in invoke/subscribe blocks
        for dep_nanoid in data.get("subscribes", []):
            if dep_nanoid in nanoid_set:
                _add_edge(nanoid, dep_nanoid, "subscribe")

        # Subscribe edges from collection references in source files
        app_dir = jsonld_path.parent
        src_content = ""
        for src_file in app_dir.rglob("*.ts"):
            try:
                src_content += src_file.read_text(errors="replace") + "\n"
            except OSError:
                pass

        for col_match in re.findall(r'subscribe\(\s*["\']([a-z][a-z0-9.]+)["\']', src_content):
            owner = collection_owner.get(col_match)
            if owner and owner != nanoid:
                _add_edge(nanoid, owner, "subscribe")

        for nsid in _RE_INVOKE.findall(src_content):
            # Map NSID to nanoid by checking if any app owns that collection prefix
            parts = nsid.split(".")
            if len(parts) >= 5:
                candidate = ".".join(parts[:4])
                for app in apps:
                    if app.nanoid != nanoid and any(c.startswith(candidate) for c in app.collections):
                        _add_edge(nanoid, app.nanoid, "invoke")
                        break

        for nsid in _RE_WRITES.findall(src_content):
            owner = collection_owner.get(nsid)
            if owner and owner != nanoid:
                _add_edge(nanoid, owner, "writes")

        for nsid in _RE_READS.findall(src_content):
            owner = collection_owner.get(nsid)
            if owner and owner != nanoid:
                _add_edge(nanoid, owner, "reads")

        # wasm-import edges from witImports cross-referencing other apps' witExports
        app_data = _app_from_jsonld(data)
        if app_data:
            for imp in app_data.wit_imports:
                owner = export_owner.get(imp)
                if owner and owner != nanoid:
                    _add_edge(nanoid, owner, "wasm-import")

        # Explicit dependency declarations
        for dep_nanoid in data.get("dependencies", []):
            if dep_nanoid in nanoid_set:
                _add_edge(nanoid, dep_nanoid, "invoke")

    return HaisenReport(apps=apps, edges=edges)


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group("haisen", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def haisen(ctx: click.Context, workspace_dir: str | None, json_out: bool) -> None:
    """Actor wiring diagram — dependency graph of the actor ecosystem."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    if json_out:
        click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        click.echo(f"haisen (配線): actor wiring diagram")
        click.echo(f"  apps={len(report.apps)}  edges={len(report.edges)}")
        orphan_list = report.orphans
        if orphan_list:
            click.echo(f"  orphans={len(orphan_list)}: " + ", ".join(a.nanoid for a in orphan_list[:5]))


@haisen.command("scan")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def haisen_scan(workspace_dir: str | None, json_out: bool) -> None:
    """Scan all actors and output app metadata."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    if json_out:
        click.echo(json.dumps([a.to_dict() for a in report.apps], ensure_ascii=False, indent=2))
    else:
        for a in sorted(report.apps, key=lambda x: x.nanoid):
            click.echo(f"  {a.nanoid}  {a.name or a.did}  [{a.performer_type}]")


@haisen.command("edges")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--type", "edge_type", default="", help="Filter by edge type")
def haisen_edges(workspace_dir: str | None, json_out: bool, edge_type: str) -> None:
    """Show all dependency edges."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    edges = report.edges
    if edge_type:
        edges = [e for e in edges if e.edge_type == edge_type]
    if json_out:
        click.echo(json.dumps([e.to_dict() for e in edges], ensure_ascii=False, indent=2))
    else:
        for e in edges:
            click.echo(f"  {e.from_nanoid} --[{e.edge_type}]--> {e.to_nanoid}")


@haisen.command("orphans")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def haisen_orphans(workspace_dir: str | None, json_out: bool) -> None:
    """List actors with no edges (neither source nor target)."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    orphan_list = report.orphans
    if json_out:
        click.echo(json.dumps([a.to_dict() for a in orphan_list], ensure_ascii=False, indent=2))
    else:
        if not orphan_list:
            click.echo("  no orphans")
        else:
            for a in orphan_list:
                click.echo(f"  {a.nanoid}  {a.name or a.did}")
        click.echo(f"  total orphans: {len(orphan_list)}/{len(report.apps)}")


@haisen.command("coupling")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--top", default=10, type=int, show_default=True)
def haisen_coupling(workspace_dir: str | None, json_out: bool, top: int) -> None:
    """Show most coupled actors (highest in-degree)."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    coupling = report.coupling()
    top_items = list(coupling.items())[:top]
    if json_out:
        click.echo(json.dumps(
            [{"nanoid": k, "in_degree": v} for k, v in top_items],
            ensure_ascii=False, indent=2,
        ))
    else:
        click.echo(f"haisen coupling (top {top} by in-degree):")
        for nanoid, count in top_items:
            click.echo(f"  {count:4d}  {nanoid}")
