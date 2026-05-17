"""source-graph — Source-level import/dependency graph.

Scans TypeScript and Python source files for import statements to build
a module-level dependency graph. Detects orphans and cycles.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import click

from .shannon import _resolve_root


# ── regexes ────────────────────────────────────────────────────────────────────

_RE_TS_IMPORT = re.compile(r"""(?:import|from)\s+['"]([^'"]+)['"]""")
_RE_PY_IMPORT = re.compile(r"""^(?:import|from)\s+([\w.]+)""", re.MULTILINE)
_RE_GO_IMPORT = re.compile(r'"([^"]+)"')

_SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build"}
_SKIP_PREFIXES = ("@", "node:", "bun:", "https://", "http://")


@dataclass
class SGNode:
    path: str
    lang: str
    imports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"path": self.path, "lang": self.lang, "imports": self.imports}


@dataclass
class SGEdge:
    source: str
    target: str

    def to_dict(self) -> dict:
        return {"source": self.source, "target": self.target}


@dataclass
class SGReport:
    nodes: list[SGNode]
    edges: list[SGEdge]

    def orphan_paths(self) -> list[str]:
        imported = {e.target for e in self.edges}
        sources = {e.source for e in self.edges}
        all_paths = {n.path for n in self.nodes}
        return sorted(all_paths - imported - sources)

    def cycles(self) -> list[list[str]]:
        adj: dict[str, set[str]] = {}
        for e in self.edges:
            adj.setdefault(e.source, set()).add(e.target)
        found: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            for nb in adj.get(node, set()):
                if nb not in visited:
                    dfs(nb, path + [nb])
                elif nb in rec_stack:
                    idx = path.index(nb) if nb in path else 0
                    cycle = path[idx:] + [nb]
                    if cycle not in found:
                        found.append(cycle)
            rec_stack.discard(node)

        for n in adj:
            if n not in visited:
                dfs(n, [n])
        return found

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }


# ── scanner ────────────────────────────────────────────────────────────────────

def _parse_ts_imports(content: str) -> list[str]:
    return [m for m in _RE_TS_IMPORT.findall(content)
            if not any(m.startswith(p) for p in _SKIP_PREFIXES)]


def _parse_py_imports(content: str) -> list[str]:
    return [m for m in _RE_PY_IMPORT.findall(content)
            if not m.startswith("_")]


def _resolve_ts_import(imp: str, source_path: Path, ws: Path) -> str | None:
    if imp.startswith("."):
        base = source_path.parent / imp
        for ext in ("", ".ts", ".svelte", "/index.ts"):
            candidate = Path(str(base) + ext)
            if candidate.exists():
                try:
                    return str(candidate.relative_to(ws))
                except ValueError:
                    pass
    return None


def scan_source_graph(ws: Path) -> SGReport:
    nodes: list[SGNode] = []
    edges: list[SGEdge] = []
    seen_edges: set[tuple[str, str]] = set()

    for p in ws.rglob("*"):
        if not p.is_file():
            continue
        if any(d in p.parts for d in _SKIP_DIRS):
            continue

        rel = str(p.relative_to(ws))

        if p.suffix in (".ts", ".svelte"):
            try:
                content = p.read_text(errors="replace")
            except OSError:
                continue
            imports = _parse_ts_imports(content)
            node = SGNode(path=rel, lang="typescript", imports=imports)
            nodes.append(node)
            for imp in imports:
                resolved = _resolve_ts_import(imp, p, ws)
                if resolved:
                    key = (rel, resolved)
                    if key not in seen_edges:
                        seen_edges.add(key)
                        edges.append(SGEdge(source=rel, target=resolved))

        elif p.suffix == ".py":
            try:
                content = p.read_text(errors="replace")
            except OSError:
                continue
            imports = _parse_py_imports(content)
            node = SGNode(path=rel, lang="python", imports=imports)
            nodes.append(node)

    return SGReport(nodes=nodes, edges=edges)


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group("source-graph", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def source_graph(ctx: click.Context, workspace_dir: str | None, json_out: bool) -> None:
    """Source-level import/dependency graph analysis."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    report = scan_source_graph(ws)
    if json_out:
        click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        orphans = report.orphan_paths()
        cycles = report.cycles()
        click.echo(f"source-graph: nodes={len(report.nodes)}  edges={len(report.edges)}  "
                   f"orphans={len(orphans)}  cycles={len(cycles)}")


@source_graph.command("scan")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--lang", default="", help="Filter by language (typescript/python)")
def sg_scan(workspace_dir: str | None, json_out: bool, lang: str) -> None:
    """List all scanned source modules."""
    ws = _resolve_root(workspace_dir)
    report = scan_source_graph(ws)
    nodes = report.nodes
    if lang:
        nodes = [n for n in nodes if n.lang == lang]
    if json_out:
        click.echo(json.dumps([n.to_dict() for n in nodes], ensure_ascii=False, indent=2))
    else:
        for n in nodes:
            click.echo(f"  [{n.lang:10}] {n.path}  ({len(n.imports)} imports)")


@source_graph.command("orphans")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def sg_orphans(workspace_dir: str | None, json_out: bool) -> None:
    """Files not referenced by any other module."""
    ws = _resolve_root(workspace_dir)
    report = scan_source_graph(ws)
    orphans = report.orphan_paths()
    if json_out:
        click.echo(json.dumps(orphans, ensure_ascii=False, indent=2))
    else:
        click.echo(f"orphans: {len(orphans)}")
        for o in orphans[:50]:
            click.echo(f"  {o}")


@source_graph.command("cycles")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def sg_cycles(workspace_dir: str | None, json_out: bool) -> None:
    """Detect circular imports."""
    ws = _resolve_root(workspace_dir)
    report = scan_source_graph(ws)
    cycles = report.cycles()
    if json_out:
        click.echo(json.dumps(cycles, ensure_ascii=False, indent=2))
    else:
        if not cycles:
            click.echo("  no cycles detected")
        for cycle in cycles:
            click.echo("  cycle: " + " → ".join(cycle))


@source_graph.command("deps")
@click.argument("file_path")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def sg_deps(file_path: str, workspace_dir: str | None, json_out: bool) -> None:
    """Show all direct imports of a specific file."""
    ws = _resolve_root(workspace_dir)
    report = scan_source_graph(ws)
    node = next((n for n in report.nodes if file_path in n.path), None)
    if not node:
        raise click.ClickException(f"file not found in graph: {file_path}")
    if json_out:
        click.echo(json.dumps(node.to_dict(), ensure_ascii=False, indent=2))
    else:
        click.echo(f"{node.path}  [{node.lang}]")
        for imp in node.imports:
            click.echo(f"  → {imp}")


@source_graph.command("dot")
@click.option("--workspace-dir", default=None)
@click.option("--lang", default="all", help="Filter by language: ts, py, or all")
def sg_dot(workspace_dir: str | None, lang: str) -> None:
    """Output GraphViz DOT format of the import graph."""
    ws = _resolve_root(workspace_dir)
    report = scan_source_graph(ws)

    lang_map = {"ts": "typescript", "py": "python", "all": ""}
    lang_filter = lang_map.get(lang, lang)

    nodes = report.nodes if not lang_filter else [n for n in report.nodes if n.lang == lang_filter]
    node_paths = {n.path for n in nodes}
    edges = [e for e in report.edges if e.source in node_paths and e.target in node_paths]

    def _dot_id(path: str) -> str:
        return '"' + path.replace('"', '\\"') + '"'

    lines = ["digraph source_graph {", '  rankdir="LR";', '  node [shape=box fontsize=10];']
    for n in nodes:
        color = "lightblue" if n.lang == "typescript" else "lightyellow"
        lines.append(f'  {_dot_id(n.path)} [label={_dot_id(n.path)} style=filled fillcolor={color}];')
    for e in edges:
        lines.append(f"  {_dot_id(e.source)} -> {_dot_id(e.target)};")
    lines.append("}")
    click.echo("\n".join(lines))


@source_graph.command("sql")
@click.option("--workspace-dir", default=None)
@click.option("--lang", default="all", help="Filter by language: ts, py, or all")
def sg_sql(workspace_dir: str | None, lang: str) -> None:
    """Output SQL CREATE TABLE + INSERT for DuckDB ingestion."""
    ws = _resolve_root(workspace_dir)
    report = scan_source_graph(ws)

    lang_map = {"ts": "typescript", "py": "python", "all": ""}
    lang_filter = lang_map.get(lang, lang)

    nodes = report.nodes if not lang_filter else [n for n in report.nodes if n.lang == lang_filter]
    node_paths = {n.path for n in nodes}
    edges = [e for e in report.edges if e.source in node_paths and e.target in node_paths]

    def _esc(s: str) -> str:
        return s.replace("'", "''")

    lines = [
        "CREATE TABLE IF NOT EXISTS sg_nodes (path TEXT PRIMARY KEY, lang TEXT, import_count INTEGER);",
        "CREATE TABLE IF NOT EXISTS sg_edges (source TEXT, target TEXT, PRIMARY KEY (source, target));",
        "",
    ]
    for n in nodes:
        lines.append(
            f"INSERT OR IGNORE INTO sg_nodes VALUES ('{_esc(n.path)}', '{_esc(n.lang)}', {len(n.imports)});"
        )
    lines.append("")
    for e in edges:
        lines.append(
            f"INSERT OR IGNORE INTO sg_edges VALUES ('{_esc(e.source)}', '{_esc(e.target)}');"
        )
    click.echo("\n".join(lines))


# ── layer boundary rules ───────────────────────────────────────────────────────

_LAYER_ORDER = [
    "00-contracts",
    "10-protocol",
    "20-actors",
    "30-graph",
    "40-engine",
    "50-infra",
    "60-apps",
    "70-tools",
    "80-packages",
    "90-docs",
]


def _layer_of(path: str) -> str | None:
    for layer in _LAYER_ORDER:
        if path.startswith(layer + "/") or "/" + layer + "/" in "/" + path:
            return layer
    return None


def _layer_index(layer: str | None) -> int:
    if layer is None:
        return -1
    try:
        return _LAYER_ORDER.index(layer)
    except ValueError:
        return -1


@source_graph.command("violations")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def sg_violations(workspace_dir: str | None, json_out: bool) -> None:
    """Find structural violations: cycles, cross-layer imports, orphans."""
    ws = _resolve_root(workspace_dir)
    report = scan_source_graph(ws)

    cycles = report.cycles()
    orphans = report.orphan_paths()

    cross_layer: list[dict] = []
    for e in report.edges:
        src_layer = _layer_of(e.source)
        tgt_layer = _layer_of(e.target)
        if src_layer and tgt_layer and src_layer != tgt_layer:
            src_idx = _layer_index(src_layer)
            tgt_idx = _layer_index(tgt_layer)
            if src_idx > tgt_idx:
                cross_layer.append({
                    "source": e.source,
                    "target": e.target,
                    "source_layer": src_layer,
                    "target_layer": tgt_layer,
                    "direction": f"{src_layer} → {tgt_layer} (lower layer)",
                })

    if json_out:
        click.echo(json.dumps({
            "cycles": cycles,
            "cross_layer_imports": cross_layer,
            "orphans": orphans,
        }, ensure_ascii=False, indent=2))
    else:
        click.echo(f"violations summary: cycles={len(cycles)}  cross_layer={len(cross_layer)}  orphans={len(orphans)}")
        if cycles:
            click.echo("\n-- Cycles --")
            for c in cycles:
                click.echo("  cycle: " + " → ".join(c))
        if cross_layer:
            click.echo("\n-- Cross-layer imports (lower imports higher) --")
            for v in cross_layer[:50]:
                click.echo(f"  {v['source']}  →  {v['target']}  [{v['direction']}]")
        if orphans:
            click.echo(f"\n-- Orphans (top 30 of {len(orphans)}) --")
            for o in orphans[:30]:
                click.echo(f"  {o}")
