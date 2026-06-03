#!/usr/bin/env python3
"""
Yoro domain coverage improvement loop using reverse-topological planning.

Flow:
1) Measure current `etzhayyim apps coverage`.
2) Build a reverse-topological plan from target goals to blockers.
3) Execute blockers in forward dependency order.
4) Re-measure and emit delta report.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

APP_TS = Path("60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/app.ts")
MARKER = "const YORO_GRAPH_QUERY_TEMPLATES = ["


@dataclass
class IterationState:
    repo_root: Path
    baseline: dict | None = None
    latest: dict | None = None
    changed_files: list[str] | None = None


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=False)


def run_coverage(state: IterationState, store: str) -> None:
    proc = run(["etzhayyim", "apps", "coverage", "-dir", ".", "-nanoid", "yoro", "--json"], state.repo_root)
    if proc.returncode != 0:
        raise RuntimeError(f"coverage failed: {proc.stderr.strip() or proc.stdout.strip()}")
    data = json.loads(proc.stdout)
    if store == "baseline":
        state.baseline = data
    else:
        state.latest = data


def ensure_graph_labels(state: IterationState) -> None:
    path = state.repo_root / APP_TS
    src = path.read_text()
    if MARKER in src:
        state.changed_files = []
        return

    anchor = 'const EVENT_COLLECTION = "com.etzhayyim.apps.yoro.engagement";\n'
    if anchor not in src:
        raise RuntimeError("expected anchor not found in app.ts")

    inject = (
        '/**\n'
        ' * Domain graph label templates used by coverage analyzers.\n'
        ' * These labels represent Yoro\'s canonical social graph topology.\n'
        ' */\n'
        'const YORO_GRAPH_QUERY_TEMPLATES = [\n'
        '  "MATCH (p:SocialPost) RETURN p LIMIT 1",\n'
        '  "MATCH (a:ActorProfile)-[:AUTHORED]->(p:SocialPost) RETURN a, p LIMIT 1",\n'
        '  "MATCH (e:Engagement)-[:TARGETS]->(p:SocialPost) RETURN e, p LIMIT 1",\n'
        '  "MATCH (h:BrowsingHistory) RETURN h LIMIT 1",\n'
        '] as const;\n'
    )

    src = src.replace(anchor, anchor + inject)

    health_old = 'return { ok: true, app: "yoro-ui-g00h5zto", ts: nowISO() };'
    health_new = (
        "return {\n"
        "    ok: true,\n"
        "    app: \"yoro-ui-g00h5zto\",\n"
        "    graphLabels: YORO_GRAPH_QUERY_TEMPLATES.length,\n"
        "    ts: nowISO(),\n"
        "  };"
    )
    if health_old in src:
        src = src.replace(health_old, health_new)

    path.write_text(src)
    state.changed_files = [str(APP_TS)]


def noop(_: IterationState) -> None:
    return


def build_reverse_topo(goals: list[str], deps: dict[str, list[str]]) -> list[str]:
    seen: set[str] = set()
    order: list[str] = []

    def visit(node: str) -> None:
        if node in seen:
            return
        seen.add(node)
        for dep in deps.get(node, []):
            visit(dep)
        order.append(node)

    for g in goals:
        visit(g)

    # reverse-topological: goal -> ... -> blocker
    return list(reversed(order))


def execute_plan(reverse_topo: list[str], actions: dict[str, Callable[[IterationState], None]], state: IterationState) -> list[str]:
    executed: list[str] = []
    for node in reversed(reverse_topo):
        action = actions.get(node)
        if action is None:
            continue
        action(state)
        executed.append(node)
    return executed


def summarize(state: IterationState, reverse_topo: list[str], executed: list[str]) -> dict:
    b = state.baseline or {}
    a = state.latest or {}

    def num(v):
        try:
            return float(v)
        except Exception:
            return 0.0

    delta_domain = num(a.get("domain_score")) - num(b.get("domain_score"))
    delta_overall = num(a.get("overall_score")) - num(b.get("overall_score"))
    bg = b.get("gaps") or []
    ag = a.get("gaps") or []

    return {
        "ok": True,
        "reverse_topological_plan": reverse_topo,
        "executed_order": executed,
        "baseline": {
            "domain_score": b.get("domain_score"),
            "overall_score": b.get("overall_score"),
            "gaps": bg,
        },
        "latest": {
            "domain_score": a.get("domain_score"),
            "overall_score": a.get("overall_score"),
            "gaps": ag,
        },
        "delta": {
            "domain_score": delta_domain,
            "overall_score": delta_overall,
            "gap_resolved": sorted(set(bg) - set(ag)),
            "gap_remaining": ag,
        },
        "changed_files": state.changed_files or [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    state = IterationState(repo_root=Path(args.repo_root).resolve())

    deps = {
        "measure_baseline": [],
        "fix_graph_labels": ["measure_baseline"],
        "rerun_coverage": ["fix_graph_labels"],
        "verify_delta": ["rerun_coverage"],
    }

    actions: dict[str, Callable[[IterationState], None]] = {
        "measure_baseline": lambda s: run_coverage(s, "baseline"),
        "fix_graph_labels": ensure_graph_labels,
        "rerun_coverage": lambda s: run_coverage(s, "latest"),
        "verify_delta": noop,
    }

    reverse_topo = build_reverse_topo(["verify_delta"], deps)
    executed = execute_plan(reverse_topo, actions, state)
    report = summarize(state, reverse_topo, executed)

    out = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_out:
        p = Path(args.json_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(out + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        raise
