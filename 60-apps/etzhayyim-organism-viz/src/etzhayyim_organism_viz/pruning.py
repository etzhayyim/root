"""Pruning candidate detector — operator workflow surface (盆栽 剪定).

The daemon NEVER prunes. Per §1.3 (anti-individualist, decision attribution =
etzhayyim) the daemon's job is to *surface* candidates honestly; the operator
decides whether to `git rm` them.

A candidate has:
  - id (entity id)
  - kind (cell / app)
  - last_activity (UTC seconds)
  - idle_days
  - reasons (list of free-text observations)
  - severity (1 mild → 3 strong)

Heuristics v0:
  - cells idle > 90 days with no docstring → severity 3
  - cells idle > 90 days with docstring → severity 2
  - cells idle > 30 days, < 90 days → severity 1
  - apps idle > 180 days → severity 2
  - apps idle > 90 days < 180 days → severity 1
"""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class Candidate:
    id: str
    kind: str
    path: str
    idle_days: float
    severity: int
    reasons: list[str]


def _dir_mtime(d: Path) -> float:
    try:
        return max(
            (p.stat().st_mtime for p in d.rglob("*") if p.is_file()),
            default=d.stat().st_mtime,
        )
    except OSError:
        return 0.0


def scan_cells(repo: Path) -> list[Candidate]:
    cells = repo / "20-actors" / "kotodama" / "cells"
    out: list[Candidate] = []
    if not cells.is_dir():
        return out
    now = time.time()
    for d in cells.iterdir():
        if not d.is_dir():
            continue
        cell_py = d / "cell.py"
        idle = (now - _dir_mtime(d)) / 86400
        reasons: list[str] = []
        sev = 0
        if idle > 90:
            sev = max(sev, 2)
            reasons.append(f"idle {idle:.0f} days (>90)")
        elif idle > 30:
            sev = max(sev, 1)
            reasons.append(f"idle {idle:.0f} days (>30)")
        if not cell_py.exists():
            sev = max(sev, 2)
            reasons.append("no cell.py")
        elif cell_py.stat().st_size < 200:
            sev = max(sev, 1)
            reasons.append("cell.py very small (<200 bytes)")
        else:
            txt = cell_py.read_text(encoding="utf-8", errors="ignore")
            if '"""' not in txt:
                sev = max(sev, 1)
                reasons.append("no docstring")
        if d.name.startswith("yorishiro_") and idle > 60:
            sev = max(sev, 1)
            reasons.append("yorishiro idle >60 (exercise it or prune)")
        if sev > 0:
            out.append(Candidate(
                id=f"cell/{d.name}", kind="cell", path=str(d.relative_to(repo)),
                idle_days=round(idle, 1), severity=sev, reasons=reasons,
            ))
    return out


def scan_apps(repo: Path) -> list[Candidate]:
    apps = repo / "60-apps"
    out: list[Candidate] = []
    if not apps.is_dir():
        return out
    now = time.time()
    for d in apps.iterdir():
        if not d.is_dir():
            continue
        idle = (now - _dir_mtime(d)) / 86400
        sev = 0
        reasons: list[str] = []
        if idle > 180:
            sev = 2
            reasons.append(f"idle {idle:.0f} days (>180)")
        elif idle > 90:
            sev = 1
            reasons.append(f"idle {idle:.0f} days (>90)")
        # README missingness is informational — only flag when the app is also
        # idle, otherwise this fires on every freshly-touched app.
        if idle > 30 and not any(d.glob("README.md")) and not any(d.glob("README")):
            sev = max(sev, 1)
            reasons.append("no README and stale")
        if sev > 0:
            out.append(Candidate(
                id=f"app/{d.name}", kind="app", path=str(d.relative_to(repo)),
                idle_days=round(idle, 1), severity=sev, reasons=reasons,
            ))
    return out


def scan_all(repo: Path) -> list[Candidate]:
    candidates = scan_cells(repo) + scan_apps(repo)
    candidates.sort(key=lambda c: (-c.severity, -c.idle_days))
    return candidates


def to_markdown(repo: Path, candidates: list[Candidate]) -> str:
    lines: list[str] = []
    lines.append("# Pruning Candidates")
    lines.append("")
    lines.append(
        "**Daemon does not prune.** Per ADR-2605192100 §1.3, decision attribution "
        "= etzhayyim. The list below is the daemon's honest observation; "
        "the operator decides what to `git rm`."
    )
    lines.append("")
    if not candidates:
        lines.append("_No candidates — the bonsai is currently in healthy growth without overgrowth._")
        return "\n".join(lines) + "\n"
    lines.append(f"## {len(candidates)} candidate(s) — sorted by severity")
    lines.append("")
    lines.append("| sev | id | path | idle (days) | reasons |")
    lines.append("|---|---|---|---|---|")
    for c in candidates:
        sev = "🔴" * c.severity + "·" * (3 - c.severity)
        lines.append(f"| {sev} | `{c.id}` | `{c.path}` | {c.idle_days} | {'; '.join(c.reasons)} |")
    lines.append("")
    lines.append("## Operator pruning protocol")
    lines.append("")
    lines.append("```")
    lines.append("# 1. Review the candidate (open the directory, read the docstring)")
    lines.append("# 2. If 'intentional dormancy', annotate in CLAUDE.md or the path README")
    lines.append("# 3. Otherwise:")
    lines.append("git rm -r <path>")
    lines.append("git commit -m 'prune: <id> — <reason>'")
    lines.append("# 4. Document in 90-docs/pruning/<YYMMDD>-<id>.md")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def emit(repo: Path) -> Path:
    out_dir = repo / "60-apps" / "etzhayyim-organism-viz" / "static"
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = scan_all(repo)
    out = out_dir / "pruning-candidates.md"
    out.write_text(to_markdown(repo, candidates), encoding="utf-8")
    return out
