"""complex_stubs — Commands that require the Go binary for their core functionality.

Each command provides basic structure (subcommands, --help) but directs users
to the Go binary for operations that require CF API, DB connections, or
complex orchestration.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import statistics
import subprocess
import sys
import threading
from pathlib import Path

import click


def _go_stub(cmd: str, detail: str = "") -> None:
    msg = f"etzhayyim {cmd} requires the Go binary."
    if detail:
        msg += f" {detail}"
    msg += f" Run: etzhayyim {cmd}"
    click.echo(msg, err=True)
    sys.exit(1)


# ── version ────────────────────────────────────────────────────────────────────

@click.command("version")
def version_cmd() -> None:
    """Print etzhayyim-py version."""
    try:
        from importlib.metadata import version
        ver = version("etzhayyim")
    except Exception:
        ver = "dev"
    click.echo(f"etzhayyim-py {ver}")


# ── set-profiles ───────────────────────────────────────────────────────────────

@click.group("set-profiles")
def set_profiles() -> None:
    """Set actor profile records on PDS from kotodama.jsonld files."""


@set_profiles.command("run")
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--pds", default=None, help="PDS URL")
@click.option("--workspace-dir", "workspace_dir", default=None)
@click.option("--concurrency", default=10, type=int, show_default=True)
def sp_run(dry_run: bool, pds: str | None, workspace_dir: str | None, concurrency: int) -> None:
    """Set AT Protocol profiles for all actor apps from kotodama.jsonld."""
    import json as _json

    import httpx

    # Resolve workspace root
    if workspace_dir:
        root = Path(workspace_dir)
    else:
        try:
            root = Path(
                subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True, text=True, check=True,
                ).stdout.strip()
            )
        except Exception as exc:
            click.echo(f"error: cannot find git root: {exc}", err=True)
            sys.exit(1)

    apps_dir = root / "60-apps"
    if not apps_dir.exists():
        click.echo(f"error: {apps_dir} does not exist", err=True)
        sys.exit(1)

    # Collect kotodama.jsonld files
    jsonld_files = sorted(apps_dir.rglob("kotodama.jsonld"))
    if not jsonld_files:
        click.echo("No kotodama.jsonld files found under 60-apps/")
        return

    profiles: list[dict] = []
    for f in jsonld_files:
        try:
            data = _json.loads(f.read_text())
        except Exception as exc:
            click.echo(f"warn: skip {f} — parse error: {exc}", err=True)
            continue
        nanoid = data.get("nanoid") or data.get("id") or ""
        name = data.get("name") or nanoid
        description = data.get("description") or ""
        if not nanoid:
            continue
        profiles.append({"handle": nanoid, "displayName": name, "description": description, "_source": str(f)})

    if not profiles:
        click.echo("No valid actor profiles found.")
        return

    if dry_run:
        for p in profiles:
            click.echo(f"  [dry-run] {p['handle']!r:40s}  {p['displayName']!r}")
        click.echo(f"Would set {len(profiles)} profiles (dry-run, skipping HTTP)")
        return

    # Resolve PDS URL
    auth = _load_auth()
    pds_url = pds or auth.get("pds_url", "https://mod.etzhayyim.com")
    pds_url = pds_url.rstrip("/")

    headers: dict[str, str] = {"Content-Type": "application/json"}
    access_jwt = auth.get("access_jwt")
    if access_jwt:
        headers["Authorization"] = f"Bearer {access_jwt}"

    errors = 0
    lock = threading.Lock()

    def _set_profile(profile: dict) -> None:
        nonlocal errors
        payload = {k: v for k, v in profile.items() if k != "_source"}
        try:
            httpx.post(
                f"{pds_url}/xrpc/com.etzhayyim.pds.putProfile",
                json=payload,
                headers=headers,
                timeout=10.0,
            )
        except Exception as exc:
            with lock:
                errors += 1
            click.echo(f"error: {profile['handle']}: {exc}", err=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        list(executor.map(_set_profile, profiles))

    click.echo(f"Set {len(profiles)} profiles ({errors} errors)")


# ── seed ───────────────────────────────────────────────────────────────────────

@click.group("seed")
def seed() -> None:
    """Data seeding commands (Go binary required)."""


@seed.command("run")
@click.argument("target", default="all")
def seed_run(target: str) -> None:
    """Seed domain data (requires Go binary + DB access)."""
    _go_stub("seed run", "Requires DB access.")


@seed.command("list")
def seed_list() -> None:
    """List available seed targets."""
    for t in ["domains", "naphtha-supply", "oil-backbone", "gap"]:
        click.echo(f"  {t}")


# ── domain-ingest ──────────────────────────────────────────────────────────────

def _find_git_root() -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


def _resolve_domain_ingest_script() -> Path | None:
    root = _find_git_root()
    if root is None:
        return None
    script = root / "70-tools" / "scripts" / "ingest-domain-data.ts"
    return script if script.exists() else None


def _resolve_cc_project_script(name: str) -> Path | None:
    root = _find_git_root()
    if root is None:
        return None
    candidates = [
        root / "60-apps" / "etzhayyim-project-common-crawl" / "scripts" / name,
        root / "projects" / "etzhayyim-project-common-crawl" / "scripts" / name,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


@click.group("domain-ingest")
def domain_ingest() -> None:
    """Domain data ingestion pipeline (normalize → enrich → PDS write)."""


@domain_ingest.command("local")
@click.option("--domain", default="", help="domain filter (e.g., hanrei, gtin)")
@click.option("--limit", default=10000, type=int, show_default=True)
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
@click.option("--skip-llm", "skip_llm", is_flag=True, default=False)
def di_local(domain: str, limit: int, dry_run: bool, skip_llm: bool) -> None:
    """Ingest domain datasets from local scripts/ingest-domain-data.ts."""
    script = _resolve_domain_ingest_script()
    if script is None:
        click.echo("domain ingest script not found: 70-tools/scripts/ingest-domain-data.ts", err=True)
        sys.exit(1)
    if not subprocess.run(["which", "npx"], capture_output=True).returncode == 0:
        click.echo("npx not found in PATH", err=True)
        sys.exit(1)
    args = ["npx", "tsx", str(script)]
    if domain:
        args += ["--domain", domain]
    if limit > 0:
        args += ["--limit", str(limit)]
    if dry_run:
        args.append("--dry-run")
    if skip_llm:
        args.append("--skip-llm")
    click.echo(f"▶ domain-ingest local: script={script.name} limit={limit} dry-run={dry_run}")
    if domain:
        click.echo(f"  domain filter: {domain}")
    sys.exit(subprocess.run(args).returncode)


@domain_ingest.command("common-crawl")
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
@click.option("--batch-size", "batch_size", default=200, type=int, show_default=True)
@click.option("--source", default="intel", show_default=True,
              help="data source: intel or graph")
@click.option("--pds", "pds_url", default="https://atproto.etzhayyim.com", show_default=True)
def di_common_crawl(dry_run: bool, batch_size: int, source: str, pds_url: str) -> None:
    """Import Common Crawl exports into PDS."""
    script = _resolve_cc_project_script("phase5_inject.py")
    if script is None:
        click.echo("Common Crawl inject script not found: phase5_inject.py", err=True)
        sys.exit(1)
    args = [sys.executable, str(script)]
    if dry_run:
        args.append("--dry-run")
    args += ["--batch-size", str(batch_size), "--source", source]
    env = os.environ.copy()
    env["PDS_URL"] = pds_url
    click.echo(f"▶ domain-ingest common-crawl: source={source} batch={batch_size} dry-run={dry_run}")
    sys.exit(subprocess.run(args, env=env).returncode)


# ── collect ────────────────────────────────────────────────────────────────────

@click.group("collect")
def collect() -> None:
    """Data collection pipeline (Go binary required)."""


@collect.command("run")
@click.option("--source", default="")
def collect_run(source: str) -> None:
    """Run collection pipeline (requires Go binary)."""
    _go_stub("collect run")


# ── pds ────────────────────────────────────────────────────────────────────────

@click.group("pds")
def pds() -> None:
    """PDS management commands (Go binary required for admin ops)."""


def _load_auth() -> dict:
    """Load ~/.etzhayyim/auth.json if it exists, else return empty dict."""
    import json
    from pathlib import Path

    auth_path = Path.home() / ".etzhayyim" / "auth.json"
    if auth_path.exists():
        try:
            return json.loads(auth_path.read_text())
        except Exception:
            pass
    return {}


@pds.command("status")
@click.option("--pds", "pds_url", default=None, help="PDS base URL")
@click.option("--json", "json_out", is_flag=True, default=False)
def pds_status(pds_url: str | None, json_out: bool) -> None:
    """Show PDS health status."""
    import json as _json

    import httpx

    if pds_url is None:
        auth = _load_auth()
        pds_url = auth.get("pds_url", "https://mod.etzhayyim.com")

    url = pds_url.rstrip("/") + "/health"
    try:
        resp = httpx.get(url, timeout=5.0)
        if json_out:
            try:
                data = resp.json()
            except Exception:
                data = {"status": resp.text}
            click.echo(_json.dumps(data, ensure_ascii=False))
        else:
            click.echo(f"GET {url}  →  {resp.status_code}")
            click.echo(resp.text)
    except Exception as exc:
        if json_out:
            click.echo(_json.dumps({"error": "unreachable", "detail": str(exc)}))
        else:
            click.echo(f"unreachable: {exc}", err=True)
        sys.exit(1)


@pds.command("qa")
@click.option("--target", default=None, help="PDS base URL (default: from auth or https://mod.etzhayyim.com)")
@click.option("--rounds", default=5, type=int, show_default=True, help="Rounds per probe")
@click.option("--json", "json_out", is_flag=True, default=False)
def pds_qa(target: str | None, rounds: int, json_out: bool) -> None:
    """PDS API stability evaluation (health, cache, circuit breaker)."""
    import json as _json
    import statistics
    import time

    import httpx

    auth = _load_auth()

    if target is None:
        target = auth.get("pds_url", "https://mod.etzhayyim.com")
    base = target.rstrip("/")

    headers: dict[str, str] = {}
    access_jwt = auth.get("access_jwt")
    if access_jwt:
        headers["Authorization"] = f"Bearer {access_jwt}"

    probes = [
        ("health", "/health"),
        ("timeline", "/xrpc/app.bsky.feed.getTimeline"),
        ("author-feed", "/xrpc/app.bsky.feed.getAuthorFeed"),
        ("profile", "/xrpc/app.bsky.actor.getProfile"),
    ]

    results = []
    for name, path in probes:
        latencies: list[float] = []
        for _ in range(rounds):
            t0 = time.perf_counter()
            try:
                httpx.get(base + path, headers=headers, timeout=5.0)
                latencies.append((time.perf_counter() - t0) * 1000)
            except Exception:
                latencies.append(0.0)

        if any(v > 0 for v in latencies):
            valid = [v for v in latencies if v > 0]
            avg_ms = sum(valid) / len(valid)
            p50_ms = statistics.median(valid)
            sorted_l = sorted(valid)
            p95_idx = max(0, int(len(sorted_l) * 0.95) - 1)
            p95_ms = sorted_l[p95_idx]
        else:
            avg_ms = p50_ms = p95_ms = 0.0

        if p95_ms == 0.0:
            status = "fail"
        elif p95_ms < 300:
            status = "pass"
        elif p95_ms < 800:
            status = "warn"
        else:
            status = "fail"

        results.append({
            "probe": name,
            "status": status,
            "avg_ms": round(avg_ms, 1),
            "p50_ms": round(p50_ms, 1),
            "p95_ms": round(p95_ms, 1),
        })

    if json_out:
        click.echo(_json.dumps(results, ensure_ascii=False))
        return

    header = f"{'probe':<16}{'status':<8}{'avg_ms':>8}{'p50_ms':>8}{'p95_ms':>8}"
    click.echo(header)
    click.echo("─" * len(header))
    for r in results:
        click.echo(
            f"{r['probe']:<16}{r['status']:<8}{r['avg_ms']:>8.1f}{r['p50_ms']:>8.1f}{r['p95_ms']:>8.1f}"
        )


# ── code / code-quality / hinshitsu ───────────────────────────────────────────

@click.group("code")
def code() -> None:
    """Code analysis commands (Go binary required for full analysis)."""


@code.command("quality")
@click.option("--workspace-dir", default=None, help="repo root (default: git root)")
@click.option("--skip", default="", help="comma-separated checks to skip")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def code_quality(ctx: click.Context, workspace_dir: str | None, skip: str, json_out: bool) -> None:
    """Code quality analysis (delegates to code-quality run)."""
    from .code_quality import code_quality_cmd
    ctx.invoke(code_quality_cmd.commands["run"],
               workspace_dir=workspace_dir, skip=skip, json_out=json_out,
               rust_dir=None, go_dir=None, ts_dir=None)


def _find_agent_dir() -> Path | None:
    # try git root / 60-apps/etzhayyim-terminal-agent
    try:
        root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        p = Path(root) / "60-apps" / "etzhayyim-terminal-agent"
        if p.exists():
            return p
    except Exception:
        pass
    return None


@code.command("exec")
@click.option("--dir", "work_dir", default=".", show_default=True,
              help="Working directory for the agent")
@click.option("--message", default="", help="One-shot prompt (required)")
@click.option("--model", default="", help="Override model (default: AGENT_MODEL env or anthropic/claude-sonnet-4-6)")
@click.option("--api-key", "api_key", default="", help="OpenRouter API key (default: OPENROUTER_API_KEY env)")
@click.option("--uv-bin", "uv_bin", default="uv", show_default=True, help="uv binary path")
@click.option("--dry-run", is_flag=True, default=False)
def code_exec(work_dir: str, message: str, model: str, api_key: str, uv_bin: str, dry_run: bool) -> None:
    """Run terminal-agent in non-interactive one-shot mode (--message required)."""
    msg = message.strip()
    if not msg:
        raise click.ClickException("--message is required for 'etzhayyim code exec'")

    resolved_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not resolved_key and not dry_run:
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-s", "etzhayyim.openrouter", "-w"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                resolved_key = result.stdout.strip()
        except Exception:
            pass
    if not resolved_key and not dry_run:
        raise click.ClickException(
            "OPENROUTER_API_KEY is not set.\n"
            "Set it via env or --api-key, or load from Keychain:\n"
            "  security find-generic-password -s etzhayyim.openrouter -w"
        )

    agent_dir = _find_agent_dir()
    if agent_dir is None:
        raise click.ClickException(
            "terminal-agent directory not found. Expected: <repo>/60-apps/etzhayyim-terminal-agent"
        )

    import os as _os
    work_path = str(Path(work_dir).resolve())
    resolved_model = model or _os.environ.get("AGENT_MODEL", "anthropic/claude-sonnet-4-6")
    uv_args = ["run", "agent", "--local", "--message", msg, "--dir", work_path]

    click.echo(f"==> etzhayyim code exec: model={resolved_model} dir={work_path}", err=True)
    if dry_run:
        click.echo(f"==> dry-run: {uv_bin} {' '.join(uv_args)}", err=True)
        return

    env = _os.environ.copy()
    env["OPENROUTER_API_KEY"] = resolved_key
    env["AGENT_MODEL"] = resolved_model
    subprocess.run([uv_bin] + uv_args, cwd=agent_dir, env=env)


@code.command("agent")
@click.option("--prompt", "prompt_text", default="", help="Initial prompt")
@click.option("--local", "run_local", is_flag=True, default=False, help="Run graph in-process")
@click.option("--agent-server", default="http://localhost:2024", show_default=True)
@click.option("--model", default="", help="Override model")
@click.option("--dry-run", is_flag=True, default=False)
def code_agent(prompt_text: str, run_local: bool, agent_server: str, model: str, dry_run: bool) -> None:
    """Launch the terminal-agent (LangGraph)."""
    agent_dir = _find_agent_dir()
    if agent_dir is None:
        click.echo(
            "error: etzhayyim-terminal-agent directory not found. "
            "Check that 60-apps/etzhayyim-terminal-agent exists in the git root.",
            err=True,
        )
        sys.exit(1)

    cmd = ["uv", "run", "agent"] + (["--local"] if run_local else [])

    env = {**os.environ}
    if model:
        env["AGENT_MODEL"] = model
    env["AGENT_SERVER"] = agent_server

    if dry_run:
        click.echo(f"would run: {' '.join(cmd)} (cwd={agent_dir})")
        click.echo(f"  AGENT_SERVER={env['AGENT_SERVER']}")
        if model:
            click.echo(f"  AGENT_MODEL={env['AGENT_MODEL']}")
        return

    subprocess.run(cmd, cwd=agent_dir, env=env)


@code.command("bench")
@click.option("--runs", default=3, type=int, show_default=True)
@click.option("--model", default="", help="Override model")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--dry-run", is_flag=True, default=False)
def code_bench(runs: int, model: str, json_out: bool, dry_run: bool) -> None:
    """Run benchmark suite in terminal-agent app."""
    agent_dir = _find_agent_dir()
    if agent_dir is None:
        raise click.ClickException(
            "terminal-agent directory not found. Expected: <repo>/60-apps/etzhayyim-terminal-agent"
        )
    import os as _os
    env = _os.environ.copy()
    if model:
        env["AGENT_MODEL"] = model
    cmd = ["uv", "run", "bench", f"--runs={runs}"]
    if json_out:
        cmd.append("--json")
    if dry_run:
        click.echo(f"[dry-run] {' '.join(cmd)}")
        click.echo(f"         cwd={agent_dir}")
        return
    subprocess.run(cmd, cwd=agent_dir, env=env)


# ── performance-test ───────────────────────────────────────────────────────────

@click.group("performance-test", invoke_without_command=True)
@click.pass_context
def performance_test(ctx: click.Context) -> None:
    """PDS XRPC endpoint performance measurement."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _parse_duration(dur: str) -> int:
    """Parse duration string like '30s', '2m', '1h' into seconds (max 300)."""
    dur = dur.strip().lower()
    if dur.endswith("h"):
        secs = int(dur[:-1]) * 3600
    elif dur.endswith("m"):
        secs = int(dur[:-1]) * 60
    elif dur.endswith("s"):
        secs = int(dur[:-1])
    else:
        secs = int(dur)
    return min(secs, 300)


@performance_test.command("run")
@click.option("--target", default="", help="PDS base URL (default: https://mod.etzhayyim.com)")
@click.option("--rps", default=10, type=int, show_default=True, help="Requests per second")
@click.option("--duration", default="30s", show_default=True, help="Test duration (e.g. 30s, 2m)")
@click.option("--endpoint", default="/health", show_default=True, help="Endpoint path to test")
@click.option("--json", "json_out", is_flag=True, default=False)
def pt_run(target: str, rps: int, duration: str, endpoint: str, json_out: bool) -> None:
    """Run concurrent HTTP load test against PDS endpoint."""
    import json as _json
    import time

    import httpx

    auth = _load_auth()
    base = (target or auth.get("pds_url", "https://mod.etzhayyim.com")).rstrip("/")
    url = base + endpoint
    duration_secs = _parse_duration(duration)

    latencies: list[float] = []
    errors = 0
    lock = threading.Lock()

    def _do_request() -> None:
        nonlocal errors
        t0 = time.perf_counter()
        try:
            httpx.get(url, timeout=10.0)
            ms = (time.perf_counter() - t0) * 1000
            with lock:
                latencies.append(ms)
        except Exception:
            with lock:
                errors += 1

    deadline = time.monotonic() + duration_secs
    threads: list[threading.Thread] = []
    while time.monotonic() < deadline:
        tick_start = time.monotonic()
        batch: list[threading.Thread] = []
        for _ in range(rps):
            t = threading.Thread(target=_do_request, daemon=True)
            t.start()
            batch.append(t)
        threads.extend(batch)
        # Sleep remainder of the second
        elapsed = time.monotonic() - tick_start
        remaining = 1.0 - elapsed
        if remaining > 0:
            time.sleep(remaining)

    for t in threads:
        t.join(timeout=15)

    total = len(latencies) + errors
    error_rate = (errors / total * 100) if total else 0.0

    if latencies:
        avg_ms = round(statistics.mean(latencies), 1)
        sorted_l = sorted(latencies)
        p50_ms = round(statistics.median(sorted_l), 1)
        p95_ms = round(sorted_l[max(0, int(len(sorted_l) * 0.95) - 1)], 1)
        p99_ms = round(sorted_l[max(0, int(len(sorted_l) * 0.99) - 1)], 1)
    else:
        avg_ms = p50_ms = p95_ms = p99_ms = 0.0

    if p95_ms < 500 and error_rate < 5:
        verdict = "PASS"
    elif p95_ms < 1000 and error_rate < 10:
        verdict = "WARN"
    else:
        verdict = "FAIL"

    stats = {
        "target": url,
        "duration": duration,
        "rps_target": rps,
        "total": total,
        "errors": errors,
        "error_rate": round(error_rate, 1),
        "avg_ms": avg_ms,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "p99_ms": p99_ms,
        "verdict": verdict,
    }

    if json_out:
        click.echo(_json.dumps(stats, ensure_ascii=False))
        return

    click.echo(f"Performance Test: {url}")
    click.echo("─" * 40)
    click.echo(f"{'duration:':<14}{duration}")
    click.echo(f"{'rps_target:':<14}{rps}")
    click.echo(f"{'total:':<14}{total}")
    click.echo(f"{'errors:':<14}{errors} ({error_rate:.1f}%)")
    click.echo(f"{'avg_ms:':<14}{avg_ms}")
    click.echo(f"{'p50_ms:':<14}{p50_ms}")
    click.echo(f"{'p95_ms:':<14}{p95_ms}")
    click.echo(f"{'p99_ms:':<14}{p99_ms}")
    click.echo(f"{'verdict:':<14}{verdict}")


@performance_test.command("report")
@click.option("--target", default="", help="PDS base URL")
@click.option("--json", "json_out", is_flag=True, default=False)
def pt_report(target: str, json_out: bool) -> None:
    """Quick single-round latency report (1 req per endpoint)."""
    import json as _json
    import time

    import httpx

    auth = _load_auth()
    base = (target or auth.get("pds_url", "https://mod.etzhayyim.com")).rstrip("/")

    endpoints = [
        ("/health", "health"),
        ("/xrpc/app.bsky.feed.getTimeline", "getTimeline"),
        ("/xrpc/com.atproto.server.describeServer", "describeServer"),
        ("/xrpc/app.bsky.actor.getProfile?actor=test", "getProfile"),
    ]

    headers: dict[str, str] = {}
    access_jwt = auth.get("access_jwt")
    if access_jwt:
        headers["Authorization"] = f"Bearer {access_jwt}"

    rows = []
    for path, name in endpoints:
        t0 = time.perf_counter()
        try:
            resp = httpx.get(base + path, headers=headers, timeout=10.0)
            ms = round((time.perf_counter() - t0) * 1000, 1)
            status = resp.status_code
        except Exception as exc:
            ms = 0.0
            status = f"ERR: {exc}"
        rows.append({"endpoint": name, "status": status, "latency_ms": ms})

    if json_out:
        click.echo(_json.dumps(rows, ensure_ascii=False))
        return

    header = f"{'endpoint':<30}{'status':>8}{'latency_ms':>12}"
    click.echo(header)
    click.echo("─" * len(header))
    for r in rows:
        click.echo(f"{r['endpoint']:<30}{str(r['status']):>8}{r['latency_ms']:>12.1f}")


# ── common-crawler ─────────────────────────────────────────────────────────────

def _cc_data_dir() -> str:
    return os.environ.get("CC_DATA_DIR", "/Volumes/251220/CC/2603")


def _cc_python() -> str:
    return os.path.join(_cc_data_dir(), ".venv", "bin", "python3")


def _cc_script(name: str) -> str:
    return os.path.join(_cc_data_dir(), "scripts", name)


def _cc_project_script(name: str) -> str:
    """Resolve script from monorepo project dir first, then CC_DATA_DIR/scripts/."""
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
        ).strip().decode()
        candidates = [
            os.path.join(repo_root, "60-apps", "etzhayyim-project-common-crawl", "scripts", name),
            os.path.join(repo_root, "projects", "etzhayyim-project-common-crawl", "scripts", name),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
    except Exception:
        pass
    return _cc_script(name)


def _cc_exec(py_args: list[str], env: dict | None = None) -> None:
    python = _cc_python()
    if not os.path.exists(python):
        raise click.ClickException(
            f"venv python not found at {python}\n"
            f"Run: python3 -m venv {_cc_data_dir()}/.venv && "
            f"{_cc_data_dir()}/.venv/bin/pip install warcio requests httpx"
        )
    merged = {**os.environ, **(env or {})}
    result = subprocess.run([python, *py_args], env=merged)
    sys.exit(result.returncode)


@click.group("common-crawler")
def common_crawler() -> None:
    """Common Crawl pipeline: download WAT/WET, build property graph, extract intel."""


@common_crawler.command("download")
@click.option("--workers", default=4, show_default=True)
@click.option("--wat-only", "wat_only", is_flag=True, default=False)
@click.option("--wet-only", "wet_only", is_flag=True, default=False)
@click.option("--resume/--no-resume", default=True, show_default=True)
@click.option("--crawl", default="CC-MAIN-2026-12", show_default=True)
@click.option("--format", "fmt", default="wat,wet", show_default=True)
@click.option("--domains", default="", help="domain filter file (one domain per line)")
@click.option("--range-start", "range_start", default=0, type=int)
@click.option("--range-end", "range_end", default=0, type=int)
def cc_download(workers: int, wat_only: bool, wet_only: bool, resume: bool,
                crawl: str, fmt: str, domains: str, range_start: int, range_end: int) -> None:
    """Download WAT/WET files from Common Crawl S3."""
    py_args = [_cc_script("download_all.py")]
    if wat_only:
        py_args.append("--wat-only")
    if wet_only:
        py_args.append("--wet-only")
    if resume:
        py_args.append("--resume")
    py_args += ["--workers", str(workers)]
    env: dict = {"CC_CRAWL_ID": crawl, "CC_FORMATS": fmt}
    if domains:
        env["CC_DOMAINS_FILE"] = domains
    if range_start > 0:
        env["CC_RANGE_START"] = str(range_start)
    if range_end > 0:
        env["CC_RANGE_END"] = str(range_end)
    click.echo(f"▶ common-crawler download: {crawl} format={fmt} workers={workers}")
    if domains:
        click.echo(f"  domain filter: {domains}")
    _cc_exec(py_args, env)


@common_crawler.command("graph")
@click.option("--source", default="full", show_default=True, help="WAT source: full or filtered")
@click.option("--batch-size", "batch_size", default=5000, type=int, show_default=True)
@click.option("--output", default="sql", show_default=True, help="sql, jsonl, parquet")
@click.option("--domain", "domain_filter", default="", help="filter by domain pattern")
@click.option("--crawl", default="CC-MAIN-2026-12", show_default=True)
def cc_graph(source: str, batch_size: int, output: str, domain_filter: str, crawl: str) -> None:
    """Build DID property graph from WAT files."""
    py_args = [
        _cc_project_script("phase3_wat_to_sql.py"),
        "--source", source,
        "--batch-size", str(batch_size),
    ]
    if domain_filter:
        py_args += ["--domain", domain_filter]
    env: dict = {"CC_OUTPUT_FORMAT": output, "CC_CRAWL_ID": crawl}
    if domain_filter:
        env["CC_DOMAIN_FILTER"] = domain_filter
    click.echo(f"▶ common-crawler graph: {crawl} → DID property graph (source={source}, format={output})")
    _cc_exec(py_args, env)


@common_crawler.command("intel")
@click.option("--limit", default=0, type=int, help="max domains to process (0=all)")
@click.option("--resume", is_flag=True, default=False)
@click.option("--model", default="qwen3.5-9b", show_default=True)
@click.option("--min-pages", "min_pages", default=0, type=int)
@click.option("--domain", "domain_filter", default="")
@click.option("--output", default="jsonl", show_default=True, help="jsonl, sql, parquet")
@click.option("--concurrency", default=1, type=int, show_default=True)
def cc_intel(limit: int, resume: bool, model: str, min_pages: int,
             domain_filter: str, output: str, concurrency: int) -> None:
    """Extract intelligence from crawl pages using Murakumo LLM."""
    py_args = [_cc_script("phase4_intel_extract.py")]
    if limit > 0:
        py_args += ["--limit", str(limit)]
    if resume:
        py_args.append("--resume")
    env: dict = {
        "MURAKUMO_MODEL": model,
        "CC_OUTPUT_FORMAT": output,
        "CC_CONCURRENCY": str(concurrency),
    }
    if min_pages > 0:
        env["CC_MIN_PAGES"] = str(min_pages)
    if domain_filter:
        env["CC_DOMAIN_FILTER"] = domain_filter
    click.echo(f"▶ common-crawler intel: {model} (limit={limit}, min-pages={min_pages}, format={output})")
    _cc_exec(py_args, env)


@common_crawler.command("inject")
@click.option("--source", default="intel", show_default=True)
@click.option("--batch-size", "batch_size", default=500, type=int, show_default=True)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--pds", default=None)
def cc_inject(source: str, batch_size: int, dry_run: bool, pds: str | None) -> None:
    """[deprecated] Use: etzhayyim domain-ingest common-crawl"""
    click.echo("warning: 'etzhayyim common-crawler inject' is deprecated; use 'etzhayyim domain-ingest common-crawl' instead", err=True)
    cmd = [sys.executable, "-m", "etzhayyim", "domain-ingest", "common-crawl",
           "--source", source, "--batch-size", str(batch_size)]
    if dry_run:
        cmd.append("--dry-run")
    if pds:
        cmd += ["--pds", pds]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


@common_crawler.command("monitor")
def cc_monitor() -> None:
    """Show Common Crawl pipeline status (disk usage, log tail, process check)."""
    _cc_monitor_impl()


@common_crawler.command("status")
def cc_status() -> None:
    """Alias for monitor."""
    _cc_monitor_impl()


def _cc_monitor_impl() -> None:
    import shutil
    data_dir = _cc_data_dir()
    scripts_dir = os.path.join(data_dir, "scripts")

    click.echo("═══ Common Crawl Pipeline Monitor ═══")
    click.echo(f"Data dir: {data_dir}")
    import datetime
    click.echo(f"Time:     {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def show_log_tail(path: str, n: int = 2) -> None:
        try:
            lines = Path(path).read_text(errors="replace").splitlines()
            for line in lines[-n:]:
                click.echo(f"  {line}")
        except OSError:
            click.echo(f"  (no log: {os.path.basename(path)})")

    def show_disk(path: str) -> None:
        try:
            total = sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())
            click.echo(f"  {path}: {total / 1024 / 1024:.1f} MB")
        except OSError:
            click.echo(f"  {path}: (not found)")

    def show_count(path: str, pattern: str) -> None:
        try:
            count = len(list(Path(path).glob(pattern)))
            click.echo(f"  {pattern} count: {count}")
        except OSError:
            pass

    def check_process(script: str) -> None:
        try:
            out = subprocess.check_output(["pgrep", "-f", script], stderr=subprocess.DEVNULL)
            pids = out.decode().strip().split()
            click.echo(f"  {script}: running (pid {','.join(pids)})")
        except subprocess.CalledProcessError:
            click.echo(f"  {script}: not running")

    click.echo("── Download ──")
    show_log_tail(os.path.join(scripts_dir, "download.log"))
    show_disk(os.path.join(data_dir, "wat-full"))
    show_count(os.path.join(data_dir, "wat-full"), "*.gz")

    click.echo("\n── Filtered ──")
    show_disk(os.path.join(data_dir, "filtered/wat"))
    show_disk(os.path.join(data_dir, "filtered/wet"))

    click.echo("\n── DID Property Graph ──")
    show_log_tail(os.path.join(scripts_dir, "phase3v2.log"))
    show_count(os.path.join(data_dir, "graph"), "did_batch_*.sql")
    show_disk(os.path.join(data_dir, "graph"))

    click.echo("\n── Intelligence Extraction ──")
    show_log_tail(os.path.join(scripts_dir, "phase4v3.log"))

    click.echo("\n── State ──")
    for sf in [".download_state.json", ".phase4v3_state.json"]:
        path = os.path.join(scripts_dir, sf)
        try:
            st = Path(path).stat()
            import datetime
            mtime = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%H:%M:%S")
            click.echo(f"  {sf}: {mtime} ({st.st_size / 1024:.0f} KB)")
        except OSError:
            pass

    click.echo("\n── Processes ──")
    for script in ["download_all.py", "phase3_did_property_graph.py", "phase4_intel_extract.py"]:
        check_process(script)


@common_crawler.command("purge")
@click.option("--phase", required=True, type=click.Choice(["download", "graph", "intel", "all"]))
def cc_purge(phase: str) -> None:
    """Purge pipeline state files (download/graph/intel/all)."""
    data_dir = _cc_data_dir()
    scripts_dir = os.path.join(data_dir, "scripts")
    phase_files: dict[str, list[str]] = {
        "download": [os.path.join(scripts_dir, ".download_state.json")],
        "graph": [os.path.join(scripts_dir, ".phase3v2_state.json")],
        "intel": [
            os.path.join(scripts_dir, ".phase4v3_state.json"),
            os.path.join(data_dir, "graph", "domain_intel.jsonl.gz"),
            os.path.join(data_dir, "graph", "knowledge_graph.sql"),
        ],
    }
    files = []
    if phase == "all":
        for fs in phase_files.values():
            files.extend(fs)
    else:
        files = phase_files.get(phase, [])
    for f in files:
        try:
            os.remove(f)
            click.echo(f"  removed: {os.path.basename(f)}")
        except OSError:
            pass
    click.echo(f"Purged state for phase: {phase}")


@common_crawler.command("list-crawls")
@click.option("--year", default=0, type=int, help="filter by year (e.g., 2026)")
@click.option("--json", "json_out", is_flag=True, default=False)
def cc_list_crawls(year: int, json_out: bool) -> None:
    """List available Common Crawl crawl IDs from index.commoncrawl.org."""
    py_args = [_cc_script("list_crawls.py")]
    if year > 0:
        py_args += ["--year", str(year)]
    if json_out:
        py_args.append("--json")
    click.echo("▶ common-crawler list-crawls: querying index.commoncrawl.org")
    _cc_exec(py_args)


# ── docs / docs-gen ────────────────────────────────────────────────────────────

def _find_git_root_docs() -> Path | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                      stderr=subprocess.DEVNULL)
        return Path(out.strip().decode())
    except Exception:
        return None


def _is_date(s: str) -> bool:
    if len(s) != 10:
        return False
    return s[4] == "-" and s[7] == "-" and s[:4].isdigit() and s[5:7].isdigit() and s[8:].isdigit()


def _parse_front_matter(path: Path) -> tuple[dict, str | None]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {}, str(e)
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "missing YAML front matter opening delimiter"
    end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end == -1:
        return {}, "missing YAML front matter closing delimiter"

    result: dict = {}
    i = 1
    while i < end:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if ":" not in stripped:
            i += 1
            continue
        colon = line.index(":")
        key = line[:colon].strip()
        raw = line[colon + 1:].strip()
        if raw:
            if raw in ("true", "True"):
                result[key] = True
            elif raw in ("false", "False"):
                result[key] = False
            elif raw.startswith('"') and raw.endswith('"'):
                result[key] = raw[1:-1]
            elif raw.startswith("'") and raw.endswith("'"):
                result[key] = raw[1:-1]
            else:
                result[key] = raw
            i += 1
        else:
            lst: list[str] = []
            i += 1
            while i < end:
                child = lines[i]
                child_stripped = child.strip()
                if not child_stripped:
                    i += 1
                    continue
                if child_stripped.startswith("- "):
                    lst.append(child_stripped[2:].strip())
                    i += 1
                else:
                    break
            result[key] = lst
    return result, None


def _docs_validate_impl(repo_root: Path) -> list[str]:
    errs: list[str] = []

    # Support both docs/ and 90-docs/ layout
    docs_dir = repo_root / "90-docs"
    if not docs_dir.exists():
        docs_dir = repo_root / "docs"

    registry_path = docs_dir / "_registry" / "docs.json"

    if not registry_path.exists():
        errs.append(f"required file missing: {registry_path.relative_to(repo_root)}")

    if errs:
        return errs

    try:
        registry = json.loads(registry_path.read_text())
    except Exception as e:
        return [f"parse docs registry: {e}"]

    if registry.get("version", 0) < 1:
        errs.append("docs registry version must be >= 1")
    if not _is_date(str(registry.get("updated_at", ""))):
        errs.append(f"docs registry updated_at has invalid format: {registry.get('updated_at')!r}")

    allowed_status = {"active", "deprecated", "superseded", "proposed"}
    allowed_doc_types = {"explanation", "reference", "how-to", "tutorial", "adr"}

    by_id: dict[str, dict] = {}
    authoritative_topics: dict[str, str] = {}
    for entry in registry.get("entries", []):
        eid = entry.get("id", "")
        if not eid:
            errs.append("registry entry has empty id")
            continue
        if eid in by_id:
            errs.append(f"duplicate registry id: {eid}")
            continue
        by_id[eid] = entry
        epath = entry.get("path", "")
        if not epath or not epath.endswith(".md"):
            errs.append(f"registry entry {eid} has invalid path: {epath}")
        elif not (repo_root / epath).exists():
            errs.append(f"registry entry {eid} points to missing file: {epath}")
        if not entry.get("title"):
            errs.append(f"registry entry {eid} has empty title")
        if entry.get("status") not in allowed_status:
            errs.append(f"registry entry {eid} has invalid status: {entry.get('status')}")
        if entry.get("doc_type") not in allowed_doc_types:
            errs.append(f"registry entry {eid} has invalid doc_type: {entry.get('doc_type')}")
        if not entry.get("topic"):
            errs.append(f"registry entry {eid} has empty topic")
        if entry.get("authoritative"):
            topic = entry.get("topic", "")
            if topic in authoritative_topics:
                errs.append(f"topic {topic!r} has more than one authoritative doc: "
                            f"{authoritative_topics[topic]}, {eid}")
            else:
                authoritative_topics[topic] = eid

    # Validate front matter for each entry
    for eid, entry in by_id.items():
        epath = entry.get("path", "")
        if not epath or not (repo_root / epath).exists():
            continue
        fm, err = _parse_front_matter(repo_root / epath)
        if err:
            errs.append(f"{epath}: {err}")
            continue
        for key in ["id", "title", "status", "doc_type", "topic", "authoritative", "last_verified"]:
            if key not in fm:
                errs.append(f"{epath}: missing front matter key {key!r}")
        if not _is_date(str(fm.get("last_verified", ""))):
            errs.append(f"{epath}: front matter last_verified has invalid format: {fm.get('last_verified')!r}")

    # The relation graph (90-docs/_registry/graph.edn) is a pure deterministic
    # projection of docs.edn by regen-graph-edn.clj — the registry↔graph 1:1
    # invariant is guaranteed by construction + docs-graph-edn-freshness, so no
    # separate cross-check is done here. (Was a graph.jsonld cross-check before
    # the JSON-LD → EDN migration.)

    return sorted(errs)


@click.group("docs")
def docs() -> None:
    """Documentation commands."""


@docs.command("validate")
@click.option("--workspace-dir", default=None, help="repo root (default: git root)")
def docs_validate(workspace_dir: str | None) -> None:
    """Validate docs registry against registry JSON + front matter."""
    if workspace_dir:
        root = Path(workspace_dir)
    else:
        root = _find_git_root_docs()
    if root is None or not root.exists():
        raise click.ClickException("could not find git root; use --workspace-dir")
    errs = _docs_validate_impl(root)
    if errs:
        for e in errs:
            click.echo(f"  ERROR: {e}", err=True)
        raise click.ClickException(f"{len(errs)} validation error(s)")
    click.echo("docs registry validation passed")


@docs.command("generate")
@click.argument("path", default=".")
def docs_generate(path: str) -> None:
    """Generate documentation (requires Go binary + LLM)."""
    _go_stub("docs generate", "Requires LLM access.")


@click.group("docs-gen")
def docs_gen() -> None:
    """Auto-generate factual schema docs from local sources."""


def _strip_jsonc_comments(src: str) -> str:
    result: list[str] = []
    in_string = False
    i = 0
    while i < len(src):
        c = src[i]
        if in_string:
            if c == "\\" and i + 1 < len(src):
                result.append(c)
                result.append(src[i + 1])
                i += 2
                continue
            if c == '"':
                in_string = False
            result.append(c)
            i += 1
            continue
        if c == '"':
            in_string = True
            result.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < len(src) and src[i + 1] == "/":
            while i < len(src) and src[i] != "\n":
                i += 1
            continue
        result.append(c)
        i += 1
    return "".join(result)


def _scan_wrangler_bindings(project_dir: Path) -> list[str]:
    import re
    wrangler = project_dir / "wrangler.jsonc"
    if not wrangler.exists():
        return []
    stripped = _strip_jsonc_comments(wrangler.read_text(encoding="utf-8", errors="replace"))
    matches = re.findall(r'"binding"\s*:\s*"([^"]+)"', stripped)
    seen: set[str] = set()
    bindings: list[str] = []
    for b in matches:
        if b not in seen:
            seen.add(b)
            bindings.append(b)
    return sorted(bindings)


def _scan_ts_graph_labels(project_dir: Path) -> list[str]:
    import re
    _G_LABEL_RE = re.compile(r'G\(\s*["\']([A-Z][a-zA-Z0-9]*)["\']')
    src_dir = project_dir / "src"
    if not src_dir.is_dir():
        return []
    seen: set[str] = set()
    labels: list[str] = []
    for f in sorted(src_dir.iterdir()):
        if f.is_file() and f.suffix == ".ts":
            text = f.read_text(encoding="utf-8", errors="replace")
            for m in _G_LABEL_RE.finditer(text):
                lbl = m.group(1)
                if lbl not in seen:
                    seen.add(lbl)
                    labels.append(lbl)
    return sorted(labels)


def _scan_app_schema(project_dir: Path) -> dict:
    import datetime
    import json as _json
    manifest_path = project_dir / "kotodama.jsonld"
    if not manifest_path.exists():
        raise click.ClickException(f"kotodama.jsonld not found in {project_dir}")
    manifest = _json.loads(manifest_path.read_text(encoding="utf-8"))

    schema: dict = {
        "app": manifest.get("name", ""),
        "scannedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if manifest.get("nanoid"):
        schema["nanoid"] = manifest["nanoid"]
    if manifest.get("@id") or manifest.get("id"):
        schema["did"] = manifest.get("@id") or manifest.get("id")
    if manifest.get("project"):
        schema["project"] = manifest["project"]
    if manifest.get("performerType"):
        schema["performerType"] = manifest["performerType"]

    # Collections from triggers.subscribeRepos
    triggers = manifest.get("triggers", {})
    subscribe = triggers.get("subscribeRepos", {}) if triggers else {}
    colls = subscribe.get("collections", []) if subscribe else []
    if colls:
        schema["collections"] = colls

    # Service bindings from wrangler.jsonc
    bindings = _scan_wrangler_bindings(project_dir)
    schema["serviceBindings"] = bindings if bindings else ["HYPERDRIVE", "PDS_SERVICE"]

    # Graph labels from src/*.ts
    labels = _scan_ts_graph_labels(project_dir)
    if labels:
        schema["graphLabels"] = labels

    return schema


def _render_schema_md(s: dict) -> str:
    lines = [
        "<!-- AUTO-GENERATED by etzhayyim docs-gen schema. Regenerate: etzhayyim docs-gen schema --dir . --format md --out schema.auto.md -->",
        f"<!-- scannedAt: {s.get('scannedAt', '')} -->",
        "",
        f"## Schema: {s.get('app', '')}",
        "",
        "### App",
        "",
        "| Key | Value |",
        "|---|---|",
        f"| **name** | `{s.get('app', '')}` |",
    ]
    for key in ("nanoid", "did", "project", "performerType"):
        if s.get(key):
            lines.append(f"| **{key}** | `{s[key]}` |")
    lines.append("")

    if s.get("collections"):
        lines += ["### Collections", ""]
        for c in s["collections"]:
            lines.append(f"- `{c}`")
        lines.append("")

    if s.get("graphLabels"):
        lines += ["### Graph Labels (G() scan)", ""]
        for lbl in s["graphLabels"]:
            lines.append(f"- `:{lbl}`")
        lines.append("")

    if s.get("serviceBindings"):
        lines += ["### Service Bindings", ""]
        for b in s["serviceBindings"]:
            lines.append(f"- `{b}`")
        lines.append("")

    return "\n".join(lines).rstrip()


@docs_gen.command("schema")
@click.option("--dir", "component_dir", default=".", show_default=True,
              help="project directory containing kotodama.jsonld")
@click.option("--all", "scan_all", is_flag=True, default=False,
              help="scan all projects under 60-apps/ and write schema.auto.md per project")
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "md"]),
              show_default=True, help="output format")
@click.option("--out", "out_path", default="", help="output file path (default: stdout)")
def docs_gen_schema(component_dir: str, scan_all: bool, fmt: str, out_path: str) -> None:
    """Generate schema.auto.md / JSON from kotodama.jsonld + src scan."""
    import json as _json

    if scan_all:
        git_root = _find_git_root_docs()
        if git_root is None:
            raise click.ClickException("--all requires a git repository")
        pattern_dir = git_root / "60-apps"
        if not pattern_dir.is_dir():
            raise click.ClickException(f"60-apps/ not found under {git_root}")
        wrote = skipped = 0
        for manifest in sorted(pattern_dir.glob("etzhayyim-project-*/wasm/*/kotodama.jsonld")):
            comp = manifest.parent
            if ".etzhayyim-deploy" in str(comp):
                continue
            try:
                schema = _scan_app_schema(comp)
            except Exception as exc:
                click.echo(f"docs-gen: skip {comp}: {exc}", err=True)
                skipped += 1
                continue
            out = comp / "schema.auto.md"
            out.write_text(_render_schema_md(schema) + "\n", encoding="utf-8")
            wrote += 1
        click.echo(f"docs-gen schema --all: wrote {wrote}, skipped {skipped}", err=True)
        return

    comp = Path(component_dir).resolve()
    schema = _scan_app_schema(comp)
    if fmt == "md":
        rendered = _render_schema_md(schema)
    else:
        rendered = _json.dumps(schema, indent=2, ensure_ascii=False)

    if out_path:
        Path(out_path).write_text(rendered + "\n", encoding="utf-8")
    else:
        click.echo(rendered)


# ── migrate-manifest ──────────────────────────────────────────────────────────

@click.group("migrate-manifest")
def migrate_manifest() -> None:
    """Migration manifest management."""


def _parse_toml_array(s: str) -> list[str]:
    """Parse a simple TOML array like ["a", "b", "c"]."""
    s = s.strip()
    if "]" not in s:
        return []
    s = s.lstrip("[").rstrip("]").strip()
    if not s:
        return []
    result = []
    for item in s.split(","):
        item = item.strip().strip("\"'").rstrip(",").strip()
        if item:
            result.append(item)
    return result


def _parse_legacy_toml(content: str, manifest: dict) -> None:
    """Parse kotodama.toml line-by-line and populate the manifest dict."""
    section = ""
    channels: list[dict] = []
    current_channel: dict | None = None

    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue

        if trimmed.startswith("["):
            if current_channel is not None:
                channels.append(current_channel)
                current_channel = None

            if trimmed == "[component]":
                section = "component"
                manifest.setdefault("component", {})
            elif trimmed == "[component.env]":
                section = "component.env"
                manifest.setdefault("component", {})
                manifest["component"].setdefault("env", {})
            elif trimmed == "[component.compose]":
                section = "component.compose"
            elif trimmed == "[triggers.http]":
                section = "triggers.http"
                manifest.setdefault("triggers", {})
                manifest["triggers"].setdefault("http", {})
            elif trimmed == "[triggers.w_commit]":
                section = "triggers.w_commit"
                manifest.setdefault("triggers", {})
                manifest["triggers"].setdefault("subscribeRepos", {})
            elif trimmed == "[ui]":
                section = "ui"
                manifest.setdefault("ui", {})
            elif trimmed == "[ui.ssr_routes]":
                section = "ui.ssr_routes"
                manifest.setdefault("ui", {})
                manifest["ui"].setdefault("ssrRoutes", {})
            elif trimmed == "[game]":
                section = "game"
                manifest.setdefault("game", {})
            elif trimmed == "[space]":
                section = "space"
                manifest.setdefault("space", {})
            elif trimmed == "[[space.channels]]":
                section = "space.channels"
                manifest.setdefault("space", {})
                current_channel = {"kind": "public"}
            elif trimmed == "[evolver]":
                section = "evolver"
                manifest.setdefault("evolver", {})
            elif trimmed == "[pool]":
                section = "pool"
                manifest.setdefault("pool", {})
            elif trimmed == "[[extensions]]":
                section = "extensions"
                manifest.setdefault("extensions", [])
                manifest["extensions"].append({})
            elif trimmed == "[interfaces]":
                section = "interfaces"
                manifest.setdefault("interfaces", {})
            else:
                section = ""
            continue

        parts = trimmed.split("=", 1)
        if len(parts) != 2:
            continue
        key = parts[0].strip()
        val = parts[1].strip()
        # strip inline comments
        comment_idx = val.find(" #")
        if comment_idx >= 0:
            val = val[:comment_idx].strip()
        val = val.strip("\"'")

        if section == "component":
            if key == "path":
                manifest["component"]["path"] = val
        elif section == "component.env":
            manifest["component"]["env"][key] = val
        elif section == "component.compose":
            if key == "signal":
                manifest["component"]["compose"] = {"signal": val}
        elif section == "triggers.http":
            http = manifest["triggers"]["http"]
            if key == "listen":
                http["listen"] = val
            elif key == "routes":
                http["routes"] = _parse_toml_array(val)
            elif key == "static_dir":
                http["staticDir"] = val
            elif key == "spa":
                http["spa"] = val == "true"
        elif section == "triggers.w_commit":
            if key == "collections":
                manifest["triggers"]["subscribeRepos"]["collections"] = _parse_toml_array(val)
        elif section == "ui":
            ui = manifest["ui"]
            if key == "mode":
                manifest["uiType"] = "appview" if val in ("custom", "full") else val
            elif key == "accent":
                ui["accent"] = val
            elif key == "icon":
                ui["icon"] = val
        elif section == "ui.ssr_routes":
            manifest["ui"]["ssrRoutes"][key] = val
        elif section == "game":
            game = manifest["game"]
            if key == "runtime":
                game["runtime"] = val
            elif key == "entry":
                game["entry"] = val
        elif section == "space":
            space = manifest["space"]
            if key == "name":
                space["name"] = val
            elif key == "description":
                space["description"] = val
            elif key == "join_rule":
                space["joinRule"] = val
            elif key == "history_visibility":
                space["historyVisibility"] = val
        elif section == "space.channels" and current_channel is not None:
            if key == "name":
                current_channel["name"] = val
            elif key == "kind":
                current_channel["kind"] = val
            elif key == "description":
                current_channel["description"] = val
            elif key == "default":
                current_channel["default"] = val == "true"
        elif section == "evolver":
            evolver = manifest["evolver"]
            if key == "murakumo_endpoint":
                evolver["murakumoEndpoint"] = val
            elif key == "murakumo_model":
                evolver["murakumoModel"] = val
        elif section == "extensions" and manifest.get("extensions"):
            ext = manifest["extensions"][-1]
            if key == "name":
                ext["name"] = val
            elif key == "package":
                ext["package"] = val
            elif key == "component":
                ext["component"] = val
            elif key == "kinds":
                ext["kinds"] = _parse_toml_array(val)
        elif section == "interfaces":
            if key == "package":
                manifest["interfaces"]["package"] = val

    if current_channel is not None:
        channels.append(current_channel)
    if channels and "space" in manifest:
        manifest["space"]["channels"] = channels


def _migrate_single(comp_dir: Path, dry_run: bool) -> bool:
    """Migrate a single component dir from etzhayyim.json → kotodama.jsonld."""
    jsonld_path = comp_dir / "kotodama.jsonld"
    if jsonld_path.exists() and not dry_run:
        click.echo(f"  skip {comp_dir.name} (kotodama.jsonld already exists)", err=True)
        return False

    etzhayyim_path = comp_dir / "etzhayyim.json"
    if not etzhayyim_path.exists():
        click.echo(f"  skip {comp_dir.name} (no etzhayyim.json)", err=True)
        return False

    try:
        etzhayyim = json.loads(etzhayyim_path.read_text(encoding="utf-8"))
    except Exception as exc:
        click.echo(f"  FAIL {comp_dir.name}: parse etzhayyim.json: {exc}", err=True)
        return False

    # Build host from routes or project/nanoid
    routes = etzhayyim.get("routes", [])
    host = ""
    if routes and isinstance(routes[0], dict):
        host = routes[0].get("host", "")
    if not host:
        project = etzhayyim.get("project", "")
        nanoid = etzhayyim.get("nanoid", "")
        host = f"{project}.etzhayyim.com" if project else f"{nanoid}.etzhayyim.com"

    rt = etzhayyim.get("runtime") or "worker"

    manifest: dict = {
        "@context": "https://etzhayyim.com/ns/kotodama/v1",
        "@id": f"did:web:{host}",
        "performerType": "service",
        "name": etzhayyim.get("name", ""),
        "nanoid": etzhayyim.get("nanoid", ""),
    }

    for key in ("project", "org", "version", "template", "source"):
        if etzhayyim.get(key):
            manifest[key] = etzhayyim[key]

    manifest["runtimeType"] = rt

    if routes:
        manifest["routes"] = routes

    hooks = etzhayyim.get("hooks", [])
    if hooks:
        manifest["hooks"] = hooks

    evolved_at = etzhayyim.get("evolved_at", "")
    if evolved_at:
        manifest["evolvedAt"] = evolved_at

    # Build config
    wit_world = etzhayyim.get("wit_world", "")
    guest_lang = etzhayyim.get("guest_language", "")
    wasi_ver = etzhayyim.get("wasi_adapter_version", "")
    if wit_world or guest_lang or wasi_ver:
        manifest["build"] = {k: v for k, v in {
            "witWorld": wit_world,
            "guestLanguage": guest_lang,
            "wasiAdapterVersion": wasi_ver,
        }.items() if v}

    # Deploy config
    dockerfile = etzhayyim.get("dockerfile", "")
    base_image = etzhayyim.get("base_image", "")
    health_check = etzhayyim.get("health_check", "")
    sleep_after = etzhayyim.get("sleep_after", "")
    if dockerfile or base_image or health_check or sleep_after:
        manifest["deploy"] = {k: v for k, v in {
            "dockerfile": dockerfile,
            "baseImage": base_image,
            "healthCheck": health_check,
            "sleepAfter": sleep_after,
        }.items() if v}

    # Parse kotodama.toml if it exists
    toml_path = comp_dir / "kotodama.toml"
    if toml_path.exists():
        try:
            _parse_legacy_toml(toml_path.read_text(encoding="utf-8"), manifest)
        except Exception as exc:
            click.echo(f"  WARN {comp_dir.name}: parse kotodama.toml: {exc}", err=True)

    # Remove None/empty values at top level
    manifest = {k: v for k, v in manifest.items() if v is not None and v != "" and v != [] and v != {}}

    output = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"

    if dry_run:
        click.echo(f"--- {comp_dir.name}/kotodama.jsonld ---")
        click.echo(output)
        return True

    try:
        jsonld_path.write_text(output, encoding="utf-8")
        click.echo(f"  migrated {comp_dir.name}", err=True)
        return True
    except Exception as exc:
        click.echo(f"  FAIL {comp_dir.name}: write: {exc}", err=True)
        return False


@migrate_manifest.command("run")
@click.option("--dir", "component_dir", default=".", show_default=True,
              help="Component directory (or parent directory with --batch)")
@click.option("--batch", is_flag=True, default=False,
              help="Migrate all subdirectories containing etzhayyim.json")
@click.option("--dry-run", is_flag=True, default=False,
              help="Show what would be generated without writing")
def mm_run(component_dir: str, batch: bool, dry_run: bool) -> None:
    """Migrate etzhayyim.json → kotodama.jsonld (pure file transformation, no DB)."""
    abs_dir = Path(component_dir).resolve()

    if batch:
        count = 0
        try:
            entries = sorted(abs_dir.iterdir())
        except OSError as exc:
            click.echo(f"error: {exc}", err=True)
            sys.exit(1)
        for entry in entries:
            if not entry.is_dir():
                continue
            if not (entry / "etzhayyim.json").exists():
                continue
            if _migrate_single(entry, dry_run):
                count += 1
        click.echo(f"==> migrated {count} apps", err=True)
    else:
        if not _migrate_single(abs_dir, dry_run):
            sys.exit(1)


# ── plugin ────────────────────────────────────────────────────────────────────

import platform as _platform
import shutil as _shutil
import tarfile as _tarfile
import tempfile as _tempfile
import urllib.request as _url_request

_PLUGIN_DEFS = [
    {
        "name": "wasm-tools",
        "description": "WebAssembly component toolchain (embed/new/print)",
        "latest_url": "https://api.github.com/repos/bytecodealliance/wasm-tools/releases/latest",
        "install_bin": "wasm-tools",
    },
]


def _plugin_cache_dir(name: str) -> Path:
    home = Path.home()
    return home / ".cache" / "etzhayyim" / "plugins" / name


def _plugin_bin_path(name: str, install_bin: str) -> Path:
    return _plugin_cache_dir(name) / install_bin


def _plugin_status(p: dict) -> tuple[bool, str]:
    """Return (installed, version) for a plugin."""
    bin_path = _plugin_bin_path(p["name"], p["install_bin"])
    if not bin_path.exists():
        return False, ""
    try:
        import subprocess as _sp
        out = _sp.check_output([str(bin_path), "--version"], stderr=_sp.STDOUT, text=True).strip()
        parts = out.split()
        return True, parts[-1] if len(parts) >= 2 else out
    except Exception:
        return True, "unknown"


def _fetch_latest_plugin_version(p: dict, timeout: int = 10) -> str:
    req = _url_request.Request(
        p["latest_url"],
        headers={"Accept": "application/vnd.github+json", "User-Agent": "etzhayyim-py/1.0"},
    )
    with _url_request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    tag = data.get("tag_name", "")
    return tag.lstrip("v")


def _wasm_tools_url(version: str) -> str:
    sys = _platform.system().lower()
    arch = _platform.machine().lower()
    if sys == "darwin":
        sys = "macos"
    if arch in ("x86_64", "amd64"):
        arch = "x86_64"
    elif arch in ("arm64", "aarch64"):
        arch = "aarch64"
    return (
        f"https://github.com/bytecodealliance/wasm-tools/releases/download/"
        f"v{version}/wasm-tools-{version}-{arch}-{sys}.tar.gz"
    )


def _install_plugin(p: dict, version: str) -> None:
    url = _wasm_tools_url(version)
    cache_dir = _plugin_cache_dir(p["name"])
    cache_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"==> downloading {p['name']} v{version}", err=True)
    click.echo(f"    {url}", err=True)

    with _tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        try:
            with _url_request.urlopen(url, timeout=120) as resp:
                if resp.status != 200:
                    raise click.ClickException(f"HTTP {resp.status} from {url}")
                tmp.write(resp.read())
        except Exception as exc:
            tmp_path.unlink(missing_ok=True)
            raise click.ClickException(f"download failed: {exc}") from exc

    try:
        click.echo(f"==> extracting {p['name']}", err=True)
        extract_dir = cache_dir / f"tmp-{version}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        with _tarfile.open(tmp_path, "r:gz") as tf:
            for member in tf.getmembers():
                # strip first path component
                parts = Path(member.name).parts
                if len(parts) > 1:
                    member.name = str(Path(*parts[1:]))
                elif len(parts) == 1:
                    member.name = parts[0]
                tf.extract(member, extract_dir)

        src_bin = extract_dir / p["install_bin"]
        dst_bin = _plugin_bin_path(p["name"], p["install_bin"])
        _shutil.copy2(src_bin, dst_bin)
        dst_bin.chmod(0o755)

        click.echo(f"==> installed {p['name']} v{version} → {dst_bin}", err=True)
        click.echo(f"    add to PATH: export PATH=\"{cache_dir}:$PATH\"", err=True)
    finally:
        tmp_path.unlink(missing_ok=True)
        try:
            _shutil.rmtree(extract_dir, ignore_errors=True)
        except Exception:
            pass


@click.group("plugin")
def plugin() -> None:
    """Manage build tools (wasm-tools, tinygo adapters)."""


@plugin.command("list")
def plugin_list() -> None:
    """List installed plugins and system tools."""
    click.echo(f"{'PLUGIN':<20} {'VERSION':<9} PATH")
    click.echo(f"{'------':<20} {'-------':<9} ----")
    for p in _PLUGIN_DEFS:
        installed, ver = _plugin_status(p)
        if installed:
            bin_path = _plugin_bin_path(p["name"], p["install_bin"])
            click.echo(f"{p['name']:<20} {ver:<9} {bin_path}")
        else:
            click.echo(f"{p['name']:<20} {'-':<9} (not installed)")
    for tool in ("tinygo", "docker"):
        path = _shutil.which(tool)
        if path:
            try:
                import subprocess as _sp
                out = _sp.check_output([tool, "--version"], stderr=_sp.STDOUT, text=True).strip()
                ver = out.split()[-1] if out.split() else "?"
            except Exception:
                ver = "?"
            click.echo(f"{tool:<20} {ver:<9} {path}")
        else:
            click.echo(f"{tool:<20} {'-':<9} (not found in PATH)")


@plugin.command("install")
@click.argument("plugin_name")
@click.option("--version", "version", default="", help="Specific version (default: latest)")
def plugin_install(plugin_name: str, version: str) -> None:
    """Install a plugin from GitHub releases."""
    p = next((x for x in _PLUGIN_DEFS if x["name"] == plugin_name), None)
    if p is None:
        click.echo(
            f"unknown plugin: {plugin_name}\nRun 'etzhayyim plugin list' to see available plugins",
            err=True,
        )
        sys.exit(1)
    ver = version
    if not ver:
        try:
            ver = _fetch_latest_plugin_version(p)
        except Exception as exc:
            raise click.ClickException(f"fetch latest version for {plugin_name}: {exc}") from exc
    _install_plugin(p, ver)


@plugin.command("upgrade")
@click.argument("plugin_name")
def plugin_upgrade(plugin_name: str) -> None:
    """Upgrade a plugin to latest version."""
    p = next((x for x in _PLUGIN_DEFS if x["name"] == plugin_name), None)
    if p is None:
        click.echo(f"unknown plugin: {plugin_name}", err=True)
        sys.exit(1)
    try:
        latest = _fetch_latest_plugin_version(p)
    except Exception as exc:
        raise click.ClickException(f"fetch latest version: {exc}") from exc
    installed, current = _plugin_status(p)
    if installed and current == latest:
        click.echo(f"{plugin_name} is already at latest version {latest}")
        return
    _install_plugin(p, latest)
