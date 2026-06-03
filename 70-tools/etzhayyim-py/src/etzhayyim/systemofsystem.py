"""systemofsystem — System-of-Systems (SoS) analysis.

Scans the workspace to identify clusters of interacting actors,
map SoS boundaries, and measure inter-system coupling.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import click

from .haisen import _scan_workspace, HaisenReport
from .shannon import _resolve_root


@dataclass
class SoSCluster:
    name: str
    nanoids: list[str]
    internal_edges: int
    external_edges: int

    @property
    def cohesion(self) -> float:
        total = self.internal_edges + self.external_edges
        return self.internal_edges / max(total, 1)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "nanoids": self.nanoids,
            "internal_edges": self.internal_edges,
            "external_edges": self.external_edges,
            "cohesion": round(self.cohesion, 3),
        }


def _cluster_by_project(report: HaisenReport, ws: Path) -> list[SoSCluster]:
    """Group actors by their project (etzhayyim-project-X)."""
    project_of: dict[str, str] = {}

    projects_dir = ws / "60-apps"
    if not projects_dir.exists():
        projects_dir = ws / "projects"

    for app in report.apps:
        for jsonld in (projects_dir).rglob("magatama.jsonld") if projects_dir.exists() else []:
            try:
                import json as _json
                data = _json.loads(jsonld.read_text(errors="replace"))
                if data.get("nanoid") == app.nanoid:
                    for seg in jsonld.parts:
                        if seg.startswith("etzhayyim-project-"):
                            project_of[app.nanoid] = seg.removeprefix("etzhayyim-project-")
                            break
            except (OSError, Exception):
                pass

    # Build clusters
    clusters: dict[str, list[str]] = {}
    for app in report.apps:
        proj = project_of.get(app.nanoid, "unknown")
        clusters.setdefault(proj, []).append(app.nanoid)

    result = []
    for proj, nanoids in clusters.items():
        nanoid_set = set(nanoids)
        internal = sum(
            1 for e in report.edges
            if e.from_nanoid in nanoid_set and e.to_nanoid in nanoid_set
        )
        external = sum(
            1 for e in report.edges
            if (e.from_nanoid in nanoid_set) != (e.to_nanoid in nanoid_set)
        )
        result.append(SoSCluster(name=proj, nanoids=nanoids,
                                 internal_edges=internal, external_edges=external))
    return sorted(result, key=lambda c: -c.cohesion)


@click.group("systemofsystem", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def systemofsystem(ctx: click.Context, workspace_dir: str | None, json_out: bool) -> None:
    """System-of-Systems boundary and coupling analysis."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    clusters = _cluster_by_project(report, ws)
    if json_out:
        click.echo(json.dumps([c.to_dict() for c in clusters], ensure_ascii=False, indent=2))
    else:
        click.echo(f"system-of-systems: {len(clusters)} clusters  {len(report.apps)} actors")
        for c in clusters:
            click.echo(f"  {c.name:<20}  actors={len(c.nanoids):3d}  "
                       f"cohesion={c.cohesion:.2f}  "
                       f"internal={c.internal_edges}  external={c.external_edges}")


@systemofsystem.command("clusters")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def sos_clusters(workspace_dir: str | None, json_out: bool) -> None:
    """List system clusters and their cohesion metrics."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    clusters = _cluster_by_project(report, ws)
    if json_out:
        click.echo(json.dumps([c.to_dict() for c in clusters], ensure_ascii=False, indent=2))
    else:
        for c in clusters:
            click.echo(f"  {c.name}  actors={len(c.nanoids)}  cohesion={c.cohesion:.2f}")
            for n in c.nanoids[:5]:
                click.echo(f"    {n}")
            if len(c.nanoids) > 5:
                click.echo(f"    ... +{len(c.nanoids)-5} more")


@systemofsystem.command("coupling")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def sos_coupling(workspace_dir: str | None, json_out: bool) -> None:
    """Show inter-system coupling (cross-cluster edges)."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    clusters = _cluster_by_project(report, ws)
    cross = [c for c in clusters if c.external_edges > 0]
    if json_out:
        click.echo(json.dumps([c.to_dict() for c in cross], ensure_ascii=False, indent=2))
    else:
        click.echo(f"cross-cluster edges in {len(cross)} systems:")
        for c in sorted(cross, key=lambda x: -x.external_edges):
            click.echo(f"  {c.name}  external={c.external_edges}")


@systemofsystem.command("scan")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def sos_scan(workspace_dir: str | None, json_out: bool) -> None:
    """Full system-of-systems JSON report with coupling and cohesion stats."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    clusters = _cluster_by_project(report, ws)

    # Build a nanoid → cluster name lookup
    nanoid_to_cluster: dict[str, str] = {}
    for c in clusters:
        for n in c.nanoids:
            nanoid_to_cluster[n] = c.name

    cross_edges = sum(
        1 for e in report.edges
        if nanoid_to_cluster.get(e.from_nanoid) != nanoid_to_cluster.get(e.to_nanoid)
    )
    intra_edges = sum(
        1 for e in report.edges
        if nanoid_to_cluster.get(e.from_nanoid) == nanoid_to_cluster.get(e.to_nanoid)
    )

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_apps": len(report.apps),
        "total_edges": len(report.edges),
        "clusters": [c.to_dict() for c in clusters],
        "stats": {
            "coupling_score": round(cross_edges / max(len(report.edges), 1) * 100, 1),
            "cohesion_score": round(intra_edges / max(len(report.edges), 1) * 100, 1),
            "orphan_apps": sum(
                1 for a in report.apps
                if not any(
                    e.from_nanoid == a.nanoid or e.to_nanoid == a.nanoid
                    for e in report.edges
                )
            ),
        },
    }

    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(
            f"system-of-systems: {len(clusters)} clusters  "
            f"{len(report.apps)} actors  {len(report.edges)} edges"
        )


_LAYER_MAP: list[tuple[list[str], str]] = [
    (["auth", "authn", "authz"], "identity"),
    (["yoro", "chat", "ui"], "interface"),
    (["pds", "infra", "deploy"], "infra"),
    (["murakumo", "inference", "llm"], "inference"),
    (["data", "graph", "db"], "data"),
]


def _cluster_layer(name: str) -> str:
    for keywords, layer in _LAYER_MAP:
        if any(kw in name for kw in keywords):
            return layer
    return "app"


@systemofsystem.command("layers")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def sos_layers(workspace_dir: str | None, json_out: bool) -> None:
    """Group clusters by architectural layer."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    clusters = _cluster_by_project(report, ws)

    layers: dict[str, list[str]] = {}
    for c in clusters:
        layer = _cluster_layer(c.name)
        layers.setdefault(layer, []).append(c.name)

    if json_out:
        out = [
            {"layer": layer, "systems": names, "count": len(names)}
            for layer, names in sorted(layers.items())
        ]
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for layer, names in sorted(layers.items()):
            click.echo(f"{layer}:")
            for name in names:
                click.echo(f"  {name}")


@systemofsystem.command("interfaces")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def sos_interfaces(workspace_dir: str | None, json_out: bool) -> None:
    """Show inter-cluster interface edges aggregated by cluster pair."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    clusters = _cluster_by_project(report, ws)

    nanoid_to_cluster: dict[str, str] = {}
    for c in clusters:
        for n in c.nanoids:
            nanoid_to_cluster[n] = c.name

    pair_counts: dict[tuple[str, str], int] = {}
    for e in report.edges:
        fc = nanoid_to_cluster.get(e.from_nanoid)
        tc = nanoid_to_cluster.get(e.to_nanoid)
        if fc and tc and fc != tc:
            pair_counts[(fc, tc)] = pair_counts.get((fc, tc), 0) + 1

    sorted_pairs = sorted(pair_counts.items(), key=lambda x: -x[1])

    if json_out:
        out = [
            {"from": pair[0], "to": pair[1], "edge_count": count}
            for pair, count in sorted_pairs
        ]
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for (fc, tc), count in sorted_pairs:
            click.echo(f"  {fc} ──> {tc}  edges: {count}")


@systemofsystem.command("health")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def sos_health(workspace_dir: str | None, json_out: bool) -> None:
    """Compute system-of-systems health verdict."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)
    clusters = _cluster_by_project(report, ws)

    nanoid_to_cluster: dict[str, str] = {}
    for c in clusters:
        for n in c.nanoids:
            nanoid_to_cluster[n] = c.name

    cross_edges = sum(
        1 for e in report.edges
        if nanoid_to_cluster.get(e.from_nanoid) != nanoid_to_cluster.get(e.to_nanoid)
    )
    intra_edges = sum(
        1 for e in report.edges
        if nanoid_to_cluster.get(e.from_nanoid) == nanoid_to_cluster.get(e.to_nanoid)
    )

    total = max(len(report.edges), 1)
    coupling = round(cross_edges / total * 100, 1)
    cohesion = round(intra_edges / total * 100, 1)

    if coupling < 20 and cohesion > 60:
        verdict = "HEALTHY"
    elif coupling < 40 and cohesion > 40:
        verdict = "ACCEPTABLE"
    else:
        verdict = "NEEDS ATTENTION"

    stats = {
        "clusters": len(clusters),
        "actors": len(report.apps),
        "edges": len(report.edges),
        "coupling_score": coupling,
        "cohesion_score": cohesion,
        "verdict": verdict,
    }

    if json_out:
        click.echo(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        click.echo("System-of-Systems Health")
        click.echo("────────────────────────")
        click.echo(f"  clusters:   {len(clusters)}")
        click.echo(f"  actors:     {len(report.apps)}")
        click.echo(f"  edges:      {len(report.edges)}")
        click.echo(f"  coupling:   {coupling}% (lower = better)")
        click.echo(f"  cohesion:   {cohesion}% (higher = better)")
        click.echo()
        click.echo(f"  verdict: {verdict}")
