"""coverage — Coverage analysis commands (Python port).

domain: reuses kaizen 9-axis scoring.
actors: scans magatama.jsonld for metadata completeness.
actors heal: LLM-driven metadata healing for actors with missing fields.
test:   runs local test suites (pytest / cargo / go test).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

import click
import httpx

from .kaizen import collect_and_score_domain_apps, build_kaizen_report
from .shannon import _resolve_root

_RE_JSON_BLOCK = re.compile(r'\{[\s\S]+\}', re.DOTALL)
_DEFAULT_MURAKUMO = "https://murakumo.etzhayyim.com"
_DEFAULT_OLLAMA = "http://127.0.0.1:11434"


# ── actors metadata completeness ───────────────────────────────────────────────

_REQUIRED_FIELDS = ["nanoid", "did", "name", "performerType"]
_OPTIONAL_FIELDS = ["uiType", "runtimeType", "collections", "governance"]


def _check_actor_completeness(data: dict) -> dict[str, bool]:
    return {
        field: bool(data.get(field))
        for field in _REQUIRED_FIELDS + _OPTIONAL_FIELDS
    }


def _scan_actors(ws: Path) -> list[dict]:
    projects_dir = ws / "60-apps"
    if not projects_dir.exists():
        projects_dir = ws / "projects"
    if not projects_dir.exists():
        return []

    results = []
    for jsonld_path in projects_dir.rglob("magatama.jsonld"):
        try:
            data = json.loads(jsonld_path.read_text(errors="replace"))
        except (OSError, json.JSONDecodeError):
            continue
        completeness = _check_actor_completeness(data)
        missing = [f for f, present in completeness.items() if not present and f in _REQUIRED_FIELDS]
        score = int(sum(completeness.values()) / len(completeness) * 100)
        results.append({
            "nanoid": data.get("nanoid", ""),
            "name": data.get("name", ""),
            "path": str(jsonld_path.relative_to(ws)),
            "score": score,
            "missing": missing,
            "completeness": completeness,
        })
    return sorted(results, key=lambda x: x["score"])


# ── actors heal ────────────────────────────────────────────────────────────────

def _build_heal_prompt(actor: dict) -> str:
    missing = actor.get("missing", [])
    ctx_parts = [f"nanoid={actor.get('nanoid', '')!r}", f"name={actor.get('name', '')!r}",
                 f"path={actor.get('path', '')!r}"]
    ctx = ", ".join(ctx_parts)
    field_list = ", ".join(f'"{f}"' for f in missing)
    return (
        f"You are a metadata filler for AI actor manifests on the etzhayyim.com platform.\n"
        f"Actor context: {ctx}\n"
        f"Missing fields: {field_list}\n\n"
        f"Generate appropriate values for the missing fields based on the actor's name and path.\n"
        f"Output ONLY a valid JSON object with exactly these keys: {field_list}\n"
        f"Infer values from the actor name/path. For 'performerType' use one of: actor, agent, worker, service.\n"
        f"For 'did' generate a placeholder like did:plc:unknown-{{nanoid}}.\n"
        f"Output only JSON:"
    )


def _call_llm_sync(prompt: str, *, model: str, use_murakumo: bool,
                   murakumo_url: str, murakumo_api_key: str, ollama_base: str) -> str:
    if use_murakumo:
        headers = {"Authorization": f"Bearer {murakumo_api_key}"} if murakumo_api_key else {}
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a metadata generator. Always respond with valid JSON only. No markdown, no explanation."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 512,
            "response_format": {"type": "json_object"},
        }
        resp = httpx.post(f"{murakumo_url}/api/openai/v1/chat/completions",
                          json=body, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    else:
        body = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.3, "num_predict": 512},
        }
        resp = httpx.post(f"{ollama_base}/api/generate", json=body, timeout=60)
        resp.raise_for_status()
        return resp.json()["response"]


def _heal_one(actor: dict, ws: Path, llm_fn: Callable[[str], str],
              dry_run: bool) -> dict:
    result = {"nanoid": actor["nanoid"], "name": actor["name"],
              "path": actor["path"], "fixed_fields": [], "error": ""}
    if not actor.get("missing"):
        return result
    try:
        prompt = _build_heal_prompt(actor)
        raw = llm_fn(prompt)
        m = _RE_JSON_BLOCK.search(raw)
        if not m:
            result["error"] = "no JSON in LLM response"
            return result
        patch = json.loads(m.group(0))
    except Exception as exc:
        result["error"] = str(exc)
        return result

    fixed = [f for f in actor["missing"] if f in patch]
    result["fixed_fields"] = fixed

    if not dry_run and fixed:
        jsonld_path = ws / actor["path"]
        try:
            data = json.loads(jsonld_path.read_text(errors="replace"))
            data.update({f: patch[f] for f in fixed})
            jsonld_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        except (OSError, json.JSONDecodeError) as exc:
            result["error"] = f"write-back failed: {exc}"

    return result


def _run_heal(actors_to_heal: list[dict], ws: Path, llm_fn: Callable[[str], str],
              dry_run: bool, concurrency: int) -> list[dict]:
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(_heal_one, a, ws, llm_fn, dry_run): a
                   for a in actors_to_heal}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


# ── test runner ────────────────────────────────────────────────────────────────

def _detect_and_run_tests(ws: Path) -> list[dict]:
    results = []

    # pytest
    if (ws / "pyproject.toml").exists() or (ws / "setup.py").exists():
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "--tb=short", "-q"],
            capture_output=True, text=True, cwd=ws
        )
        results.append({
            "suite": "pytest",
            "exit_code": r.returncode,
            "output": (r.stdout + r.stderr)[-2000:],
            "passed": r.returncode == 0,
        })

    # cargo test
    if (ws / "Cargo.toml").exists():
        r = subprocess.run(
            ["cargo", "test", "--quiet"],
            capture_output=True, text=True, cwd=ws
        )
        results.append({
            "suite": "cargo test",
            "exit_code": r.returncode,
            "output": (r.stdout + r.stderr)[-2000:],
            "passed": r.returncode == 0,
        })

    # go test
    if any(ws.glob("**/*.go")):
        r = subprocess.run(
            ["go", "test", "./..."],
            capture_output=True, text=True, cwd=ws
        )
        results.append({
            "suite": "go test",
            "exit_code": r.returncode,
            "output": (r.stdout + r.stderr)[-2000:],
            "passed": r.returncode == 0,
        })

    return results


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group("coverage")
def coverage() -> None:
    """Coverage analysis: domain scoring, actor metadata, test suites."""


@coverage.command("domain")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--apps", "show_apps", is_flag=True, default=False)
@click.option("--grade", "filter_grade", default="")
def coverage_domain(workspace_dir: str | None, json_out: bool, show_apps: bool,
                    filter_grade: str) -> None:
    """Domain coverage via kaizen 9-axis scoring (alias of kaizen)."""
    ws = _resolve_root(workspace_dir)
    all_apps = collect_and_score_domain_apps(ws)
    report = build_kaizen_report(all_apps)

    display = list(all_apps)
    if filter_grade:
        display = [a for a in display if a.grade == filter_grade]
    display.sort(key=lambda a: a.domain_score)

    if json_out:
        out = report.to_dict()
        if not show_apps:
            out.pop("apps", None)
        else:
            out["apps"] = [a.to_dict() for a in display]
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        click.echo(f"coverage domain: {report.total_apps} apps  avg={report.avg_domain_score:.1f}")
        click.echo(f"  S={report.grades.get('S',0)} A={report.grades.get('A',0)} "
                   f"B={report.grades.get('B',0)} C={report.grades.get('C',0)} "
                   f"D={report.grades.get('D',0)}")


@coverage.command("actors")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--missing-only", is_flag=True, default=False)
def coverage_actors(workspace_dir: str | None, json_out: bool, missing_only: bool) -> None:
    """Actor metadata completeness scan."""
    ws = _resolve_root(workspace_dir)
    actors = _scan_actors(ws)
    if missing_only:
        actors = [a for a in actors if a["missing"]]
    if json_out:
        click.echo(json.dumps({
            "total": len(actors),
            "actors": actors,
        }, ensure_ascii=False, indent=2))
    else:
        click.echo(f"coverage actors: {len(actors)} actors scanned")
        for a in actors:
            missing_str = ",".join(a["missing"]) if a["missing"] else "ok"
            click.echo(f"  {a['score']:3d}%  {a['nanoid'] or '?':12}  {a['name'] or a['path'][:30]:<30}  {missing_str}")


@coverage.command("heal")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--model", default=os.environ.get("etzhayyim_SHINKA_MODEL", "gemma3:4b"), show_default=True)
@click.option("--murakumo/--no-murakumo", default=True,
              help="Use Murakumo (default). --no-murakumo uses Ollama.")
@click.option("--murakumo-url", default=os.environ.get("etzhayyim_MURAKUMO", _DEFAULT_MURAKUMO), show_default=True)
@click.option("--ollama", "ollama_base", default=os.environ.get("OLLAMA_BASE", _DEFAULT_OLLAMA), show_default=True)
@click.option("--limit", default=20, type=int, show_default=True,
              help="Max actors to heal")
@click.option("--concurrency", default=4, type=int, show_default=True)
def coverage_actors_heal(workspace_dir: str | None, json_out: bool, dry_run: bool,
                         model: str, murakumo: bool, murakumo_url: str, ollama_base: str,
                         limit: int, concurrency: int) -> None:
    """Heal missing actor metadata fields via LLM.

    Scans magatama.jsonld files, calls LLM for actors with missing required
    fields, and writes generated values back to the manifest (unless --dry-run).
    """
    ws = _resolve_root(workspace_dir)
    all_actors = _scan_actors(ws)
    to_heal = [a for a in all_actors if a["missing"]][:limit]

    if not to_heal:
        click.echo("coverage actors heal: no actors with missing required fields")
        return

    api_key = os.environ.get("MURAKUMO_API_KEY", "")

    def llm_fn(prompt: str) -> str:
        return _call_llm_sync(
            prompt, model=model, use_murakumo=murakumo,
            murakumo_url=murakumo_url, murakumo_api_key=api_key, ollama_base=ollama_base,
        )

    click.echo(
        f"[heal] {len(to_heal)} actors to heal"
        + (" (dry-run)" if dry_run else ""),
        err=True,
    )
    results = _run_heal(to_heal, ws, llm_fn, dry_run, concurrency)

    healed = sum(1 for r in results if r["fixed_fields"] and not r["error"])
    if json_out:
        click.echo(json.dumps({
            "healed": healed,
            "dry_run": dry_run,
            "results": results,
        }, ensure_ascii=False, indent=2))
    else:
        click.echo(f"coverage actors heal: {healed}/{len(to_heal)} healed"
                   + (" (dry-run)" if dry_run else ""))
        for r in results:
            status = "OK  " if r["fixed_fields"] and not r["error"] else "FAIL"
            fixed = ",".join(r["fixed_fields"]) or r["error"]
            click.echo(f"  [{status}] {r['nanoid'] or '?':12}  {fixed}")


@coverage.command("governance")
@click.option("--pds", default=None)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def coverage_governance(pds: str | None, workspace_dir: str | None, json_out: bool) -> None:
    """Governance coverage: check operator/authority/visibility fields in actor manifests."""
    ws = _resolve_root(workspace_dir)
    actors = []
    for p in ws.rglob("magatama.jsonld"):
        try:
            data = json.loads(p.read_text(errors="replace"))
        except Exception:
            continue
        if not data.get("nanoid"):
            continue
        issues = []
        for fld in ["operator", "authority", "visibility"]:
            if not data.get(fld):
                issues.append(fld)
        actors.append({
            "nanoid": data.get("nanoid", ""),
            "name": data.get("name", ""),
            "missing_governance": issues,
            "ok": len(issues) == 0,
        })
    total = len(actors)
    ok = sum(1 for a in actors if a["ok"])
    result = {"total": total, "ok": ok, "actors": actors}
    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"governance coverage: {ok}/{total} actors complete")
        for a in actors:
            if not a["ok"]:
                click.echo(f"  MISS  {a['nanoid']}  {a['name']}  missing: {a['missing_governance']}")


_OIL_KEYWORDS = {"oil", "energy", "crude", "barrel", "naphtha", "petroleum", "lng", "refinery"}


@coverage.command("oil")
@click.option("--pds", default=None)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def coverage_oil(pds: str | None, workspace_dir: str | None, json_out: bool) -> None:
    """Oil/energy domain coverage analysis."""
    ws = _resolve_root(workspace_dir)
    oil_actors = []
    for p in ws.rglob("magatama.jsonld"):
        try:
            data = json.loads(p.read_text(errors="replace"))
        except Exception:
            continue
        name = (data.get("name", "") + data.get("description", "")).lower()
        if any(k in name for k in _OIL_KEYWORDS):
            oil_actors.append({
                "nanoid": data.get("nanoid", ""),
                "name": data.get("name", ""),
                "description": data.get("description", "")[:80],
            })
    result = {"oil_actors": len(oil_actors), "actors": oil_actors}
    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"oil/energy coverage: {len(oil_actors)} actors")
        for a in oil_actors:
            click.echo(f"  {a['nanoid']}  {a['name']}")


@coverage.command("world")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--domain", default="", help="filter by domain")
@click.option("--top", default=30, type=int)
@click.option("--offline", is_flag=True, default=False)
def coverage_world(pds: str | None, json_out: bool, domain: str, top: int, offline: bool) -> None:
    """World coverage (403 domains) — requires Go binary for Hyperdrive direct query."""
    import sys
    click.echo(
        "coverage world requires direct RisingWave access. Use: etzhayyim coverage world",
        err=True,
    )
    sys.exit(1)


@coverage.command("infer")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--method", default="gmm", type=click.Choice(["gmm", "kmeans"]))
@click.option("--k", default=0, type=int, help="number of clusters (0=auto)")
def coverage_infer(pds: str | None, json_out: bool, method: str, k: int) -> None:
    """Statistical entity resolution / cluster inference — requires Go binary (pgxpool)."""
    import sys
    click.echo(
        "coverage infer requires direct RisingWave access. Use: etzhayyim coverage infer",
        err=True,
    )
    sys.exit(1)


@coverage.command("hospitality")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--domain", default="kaigo", help="hospitality sub-domain")
def coverage_hospitality(pds: str | None, json_out: bool, domain: str) -> None:
    """Hospitality domain coverage — requires Go binary (pgxpool)."""
    import sys
    click.echo(
        "coverage hospitality requires direct RisingWave access. Use: etzhayyim coverage hospitality",
        err=True,
    )
    sys.exit(1)


@coverage.command("test")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def coverage_test(workspace_dir: str | None, json_out: bool) -> None:
    """Run local test suites and report results."""
    ws = _resolve_root(workspace_dir)
    results = _detect_and_run_tests(ws)
    if not results:
        click.echo("no test suites detected")
        sys.exit(0)
    all_pass = all(r["passed"] for r in results)
    if json_out:
        click.echo(json.dumps({"passed": all_pass, "suites": results}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            click.echo(f"  [{status}] {r['suite']}")
            if not r["passed"]:
                click.echo(r["output"])
    if not all_pass:
        sys.exit(1)
