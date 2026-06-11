"""mokuteki (目的) — Purpose-driven 4-layer Shannon optimization evaluator (Python port).

Mokuteki: Global Well-Becoming Generative Society
Principle: DSMで依存構造を表現し、Bayesで不確実性を伝播させ、POMDPで観測と制御を最適化する

4-Layer Framework:
  Layer A (構造)      30%   DSM, graph connectivity, Shannon redundancy, hypergraph coupling
  Layer B (不確実性)  25%   BayesNet, causal DAG, information bottleneck, state-space diversity
  Layer C (制御)      20%   POMDP observation, constraint optimization, MPC, bandit sensing
  Layer D (実装)      25%   Event sourcing, immutable log, policy as code, typed schema, attestation

Python port implements Layers A (partial) and D (partial) from local filesystem scanning.
Layers B and C require the haisen graph from the Go binary.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click

from .shannon import (
    ShannonCheck,
    _resolve_root,
    _walk,
    _SKIP_DIRS,
    build_report,
    run_all_checks,
)

# ── Kyu/Dan rank ladder ────────────────────────────────────────────────────────

@dataclass
class MokutekiRank:
    name: str
    color: str
    min_score: int

    def to_dict(self) -> dict:
        return {"name": self.name, "color": self.color, "min_score": self.min_score}


RANK_LADDER: list[MokutekiRank] = [
    MokutekiRank("Dan 10", "#000000", 12000),
    MokutekiRank("Dan 9",  "#000000", 11000),
    MokutekiRank("Dan 8",  "#000000", 10000),
    MokutekiRank("Dan 7",  "#000000",  9000),
    MokutekiRank("Dan 6",  "#000000",  8000),
    MokutekiRank("Dan 5",  "#000000",  7000),
    MokutekiRank("Dan 4",  "#000000",  6000),
    MokutekiRank("Dan 3",  "#000000",  5000),
    MokutekiRank("Dan 2",  "#000000",  4000),
    MokutekiRank("Dan 1",  "#000000",  2000),
    MokutekiRank("Kyu 1",  "#8B4513",  1500),
    MokutekiRank("Kyu 2",  "#3B82F6",  1000),
    MokutekiRank("Kyu 3",  "#22C55E",   600),
    MokutekiRank("Kyu 4",  "#FF8C00",   300),
    MokutekiRank("Kyu 5",  "#FFD700",   100),
    MokutekiRank("Kyu 6",  "#FFFFFF",     0),
]


def resolve_rank(score: int) -> MokutekiRank:
    for r in RANK_LADDER:
        if score >= r.min_score:
            return r
    return RANK_LADDER[-1]


def next_rank(score: int) -> tuple[str, int]:
    for r in reversed(RANK_LADDER):
        if score < r.min_score:
            return r.name, r.min_score - score
    return "", 0


# ── report types ───────────────────────────────────────────────────────────────

@dataclass
class MokutekiComponent:
    name: str
    score: float
    weight: float
    details: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "score": self.score, "weight": self.weight, "details": self.details}


@dataclass
class MokutekiLayer:
    id: str
    name: str
    name_jp: str
    weight: float
    score: float
    points: int
    components: list[MokutekiComponent] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "name_jp": self.name_jp,
            "weight": self.weight, "score": self.score, "points": self.points,
            "components": [c.to_dict() for c in self.components],
        }


@dataclass
class MokutekiAxis:
    name: str
    weight: float
    score: float
    points: int
    source: str
    details: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name, "weight": self.weight, "score": self.score,
            "points": self.points, "source": self.source, "details": self.details,
        }


@dataclass
class MokutekiReport:
    generated_at: str
    mokuteki: str
    principle: str
    layers: list[MokutekiLayer]
    axes: list[MokutekiAxis]
    total_score: int
    max_score: int
    rank: MokutekiRank
    diagnosis: list[str]

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "mokuteki": self.mokuteki,
            "principle": self.principle,
            "layers": [l.to_dict() for l in self.layers],
            "axes": [a.to_dict() for a in self.axes],
            "total_score": self.total_score,
            "max_score": self.max_score,
            "rank": self.rank.to_dict(),
            "diagnosis": self.diagnosis,
        }


# ── Layer evaluation ──────────────────────────────────────────────────────────

def _weighted_score(components: list[MokutekiComponent]) -> float:
    return sum(c.score * c.weight for c in components)


def _scan_app_meta(ws: Path) -> dict[str, dict]:
    """Scan kotodama.jsonld files for app metadata."""
    meta: dict[str, dict] = {}
    for f in _walk(ws, name="kotodama.jsonld"):
        try:
            data = json.loads(f.read_text(errors="replace"))
        except (OSError, json.JSONDecodeError):
            continue
        nanoid = data.get("nanoid") or data.get("id", "")
        if not nanoid:
            continue
        meta[nanoid] = {
            "did": data.get("did") or data.get("defaultDid", ""),
            "display_name": data.get("displayName") or data.get("name", ""),
            "collections": data.get("collections", []),
            "wit_imports": data.get("witImports", []),
            "wit_exports": data.get("witExports", []),
        }
    return meta


def eval_layer_a(ws: Path) -> MokutekiLayer:
    """Layer A: Structure — Shannon redundancy, app count, collections."""
    # A1: Shannon redundancy (from the shannon checks)
    checks = run_all_checks(ws)
    report = build_report(checks, 5)
    a1 = MokutekiComponent(
        name="Shannon redundancy", weight=0.40, score=report.overall_score,
        details=f"redundancy_rate={report.redundancy_rate*100:.1f}%",
    )

    # A2: App count (connectivity proxy) — count kotodama.jsonld files
    meta = _scan_app_meta(ws)
    total_apps = len(meta)
    apps_with_collections = sum(1 for m in meta.values() if m["collections"])
    connectivity_score = min(100.0, (apps_with_collections / max(total_apps, 1)) * 100)
    a2 = MokutekiComponent(
        name="Directed graph connectivity (proxy)", weight=0.30, score=connectivity_score,
        details=f"apps_with_collections={apps_with_collections}/{total_apps}",
    )

    # A3: Hypergraph coupling — fewer multi-writer collections = better
    # (simplified: count collections mentioned in multiple kotodama.jsonld)
    coll_writers: dict[str, set[str]] = {}
    for nanoid, m in meta.items():
        for c in m["collections"]:
            coll_writers.setdefault(c, set()).add(nanoid)
    multi = sum(1 for writers in coll_writers.values() if len(writers) > 1)
    total_colls = len(coll_writers)
    hyper_score = 100.0 * (1.0 - multi / max(total_colls, 1)) if total_colls > 0 else 100.0
    a3 = MokutekiComponent(
        name="Hypergraph coupling", weight=0.15, score=hyper_score,
        details=f"collections={total_colls}, multi_writer={multi}",
    )

    # A4: Type system — WIT exports coverage
    with_exports = sum(1 for m in meta.values() if m["wit_exports"])
    type_score = (with_exports / max(total_apps, 1)) * 100
    a4 = MokutekiComponent(
        name="Category/type system", weight=0.15, score=type_score,
        details=f"typed={with_exports}/{total_apps}",
    )

    components = [a1, a2, a3, a4]
    score = _weighted_score(components)
    points = int(score * 0.30 * 120)
    return MokutekiLayer(id="A", name="Structure", name_jp="構造",
                         weight=0.30, score=score, points=points, components=components)


def eval_layer_b_stub() -> MokutekiLayer:
    """Layer B: Uncertainty — requires haisen graph (Go binary)."""
    c = MokutekiComponent(
        name="BayesNet/causal/bottleneck (Go binary required)", weight=1.0, score=50.0,
        details="run `etzhayyim shannon bayesnet` + `etzhayyim shannon bottleneck` for full evaluation",
    )
    score = 50.0
    points = int(score * 0.25 * 120)
    return MokutekiLayer(id="B", name="Uncertainty", name_jp="不確実性",
                         weight=0.25, score=score, points=points, components=[c])


def eval_layer_c_stub() -> MokutekiLayer:
    """Layer C: Control — requires haisen graph (Go binary)."""
    c = MokutekiComponent(
        name="POMDP/MPC/bandit (Go binary required)", weight=1.0, score=50.0,
        details="run `etzhayyim mokuteki` (Go binary) for full evaluation",
    )
    score = 50.0
    points = int(score * 0.20 * 120)
    return MokutekiLayer(id="C", name="Control", name_jp="制御",
                         weight=0.20, score=score, points=points, components=[c])


def eval_layer_d(ws: Path) -> MokutekiLayer:
    """Layer D: Implementation — local filesystem scan."""
    meta = _scan_app_meta(ws)
    total = len(meta)

    # D1: Event sourcing — apps with collections (reactive Design E proxy)
    with_trigger = sum(1 for m in meta.values() if m["collections"])
    d1_score = (with_trigger / max(total, 1)) * 100
    d1 = MokutekiComponent(
        name="Event sourcing (Design E)", weight=0.25, score=d1_score,
        details=f"reactive={with_trigger}/{total}",
    )

    # D2: Immutable log — apps with a DID
    with_did = sum(1 for m in meta.values() if m["did"])
    d2_score = (with_did / max(total, 1)) * 100
    d2 = MokutekiComponent(
        name="Immutable log (AT Protocol)", weight=0.20, score=d2_score,
        details=f"with_DID={with_did}/{total}",
    )

    # D3: Policy as code — CLAUDE.md presence per project dir
    project_dirs = {f.parent.parent for f in ws.rglob("kotodama.jsonld")}
    with_claude_md = sum(1 for d in project_dirs if (d / "CLAUDE.md").exists())
    d3_score = (with_claude_md / max(len(project_dirs), 1)) * 100
    d3 = MokutekiComponent(
        name="Policy as code (CLAUDE.md coverage)", weight=0.15, score=d3_score,
        details=f"with_CLAUDE.md={with_claude_md}/{len(project_dirs)}",
    )

    # D4: Typed schema — WIT exports
    with_exports = sum(1 for m in meta.values() if m["wit_exports"])
    d4_score = (with_exports / max(total, 1)) * 100
    d4 = MokutekiComponent(
        name="Typed schema (WIT)", weight=0.20, score=d4_score,
        details=f"with_exports={with_exports}/{total}",
    )

    # D5: Attestation — DID + display_name
    attested = sum(1 for m in meta.values() if m["did"] and m["display_name"])
    d5_score = (attested / max(total, 1)) * 100
    d5 = MokutekiComponent(
        name="Attestation (DID+profile)", weight=0.20, score=d5_score,
        details=f"attested={attested}/{total}",
    )

    components = [d1, d2, d3, d4, d5]
    score = _weighted_score(components)
    points = int(score * 0.25 * 120)
    return MokutekiLayer(id="D", name="Implementation", name_jp="実装",
                         weight=0.25, score=score, points=points, components=components)


def derive_axes(a: MokutekiLayer, b: MokutekiLayer,
                c: MokutekiLayer, d: MokutekiLayer) -> list[MokutekiAxis]:
    engagement   = a.score * 0.5 + d.score * 0.5
    competence   = a.score * 0.6 + b.score * 0.4
    contribution = b.score * 0.4 + c.score * 0.6
    growth       = c.score * 0.5 + a.score * 0.5
    resilience   = b.score * 0.5 + d.score * 0.5

    axes = [
        MokutekiAxis("Engagement (参与)",   0.25, engagement,   int(engagement   * 0.25 * 120), "Layer A + D"),
        MokutekiAxis("Competence (能力)",   0.25, competence,   int(competence   * 0.25 * 120), "Layer A + B"),
        MokutekiAxis("Contribution (貢献)", 0.20, contribution, int(contribution * 0.20 * 120), "Layer B + C"),
        MokutekiAxis("Growth (成長)",       0.20, growth,       int(growth       * 0.20 * 120), "Layer C + A"),
        MokutekiAxis("Resilience (回復)",   0.10, resilience,   int(resilience   * 0.10 * 120), "Layer B + D"),
    ]
    return axes


def build_mokuteki_report(ws: Path) -> MokutekiReport:
    layer_a = eval_layer_a(ws)
    layer_b = eval_layer_b_stub()
    layer_c = eval_layer_c_stub()
    layer_d = eval_layer_d(ws)

    layers = [layer_a, layer_b, layer_c, layer_d]
    axes = derive_axes(layer_a, layer_b, layer_c, layer_d)

    total_score = sum(l.points for l in layers)
    rank = resolve_rank(total_score)

    # Diagnosis
    diag: list[str] = []
    for l in layers:
        if l.score < 30:
            diag.append(f"[CRITICAL] Layer {l.id} ({l.name_jp}): {l.score:.0f}/100")
        elif l.score < 60:
            diag.append(f"[IMPROVE] Layer {l.id} ({l.name_jp}): {l.score:.0f}/100")
        for c in l.components:
            if c.score < 30 and c.weight >= 0.15:
                diag.append(f"  └ {c.name}: {c.score:.0f}/100 — {c.details}")

    for ax in sorted(axes, key=lambda x: x.score):
        if ax.score < 50:
            diag.append(f"[WELLBEING] {ax.name}: {ax.score:.0f}/100 ← {ax.source}")

    next_r, pts_needed = next_rank(total_score)
    if next_r:
        diag.append(f"[NEXT] {rank.name} → {next_r} (need {pts_needed} pts)")

    if not diag:
        diag = ["all layers aligned with mokuteki"]

    return MokutekiReport(
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        mokuteki="Global Well-Becoming Generative Society",
        principle="DSMで依存構造を表現し、Bayesで不確実性を伝播させ、POMDPで観測と制御を最適化する",
        layers=layers,
        axes=axes,
        total_score=total_score,
        max_score=12000,
        rank=rank,
        diagnosis=diag,
    )


def _bar(score: float, width: int = 20) -> str:
    filled = min(int(score / 100 * width), width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


def _print_text(r: MokutekiReport) -> None:
    click.echo(f"mokuteki (目的): {r.mokuteki}")
    click.echo(f"  principle: {r.principle}")
    click.echo()
    click.echo(f"  ╔══════════════════════════════════════╗")
    click.echo(f"  ║  RANK: {r.rank.name:<10}  SCORE: {r.total_score:>5}/{r.max_score}  ║")
    click.echo(f"  ╚══════════════════════════════════════╝")
    click.echo()
    click.echo(f"  layers:")
    for l in r.layers:
        bar = _bar(l.score)
        click.echo(f"    Layer {l.id} {l.name_jp:<15} {bar} {l.score:5.1f}  ({l.points} pts, ×{l.weight*100:.0f}%)")
        for c in l.components:
            marker = "!!" if c.score < 30 else ("! " if c.score < 60 else "  ")
            click.echo(f"      {marker} {c.name:<28} {c.score:5.1f} (×{c.weight*100:.0f}%)")
    click.echo()
    click.echo(f"  well-becoming:")
    for ax in r.axes:
        bar = _bar(ax.score)
        click.echo(f"    {ax.name:<24} {bar} {ax.score:5.1f}  ({ax.points} pts)")
    click.echo()
    if r.diagnosis:
        click.echo(f"  diagnosis:")
        for d in r.diagnosis:
            click.echo(f"    {d}")


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group("mokuteki", invoke_without_command=True)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.pass_context
def mokuteki(ctx: click.Context, json_out: bool, workspace_dir: str | None):
    """Purpose-driven 4-layer Shannon optimization evaluator."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    report = build_mokuteki_report(ws)
    if json_out:
        click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_text(report)


# ── kashika (visualization) ────────────────────────────────────────────────────

_KASHIKA_HTML_TMPL = """\
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"><title>Mokuteki Kashika</title>
<style>
body{{font-family:system-ui,sans-serif;background:#0a0a0a;color:#e0e0e0;margin:0;padding:24px}}
h1{{color:#00d4ff;margin-bottom:4px}}
.subtitle{{color:#888;margin-bottom:24px;font-size:.9em}}
.rank{{display:inline-block;padding:4px 12px;border-radius:4px;font-weight:bold;margin-bottom:20px}}
.layers{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-bottom:24px}}
.layer{{background:#1a1a2e;border:1px solid #333;border-radius:8px;padding:16px}}
.layer h3{{margin:0 0 8px;color:#00d4ff;font-size:.95em}}
.bar-bg{{background:#333;border-radius:4px;height:8px;margin-bottom:12px}}
.bar-fill{{height:8px;border-radius:4px;background:linear-gradient(90deg,#00d4ff,#0066ff)}}
.axes{{margin-bottom:24px}}
.axis{{display:flex;align-items:center;gap:12px;margin-bottom:6px;font-size:.88em}}
.axis-name{{width:180px;color:#aaa}}
.axis-pts{{width:60px;text-align:right;color:#00d4ff}}
.diagnosis{{background:#1a1a2e;border-left:3px solid #ff6b6b;padding:12px 16px;border-radius:0 8px 8px 0}}
.diagnosis h3{{margin:0 0 8px;color:#ff6b6b}}
.diagnosis li{{margin-bottom:4px;font-size:.9em}}
</style>
</head>
<body>
<h1>Mokuteki 目的</h1>
<div class="subtitle">{mokuteki}</div>
<div class="rank" style="background:{rank_color}">{rank_name} — {total_score}/{max_score} pts</div>
<div class="layers" id="layers"></div>
<div class="axes"><h3 style="color:#00d4ff">Well-Becoming Axes</h3><div id="axes"></div></div>
{diagnosis_html}
<script>
const DATA = {data_json};
const layers = document.getElementById('layers');
DATA.layers.forEach(l => {{
  const pct = Math.round(l.score * 100);
  layers.innerHTML += `<div class="layer"><h3>${{l.name_jp}} (${{l.id}})</h3>
  <div class="bar-bg"><div class="bar-fill" style="width:${{pct}}%"></div></div>
  <div style="font-size:.85em;color:#aaa">${{pct}}% · ${{l.points}} pts</div></div>`;
}});
const axesEl = document.getElementById('axes');
DATA.axes.forEach(a => {{
  axesEl.innerHTML += `<div class="axis"><span class="axis-name">${{a.name}}</span>
  <span class="axis-pts">${{a.points}} pts</span>
  <span style="font-size:.8em;color:#666">${{a.source}}</span></div>`;
}});
</script>
</body></html>
"""


def _flatten_report(report: "MokutekiReport") -> dict:
    d = report.to_dict()
    flat: dict[str, Any] = {
        "generated_at": d["generated_at"],
        "total_score": d["total_score"],
        "max_score": d["max_score"],
        "rank_name": d["rank"]["name"],
    }
    for layer in d["layers"]:
        lid = layer["id"].lower()
        flat[f"layer_{lid}_score"] = layer["score"]
        flat[f"layer_{lid}_points"] = layer["points"]
    for axis in d["axes"]:
        key = re.sub(r"[^a-z0-9]+", "_", axis["name"].lower()).strip("_")
        flat[f"axis_{key}_points"] = axis["points"]
    flat["diagnosis"] = json.dumps(d["diagnosis"], ensure_ascii=False)
    return flat


def _catalog_path(data_dir: Path) -> Path:
    return data_dir / "catalog.json"


def _load_catalog(data_dir: Path) -> dict:
    p = _catalog_path(data_dir)
    if p.exists():
        return json.loads(p.read_text())
    return {
        "format_version": 1,
        "table_uuid": "mokuteki-local-001",
        "location": str(data_dir),
        "schema": "generated_at STRING, total_score INT, max_score INT, rank_name STRING",
        "snapshots": [],
        "current_id": "",
    }


def _save_catalog(data_dir: Path, cat: dict) -> None:
    _catalog_path(data_dir).write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n")


@mokuteki.command("kashika")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--format", "fmt", default="html",
              type=click.Choice(["html", "terminal", "json", "dot"]), show_default=True)
@click.option("--output", "output_path", default=None, help="Output file path")
@click.option("--no-open", is_flag=True, default=False, help="Do not open browser")
def mokuteki_kashika(workspace_dir: str | None, fmt: str, output_path: str | None, no_open: bool) -> None:
    """Visualize mokuteki report as HTML, JSON, DOT, or terminal."""
    ws = _resolve_root(workspace_dir)
    report = build_mokuteki_report(ws)

    if fmt == "terminal":
        _print_text(report)
        return

    if fmt == "json":
        out = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
        if output_path:
            Path(output_path).write_text(out)
        else:
            click.echo(out)
        return

    if fmt == "dot":
        d = report.to_dict()
        lines = ["digraph mokuteki {", f'  label="{d["mokuteki"]}"', '  rankdir=LR']
        for layer in d["layers"]:
            lines.append(f'  {layer["id"]} [label="{layer["name_jp"]}\\n{layer["points"]}pts"]')
        lines.append("}")
        out = "\n".join(lines)
        if output_path:
            Path(output_path).write_text(out)
        else:
            click.echo(out)
        return

    # html
    d = report.to_dict()
    diag = d.get("diagnosis", [])
    diag_html = ""
    if diag:
        items = "".join(f"<li>{x}</li>" for x in diag)
        diag_html = f'<div class="diagnosis"><h3>Diagnosis</h3><ul>{items}</ul></div>'
    html = _KASHIKA_HTML_TMPL.format(
        mokuteki=d["mokuteki"],
        rank_color=d["rank"]["color"] if d["rank"]["color"] != "#000000" else "#222",
        rank_name=d["rank"]["name"],
        total_score=d["total_score"],
        max_score=d["max_score"],
        data_json=json.dumps(d, ensure_ascii=False),
        diagnosis_html=diag_html,
    )
    dest = output_path or "/tmp/mokuteki-kashika.html"
    Path(dest).write_text(html)
    click.echo(f"kashika: wrote {dest}", err=True)
    if not no_open:
        webbrowser.open(f"file://{dest}")


@mokuteki.command("store")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--data-dir", "data_dir_opt", default=None, help="Override 80-data/mokuteki/ path")
def mokuteki_store(workspace_dir: str | None, json_out: bool, data_dir_opt: str | None) -> None:
    """Evaluate mokuteki and store snapshot as Parquet."""
    ws = _resolve_root(workspace_dir)
    report = build_mokuteki_report(ws)
    flat = _flatten_report(report)

    data_dir = Path(data_dir_opt) if data_dir_opt else (ws / "80-data" / "mokuteki")
    data_dir.mkdir(parents=True, exist_ok=True)

    snap_id = str(uuid.uuid4())[:8]
    snap_ms = int(time.time() * 1000)
    parquet_name = f"snapshot-{snap_ms}-{snap_id}.parquet"
    parquet_path = data_dir / parquet_name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        tf.write(json.dumps([flat], ensure_ascii=False))
        tmp_json = tf.name

    try:
        sql = (
            f"COPY (SELECT * FROM read_json_auto('{tmp_json}')) "
            f"TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        r = subprocess.run(["duckdb", "-c", sql], capture_output=True, text=True)
        if r.returncode != 0:
            click.echo(f"duckdb error: {r.stderr.strip()}", err=True)
            sys.exit(1)
    finally:
        os.unlink(tmp_json)

    cat = _load_catalog(data_dir)
    cat["snapshots"].append({
        "snapshot_id": snap_id,
        "snapshot_ms": snap_ms,
        "summary": f"{report.rank.name} score={report.total_score}",
        "data_file": parquet_name,
    })
    cat["current_id"] = snap_id
    _save_catalog(data_dir, cat)

    if json_out:
        click.echo(json.dumps({
            "snapshot_id": snap_id,
            "snapshot_ms": snap_ms,
            "parquet": str(parquet_path),
            "total_score": report.total_score,
            "rank": report.rank.name,
        }, ensure_ascii=False, indent=2))
    else:
        click.echo(f"mokuteki store: {snap_id}  {report.rank.name}  score={report.total_score}  → {parquet_name}")


@mokuteki.command("query")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--data-dir", "data_dir_opt", default=None)
@click.option("--sql", "sql_query", default=None,
              help="Custom SQL. Use $TABLE for the parquet glob expression.")
def mokuteki_query(workspace_dir: str | None, data_dir_opt: str | None, sql_query: str | None) -> None:
    """Query stored mokuteki snapshots via duckdb."""
    ws = _resolve_root(workspace_dir)
    data_dir = Path(data_dir_opt) if data_dir_opt else (ws / "80-data" / "mokuteki")
    parquet_glob = str(data_dir / "*.parquet")

    table_expr = f"read_parquet('{parquet_glob}')"
    if sql_query:
        sql = sql_query.replace("$TABLE", table_expr)
    else:
        sql = (
            f"SELECT generated_at, rank_name, total_score, max_score "
            f"FROM {table_expr} "
            f"ORDER BY generated_at DESC LIMIT 20"
        )

    r = subprocess.run(["duckdb", "-c", sql], capture_output=True, text=True)
    if r.returncode != 0:
        click.echo(f"duckdb error: {r.stderr.strip()}", err=True)
        sys.exit(1)
    click.echo(r.stdout, nl=False)


@mokuteki.command("history")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--data-dir", "data_dir_opt", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def mokuteki_history(workspace_dir: str | None, data_dir_opt: str | None, json_out: bool) -> None:
    """List stored mokuteki snapshots."""
    ws = _resolve_root(workspace_dir)
    data_dir = Path(data_dir_opt) if data_dir_opt else (ws / "80-data" / "mokuteki")
    cat = _load_catalog(data_dir)
    snapshots = sorted(cat.get("snapshots", []), key=lambda s: s.get("snapshot_ms", 0), reverse=True)

    if json_out:
        click.echo(json.dumps({"total": len(snapshots), "snapshots": snapshots}, ensure_ascii=False, indent=2))
        return

    if not snapshots:
        click.echo("mokuteki history: no snapshots")
        return

    click.echo(f"mokuteki history: {len(snapshots)} snapshots")
    for s in snapshots:
        ms = s.get("snapshot_ms", 0)
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ms / 1000)) if ms else "?"
        click.echo(f"  {s.get('snapshot_id','?'):10}  {ts}  {s.get('summary','')}")
