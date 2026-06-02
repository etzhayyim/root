"""process_mining — PDS handler static analysis for performance bottlenecks."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import click

from .shannon import _resolve_root


# ── helpers ────────────────────────────────────────────────────────────────────


def _resolve_pm_handler_dir(ws: Path) -> Path | None:
    """Find the PDS handler directory. Returns first existing path or None."""
    candidates = [
        ws / "50-infra/cloudflare/workers/atproto/src/handlers",
        ws / "50-infra/cloudflare/workers/atproto/src",
        ws / "infra/cloudflare/workers/pds/src",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _analyze_handler_file(path: Path) -> dict:
    """Analyze a single TypeScript handler file for performance bottlenecks."""
    try:
        content = path.read_text(errors="replace")
    except Exception:
        content = ""

    # NSID: strip .ts, replace - with .
    nsid = path.stem.replace("-", ".")

    bottlenecks: list[dict] = []

    patterns = [
        (
            r"await.*await",
            "critical",
            "nested-await",
            "Multiple sequential awaits may serialize I/O",
        ),
        (
            r'throw new Error.*\b(400|401|403|404)\b|status.*\b(400|401|403)\b',
            "low",
            "error-response",
            "Error response with HTTP status code",
        ),
        (
            r"setTimeout|setInterval",
            "medium",
            "timer",
            "Timers in handlers cause latency spikes",
        ),
        (
            r"fetch\(|new Request\(",
            "high",
            "outbound-fetch",
            "Outbound fetch in hot path adds tail latency",
        ),
        (
            r"while\s*\(\s*true\s*\)|for\s*\(\s*;;\s*\)",
            "critical",
            "infinite-loop",
            "Infinite loop detected in handler",
        ),
        (
            r"catch\s*\([^)]*\)\s*\{\s*\}|catch\s*\([^)]*\)\s*//",
            "high",
            "silent-catch",
            "Empty or silent catch swallows errors",
        ),
    ]

    for regex, severity, pattern_name, detail in patterns:
        if pattern_name == "repeated-json-parse":
            continue  # handled separately below
        for m in re.finditer(regex, content, re.IGNORECASE):
            line_no = content[: m.start()].count("\n") + 1
            bottlenecks.append(
                {
                    "pattern": pattern_name,
                    "severity": severity,
                    "line_no": line_no,
                    "detail": detail,
                }
            )

    # repeated JSON parse/stringify (>2 occurrences total)
    json_matches = list(re.finditer(r"JSON\.parse|JSON\.stringify", content))
    if len(json_matches) > 2:
        m = json_matches[0]
        line_no = content[: m.start()].count("\n") + 1
        bottlenecks.append(
            {
                "pattern": "repeated-json-parse",
                "severity": "medium",
                "line_no": line_no,
                "detail": f"JSON.parse/stringify called {len(json_matches)} times — consider caching",
            }
        )

    return {
        "path": str(path),
        "nsid": nsid,
        "bottleneck_count": len(bottlenecks),
        "bottlenecks": bottlenecks,
    }


def _compute_pm_summary(handlers: list[dict]) -> dict:
    """Compute aggregate summary across all analyzed handlers."""
    total_bottlenecks = sum(h["bottleneck_count"] for h in handlers)
    critical = sum(
        1 for h in handlers for b in h["bottlenecks"] if b["severity"] == "critical"
    )
    high = sum(
        1 for h in handlers for b in h["bottlenecks"] if b["severity"] == "high"
    )
    medium = sum(
        1 for h in handlers for b in h["bottlenecks"] if b["severity"] == "medium"
    )
    low = sum(
        1 for h in handlers for b in h["bottlenecks"] if b["severity"] == "low"
    )
    score = max(0.0, 100.0 - critical * 25 - high * 10 - medium * 5 - low * 2)
    if score >= 90:
        grade = "S"
    elif score >= 70:
        grade = "A"
    elif score >= 50:
        grade = "B"
    elif score >= 30:
        grade = "C"
    else:
        grade = "D"
    return {
        "total_handlers": len(handlers),
        "total_bottlenecks": total_bottlenecks,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "score": score,
        "grade": grade,
    }


# ── command group ──────────────────────────────────────────────────────────────


@click.group("process-mining", invoke_without_command=True)
@click.option("--workspace-dir", "workspace_dir", default=None, help="Workspace root override.")
@click.option("--json", "json_out", is_flag=True, default=False, help="Output as JSON.")
@click.pass_context
def process_mining(ctx, workspace_dir, json_out):
    """PDS handler static analysis + performance bottleneck detection."""
    if ctx.invoked_subcommand is not None:
        return
    # Default behaviour: delegate to scan
    ctx.ensure_object(dict)
    ctx.obj["workspace_dir"] = workspace_dir
    ctx.obj["json_out"] = json_out
    ctx.invoke(scan)


# ── scan ───────────────────────────────────────────────────────────────────────


@process_mining.command("scan")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--severity", "severity_filter", default="", help="Filter by severity (critical/high/medium/low).")
def scan(workspace_dir, json_out, severity_filter):
    """Full handler analysis — scan all *.ts files and report bottlenecks."""
    ws = _resolve_root(workspace_dir)
    handler_dir = _resolve_pm_handler_dir(ws)
    if handler_dir is None:
        msg = {"error": "Handler directory not found", "workspace": str(ws)}
        if json_out:
            click.echo(json.dumps(msg, indent=2))
        else:
            click.echo(f"[process-mining] Handler directory not found under {ws}", err=True)
        return

    ts_files = sorted(handler_dir.glob("**/*.ts"))
    if not ts_files:
        msg = {"error": "No .ts files found", "handler_dir": str(handler_dir)}
        if json_out:
            click.echo(json.dumps(msg, indent=2))
        else:
            click.echo(f"[process-mining] No .ts files found in {handler_dir}", err=True)
        return

    t0 = time.monotonic()
    handlers = [_analyze_handler_file(f) for f in ts_files]
    elapsed = time.monotonic() - t0

    if severity_filter:
        for h in handlers:
            h["bottlenecks"] = [b for b in h["bottlenecks"] if b["severity"] == severity_filter]
            h["bottleneck_count"] = len(h["bottlenecks"])

    summary = _compute_pm_summary(handlers)

    if json_out:
        click.echo(json.dumps({"summary": summary, "handlers": handlers, "elapsed_s": round(elapsed, 3)}, indent=2))
        return

    # Human-readable table
    click.echo(f"\n[process-mining scan]  handler_dir={handler_dir}  elapsed={elapsed:.2f}s\n")
    click.echo(f"{'NSID':<50}  {'bottlenecks':>11}  path")
    click.echo("-" * 100)
    for h in handlers:
        nsid = h["nsid"][:49]
        click.echo(f"{nsid:<50}  {h['bottleneck_count']:>11}  {h['path']}")
    click.echo("-" * 100)
    s = summary
    click.echo(
        f"\nSummary: handlers={s['total_handlers']}  bottlenecks={s['total_bottlenecks']}"
        f"  critical={s['critical']}  high={s['high']}  medium={s['medium']}  low={s['low']}"
        f"  score={s['score']:.1f}  grade={s['grade']}\n"
    )


# ── bottlenecks ────────────────────────────────────────────────────────────────


@process_mining.command("bottlenecks")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--severity", "severity_filter", default="", help="Filter by severity.")
def bottlenecks(workspace_dir, json_out, severity_filter):
    """Show only critical and high severity findings across all handlers."""
    ws = _resolve_root(workspace_dir)
    handler_dir = _resolve_pm_handler_dir(ws)
    if handler_dir is None:
        click.echo("[process-mining] Handler directory not found.", err=True)
        return

    ts_files = sorted(handler_dir.glob("**/*.ts"))
    handlers = [_analyze_handler_file(f) for f in ts_files]

    _severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    target_severities = {"critical", "high"} if not severity_filter else {severity_filter}

    findings = []
    for h in handlers:
        for b in h["bottlenecks"]:
            if b["severity"] in target_severities:
                findings.append({
                    "nsid": h["nsid"],
                    "path": h["path"],
                    **b,
                })

    findings.sort(key=lambda x: (_severity_order.get(x["severity"], 99), x["nsid"]))

    if json_out:
        click.echo(json.dumps({"findings": findings, "count": len(findings)}, indent=2))
        return

    click.echo(f"\n[process-mining bottlenecks]  {len(findings)} critical/high finding(s)\n")
    if not findings:
        click.echo("  No critical or high severity bottlenecks found.")
        return
    click.echo(f"{'SEV':<9}  {'PATTERN':<20}  {'LINE':>5}  {'NSID':<40}  detail")
    click.echo("-" * 110)
    for f in findings:
        click.echo(
            f"{f['severity']:<9}  {f['pattern']:<20}  {f['line_no']:>5}  {f['nsid'][:39]:<40}  {f['detail']}"
        )
    click.echo()


# ── flow ───────────────────────────────────────────────────────────────────────


@process_mining.command("flow")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--handler", "handler_name", required=True, help="Handler filename stem or NSID fragment to inspect.")
def flow(workspace_dir, json_out, handler_name):
    """Show request flow (XRPC calls + await chain) for a specific handler."""
    ws = _resolve_root(workspace_dir)
    handler_dir = _resolve_pm_handler_dir(ws)
    if handler_dir is None:
        click.echo("[process-mining] Handler directory not found.", err=True)
        return

    # Find matching file
    ts_files = list(handler_dir.glob("**/*.ts"))
    candidate = None
    for f in ts_files:
        if handler_name in f.stem or handler_name.replace(".", "-") in f.stem:
            candidate = f
            break

    if candidate is None:
        click.echo(f"[process-mining] No handler file matching '{handler_name}' found.", err=True)
        return

    try:
        content = candidate.read_text(errors="replace")
    except Exception as e:
        click.echo(f"[process-mining] Could not read {candidate}: {e}", err=True)
        return

    nsid = candidate.stem.replace("-", ".")

    # Extract XRPC calls
    xrpc_calls = re.findall(r"xrpc\.\w+\.(?:get|post|query|procedure)\s*\([^)]*\)", content)
    # Extract await expressions (first identifier/call after await)
    await_steps = re.findall(r"await\s+([\w.]+(?:\([^)]{0,80}\))?)", content)

    flow_steps = []
    for call in xrpc_calls:
        flow_steps.append({"type": "xrpc", "call": call.strip()})
    for step in await_steps[:20]:  # cap at 20 to avoid noise
        flow_steps.append({"type": "await", "call": step.strip()})

    if json_out:
        click.echo(json.dumps({"nsid": nsid, "path": str(candidate), "flow": flow_steps}, indent=2))
        return

    click.echo(f"\n[process-mining flow]  {nsid}  ({candidate})\n")
    if not flow_steps:
        click.echo("  No XRPC calls or await chains detected.")
        return

    # Build simple text-art flow diagram
    nodes = [nsid] + [s["call"] for s in flow_steps]
    click.echo("  " + " → ".join(nodes[:10]))
    if len(nodes) > 10:
        click.echo(f"  … ({len(nodes) - 10} more steps)")
    click.echo()
