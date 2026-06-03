"""kosei (構成) — Structural compliance analysis.

Checks that apps conform to required file conventions and naming rules.
Ported from the kaizen/shannon structural checks.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import click

from .shannon import _resolve_root


# ── required structure rules ───────────────────────────────────────────────────

_REQUIRED_FILES = ["magatama.jsonld", "src/app.ts", "wrangler.jsonc"]
_RE_NANOID = re.compile(r'^[A-Za-z0-9_-]{8,12}$')
_RE_APP_DIR = re.compile(r'^etzhayyim-wasm-.+-[A-Za-z0-9]{8}$')
_RE_PROJECT_DIR = re.compile(r'^etzhayyim-project-.+$')
_RE_NSID_HARDCODE = re.compile(r'"nsid"')
_RE_CORS = re.compile(r'Access-Control-Allow-Origin:\s*\*')
_RE_PDS_HARDCODE = re.compile(r'https://pds\.etzhayyim\.ai')
_RE_MODEL_HARDCODE = re.compile(
    r'"(?:claude-3|gpt-4|gemini-|llama-|qwen)[^"]*"', re.IGNORECASE
)

_SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build"}


@dataclass
class KoseiViolation:
    rule: str
    severity: str  # error / warning
    path: str
    detail: str = ""

    def to_dict(self) -> dict:
        return {"rule": self.rule, "severity": self.severity,
                "path": self.path, "detail": self.detail}


@dataclass
class KoseiAppResult:
    app_dir: str
    missing_files: list[str] = field(default_factory=list)
    violations: list[KoseiViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing_files and not any(
            v.severity == "error" for v in self.violations
        )

    def to_dict(self) -> dict:
        return {
            "app_dir": self.app_dir,
            "ok": self.ok,
            "missing_files": self.missing_files,
            "violations": [v.to_dict() for v in self.violations],
        }


@dataclass
class KoseiReport:
    evaluated_at: str
    total_apps: int
    ok_apps: int
    results: list[KoseiAppResult]
    global_violations: list[KoseiViolation] = field(default_factory=list)

    @property
    def compliance_pct(self) -> float:
        return (self.ok_apps / max(self.total_apps, 1)) * 100

    def to_dict(self) -> dict:
        return {
            "evaluated_at": self.evaluated_at,
            "total_apps": self.total_apps,
            "ok_apps": self.ok_apps,
            "compliance_pct": round(self.compliance_pct, 1),
            "results": [r.to_dict() for r in self.results],
            "global_violations": [v.to_dict() for v in self.global_violations],
        }


# ── scanner ────────────────────────────────────────────────────────────────────

def _check_app(app_dir: Path, ws: Path) -> KoseiAppResult:
    rel = str(app_dir.relative_to(ws))
    result = KoseiAppResult(app_dir=rel)

    for req in _REQUIRED_FILES:
        if not (app_dir / req).exists():
            result.missing_files.append(req)

    # Check wrangler.jsonc content
    wrangler = app_dir / "wrangler.jsonc"
    if wrangler.exists():
        try:
            content = wrangler.read_text(errors="replace")
            if _RE_CORS.search(content):
                result.violations.append(KoseiViolation(
                    rule="no-wildcard-cors", severity="error",
                    path=str(wrangler.relative_to(ws)), detail="wildcard CORS in wrangler.jsonc",
                ))
            if _RE_PDS_HARDCODE.search(content):
                result.violations.append(KoseiViolation(
                    rule="no-pds-hardcode", severity="warning",
                    path=str(wrangler.relative_to(ws)), detail="hardcoded PDS URL",
                ))
        except OSError:
            pass

    # Check app.ts content
    app_ts = app_dir / "src" / "app.ts"
    if app_ts.exists():
        try:
            content = app_ts.read_text(errors="replace")
            if _RE_NSID_HARDCODE.search(content):
                result.violations.append(KoseiViolation(
                    rule="no-nsid-placeholder", severity="error",
                    path=str(app_ts.relative_to(ws)), detail='"nsid" placeholder found',
                ))
            if _RE_MODEL_HARDCODE.search(content):
                result.violations.append(KoseiViolation(
                    rule="no-model-hardcode", severity="warning",
                    path=str(app_ts.relative_to(ws)),
                    detail="LLM model name hardcoded (use resolveModelId())",
                ))
        except OSError:
            pass

    # App dir naming convention
    if not _RE_APP_DIR.match(app_dir.name):
        result.violations.append(KoseiViolation(
            rule="app-dir-naming", severity="warning",
            path=rel, detail=f"dir '{app_dir.name}' should match etzhayyim-wasm-<name>-<nanoid8>",
        ))

    return result


def scan_kosei(ws: Path) -> KoseiReport:
    projects_dir = ws / "60-apps"
    if not projects_dir.exists():
        projects_dir = ws / "projects"

    results: list[KoseiAppResult] = []
    if projects_dir.exists():
        for jsonld in projects_dir.rglob("magatama.jsonld"):
            app_dir = jsonld.parent
            results.append(_check_app(app_dir, ws))

    ok = sum(1 for r in results if r.ok)
    return KoseiReport(
        evaluated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        total_apps=len(results),
        ok_apps=ok,
        results=results,
    )


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group("kosei", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def kosei(ctx: click.Context, workspace_dir: str | None, json_out: bool) -> None:
    """Structural compliance analysis (file conventions, naming, guardrails)."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    report = scan_kosei(ws)
    if json_out:
        click.echo(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        click.echo(f"kosei (構成): {report.ok_apps}/{report.total_apps} apps OK  "
                   f"({report.compliance_pct:.0f}% compliant)")
        for r in report.results:
            if not r.ok:
                issues = r.missing_files + [v.rule for v in r.violations if v.severity == "error"]
                click.echo(f"  FAIL  {r.app_dir}  [{', '.join(issues[:3])}]")


@kosei.command("scan")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--errors-only", is_flag=True, default=False)
def kosei_scan(workspace_dir: str | None, json_out: bool, errors_only: bool) -> None:
    """Full structural compliance scan."""
    ws = _resolve_root(workspace_dir)
    report = scan_kosei(ws)
    results = report.results
    if errors_only:
        results = [r for r in results if not r.ok]
    if json_out:
        click.echo(json.dumps({
            "compliance_pct": report.compliance_pct,
            "apps": [r.to_dict() for r in results],
        }, ensure_ascii=False, indent=2))
    else:
        for r in results:
            status = "OK  " if r.ok else "FAIL"
            click.echo(f"  [{status}] {r.app_dir}")
            for f in r.missing_files:
                click.echo(f"         missing: {f}")
            for v in r.violations:
                click.echo(f"         [{v.severity}] {v.rule}: {v.detail}")


@kosei.command("check")
@click.argument("rule")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def kosei_check(rule: str, workspace_dir: str | None, json_out: bool) -> None:
    """Check a specific rule across all apps."""
    ws = _resolve_root(workspace_dir)
    report = scan_kosei(ws)
    violations = [
        v for r in report.results
        for v in r.violations if v.rule == rule
    ]
    if json_out:
        click.echo(json.dumps([v.to_dict() for v in violations], ensure_ascii=False, indent=2))
    else:
        if not violations:
            click.echo(f"  rule '{rule}': no violations")
        for v in violations:
            click.echo(f"  [{v.severity}] {v.path}: {v.detail}")


# ── tier management helpers ────────────────────────────────────────────────────

import subprocess
import tempfile
import webbrowser

_TIER_ETA = {"T1": 0.667, "T2": 0.500, "T3": 0.910}
_DEFAULT_TIER = "T2"
_TIER_ORDER = ["T1", "T2", "T3"]


def _kosei_data_dir(data_dir: str | None, ws: Path) -> Path:
    if data_dir:
        return Path(data_dir)
    return ws / "80-data" / "kosei"


def _load_kosei_config(data_dir: Path) -> dict:
    cfg_path = data_dir / "config.json"
    if cfg_path.exists():
        return json.loads(cfg_path.read_text(errors="replace"))
    return {"format_version": 1, "updated_at": "", "apps": {}}


def _save_kosei_config(data_dir: Path, cfg: dict) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    cfg["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (data_dir / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2))


def _discover_apps_meta(ws: Path) -> list[dict]:
    apps = []
    for p in ws.rglob("magatama.jsonld"):
        try:
            data = json.loads(p.read_text(errors="replace"))
        except Exception:
            continue
        if data.get("nanoid"):
            apps.append({
                "nanoid": data.get("nanoid", ""),
                "name": data.get("name", ""),
                "did": data.get("did", ""),
                "performerType": data.get("performerType", ""),
                "guestLanguage": data.get("guestLanguage", ""),
                "dir": str(p.parent.relative_to(ws)),
                "path": str(p.parent),
            })
    return apps


def _suggest_tier(meta: dict) -> str:
    name = (meta.get("name", "") + " " + meta.get("dir", "")).lower()
    pt = meta.get("performerType", "").lower()
    infra_kws = ("infra", "gateway", "auth", "pds", "graph", "router", "proxy", "platform")
    if any(k in name for k in infra_kws) or pt == "system" or "50-infra" in meta.get("dir", ""):
        return "T3"
    if "20-actors" in meta.get("dir", "") or "magatama" in name or pt == "actor":
        return "T1"
    return "T2"


def _record_change(data_dir: Path, nanoid: str, old_tier: str | None, new_tier: str, reason: str) -> None:
    history_dir = data_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    changes_file = history_dir / "changes.jsonl"
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "nanoid": nanoid,
        "old_tier": old_tier,
        "new_tier": new_tier,
        "reason": reason,
    }
    with changes_file.open("a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── kosei list ─────────────────────────────────────────────────────────────────

@kosei.command("list")
@click.option("--tier", default=None, type=click.Choice(["T1", "T2", "T3"]))
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_list(tier: str | None, json_out: bool, workspace_dir: str | None, data_dir: str | None) -> None:
    """List all apps with tier assignments."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps_cfg = cfg.get("apps", {})
    metas = _discover_apps_meta(ws)

    rows = []
    for m in metas:
        nid = m["nanoid"]
        entry = apps_cfg.get(nid, {})
        t = entry.get("tier", "")
        if tier and t != tier:
            continue
        rows.append({
            "nanoid": nid,
            "name": m["name"],
            "tier": t or "—",
            "eta": _TIER_ETA.get(t, 0.0) if t else 0.0,
            "assigned_by": entry.get("assigned_by", "—"),
            "notes": entry.get("notes", ""),
        })

    rows.sort(key=lambda r: (r["tier"], r["name"]))

    if json_out:
        click.echo(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        click.echo(f"{'nanoid':<14} {'name':<36} {'tier':<5} {'η':<7} {'assigned_by':<12} notes")
        click.echo("-" * 90)
        for r in rows:
            eta_s = f"{r['eta']:.3f}" if r["eta"] else "—    "
            click.echo(f"{r['nanoid']:<14} {r['name']:<36} {r['tier']:<5} {eta_s:<7} {r['assigned_by']:<12} {r['notes']}")


# ── kosei show ─────────────────────────────────────────────────────────────────

@kosei.command("show")
@click.argument("nanoid")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_show(nanoid: str, json_out: bool, workspace_dir: str | None, data_dir: str | None) -> None:
    """Show detailed config for one app."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    entry = cfg.get("apps", {}).get(nanoid, {})

    metas = _discover_apps_meta(ws)
    meta = next((m for m in metas if m["nanoid"] == nanoid), {})

    tier = entry.get("tier", "")
    result = {
        "nanoid": nanoid,
        "name": meta.get("name", ""),
        "dir": meta.get("dir", ""),
        "performerType": meta.get("performerType", ""),
        "tier": tier or "—",
        "eta": _TIER_ETA.get(tier, 0.0) if tier else 0.0,
        "assigned_at": entry.get("assigned_at", ""),
        "assigned_by": entry.get("assigned_by", ""),
        "notes": entry.get("notes", ""),
    }

    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for k, v in result.items():
            click.echo(f"  {k:<16} {v}")


# ── kosei set ──────────────────────────────────────────────────────────────────

@kosei.command("set")
@click.argument("nanoid")
@click.option("--tier", required=True, type=click.Choice(["T1", "T2", "T3"]))
@click.option("--reason", default="", help="Reason for this assignment.")
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_set(nanoid: str, tier: str, reason: str, workspace_dir: str | None, data_dir: str | None) -> None:
    """Set tier explicitly for an app."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps = cfg.setdefault("apps", {})
    old_tier = apps.get(nanoid, {}).get("tier")
    apps[nanoid] = {
        "tier": tier,
        "notes": reason,
        "assigned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "assigned_by": "manual",
    }
    _save_kosei_config(dd, cfg)
    _record_change(dd, nanoid, old_tier, tier, reason)
    click.echo(f"kosei set: {nanoid}  {old_tier or '—'} → {tier}  η={_TIER_ETA[tier]:.3f}")


# ── kosei promote ──────────────────────────────────────────────────────────────

@kosei.command("promote")
@click.argument("nanoid")
@click.option("--reason", default="", help="Reason for promotion.")
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_promote(nanoid: str, reason: str, workspace_dir: str | None, data_dir: str | None) -> None:
    """Promote app tier: T1→T2→T3."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps = cfg.setdefault("apps", {})
    current = apps.get(nanoid, {}).get("tier", _DEFAULT_TIER)
    idx = _TIER_ORDER.index(current) if current in _TIER_ORDER else 1
    if idx >= len(_TIER_ORDER) - 1:
        click.echo(f"kosei promote: {nanoid} already at {current} (max tier)", err=True)
        raise SystemExit(1)
    new_tier = _TIER_ORDER[idx + 1]
    apps[nanoid] = {
        "tier": new_tier,
        "notes": reason,
        "assigned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "assigned_by": "manual",
    }
    _save_kosei_config(dd, cfg)
    _record_change(dd, nanoid, current, new_tier, reason)
    click.echo(f"kosei promote: {nanoid}  {current} → {new_tier}  η={_TIER_ETA[new_tier]:.3f}")


# ── kosei demote ───────────────────────────────────────────────────────────────

@kosei.command("demote")
@click.argument("nanoid")
@click.option("--reason", default="", help="Reason for demotion.")
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_demote(nanoid: str, reason: str, workspace_dir: str | None, data_dir: str | None) -> None:
    """Demote app tier: T3→T2→T1."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps = cfg.setdefault("apps", {})
    current = apps.get(nanoid, {}).get("tier", _DEFAULT_TIER)
    idx = _TIER_ORDER.index(current) if current in _TIER_ORDER else 1
    if idx <= 0:
        click.echo(f"kosei demote: {nanoid} already at {current} (min tier)", err=True)
        raise SystemExit(1)
    new_tier = _TIER_ORDER[idx - 1]
    apps[nanoid] = {
        "tier": new_tier,
        "notes": reason,
        "assigned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "assigned_by": "manual",
    }
    _save_kosei_config(dd, cfg)
    _record_change(dd, nanoid, current, new_tier, reason)
    click.echo(f"kosei demote: {nanoid}  {current} → {new_tier}  η={_TIER_ETA[new_tier]:.3f}")


# ── kosei suggest ──────────────────────────────────────────────────────────────

@kosei.command("suggest")
@click.option("--apply", is_flag=True, default=False, help="Save suggestions to config.json.")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_suggest(apply: bool, json_out: bool, workspace_dir: str | None, data_dir: str | None) -> None:
    """Auto-suggest tiers via heuristics."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps = cfg.setdefault("apps", {})
    metas = _discover_apps_meta(ws)

    suggestions = []
    for m in metas:
        nid = m["nanoid"]
        suggested = _suggest_tier(m)
        current = apps.get(nid, {}).get("tier", "")
        suggestions.append({
            "nanoid": nid,
            "name": m["name"],
            "current_tier": current or "—",
            "suggested_tier": suggested,
            "changed": current != suggested,
        })

    if apply:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for s in suggestions:
            if s["changed"]:
                nid = s["nanoid"]
                apps[nid] = {
                    "tier": s["suggested_tier"],
                    "notes": "auto-suggested",
                    "assigned_at": now,
                    "assigned_by": "auto",
                }
        _save_kosei_config(dd, cfg)

    if json_out:
        click.echo(json.dumps(suggestions, ensure_ascii=False, indent=2))
    else:
        changed = [s for s in suggestions if s["changed"]]
        click.echo(f"kosei suggest: {len(suggestions)} apps  {len(changed)} changes" +
                   ("  (applied)" if apply else "  (dry-run, use --apply to save)"))
        click.echo(f"{'nanoid':<14} {'name':<36} {'current':<9} {'suggested':<9}")
        click.echo("-" * 72)
        for s in suggestions:
            marker = "*" if s["changed"] else " "
            click.echo(f"{marker} {s['nanoid']:<13} {s['name']:<36} {s['current_tier']:<9} {s['suggested_tier']:<9}")


# ── kosei diff ─────────────────────────────────────────────────────────────────

@kosei.command("diff")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_diff(json_out: bool, workspace_dir: str | None, data_dir: str | None) -> None:
    """Compare config.json vs apps on disk."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps_cfg = cfg.get("apps", {})
    metas = _discover_apps_meta(ws)

    disk_ids = {m["nanoid"]: m for m in metas}
    cfg_ids = set(apps_cfg.keys())

    unassigned = [m for m in metas if m["nanoid"] not in cfg_ids]
    missing = [{"nanoid": nid, **apps_cfg[nid]} for nid in cfg_ids if nid not in disk_ids]

    result = {
        "unassigned": [{"nanoid": m["nanoid"], "name": m["name"], "dir": m["dir"]} for m in unassigned],
        "missing_on_disk": missing,
        "unassigned_count": len(unassigned),
        "missing_count": len(missing),
    }

    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"kosei diff: {len(unassigned)} unassigned  {len(missing)} missing on disk")
        if unassigned:
            click.echo("\nunassigned (on disk, not in config):")
            for m in unassigned:
                click.echo(f"  + {m['nanoid']:<14} {m['name']:<36} {m['dir']}")
        if missing:
            click.echo("\nmissing on disk (in config, not found):")
            for m in missing:
                click.echo(f"  - {m['nanoid']:<14} tier={m.get('tier','?')}")


# ── kosei stats ────────────────────────────────────────────────────────────────

@kosei.command("stats")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_stats(json_out: bool, workspace_dir: str | None, data_dir: str | None) -> None:
    """Tier distribution and system η."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps_cfg = cfg.get("apps", {})
    metas = _discover_apps_meta(ws)

    counts: dict[str, int] = {"T1": 0, "T2": 0, "T3": 0, "unassigned": 0}
    eta_sum = 0.0
    assigned_count = 0

    for m in metas:
        nid = m["nanoid"]
        tier = apps_cfg.get(nid, {}).get("tier", "")
        if tier in _TIER_ETA:
            counts[tier] += 1
            eta_sum += _TIER_ETA[tier]
            assigned_count += 1
        else:
            counts["unassigned"] += 1

    total = len(metas)
    system_eta = eta_sum / assigned_count if assigned_count else 0.0

    result = {
        "total": total,
        "assigned": assigned_count,
        "unassigned": counts["unassigned"],
        "T1": counts["T1"],
        "T2": counts["T2"],
        "T3": counts["T3"],
        "system_eta": round(system_eta, 4),
    }

    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"kosei stats: {total} apps  system η={system_eta:.4f}")
        click.echo(f"  T1 (η=0.667): {counts['T1']:4d}  ({counts['T1']/max(total,1)*100:.1f}%)")
        click.echo(f"  T2 (η=0.500): {counts['T2']:4d}  ({counts['T2']/max(total,1)*100:.1f}%)")
        click.echo(f"  T3 (η=0.910): {counts['T3']:4d}  ({counts['T3']/max(total,1)*100:.1f}%)")
        click.echo(f"  unassigned:   {counts['unassigned']:4d}  ({counts['unassigned']/max(total,1)*100:.1f}%)")


# ── kosei summary ──────────────────────────────────────────────────────────────

@kosei.command("summary")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_summary(json_out: bool, workspace_dir: str | None, data_dir: str | None) -> None:
    """Brief one-liner summary table per tier."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps_cfg = cfg.get("apps", {})
    metas = _discover_apps_meta(ws)

    by_tier: dict[str, list[str]] = {"T1": [], "T2": [], "T3": [], "unassigned": []}
    for m in metas:
        tier = apps_cfg.get(m["nanoid"], {}).get("tier", "")
        key = tier if tier in by_tier else "unassigned"
        by_tier[key].append(m["name"] or m["nanoid"])

    rows = [
        {"tier": "T1", "description": "Mitama Shared Executor", "eta": 0.667, "count": len(by_tier["T1"])},
        {"tier": "T2", "description": "App Worker",             "eta": 0.500, "count": len(by_tier["T2"])},
        {"tier": "T3", "description": "Infra Worker",           "eta": 0.910, "count": len(by_tier["T3"])},
        {"tier": "—",  "description": "Unassigned",             "eta": 0.0,   "count": len(by_tier["unassigned"])},
    ]

    if json_out:
        click.echo(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        click.echo(f"{'tier':<5} {'η':<7} {'count':<7} description")
        click.echo("-" * 48)
        for r in rows:
            eta_s = f"{r['eta']:.3f}" if r["eta"] else "—    "
            click.echo(f"{r['tier']:<5} {eta_s:<7} {r['count']:<7} {r['description']}")


# ── kosei snapshot ─────────────────────────────────────────────────────────────

@kosei.command("snapshot")
@click.option("--data-dir", default=None)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def kosei_snapshot(data_dir: str | None, workspace_dir: str | None, json_out: bool) -> None:
    """Write current tier config to Parquet snapshot via duckdb."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps_cfg = cfg.get("apps", {})
    metas = _discover_apps_meta(ws)

    snap_ts = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    snap_dir = dd / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    parquet_name = f"kosei_{snap_ts}.parquet"
    parquet_path = snap_dir / parquet_name

    rows = []
    for m in metas:
        nid = m["nanoid"]
        entry = apps_cfg.get(nid, {})
        tier = entry.get("tier", "")
        rows.append({
            "nanoid": nid,
            "name": m["name"],
            "performerType": m["performerType"],
            "dir": m["dir"],
            "tier": tier,
            "eta": _TIER_ETA.get(tier, 0.0) if tier else 0.0,
            "assigned_at": entry.get("assigned_at", ""),
            "assigned_by": entry.get("assigned_by", ""),
            "notes": entry.get("notes", ""),
            "snapshot_ts": snap_ts,
        })

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        json.dump(rows, tf, ensure_ascii=False)
        tmp_json = tf.name

    sql = (
        f"COPY (SELECT * FROM read_json_auto('{tmp_json}')) "
        f"TO '{parquet_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    r = subprocess.run(["duckdb", "-c", sql], capture_output=True, text=True)
    Path(tmp_json).unlink(missing_ok=True)

    if r.returncode != 0:
        click.echo(f"duckdb error: {r.stderr.strip()}", err=True)
        raise SystemExit(1)

    result = {"snapshot_ts": snap_ts, "parquet": str(parquet_path), "rows": len(rows)}
    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"kosei snapshot: {snap_ts}  {len(rows)} apps  → {parquet_path}")


# ── kosei query ────────────────────────────────────────────────────────────────

@kosei.command("query")
@click.argument("sql")
@click.option("--data-dir", default=None)
@click.option("--workspace-dir", default=None)
def kosei_query(sql: str, data_dir: str | None, workspace_dir: str | None) -> None:
    """Query Parquet snapshots via duckdb. Use $TABLE for the parquet glob."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    parquet_glob = str(dd / "snapshots" / "*.parquet")
    table_expr = f"read_parquet('{parquet_glob}')"
    resolved = sql.replace("$TABLE", table_expr)
    r = subprocess.run(["duckdb", "-c", resolved], capture_output=True, text=True)
    if r.returncode != 0:
        click.echo(f"duckdb error: {r.stderr.strip()}", err=True)
        raise SystemExit(1)
    click.echo(r.stdout, nl=False)


# ── kosei history ──────────────────────────────────────────────────────────────

@kosei.command("history")
@click.option("--limit", default=20, show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--data-dir", default=None)
def kosei_history(limit: int, json_out: bool, data_dir: str | None) -> None:
    """Show change history."""
    dd = Path(data_dir) if data_dir else None
    if dd is None:
        click.echo("kosei history: --data-dir required", err=True)
        raise SystemExit(1)

    parquet_path = dd / "history" / "changes.parquet"
    jsonl_path = dd / "history" / "changes.jsonl"

    if parquet_path.exists():
        sql = (
            f"SELECT * FROM read_parquet('{parquet_path}') "
            f"ORDER BY ts DESC LIMIT {limit}"
        )
        r = subprocess.run(["duckdb", "-c", sql], capture_output=True, text=True)
        if r.returncode == 0:
            click.echo(r.stdout, nl=False)
            return
        click.echo(f"duckdb error: {r.stderr.strip()}", err=True)

    if jsonl_path.exists():
        lines = jsonl_path.read_text(errors="replace").strip().splitlines()
        entries = []
        for line in lines:
            try:
                entries.append(json.loads(line))
            except Exception:
                continue
        entries = list(reversed(entries[-limit:]))
        if json_out:
            click.echo(json.dumps(entries, ensure_ascii=False, indent=2))
        else:
            click.echo(f"kosei history: {len(entries)} entries (from jsonl)")
            for e in entries:
                click.echo(f"  {e.get('ts','')}  {e.get('nanoid',''):<14}  "
                           f"{e.get('old_tier','—')} → {e.get('new_tier','?')}  {e.get('reason','')}")
        return

    click.echo("kosei history: no history found (run kosei set/promote/demote first)")


# ── kosei matrix ───────────────────────────────────────────────────────────────

@kosei.command("matrix")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_matrix(json_out: bool, workspace_dir: str | None, data_dir: str | None) -> None:
    """Technology stack matrix per tier."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps_cfg = cfg.get("apps", {})
    metas = _discover_apps_meta(ws)

    by_tier: dict[str, list[dict]] = {"T1": [], "T2": [], "T3": [], "unassigned": []}
    for m in metas:
        tier = apps_cfg.get(m["nanoid"], {}).get("tier", "")
        key = tier if tier in by_tier else "unassigned"
        by_tier[key].append({
            "nanoid": m["nanoid"],
            "name": m["name"],
            "performerType": m["performerType"],
            "guestLanguage": m["guestLanguage"],
        })

    result = {t: by_tier[t] for t in ("T1", "T2", "T3", "unassigned")}

    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for tier in ("T1", "T2", "T3", "unassigned"):
            items = by_tier[tier]
            if not items:
                continue
            eta = _TIER_ETA.get(tier, 0.0)
            eta_s = f"η={eta:.3f}" if eta else ""
            click.echo(f"\n[{tier}] {eta_s}  ({len(items)} apps)")
            click.echo(f"  {'nanoid':<14} {'name':<32} {'performerType':<14} guestLanguage")
            for item in items:
                click.echo(f"  {item['nanoid']:<14} {item['name']:<32} "
                           f"{item['performerType']:<14} {item['guestLanguage']}")


# ── kosei sbom ─────────────────────────────────────────────────────────────────

@kosei.command("sbom")
@click.argument("nanoid")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_sbom(nanoid: str, json_out: bool, workspace_dir: str | None, data_dir: str | None) -> None:
    """SBOM: list CF bindings, npm deps, WIT imports, and tier for one app."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    entry = cfg.get("apps", {}).get(nanoid, {})

    metas = _discover_apps_meta(ws)
    meta = next((m for m in metas if m["nanoid"] == nanoid), None)
    if meta is None:
        click.echo(f"kosei sbom: nanoid '{nanoid}' not found", err=True)
        raise SystemExit(1)

    app_dir = Path(meta["path"])

    cf_bindings: list[str] = []
    wrangler_path = app_dir / "wrangler.jsonc"
    if wrangler_path.exists():
        try:
            import re as _re
            raw = wrangler_path.read_text(errors="replace")
            raw_stripped = _re.sub(r'//[^\n]*', '', raw)
            raw_stripped = _re.sub(r'/\*.*?\*/', '', raw_stripped, flags=_re.DOTALL)
            wdata = json.loads(raw_stripped)
            for key in ("kv_namespaces", "r2_buckets", "d1_databases", "durable_objects",
                        "hyperdrive", "queues", "vectorize", "ai", "services"):
                val = wdata.get(key)
                if val:
                    if isinstance(val, list):
                        cf_bindings.extend(f"{key}:{v.get('binding', v.get('name', '?'))}" for v in val)
                    elif isinstance(val, dict):
                        cf_bindings.append(key)
        except Exception:
            pass

    npm_deps: list[str] = []
    pkg_path = app_dir / "package.json"
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text(errors="replace"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            npm_deps = [f"{k}@{v}" for k, v in sorted(deps.items())]
        except Exception:
            pass

    wit_imports: list[str] = []
    jsonld_path = app_dir / "magatama.jsonld"
    if jsonld_path.exists():
        try:
            jdata = json.loads(jsonld_path.read_text(errors="replace"))
            wit_imports = jdata.get("witImports", jdata.get("imports", []))
        except Exception:
            pass

    tier = entry.get("tier", "")
    result = {
        "nanoid": nanoid,
        "name": meta["name"],
        "dir": meta["dir"],
        "tier": tier or "—",
        "eta": _TIER_ETA.get(tier, 0.0) if tier else 0.0,
        "performerType": meta["performerType"],
        "guestLanguage": meta["guestLanguage"],
        "cf_bindings": cf_bindings,
        "npm_deps": npm_deps,
        "wit_imports": wit_imports,
    }

    if json_out:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        click.echo(f"sbom: {nanoid}  {meta['name']}  tier={tier or '—'}  η={result['eta']:.3f}")
        click.echo(f"  dir:          {meta['dir']}")
        click.echo(f"  performerType: {meta['performerType']}")
        click.echo(f"  guestLanguage: {meta['guestLanguage']}")
        click.echo(f"  CF bindings ({len(cf_bindings)}):")
        for b in cf_bindings:
            click.echo(f"    {b}")
        click.echo(f"  WIT imports ({len(wit_imports)}):")
        for w in wit_imports:
            click.echo(f"    {w}")
        click.echo(f"  npm deps ({len(npm_deps)}):")
        for d in npm_deps[:20]:
            click.echo(f"    {d}")
        if len(npm_deps) > 20:
            click.echo(f"    ... and {len(npm_deps) - 20} more")


# ── kosei stack ────────────────────────────────────────────────────────────────

def _scan_app_stack(app_dir: Path) -> dict:
    """Scan an app directory and return a tech-stack profile dict."""
    import re as _re

    result: dict = {
        "language": "typescript", "framework": "ts-native", "guest_language": "",
        "has_assets": False, "has_workers_ai": False, "has_browser": False,
        "has_pds_rpc": False, "has_graph_sql": False,
        "r2_count": 0, "service_count": 0, "secret_count": 0, "cf_bindings": [],
        "content_mode": "", "has_subscribe": False, "coll_count": 0,
        "has_evolver": False, "has_space": False, "has_game": False,
        "has_desktop": False, "has_signal": False, "has_convo_prompt": False,
        "has_wit": False, "requires_count": 0, "provides_count": 0,
        "has_rw": False, "has_yata": False,
        "has_webgpu": False, "has_onnx": False, "has_fido2": False,
        "has_wasm": False, "has_mcp": False, "has_bpmn": False,
        "npm_deps": [], "cargo_crates": [], "wit_imports": [],
    }

    # wrangler.jsonc
    wrangler = app_dir / "wrangler.jsonc"
    if wrangler.exists():
        try:
            raw = wrangler.read_text(errors="replace")
            raw = _re.sub(r'//[^\n]*', '', raw)
            raw = _re.sub(r'/\*.*?\*/', '', raw, flags=_re.DOTALL)
            wd = json.loads(raw)
            bindings: list[str] = []
            for key in ("kv_namespaces", "r2_buckets", "d1_databases", "durable_objects",
                        "hyperdrive", "queues", "vectorize", "ai", "services",
                        "browser", "assets", "secrets_store"):
                val = wd.get(key)
                if val:
                    if isinstance(val, list):
                        for v in val:
                            b = v.get("binding") or v.get("name", key)
                            bindings.append(b)
                            if key == "r2_buckets":
                                result["r2_count"] += 1
                            if key == "services":
                                result["service_count"] += 1
                            if key == "secrets_store":
                                result["secret_count"] += 1
                    else:
                        bindings.append(key)
                    if key == "ai":
                        result["has_workers_ai"] = True
                    if key == "browser":
                        result["has_browser"] = True
                    if key == "assets":
                        result["has_assets"] = True
            result["cf_bindings"] = bindings
            if wd.get("pds_rpc") or "PDS_RPC" in bindings:
                result["has_pds_rpc"] = True
        except Exception:
            pass

    # magatama.jsonld
    jsonld = app_dir / "magatama.jsonld"
    if jsonld.exists():
        try:
            jd = json.loads(jsonld.read_text(errors="replace"))
            result["guest_language"] = jd.get("build", {}).get("guestLanguage", "")
            result["content_mode"] = jd.get("contentMode", "")
            result["has_subscribe"] = bool(jd.get("subscribeRepos"))
            result["coll_count"] = len(jd.get("subscribeRepos", {}).get("collections", []))
            result["has_evolver"] = bool(jd.get("evolver"))
            result["has_space"] = bool(jd.get("space"))
            result["has_game"] = bool(jd.get("game"))
            result["has_desktop"] = bool(jd.get("desktop"))
            result["has_signal"] = bool(jd.get("signal"))
            result["has_convo_prompt"] = bool(jd.get("convoSystemPrompt"))
            result["has_bpmn"] = bool(jd.get("pipeline") or jd.get("bpmn"))
            ifaces = jd.get("interfaces", {})
            result["requires_count"] = len(ifaces.get("requires", []))
            result["provides_count"] = len(ifaces.get("provides", []))
            result["wit_imports"] = jd.get("witImports", jd.get("imports", []))
        except Exception:
            pass

    # WIT contract
    if (app_dir / "wit" / "world.wit").exists():
        result["has_wit"] = True

    # package.json
    pkg = app_dir / "package.json"
    if pkg.exists():
        try:
            pd = json.loads(pkg.read_text(errors="replace"))
            all_deps = {**pd.get("dependencies", {}), **pd.get("devDependencies", {})}
            result["npm_deps"] = [f"{k}@{v}" for k, v in sorted(all_deps.items())]
            dep_str = " ".join(all_deps.keys()).lower()
            if "onnx" in dep_str:
                result["has_onnx"] = True
            if "webgpu" in dep_str or "wgpu" in dep_str:
                result["has_webgpu"] = True
            if "fido" in dep_str or "webauthn" in dep_str:
                result["has_fido2"] = True
            if "@modelcontextprotocol" in dep_str or "mcp-server" in dep_str:
                result["has_mcp"] = True
            if "wasm" in dep_str:
                result["has_wasm"] = True
        except Exception:
            pass

    # Cargo.toml
    cargo = app_dir / "Cargo.toml"
    if cargo.exists():
        result["language"] = "rust"
        try:
            import tomllib as _tl
            cd = _tl.loads(cargo.read_text(errors="replace"))
            crates = list(cd.get("dependencies", {}).keys())
            result["cargo_crates"] = crates
            joined = " ".join(crates).lower()
            if "wgpu" in joined:
                result["has_webgpu"] = True
            if "ort" in joined or "onnx" in joined:
                result["has_onnx"] = True
            if "webauthn" in joined:
                result["has_fido2"] = True
        except Exception:
            pass

    # Go
    if (app_dir / "go.mod").exists():
        result["language"] = "go"
    # Python
    if (app_dir / "pyproject.toml").exists() or (app_dir / "requirements.txt").exists():
        result["language"] = "python"

    return result


@kosei.command("stack")
@click.argument("nanoid")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
@click.option("--data-dir", default=None)
def kosei_stack(nanoid: str, json_out: bool, workspace_dir: str | None, data_dir: str | None) -> None:
    """Deep tech-stack profile for one app (bindings, features, deps)."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps_cfg = cfg.get("apps", {})

    metas = _discover_apps_meta(ws)
    meta = next((m for m in metas if m["nanoid"] == nanoid or m["name"] == nanoid), None)
    if meta is None:
        raise click.ClickException(f"app '{nanoid}' not found")

    app_dir = Path(meta["path"])
    stack = _scan_app_stack(app_dir)
    tier = apps_cfg.get(meta["nanoid"], {}).get("tier", "")
    eta = _TIER_ETA.get(tier, 0.0)

    if json_out:
        click.echo(json.dumps({"meta": {**meta, "tier": tier, "eta": eta}, "stack": stack},
                              ensure_ascii=False, indent=2))
        return

    def _b(v: bool) -> str:
        return "yes" if v else "no"

    click.echo(f"Stack: {meta['name']}  ({meta['nanoid']})")
    click.echo(f"Tier:  {tier or '—'}  η={eta:.3f}")
    click.echo(f"Dir:   {meta['dir']}\n")
    click.echo("── Execution ──────────────────────────────────────")
    click.echo(f"  Language:    {stack['language']}")
    click.echo(f"  Framework:   {stack['framework']}")
    click.echo(f"  GuestLang:   {stack['guest_language'] or '—'}")
    click.echo(f"  PerformerType: {meta['performerType']}")
    click.echo(f"  ContentMode: {stack['content_mode'] or '—'}\n")
    click.echo("── Cloudflare Bindings ────────────────────────────")
    click.echo(f"  Workers AI:   {_b(stack['has_workers_ai'])}")
    click.echo(f"  Browser:      {_b(stack['has_browser'])}")
    click.echo(f"  Svelte Assets:{_b(stack['has_assets'])}")
    click.echo(f"  PDS_RPC:      {_b(stack['has_pds_rpc'])}")
    click.echo(f"  R2 buckets:   {stack['r2_count']}")
    click.echo(f"  Services:     {stack['service_count']}")
    click.echo(f"  Secrets:      {stack['secret_count']}")
    if stack["cf_bindings"]:
        click.echo(f"  All bindings: {', '.join(stack['cf_bindings'][:10])}")
    click.echo("\n── Features ───────────────────────────────────────")
    click.echo(f"  WebGPU:       {_b(stack['has_webgpu'])}")
    click.echo(f"  ONNX/ML:      {_b(stack['has_onnx'])}")
    click.echo(f"  FIDO2:        {_b(stack['has_fido2'])}")
    click.echo(f"  Signal E2E:   {_b(stack['has_signal'])}")
    click.echo(f"  WASM:         {_b(stack['has_wasm'])}")
    click.echo(f"  MCP server:   {_b(stack['has_mcp'])}")
    click.echo(f"  BPMN:         {_b(stack['has_bpmn'])}")
    click.echo(f"  Evolver:      {_b(stack['has_evolver'])}")
    click.echo(f"  Space/Chan:   {_b(stack['has_space'])}")
    click.echo(f"  subscribeRepos: {_b(stack['has_subscribe'])} ({stack['coll_count']} collections)")
    click.echo(f"  WIT contract: {_b(stack['has_wit'])}")
    click.echo(f"  requires/provides: {stack['requires_count']}/{stack['provides_count']}")
    if stack["wit_imports"]:
        click.echo(f"\n── WIT Imports ───────────────────────────────────")
        for imp in stack["wit_imports"]:
            click.echo(f"  {imp}")
    if stack["cargo_crates"]:
        click.echo(f"\n── Cargo crates ({len(stack['cargo_crates'])}) ─────────────────────────────")
        for c in stack["cargo_crates"][:15]:
            click.echo(f"  {c}")
    if stack["npm_deps"]:
        click.echo(f"\n── Notable npm deps ({len(stack['npm_deps'])}) ─────────────────────────")
        for d in stack["npm_deps"][:15]:
            click.echo(f"  {d}")
        if len(stack["npm_deps"]) > 15:
            click.echo(f"  ... and {len(stack['npm_deps']) - 15} more")


# ── kosei kashika ──────────────────────────────────────────────────────────────

@kosei.command("kashika")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--data-dir", "data_dir", default=None)
@click.option("--out", default=None, help="Output HTML file path (default: temp file)")
@click.option("--no-open", "no_open", is_flag=True, default=False, help="Do not open browser")
def kosei_kashika(workspace_dir: str | None, data_dir: str | None, out: str | None, no_open: bool) -> None:
    """Generate an interactive HTML tier dashboard and open in browser."""
    ws = _resolve_root(workspace_dir)
    dd = _kosei_data_dir(data_dir, ws)
    cfg = _load_kosei_config(dd)
    apps_cfg = cfg.get("apps", {})
    metas = _discover_apps_meta(ws)

    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    total = len(metas)
    t1_count = sum(1 for m in metas if apps_cfg.get(m["nanoid"], {}).get("tier") == "T1")
    t2_count = sum(1 for m in metas if apps_cfg.get(m["nanoid"], {}).get("tier") == "T2")
    t3_count = sum(1 for m in metas if apps_cfg.get(m["nanoid"], {}).get("tier") == "T3")
    unset_count = total - t1_count - t2_count - t3_count

    rows_data = []
    for m in metas:
        nid = m["nanoid"]
        tier = apps_cfg.get(nid, {}).get("tier", "")
        eta = _TIER_ETA.get(tier, None)
        eta_str = f"{eta:.3f}" if eta is not None else "–"
        tier_display = tier if tier else "–"
        tier_class = f"tier-{tier}" if tier in _TIER_ETA else ""
        rows_data.append((tier_display, nid, m.get("name", ""), tier_class, eta_str))

    rows_data.sort(key=lambda r: (r[0], r[1]))

    row_html_parts = []
    for tier_display, nid, name, tier_class, eta_str in rows_data:
        tier_cell = (
            f'<span class="{tier_class}">{tier_display}</span>'
            if tier_class
            else tier_display
        )
        row_html_parts.append(
            f"<tr><td>{nid}</td><td>{name}</td><td>{tier_cell}</td><td>{eta_str}</td></tr>"
        )
    rows = "\n".join(row_html_parts)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Kosei Tier Dashboard</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #f9f9f9; }}
  h1 {{ color: #1a1a1a; }}
  .stats {{ display: flex; gap: 2rem; margin: 1rem 0; }}
  .stat-box {{ background: white; padding: 1rem 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  .stat-box .label {{ font-size: .75rem; color: #666; }}
  .stat-box .value {{ font-size: 2rem; font-weight: bold; }}
  .tier-T1 {{ background: #d4edda; color: #155724; border-radius: 4px; padding: 2px 8px; }}
  .tier-T2 {{ background: #fff3cd; color: #856404; border-radius: 4px; padding: 2px 8px; }}
  .tier-T3 {{ background: #cce5ff; color: #004085; border-radius: 4px; padding: 2px 8px; }}
  table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  th {{ text-align: left; padding: .75rem 1rem; background: #f0f0f0; }}
  td {{ padding: .6rem 1rem; border-top: 1px solid #eee; }}
  tr:hover {{ background: #f5f5f5; }}
</style>
</head>
<body>
<h1>Kosei Tier Dashboard</h1>
<p>Generated: {generated_at}</p>
<div class="stats">
  <div class="stat-box"><div class="label">Total Apps</div><div class="value">{total}</div></div>
  <div class="stat-box"><div class="label">T1 (η=0.667)</div><div class="value">{t1_count}</div></div>
  <div class="stat-box"><div class="label">T2 (η=0.500)</div><div class="value">{t2_count}</div></div>
  <div class="stat-box"><div class="label">T3 (η=0.910)</div><div class="value">{t3_count}</div></div>
  <div class="stat-box"><div class="label">Unset</div><div class="value">{unset_count}</div></div>
</div>
<table>
<thead><tr><th>Nanoid</th><th>Name</th><th>Tier</th><th>η</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>"""

    out_path = out if out else tempfile.mktemp(suffix=".html", prefix="kosei-")
    Path(out_path).write_text(html, encoding="utf-8")
    click.echo(f"Saved to: {out_path}")
    if not no_open:
        webbrowser.open(f"file://{out_path}")
