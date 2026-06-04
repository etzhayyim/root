"""bonsai — Workspace growth/prune analysis (ADR-2605080100, ADR-2605091300).

6-tier pruning: fruit/flower/leaf/branch/trunk/seed.
Scans workspace for growth indicators and prune candidates.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import click

from .shannon import _resolve_root


# ── pruning tiers ──────────────────────────────────────────────────────────────

PRUNE_TIERS = ["fruit", "flower", "leaf", "branch", "trunk", "seed"]

_TIER_HINTS: dict[str, list[str]] = {
    "fruit":  ["TODO", "FIXME", "HACK", "TEMP", "xxx"],
    "flower": ["test_", "_test", ".spec.", ".test."],
    "leaf":   [".md", ".txt", ".yaml", ".yml", ".toml"],
    "branch": [".ts", ".py", ".go"],
    "trunk":  ["magatama.jsonld", "wrangler.jsonc", "pyproject.toml"],
    "seed":   ["deps.toml", "CLAUDE.md"],
}

_RE_TODO = re.compile(r'\b(TODO|FIXME|HACK|TEMP|XXX)\b', re.IGNORECASE)
_RE_DEAD_CODE = re.compile(r'//\s*(?:dead|unused|legacy|deprecated)\b', re.IGNORECASE)


@dataclass
class BonsaiNode:
    path: str
    tier: str
    lines: int
    prune_score: int  # 0–100: higher = more pruneable
    signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path, "tier": self.tier, "lines": self.lines,
            "prune_score": self.prune_score, "signals": self.signals,
        }


@dataclass
class BonsaiReport:
    evaluated_at: str
    total_files: int
    total_lines: int
    tier_counts: dict[str, int]
    prune_candidates: list[BonsaiNode]
    growth_score: int  # 0–100

    def to_dict(self) -> dict:
        return {
            "evaluated_at": self.evaluated_at,
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "tier_counts": self.tier_counts,
            "prune_candidates": [n.to_dict() for n in self.prune_candidates],
            "growth_score": self.growth_score,
        }


# ── analysis ───────────────────────────────────────────────────────────────────

_SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build", ".langgraph_api"}
_SOURCE_EXTS = {".ts", ".py", ".go", ".rs", ".svelte"}
_IGNORE_EXTS = {".lock", ".pckl", ".pyc", ".wasm"}


def _classify_tier(path: Path) -> str:
    name = path.name
    for tier, hints in _TIER_HINTS.items():
        if any(hint in name for hint in hints):
            return tier
    if path.suffix in _SOURCE_EXTS:
        return "branch"
    if path.suffix in {".md", ".txt", ".yaml", ".yml", ".toml", ".json"}:
        return "leaf"
    return "leaf"


def _score_node(path: Path, content: str) -> tuple[int, list[str]]:
    signals = []
    score = 0

    todos = _RE_TODO.findall(content)
    if todos:
        score += min(len(todos) * 10, 30)
        signals.append(f"{len(todos)} TODO/FIXME")

    dead = _RE_DEAD_CODE.findall(content)
    if dead:
        score += 20
        signals.append("dead code comments")

    lines = content.count("\n")
    if lines == 0:
        score += 40
        signals.append("empty file")
    elif lines < 5:
        score += 20
        signals.append(f"trivial ({lines} lines)")

    if re.search(r'(?:^|_)(deprecated|legacy|old|backup|bak)(?:_|$|\.)', path.name, re.IGNORECASE):
        score += 30
        signals.append("legacy name")

    return min(score, 100), signals


def scan_workspace(ws: Path, prune_threshold: int = 50) -> BonsaiReport:
    tier_counts: dict[str, int] = {t: 0 for t in PRUNE_TIERS}
    nodes: list[BonsaiNode] = []
    total_lines = 0

    for p in ws.rglob("*"):
        if not p.is_file():
            continue
        if any(d in p.parts for d in _SKIP_DIRS):
            continue
        if p.suffix in _IGNORE_EXTS:
            continue

        tier = _classify_tier(p)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        if p.suffix not in _SOURCE_EXTS:
            continue

        try:
            content = p.read_text(errors="replace")
        except OSError:
            continue

        lines = content.count("\n")
        total_lines += lines
        prune_score, signals = _score_node(p, content)

        rel = str(p.relative_to(ws))
        nodes.append(BonsaiNode(path=rel, tier=tier, lines=lines,
                                prune_score=prune_score, signals=signals))

    candidates = sorted(
        [n for n in nodes if n.prune_score >= prune_threshold],
        key=lambda n: n.prune_score, reverse=True,
    )

    total_files = sum(tier_counts.values())
    fruit_count = tier_counts.get("fruit", 0) + tier_counts.get("flower", 0)
    growth_score = max(0, 100 - int(fruit_count / max(total_files, 1) * 100))

    return BonsaiReport(
        evaluated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        total_files=total_files,
        total_lines=total_lines,
        tier_counts=tier_counts,
        prune_candidates=candidates,
        growth_score=growth_score,
    )


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group("bonsai", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def bonsai(ctx: click.Context, workspace_dir: str | None, json_out: bool) -> None:
    """Bonsai growth/prune workspace analysis (ADR-2605080100)."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    report = scan_workspace(ws)
    if json_out:
        click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        click.echo(f"bonsai: growth={report.growth_score}  files={report.total_files}  "
                   f"lines={report.total_lines}")
        click.echo("  tiers: " + "  ".join(
            f"{t}={report.tier_counts.get(t, 0)}" for t in PRUNE_TIERS
        ))
        if report.prune_candidates:
            click.echo(f"  prune candidates: {len(report.prune_candidates)}")


@bonsai.command("scan")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def bonsai_scan(workspace_dir: str | None, json_out: bool) -> None:
    """Scan workspace growth metrics."""
    ws = _resolve_root(workspace_dir)
    report = scan_workspace(ws)
    if json_out:
        click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        click.echo(f"files={report.total_files}  lines={report.total_lines}  "
                   f"growth={report.growth_score}")


@bonsai.command("prune")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--threshold", default=50, type=int, show_default=True,
              help="Minimum prune score to include (0–100)")
@click.option("--top", default=20, type=int, show_default=True)
def bonsai_prune(workspace_dir: str | None, json_out: bool, threshold: int, top: int) -> None:
    """List top prune candidates."""
    ws = _resolve_root(workspace_dir)
    report = scan_workspace(ws, prune_threshold=threshold)
    candidates = report.prune_candidates[:top]
    if json_out:
        click.echo(json.dumps([n.to_dict() for n in candidates], ensure_ascii=False, indent=2))
    else:
        if not candidates:
            click.echo("  no prune candidates above threshold")
        for n in candidates:
            signals = ", ".join(n.signals)
            click.echo(f"  [{n.prune_score:3d}] [{n.tier:6}] {n.path}  ({signals})")


@bonsai.command("status")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def bonsai_status(workspace_dir: str | None, json_out: bool) -> None:
    """Overall bonsai ecosystem health."""
    ws = _resolve_root(workspace_dir)
    report = scan_workspace(ws)
    health = "healthy" if report.growth_score >= 70 else "needs pruning" if report.growth_score >= 40 else "overgrown"
    if json_out:
        click.echo(json.dumps({
            "health": health,
            "growth_score": report.growth_score,
            "prune_candidates": len(report.prune_candidates),
        }, ensure_ascii=False, indent=2))
    else:
        click.echo(f"bonsai status: {health}  growth={report.growth_score}  "
                   f"prune_candidates={len(report.prune_candidates)}")


@bonsai.command("canopy")
@click.option("--min-eta", default=0.0, type=float, show_default=True)
@click.option("--max-eta", default=1.0, type=float, show_default=True)
@click.option("--status", "status_filter", default="", help="alive|dormant|blocked")
@click.option("--limit", default=100, type=int, show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
def bonsai_canopy(min_eta: float, max_eta: float, status_filter: str,
                  limit: int, json_out: bool) -> None:
    """Live canopy shape with Shannon η scores (requires DB — use Go binary)."""
    raise click.ClickException(
        "bonsai canopy requires direct RisingWave access (etzhayyimdb). "
        "Use the Go binary: etzhayyim bonsai canopy"
    )


@bonsai.command("growth")
@click.option("--type", "growth_type", default="", help="actor|table|mv|bpmn|udf")
@click.option("--limit", default=50, type=int, show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
def bonsai_growth(growth_type: str, limit: int, json_out: bool) -> None:
    """Growth event log from vertex_growth_event (requires DB — use Go binary)."""
    raise click.ClickException(
        "bonsai growth requires direct RisingWave access (etzhayyimdb). "
        "Use the Go binary: etzhayyim bonsai growth"
    )


@bonsai.command("release")
@click.argument("actor_did")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--yes", is_flag=True, default=False)
def bonsai_release(actor_did: str, json_out: bool, yes: bool) -> None:
    """Release anastomosis gate for an actor (requires DB — use Go binary)."""
    raise click.ClickException(
        "bonsai release requires direct RisingWave access (etzhayyimdb). "
        "Use the Go binary: etzhayyim bonsai release"
    )
