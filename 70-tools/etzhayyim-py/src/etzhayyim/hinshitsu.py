"""hinshitsu (品質) — Code quality analysis for the actor fleet."""
from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click
import httpx

from .shannon import _resolve_root


def _discover_actors(ws: Path) -> list[dict]:
    actors = []
    base = ws / "20-actors"
    iterator = base.rglob("kotodama.jsonld") if base.exists() else ws.rglob("kotodama.jsonld")
    for p in iterator:
        try:
            data = json.loads(p.read_text(errors="replace"))
        except Exception:
            continue
        if not data.get("nanoid"):
            continue
        actors.append({
            "nanoid": data["nanoid"],
            "name": data.get("name", ""),
            "did": data.get("did", ""),
            "performerType": data.get("performerType", ""),
            "description": data.get("description", ""),
            "dir": str(p.parent),
            "manifest_path": str(p),
        })
    return actors


def _score_actor(actor: dict) -> tuple[int, list[str]]:
    issues = []
    score = 100
    p = Path(actor["dir"])
    for req in ["kotodama.jsonld", "src/app.ts", "wrangler.jsonc"]:
        if not (p / req).exists():
            issues.append(f"missing:{req}")
            score -= 20
    for fld in ["name", "did", "performerType", "description"]:
        if not actor.get(fld):
            issues.append(f"missing_field:{fld}")
            score -= 5
    app_ts = p / "src" / "app.ts"
    if app_ts.exists():
        src = app_ts.read_text(errors="replace")
        if '"nsid"' in src:
            issues.append("nsid_placeholder")
            score -= 10
        if re.search(r'"(?:claude-3|gpt-4|gemini-|llama-)[^"]*"', src, re.IGNORECASE):
            issues.append("hardcoded_model")
            score -= 10
    return max(score, 0), issues


def _grade(score: int) -> str:
    if score >= 90:
        return "S"
    if score >= 70:
        return "A"
    if score >= 50:
        return "B"
    if score >= 30:
        return "C"
    return "D"


def _build_actor_report(actor: dict) -> dict:
    score, issues = _score_actor(actor)
    return {
        "nanoid": actor["nanoid"],
        "name": actor["name"],
        "score": score,
        "grade": _grade(score),
        "issues": issues,
        "dir": actor["dir"],
    }


def _fix_suggestions(issues: list[str]) -> list[str]:
    suggestions = []
    for issue in issues:
        if issue.startswith("missing:"):
            fname = issue[len("missing:"):]
            suggestions.append(f"Create {fname}")
        elif issue.startswith("missing_field:"):
            fname = issue[len("missing_field:"):]
            suggestions.append(f"Add '{fname}' field to kotodama.jsonld")
        elif issue == "nsid_placeholder":
            suggestions.append('Replace "nsid" placeholder with proper NSID (com.etzhayyim.apps.<actor>.<method>)')
        elif issue == "hardcoded_model":
            suggestions.append("Replace hardcoded model name with resolveModelId() / MURAKUMO_DEFAULT_MODEL")
    return suggestions


def _health_check(nanoid: str, timeout: float) -> dict:
    url = f"https://{nanoid}.etzhayyim.com/health"
    t0 = time.monotonic()
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        latency_ms = int((time.monotonic() - t0) * 1000)
        return {
            "nanoid": nanoid,
            "url": url,
            "health_ok": resp.status_code < 400,
            "status_code": resp.status_code,
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        latency_ms = int((time.monotonic() - t0) * 1000)
        return {
            "nanoid": nanoid,
            "url": url,
            "health_ok": False,
            "status_code": None,
            "latency_ms": latency_ms,
            "error": str(exc),
        }


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group("hinshitsu", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def hinshitsu(ctx: click.Context, workspace_dir: str | None, json_out: bool) -> None:
    """hinshitsu (品質) — Code quality analysis for the actor fleet."""
    if ctx.invoked_subcommand is None:
        ws = _resolve_root(workspace_dir)
        actors = _discover_actors(ws)
        reports = [_build_actor_report(a) for a in actors]
        reports.sort(key=lambda r: r["score"])
        total = len(reports)
        avg = sum(r["score"] for r in reports) / total if total else 0
        grades = {g: sum(1 for r in reports if r["grade"] == g) for g in ("S", "A", "B", "C", "D")}
        summary = {"total": total, "avg_score": round(avg, 1), "grades": grades, "actors": reports}
        if json_out:
            click.echo(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            click.echo(f"hinshitsu: {total} actors  avg={avg:.1f}")
            click.echo(f"  S={grades['S']} A={grades['A']} B={grades['B']} C={grades['C']} D={grades['D']}")


@hinshitsu.command("actors")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--min-score", default=0, type=int, show_default=True)
@click.option("--top", default=20, type=int, show_default=True)
def hinshitsu_actors(workspace_dir: str | None, json_out: bool, min_score: int, top: int) -> None:
    """Scan workspace actors for code quality issues."""
    ws = _resolve_root(workspace_dir)
    actors = _discover_actors(ws)
    reports = [_build_actor_report(a) for a in actors]
    reports = [r for r in reports if r["score"] >= min_score]
    reports.sort(key=lambda r: r["score"])
    reports = reports[:top]
    if json_out:
        click.echo(json.dumps({"total": len(reports), "actors": reports}, ensure_ascii=False, indent=2))
    else:
        click.echo(f"hinshitsu actors: {len(reports)} actors")
        for r in reports:
            issues_str = ", ".join(r["issues"]) if r["issues"] else "ok"
            click.echo(f"  [{r['grade']}] {r['score']:3d}  {r['nanoid']:20}  {r['name'][:24]:<24}  {issues_str}")


@hinshitsu.command("kojo")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--top", default=10, type=int, show_default=True)
def hinshitsu_kojo(workspace_dir: str | None, json_out: bool, top: int) -> None:
    """Improvement factory: rank worst actors and show fix suggestions."""
    ws = _resolve_root(workspace_dir)
    actors = _discover_actors(ws)
    reports = [_build_actor_report(a) for a in actors]
    reports.sort(key=lambda r: r["score"])
    reports = reports[:top]
    for r in reports:
        r["suggestions"] = _fix_suggestions(r["issues"])
    if json_out:
        click.echo(json.dumps({"top": top, "actors": reports}, ensure_ascii=False, indent=2))
    else:
        click.echo(f"hinshitsu kojo: top {top} actors needing improvement")
        for r in reports:
            click.echo(f"\n  [{r['grade']}] {r['score']:3d}  {r['nanoid']}  {r['name']}")
            for sug in r["suggestions"]:
                click.echo(f"       -> {sug}")


@hinshitsu.group("fleet")
@click.option("--pds", default=None)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def hinshitsu_fleet(ctx: click.Context, pds: str | None, workspace_dir: str | None, json_out: bool) -> None:
    """Fleet-wide quality operations."""
    ctx.ensure_object(dict)
    ctx.obj["pds"] = pds
    ctx.obj["workspace_dir"] = workspace_dir
    ctx.obj["json_out"] = json_out


@hinshitsu_fleet.command("scan")
@click.option("--pds", default=None)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--timeout", default=15, type=float, show_default=True)
def hinshitsu_fleet_scan(pds: str | None, workspace_dir: str | None, json_out: bool, timeout: float) -> None:
    """Parallel health check for each actor URL."""
    ws = _resolve_root(workspace_dir)
    actors = _discover_actors(ws)
    if not actors:
        click.echo("no actors discovered")
        return
    results = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {pool.submit(_health_check, a["nanoid"], timeout): a for a in actors}
        for fut in as_completed(futures):
            results.append(fut.result())
    results.sort(key=lambda r: r["nanoid"])
    ok = sum(1 for r in results if r["health_ok"])
    if json_out:
        click.echo(json.dumps({"total": len(results), "healthy": ok, "actors": results}, ensure_ascii=False, indent=2))
    else:
        click.echo(f"fleet scan: {ok}/{len(results)} healthy")
        for r in results:
            status = "UP  " if r["health_ok"] else "DOWN"
            code = r["status_code"] or "---"
            click.echo(f"  [{status}] {r['nanoid']:20}  {code}  {r['latency_ms']}ms")


@hinshitsu_fleet.command("evaluate")
@click.option("--pds", default=None)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def hinshitsu_fleet_evaluate(pds: str | None, workspace_dir: str | None, json_out: bool) -> None:
    """Combine static quality scores with fleet health."""
    ws = _resolve_root(workspace_dir)
    actors = _discover_actors(ws)
    quality = {_build_actor_report(a)["nanoid"]: _build_actor_report(a) for a in actors}
    health_results = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {pool.submit(_health_check, a["nanoid"], 10.0): a for a in actors}
        for fut in as_completed(futures):
            health_results.append(fut.result())
    health_by_nanoid = {r["nanoid"]: r for r in health_results}
    composite = []
    for nanoid, q in quality.items():
        h = health_by_nanoid.get(nanoid, {})
        composite.append({
            "nanoid": nanoid,
            "name": q["name"],
            "quality_score": q["score"],
            "grade": q["grade"],
            "health_ok": h.get("health_ok"),
            "latency_ms": h.get("latency_ms"),
            "issues": q["issues"],
        })
    composite.sort(key=lambda r: r["quality_score"])
    if json_out:
        click.echo(json.dumps({"total": len(composite), "actors": composite}, ensure_ascii=False, indent=2))
    else:
        click.echo(f"fleet evaluate: {len(composite)} actors")
        for r in composite:
            health_str = "UP" if r["health_ok"] else ("DOWN" if r["health_ok"] is False else "?")
            click.echo(f"  [{r['grade']}] {r['quality_score']:3d}  {health_str:4}  {r['nanoid']:20}  {r['name']}")


@hinshitsu_fleet.command("verify")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--min-score", default=50, type=int, show_default=True)
def hinshitsu_fleet_verify(workspace_dir: str | None, json_out: bool, min_score: int) -> None:
    """Verify all actors meet minimum quality score. Exits 1 on violations."""
    ws = _resolve_root(workspace_dir)
    actors = _discover_actors(ws)
    reports = [_build_actor_report(a) for a in actors]
    violations = [r for r in reports if r["score"] < min_score]
    passed = len(violations) == 0
    if json_out:
        click.echo(json.dumps({
            "passed": passed,
            "min_score": min_score,
            "total": len(reports),
            "violations": violations,
        }, ensure_ascii=False, indent=2))
    else:
        if passed:
            click.echo(f"fleet verify: PASS  all {len(reports)} actors >= {min_score}")
        else:
            click.echo(f"fleet verify: FAIL  {len(violations)}/{len(reports)} actors below {min_score}")
            for r in violations:
                click.echo(f"  [{r['grade']}] {r['score']:3d}  {r['nanoid']:20}  {r['name']}")
    if not passed:
        sys.exit(1)


@hinshitsu_fleet.command("kaizen")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--top", default=5, type=int, show_default=True)
def hinshitsu_fleet_kaizen(workspace_dir: str | None, json_out: bool, top: int) -> None:
    """Top-N actors needing improvement with action items."""
    ws = _resolve_root(workspace_dir)
    actors = _discover_actors(ws)
    reports = [_build_actor_report(a) for a in actors]
    reports.sort(key=lambda r: r["score"])
    reports = reports[:top]
    for r in reports:
        r["suggestions"] = _fix_suggestions(r["issues"])
    if json_out:
        click.echo(json.dumps({"top": top, "actors": reports}, ensure_ascii=False, indent=2))
    else:
        click.echo(f"fleet kaizen: top {top} actors needing improvement")
        for r in reports:
            click.echo(f"\n  [{r['grade']}] {r['score']:3d}  {r['nanoid']}  {r['name']}")
            for sug in r["suggestions"]:
                click.echo(f"       -> {sug}")


def _load_json_file(path: str) -> dict:
    import pathlib
    p = pathlib.Path(path)
    if not p.exists():
        raise click.ClickException(f"file not found: {path}")
    with open(p) as f:
        return json.load(f)


def _diff_snap(dids: list[str], scan_map: dict, score_map: dict) -> dict:
    scan_count = sum(1 for d in dids if d in scan_map)
    score_count = sum(1 for d in dids if d in score_map)
    did_doc_reachable = sum(
        1 for d in dids
        if scan_map.get(d, {}).get("did_doc_reachable") or scan_map.get(d, {}).get("DidDocReachable")
    )
    atproto_reachable = sum(
        1 for d in dids
        if scan_map.get(d, {}).get("atproto_did_reachable") or scan_map.get(d, {}).get("AtprotoDidReachable")
    )
    with_posts = sum(
        1 for d in dids
        if scan_map.get(d, {}).get("with_posts") or scan_map.get(d, {}).get("WithPosts")
    )
    scores = [
        score_map[d].get("total_score") or score_map[d].get("TotalScore", 0)
        for d in dids if d in score_map
    ]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    return {
        "scan_count": scan_count,
        "score_count": score_count,
        "did_doc_reachable": did_doc_reachable,
        "atproto_did_reachable": atproto_reachable,
        "with_posts": with_posts,
        "avg_total_score": avg_score,
    }


@hinshitsu_fleet.command("diff-fixed")
@click.option("--before-scan", "before_scan_path", required=True, help="before scan report JSON")
@click.option("--after-scan", "after_scan_path", required=True, help="after scan report JSON")
@click.option("--before-score", "before_score_path", required=True, help="before score report JSON")
@click.option("--after-score", "after_score_path", required=True, help="after score report JSON")
@click.option("--did-list", "did_list_path", default=None, help="optional fixed DID list file (one DID per line)")
@click.option("--out", default=None, help="write JSON report to file")
@click.option("--json", "json_out", is_flag=True, default=False)
def hinshitsu_fleet_diff_fixed(
    before_scan_path: str,
    after_scan_path: str,
    before_score_path: str,
    after_score_path: str,
    did_list_path: str | None,
    out: str | None,
    json_out: bool,
) -> None:
    """Compare before/after fleet scan+score reports to measure improvement delta."""
    import pathlib

    before_scan = _load_json_file(before_scan_path)
    after_scan = _load_json_file(after_scan_path)
    before_score = _load_json_file(before_score_path)
    after_score = _load_json_file(after_score_path)

    def _to_map(report: dict, key_field: str) -> dict:
        items = report.get("targets") or report.get("results") or report.get("Targets") or report.get("Results") or []
        return {
            (item.get(key_field) or item.get(key_field.capitalize(), "")): item
            for item in items
            if item.get(key_field) or item.get(key_field.capitalize())
        }

    before_scan_map = _to_map(before_scan, "did")
    after_scan_map = _to_map(after_scan, "did")
    before_score_map = _to_map(before_score, "did")
    after_score_map = _to_map(after_score, "did")

    if did_list_path:
        raw = pathlib.Path(did_list_path).read_text().splitlines()
        dids = sorted({line.strip() for line in raw if line.strip()})
    else:
        all_dids = (
            set(before_scan_map) | set(after_scan_map) |
            set(before_score_map) | set(after_score_map)
        )
        dids = sorted(d for d in all_dids if d)

    missing_before = [d for d in dids if d not in before_scan_map or d not in before_score_map]
    missing_after = [d for d in dids if d not in after_scan_map or d not in after_score_map]

    before_snap = _diff_snap(dids, before_scan_map, before_score_map)
    after_snap = _diff_snap(dids, after_scan_map, after_score_map)

    report = {
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "compared_dids": dids,
        "missing_in_before": missing_before,
        "missing_in_after": missing_after,
        "before": before_snap,
        "after": after_snap,
        "delta": {
            "scan_count": after_snap["scan_count"] - before_snap["scan_count"],
            "score_count": after_snap["score_count"] - before_snap["score_count"],
            "did_doc_reachable": after_snap["did_doc_reachable"] - before_snap["did_doc_reachable"],
            "atproto_did_reachable": after_snap["atproto_did_reachable"] - before_snap["atproto_did_reachable"],
            "with_posts": after_snap["with_posts"] - before_snap["with_posts"],
            "avg_total_score": round(after_snap["avg_total_score"] - before_snap["avg_total_score"], 2),
        },
    }
    if did_list_path:
        report["did_list_source"] = did_list_path

    output = json.dumps(report, ensure_ascii=False, indent=2)
    if out:
        import pathlib
        pathlib.Path(out).write_text(output)
        click.echo(f"wrote diff report: {out}", err=True)
    elif json_out:
        click.echo(output)
    else:
        click.echo(f"diff-fixed: {len(dids)} DIDs compared")
        click.echo(f"  before: scan={before_snap['scan_count']} score={before_snap['score_count']} "
                   f"avg_score={before_snap['avg_total_score']}")
        click.echo(f"  after:  scan={after_snap['scan_count']} score={after_snap['score_count']} "
                   f"avg_score={after_snap['avg_total_score']}")
        d = report["delta"]
        click.echo(f"  delta:  scan={d['scan_count']:+d} score={d['score_count']:+d} "
                   f"avg_score={d['avg_total_score']:+.2f}")
        if missing_before:
            click.echo(f"  missing in before: {len(missing_before)}")
        if missing_after:
            click.echo(f"  missing in after:  {len(missing_after)}")
