"""monitor — Monitoring commands for app health, DID resolution, shinka, and votes."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds
from .shannon import _resolve_root


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    h = {"Content-Type": "application/json"}
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


@click.group("monitor", invoke_without_command=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def monitor(ctx: click.Context, pds: str | None, json_out: bool) -> None:
    """Monitor app health, DID resolution, shinka status, and votes."""
    if ctx.invoked_subcommand is not None:
        return
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/health", timeout=10)
        status = "up" if resp.status_code < 400 else "degraded"
    except httpx.HTTPError:
        status = "down"
    if json_out:
        click.echo(json.dumps({"pds": pds_url, "status": status}, ensure_ascii=False, indent=2))
    else:
        click.echo(f"monitor: pds={pds_url}  status={status}")


@monitor.command("health")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def monitor_health(pds: str | None, json_out: bool) -> None:
    """Check PDS and actor health endpoints."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    checks = []
    for path in ["/health", "/_app/meta"]:
        try:
            start = time.monotonic()
            resp = httpx.get(f"{pds_url}{path}", timeout=10)
            latency_ms = int((time.monotonic() - start) * 1000)
            checks.append({"path": path, "status": resp.status_code,
                           "ok": resp.status_code < 400, "latency_ms": latency_ms})
        except httpx.HTTPError as e:
            checks.append({"path": path, "status": 0, "ok": False, "error": str(e)})
    if json_out:
        click.echo(json.dumps(checks, ensure_ascii=False, indent=2))
    else:
        for c in checks:
            ok = "OK  " if c.get("ok") else "FAIL"
            click.echo(f"  [{ok}] {c['path']}  {c.get('status', 0)}  {c.get('latency_ms', '?')}ms")


@monitor.command("did")
@click.argument("did_or_handle")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def monitor_did(did_or_handle: str, pds: str | None, json_out: bool) -> None:
    """Resolve and monitor a DID or handle."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.atproto.identity.resolveHandle",
            params={"handle": did_or_handle}, headers=_auth_headers(), timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"did: {data.get('did', '?')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"resolve error: {e}")


@dataclass
class DiscoveredApp:
    nanoid: str
    name: str
    ui_type: str
    did: str
    dir: Path


@dataclass
class SubDIDFreshness:
    path: str
    collection: str = ""
    last_updated: str = ""
    age_hours: int = 0
    stale: bool = False


@dataclass
class ShinkaStatus:
    nanoid: str
    name: str
    did: str
    has_joucho: bool = False
    has_inbox: bool = False
    has_cadence: bool = False
    has_old_timer: bool = False
    heartbeat_ok: bool = False
    hb_actions: str = ""
    hb_mood: str = ""
    has_drill: bool = False
    has_validate: bool = False
    has_analyze: bool = False
    has_engage: bool = False
    shinka_score: int = 0
    domain_score: int = 0
    domain_grade: str = ""
    domain_gaps: list[str] = field(default_factory=list)
    kg_nodes: int = 0
    kg_labels: int = 0
    kg_score: int = 0
    hyoka_score: int = 0
    hyoka_grade: str = ""
    sub_did_fresh: list[SubDIDFreshness] = field(default_factory=list)
    stale_sub_did: int = 0
    error: str = ""


_RE_COLLECTION = re.compile(r'["\']((com\.etzhayyim\.apps|app\.bsky)\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_.\-]+)["\']')
_RE_PATH_DECL = re.compile(r'path:\s*"([^"]+)"')


def _discover_apps(scan_dir: str, nanoid_filter: str, name_filter: str) -> list[DiscoveredApp]:
    apps: list[DiscoveredApp] = []
    try:
        root = _resolve_root(None)
    except Exception:
        root = None
    base = root / scan_dir if root else Path(scan_dir)
    if not base.exists():
        base = Path(scan_dir)

    for mpath in sorted(base.rglob("kotodama.jsonld")):
        try:
            data = json.loads(mpath.read_text())
        except Exception:
            continue
        nanoid = data.get("nanoid", "")
        if not nanoid:
            continue
        if nanoid_filter and nanoid != nanoid_filter:
            continue
        name = data.get("profile", {}).get("displayName", nanoid)
        if name_filter:
            import fnmatch
            if not fnmatch.fnmatch(name, name_filter) and not fnmatch.fnmatch(nanoid, name_filter):
                continue
        apps.append(DiscoveredApp(
            nanoid=nanoid,
            name=name,
            ui_type=data.get("uiType", ""),
            did=data.get("@id", f"did:web:{nanoid}.etzhayyim.com"),
            dir=mpath.parent,
        ))
    return apps


def _compute_shinka_score(s: ShinkaStatus) -> int:
    score = 0
    if s.has_joucho:
        score += 30
    if s.has_inbox:
        score += 15
    if s.has_cadence:
        score += 15
    if s.has_drill:
        score += 10
    if s.has_validate:
        score += 10
    if s.has_analyze:
        score += 10
    if s.has_engage:
        score += 10
    if s.has_old_timer:
        score -= 30
    return max(0, score)


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


def _tier_score(val: int, t1: int, t2: int, t3: int) -> float:
    if val >= t3:
        return 100.0
    if val >= t2:
        return 60.0 + 40.0 * (val - t2) / (t3 - t2)
    if val >= t1:
        return 20.0 + 40.0 * (val - t1) / (t2 - t1)
    if val > 0:
        return 20.0 * val / t1
    return 0.0


def _collection_namespace_candidates(app: DiscoveredApp) -> list[str]:
    candidates = [app.nanoid]
    mpath = app.dir / "kotodama.jsonld"
    try:
        data = json.loads(mpath.read_text())
        for col in data.get("collections", []):
            parts = col.split(".")
            if len(parts) >= 4:
                candidates.append(parts[3])
    except Exception:
        pass
    return list(dict.fromkeys(candidates))


def _normalize_domain_lookup(v: str) -> str:
    return v.replace("-", "_").strip()


def _extract_collection_literals(src: str, ns_candidates: list[str]) -> list[str]:
    prefixes = [f"com.etzhayyim.apps.{_normalize_domain_lookup(ns)}." for ns in ns_candidates if ns]
    seen: set[str] = set()
    out: list[str] = []
    for m in _RE_COLLECTION.finditer(src):
        col = m.group(1).strip()
        if not col or col in seen:
            continue
        if prefixes:
            if not any(col.startswith(pfx) for pfx in prefixes):
                continue
        seen.add(col)
        out.append(col)
    return out


def _extract_sub_did_paths(src: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for m in _RE_PATH_DECL.finditer(src):
        p = m.group(1).strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _latest_record_ts(client: httpx.Client, pds_url: str, token: str, repo: str, collection: str) -> datetime | None:
    try:
        resp = client.get(
            f"{pds_url}/xrpc/com.atproto.repo.listRecords",
            params={"repo": repo, "collection": collection, "limit": 1},
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=10,
        )
        if resp.status_code >= 400:
            return None
        data = resp.json()
        records = data.get("records", [])
        if not records:
            return None
        val = records[0].get("value", {})
        raw = val.get("updatedAt") or val.get("createdAt") or ""
        if raw:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        pass
    return None


def _probe_sub_did_freshness(
    client: httpx.Client, pds_url: str, token: str,
    nanoid: str, paths: list[str], collections: list[str], threshold_hours: int,
) -> list[SubDIDFreshness]:
    if not paths or not collections:
        return []
    now = datetime.now(timezone.utc)
    out: list[SubDIDFreshness] = []
    for path in paths:
        sub_did_path = path.strip("/").replace("/", ":")
        sub_did = f"did:web:{nanoid}.etzhayyim.com:{sub_did_path}"
        best_ts: datetime | None = None
        best_col = ""
        for col in collections:
            ts = _latest_record_ts(client, pds_url, token, sub_did, col)
            if ts and (best_ts is None or ts > best_ts):
                best_ts = ts
                best_col = col
        f = SubDIDFreshness(path=path, collection=best_col)
        if best_ts:
            age_h = int((now - best_ts).total_seconds() / 3600)
            f.last_updated = best_ts.isoformat()
            f.age_hours = age_h
            f.stale = age_h >= threshold_hours
        else:
            f.stale = True
        out.append(f)
    return out


def _analyze_shinka_app(
    app: DiscoveredApp,
    live: bool,
    hyoka: bool,
    pds_url: str,
    token: str,
    domain_by_nanoid: dict[str, Any],
    freshness_hours: int,
    timeout: int,
) -> ShinkaStatus:
    s = ShinkaStatus(
        nanoid=app.nanoid,
        name=app.name,
        did=f"did:web:{app.nanoid}.etzhayyim.com",
    )

    app_ts = app.dir / "src" / "app.ts"
    if not app_ts.exists():
        s.error = "no app.ts"
        return s

    src = app_ts.read_text(errors="replace")
    s.has_joucho = "resolveHeartbeatCadence" in src
    s.has_inbox = "createInboxBuffer" in src
    s.has_cadence = "createCadenceState" in src
    s.has_old_timer = "heartbeatCount %" in src
    s.has_drill = "shouldDrill" in src
    s.has_validate = "shouldValidate" in src
    s.has_analyze = "shouldAnalyze" in src
    s.has_engage = "shouldEngage" in src
    s.shinka_score = _compute_shinka_score(s)

    if freshness_hours > 0:
        ns_candidates = _collection_namespace_candidates(app)
        collections = _extract_collection_literals(src, ns_candidates)
        paths = _extract_sub_did_paths(src)
        with httpx.Client(timeout=timeout) as client:
            s.sub_did_fresh = _probe_sub_did_freshness(
                client, pds_url, token, app.nanoid, paths, collections, freshness_hours
            )
        s.stale_sub_did = sum(1 for f in s.sub_did_fresh if f.stale)

    if live:
        try:
            with httpx.Client(timeout=timeout) as client:
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                resp = client.post(
                    f"https://{app.nanoid}.etzhayyim.com/_heartbeat", headers=headers
                )
                body = resp.json()
                s.heartbeat_ok = body.get("ok", False)
                actions = body.get("actions", [])
                if isinstance(actions, list) and actions:
                    s.hb_mood = str(actions[0].get("mood", ""))
                    s.hb_actions = str(actions[0].get("action", ""))
        except Exception:
            s.error = "heartbeat unreachable"

    if hyoka:
        dr = domain_by_nanoid.get(app.nanoid)
        if dr:
            s.domain_score = dr.get("domain_score", 0)
            s.domain_grade = dr.get("grade", "")
            s.domain_gaps = dr.get("missing", [])
        s.kg_nodes = 0
        s.kg_labels = 0
        kg_nodes_score = int(_tier_score(s.kg_nodes, 1, 10, 100))
        kg_label_score = int(_tier_score(s.kg_labels, 3, 8, 20))
        s.kg_score = min(100, int(kg_nodes_score * 0.7 + kg_label_score * 0.3))
        s.hyoka_score = min(100, int(0.45 * s.shinka_score + 0.35 * s.domain_score + 0.20 * s.kg_score))
        s.hyoka_grade = _coverage_grade(s.hyoka_score)

    return s


def _store_hyoka_results(
    ws_root: Path, results: list[ShinkaStatus],
    gate: bool, max_avg_drop: float, max_top10_drop: float, max_low_increase: int,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "snapshot_at": now, "nanoid": r.nanoid, "name": r.name,
            "has_joucho": r.has_joucho, "has_inbox": r.has_inbox,
            "has_cadence": r.has_cadence, "has_drill": r.has_drill,
            "has_validate": r.has_validate, "has_analyze": r.has_analyze,
            "has_engage": r.has_engage, "shinka_score": r.shinka_score,
            "domain_score": r.domain_score, "domain_grade": r.domain_grade,
            "kg_nodes": r.kg_nodes, "kg_labels": r.kg_labels,
            "kg_score": r.kg_score, "hyoka_score": r.hyoka_score,
            "hyoka_grade": r.hyoka_grade, "stale_sub_did": r.stale_sub_did,
        }
        for r in results
    ]

    hyoka_dir = ws_root / "80-data" / "hyoka"
    hyoka_dir.mkdir(parents=True, exist_ok=True)
    ts_slug = now[:19].replace(":", "").replace("-", "").replace("T", "_")
    ndjson_path = hyoka_dir / f"hyoka_{ts_slug}.ndjson"
    with ndjson_path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    parquet_path = hyoka_dir / f"hyoka_{ts_slug}.parquet"
    sql = (
        f"COPY (SELECT * FROM read_ndjson_auto('{ndjson_path}')) "
        f"TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION ZSTD);"
    )
    result = subprocess.run(
        ["duckdb", "-c", sql], capture_output=True, text=True
    )
    if result.returncode == 0:
        ndjson_path.unlink(missing_ok=True)
        click.echo(f"hyoka stored: {parquet_path}", err=True)
    else:
        click.echo(f"hyoka store warning: {result.stderr.strip()}", err=True)
        parquet_path = ndjson_path

    scores = [r.hyoka_score for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    top10_avg = sum(sorted(scores, reverse=True)[:10]) / min(10, len(scores)) if scores else 0.0
    low_count = sum(1 for s in scores if s < 60)
    click.echo(f"hyoka summary: avg={avg_score:.2f} top10={top10_avg:.2f} low={low_count}", err=True)

    if not gate:
        return

    # Gate: query previous snapshot
    glob_path = hyoka_dir / "hyoka_*.parquet"
    prev_sql = f"""
SELECT round(avg(hyoka_score), 2) AS avg_score,
  round(avg(CASE WHEN rn <= 10 THEN hyoka_score END), 2) AS top10_avg,
  count(CASE WHEN hyoka_score < 60 THEN 1 END) AS low_count
FROM (
  SELECT hyoka_score, snapshot_at,
    row_number() OVER (ORDER BY hyoka_score DESC) AS rn
  FROM read_parquet('{glob_path}')
  WHERE snapshot_at = (
    SELECT snapshot_at FROM read_parquet('{glob_path}')
    GROUP BY snapshot_at ORDER BY snapshot_at DESC LIMIT 1 OFFSET 1
  )
) sub
"""
    result = subprocess.run(
        ["duckdb", "-json", "-c", prev_sql], capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        click.echo("hyoka gate: no previous snapshot, skipping", err=True)
        return

    try:
        prev_rows = json.loads(result.stdout)
        prev = prev_rows[0] if prev_rows else {}
    except Exception:
        click.echo("hyoka gate: could not parse previous snapshot", err=True)
        return

    prev_avg = float(prev.get("avg_score") or 0)
    prev_top10 = float(prev.get("top10_avg") or 0)
    prev_low = int(prev.get("low_count") or 0)

    failures = []
    if (prev_avg - avg_score) > max_avg_drop:
        failures.append(f"avg_hyoka drop {prev_avg - avg_score:.2f} > {max_avg_drop}")
    if (prev_top10 - top10_avg) > max_top10_drop:
        failures.append(f"top10_hyoka drop {prev_top10 - top10_avg:.2f} > {max_top10_drop}")
    if (low_count - prev_low) > max_low_increase:
        failures.append(f"low-score increase {low_count - prev_low} > {max_low_increase}")

    if failures:
        click.echo("hyoka gate failed:", err=True)
        for f in failures:
            click.echo(f"  - {f}", err=True)
        raise click.ClickException("hyoka gate: regression detected")
    click.echo("hyoka gate: passed", err=True)


def _print_shinka_table(results: list[ShinkaStatus]) -> None:
    joucho = sum(1 for r in results if r.has_joucho)
    old_timer = sum(1 for r in results if r.has_old_timer)
    drill = sum(1 for r in results if r.has_drill)

    click.echo(f"\nShinka/Kyumei-Koji Health ({len(results)} apps)\n")
    header = (
        "Shinka  Hyoka   Domain  KG  Nanoid    Name                  "
        "Joucho  Inbox  Cadence  Drill  Validate  Analyze  Engage  OldTimer  StaleSubDID  Mood"
    )
    click.echo(header)
    click.echo("-" * len(header))

    for r in results:
        hyoka_cell = "—"
        if r.hyoka_score or r.domain_score or r.kg_score:
            if r.hyoka_grade:
                hyoka_cell = f"{r.hyoka_score}({r.hyoka_grade})"
            else:
                hyoka_cell = str(r.hyoka_score)

        def bm(b: bool) -> str:
            return "✓" if b else "·"

        def vm(b: bool) -> str:
            return "!!✗" if b else "✓"

        name = (r.name[:19] + "…") if len(r.name) > 20 else r.name
        click.echo(
            f"{r.shinka_score:<7} {hyoka_cell:<7} {r.domain_score:<7} {r.kg_score:<3} "
            f"{r.nanoid:<9} {name:<22}"
            f"{bm(r.has_joucho):<7} {bm(r.has_inbox):<6} {bm(r.has_cadence):<8} "
            f"{bm(r.has_drill):<6} {bm(r.has_validate):<9} {bm(r.has_analyze):<8} "
            f"{bm(r.has_engage):<7} {vm(r.has_old_timer):<9} {r.stale_sub_did:<12} {r.hb_mood}"
        )

    pct = lambda n, t: (100 * n / t) if t else 0
    click.echo()
    click.echo("Summary:")
    click.echo(f"  joucho cadence:  {joucho}/{len(results)} ({pct(joucho, len(results)):.0f}%)")
    click.echo(f"  old timer (!!):  {old_timer}/{len(results)} ({pct(old_timer, len(results)):.0f}% violation)")
    click.echo(f"  kyumei-koji:     {drill}/{len(results)} ({pct(drill, len(results)):.0f}% have shouldDrill)")


@monitor.command("shinka")
@click.option("--dir", "scan_dir", default="60-apps", show_default=True,
              help="Parent directory to scan for kotodama.jsonld")
@click.option("--filter", "name_filter", default="", help="Glob pattern for app names")
@click.option("--nanoid", default="", help="Check a single app by nanoid")
@click.option("--concurrency", default=16, show_default=True, help="Parallel workers")
@click.option("--timeout", "timeout_s", default=10, show_default=True, help="HTTP timeout in seconds")
@click.option("--live", is_flag=True, default=False, help="POST /_heartbeat to test live cadence")
@click.option("--hyoka", is_flag=True, default=False,
              help="Include domain coverage + actor KG metrics")
@click.option("--pds", "pds_url", default="https://atproto.etzhayyim.com", show_default=True,
              help="PDS base URL for hyoka/freshness mode")
@click.option("--freshness-hours", default=24, show_default=True,
              help="Sub-DID freshness warning threshold (hours)")
@click.option("--json", "json_out", is_flag=True, default=False, help="JSON output")
@click.option("--store", "store_out", is_flag=True, default=False,
              help="Store results to 80-data/hyoka/ Parquet (requires duckdb)")
@click.option("--gate", is_flag=True, default=False,
              help="Fail if hyoka regresses beyond thresholds (use with --store)")
@click.option("--max-avg-drop", default=3.0, show_default=True,
              help="Max allowed avg hyoka_score drop (gate)")
@click.option("--max-top10-drop", default=5.0, show_default=True,
              help="Max allowed top-10 avg drop (gate)")
@click.option("--max-low-increase", default=5, show_default=True,
              help="Max allowed increase in low-score (<60) actors (gate)")
def monitor_shinka(
    scan_dir: str, name_filter: str, nanoid: str,
    concurrency: int, timeout_s: int, live: bool,
    hyoka: bool, pds_url: str, freshness_hours: int,
    json_out: bool, store_out: bool, gate: bool,
    max_avg_drop: float, max_top10_drop: float, max_low_increase: int,
) -> None:
    """Analyze shinka/kyumei-koji implementation quality across apps."""
    pds_url = pds_url.rstrip("/")
    token = os.environ.get("etzhayyim_TOKEN", "")
    if not token:
        auth = _load_auth()
        token = auth.get("accessJwt") or auth.get("access_token") or ""

    domain_by_nanoid: dict[str, Any] = {}

    apps = _discover_apps(scan_dir, nanoid, name_filter)
    if not apps:
        click.echo("No apps found", err=True)
        return

    click.echo(f"==> Analyzing shinka/kyumei-koji for {len(apps)} apps...\n", err=True)

    results: list[ShinkaStatus] = [None] * len(apps)  # type: ignore

    def analyze(idx: int, app: DiscoveredApp) -> None:
        results[idx] = _analyze_shinka_app(
            app, live, hyoka, pds_url, token, domain_by_nanoid, freshness_hours, timeout_s
        )

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(analyze, i, app): i for i, app in enumerate(apps)}
        for fut in as_completed(futures):
            fut.result()

    results.sort(key=lambda r: (-_compute_shinka_score(r), r.name))

    if json_out:
        import dataclasses
        out = [dataclasses.asdict(r) for r in results]
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        _print_shinka_table(results)

    if store_out:
        try:
            ws_root = _resolve_root(None)
        except Exception:
            ws_root = Path(".")
        _store_hyoka_results(ws_root, results, gate, max_avg_drop, max_top10_drop, max_low_increase)


@monitor.command("vote")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def monitor_vote(pds: str | None, json_out: bool) -> None:
    """Monitor governance votes."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.governance.listVotes",
            headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            votes = data if isinstance(data, list) else data.get("votes", [])
            for v in votes:
                click.echo(f"  {v.get('id', '')}  {v.get('proposal', '')}  "
                           f"yes={v.get('yes', 0)}  no={v.get('no', 0)}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")
