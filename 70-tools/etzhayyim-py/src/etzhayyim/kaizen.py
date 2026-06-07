"""kaizen — Domain coverage analysis + log quality analysis.

kaizen (default): 9-axis domain coverage scoring on app.ts files.
kaizen logs: OCEL event aggregation from CF Analytics Engine or PDS fallback;
             slow query / error rate analysis; --fix builds an agent prompt.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds
from .shannon import _resolve_root, _walk


# ── regexes (ported from domain_coverage_check.go) ────────────────────────────

_RE_SQL_LABEL = re.compile(r'(?:MATCH\s*\(\w:|Graph\(")(\w+)')
_RE_COLLECTION_KIND = re.compile(r'com\.etzhayyim\.apps\.\w+\.(\w+)')
_RE_TEMPLATE_CMDS = re.compile(
    r'function cmd_(?:list|get|search|create|wave|stats|export|describe|summarize|ingest|audit|health)_\w+|'
    r'function cmd(?:Stats|ExportData|Describe|Summarize|Audit|Ingest|GetInfo|GetStatus)\b'
)
_RE_CUSTOM_CMDS = re.compile(r'function cmd[A-Z]\w+|function cmd_[a-z]\w+')
_RE_IF_BRANCH = re.compile(r'if\s*\(.+\)\s*\{')
_RE_SWITCH_CASE = re.compile(r'\bswitch\b|\bcase\s+["\']')
_RE_TRANSFORM = re.compile(r'\.map\(|\.filter\(|\.reduce\(|\.sort\(|\.forEach\(')
_RE_RSS_URL = re.compile(r'https?://[^\s"]+\.(?:xml|rss|rdf|atom|json)')
_RE_API_URL = re.compile(r'https?://(?:api\.|www\.)[^\s"]+')
_RE_DID_PATH = re.compile(r'comAtprotoIdentityCreate\(\s*"([^"]+)"')
_RE_WRITER_ENTITY = re.compile(r'WriterEntity|writerDID|writer_did')
_RE_DC_INTERFACE = re.compile(r'(?m)^interface\s+\w+')
_RE_CONST_ARRAY = re.compile(r'const\s+\w+(?:\s*:\s*\w+\[\])?\s*=\s*\[')
_RE_NEW_MAP = re.compile(r'new Map')

_GENERIC_LABELS = {"Record", "n", "Entity"}
_GENERIC_KINDS = {"record"}
_DEFAULT_GOV = '{"raci":"responsible","classification":"internal","complianceFrameworks":[]}'


# ── data types ─────────────────────────────────────────────────────────────────

@dataclass
class DomainAppReport:
    project: str
    app: str
    nanoid: str
    domain_score: int
    grade: str
    lines: int
    sql_labels: list[str] = field(default_factory=list)
    collection_kinds: list[str] = field(default_factory=list)
    custom_commands: list[str] = field(default_factory=list)
    template_cmds: int = 0
    business_rules: int = 0
    data_sources: int = 0
    did_paths: list[str] = field(default_factory=list)
    governance_unique: bool = False
    has_writer_entity: bool = False
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project": self.project, "app": self.app, "nanoid": self.nanoid,
            "domain_score": self.domain_score, "grade": self.grade, "lines": self.lines,
            "sql_labels": self.sql_labels, "collection_kinds": self.collection_kinds,
            "custom_commands": self.custom_commands, "template_cmds": self.template_cmds,
            "business_rules": self.business_rules, "data_sources": self.data_sources,
            "did_paths": self.did_paths, "governance_unique": self.governance_unique,
            "has_writer_entity": self.has_writer_entity, "missing": self.missing,
        }


@dataclass
class KaizenGap:
    feature: str
    count: int
    impact: str


@dataclass
class KaizenReport:
    evaluated_at: str
    total_apps: int
    avg_domain_score: float
    grades: dict[str, int]
    gaps: list[KaizenGap]
    apps: list[DomainAppReport] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "evaluated_at": self.evaluated_at,
            "total_apps": self.total_apps,
            "avg_domain_score": self.avg_domain_score,
            "grades": self.grades,
            "gaps": [{"feature": g.feature, "count": g.count, "impact": g.impact} for g in self.gaps],
            "apps": [a.to_dict() for a in self.apps],
        }


# ── scoring ────────────────────────────────────────────────────────────────────

def _score_app(content: str, nanoid: str, project: str, app: str) -> DomainAppReport:
    lines = len(content.strip().splitlines())

    # SQL labels
    label_matches = _RE_SQL_LABEL.findall(content)
    labels = sorted({m for m in label_matches if m not in _GENERIC_LABELS})

    # Collection kinds
    kind_matches = _RE_COLLECTION_KIND.findall(content)
    kinds = sorted({m for m in kind_matches if m not in _GENERIC_KINDS})

    # Commands
    template_cmds = _RE_TEMPLATE_CMDS.findall(content)
    all_cmds = _RE_CUSTOM_CMDS.findall(content)
    template_set = set(template_cmds)
    custom_cmds = [c for c in all_cmds if c not in template_set]

    # Business rules
    business_rules = len(_RE_IF_BRANCH.findall(content))
    if _RE_SWITCH_CASE.search(content):
        business_rules += 5
    business_rules += len(_RE_TRANSFORM.findall(content))

    # Data sources
    data_sources = len(_RE_RSS_URL.findall(content)) + len(_RE_API_URL.findall(content))

    # DID paths
    did_paths = _RE_DID_PATH.findall(content)

    # Writer entity
    has_writer = bool(_RE_WRITER_ENTITY.search(content))

    # Data structures
    custom_interfaces = len(_RE_DC_INTERFACE.findall(content))
    const_arrays = len(_RE_CONST_ARRAY.findall(content))
    const_maps = len(_RE_NEW_MAP.findall(content))

    # Score
    score = 0
    score += min(len(labels) * 10, 30)
    score += min(len(kinds) * 10, 20)
    score += min(len(custom_cmds) * 5, 15)
    score += min(business_rules, 15)
    score += min((custom_interfaces + const_arrays + const_maps) * 3, 10)
    score += min(data_sources * 3, 5)
    # governance uniqueness checked separately
    score += min(len(did_paths) * 3, 5)
    if has_writer:
        score += 3

    # Penalty for template-only
    if not custom_cmds and not labels and not kinds:
        score = max(score - 20, 0)

    score = min(score, 100)

    # Grade
    if score >= 70:
        grade = "S"
    elif score >= 50:
        grade = "A"
    elif score >= 30:
        grade = "B"
    elif score >= 15:
        grade = "C"
    else:
        grade = "D"

    missing: list[str] = []
    if not labels:
        missing.append("graph_labels")
    if not kinds:
        missing.append("collection_kinds")
    if not custom_cmds:
        missing.append("custom_commands")
    if business_rules < 5:
        missing.append("business_rules")

    return DomainAppReport(
        project=project, app=app, nanoid=nanoid,
        domain_score=score, grade=grade, lines=lines,
        sql_labels=labels, collection_kinds=kinds,
        custom_commands=custom_cmds, template_cmds=len(template_cmds),
        business_rules=business_rules, data_sources=data_sources,
        did_paths=did_paths, has_writer_entity=has_writer,
        missing=missing,
    )


def _check_governance(jsonld_path: Path) -> tuple[str, bool]:
    """Returns (nanoid, governance_unique)."""
    try:
        data = json.loads(jsonld_path.read_text(errors="replace"))
    except (OSError, json.JSONDecodeError):
        return "", False
    nanoid = data.get("nanoid", "")
    gov = data.get("governance")
    if gov is None:
        return nanoid, False
    try:
        gov_json = json.dumps(gov, separators=(",", ":"))
    except (TypeError, ValueError):
        return nanoid, True
    return nanoid, gov_json != _DEFAULT_GOV


def collect_and_score_domain_apps(ws: Path) -> list[DomainAppReport]:
    """Walk 60-apps (or projects) and return per-app domain reports."""
    projects_dir = ws / "60-apps"
    if not projects_dir.exists():
        projects_dir = ws / "projects"
    if not projects_dir.exists():
        return []

    apps: list[DomainAppReport] = []
    for app_ts in projects_dir.rglob("src/app.ts"):
        app_dir = app_ts.parent.parent
        dirname = app_dir.name

        # Infer project name
        project = ""
        for seg in app_dir.parts:
            if seg.startswith("etzhayyim-project-"):
                project = seg.removeprefix("etzhayyim-project-")
                break

        try:
            content = app_ts.read_text(errors="replace")
        except OSError:
            continue

        nanoid, gov_unique = _check_governance(app_dir / "kotodama.jsonld")
        report = _score_app(content, nanoid, project, dirname)
        report.governance_unique = gov_unique
        if gov_unique and "governance" in report.missing:
            report.missing.remove("governance")
        if gov_unique:
            report.domain_score = min(report.domain_score + 5, 100)
            # Recompute grade
            s = report.domain_score
            report.grade = "S" if s >= 70 else "A" if s >= 50 else "B" if s >= 30 else "C" if s >= 15 else "D"
        apps.append(report)

    return apps


def build_kaizen_report(apps: list[DomainAppReport]) -> KaizenReport:
    grades: dict[str, int] = {}
    total_score = 0
    gap_counts: dict[str, int] = {}

    for a in apps:
        grades[a.grade] = grades.get(a.grade, 0) + 1
        total_score += a.domain_score
        for m in a.missing:
            gap_counts[m] = gap_counts.get(m, 0) + 1

    avg = total_score / max(len(apps), 1)

    _IMPACT = {
        "graph_labels": "critical — no domain graph model",
        "collection_kinds": "high — no typed records",
        "custom_commands": "high — only template CRUD",
        "governance": "medium — default RACI",
        "business_rules": "medium — no conditional logic",
    }
    gaps = sorted(
        [KaizenGap(k, v, _IMPACT.get(k, "")) for k, v in gap_counts.items()],
        key=lambda g: g.count, reverse=True,
    )

    return KaizenReport(
        evaluated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        total_apps=len(apps),
        avg_domain_score=avg,
        grades=grades,
        gaps=gaps,
        apps=apps,
    )


# ── kaizen agent (codex exec) ─────────────────────────────────────────────────

def _run_kaizen_agent(ws: Path, gaps: list[KaizenGap], apps: list[DomainAppReport]) -> None:
    lines: list[str] = [
        "You are a kaizen agent improving domain coverage for App implementations.\n",
        "CRITICAL RULES:",
        "- Do NOT create git worktrees. Work directly in the current directory.",
        "- Each app needs DOMAIN-SPECIFIC logic, not template copies.",
        "- Read each app's CLAUDE.md, kotodama.jsonld, and existing app.ts to understand its domain.",
        "- Design domain-specific Sql graph labels (not generic 'Record').",
        "- Design domain-specific collection kinds (not generic 'record').",
        "- Design domain-specific commands based on actual business operations.",
        "- Design domain-specific governance (RACI roles, compliance frameworks).",
        "- Add real business rules with conditional logic.\n",
        "EVALUATION CRITERIA (etzhayyim kaizen scoring):",
        "- Graph labels: +10 pts per unique domain label (max 30)",
        "- Collection kinds: +10 pts per unique domain kind (max 20)",
        "- Custom commands: +5 pts per non-template command (max 15)",
        "- Business rules: +1 pt per if/switch/transform (max 15)",
        "- Data structures: +3 pts per interface/array/map (max 10)",
        "- Governance: +5 pts if unique (not default template)",
        "- DID paths: +3 pts per comAtprotoIdentityCreate path (max 5)",
        "- Score >= 70 = S-grade\n",
        "TOP GAPS:",
    ]
    for g in gaps:
        if g.count > 50:
            lines.append(f"  {g.feature}: {g.count} apps ({g.impact})")

    lines.append("\nWORST 20 APPS (fix these first):")
    for a in apps[:20]:
        missing = ",".join(a.missing)
        lines.append(f"  score={a.domain_score} project={a.project} app={a.app} missing=[{missing}]")

    lines += [
        "\nProcess each app:",
        "1. Read projects/etzhayyim-project-{project}/CLAUDE.md for domain context",
        "2. Read the app's kotodama.jsonld for identity/collections",
        "3. Read the app's src/app.ts current implementation",
        "4. Design domain-specific graph labels, collection kinds, commands",
        "5. Update src/app.ts with domain logic",
        "6. Update kotodama.jsonld governance with domain-specific RACI",
        "7. Verify with: etzhayyim-py kaizen --apps --limit 5",
        "\n---",
        "Fix the worst 20 apps listed above. Do NOT create worktrees.",
    ]
    prompt = "\n".join(lines)

    import shutil
    claude = shutil.which("claude")
    codex = shutil.which("codex")

    if not claude and not codex:
        raise click.ClickException(
            "neither claude nor codex found in PATH\n"
            "  install claude: npm i -g @anthropic-ai/claude-code\n"
            "  install codex:  npm i -g @anthropic-ai/codex"
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key.startswith("sk-ant-"):
        click.echo("warning: ANTHROPIC_API_KEY not set or invalid — agent may fail", err=True)

    if claude:
        click.echo("==> launching claude agent via claude -p", err=True)
        result = subprocess.run(["claude", "-p", prompt], cwd=str(ws))
    else:
        click.echo("==> launching codex agent via codex exec sh", err=True)
        result = subprocess.run(["codex", "exec", "-"], input=prompt, text=True, cwd=str(ws))
    sys.exit(result.returncode)


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group("kaizen", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--fix", "auto_fix", is_flag=True, default=False,
              help="Run kaizen agent via codex exec to fix domain coverage gaps.")
@click.option("--grade", "filter_grade", default="",
              help="Show only apps with this grade (S/A/B/C/D)")
@click.option("--limit", default=0, type=int,
              help="Limit to N apps (0=all)")
@click.option("--apps", "show_apps", is_flag=True, default=False,
              help="Show per-app details")
@click.pass_context
def kaizen(ctx: click.Context, workspace_dir: str | None, json_out: bool,
           auto_fix: bool, filter_grade: str, limit: int, show_apps: bool) -> None:
    """Domain coverage analysis (9-axis scoring on app.ts files)."""
    if ctx.invoked_subcommand is not None:
        return

    ws = _resolve_root(workspace_dir)
    all_apps = collect_and_score_domain_apps(ws)
    report = build_kaizen_report(all_apps)

    if auto_fix:
        all_apps.sort(key=lambda a: a.domain_score)
        _run_kaizen_agent(ws, report.gaps, all_apps)
        return  # _run_kaizen_agent calls sys.exit

    # Filter + sort
    display = list(all_apps)
    if filter_grade:
        display = [a for a in display if a.grade == filter_grade]
    display.sort(key=lambda a: a.domain_score)
    if limit > 0:
        display = display[:limit]

    if json_out:
        out = report.to_dict()
        if not show_apps:
            out.pop("apps", None)
        else:
            out["apps"] = [a.to_dict() for a in display]
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
        return

    click.echo(f"kaizen (改善): domain coverage analysis")
    click.echo(f"  apps={report.total_apps}  avg={report.avg_domain_score:.1f}  "
               f"S={report.grades.get('S',0)} A={report.grades.get('A',0)} "
               f"B={report.grades.get('B',0)} C={report.grades.get('C',0)} "
               f"D={report.grades.get('D',0)}")
    click.echo()
    if report.gaps:
        click.echo("  gaps:")
        for g in report.gaps[:5]:
            click.echo(f"    [{g.count:3d} apps] {g.feature}: {g.impact}")
    if show_apps and display:
        click.echo()
        click.echo(f"  {'score':>5} {'grade':>5} {'project':<20} {'app'}")
        for a in display:
            missing = ",".join(a.missing[:3])
            click.echo(f"  {a.domain_score:>5} {a.grade:>5} {a.project:<20} {a.app[:40]:<40} {missing}")


# ── OCEL event types ──────────────────────────────────────────────────────────

_CF_ACCOUNT_ID = "4da88288dc30d9ee257f319d3c33ecf0"


def _resolve_cf_token() -> str:
    for var in ("CF_API_TOKEN", "CLOUDFLARE_API_TOKEN", "etzhayyim_CLOUDFLARE_API_TOKEN"):
        v = os.environ.get(var, "")
        if v:
            return v
    return ""


def _resolve_etzhayyim_token() -> str:
    tok = os.environ.get("etzhayyim_TOKEN", "")
    if tok:
        return tok
    auth = _load_auth()
    return auth.get("accessJwt") or auth.get("id_token") or auth.get("access_token") or ""


def _percentile(samples: list[int | float], pct: float) -> float:
    if not samples:
        return 0.0
    s = sorted(samples)
    idx = max(0, min(len(s) - 1, math.ceil(len(s) * pct) - 1))
    return float(s[idx])


def _fetch_ocel_from_cf_ae(api_token: str, limit: int) -> dict:
    """Query CF Analytics Engine SQL API for OCEL events + aggregates."""
    sql_events = (
        f"SELECT timestamp,blob1 AS method,blob2 AS type,blob3 AS auth,"
        f"double1 AS ms,double2 AS status "
        f"FROM ocel_v2 WHERE blob2='xrpc' "
        f"ORDER BY timestamp DESC LIMIT {limit}"
    )
    sql_agg = (
        f"SELECT blob1 AS method, count() AS count, "
        f"sum(double2>=400) AS errors, avg(double1) AS avgMs, max(double1) AS maxMs, "
        f"quantileWeighted(0.50)(double1,1) AS p50Ms, "
        f"quantileWeighted(0.99)(double1,1) AS p99Ms "
        f"FROM (SELECT timestamp,blob1,double1,double2 FROM ocel_v2 "
        f"WHERE blob2='xrpc' ORDER BY timestamp DESC LIMIT {limit}) "
        f"GROUP BY blob1 ORDER BY count DESC LIMIT 50"
    )
    url = f"https://api.cloudflare.com/client/v4/accounts/{_CF_ACCOUNT_ID}/analytics_engine/sql"
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "text/plain"}

    events: list[dict] = []
    aggs: dict[str, dict] = {}

    resp = httpx.post(url, content=sql_events.encode(), headers=headers, timeout=30)
    resp.raise_for_status()
    for row in resp.json().get("data", []):
        events.append({
            "ts": str(row.get("timestamp", "")),
            "method": str(row.get("method", "")),
            "ms": int(float(row.get("ms") or 0)),
            "status": int(float(row.get("status") or 0)),
            "auth": str(row.get("auth", "")),
        })

    resp2 = httpx.post(url, content=sql_agg.encode(), headers=headers, timeout=30)
    resp2.raise_for_status()
    for row in resp2.json().get("data", []):
        m = str(row.get("method", ""))
        if m:
            aggs[m] = {
                "count": int(float(row.get("count") or 0)),
                "errors": int(float(row.get("errors") or 0)),
                "avgMs": float(row.get("avgMs") or 0),
                "maxMs": float(row.get("maxMs") or 0),
                "p50Ms": float(row.get("p50Ms") or 0),
                "p99Ms": float(row.get("p99Ms") or 0),
            }

    return {"events": events, "aggregates": aggs}


def _fetch_ocel_from_pds(token: str, pds_url: str, limit: int) -> dict:
    """Fetch OCEL from PDS internal endpoint."""
    base = pds_url.rstrip("/")
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "etzhayyim-py/1.0"}
    for endpoint in [f"{base}/_pds/ocel?limit={limit}",
                     f"{base}/xrpc/com.etzhayyim.pds.getOcel?limit={limit}"]:
        try:
            resp = httpx.get(endpoint, headers=headers, timeout=30)
            if resp.status_code == 404:
                continue
            if resp.status_code == 200:
                return resp.json()
        except httpx.HTTPError:
            continue
    raise click.ClickException(
        "PDS OCEL endpoint unavailable. Set CF_API_TOKEN for Analytics Engine, "
        "or ensure PDS is reachable."
    )


def _load_ocel(pds_url: str, limit: int) -> tuple[dict, str]:
    """Load OCEL: try CF AE first, fall back to PDS."""
    cf_token = _resolve_cf_token()
    if cf_token:
        try:
            data = _fetch_ocel_from_cf_ae(cf_token, limit)
            return data, "analytics_engine"
        except Exception as e:
            click.echo(f"WARN: CF Analytics Engine failed ({e}), falling back to PDS", err=True)

    token = _resolve_etzhayyim_token()
    if not token:
        raise click.ClickException(
            "not signed in — run: etzhayyim authn signin\n"
            "  or set CF_API_TOKEN for CF Analytics Engine"
        )
    data = _fetch_ocel_from_pds(token, pds_url, limit)
    return data, "pds_fallback"


def _aggregate_events(events: list[dict]) -> dict[str, dict]:
    """Build per-method stats from raw events."""
    stats: dict[str, dict] = {}
    for e in events:
        m = e.get("method", "")
        if not m:
            continue
        s = stats.setdefault(m, {"count": 0, "errors": 0, "ms_samples": []})
        s["count"] += 1
        if int(e.get("status", 0)) >= 400:
            s["errors"] += 1
        ms = e.get("ms", 0)
        if ms:
            s["ms_samples"].append(int(ms))
    return stats


def _build_findings(events: list[dict], aggs: dict[str, dict],
                    top: int, p99_threshold: float, err_rate_threshold: float,
                    show_events: int) -> dict:
    """Build slow/error findings from events + pre-computed aggregates."""
    event_stats = _aggregate_events(events)
    all_methods = set(event_stats) | set(aggs)
    findings = []

    for method in all_methods:
        es = event_stats.get(method, {})
        ag = aggs.get(method, {})
        count = ag.get("count") or es.get("count", 0)
        if count == 0:
            continue
        errors = ag.get("errors") or es.get("errors", 0)
        err_rate = errors / count * 100 if count else 0

        samples = es.get("ms_samples", [])
        p50 = ag.get("p50Ms") or (_percentile(samples, 0.50) if samples else 0)
        p99 = ag.get("p99Ms") or (_percentile(samples, 0.99) if samples else 0)
        avg_ms = ag.get("avgMs") or (sum(samples) / len(samples) if samples else 0)
        max_ms = ag.get("maxMs") or (max(samples) if samples else 0)

        # severity
        if err_rate >= 10 or p99 >= 2000:
            severity = "critical"
        elif err_rate >= 5 or p99 >= 1000:
            severity = "high"
        elif err_rate >= 1 or p99 >= 500:
            severity = "medium"
        else:
            severity = "low"

        findings.append({
            "method": method, "count": count, "errors": errors,
            "errRate": round(err_rate, 2),
            "avgMs": round(avg_ms, 2), "p50Ms": round(p50, 2),
            "p99Ms": round(p99, 2), "maxMs": round(max_ms, 2),
            "severity": severity,
        })

    slow = sorted(
        [f for f in findings if f["p99Ms"] >= p99_threshold],
        key=lambda f: (-f["p99Ms"], -f["errRate"]),
    )[:top]

    errors_list = sorted(
        [f for f in findings if f["errRate"] >= err_rate_threshold or f["errors"] > 0],
        key=lambda f: (-f["errRate"], -f["errors"]),
    )[:top]

    recent_errs = [e for e in events if int(e.get("status", 0)) >= 400][:show_events]

    total_req = sum(f["count"] for f in findings)
    total_err = sum(f["errors"] for f in findings)
    overall_err_rate = total_err / total_req * 100 if total_req else 0

    return {
        "total_requests": total_req,
        "total_errors": total_err,
        "overall_error_rate": round(overall_err_rate, 2),
        "slow_queries": slow,
        "error_queries": errors_list,
        "recent_error_events": recent_errs,
    }


def _build_kaizen_logs_prompt(summary: dict, source: str) -> str:
    lines = [
        "ログ由来の性能/障害 kaizen を実施してください。",
        "目的: 遅い query と高エラー率メソッドの原因をコードから特定し、改善案と必要なら修正を行う。\n",
        "観測サマリ:",
        f"  source: {source}",
        f"  total_requests: {summary['total_requests']}",
        f"  total_errors: {summary['total_errors']} ({summary['overall_error_rate']:.2f}%)\n",
        "遅い query (p99上位):",
    ]
    for q in summary["slow_queries"]:
        lines.append(
            f"  {q['method']}: p99={q['p99Ms']:.0f}ms p50={q['p50Ms']:.0f}ms "
            f"avg={q['avgMs']:.0f}ms errRate={q['errRate']:.2f}% count={q['count']}"
        )
    lines.append("\nエラー query (errRate上位):")
    for q in summary["error_queries"]:
        lines.append(
            f"  {q['method']}: errRate={q['errRate']:.2f}% "
            f"errors={q['errors']}/{q['count']} p99={q['p99Ms']:.0f}ms"
        )
    if summary["recent_error_events"]:
        lines.append("\n最近のエラーイベント:")
        for e in summary["recent_error_events"][:10]:
            ts = str(e.get("ts", ""))[:19]
            lines.append(
                f"  ts={ts} status={e.get('status')} ms={e.get('ms')} "
                f"method={e.get('method')} err={e.get('err', '')}"
            )
    lines += [
        "\nやってほしいこと:",
        "1. 上記メソッド実装を特定し、遅延/失敗の主要因を列挙。",
        "2. すぐ効く改善を優先して実装 (N+1削減、不要I/O削減、キャッシュ、validation、error handling)。",
        "3. 変更点、想定改善効果、追加テストをまとめる。",
        "4. 実行可能な検証コマンドを提示する。",
    ]
    return "\n".join(lines)


def _run_kaizen_logs_fix_murakumo(summary: dict, pds_url: str) -> None:
    """Call murakumo scoreDataQuality + optimizeCycle."""
    token = _resolve_etzhayyim_token()
    if not token:
        raise click.ClickException("not signed in — run: etzhayyim authn signin")
    base = pds_url.rstrip("/")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    max_p99 = max((q["p99Ms"] for q in summary["slow_queries"]), default=0)
    ingest_count = 20 if max_p99 >= 10000 else 10
    train_count = 8 if max_p99 >= 10000 else 4
    eval_limit = 40 if summary["total_errors"] >= 20 else 20

    click.echo("==> murakumo scoreDataQuality", err=True)
    try:
        resp = httpx.post(
            f"{base}/xrpc/com.etzhayyim.murakumo.scoreDataQuality",
            json={"minRows": 50, "sampleRows": 64, "maxLabels": 0},
            headers=headers, timeout=60,
        )
        click.echo(resp.text)
    except httpx.HTTPError as e:
        click.echo(f"WARN: scoreDataQuality failed: {e}", err=True)

    opt_payload = {
        "ingestStart": 0, "ingestCount": ingest_count,
        "trainStart": 0, "trainCount": train_count,
        "samplesPer": 200, "evalLimit": eval_limit,
    }
    click.echo("==> murakumo optimizeCycle", err=True)
    try:
        resp2 = httpx.post(
            f"{base}/xrpc/com.etzhayyim.murakumo.optimizeCycle",
            json=opt_payload, headers=headers, timeout=60,
        )
        click.echo(resp2.text)
    except httpx.HTTPError as e:
        raise click.ClickException(f"murakumo optimizeCycle failed: {e}")


@kaizen.command("logs")
@click.option("--pds", default=None, help="PDS base URL")
@click.option("--limit", default=300, type=int, show_default=True)
@click.option("--top", default=8, type=int, show_default=True)
@click.option("--show-events", default=20, type=int, show_default=True)
@click.option("--p99-threshold", default=500.0, type=float, show_default=True,
              help="Slow query threshold (ms, p99)")
@click.option("--error-rate-threshold", default=1.0, type=float, show_default=True,
              help="Error query threshold (%)")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--fix", "auto_fix", is_flag=True, default=False,
              help="Run agent fix after analysis")
@click.option("--fix-engine", default="code-exec", show_default=True,
              type=click.Choice(["code-exec", "murakumo"]))
def kaizen_logs(pds: str | None, limit: int, top: int, show_events: int,
                p99_threshold: float, error_rate_threshold: float,
                json_out: bool, auto_fix: bool, fix_engine: str) -> None:
    """OCEL log analysis: slow queries, error rates, reverse topology."""
    from datetime import datetime, timezone

    pds_url = (pds or resolve_pds()).rstrip("/")
    data, source = _load_ocel(pds_url, limit)

    events: list[dict] = data.get("events", [])
    aggs: dict[str, dict] = data.get("aggregates", {})

    findings = _build_findings(events, aggs, top, p99_threshold,
                               error_rate_threshold, show_events)

    report = {
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "data_source": source,
        "window_limit": limit,
        "event_count": len(events),
        **findings,
    }

    if json_out:
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        click.echo("etzhayyim kaizen logs — Query速度/エラー分析")
        click.echo(f"  source:   {source}")
        click.echo(f"  events:   {len(events)}")
        click.echo(f"  errors:   {findings['total_errors']} "
                   f"({findings['overall_error_rate']:.2f}%)")
        click.echo()
        click.echo("  Slow Queries (p99 ≥ {:.0f}ms):".format(p99_threshold))
        click.echo(f"    {'p99(ms)':>8}  {'err%':>6}  {'count':>6}  method")
        if not findings["slow_queries"]:
            click.echo("    (none above threshold)")
        for q in findings["slow_queries"]:
            click.echo(f"    {q['p99Ms']:>8.0f}  {q['errRate']:>6.2f}  "
                       f"{q['count']:>6}  {q['method']}")
        click.echo()
        click.echo("  Error Queries:")
        click.echo(f"    {'err%':>6}  {'errs':>6}  {'count':>6}  method")
        if not findings["error_queries"]:
            click.echo("    (none)")
        for q in findings["error_queries"]:
            click.echo(f"    {q['errRate']:>6.2f}  {q['errors']:>6}  "
                       f"{q['count']:>6}  {q['method']}")
        if findings["recent_error_events"]:
            click.echo()
            click.echo("  Recent Error Events:")
            click.echo(f"    {'ts':19}  {'status':>6}  {'ms':>4}  method")
            for e in findings["recent_error_events"]:
                ts = str(e.get("ts", ""))[:19]
                click.echo(f"    {ts:19}  {e.get('status', 0):>6}  "
                           f"{e.get('ms', 0):>4}  {e.get('method', '')}")

    if not auto_fix:
        return

    prompt = _build_kaizen_logs_prompt(findings, source)
    if fix_engine == "murakumo":
        _run_kaizen_logs_fix_murakumo(findings, pds_url)
        return

    # code-exec: pipe prompt to codex or claude
    ws = _resolve_root(None)
    claude_bin = shutil.which("claude")
    codex_bin = shutil.which("codex")
    if not claude_bin and not codex_bin:
        raise click.ClickException(
            "neither claude nor codex found in PATH. "
            "Install: npm i -g @anthropic-ai/claude-code"
        )
    if claude_bin:
        click.echo("==> launching claude -p", err=True)
        result = subprocess.run(["claude", "-p", prompt], cwd=str(ws))
    else:
        click.echo("==> launching codex exec -", err=True)
        result = subprocess.run(["codex", "exec", "-"], input=prompt, text=True, cwd=str(ws))
    sys.exit(result.returncode)
