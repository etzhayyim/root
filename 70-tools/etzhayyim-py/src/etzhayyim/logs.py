"""logs — OCEL v2 log viewer and analysis.

Reads OCEL event logs from PDS or local log files.
Full analysis (anomaly detection, clustering) requires the Go binary.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds
from .shannon import _resolve_root


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@click.group("logs", invoke_without_command=True)
@click.option("--pds", default=None)
@click.option("--limit", default=100, type=int, show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def logs(ctx: click.Context, pds: str | None, limit: int, json_out: bool) -> None:
    """OCEL v2 log viewer (recent events from PDS)."""
    if ctx.invoked_subcommand is not None:
        return
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.logs.listEvents",
            params={"limit": limit}, headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            events = data if isinstance(data, list) else data.get("events", [])
            for e in events:
                ts = e.get("ts", "")
                method = e.get("method", "")
                status = e.get("status", "")
                ms = e.get("ms", "")
                click.echo(f"  {ts}  {method:40}  {status}  {ms}ms")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@logs.command("tail")
@click.option("--pds", default=None)
@click.option("--limit", default=50, type=int, show_default=True)
@click.option("--filter", "filter_text", default="")
@click.option("--json", "json_out", is_flag=True, default=False)
def logs_tail(pds: str | None, limit: int, filter_text: str, json_out: bool) -> None:
    """Tail recent log events."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.logs.listEvents",
            params={"limit": limit, "filter": filter_text},
            headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            events = data if isinstance(data, list) else data.get("events", [])
            for e in events:
                click.echo(f"  {e.get('ts', '')}  {e.get('method', '')}  {e.get('status', '')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@logs.command("errors")
@click.option("--pds", default=None)
@click.option("--limit", default=50, type=int, show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
def logs_errors(pds: str | None, limit: int, json_out: bool) -> None:
    """Show recent error events (status >= 500)."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.logs.listEvents",
            params={"limit": limit, "minStatus": 500},
            headers=_auth_headers(), timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            events = data if isinstance(data, list) else data.get("events", [])
            for e in events:
                click.echo(f"  {e.get('ts', '')}  {e.get('method', '')}  "
                           f"status={e.get('status', '')}  {e.get('ms', '')}ms")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@logs.command("stats")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def logs_stats(pds: str | None, json_out: bool) -> None:
    """Aggregate log statistics (p50/p95 latency, error rate)."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.logs.getStats",
            headers=_auth_headers(), timeout=30,
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


_LAYER_PREFIXES = [
    ("orgs/etzhayyim/com-etzhayyim-", "actors"),
    ("60-apps/", "projects"), ("50-infra/", "infra"),
    ("20-actors/", "actors"),  # historical events before flat-west migration
    ("90-docs/", "docs"),
    ("40-engine/", "engine"), ("30-graph/", "graph"),
    ("00-contracts/", "contracts"), ("70-tools/", "tools"),
]


def _classify_layer(path: str) -> str:
    for prefix, layer in _LAYER_PREFIXES:
        if path.startswith(prefix):
            return layer
    return "root"


def _classify_scope(path: str, layer: str) -> str:
    parts = path.split("/")
    if layer == "root" or len(parts) < 2:
        return "root"
    return parts[1]


@logs.command("arch")
@click.option("--since", default="30 days ago", show_default=True, help="git --since value")
@click.option("--limit", default=200, type=int, show_default=True)
@click.option("--root", default=None, help="repo root (default: git rev-parse)")
@click.option("--json", "json_out", is_flag=True, default=False)
def logs_arch(since: str, limit: int, root: str | None, json_out: bool) -> None:
    """Architecture-layer commit distribution (git log --stat analysis)."""
    import subprocess
    import re
    from datetime import datetime, timezone

    def _git_root() -> str:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else "."

    repo_root = root or _git_root()
    fmt = "%H|%aI|%an|%s"
    r = subprocess.run(
        ["git", "log", f"--pretty=format:{fmt}", "--stat",
         f"--since={since}", f"-n{limit}"],
        capture_output=True, text=True, cwd=repo_root,
    )
    if r.returncode != 0:
        if "does not have any commits" in r.stderr:
            r = subprocess.CompletedProcess(r.args, 0, stdout="", stderr="")
        else:
            raise click.ClickException(f"git log failed: {r.stderr.strip()}")

    header_re = re.compile(r"^([0-9a-f]{40})\|(.+?)\|(.+?)\|(.*)$")
    stat_re = re.compile(r"^\s*(\d+) files? changed")
    file_re = re.compile(r"^\s*(.+?)\s+\|\s+\d+")

    events: list[dict] = []
    cur: dict | None = None
    cur_files: list[str] = []

    def _flush():
        nonlocal cur, cur_files
        if cur is None:
            return
        layer_counts: dict[str, int] = {}
        for f in cur_files:
            ly = _classify_layer(f)
            layer_counts[ly] = layer_counts.get(ly, 0) + 1
        dominant = max(layer_counts, key=lambda k: layer_counts[k]) if layer_counts else "root"
        scope = _classify_scope(cur_files[0], dominant) if cur_files else "root"
        cur.update({"layer": dominant, "scope": scope, "files": cur_files[:]})
        events.append(cur)
        cur = None
        cur_files = []

    for line in r.stdout.splitlines():
        m = header_re.match(line)
        if m:
            _flush()
            sha, ts, author, msg = m.group(1), m.group(2), m.group(3), m.group(4)
            cur = {"sha": sha[:12], "ts": ts, "author": author, "message": msg,
                   "added": 0, "removed": 0}
            cur_files = []
            continue
        if cur is None:
            continue
        sm = stat_re.match(line)
        if sm:
            added = re.search(r"(\d+) insertion", line)
            removed = re.search(r"(\d+) deletion", line)
            cur["added"] = int(added.group(1)) if added else 0
            cur["removed"] = int(removed.group(1)) if removed else 0
            continue
        fm = file_re.match(line)
        if fm and not line.strip().startswith(("Bin ", "binary")):
            cur_files.append(fm.group(1).strip())

    _flush()

    by_layer: dict[str, int] = {}
    by_scope: dict[str, int] = {}
    for ev in events:
        ly = ev["layer"]
        sc = ev["scope"]
        by_layer[ly] = by_layer.get(ly, 0) + 1
        by_scope[sc] = by_scope.get(sc, 0) + 1

    deploy_state: dict = {}
    ds_path = Path(repo_root) / ".deploy-state.json"
    if ds_path.exists():
        try:
            deploy_state = json.loads(ds_path.read_text())
        except Exception:
            pass

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "since": since,
        "total_events": len(events),
        "by_layer": by_layer,
        "by_scope": by_scope,
        "events": events,
        "deploy_state": deploy_state,
    }

    if json_out:
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  arch log report  since={since}  commits={len(events)}")
        click.echo("  by layer:")
        for ly, cnt in sorted(by_layer.items(), key=lambda x: -x[1]):
            bar = "█" * min(cnt, 40)
            click.echo(f"    {ly:12}  {cnt:4}  {bar}")
        click.echo("  top scopes:")
        for sc, cnt in sorted(by_scope.items(), key=lambda x: -x[1])[:10]:
            click.echo(f"    {sc:30}  {cnt}")
