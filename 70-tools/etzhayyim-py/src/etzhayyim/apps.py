"""apps — App status checker (health, metadata, coverage, kyumei-koji).

Checks deployed app health via /_app/meta and /health endpoints.
Coverage evaluates domain knowledge via static analysis + PDS live data + XRPC self-eval.
Kyumei-koji evaluates DID self-information gathering readiness.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import click
import httpx

from .authn import _load_auth
from .haisen import _read_jsonld
from .projector import resolve_pds
from .shannon import _resolve_root


@dataclass
class AppStatus:
    nanoid: str
    name: str
    health_ok: bool
    health_code: int
    latency_ms: int
    meta_ok: bool
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "nanoid": self.nanoid, "name": self.name,
            "health_ok": self.health_ok, "health_code": self.health_code,
            "latency_ms": self.latency_ms, "meta_ok": self.meta_ok, "error": self.error,
        }


def _check_app_health(nanoid: str, name: str, base_url: str) -> AppStatus:
    try:
        start = time.monotonic()
        resp = httpx.get(f"{base_url}/health", timeout=10)
        latency = int((time.monotonic() - start) * 1000)
        health_ok = resp.status_code < 400
    except httpx.HTTPError as e:
        return AppStatus(nanoid=nanoid, name=name, health_ok=False, health_code=0,
                         latency_ms=0, meta_ok=False, error=str(e))

    meta_ok = False
    try:
        meta_resp = httpx.get(f"{base_url}/_app/meta", timeout=10)
        meta_ok = meta_resp.status_code < 400
    except httpx.HTTPError:
        pass

    return AppStatus(nanoid=nanoid, name=name, health_ok=health_ok,
                     health_code=resp.status_code, latency_ms=latency, meta_ok=meta_ok)


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    h = {"Content-Type": "application/json"}
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


@click.group("apps", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def apps(ctx: click.Context, workspace_dir: str | None, pds: str | None, json_out: bool) -> None:
    """App status — list and health-check deployed apps."""
    if ctx.invoked_subcommand is not None:
        return
    pds_url = (pds or resolve_pds()).rstrip("/")
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.apps.listApps",
            headers={"Authorization": f"Bearer {tok}"} if tok else {},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            app_list = data if isinstance(data, list) else data.get("apps", [])
            click.echo(f"apps: {len(app_list)}")
            for a in app_list:
                click.echo(f"  {a.get('nanoid', '')}  {a.get('name', '')}  "
                           f"{a.get('status', '')}  {a.get('url', '')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@apps.command("list")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def apps_list(workspace_dir: str | None, json_out: bool) -> None:
    """List apps from local workspace kotodama.jsonld files."""
    ws = _resolve_root(workspace_dir)
    apps_dir = ws / "60-apps"
    app_list = []
    if apps_dir.exists():
        for jsonld in apps_dir.rglob("kotodama.jsonld"):
            data = _read_jsonld(jsonld)
            if data.get("nanoid"):
                app_list.append({
                    "nanoid": data.get("nanoid", ""),
                    "name": data.get("name", ""),
                    "performerType": data.get("performerType", ""),
                })
    if json_out:
        click.echo(json.dumps(app_list, ensure_ascii=False, indent=2))
    else:
        click.echo(f"apps: {len(app_list)}")
        for a in app_list:
            click.echo(f"  {a['nanoid']}  {a['name']}  [{a['performerType']}]")


@apps.command("health")
@click.option("--url", required=True, help="App base URL to check")
@click.option("--nanoid", default="", help="Nanoid label")
@click.option("--json", "json_out", is_flag=True, default=False)
def apps_health(url: str, nanoid: str, json_out: bool) -> None:
    """Health-check a specific app URL."""
    status = _check_app_health(nanoid, "", url)
    if json_out:
        click.echo(json.dumps(status.to_dict(), ensure_ascii=False, indent=2))
    else:
        ok = "OK  " if status.health_ok else "FAIL"
        click.echo(f"  [{ok}] {url}  {status.health_code}  {status.latency_ms}ms")


# ── coverage helpers ───────────────────────────────────────────────────────────

_RE_COLLECTION = re.compile(r"""["']((?:com\.etzhayyim\.apps|app\.bsky)\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_.\-]+)["']""")
_RE_SQL_LABEL = re.compile(r"""vertex_([a-z0-9_]+)""")
_RE_CUSTOM_CMD = re.compile(r"""sdk\.app\.command\s*\(""")
_RE_BUSINESS_RULE = re.compile(r"""(?:if|when|require|assert|validate)\s*\(""")
_RE_SUBDID_PATH = re.compile(r"""path\s*:\s*["']([^"']+)["']""")
_RE_SOURCE_URL = re.compile(r"""(?:sourceUrl|caseDbUrl|legislationUrl)\s*:\s*["'](https?://[^"']+)["']""")


def _discover_app_jsonld(ws: Path, nanoid: str) -> dict | None:
    for p in ws.rglob("kotodama.jsonld"):
        try:
            data = _read_jsonld(p)
        except Exception:
            continue
        if data.get("nanoid") == nanoid:
            return {"nanoid": nanoid, "name": data.get("name", nanoid),
                    "did": data.get("did", f"did:web:{nanoid}.etzhayyim.com"),
                    "dir": str(p.parent)}
    return None


def _list_pds_records(pds_url: str, token: str, repo_did: str, collection: str,
                      limit: int = 100, timeout: int = 15) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.atproto.repo.listRecords",
            params={"repo": repo_did, "collection": collection, "limit": limit},
            headers=headers, timeout=timeout,
        )
        if resp.status_code >= 400:
            return []
        data = resp.json()
        return data.get("records", []) if isinstance(data, dict) else []
    except httpx.HTTPError:
        return []


def _xrpc_coverage_stats(nanoid: str, app_name: str, token: str, timeout: int = 15) -> dict | None:
    if not app_name:
        app_name = nanoid
    url = f"https://{nanoid}.etzhayyim.com/xrpc/com.etzhayyim.apps.{app_name}.coverageStats"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = httpx.post(url, json={}, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
    except httpx.HTTPError:
        pass
    return None


def _infer_app_name_from_collections(cols: list[str]) -> str:
    for col in cols:
        parts = col.split(".")
        if len(parts) >= 5 and parts[:3] == ["com", "etzhayyim", "apps"]:
            return parts[3]
    return ""


def _score_domain_static(app_dir: str, nanoid: str) -> tuple[int, list[str], list[str], list[str], int, list[str]]:
    """Return (score, sql_labels, collections, custom_commands, business_rules, sub_did_paths)."""
    app_ts = None
    for candidate in ["src/app.ts", "app.ts", "src/index.ts"]:
        p = Path(app_dir) / candidate
        if p.exists():
            app_ts = p
            break

    if not app_ts:
        return 0, [], [], [], 0, []

    src = app_ts.read_text(errors="replace")
    sql_labels = list({m.group(1) for m in _RE_SQL_LABEL.finditer(src)})
    collections = list({m.group(1) for m in _RE_COLLECTION.finditer(src)})
    custom_cmds = _RE_CUSTOM_CMD.findall(src)
    biz_rules = len(_RE_BUSINESS_RULE.findall(src))
    sub_did_paths = list({m.group(1) for m in _RE_SUBDID_PATH.finditer(src)})
    lines = src.count("\n")

    score = 0
    score += min(len(sql_labels) * 10, 30)
    score += min(len(collections) * 10, 20)
    score += min(len(custom_cmds) * 5, 15)
    score += min(biz_rules, 15)
    score += min(lines // 100, 10)
    score += min(len(sub_did_paths) * 3, 5)
    score = min(score, 100)
    return score, sql_labels, collections, custom_cmds, biz_rules, sub_did_paths


def _coverage_grade(score: float) -> str:
    if score >= 80:
        return "S"
    if score >= 60:
        return "A"
    if score >= 40:
        return "B"
    if score >= 20:
        return "C"
    return "D"


def _tier_score(n: int, lo: int, mid: int, hi: int) -> float:
    if n <= 0:
        return 0
    if n >= hi:
        return 100
    if n >= mid:
        return 60 + 40 * (n - mid) / max(hi - mid, 1)
    return 20 + 40 * (n - lo) / max(mid - lo, 1)


@apps.command("coverage")
@click.argument("nanoid")
@click.option("--pds", default=None)
@click.option("--timeout", default=15, show_default=True, type=int)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def apps_coverage(nanoid: str, pds: str | None, timeout: int,
                  workspace_dir: str | None, json_out: bool) -> None:
    """Evaluate domain knowledge coverage for an app (static + PDS live + XRPC self-eval)."""
    ws = _resolve_root(workspace_dir)
    pds_url = (pds or resolve_pds()).rstrip("/")
    auth = _load_auth()
    token = auth.get("accessJwt") or auth.get("access_token") or ""

    app = _discover_app_jsonld(ws, nanoid)
    if not app:
        app = {"nanoid": nanoid, "name": nanoid,
               "did": f"did:web:{nanoid}.etzhayyim.com", "dir": ""}

    did = app["did"] or f"did:web:{nanoid}.etzhayyim.com"
    click.echo(f"==> Evaluating domain coverage for {app['name']} ({nanoid})...\n", err=True)

    domain_score, sql_labels, collections, custom_cmds, biz_rules, sub_paths = \
        _score_domain_static(app["dir"], nanoid)
    domain_grade = _coverage_grade(domain_score)

    # PDS live record count
    live_records = 0
    live_by_did: dict[str, int] = {}
    repo_dids = [did, f"did:web:{nanoid}.etzhayyim.com"]
    repo_dids = list(dict.fromkeys(repo_dids))
    for repo_did in repo_dids:
        for col in (collections or [f"com.etzhayyim.apps.{nanoid}.status"]):
            recs = _list_pds_records(pds_url, token, repo_did, col, 250, timeout)
            for r in recs:
                live_records += 1
                actor = r.get("value", {}).get("actorDid", repo_did)
                live_by_did[actor] = live_by_did.get(actor, 0) + 1

    # XRPC self-eval
    app_name = _infer_app_name_from_collections(collections) or nanoid
    xrpc_coverage = _xrpc_coverage_stats(nanoid, app_name, token, timeout)
    xrpc_pct = 0.0
    if xrpc_coverage:
        if "totalJurisdictions" in xrpc_coverage:
            xrpc_pct = 100 if float(xrpc_coverage["totalJurisdictions"]) > 0 else 0
        else:
            xrpc_pct = 50

    live_pct = _tier_score(live_records, 1, 10, 100)
    did_pct = _tier_score(len(live_by_did), 1, 3, 10)
    overall = 0.40 * domain_score + 0.25 * live_pct + 0.20 * xrpc_pct + 0.15 * did_pct
    overall_grade = _coverage_grade(overall)

    report = {
        "nanoid": nanoid, "name": app["name"], "did": did,
        "domain_score": domain_score, "domain_grade": domain_grade,
        "live_records": live_records, "live_dids": len(live_by_did),
        "live_by_did": [{"actor_did": k, "records": v} for k, v in live_by_did.items()],
        "xrpc_coverage": xrpc_coverage,
        "knowledge_axes": [
            {"name": "graph_labels", "score": min(len(sql_labels) * 10, 30), "max": 30,
             "detail": ", ".join(sql_labels)},
            {"name": "collection_kinds", "score": min(len(collections) * 10, 20), "max": 20,
             "detail": ", ".join(collections[:5])},
            {"name": "custom_commands", "score": min(len(custom_cmds) * 5, 15), "max": 15,
             "detail": f"{len(custom_cmds)} commands"},
            {"name": "business_rules", "score": min(biz_rules, 15), "max": 15,
             "detail": f"{biz_rules} rules"},
            {"name": "sub_did_paths", "score": min(len(sub_paths) * 3, 5), "max": 5,
             "detail": ", ".join(sub_paths[:5])},
        ],
        "overall_score": round(overall, 1),
        "overall_grade": overall_grade,
    }

    if json_out:
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
        return

    click.echo(f"App Coverage Report: {app['name']} ({nanoid})")
    click.echo(f"DID: {did}\n")
    click.echo(f"Overall:       {overall_grade}  {overall:.1f} / 100")
    click.echo(f"Domain Score:  {domain_grade}  {domain_score} / 100")
    click.echo(f"Live Records:  {live_records}")
    click.echo(f"Live DIDs:     {len(live_by_did)}")
    if live_by_did:
        click.echo("\nLive by DID:")
        for actor, cnt in sorted(live_by_did.items(), key=lambda x: -x[1]):
            click.echo(f"  {actor[:60]}  {cnt}")
    click.echo("\nKnowledge Axes:")
    click.echo(f"  {'Axis':<22}  {'Score':>5}  {'Max':>3}  Detail")
    for ax in report["knowledge_axes"]:
        click.echo(f"  {ax['name']:<22}  {ax['score']:>5}  {ax['max']:>3}  {ax['detail'][:50]}")
    if xrpc_coverage:
        click.echo("\nApp Self-Evaluation (XRPC coverageStats):")
        for k, v in xrpc_coverage.items():
            click.echo(f"  {k}: {v}")


# ── kyumei-koji helpers ────────────────────────────────────────────────────────

def _extract_sources_from_src(src: str) -> list[dict]:
    sources = []
    for m in _RE_SOURCE_URL.finditer(src):
        sources.append({"url": m.group(1), "format": "http", "category": "external"})
    return sources[:20]


def _kyumei_grade(score: float) -> str:
    return _coverage_grade(score)


@apps.command("kyumei-koji")
@click.argument("nanoid")
@click.option("--pds", default=None)
@click.option("--domain", default="", help="App domain (e.g. isco or isco.etzhayyim.com)")
@click.option("--fast", is_flag=True, default=False, help="Skip expensive per-subDID live checks")
@click.option("--timeout", default=15, show_default=True, type=int)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def apps_kyumei_koji(nanoid: str, pds: str | None, domain: str, fast: bool,
                     timeout: int, workspace_dir: str | None, json_out: bool) -> None:
    """Evaluate DID self-information gathering readiness (kyumei-koji) for an app."""
    ws = _resolve_root(workspace_dir)
    pds_url = (pds or resolve_pds()).rstrip("/")
    auth = _load_auth()
    token = auth.get("accessJwt") or auth.get("access_token") or ""

    app = _discover_app_jsonld(ws, nanoid)
    if not app:
        app = {"nanoid": nanoid, "name": nanoid,
               "did": f"did:web:{nanoid}.etzhayyim.com", "dir": ""}

    did = app["did"] or f"did:web:{nanoid}.etzhayyim.com"
    click.echo(f"==> Kyumei-Koji analysis for {app['name']} ({nanoid})...\n", err=True)

    # Static: extract declared sources + collections + sub-DID paths from app.ts
    declared_sources: list[dict] = []
    collections: list[str] = []
    sub_did_paths: list[str] = []
    if app["dir"]:
        for cand in ["src/app.ts", "app.ts", "src/index.ts"]:
            p = Path(app["dir"]) / cand
            if p.exists():
                src = p.read_text(errors="replace")
                declared_sources = _extract_sources_from_src(src)
                collections = list({m.group(1) for m in _RE_COLLECTION.finditer(src)})
                sub_did_paths = list({m.group(1) for m in _RE_SUBDID_PATH.finditer(src)})
                break

    # Live record counts from PDS
    repo_dids = list(dict.fromkeys([did, f"did:web:{nanoid}.etzhayyim.com"]))
    live_record_counts: dict[str, int] = {}
    default_cols = [f"com.etzhayyim.apps.{nanoid}.status"] if not collections else []
    for col in (collections or default_cols):
        total = 0
        for repo_did in repo_dids:
            recs = _list_pds_records(pds_url, token, repo_did, col, 400, timeout)
            total += len(recs)
        live_record_counts[col] = total

    total_records = sum(live_record_counts.values())

    # Sub-DID live metrics
    sub_dids_info: list[dict] = []
    if not fast:
        for path in sub_did_paths[:12]:
            sub_did = f"did:web:{nanoid}.etzhayyim.com:{path.replace('/', ':')}"
            cnt = 0
            for col in (collections[:3] or [f"com.etzhayyim.apps.{nanoid}.status"]):
                cnt += len(_list_pds_records(pds_url, token, sub_did, col, 100, timeout))
            sub_dids_info.append({"path": path, "records": cnt})
            if cnt > 0:
                total_records = max(total_records, cnt)

    # Knowledge gaps
    gaps: list[dict] = []
    if total_records == 0:
        gaps.append({"area": "live_data", "severity": "high",
                     "detail": "No live records found in PDS",
                     "suggestion": "Verify app DID and collection NSIDs"})
    if not declared_sources:
        gaps.append({"area": "data_sources", "severity": "medium",
                     "detail": "No declared data sources found in app.ts",
                     "suggestion": "Declare sourceUrl in app data definitions"})
    if not sub_did_paths:
        gaps.append({"area": "sub_dids", "severity": "low",
                     "detail": "No sub-DID path declarations found",
                     "suggestion": "Add path: declarations to enable multi-actor coverage"})

    # Recommendations
    recs: list[str] = []
    if total_records == 0:
        recs.append("Run data ingestion to populate live records")
    if not collections:
        recs.append("Declare XRPC collection NSIDs in app.ts")
    if len(sub_did_paths) == 0:
        recs.append("Add sub-DID path declarations for multi-actor support")

    # Readiness score
    source_score = min(len(declared_sources) * 10, 25)
    live_score = _tier_score(total_records, 1, 10, 100) * 0.40
    sub_did_score = min(len(sub_did_paths) * 5, 15)
    col_score = min(len(collections) * 5, 20)
    readiness = source_score + live_score + sub_did_score + col_score
    readiness = min(readiness, 100)
    readiness_grade = _kyumei_grade(readiness)

    report = {
        "nanoid": nanoid, "name": app["name"], "did": did,
        "declared_sources": declared_sources,
        "live_record_counts": live_record_counts,
        "sub_dids": sub_dids_info,
        "knowledge_gaps": gaps,
        "recommendations": recs,
        "readiness_score": round(readiness, 1),
        "readiness_grade": readiness_grade,
    }

    if json_out:
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
        return

    click.echo(f"Kyumei-Koji Report: {app['name']} ({nanoid})")
    click.echo(f"DID: {did}\n")
    click.echo(f"Readiness:         {readiness_grade}  {readiness:.1f} / 100")
    click.echo(f"Declared Sources:  {len(declared_sources)}")
    click.echo(f"Collections:       {len(collections)}")
    click.echo(f"Sub-DID Paths:     {len(sub_did_paths)}")
    click.echo(f"Total Live Records:{total_records}")
    if live_record_counts:
        click.echo("\nLive Record Counts:")
        for col, cnt in sorted(live_record_counts.items()):
            click.echo(f"  {col[:60]:<60}  {cnt:>6}")
    if sub_dids_info:
        click.echo("\nSub-DIDs:")
        for sd in sub_dids_info:
            click.echo(f"  {sd['path']:<40}  {sd['records']:>6}")
    if gaps:
        click.echo("\nKnowledge Gaps:")
        for g in gaps:
            click.echo(f"  [{g['severity'].upper():>6}] {g['area']}: {g['detail']}")
            click.echo(f"           → {g['suggestion']}")
    if recs:
        click.echo("\nRecommendations:")
        for r in recs:
            click.echo(f"  - {r}")
