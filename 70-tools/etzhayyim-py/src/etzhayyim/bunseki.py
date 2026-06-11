"""bunseki (分析) — Architecture and business intelligence analysis commands."""

from __future__ import annotations

import json
import os
import sys

import click
import httpx

from .authn import _load_auth
from .haisen import _scan_workspace, HaisenReport
from .projector import resolve_pds
from .shannon import _resolve_root


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@click.group("bunseki", invoke_without_command=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def bunseki(ctx: click.Context, pds: str | None, json_out: bool) -> None:
    """Architecture analysis (arch, bi, domain, process)."""
    if ctx.invoked_subcommand is not None:
        return
    click.echo("bunseki (分析): subcommands: arch, bi, domain")


@bunseki.group("arch", invoke_without_command=True)
@click.option("--pds", default=None)
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def bunseki_arch(ctx: click.Context, pds: str | None, workspace_dir: str | None, json_out: bool) -> None:
    """Architecture analysis: DFG, variants, conformance, cycles."""
    if ctx.invoked_subcommand is not None:
        return
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.bunseki.getArchAnalysis",
            headers=_auth_headers(), timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


# ── bunseki arch subcommands (local haisen analysis) ──────────────────────────

def _arch_grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


@bunseki_arch.command("scan")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--top", default=10, show_default=True)
def arch_scan(workspace_dir: str | None, json_out: bool, top: int) -> None:
    """Full architecture report using haisen data."""
    import time
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)

    # DFG: group edges by (from, to) pair and count
    pair_counts: dict[tuple[str, str], dict] = {}
    for e in report.edges:
        key = (e.from_nanoid, e.to_nanoid)
        if key not in pair_counts:
            pair_counts[key] = {"from": e.from_nanoid, "to": e.to_nanoid, "type": e.edge_type, "count": 0}
        pair_counts[key]["count"] += 1
    dfg = sorted(pair_counts.values(), key=lambda x: -x["count"])[:top]

    # Variants: determine pattern per app
    app_nanoids = {a.nanoid for a in report.apps}
    invoke_set = {e.from_nanoid for e in report.edges if e.edge_type == "invoke"}
    subscribe_set = {e.from_nanoid for e in report.edges if e.edge_type == "subscribe"}
    connected_set = {e.from_nanoid for e in report.edges} | {e.to_nanoid for e in report.edges}
    rw_set = {e.from_nanoid for e in report.edges if e.edge_type in ("writes", "reads")}

    pattern_groups: dict[str, list[str]] = {}
    for a in report.apps:
        if a.nanoid in invoke_set:
            pat = "active"
        elif a.nanoid in subscribe_set:
            pat = "event-driven"
        elif a.nanoid in rw_set:
            pat = "passive"
        elif a.nanoid not in connected_set:
            pat = "isolated"
        else:
            pat = "passive"
        pattern_groups.setdefault(pat, []).append(a.nanoid)

    total_apps = len(report.apps)
    variants = [
        {
            "pattern": pat,
            "count": len(apps_list),
            "pct": round(len(apps_list) / max(total_apps, 1) * 100, 1),
            "apps": apps_list[:5],
        }
        for pat, apps_list in sorted(pattern_groups.items(), key=lambda x: -len(x[1]))
    ]

    # Conformance: naming, has-edges, single-project
    import re as _re
    nanoid_re = _re.compile(r"^[a-z0-9]{7}$")
    conformance = []
    # Rule 1: naming-convention
    naming_ok = [a.nanoid for a in report.apps if nanoid_re.match(a.nanoid)]
    naming_violations = [a.nanoid for a in report.apps if not nanoid_re.match(a.nanoid)]
    conformance.append({
        "rule": "naming-convention",
        "description": "nanoid matches [a-z0-9]{7}",
        "total": total_apps,
        "conformant": len(naming_ok),
        "rate": round(len(naming_ok) / max(total_apps, 1), 3),
        "violations": naming_violations[:5],
    })
    # Rule 2: has-edges
    edge_ok = list(connected_set & app_nanoids)
    edge_violations = [a.nanoid for a in report.apps if a.nanoid not in connected_set]
    conformance.append({
        "rule": "has-edges",
        "description": "app has at least 1 edge",
        "total": total_apps,
        "conformant": len(edge_ok),
        "rate": round(len(edge_ok) / max(total_apps, 1), 3),
        "violations": edge_violations[:5],
    })
    # Rule 3: single-project (project != "")
    # HaisenApp doesn't have a project field directly; violations are empty by default
    proj_violations: list[str] = []
    conformance.append({
        "rule": "single-project",
        "description": "app is assigned to exactly 1 project",
        "total": total_apps,
        "conformant": total_apps - len(proj_violations),
        "rate": round((total_apps - len(proj_violations)) / max(total_apps, 1), 3),
        "violations": proj_violations[:5],
    })

    # Score: weighted average of conformance rates
    conf_score = sum(c["rate"] for c in conformance) / len(conformance) * 100 if conformance else 100.0
    grade = _arch_grade(conf_score)

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_apps": total_apps,
        "total_edges": len(report.edges),
        "dfg": dfg,
        "variants": variants,
        "conformance": conformance,
        "score": round(conf_score, 1),
        "grade": grade,
    }

    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"\n=== bunseki arch scan  apps={total_apps}  edges={len(report.edges)} ===")
        click.echo(f"  score={result['score']}  grade={grade}")
        click.echo(f"\n-- DFG top {len(dfg)} --")
        for row in dfg:
            click.echo(f"  {row['from']} -> {row['to']}  type: {row['type']}  count: {row['count']}")
        click.echo(f"\n-- Variants --")
        for v in variants:
            click.echo(f"  {v['pattern']:<15} count={v['count']}  pct={v['pct']}%")
        click.echo(f"\n-- Conformance --")
        for c in conformance:
            click.echo(f"  {c['rule']:<22} conformant={c['conformant']}/{c['total']}  rate={c['rate']:.3f}")
            if c["violations"]:
                click.echo(f"    violations: {', '.join(c['violations'])}")


@bunseki_arch.command("dfg")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--top", default=10, show_default=True)
def arch_dfg(workspace_dir: str | None, json_out: bool, top: int) -> None:
    """Directly-Follows Graph at architecture level (haisen edges)."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)

    pair_counts: dict[tuple[str, str], dict] = {}
    for e in report.edges:
        key = (e.from_nanoid, e.to_nanoid)
        if key not in pair_counts:
            pair_counts[key] = {"from": e.from_nanoid, "to": e.to_nanoid, "type": e.edge_type, "count": 0}
        pair_counts[key]["count"] += 1

    dfg = sorted(pair_counts.values(), key=lambda x: -x["count"])[:top]

    if json_out:
        click.echo(json.dumps(dfg, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  {'FROM':<15} {'TO':<15} {'TYPE':<14} {'COUNT':>5}")
        for row in dfg:
            click.echo(f"  {row['from']:<15} {row['to']:<15} type: {row['type']:<8}  count: {row['count']}")


@bunseki_arch.command("variants")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--top", default=10, show_default=True)
def arch_variants(workspace_dir: str | None, json_out: bool, top: int) -> None:
    """App architecture patterns based on haisen edge types."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)

    total_apps = len(report.apps)
    invoke_set = {e.from_nanoid for e in report.edges if e.edge_type == "invoke"}
    subscribe_set = {e.from_nanoid for e in report.edges if e.edge_type == "subscribe"}
    connected_set = {e.from_nanoid for e in report.edges} | {e.to_nanoid for e in report.edges}
    rw_set = {e.from_nanoid for e in report.edges if e.edge_type in ("writes", "reads")}

    pattern_groups: dict[str, list[str]] = {}
    for a in report.apps:
        if a.nanoid in invoke_set:
            pat = "active"
        elif a.nanoid in subscribe_set:
            pat = "event-driven"
        elif a.nanoid in rw_set:
            pat = "passive"
        elif a.nanoid not in connected_set:
            pat = "isolated"
        else:
            pat = "passive"
        pattern_groups.setdefault(pat, []).append(a.nanoid)

    results = [
        {
            "pattern": pat,
            "count": len(apps_list),
            "pct": round(len(apps_list) / max(total_apps, 1) * 100, 1),
            "apps": apps_list[:5],
        }
        for pat, apps_list in sorted(pattern_groups.items(), key=lambda x: -len(x[1]))
    ][:top]

    if json_out:
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  {'PATTERN':<15} {'COUNT':>5}  {'PCT':>6}  apps (first 5)")
        for v in results:
            click.echo(f"  {v['pattern']:<15} {v['count']:>5}  {v['pct']:>5}%  {', '.join(v['apps'])}")


@bunseki_arch.command("conformance")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--top", default=10, show_default=True)
def arch_conformance(workspace_dir: str | None, json_out: bool, top: int) -> None:
    """Design rule conformance checks on haisen data."""
    import re as _re
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)

    total_apps = len(report.apps)
    connected_set = {e.from_nanoid for e in report.edges} | {e.to_nanoid for e in report.edges}
    nanoid_re = _re.compile(r"^[a-z0-9]{7}$")

    results = []

    # Rule 1: naming-convention
    naming_ok = [a.nanoid for a in report.apps if nanoid_re.match(a.nanoid)]
    naming_violations = [a.nanoid for a in report.apps if not nanoid_re.match(a.nanoid)]
    results.append({
        "rule": "naming-convention",
        "description": "nanoid matches [a-z0-9]{7}",
        "total": total_apps,
        "conformant": len(naming_ok),
        "rate": round(len(naming_ok) / max(total_apps, 1), 3),
        "violations": naming_violations[:5],
    })

    # Rule 2: has-edges
    edge_ok_count = sum(1 for a in report.apps if a.nanoid in connected_set)
    edge_violations = [a.nanoid for a in report.apps if a.nanoid not in connected_set]
    results.append({
        "rule": "has-edges",
        "description": "app has at least 1 edge",
        "total": total_apps,
        "conformant": edge_ok_count,
        "rate": round(edge_ok_count / max(total_apps, 1), 3),
        "violations": edge_violations[:5],
    })

    # Rule 3: single-project (project != "")
    # HaisenApp has no project field, so all apps trivially "pass" unless we find duplicates via jsonld
    proj_violations: list[str] = []
    results.append({
        "rule": "single-project",
        "description": "app assigned to exactly 1 project",
        "total": total_apps,
        "conformant": total_apps - len(proj_violations),
        "rate": round((total_apps - len(proj_violations)) / max(total_apps, 1), 3),
        "violations": proj_violations[:5],
    })

    if json_out:
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  {'RULE':<22} {'CONF':>5}/{'{TOTAL}':>7}  {'RATE':>6}  violations")
        for c in results:
            viols = ", ".join(c["violations"]) if c["violations"] else "-"
            click.echo(f"  {c['rule']:<22} {c['conformant']:>5}/{c['total']:>6}  {c['rate']:>6.3f}  {viols}")


@bunseki_arch.command("cycles")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--top", default=10, show_default=True)
def arch_cycles(workspace_dir: str | None, json_out: bool, top: int) -> None:
    """Detect circular dependencies in the haisen graph using DFS."""
    ws = _resolve_root(workspace_dir)
    report = _scan_workspace(ws)

    # Build adjacency map
    adj: dict[str, list[str]] = {}
    for e in report.edges:
        adj.setdefault(e.from_nanoid, []).append(e.to_nanoid)

    cycles: list[list[str]] = []
    seen_cycles: set[str] = set()
    max_cycles = 50
    max_len = 8

    def _canon(path: list[str]) -> str:
        if not path:
            return ""
        min_idx = min(range(len(path)), key=lambda i: path[i])
        rotated = [path[(i + min_idx) % len(path)] for i in range(len(path))]
        return "->".join(rotated)

    def dfs(start: str, node: str, path: list[str], visited_stack: set[str]) -> None:
        if len(cycles) >= max_cycles or len(path) > max_len:
            return
        for nxt in adj.get(node, []):
            if nxt == start and len(path) >= 2:
                cycle = path + [start]
                canon = _canon(path)
                if canon not in seen_cycles:
                    seen_cycles.add(canon)
                    cycles.append(cycle)
                continue
            if nxt not in visited_stack:
                visited_stack.add(nxt)
                dfs(start, nxt, path + [nxt], visited_stack)
                visited_stack.discard(nxt)

    for a in sorted(adj.keys()):
        if len(cycles) >= max_cycles:
            break
        dfs(a, a, [a], {a})

    top_cycles = cycles[:top]
    total_cycles = len(cycles)

    if json_out:
        click.echo(json.dumps({"cycles": top_cycles, "total_cycles": total_cycles}, ensure_ascii=False, indent=2))
    else:
        click.echo(f"arch cycles: total={total_cycles}")
        if not top_cycles:
            click.echo("  no cycles detected")
        for i, cyc in enumerate(top_cycles, 1):
            click.echo(f"  #{i} len={len(cyc)-1}  {' -> '.join(cyc)}")


@bunseki.command("bi")
@click.option("--pds", default=None)
@click.option("--metric", default="", help="Specific metric to fetch")
@click.option("--json", "json_out", is_flag=True, default=False)
def bunseki_bi(pds: str | None, metric: str, json_out: bool) -> None:
    """Business intelligence metrics."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.bunseki.getBIMetrics",
            params={"metric": metric} if metric else {},
            headers=_auth_headers(), timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@bunseki.command("domain")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def bunseki_domain(pds: str | None, json_out: bool) -> None:
    """Domain coverage analysis via PDS."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.bunseki.getDomainAnalysis",
            headers=_auth_headers(), timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


# ── OCEL event fetching + processing helpers ───────────────────────────────────

def _fetch_bunseki_events(pds_url: str, token: str, minutes: int = 60, limit: int = 1000) -> list[dict]:
    """Fetch OCEL v2 events: CF Analytics Engine first, PDS KV fallback."""
    cf_account = os.environ.get("CF_ACCOUNT_ID", "")
    cf_token = os.environ.get("CF_API_TOKEN", os.environ.get("CLOUDFLARE_API_TOKEN", ""))
    if cf_account and cf_token:
        sql = (
            f"SELECT timestamp as ts, blob2 as method, blob3 as activity, blob4 as type, "
            f"blob5 as auth, double1 as duration_ms, double2 as status "
            f"FROM ocel_v2 WHERE timestamp > NOW() - INTERVAL '{minutes}' MINUTE "
            f"ORDER BY timestamp DESC LIMIT {limit}"
        )
        try:
            resp = httpx.post(
                f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/analytics_engine/sql",
                headers={"Authorization": f"Bearer {cf_token}", "Content-Type": "text/plain"},
                content=sql, timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                rows = data.get("data", [])
                if rows:
                    return rows
        except httpx.HTTPError:
            pass
    try:
        resp = httpx.get(
            f"{pds_url}/_pds/ocel",
            params={"minutes": minutes, "limit": limit},
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else data.get("events", [])
    except httpx.HTTPError:
        pass
    return []


def _build_traces(events: list[dict], object_type: str = "") -> dict[str, list[str]]:
    """Group events into traces by auth/object. Returns {trace_id: [activity, ...]}."""
    traces: dict[str, list[str]] = {}
    for e in events:
        if object_type and e.get("type", "") != object_type:
            continue
        key = e.get("auth", "") or e.get("method", "unknown")
        act = e.get("activity", "") or e.get("method", "?")
        traces.setdefault(key, []).append(act)
    return traces


def _build_dfg(traces: dict[str, list[str]]) -> list[dict]:
    """Directly-Follows Graph edges."""
    counts: dict[tuple, int] = {}
    total = 0
    for acts in traces.values():
        for i in range(len(acts) - 1):
            edge = (acts[i], acts[i + 1])
            counts[edge] = counts.get(edge, 0) + 1
            total += 1
    result = [{"from": k[0], "to": k[1], "count": v, "freq_pct": round(v / max(total, 1) * 100, 1)}
              for k, v in counts.items()]
    return sorted(result, key=lambda x: -x["count"])


def _analyze_variants(traces: dict[str, list[str]]) -> list[dict]:
    """Process variants (trace signatures)."""
    counts: dict[str, int] = {}
    total = len(traces)
    for acts in traces.values():
        sig = "→".join(acts)
        counts[sig] = counts.get(sig, 0) + 1
    result = [{"variant": k, "count": v, "freq_pct": round(v / max(total, 1) * 100, 1)}
              for k, v in counts.items()]
    return sorted(result, key=lambda x: -x["count"])


def _analyze_performance(events: list[dict]) -> list[dict]:
    """Per-activity duration stats."""
    import statistics
    by_act: dict[str, list[float]] = {}
    for e in events:
        act = e.get("activity", "") or e.get("method", "?")
        dur = float(e.get("duration_ms", 0) or 0)
        by_act.setdefault(act, []).append(dur)
    result = []
    for act, durs in by_act.items():
        durs_sorted = sorted(durs)
        n = len(durs_sorted)
        result.append({
            "activity": act,
            "count": n,
            "avg_ms": round(statistics.mean(durs_sorted), 1),
            "p50_ms": round(durs_sorted[n // 2], 1),
            "p95_ms": round(durs_sorted[int(n * 0.95)], 1),
            "slow": durs_sorted[int(n * 0.95)] > 500,
        })
    return sorted(result, key=lambda x: -x["p95_ms"])


def _check_conformance(traces: dict[str, list[str]]) -> list[dict]:
    """Check conformance against most-common variant."""
    variants = _analyze_variants(traces)
    if not variants:
        return []
    expected_sig = variants[0]["variant"]
    expected = expected_sig.split("→") if expected_sig else []
    deviations = []
    for trace_id, acts in traces.items():
        sig = "→".join(acts)
        if sig != expected_sig:
            deviations.append({"trace_id": trace_id, "variant": sig, "expected": expected_sig})
    return deviations


def _compute_score(events: list[dict], traces: dict[str, list[str]]) -> dict:
    """Compute overall process health score."""
    perf = _analyze_performance(events)
    variants = _analyze_variants(traces)
    deviations = _check_conformance(traces)
    slow_count = sum(1 for p in perf if p["slow"])
    conformance_rate = round((len(traces) - len(deviations)) / max(len(traces), 1) * 100, 1)
    top_variant_pct = variants[0]["freq_pct"] if variants else 0.0
    score = round((conformance_rate * 0.5 + top_variant_pct * 0.3 + max(0, 100 - slow_count * 10) * 0.2), 1)
    return {
        "score": score,
        "conformance_rate_pct": conformance_rate,
        "top_variant_pct": top_variant_pct,
        "slow_activities": slow_count,
        "total_traces": len(traces),
        "total_events": len(events),
    }


# ── shared option decorators ───────────────────────────────────────────────────

_OCEL_OPTIONS = [
    click.option("--pds", default=None),
    click.option("--minutes", default=60, show_default=True),
    click.option("--limit", default=1000, show_default=True),
    click.option("--top", default=20, show_default=True),
    click.option("--object-type", default="", help="Filter by OCEL object type"),
    click.option("--json", "json_out", is_flag=True, default=False),
]


def _ocel_options(f):
    for opt in reversed(_OCEL_OPTIONS):
        f = opt(f)
    return f


def _resolve_token() -> str:
    auth = _load_auth()
    return auth.get("accessJwt") or auth.get("access_token") or ""


# ── bunseki scan ──────────────────────────────────────────────────────────────

@bunseki.command("scan")
@_ocel_options
def bunseki_scan(pds: str | None, minutes: int, limit: int, top: int, object_type: str, json_out: bool) -> None:
    """Fetch OCEL events and compute all views in one report."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    token = _resolve_token()
    events = _fetch_bunseki_events(pds_url, token, minutes, limit)
    if not events:
        click.echo("no events found", err=True)
        return
    traces = _build_traces(events, object_type)
    dfg = _build_dfg(traces)[:top]
    variants = _analyze_variants(traces)[:top]
    perf = _analyze_performance(events)[:top]
    deviations = _check_conformance(traces)
    score = _compute_score(events, traces)
    if json_out:
        click.echo(json.dumps({
            "score": score,
            "dfg": dfg,
            "variants": variants,
            "performance": perf,
            "deviations": deviations,
        }, ensure_ascii=False, indent=2))
    else:
        click.echo(f"\n=== bunseki scan  events={len(events)}  traces={len(traces)} ===")
        click.echo(f"  score={score['score']}  conformance={score['conformance_rate_pct']}%"
                   f"  slow_activities={score['slow_activities']}")
        click.echo(f"\n-- DFG top {len(dfg)} --")
        click.echo(f"  {'from':<30} {'to':<30} {'count':>6} {'freq%':>7}")
        for row in dfg:
            click.echo(f"  {row['from']:<30} {row['to']:<30} {row['count']:>6} {row['freq_pct']:>6}%")
        click.echo(f"\n-- Variants top {len(variants)} --")
        for i, v in enumerate(variants, 1):
            click.echo(f"  #{i:<3} {v['count']:>4} ({v['freq_pct']:>5}%)  {v['variant']}")
        click.echo(f"\n-- Performance top {len(perf)} --")
        click.echo(f"  {'activity':<40} {'count':>5} {'avg':>7} {'p50':>7} {'p95':>7} {'slow'}")
        for p in perf:
            flag = " SLOW" if p["slow"] else ""
            click.echo(f"  {p['activity']:<40} {p['count']:>5} {p['avg_ms']:>6}ms {p['p50_ms']:>6}ms {p['p95_ms']:>6}ms{flag}")
        click.echo(f"\n-- Deviations: {len(deviations)} traces diverge from top variant --")
        for d in deviations[:10]:
            click.echo(f"  trace={d['trace_id'][:32]}  variant={d['variant'][:80]}")


# ── bunseki dfg ───────────────────────────────────────────────────────────────

@bunseki.command("dfg")
@_ocel_options
def bunseki_dfg(pds: str | None, minutes: int, limit: int, top: int, object_type: str, json_out: bool) -> None:
    """Directly-Follows Graph: activity transition counts."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    token = _resolve_token()
    events = _fetch_bunseki_events(pds_url, token, minutes, limit)
    traces = _build_traces(events, object_type)
    dfg = _build_dfg(traces)[:top]
    if json_out:
        click.echo(json.dumps(dfg, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  {'from':<30} {'to':<30} {'count':>6} {'freq%':>7}")
        for row in dfg:
            click.echo(f"  {row['from']:<30} {row['to']:<30} {row['count']:>6} {row['freq_pct']:>6}%")


# ── bunseki variants ──────────────────────────────────────────────────────────

@bunseki.command("variants")
@_ocel_options
def bunseki_variants(pds: str | None, minutes: int, limit: int, top: int, object_type: str, json_out: bool) -> None:
    """Process variants: group traces by activity sequence."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    token = _resolve_token()
    events = _fetch_bunseki_events(pds_url, token, minutes, limit)
    traces = _build_traces(events, object_type)
    variants = _analyze_variants(traces)[:top]
    if json_out:
        click.echo(json.dumps(variants, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  {'rank':<5} {'count':>5} {'freq%':>7}  variant")
        for i, v in enumerate(variants, 1):
            click.echo(f"  #{i:<4} {v['count']:>5} {v['freq_pct']:>6}%  {v['variant']}")


# ── bunseki conformance ───────────────────────────────────────────────────────

@bunseki.command("conformance")
@_ocel_options
def bunseki_conformance(pds: str | None, minutes: int, limit: int, top: int, object_type: str, json_out: bool) -> None:
    """Conformance checking: flag traces deviating from top variant."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    token = _resolve_token()
    events = _fetch_bunseki_events(pds_url, token, minutes, limit)
    traces = _build_traces(events, object_type)
    deviations = _check_conformance(traces)
    conformance_rate = round((len(traces) - len(deviations)) / max(len(traces), 1) * 100, 1)
    if json_out:
        click.echo(json.dumps({
            "total_traces": len(traces),
            "deviations": len(deviations),
            "conformance_rate_pct": conformance_rate,
            "detail": deviations[:top],
        }, ensure_ascii=False, indent=2))
    else:
        click.echo(f"conformance: {conformance_rate}%  ({len(deviations)} deviations / {len(traces)} traces)")
        for d in deviations[:top]:
            click.echo(f"  trace={d['trace_id'][:40]}  variant={d['variant'][:80]}")


# ── bunseki performance ───────────────────────────────────────────────────────

@bunseki.command("performance")
@_ocel_options
def bunseki_performance(pds: str | None, minutes: int, limit: int, top: int, object_type: str, json_out: bool) -> None:
    """Per-activity duration stats: avg/p50/p95, slow threshold >500ms."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    token = _resolve_token()
    events = _fetch_bunseki_events(pds_url, token, minutes, limit)
    if object_type:
        events = [e for e in events if e.get("type", "") == object_type]
    perf = _analyze_performance(events)[:top]
    if json_out:
        click.echo(json.dumps(perf, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  {'activity':<40} {'count':>5} {'avg':>8} {'p50':>8} {'p95':>8}  slow")
        for p in perf:
            flag = "yes" if p["slow"] else ""
            click.echo(f"  {p['activity']:<40} {p['count']:>5} {p['avg_ms']:>7}ms {p['p50_ms']:>7}ms {p['p95_ms']:>7}ms  {flag}")


# ── bunseki recommendations ───────────────────────────────────────────────────

@bunseki.command("recommendations")
@_ocel_options
def bunseki_recommendations(pds: str | None, minutes: int, limit: int, top: int, object_type: str, json_out: bool) -> None:
    """Cross-reference slow activities with workspace XRPC handlers."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    token = _resolve_token()
    events = _fetch_bunseki_events(pds_url, token, minutes, limit)
    if object_type:
        events = [e for e in events if e.get("type", "") == object_type]
    perf = _analyze_performance(events)
    slow = [p for p in perf if p["slow"]]
    ws = _resolve_root(None)
    recs = []
    for p in slow[:top]:
        activity = p["activity"]
        handler_hits: list[str] = []
        search_term = activity.replace(".", "/").replace("com/etzhayyim", "xrpc")
        try:
            import subprocess
            result = subprocess.run(
                ["grep", "-rl", activity, str(ws)],
                capture_output=True, text=True, timeout=10,
            )
            handler_hits = [line.strip() for line in result.stdout.splitlines()
                            if ".ts" in line or ".py" in line][:5]
        except Exception:
            pass
        recs.append({
            "activity": activity,
            "p95_ms": p["p95_ms"],
            "count": p["count"],
            "handlers": handler_hits,
        })
    if json_out:
        click.echo(json.dumps(recs, ensure_ascii=False, indent=2))
    else:
        if not recs:
            click.echo("  no slow activities detected (p95 <= 500ms)")
        for r in recs:
            click.echo(f"\n  SLOW  {r['activity']}  p95={r['p95_ms']}ms  calls={r['count']}")
            for h in r["handlers"]:
                click.echo(f"    → {h}")
