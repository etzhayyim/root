"""code-quality — Unified code quality score across Rust/Go/TS/Python layers.

Each check returns a score 0-100 and an issue count. Available=False means the
required tool is not installed; those checks are skipped from the overall average.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

import click


@dataclass
class CQCheck:
    name: str
    tool: str
    available: bool = True
    score: float = 0.0
    issues: int = 0
    details: str = ""
    error: str = ""


@dataclass
class CQReport:
    evaluated_at: str
    overall_score: float
    available_tools: int
    skipped_tools: int
    checks: list[CQCheck] = field(default_factory=list)
    scoring_model: str = "average of available tool scores"


def _cap(v: float) -> float:
    return max(0.0, min(100.0, v))


def _git_root(start: Path | None = None) -> Path | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start or Path.cwd(),
            stderr=subprocess.DEVNULL,
        )
        return Path(out.strip().decode())
    except Exception:
        return None


def _find_cargo_workspaces(rust_dir: Path) -> list[Path]:
    if not rust_dir.exists():
        return []
    result = []
    for p in rust_dir.rglob("Cargo.toml"):
        if "target" in p.parts:
            continue
        result.append(p.parent)
    return result[:10]


def _find_go_mod_dirs(go_dir: Path) -> list[Path]:
    if not go_dir.exists():
        return []
    result = []
    for p in go_dir.rglob("go.mod"):
        if "vendor" in p.parts:
            continue
        result.append(p.parent)
    return result[:10]


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> tuple[str, int]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "timeout", 1
    except Exception as e:
        return str(e), 1


# ── individual checks ─────────────────────────────────────────────────────────

def check_cargo_machete(rust_dir: Path) -> CQCheck:
    c = CQCheck(name="cargo_machete", tool="cargo-machete")
    if not shutil.which("cargo"):
        c.available = False
        return c
    workspaces = _find_cargo_workspaces(rust_dir)
    if not workspaces:
        c.score = 100.0
        c.details = "no cargo workspaces found"
        return c
    total_unused = 0
    parts = []
    for ws in workspaces:
        out, _ = _run(["cargo", "machete", "--skip-target-dir"], ws)
        count = sum(1 for ln in out.splitlines() if ln.startswith("\t"))
        total_unused += count
        if count:
            parts.append(f"{count} unused in {ws.name}")
    c.issues = total_unused
    c.score = _cap(100 - total_unused * 3)
    if parts:
        c.details = ", ".join(parts)
    return c


def check_cargo_duplicates(rust_dir: Path) -> CQCheck:
    c = CQCheck(name="cargo_duplicates", tool="cargo tree -d")
    if not shutil.which("cargo"):
        c.available = False
        return c
    workspaces = _find_cargo_workspaces(rust_dir)
    if not workspaces:
        c.score = 100.0
        c.details = "no cargo workspaces found"
        return c
    crate_line_re = re.compile(r"^([a-zA-Z0-9_-]+)\s+v")
    dup_crates: set[str] = set()
    for ws in workspaces:
        out, _ = _run(["cargo", "tree", "-d", "--workspace"], ws)
        for line in out.splitlines():
            m = crate_line_re.match(line.strip())
            if m:
                dup_crates.add(m.group(1))
    count = len(dup_crates)
    c.issues = count
    if count > 0:
        penalty = 10.0 * math.sqrt(count)
        c.score = _cap(100 - penalty)
        c.details = f"{count} duplicate crates across workspaces"
    else:
        c.score = 100.0
    return c


def check_go_vet(go_dir: Path) -> CQCheck:
    c = CQCheck(name="go_vet", tool="go vet")
    if not shutil.which("go"):
        c.available = False
        return c
    mods = _find_go_mod_dirs(go_dir)
    if not mods:
        c.score = 100.0
        c.details = "no go modules found"
        return c
    total = 0
    for d in mods:
        out, rc = _run(["go", "vet", "./..."], d)
        if rc != 0:
            for ln in out.splitlines():
                ln = ln.strip()
                if ln and not ln.startswith("#") and "matched no packages" not in ln and not ln.startswith("go: warning:"):
                    total += 1
    c.issues = total
    c.score = _cap(100 - total * 10)
    if total:
        c.details = f"{total} vet issues across go modules"
    return c


def check_go_mod_tidy(go_dir: Path) -> CQCheck:
    c = CQCheck(name="go_mod_tidy", tool="go mod tidy -diff")
    if not shutil.which("go"):
        c.available = False
        return c
    mods = _find_go_mod_dirs(go_dir)
    if not mods:
        c.score = 100.0
        c.details = "no go modules found"
        return c
    clean, dirty, dirty_names = 0, 0, []
    for d in mods:
        out, rc = _run(["go", "mod", "tidy", "-diff"], d)
        if rc != 0 or out.strip():
            dirty += 1
            dirty_names.append(d.name)
        else:
            clean += 1
    total = clean + dirty
    c.issues = dirty
    c.score = (clean / total * 100) if total else 100.0
    if dirty:
        c.details = f"{dirty}/{total} modules dirty: {', '.join(dirty_names)}"
    return c


def check_jscpd(ws_root: Path, ts_dir: Path) -> CQCheck:
    c = CQCheck(name="jscpd_clones", tool="jscpd")
    if not shutil.which("npx"):
        c.available = False
        return c
    dirs_to_scan = []
    for p in [ts_dir, ws_root / "20-actors"]:
        if p.exists():
            dirs_to_scan.append(str(p))
    if not dirs_to_scan:
        c.score = 100.0
        c.details = "no TS directories found"
        return c
    out, rc = _run(
        ["npx", "--yes", "jscpd", "--reporters", "json", "--output", "/tmp/jscpd-cq",
         "--min-lines", "10", "--threshold", "0"] + dirs_to_scan[:2],
        ws_root, timeout=180,
    )
    # Try to read JSON output
    try:
        report_file = Path("/tmp/jscpd-cq/jscpd-report.json")
        if report_file.exists():
            data = json.loads(report_file.read_text())
            stat = data.get("statistics", {})
            pct = stat.get("total", {}).get("percentage", 0) or 0
            clones = stat.get("total", {}).get("clones", 0) or 0
            c.issues = clones
            c.score = _cap(100 - pct * 3)
            c.details = f"{clones} clone pairs ({pct:.1f}% duplication)"
            return c
    except Exception:
        pass
    # Fallback: parse text output
    match = re.search(r"Found (\d+) clone", out)
    clones = int(match.group(1)) if match else 0
    c.issues = clones
    c.score = _cap(100 - clones * 5)
    if clones:
        c.details = f"{clones} clone pairs found"
    return c


def check_magatama_lint(ws_root: Path) -> CQCheck:
    c = CQCheck(name="magatama_lint", tool="etzhayyim-py lint")
    # Run our own Python lint command
    py_bin = sys.executable
    out, rc = _run([py_bin, "-m", "etzhayyim", "lint"], ws_root, timeout=60)
    c.score = 100.0 if rc == 0 else 0.0
    if rc != 0:
        lines = [ln for ln in out.splitlines() if "error" in ln.lower() or "violation" in ln.lower()]
        c.issues = len(lines)
        c.details = f"{len(lines)} lint issues"
    return c


def check_frontend_lint(ws_root: Path) -> CQCheck:
    c = CQCheck(name="frontend_lint", tool="pnpm lint")
    if not shutil.which("pnpm"):
        c.available = False
        return c
    # Check key TS packages
    pkg_root = ws_root / "20-actors" / "magatama"
    if not pkg_root.exists():
        c.score = 100.0
        c.details = "no TS packages found"
        return c
    out, rc = _run(["pnpm", "lint", "--if-present"], pkg_root, timeout=120)
    errors = sum(1 for ln in out.splitlines() if "error" in ln.lower() and "warning" not in ln.lower())
    c.issues = errors
    c.score = _cap(100 - errors * 5)
    if errors:
        c.details = f"{errors} lint errors"
    return c


def check_perf_test(ws_root: Path) -> CQCheck:
    c = CQCheck(name="perf_test", tool="perf-test-coverage (built-in)")
    targets = [
        ("yoro", ws_root / "60-apps" / "etzhayyim-project-yoro", "profile-performance"),
    ]
    found, missing = 0, 0
    parts = []
    for name, proj_dir, pattern in targets:
        has_perf = False
        for spec in proj_dir.rglob(f"*{pattern}*.spec.ts"):
            if "toBeLessThan" in spec.read_text(errors="replace"):
                has_perf = True
                break
        if has_perf:
            found += 1
            parts.append(f"{name}: perf test found")
        else:
            missing += 1
            parts.append(f"{name}: perf test MISSING")
    c.issues = missing
    c.score = _cap(found / len(targets) * 100) if targets else 100.0
    c.details = ", ".join(parts)
    return c


def check_sql_injection(ws_root: Path) -> CQCheck:
    c = CQCheck(name="sql_injection", tool="sql-injection-lint (built-in)")
    pds_src = ws_root / "50-infra" / "cloudflare" / "workers" / "atproto" / "src"
    target = pds_src / "pds-dispatch.ts"
    if not target.exists():
        c.score = 100.0
        c.details = "PDS pds-dispatch.ts not found (skipped)"
        return c
    content = target.read_text(errors="replace")
    rules = [
        ("esc-interpolation", re.compile(r"\$\{esc\(")),
        ("template-sql", re.compile(r'"\$\{[^}]+\}"')),
    ]
    total = 0
    parts = []
    for rule_id, pattern in rules:
        matches = len(pattern.findall(content))
        if matches:
            total += matches
            parts.append(f"{rule_id}: {matches}")
    c.issues = total
    c.score = 100.0 if total == 0 else 0.0
    c.details = ("PDS: no SQL injection patterns" if total == 0
                 else "PDS: " + ", ".join(parts))
    return c


def check_sql_full_scan(ws_root: Path) -> CQCheck:
    c = CQCheck(name="sql_full_scan", tool="sql-full-scan-lint (built-in)")
    pds_src = ws_root / "50-infra" / "cloudflare" / "workers" / "atproto" / "src"
    handler_files = [
        "pds-handlers-feed.ts", "pds-handlers-etzhayyim.ts", "pds-handlers-repo.ts",
        "pds-actor.ts",
    ]
    identity_re = re.compile(
        r"\w\.\b(?:rkey|repo|did|nanoid|vertex_id|collection|owner_did|ownerDid|app_id|"
        r"visibility|status|region|vertex_type|project_id)\b\s*(?:=|IN\s*\[|IS\s+NOT\s+NULL|STARTS\s+WITH|<>|!=)"
    )
    match_re = re.compile(r"MATCH\s*\(\w+:\w+\)")
    total = 0
    parts = []
    for fname in handler_files:
        fpath = pds_src / fname
        if not fpath.exists():
            continue
        lines = fpath.read_text(errors="replace").splitlines()
        for i, line in enumerate(lines):
            if not match_re.search(line):
                continue
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            if identity_re.search(line):
                continue
            if any(kw in line for kw in ["${filter}", "${conditions", "multiDidFilter", "{nanoid:", "{rkey:", "{did:"]):
                continue
            total += 1
            parts.append(f"{fname}:{i+1}")
    c.issues = total
    c.score = 100.0 if total == 0 else _cap(100 - total * 5)
    c.details = ("PDS handlers: no full scan queries" if total == 0
                 else f"PDS handlers: {total} full scan queries — {', '.join(parts[:10])}")
    return c


def check_dead_exports(ws_root: Path) -> CQCheck:
    c = CQCheck(name="dead_exports", tool="dead-exports.mjs")
    if not shutil.which("node") or not shutil.which("rg"):
        c.available = False
        return c
    script = ws_root / "70-tools" / "scripts" / "lint" / "dead-exports.mjs"
    if not script.exists():
        c.score = 100.0
        c.details = "dead-exports.mjs not found (skip)"
        return c
    out, _ = _run(["node", str(script), "--json", "--warn-only"], ws_root, timeout=120)
    try:
        data = json.loads(out)
        total = data.get("total", 0)
        c.issues = total
        c.score = _cap(100 - total * 5)
        if total:
            by_file: dict[str, int] = {}
            for d in data.get("dead", []):
                by_file[d.get("file", "?")] = by_file.get(d.get("file", "?"), 0) + 1
            parts = [f"{n} in {Path(f).parent.name}" for f, n in by_file.items()]
            c.details = ", ".join(parts[:10])
    except Exception as e:
        c.error = f"parse dead-exports output: {e}"
    return c


# ── main runner ───────────────────────────────────────────────────────────────

def run_code_quality(
    ws_root: Path,
    rust_dir: Path,
    go_dir: Path,
    ts_dir: Path,
    skip: set[str],
) -> CQReport:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_checks: list[tuple[str, object]] = [
        ("cargo_machete",    lambda: check_cargo_machete(rust_dir)),
        ("cargo_duplicates", lambda: check_cargo_duplicates(rust_dir)),
        ("go_vet",           lambda: check_go_vet(go_dir)),
        ("go_mod_tidy",      lambda: check_go_mod_tidy(go_dir)),
        ("jscpd_clones",     lambda: check_jscpd(ws_root, ts_dir)),
        ("magatama_lint",    lambda: check_magatama_lint(ws_root)),
        ("frontend_lint",    lambda: check_frontend_lint(ws_root)),
        ("perf_test",        lambda: check_perf_test(ws_root)),
        ("sql_injection",    lambda: check_sql_injection(ws_root)),
        ("sql_full_scan",    lambda: check_sql_full_scan(ws_root)),
        ("dead_exports",     lambda: check_dead_exports(ws_root)),
    ]

    results: list[CQCheck] = []
    available, skipped = 0, 0
    for name, fn in all_checks:
        if name in skip:
            skipped += 1
            continue
        r = fn()
        results.append(r)
        if r.available:
            available += 1

    scored = [r for r in results if r.available and not r.error]
    overall = sum(r.score for r in scored) / len(scored) if scored else 0.0

    return CQReport(
        evaluated_at=now,
        overall_score=round(overall, 1),
        available_tools=available,
        skipped_tools=skipped,
        checks=results,
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.group("code-quality")
def code_quality_cmd() -> None:
    """Unified code quality score across Rust/Go/TS layers."""


@code_quality_cmd.command("run")
@click.option("--workspace-dir", default=None, help="repo root (default: git root)")
@click.option("--rust-dir", default=None, help="Rust packages dir")
@click.option("--go-dir", default=None, help="Go packages dir")
@click.option("--ts-dir", default=None, help="TS packages dir")
@click.option("--skip", default="", help="comma-separated checks to skip")
@click.option("--json", "json_out", is_flag=True, default=False)
def cq_run(workspace_dir: str | None, rust_dir: str | None, go_dir: str | None,
           ts_dir: str | None, skip: str, json_out: bool) -> None:
    """Run all code quality checks and output a unified score."""
    ws = Path(workspace_dir) if workspace_dir else _git_root()
    if ws is None or not ws.exists():
        raise click.ClickException("could not find workspace root; use --workspace-dir")

    r_dir = Path(rust_dir) if rust_dir else ws / "20-actors" / "magatama"
    g_dir = Path(go_dir) if go_dir else ws / "70-tools" / "etzhayyim"
    t_dir = Path(ts_dir) if ts_dir else ws / "20-actors"
    skip_set = {s.strip() for s in skip.split(",") if s.strip()}

    report = run_code_quality(ws, r_dir, g_dir, t_dir, skip_set)

    if json_out:
        out = {
            "evaluated_at": report.evaluated_at,
            "overall_score": report.overall_score,
            "available_tools": report.available_tools,
            "skipped_tools": report.skipped_tools,
            "scoring_model": report.scoring_model,
            "checks": [asdict(c) for c in report.checks],
        }
        click.echo(json.dumps(out, ensure_ascii=False, indent=2))
        return

    # Text output
    click.echo(f"code quality report  {report.evaluated_at}")
    click.echo(f"overall score: {report.overall_score:.1f}/100  "
               f"(tools: {report.available_tools} available, {report.skipped_tools} skipped)")
    click.echo("")
    fmt = "  {:<22} {:>6}  {:>8}  {}"
    click.echo(fmt.format("check", "score", "issues", "details"))
    click.echo("  " + "-" * 70)
    for c in report.checks:
        avail = "" if c.available else " [not installed]"
        err = f" ERR:{c.error[:40]}" if c.error else ""
        click.echo(fmt.format(
            c.name,
            f"{c.score:.0f}" if c.available else "—",
            str(c.issues) if c.available else "—",
            (c.details[:50] + avail + err) or avail or err or "ok",
        ))
