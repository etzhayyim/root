"""kashika (可視化) — Visualization export for actor ecosystem.

Exports haisen/source-graph data to Mermaid, DOT (Graphviz), or JSON.
Interactive rendering requires external tooling.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from .haisen import _scan_workspace as _haisen_scan
from .shannon import _resolve_root


def _read_stdin_or_file(input_file: str | None) -> bytes:
    if input_file:
        return Path(input_file).read_bytes()
    return sys.stdin.buffer.read()


def _to_mermaid(report) -> str:
    lines = ["graph LR"]
    app_names = {a.nanoid: (a.name or a.nanoid) for a in report.apps}
    for e in report.edges:
        src = app_names.get(e.from_nanoid, e.from_nanoid)
        dst = app_names.get(e.to_nanoid, e.to_nanoid)
        label = e.edge_type
        lines.append(f'    {e.from_nanoid}["{src}"] -->|{label}| {e.to_nanoid}["{dst}"]')
    return "\n".join(lines)


def _to_dot(report) -> str:
    lines = ["digraph actors {", '  rankdir="LR";', '  node [shape=box];']
    app_names = {a.nanoid: (a.name or a.nanoid) for a in report.apps}
    for a in report.apps:
        label = app_names.get(a.nanoid, a.nanoid)
        lines.append(f'  "{a.nanoid}" [label="{label}"];')
    for e in report.edges:
        lines.append(f'  "{e.from_nanoid}" -> "{e.to_nanoid}" [label="{e.edge_type}"];')
    lines.append("}")
    return "\n".join(lines)


@click.group("kashika", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--format", "fmt", default="mermaid",
              type=click.Choice(["mermaid", "dot", "json"]), show_default=True)
@click.option("--output", "-o", default=None, help="Output file (default: stdout)")
@click.pass_context
def kashika(ctx: click.Context, workspace_dir: str | None, fmt: str, output: str | None) -> None:
    """Visualization export (Mermaid/DOT/JSON) of actor wiring diagram."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    report = _haisen_scan(ws)
    if fmt == "mermaid":
        out = _to_mermaid(report)
    elif fmt == "dot":
        out = _to_dot(report)
    else:
        out = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(out)
        click.echo(f"written to {output}")
    else:
        click.echo(out)


@kashika.command("mermaid")
@click.option("--workspace-dir", default=None)
@click.option("--output", "-o", default=None)
def kashika_mermaid(workspace_dir: str | None, output: str | None) -> None:
    """Export actor graph as Mermaid diagram."""
    ws = _resolve_root(workspace_dir)
    report = _haisen_scan(ws)
    out = _to_mermaid(report)
    if output:
        Path(output).write_text(out)
        click.echo(f"written to {output}")
    else:
        click.echo(out)


@kashika.command("dot")
@click.option("--workspace-dir", default=None)
@click.option("--output", "-o", default=None)
def kashika_dot(workspace_dir: str | None, output: str | None) -> None:
    """Export actor graph as Graphviz DOT file."""
    ws = _resolve_root(workspace_dir)
    report = _haisen_scan(ws)
    out = _to_dot(report)
    if output:
        Path(output).write_text(out)
        click.echo(f"written to {output}")
    else:
        click.echo(out)


@kashika.command("json")
@click.option("--workspace-dir", default=None)
@click.option("--output", "-o", default=None)
def kashika_json(workspace_dir: str | None, output: str | None) -> None:
    """Export actor graph as JSON."""
    ws = _resolve_root(workspace_dir)
    report = _haisen_scan(ws)
    out = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(out)
        click.echo(f"written to {output}")
    else:
        click.echo(out)


# ── terminal ───────────────────────────────────────────────────────────────────

def _haisen_terminal(data: dict[str, Any]) -> str:
    apps = data.get("apps", [])
    edges = data.get("edges", [])
    stats = data.get("stats", {})
    lines = [
        f"Apps: {len(apps)}  Edges: {len(edges)}",
        f"  total_apps={stats.get('total_apps', len(apps))}  "
        f"total_edges={stats.get('total_edges', len(edges))}",
        "",
        f"{'NANOID':<12}  {'NAME':<28}  {'TYPE':<10}  EDGES",
    ]
    edge_count: dict[str, int] = {}
    for e in edges:
        edge_count[e.get("from_nanoid", "")] = edge_count.get(e.get("from_nanoid", ""), 0) + 1
    for a in apps[:50]:
        nanoid = (a.get("nanoid") or "")[:12]
        name = (a.get("name") or "")[:28]
        ptype = (a.get("performer_type") or "")[:10]
        ec = edge_count.get(a.get("nanoid", ""), 0)
        lines.append(f"{nanoid:<12}  {name:<28}  {ptype:<10}  {ec}")
    if len(apps) > 50:
        lines.append(f"  ... {len(apps) - 50} more")
    return "\n".join(lines)


@kashika.command("terminal")
@click.option("--input", "input_file", default=None, help="Haisen JSON file (default: stdin)")
@click.option("--source", default="haisen", type=click.Choice(["haisen", "sos"]),
              show_default=True)
@click.option("--workspace-dir", default=None)
def kashika_terminal(input_file: str | None, source: str, workspace_dir: str | None) -> None:
    """ANSI terminal table of actor wiring (reads haisen JSON from stdin or --input)."""
    if input_file or not sys.stdin.isatty():
        raw = _read_stdin_or_file(input_file)
        data = json.loads(raw)
    else:
        ws = _resolve_root(workspace_dir)
        report = _haisen_scan(ws)
        data = report.to_dict()
    click.echo(_haisen_terminal(data))


# ── html ───────────────────────────────────────────────────────────────────────

def _haisen_html(data: dict[str, Any]) -> str:
    apps = data.get("apps", [])
    edges = data.get("edges", [])
    nodes_json = json.dumps([
        {"id": a.get("nanoid", ""), "name": a.get("name") or a.get("nanoid", ""),
         "type": a.get("performer_type", "")}
        for a in apps
    ], ensure_ascii=False)
    links_json = json.dumps([
        {"source": e.get("from_nanoid", ""), "target": e.get("to_nanoid", ""),
         "type": e.get("edge_type", "")}
        for e in edges
    ], ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">
<title>etzhayyim haisen</title>
<style>
body{{background:#0b1020;color:#e0e0ff;font-family:'SF Mono',monospace;margin:0}}
#info{{padding:8px 16px;background:#1a1a3a;font-size:13px}}
canvas{{display:block}}
.node{{fill:#4488ff;stroke:#88aaff;stroke-width:1.5}}
.edge{{stroke:#aaa;stroke-opacity:0.4}}
text{{font-size:10px;fill:#c0c0e0;pointer-events:none}}
</style>
</head>
<body>
<div id="info">etzhayyim kashika html &mdash; {len(apps)} apps, {len(edges)} edges</div>
<svg id="graph" width="100%" height="calc(100vh - 40px)">
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
  markerWidth="5" markerHeight="5" orient="auto">
  <path d="M 0 0 L 10 5 L 0 10 z" fill="#4488ff"/></marker></defs>
<g id="links"></g><g id="nodes"></g>
</svg>
<script>
const nodes={nodes_json};
const links={links_json};
const W=window.innerWidth,H=window.innerHeight-40;
const svg=document.getElementById('graph');
const gL=document.getElementById('links');
const gN=document.getElementById('nodes');
// Simple force layout simulation
const pos={{}};
nodes.forEach((n,i)=>{{
  const angle=(i/nodes.length)*2*Math.PI;
  pos[n.id]={{x:W/2+Math.cos(angle)*Math.min(W,H)*0.35,
               y:H/2+Math.sin(angle)*Math.min(W,H)*0.35}};
}});
// Render edges
links.forEach(l=>{{
  const s=pos[l.source],t=pos[l.target];
  if(!s||!t)return;
  const line=document.createElementNS('http://www.w3.org/2000/svg','line');
  line.setAttribute('x1',s.x);line.setAttribute('y1',s.y);
  line.setAttribute('x2',t.x);line.setAttribute('y2',t.y);
  line.setAttribute('class','edge');
  line.setAttribute('marker-end','url(#arrow)');
  gL.appendChild(line);
}});
// Render nodes
nodes.forEach(n=>{{
  const p=pos[n.id];if(!p)return;
  const g=document.createElementNS('http://www.w3.org/2000/svg','g');
  const c=document.createElementNS('http://www.w3.org/2000/svg','circle');
  c.setAttribute('cx',p.x);c.setAttribute('cy',p.y);c.setAttribute('r',6);
  c.setAttribute('class','node');
  c.setAttribute('title',n.id);
  const t=document.createElementNS('http://www.w3.org/2000/svg','text');
  t.setAttribute('x',p.x+8);t.setAttribute('y',p.y+4);
  t.textContent=n.name.substring(0,18);
  g.appendChild(c);g.appendChild(t);
  gN.appendChild(g);
}});
</script></body></html>"""


@kashika.command("html")
@click.option("--input", "input_file", default=None, help="Haisen JSON file (default: stdin)")
@click.option("--source", default="haisen", type=click.Choice(["haisen", "sos"]),
              show_default=True)
@click.option("--output", "-o", default=None, help="Output file (default: stdout)")
@click.option("--workspace-dir", default=None)
def kashika_html(input_file: str | None, source: str, output: str | None,
                 workspace_dir: str | None) -> None:
    """Self-contained HTML force-directed graph (reads haisen JSON from stdin or --input)."""
    if input_file or not sys.stdin.isatty():
        raw = _read_stdin_or_file(input_file)
        data = json.loads(raw)
    else:
        ws = _resolve_root(workspace_dir)
        report = _haisen_scan(ws)
        data = report.to_dict()
    out = _haisen_html(data)
    if output:
        Path(output).write_text(out)
        click.echo(f"written to {output}", err=True)
    else:
        click.echo(out)


# ── sla ────────────────────────────────────────────────────────────────────────

_SLA_COMPONENTS = [
    {"name": "CF Workers (Dispatcher)", "layer": "edge",
     "avail": 0.9999, "redundancy": 1, "spof": False,
     "issues": [], "mitigations": ["Anycast global, auto-failover across 300+ PoP"]},
    {"name": "CF Workers (PDS)", "layer": "gateway",
     "avail": 0.9999, "redundancy": 1, "spof": True,
     "issues": ["Single Worker, no multi-region active-active"],
     "mitigations": ["Circuit breaker (10s cooldown)", "Rate limiter 600/min"]},
    {"name": "CF KV (PDS_KV)", "layer": "storage",
     "avail": 0.9999, "redundancy": 1, "spof": False,
     "issues": [], "mitigations": ["11 nines durability", "Global replication"]},
    {"name": "yata Container", "layer": "compute",
     "avail": 0.9995, "redundancy": 1, "spof": True,
     "issues": ["Single instance (min_instances=1)", "CSR data lost on restart"],
     "mitigations": ["Fire-and-forget write (KV authoritative)"]},
    {"name": "CF Workers (App)", "layer": "compute",
     "avail": 0.9999, "redundancy": 1, "spof": False,
     "issues": [], "mitigations": ["V8 isolate per request"]},
    {"name": "Vultr VKE (LangServer pods)", "layer": "compute",
     "avail": 0.995, "redundancy": 2, "spof": True,
     "issues": ["Single region (LAX)", "Pod restarts lose in-flight LangGraph state"],
     "mitigations": ["LangGraph checkpointer (Postgres)", "Granian multi-worker"]},
    {"name": "RisingWave (Vultr VKE)", "layer": "data",
     "avail": 0.999, "redundancy": 1, "spof": True,
     "issues": ["Single-region streaming DB", "B2 rps quota risk (incident 2026-04-25)"],
     "mitigations": ["B2 defense-in-depth refill levels", "statement_timeout_secs=120"]},
    {"name": "Cloudflare R2 (B2 via gateway)", "layer": "storage",
     "avail": 0.9999, "redundancy": 1, "spof": False,
     "issues": [], "mitigations": ["11 nines durability"]},
    {"name": "Murakumo Fleet (Mac Mini)", "layer": "inference",
     "avail": 0.99, "redundancy": 4, "spof": False,
     "issues": ["On-prem power/network dependency"],
     "mitigations": ["4-node fleet", "Nomad rolling restart", "RunPod fallback"]},
]

_TARGET_SLA = 0.9999  # 99.99%


def _sla_effective(avail: float, redundancy: int) -> float:
    fail = 1.0
    for _ in range(redundancy):
        fail *= (1 - avail)
    return 1 - fail


def _downtime_per_year(avail: float) -> str:
    minutes = (1 - avail) * 365.25 * 24 * 60
    if minutes < 1:
        return f"{minutes * 60:.1f}s"
    if minutes < 60:
        return f"{minutes:.1f}m"
    return f"{minutes / 60:.2f}h"


@kashika.command("sla")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--svg", "svg_out", is_flag=True, default=False,
              help="Output SVG (writes to stdout or --output)")
@click.option("--output", "-o", default=None)
def kashika_sla(json_out: bool, svg_out: bool, output: str | None) -> None:
    """99.999% SLA design analysis for etzhayyim platform components."""
    target_label = f"{_TARGET_SLA * 100:.4f}%"
    downtime_target = _downtime_per_year(_TARGET_SLA)

    components = []
    for c in _SLA_COMPONENTS:
        eff = _sla_effective(c["avail"], c["redundancy"])
        components.append({**c, "effective_avail": eff,
                           "downtime_per_year": _downtime_per_year(eff),
                           "meets_target": eff >= _TARGET_SLA})

    spofs = [c for c in components if c["spof"]]

    if json_out:
        out = json.dumps({
            "target": _TARGET_SLA,
            "target_label": target_label,
            "downtime_target": downtime_target,
            "components": components,
            "spof_count": len(spofs),
        }, ensure_ascii=False, indent=2)
        if output:
            Path(output).write_text(out)
        else:
            click.echo(out)
        return

    lines = [
        f"etzhayyim Platform SLA Analysis",
        f"  Target: {target_label}  Max downtime: {downtime_target}/year",
        "",
        f"{'COMPONENT':<32}  {'LAYER':<10}  {'AVAIL':<8}  {'EFF_AVAIL':<10}  SPOF  DOWNTIME/yr",
    ]
    for c in components:
        spof_flag = "YES" if c["spof"] else ""
        lines.append(
            f"{c['name']:<32}  {c['layer']:<10}  {c['avail']:.4f}    "
            f"{c['effective_avail']:.4f}      {spof_flag:<5}  {c['downtime_per_year']}"
        )
    lines += ["", f"SPOFs: {len(spofs)}  ({', '.join(c['name'] for c in spofs) or 'none'})"]
    out = "\n".join(lines)
    if output:
        Path(output).write_text(out)
        click.echo(f"written to {output}", err=True)
    else:
        click.echo(out)


# ── shinka ─────────────────────────────────────────────────────────────────────

def _shinka_summary(rows: list[dict]) -> dict:
    total = len(rows)
    shinka_sum = sum(r.get("ShinkaScore", 0) for r in rows)
    hyoka_sum = sum(r.get("HyokaScore", 0) for r in rows)
    max_hyoka = max((r.get("HyokaScore", 0) for r in rows), default=0)
    top_actor = next((r.get("Nanoid", "") for r in rows
                      if r.get("HyokaScore", 0) == max_hyoka), "")
    return {
        "total": total,
        "avg_shinka": shinka_sum / total if total else 0.0,
        "avg_hyoka": hyoka_sum / total if total else 0.0,
        "max_hyoka": max_hyoka,
        "top_actor": top_actor,
        "joucho": sum(1 for r in rows if r.get("HasJoucho")),
        "inbox": sum(1 for r in rows if r.get("HasInbox")),
        "cadence": sum(1 for r in rows if r.get("HasCadence")),
        "drill": sum(1 for r in rows if r.get("HasDrill")),
        "validate": sum(1 for r in rows if r.get("HasValidate")),
        "analyze": sum(1 for r in rows if r.get("HasAnalyze")),
        "engage": sum(1 for r in rows if r.get("HasEngage")),
        "old_timer": sum(1 for r in rows if r.get("HasOldTimer")),
    }


def _pct(n: int, total: int) -> str:
    return f"{n / total * 100:.1f}%" if total else "0.0%"


@kashika.command("shinka")
@click.option("--input", "input_file", default=None,
              help="Shinka JSON file from `monitor shinka --json` (default: stdin)")
@click.option("--format", "fmt", default="terminal",
              type=click.Choice(["terminal", "json"]), show_default=True)
@click.option("--output", "-o", default=None)
@click.option("--top", default=20, type=int, show_default=True)
def kashika_shinka(input_file: str | None, fmt: str, output: str | None, top: int) -> None:
    """Render shinka/kyumei-koji health from JSON (reads from stdin or --input)."""
    raw = _read_stdin_or_file(input_file)
    rows: list[dict] = json.loads(raw)
    if isinstance(rows, dict):
        rows = rows.get("apps", [])
    s = _shinka_summary(rows)

    if fmt == "json":
        data = {"summary": s, "apps": rows}
        out = json.dumps(data, ensure_ascii=False, indent=2)
        if output:
            Path(output).write_text(out)
        else:
            click.echo(out)
        return

    total = s["total"]
    lines = [
        f"Shinka/Kyumei-Koji Health ({total} apps)",
        f"  AvgShinka: {s['avg_shinka']:5.1f}",
        f"  AvgHyoka:  {s['avg_hyoka']:5.1f}",
        f"  Joucho:  {s['joucho']:4d} ({_pct(s['joucho'], total)})",
        f"  Inbox:   {s['inbox']:4d} ({_pct(s['inbox'], total)})",
        f"  Cadence: {s['cadence']:4d} ({_pct(s['cadence'], total)})",
        f"  Drill:   {s['drill']:4d} ({_pct(s['drill'], total)})",
        f"  Validate:{s['validate']:4d} ({_pct(s['validate'], total)})",
        f"  Analyze: {s['analyze']:4d} ({_pct(s['analyze'], total)})",
        f"  Engage:  {s['engage']:4d} ({_pct(s['engage'], total)})",
        f"  OldTimer:{s['old_timer']:4d} ({_pct(s['old_timer'], total)})",
        "",
        f"Top actor by hyoka: {s['top_actor']} ({s['max_hyoka']})",
        "",
        f"{'NANOID':<12}  {'SHINKA':>6}  {'HYOKA':>5}  {'DOMAIN':>6}  {'KG':>4}",
    ]
    old_timers = [r for r in rows if r.get("HasOldTimer")][:top]
    for r in old_timers:
        lines.append(
            f"{r.get('Nanoid', ''):<12}  {r.get('ShinkaScore', 0):6d}  "
            f"{r.get('HyokaScore', 0):5d}  {r.get('DomainScore', 0):6d}  "
            f"{r.get('KGNodes', 0):4d}"
        )
    out = "\n".join(lines)
    if output:
        Path(output).write_text(out)
        click.echo(f"written to {output}", err=True)
    else:
        click.echo(out)


# ── hyoka ─────────────────────────────────────────────────────────────────────

@kashika.command("hyoka")
@click.option("--input", "input_file", default=None,
              help="Hyoka JSON file from `monitor shinka --hyoka --json` (default: stdin)")
@click.option("--format", "fmt", default="terminal",
              type=click.Choice(["terminal", "json", "html"]), show_default=True)
@click.option("--output", "-o", default=None)
@click.option("--top", default=30, type=int, show_default=True)
def kashika_hyoka(input_file: str | None, fmt: str, output: str | None, top: int) -> None:
    """Actor hyoka score ranking (reads from stdin or --input)."""
    raw = _read_stdin_or_file(input_file)
    rows: list[dict] = json.loads(raw)
    if isinstance(rows, dict):
        rows = rows.get("apps", [])

    rows_sorted = sorted(rows, key=lambda r: (-r.get("HyokaScore", 0), r.get("Nanoid", "")))
    s = _shinka_summary(rows)

    if fmt == "json":
        data = {"summary": s, "ranking": rows_sorted}
        out = json.dumps(data, ensure_ascii=False, indent=2)
        if output:
            Path(output).write_text(out)
        else:
            click.echo(out)
        return

    if fmt == "html":
        rows_json = json.dumps(rows_sorted, ensure_ascii=False)
        html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<title>etzhayyim kashika hyoka</title>
<style>body{{background:#0b1020;color:#e0e0ff;font-family:'SF Mono',monospace;padding:16px}}
table{{border-collapse:collapse;width:100%}}
th{{background:#1a1a3a;padding:6px 10px;text-align:left}}
td{{padding:4px 10px;border-bottom:1px solid #1a1a3a}}
.grade-s{{color:#00ff88}}.grade-a{{color:#88ff00}}
.grade-b{{color:#ffcc00}}.grade-c{{color:#ff8800}}.grade-d{{color:#ff4444}}
</style></head><body>
<h2>Hyoka Ranking ({len(rows)} actors)</h2>
<p>AvgHyoka: {s['avg_hyoka']:.1f} / AvgShinka: {s['avg_shinka']:.1f}</p>
<table id="t"><tr><th>#</th><th>Nanoid</th><th>Hyoka</th><th>Grade</th>
<th>Domain</th><th>KG</th><th>Shinka</th></tr></table>
<script>
const rows={rows_json};
const t=document.getElementById('t');
rows.slice(0,{top}).forEach((r,i)=>{{
  const tr=t.insertRow();
  [i+1,r.Nanoid,r.HyokaScore,r.HyokaGrade,r.DomainScore,r.KGNodes,r.ShinkaScore]
    .forEach((v,j)=>{{
      const td=tr.insertCell();td.textContent=v;
      if(j===3)td.className='grade-'+String(v||'').toLowerCase();
    }});
}});
</script></body></html>"""
        if output:
            Path(output).write_text(html)
            click.echo(f"written to {output}", err=True)
        else:
            click.echo(html)
        return

    total = s["total"]
    lines = [
        f"Hyoka Ranking ({total} actors)",
        f"Average Hyoka: {s['avg_hyoka']:.1f} / Average Shinka: {s['avg_shinka']:.1f}",
        "",
        f"{'#':>3}  {'HYOKA':>5}  {'GRADE':<5}  {'NANOID':<12}  {'DOMAIN':>6}  {'KG':>4}  SHINKA",
    ]
    for i, r in enumerate(rows_sorted[:top], 1):
        lines.append(
            f"{i:3d}  {r.get('HyokaScore', 0):5d}  "
            f"{r.get('HyokaGrade', '?'):<5}  "
            f"{r.get('Nanoid', ''):<12}  "
            f"{r.get('DomainScore', 0):6d}  "
            f"{r.get('KGNodes', 0):4d}  "
            f"{r.get('ShinkaScore', 0)}"
        )
    out = "\n".join(lines)
    if output:
        Path(output).write_text(out)
        click.echo(f"written to {output}", err=True)
    else:
        click.echo(out)
