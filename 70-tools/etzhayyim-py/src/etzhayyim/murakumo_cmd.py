"""murakumo — LLM fleet management commands.

Full fleet orchestration (routing, load-balance, model swap) requires the Go binary.
status/list/infer operate via XRPC.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import click
import httpx

from .authn import _load_auth
from .projector import resolve_pds


def _auth_headers() -> dict:
    auth = _load_auth()
    tok = auth.get("accessJwt") or auth.get("access_token") or ""
    if not tok:
        click.echo("not signed in — run: etzhayyim authn signin", err=True)
        sys.exit(1)
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@click.group("murakumo")
def murakumo() -> None:
    """Murakumo LLM fleet management."""


@murakumo.command("status")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_status(pds: str | None, json_out: bool) -> None:
    """Fleet health and model availability."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.murakumo.getStatus",
                         headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"murakumo fleet: {data.get('status', 'unknown')}")
            for pod in data.get("pods", []):
                click.echo(f"  {pod.get('id', '')}  {pod.get('model', '')}  "
                           f"{pod.get('status', '')}  gpu={pod.get('gpu', '?')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@murakumo.command("list")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_list(pds: str | None, json_out: bool) -> None:
    """List all fleet pods."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.murakumo.listPods",
                         headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            pods = data if isinstance(data, list) else data.get("pods", [])
            for p in pods:
                click.echo(f"  {p.get('id', '')}  {p.get('model', '')}  {p.get('status', '')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@murakumo.command("infer")
@click.option("--prompt", required=True)
@click.option("--model", default="", help="Override model (default: fleet routing)")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_infer(prompt: str, model: str, pds: str | None, json_out: bool) -> None:
    """Send a single inference request to the fleet."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    payload: dict = {"prompt": prompt}
    if model:
        payload["model"] = model
    try:
        resp = httpx.post(f"{pds_url}/xrpc/com.etzhayyim.murakumo.infer",
                          json=payload, headers=_auth_headers(), timeout=120)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(data.get("text") or data.get("content") or str(data))
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@murakumo.command("route")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_route(pds: str | None, json_out: bool) -> None:
    """Show current routing configuration (full update requires Go binary)."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.murakumo.getRouting",
                         headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


def _murakumo_git_root() -> Path | None:
    try:
        root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        return Path(root)
    except Exception:
        return None


@murakumo.group("models")
def murakumo_models() -> None:
    """Murakumo fleet model placement management."""


@murakumo_models.command("declare")
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_models_declare(json_out: bool) -> None:
    """Print declared model placement from fleet-models.json."""
    root = _murakumo_git_root()
    if root is None:
        click.echo("fleet-models.json not found")
        return

    fleet_models_path = root / "60-apps" / "etzhayyim-project-murakumo" / "fleet-models.json"
    if not fleet_models_path.exists():
        click.echo("fleet-models.json not found")
        return

    with fleet_models_path.open() as f:
        data = json.load(f)

    if json_out:
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    fleet = data.get("fleet", [])
    models = data.get("models", {})
    click.echo(f"Fleet: {', '.join(fleet)}\n")
    for name in sorted(models):
        info = models[name]
        size_gb = info.get("size_gb", "?")
        kind = info.get("kind", "?")
        purpose = info.get("purpose", "")
        target_minis = info.get("target_minis", [])
        click.echo(f"  {name:<22} [{kind}]  {size_gb:.1f} GB")
        if purpose:
            click.echo(f"    {purpose}")
        click.echo(f"    target: {', '.join(target_minis)} ({len(target_minis)}/{len(fleet)} minis)")
        if kind == "ollama":
            click.echo(f"    ollama_tag: {info.get('ollama_tag', '')}")
        elif kind == "comfyui_checkpoint":
            click.echo(f"    hf: {info.get('hf_repo', '')}/{info.get('hf_file', '')} → {info.get('path', '')}/{info.get('filename', '')}")
        elif kind == "comfyui_diffusers":
            click.echo(f"    diffusers_repo: {info.get('diffusers_repo', '')} (HF cache via DiffusersLoader)")
        elif kind == "comfyui_wan":
            for c in info.get("components", []):
                click.echo(f"    component: {c.get('path', '')}/{c.get('file', '')} ← {c.get('hf_repo', '')}/{c.get('hf_file', '')}")
        click.echo()


def _load_fleet_models(root: Path) -> dict:
    fleet_models_path = root / "60-apps" / "etzhayyim-project-murakumo" / "fleet-models.json"
    if not fleet_models_path.exists():
        raise click.ClickException(f"fleet-models.json not found: {fleet_models_path}")
    with fleet_models_path.open() as f:
        return json.load(f)


def _ssh_on_mini(mini: str, cmd: str, timeout: float = 6.0) -> tuple[bool, str]:
    target = f"{mini}@{mini}.murakumo.lan"
    args = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", f"ConnectTimeout=5",
        "-o", "StrictHostKeyChecking=no",
        target, cmd,
    ]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except FileNotFoundError:
        return False, "ssh not found"


def _probe_model_on_mini(mini: str, model_info: dict) -> bool:
    kind = model_info.get("kind", "")
    if kind == "ollama":
        tag = model_info.get("ollama_tag", "")
        cmd = f'curl -fsS --max-time 3 http://localhost:11434/api/tags 2>/dev/null | grep -q \'"name":"{tag}"\''
    elif kind == "comfyui_checkpoint":
        path = model_info.get("path", "")
        filename = model_info.get("filename", "")
        cmd = f"test -s ~/comfyui/{path}/{filename}"
    elif kind == "comfyui_diffusers":
        repo = model_info.get("diffusers_repo", "").replace("/", "--")
        cmd = f"test -d ~/.cache/huggingface/hub/models--{repo}/snapshots"
    elif kind == "comfyui_wan":
        parts = []
        for c in model_info.get("components", []):
            parts.append(f"test -s ~/comfyui/{c.get('path', '')}/{c.get('file', '')}")
        cmd = " && ".join(parts) if parts else "false"
    else:
        return False
    ok, _ = _ssh_on_mini(mini, cmd, timeout=6.0)
    return ok


@murakumo_models.command("list")
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_models_list(json_out: bool) -> None:
    """Probe each fleet mini and show declared vs actual model presence."""
    import concurrent.futures

    root = _murakumo_git_root()
    if root is None:
        raise click.ClickException("could not find git root")
    data = _load_fleet_models(root)
    fleet: list[str] = data.get("fleet", [])
    models: dict = data.get("models", {})
    model_names = sorted(models)

    def probe_mini(mini: str) -> dict:
        model_status = {}
        for name in model_names:
            info = models[name]
            declared = mini in info.get("target_minis", [])
            actual = _probe_model_on_mini(mini, info) if declared else False
            model_status[name] = {"declared": declared, "actual": actual}
        return {"mini": mini, "models": model_status}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(fleet) or 1) as ex:
        statuses = list(ex.map(probe_mini, fleet))

    if json_out:
        click.echo(json.dumps({"fleet": fleet, "statuses": statuses}, ensure_ascii=False, indent=2))
        return

    header = f"{'mini':<12}"
    for n in model_names:
        header += f" {n[:22]:<22}"
    click.echo(header)
    click.echo("─" * len(header))
    for st in statuses:
        row = f"{st['mini']:<12}"
        for n in model_names:
            ms = st["models"].get(n, {})
            declared, actual = ms.get("declared", False), ms.get("actual", False)
            if declared and actual:
                cell = "✓ deployed"
            elif declared and not actual:
                cell = "✗ MISSING"
            elif not declared and actual:
                cell = "~ orphan"
            else:
                cell = "-"
            row += f" {cell:<22}"
        click.echo(row)
    click.echo()
    click.echo("legend:  ✓ ok   ✗ declared but missing   ~ present but not declared   - n/a")


@murakumo_models.command("apply")
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
@click.option("--target", default="", help="comma-separated model names (default: all)")
@click.option("--only-mini", "only_mini", default="", help="comma-separated mini names (default: all)")
def murakumo_models_apply(dry_run: bool, target: str, only_mini: str) -> None:
    """Reconcile fleet model state — install missing models (HF_TOKEN env required)."""
    import concurrent.futures
    import os as _os

    root = _murakumo_git_root()
    if root is None:
        raise click.ClickException("could not find git root")
    data = _load_fleet_models(root)
    fleet: list[str] = data.get("fleet", [])
    models: dict = data.get("models", {})
    hf_token = _os.environ.get("HF_TOKEN") or _os.environ.get("HUGGING_FACE_HUB_TOKEN", "")

    want_models = {m for m in (target.split(",") if target else models)} & set(models)
    want_fleet = {m for m in (only_mini.split(",") if only_mini else fleet)} & set(fleet)

    def _install_cmd(mini: str, name: str, info: dict) -> str | None:
        kind = info.get("kind", "")
        if kind == "ollama":
            tag = info.get("ollama_tag", "")
            return f"ollama pull {tag}"
        elif kind == "comfyui_checkpoint":
            path, filename = info.get("path", ""), info.get("filename", "")
            hf_repo, hf_file = info.get("hf_repo", ""), info.get("hf_file", "")
            url = f"https://huggingface.co/{hf_repo}/resolve/main/{hf_file}"
            return (f"set -e; mkdir -p ~/comfyui/{path}; cd ~/comfyui/{path}; "
                    f"if [ -s '{filename}' ]; then exit 0; fi; "
                    f"curl -sL --fail -H 'Authorization: Bearer {hf_token}' "
                    f"-o '{filename}' '{url}'")
        elif kind == "comfyui_diffusers":
            repo = info.get("diffusers_repo", "")
            return (f"python3 -c \"from diffusers import DiffusionPipeline; "
                    f"DiffusionPipeline.from_pretrained('{repo}')\"")
        return None

    results = []
    for mini in sorted(want_fleet):
        for name in sorted(want_models):
            info = models[name]
            if mini not in info.get("target_minis", []):
                continue
            already = _probe_model_on_mini(mini, info)
            if already:
                click.echo(f"  {mini}  {name}: already present", err=True)
                continue
            cmd = _install_cmd(mini, name, info)
            if cmd is None:
                click.echo(f"  {mini}  {name}: unsupported kind {info.get('kind')}", err=True)
                continue
            if dry_run:
                click.echo(f"  [dry-run] {mini}  {name}: would run: {cmd[:80]}...")
                results.append({"mini": mini, "model": name, "action": "would-install"})
                continue
            click.echo(f"  {mini}  {name}: installing...", err=True)
            ok, out = _ssh_on_mini(mini, cmd, timeout=1800.0)
            status = "ok" if ok else "failed"
            click.echo(f"  {mini}  {name}: {status}")
            if not ok and out:
                click.echo(f"    {out[:200]}", err=True)
            results.append({"mini": mini, "model": name, "action": status})

    ok_count = sum(1 for r in results if r["action"] == "ok")
    fail_count = sum(1 for r in results if r["action"] == "failed")
    click.echo(f"\napply done: {ok_count} installed, {fail_count} failed, {len(results)} total actions")


# ── murakumo plan ──────────────────────────────────────────────────────────

_MURAKUMO_STEPS = [
    {"command": "plan", "nsid": "com.etzhayyim.murakumo.planPipeline",
     "purpose": "Show the canonical Hayate V6 data/train/inference pipeline steps."},
    {"command": "graph-extract", "nsid": "com.etzhayyim.murakumo.graphExtract",
     "purpose": "Extract entities/relations from did_domains with Qwen4B worker."},
    {"command": "graph-ingest", "nsid": "com.etzhayyim.murakumo.graphIngest",
     "purpose": "Register graph entities as DID nodes and store into LanceDB."},
    {"command": "coverage-export", "nsid": "com.etzhayyim.murakumo.coverageExport",
     "purpose": "Export coverage domains from yata/PDS into coverage_domains npy."},
    {"command": "fleet-plan", "nsid": "com.etzhayyim.murakumo.fleetPlan",
     "purpose": "Generate slot allocation plan for Hayate V6 fleet training."},
    {"command": "train-experts", "nsid": "com.etzhayyim.murakumo.trainExperts",
     "purpose": "Run phase-2 expert training and persist bf16/int8 experts."},
    {"command": "eval", "nsid": "com.etzhayyim.murakumo.evalV6",
     "purpose": "Run Hayate V6 benchmark/eval for regression checks."},
    {"command": "optimize", "nsid": "com.etzhayyim.murakumo.optimizeCycle",
     "purpose": "Run one efficient optimization cycle (ingest → score → chunk-train → eval)."},
]


@murakumo.command("plan")
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_plan(json_out: bool) -> None:
    """Show canonical Hayate V6 pipeline steps."""
    if json_out:
        click.echo(json.dumps({"steps": _MURAKUMO_STEPS}, ensure_ascii=False, indent=2))
        return
    click.echo("Murakumo Pipeline (com.etzhayyim.murakumo.*)")
    for i, s in enumerate(_MURAKUMO_STEPS, 1):
        click.echo(f"{i}. etzhayyim murakumo {s['command']}")
        click.echo(f"   NSID: {s['nsid']}")
        click.echo(f"   {s['purpose']}")
    click.echo(f"{len(_MURAKUMO_STEPS)+1}. etzhayyim murakumo xrpc --nsid com.etzhayyim.murakumo.runPipeline --payload-file run.json")


# ── murakumo xrpc ─────────────────────────────────────────────────────────

@murakumo.command("xrpc")
@click.option("--nsid", required=True, help="NSID (e.g. com.etzhayyim.murakumo.graphExtract)")
@click.option("--payload", default="{}", help="Inline JSON payload")
@click.option("--payload-file", "payload_file", default=None, help="Path to JSON payload file")
@click.option("--pds", default=None, help="PDS base URL")
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_xrpc(nsid: str, payload: str, payload_file: str | None, pds: str | None, json_out: bool) -> None:
    """Generic murakumo XRPC call (POST)."""
    from .projector import resolve_pds
    pds_url = (pds or resolve_pds()).rstrip("/")
    body = payload
    if payload_file:
        body = Path(payload_file).read_text()
    try:
        import json as _json
        _json.loads(body)
    except ValueError as e:
        raise click.ClickException(f"Invalid JSON payload: {e}")
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/{nsid}",
            content=body.encode(),
            headers={**_auth_headers(), "content-type": "application/json"},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in (data.items() if isinstance(data, dict) else []):
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


# ── murakumo eval ──────────────────────────────────────────────────────────

_MURAKUMO_TRAINING_DIR = "60-apps/etzhayyim-project-murakumo/training"


@murakumo.command("eval")
@click.option("--python-bin", "python_bin", default="python3.11", show_default=True)
@click.option("--mode", default="eval", type=click.Choice(["eval", "quick", "full"]),
              show_default=True)
@click.option("--checkpoint", default="", help="checkpoint .npz path (auto-detect if omitted)")
@click.option("--limit", default=20, type=int, show_default=True, help="evaluation question limit")
@click.option("--dim", default=256, type=int, show_default=True)
@click.option("--groups", default=1, type=int, show_default=True)
@click.option("--sql", "run_sql", is_flag=True, default=False, help="also run eval_v6_sql.py")
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
def murakumo_eval(
    python_bin: str, mode: str, checkpoint: str, limit: int, dim: int,
    groups: int, run_sql: bool, dry_run: bool,
) -> None:
    """Run Hayate V6 evaluation benchmark (eval_v6_bench.py)."""
    try:
        repo_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True,
        ).strip())
    except subprocess.CalledProcessError:
        raise click.ClickException("not in a git repository")

    training_dir = repo_root / _MURAKUMO_TRAINING_DIR
    bench_script = training_dir / "eval_v6_bench.py"
    sql_script = training_dir / "eval_v6_sql.py"

    if not bench_script.exists():
        raise click.ClickException(f"missing script: {bench_script}")

    cmd = [
        python_bin, str(bench_script),
        "--mode", mode,
        "--limit", str(limit),
        "--dim", str(dim),
        "--groups", str(groups),
    ]

    if mode == "eval":
        ckpt = checkpoint
        if not ckpt:
            candidate = training_dir / "data" / "hayate_v6_bench.npz"
            if candidate.exists():
                ckpt = str(candidate)
        if not ckpt:
            raise click.ClickException("eval mode requires --checkpoint (auto-detect failed)")
        cmd += ["--checkpoint", ckpt]
    elif checkpoint:
        cmd += ["--checkpoint", checkpoint]

    if dry_run:
        click.echo("dry-run: " + " ".join(cmd))
        return

    result = subprocess.run(cmd, cwd=str(repo_root))
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    if run_sql and sql_script.exists():
        result2 = subprocess.run([python_bin, str(sql_script)], cwd=str(repo_root))
        if result2.returncode != 0:
            raise SystemExit(result2.returncode)


# ── murakumo fleet ────────────────────────────────────────────────────────────

@murakumo.group("fleet")
def murakumo_fleet() -> None:
    """Fleet operations (Nomad-backed; full fleet management requires Go binary)."""


@murakumo_fleet.command("jotai")
@click.option("--pds", default=None, help="Murakumo base URL")
@click.option("--limit", default=50, type=int, show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_fleet_jotai(pds: str | None, limit: int, json_out: bool) -> None:
    """Show fleet status via XRPC."""
    from .projector import resolve_pds as _resolve_pds
    pds_url = (pds or _resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.murakumo.fleetStatus",
            params={"limit": limit},
            headers=_auth_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            workers = data.get("workers", data if isinstance(data, list) else [])
            click.echo(f"murakumo fleet: {len(workers)} workers")
            for w in workers[:limit]:
                click.echo(f"  {w.get('id', '')}  {w.get('status', '')}  {w.get('model', '')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@murakumo_fleet.command("nodes")
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_fleet_nodes(json_out: bool) -> None:
    """Show Nomad node status (requires nomad CLI)."""
    try:
        out = subprocess.check_output(["nomad", "node", "status", "-json"], text=True)
        if json_out:
            click.echo(out)
        else:
            import json as _j
            nodes = _j.loads(out)
            for n in nodes:
                click.echo(f"  {n.get('ID', '')[:8]}  {n.get('Name', '')}  {n.get('Status', '')}")
    except FileNotFoundError:
        raise click.ClickException("nomad CLI not found — install Nomad or use Go binary")
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"nomad error: {e}")


@murakumo_fleet.command("versions")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_fleet_versions(pds: str | None, json_out: bool) -> None:
    """Show per-worker daemon versions via XRPC."""
    from .projector import resolve_pds as _resolve_pds
    pds_url = (pds or _resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(
            f"{pds_url}/xrpc/com.etzhayyim.murakumo.workerVersions",
            headers=_auth_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            workers = data.get("workers", [])
            for w in workers:
                click.echo(f"  {w.get('id', '')}  v{w.get('version', '?')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


_DAEMON_DEPLOY_PATH = "/usr/local/share/murakumo/daemon.py"


def _resolve_nomad_addr() -> str:
    """The Nomad server address, from NOMAD_ADDR. There is no default.

    This used to be ``os.environ.get("NOMAD_ADDR", "http://benjamin.local:4646")``.
    ``benjamin`` is a real murakumo mac-mini (scripts/fleet-ci/nodes.edn) and
    ``.local`` is the mDNS namespace (RFC 6762), so that name is claimable by
    any host on the same link — whoever answers the multicast query first wins.
    The fallback therefore aimed the whole fleet-management surface at a host
    nobody selected, and one an attacker on the same network can become.

    That is a credential path and not merely a wrong address: ``_run_nomad``
    below runs the nomad CLI, which sends ``$NOMAD_TOKEN`` as an
    ``X-Nomad-Token`` header to whatever ``NOMAD_ADDR`` names. NOMAD_TOKEN
    appears nowhere in this repo, which is exactly what made it easy to miss —
    the credential comes from the operator's shell and is named in no source
    file, so reading this module could not tell you one was in play.

    **The address is the defect, not the environment inheritance** — see the
    comment in ``_run_nomad``.

    Why require it instead of picking a better default: there is no
    etzhayyim-owned Nomad address to fall back to. ``auth.default_pds`` can name
    ``https://atproto.etzhayyim.com`` because the org actually runs it, and the
    kubo endpoint in the k8s manifests can name a fleet host because
    ``deps.edn :platform :ipfs`` declares it. The platform manifest has no Nomad
    entry at all, and this literal was the only statement of a Nomad address
    anywhere in the repo. Inventing an owned-looking host that serves nothing
    would be worse than the squattable one, because an unreachable wrong default
    still silently decides where a token goes. So require the value and say so.
    """
    import os
    addr = (os.environ.get("NOMAD_ADDR") or "").strip()
    if not addr:
        raise click.ClickException(
            "NOMAD_ADDR is not set. Point it at your Nomad server, e.g.\n"
            "    export NOMAD_ADDR=http://<nomad-server>:4646\n"
            "This command used to fall back to a fleet node's mDNS name, which "
            "any host on the same network can claim; it no longer guesses."
        )
    # Callers interpolate this as f"{addr}/v1/nodes", so a trailing slash would
    # produce "…//v1/nodes". The old `or` did not guard that either.
    return addr.rstrip("/")


def _run_nomad(*args: str) -> None:
    import shutil
    nomad = shutil.which("nomad")
    if not nomad:
        raise click.ClickException("nomad CLI not found in PATH")
    # The child gets the caller's full environment, deliberately. That is also
    # simply what subprocess.run does when `env=` is omitted — the kwarg exists
    # here only to inject NOMAD_ADDR, so this line adds no inheritance that was
    # not already the default.
    #
    # Narrowing it was considered and rejected: NOMAD_TOKEN (ACLs), NOMAD_CACERT
    # and NOMAD_CLIENT_CERT (mTLS), NOMAD_NAMESPACE and NOMAD_REGION all reach
    # the CLI this way, and any allowlist that kept the tool usable would have to
    # carry NOMAD_TOKEN anyway — so the credential would still travel and nothing
    # would be closed. Handing the token to an address the OPERATOR chose is the
    # documented way to drive Nomad; handing it to a squattable default was not.
    #
    # _resolve_nomad_addr is also the only place this could be fixed:
    # _nomad_node_id, _nomad_alloc_id and `fleet watch` reach the same address
    # over urllib with no environment involved at all, leaking node names and
    # allocation IDs, and `nomad job run` would hand a job spec to whoever
    # answered. Fixing the address closes all four paths; narrowing the
    # environment closes none of them.
    env = {**__import__("os").environ, "NOMAD_ADDR": _resolve_nomad_addr()}
    result = subprocess.run([nomad] + list(args), env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _nomad_node_id(name: str) -> str:
    import urllib.request
    url = f"{_resolve_nomad_addr()}/v1/nodes"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            nodes = json.loads(resp.read())
    except Exception as e:
        raise click.ClickException(f"cannot reach Nomad: {e}")
    for n in nodes:
        if n.get("Name") == name or (n.get("Meta") or {}).get("fleet_node") == name:
            return n["ID"]
    raise click.ClickException(f"node not found in Nomad: {name}")


def _nomad_alloc_id(name: str) -> str:
    import urllib.request
    url = f"{_resolve_nomad_addr()}/v1/job/murakumo-inference/allocations"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            allocs = json.loads(resp.read())
    except Exception as e:
        raise click.ClickException(f"cannot reach Nomad: {e}")
    for a in allocs:
        if a.get("NodeName") == name and a.get("ClientStatus") == "running":
            return a["ID"]
    raise click.ClickException(f"no running allocation for node: {name}")


@murakumo_fleet.command("deploy")
@click.option("--nodes", default="", help="Comma-separated node names (default: all)")
@click.option("--skip-restart", is_flag=True, default=False)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--concurrency", default=4, type=int, show_default=True)
def murakumo_fleet_deploy(nodes: str, skip_restart: bool, dry_run: bool,
                           concurrency: int) -> None:
    """Deploy daemon.py to fleet nodes via scp + Nomad rolling restart."""
    try:
        repo_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except subprocess.CalledProcessError:
        raise click.ClickException("not in a git repository")
    daemon_src = repo_root / "projects/etzhayyim-project-murakumo/cli/daemon.py"
    if not daemon_src.exists():
        raise click.ClickException(f"daemon.py not found: {daemon_src}")
    if dry_run:
        click.echo(f"[dry-run] would deploy {daemon_src} to nodes: {nodes or 'all'}")
        if not skip_restart:
            click.echo("[dry-run] would run: nomad job run murakumo-inference.nomad.hcl")
        return
    import shutil
    if not shutil.which("sshpass"):
        raise click.ClickException("sshpass not found — install: brew install hudochenkov/sshpass/sshpass")
    targets = [n.strip() for n in nodes.split(",") if n.strip()] if nodes else []
    click.echo(f"deploy: daemon.py → {len(targets) if targets else 'all'} nodes")
    click.echo("  (full parallel SSH deploy requires Go binary: etzhayyim murakumo fleet deploy)")
    if not skip_restart:
        job_file = repo_root / "projects/etzhayyim-project-murakumo/nomad/murakumo-inference.nomad.hcl"
        if job_file.exists():
            _run_nomad("job", "run", str(job_file))
        else:
            raise click.ClickException(f"job file not found: {job_file}")


@murakumo_fleet.command("drain")
@click.argument("node_name")
@click.option("--deadline", default="1m", show_default=True)
def murakumo_fleet_drain(node_name: str, deadline: str) -> None:
    """Gracefully drain a Nomad fleet node."""
    node_id = _nomad_node_id(node_name)
    click.echo(f"draining node {node_name} (id={node_id[:8]}, deadline={deadline})...")
    _run_nomad("node", "drain", "-enable", "-deadline", deadline, "-yes", node_id)


@murakumo_fleet.command("undrain")
@click.argument("node_name")
def murakumo_fleet_undrain(node_name: str) -> None:
    """Re-enable a drained Nomad fleet node."""
    node_id = _nomad_node_id(node_name)
    click.echo(f"enabling node {node_name} (id={node_id[:8]})...")
    _run_nomad("node", "drain", "-disable", "-yes", node_id)


@murakumo_fleet.command("restart")
def murakumo_fleet_restart() -> None:
    """Trigger rolling restart of murakumo-inference Nomad job."""
    try:
        repo_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except subprocess.CalledProcessError:
        raise click.ClickException("not in a git repository")
    job_file = repo_root / "projects/etzhayyim-project-murakumo/nomad/murakumo-inference.nomad.hcl"
    if not job_file.exists():
        raise click.ClickException(f"job file not found: {job_file}")
    click.echo("triggering rolling restart of murakumo-inference...")
    _run_nomad("job", "run", str(job_file))


@murakumo_fleet.command("logs")
@click.argument("node_name")
@click.option("-f", "--follow", is_flag=True, default=False, help="Follow log output")
@click.option("--task", default="daemon", show_default=True, help="Task name")
def murakumo_fleet_logs(node_name: str, follow: bool, task: str) -> None:
    """Show Nomad allocation logs for a fleet node."""
    alloc_id = _nomad_alloc_id(node_name)
    args = ["alloc", "logs", "-task", task]
    if follow:
        args.append("-f")
    args.append(alloc_id)
    _run_nomad(*args)


@murakumo_fleet.command("watch")
@click.option("--interval", default=15, type=int, show_default=True, help="Poll interval (seconds)")
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_fleet_watch(interval: int, json_out: bool) -> None:
    """Continuously monitor fleet health (Ctrl-C to stop)."""
    import time
    import urllib.request
    nomad_addr = _resolve_nomad_addr()
    click.echo(f"watching fleet (interval={interval}s, nomad={nomad_addr}) — Ctrl-C to stop\n")
    while True:
        now = __import__("datetime").datetime.now().strftime("%H:%M:%S")
        ready, total = 0, 0
        node_names = []
        try:
            with urllib.request.urlopen(f"{nomad_addr}/v1/nodes", timeout=10) as resp:
                nodes_data = json.loads(resp.read())
            total = len(nodes_data)
            for n in nodes_data:
                mark = "+"
                if n.get("Status") != "ready":
                    mark = "!"
                elif n.get("Drain"):
                    mark = "~"
                else:
                    ready += 1
                node_names.append(mark + n.get("Name", ""))
        except Exception:
            node_names = ["[nomad unreachable]"]
        if json_out:
            click.echo(json.dumps({
                "time": now, "nomadNodes": total, "nomadReady": ready,
                "nodes": node_names,
            }, ensure_ascii=False))
        else:
            status = "OK" if ready == total else f"DEGRADED ({ready}/{total})"
            click.echo(f"[{now}] nomad={status}  nodes={ready}/{total}  "
                       f"{' '.join(node_names)}")
        time.sleep(interval)


# ── murakumo graph-extract / graph-ingest / coverage-export ───────────────────

def _murakumo_run_script(script_name: str, cmd_args: list[str], python_bin: str = "python3.11") -> None:
    """Run a training script from murakumoTrainingDir, raise ClickException if missing."""
    try:
        repo_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True,
        ).strip())
    except subprocess.CalledProcessError:
        raise click.ClickException("not in a git repository")
    script = repo_root / _MURAKUMO_TRAINING_DIR / script_name
    if not script.exists():
        raise click.ClickException(f"missing script: {script}")
    result = subprocess.run([python_bin, str(script)] + cmd_args, cwd=str(repo_root))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


@murakumo.command("graph-extract")
@click.option("--python-bin", "python_bin", default="python3.11", show_default=True)
@click.option("--labels", required=True, help="comma-separated entity labels")
@click.option("--worker-script", "worker_script", default="", help="extraction worker script path")
@click.option("--output", default="", help="JSONL output path")
@click.option("--samples", default=50, type=int, show_default=True)
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
def murakumo_graph_extract(python_bin: str, labels: str, worker_script: str, output: str, samples: int, dry_run: bool) -> None:
    """Run graph entity extraction (lfm_worker.py) for given labels."""
    script = worker_script or "/Volumes/251220/lfm_worker.py"
    out = output or "/Volumes/251220/graph_results/graph_entities.jsonl"
    cmd = [script, "--labels", labels, "--output", out, "--samples", str(samples)]
    if dry_run:
        click.echo("dry-run: " + python_bin + " " + " ".join(cmd))
        return
    result = subprocess.run([python_bin] + cmd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


@murakumo.command("graph-ingest")
@click.option("--python-bin", "python_bin", default="python3.11", show_default=True)
@click.option("--input", "input_path", default="", help="JSONL input dir or file")
@click.option("--lancedb-uri", "lancedb_uri", default="", help="LanceDB URI")
@click.option("--pds", default=None, help="PDS base URL")
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
def murakumo_graph_ingest(python_bin: str, input_path: str, lancedb_uri: str, pds: str | None, dry_run: bool) -> None:
    """Ingest graph_results JSONL into LanceDB + push MERGE statements via kagami XRPC."""
    inp = input_path or "/Volumes/251220/graph_results"
    ldb = lancedb_uri or "/Volumes/251220/lancedb"
    cmd_args = ["--input", inp, "--lancedb-uri", ldb]
    if pds:
        cmd_args += ["--pds-url", pds]
    if dry_run:
        click.echo(f"dry-run: {python_bin} ingest_graph_entities.py " + " ".join(cmd_args))
        return
    _murakumo_run_script("ingest_graph_entities.py", cmd_args, python_bin)


@murakumo.command("coverage-export")
@click.option("--python-bin", "python_bin", default="python3.11", show_default=True)
@click.option("--output", default="", help="coverage output directory")
@click.option("--target-tokens", "target_tokens", default=1_000_000_000, type=int)
@click.option("--pds", default=None, help="PDS base URL")
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
def murakumo_coverage_export(python_bin: str, output: str, target_tokens: int, pds: str | None, dry_run: bool) -> None:
    """Export coverage domains for training (generate_yata_training.py)."""
    out = output or "/Volumes/251220/coverage_domains"
    cmd_args = ["coverage-export", "--target-tokens", str(target_tokens), "--output", out]
    if pds:
        cmd_args += ["--pds-url", pds]
    if dry_run:
        click.echo(f"dry-run: {python_bin} generate_yata_training.py " + " ".join(cmd_args))
        return
    _murakumo_run_script("generate_yata_training.py", cmd_args, python_bin)


@murakumo.command("train-experts")
@click.option("--label", default="", help="single label to train")
@click.option("--n-labels", "n_labels", default=2, type=int, show_default=True)
@click.option("--label-start", "label_start", default=0, type=int, show_default=True)
@click.option("--epochs", default=1, type=int, show_default=True)
@click.option("--slots-per", "slots_per", default=128, type=int, show_default=True)
@click.option("--device", default="wgpu", show_default=True)
@click.option("--pds", default=None, help="PDS base URL")
@click.option("--json", "json_out", is_flag=True, default=False)
def murakumo_train_experts(
    label: str, n_labels: int, label_start: int, epochs: int, slots_per: int,
    device: str, pds: str | None, json_out: bool,
) -> None:
    """Submit expert training job via XRPC (com.etzhayyim.murakumo.trainExperts)."""
    from .projector import resolve_pds as _resolve_pds
    pds_url = (pds or _resolve_pds()).rstrip("/")
    payload = {
        "label": label,
        "nLabels": n_labels,
        "labelStart": label_start,
        "epochs": epochs,
        "slotsPer": slots_per,
        "backend": device,
    }
    try:
        resp = httpx.post(
            f"{pds_url}/xrpc/com.etzhayyim.murakumo.trainExperts",
            json=payload,
            headers=_auth_headers(),
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"train-experts submitted: {data.get('runId', data)}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@murakumo.command("fleet-plan")
@click.option("--python-bin", "python_bin", default="python3.11", show_default=True)
@click.option("--data-dir", "data_dir", default="", help="expert domain npy directory")
@click.option("--target-slots", "target_slots", default=500_000, type=int, show_default=True)
@click.option("--dim", default=512, type=int, show_default=True)
@click.option("--groups", default=2, type=int, show_default=True)
@click.option("--mamba-per-group", "mamba_per_group", default=6, type=int, show_default=True)
@click.option("--top-m", "top_m", default=128, type=int, show_default=True)
@click.option("--batch-size", "batch_size", default=2, type=int, show_default=True)
@click.option("--lr", default=1e-4, type=float, show_default=True)
@click.option("--data-source", "data_source", default="lance", show_default=True,
              type=click.Choice(["lance", "npy"]))
@click.option("--lancedb-uri", "lancedb_uri", default="", help="LanceDB URI")
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
def murakumo_fleet_plan(
    python_bin: str, data_dir: str, target_slots: int, dim: int, groups: int,
    mamba_per_group: int, top_m: int, batch_size: int, lr: float,
    data_source: str, lancedb_uri: str, dry_run: bool,
) -> None:
    """Generate fleet_plan.json from expert_domains (hayate_v5_split.py fleet)."""
    d_dir = data_dir or "/Volumes/251220/expert_domains"
    ldb = lancedb_uri or "/Volumes/251220/lancedb"
    cmd_args = [
        "fleet",
        "--data-dir", d_dir,
        "--target-slots", str(target_slots),
        "--dim", str(dim),
        "--groups", str(groups),
        "--mamba-per-group", str(mamba_per_group),
        "--top-m", str(top_m),
        "--batch-size", str(batch_size),
        "--lr", str(lr),
        "--data-source", data_source,
    ]
    import os as _os
    env = {**_os.environ, "HAYATE_LANCEDB_URI": ldb}
    if dry_run:
        click.echo(f"dry-run: {python_bin} hayate_v5_split.py " + " ".join(cmd_args))
        return
    try:
        repo_root = Path(subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True,
        ).strip())
    except subprocess.CalledProcessError:
        raise click.ClickException("not in a git repository")
    script = repo_root / _MURAKUMO_TRAINING_DIR / "hayate_v5_split.py"
    if not script.exists():
        raise click.ClickException(f"script not found: {script}")
    import subprocess as _sp
    result = _sp.run([python_bin, str(script)] + cmd_args, env=env)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


@murakumo.command("optimize")
@click.option("--python-bin", "python_bin", default="python3.11", show_default=True)
@click.option("--train-count", "train_count", default=4, type=int, show_default=True)
@click.option("--ingest-count", "ingest_count", default=10, type=int, show_default=True)
@click.option("--epochs", default=1, type=int, show_default=True)
@click.option("--pds", default=None, help="PDS base URL")
@click.option("--dry-run", "dry_run", is_flag=True, default=False)
def murakumo_optimize(
    python_bin: str, train_count: int, ingest_count: int, epochs: int, pds: str | None, dry_run: bool,
) -> None:
    """Run efficient optimization cycle (ingest→score→train→eval)."""
    if dry_run:
        click.echo(
            f"dry-run: optimize cycle  ingest_count={ingest_count} train_count={train_count} epochs={epochs}"
        )
        click.echo("  Full cycle runs: ingest_did_domains_to_lancedb.py → update_schema_quality.py → train_experts → eval")
        return
    click.echo(
        "murakumo optimize (full cycle) requires training scripts in "
        f"{_MURAKUMO_TRAINING_DIR}. Use 'murakumo train-experts' for XRPC submission.",
        err=True,
    )
    raise SystemExit(1)


@murakumo.command("kubelet-deploy")
@click.option("--nodes", default="all", show_default=True,
              help="Comma-separated node IPs or 'all'")
@click.option("--dry-run", "dry_run", is_flag=True, default=False,
              help="Print resolved commands without executing")
@click.option("--concurrency", default=4, type=int, show_default=True,
              help="Parallel SSH workers")
@click.option("--repo-root", "repo_root", default=None, help="Repo root override")
def murakumo_kubelet_deploy(nodes: str, dry_run: bool, concurrency: int, repo_root: str | None) -> None:
    """Deploy murakumo-agent to Mac mini fleet via SSH and start Virtual Kubelets.

    Requires MURAKUMO_FLEET_SSH_PASS env var and fleet node access.
    Full implementation in Go binary. Python version prints the start command.
    """
    import subprocess as _sp
    import os as _os

    # Resolve repo root for agent source path
    if repo_root:
        root = Path(repo_root)
    else:
        try:
            r = _sp.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True, check=True)
            root = Path(r.stdout.strip())
        except Exception:
            root = Path(".")

    agent_src = root / "50-infra" / "k8s" / "murakumo-kubelet" / "agent" / "murakumo-agent.py"
    start_script = root / "50-infra" / "k8s" / "murakumo-kubelet" / "start_kubelets.py"

    click.echo(f"==> murakumo kubelet-deploy  nodes={nodes}  concurrency={concurrency}", err=True)
    click.echo(f"  agent_src:    {agent_src}", err=True)
    click.echo(f"  start_script: {start_script}", err=True)

    if dry_run:
        click.echo("  [dry-run] would deploy via SSH + SCP, then run:")
        click.echo(f"  cd {root / '50-infra' / 'k8s' / 'murakumo-kubelet'} && python3 start_kubelets.py")
        return

    if not _os.environ.get("MURAKUMO_FLEET_SSH_PASS"):
        raise click.ClickException(
            "MURAKUMO_FLEET_SSH_PASS env var is required for SSH deployment.\n"
            "Full SSH orchestration available in Go binary: etzhayyim murakumo kubelet-deploy"
        )

    # Print the start command as the Go binary does
    click.echo(f"cd {root / '50-infra' / 'k8s' / 'murakumo-kubelet'} && python3 start_kubelets.py")
