"""etzhayyim build / deploy — magatama Worker build + Cloudflare deploy (Python port).

Core logic ported from 70-tools/etzhayyim/etzhayyim/build.go and deploy.go.
Shells out to pnpm and wrangler the same way the Go binary does.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import click
import httpx


# ── constants ──────────────────────────────────────────────────────────────────

_CF_ACCOUNT_ID = "4da88288dc30d9ee257f319d3c33ecf0"
_SECRETS_STORE_ID = os.environ.get("etzhayyim_SECRETS_STORE_ID", "1824561668fe47cc9127d493961885af")
_DEFAULT_PDS_SERVICE = "etzhayyim-pds-2603241700"

_WRANGLER_SHARED_SECRETS: list[tuple[str, str]] = [
    ("SS_YATA_S3_KEY_ID", "yata_s3_key_id"),
    ("SS_YATA_S3_SECRET_KEY", "yata_s3_secret_key"),
    ("SS_OPENROUTER_API_KEY", "openrouter_api_key"),
    ("SS_PUBLIC_CLERK_PUBLISHABLE_KEY", "public_clerk_publishable_key"),
    ("SS_CLERK_SECRET_KEY", "clerk_secret_key"),
    ("SS_SIGNING_KEY", "signing_key"),
    ("SS_HUME_API_KEY", "hume_api_key"),
    ("SS_HUME_SECRET_KEY", "hume_secret_key"),
    ("SS_HIGGSFIELD_API_KEY", "higgsfield_api_key"),
    ("SS_HIGGSFIELD_API_SECRET", "higgsfield_api_secret"),
    ("SS_RUNWAY_API_KEY", "runway_api_key"),
    ("SS_EPIDEMIC_SOUND_JWT_1", "epidemic_sound_jwt_1"),
    ("SS_EPIDEMIC_SOUND_JWT_2", "epidemic_sound_jwt_2"),
    ("SS_TURN_KEY_ID", "turn_key_id"),
    ("SS_TURN_KEY_API_TOKEN", "turn_key_api_token"),
    ("SS_CLOUDFLARE_REGISTRAR_API_TOKEN", "cloudflare_registrar_api_token"),
    ("SS_WEBYUBIN_USERNAME", "webyubin_username"),
    ("SS_WEBYUBIN_PASSWORD", "webyubin_password"),
    ("SS_WEBYUBIN_PAYMENT_CARD_LAST4", "webyubin_payment_card_last4"),
    ("SS_M365_CLIENT_SECRET", "m365_client_secret"),
    ("DISPATCHER_INTERNAL_SECRET", "dispatcher_internal_secret"),
    ("KAISYA_SERVICE_KEY", "kaisya_service_key"),
]

_CORS_HEADER_RE = re.compile(r"Access-Control-Allow-(?:Headers|Origin|Methods)")
_PDS_HARDCODE_RE = re.compile(
    r'(?:appId|app_id)\s*[:=]\s*"pds"|mergeRecord\([^)]*"pds"\s*\)|\.sql\([^)]*"pds"\s*\)|\.mutate\([^)]*"pds"\s*\)'
)


# ── helpers ────────────────────────────────────────────────────────────────────

def _find_git_root(start: Path) -> Path | None:
    d = start.resolve()
    while True:
        if (d / ".git").exists():
            return d
        parent = d.parent
        if parent == d:
            return None
        d = parent


def _run_cmd(cwd: Path, *args: str) -> None:
    """Shell out to a command; raises ClickException on failure."""
    candidates = [list(args)]
    # pnpm fallback for macOS Homebrew
    if args[0] == "pnpm":
        candidates += [
            ["/opt/homebrew/bin/pnpm"] + list(args[1:]),
            ["/usr/local/bin/pnpm"] + list(args[1:]),
        ]
    last_err: Exception | None = None
    for cmd in candidates:
        try:
            subprocess.run(cmd, cwd=str(cwd), check=True)
            return
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            last_err = e
    raise click.ClickException(f"command failed: {' '.join(args)}: {last_err}")


def _read_magatama_jsonld(comp_dir: Path) -> dict:
    p = comp_dir / "magatama.jsonld"
    if not p.exists():
        raise click.ClickException(f"magatama.jsonld required in {comp_dir}")
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        raise click.ClickException(f"magatama.jsonld parse error: {e}")


def _app_id(cfg: dict) -> str:
    return cfg.get("nanoid") or cfg.get("name", "")


def _ui_type(cfg: dict) -> str:
    return cfg.get("uiType") or "appview"


def _resolve_pds_service() -> str:
    return os.environ.get("etzhayyim_PDS_SERVICE", _DEFAULT_PDS_SERVICE).strip()


def _resolve_etzhayyim_token() -> str:
    return os.environ.get("etzhayyim_TOKEN", "")


# ── validation ─────────────────────────────────────────────────────────────────

def _validate_no_cors(comp_dir: Path) -> None:
    main_go = comp_dir / "main.go"
    if not main_go.exists():
        return
    if _CORS_HEADER_RE.search(main_go.read_text(errors="replace")):
        raise click.ClickException(
            f"cors guard: app-side Access-Control-Allow-* headers are forbidden in {main_go}\n"
            "CORS is managed in Envoy Gateway SecurityPolicy. Remove all CORS header literals from app code."
        )


def _validate_no_pds_hardcode(comp_dir: Path) -> None:
    for name in ["main.go", "src/index.ts", "src/worker.ts"]:
        p = comp_dir / name
        if not p.exists():
            continue
        if _PDS_HARDCODE_RE.search(p.read_text(errors="replace")):
            raise click.ClickException(
                f"pds-hardcode: appId 'pds' hardcoded in {p}\n"
                "Use repo-derived appId. 'pds' is shared namespace for cross-app data only."
            )


def _validate_governance_import(comp_dir: Path) -> None:
    if not (comp_dir / "magatama.jsonld").exists():
        return
    world_path = comp_dir / "wit" / "world.wit"
    if not world_path.exists():
        return
    world = world_path.read_text(errors="replace")
    if ("import magatama:agent/governance@1.0.0;" in world or
            "include magatama:runtime/magatama-component@1.0.0;" in world):
        return
    raise click.ClickException(
        f"magatama governance guard: {world_path} must import `magatama:agent/governance@1.0.0` "
        "or include `magatama:runtime/magatama-component@1.0.0`"
    )


def _validate_profile(cfg: dict) -> None:
    profile = cfg.get("profile")
    if profile is None:
        raise click.ClickException(
            "profile block is required in magatama.jsonld (add profile.displayName and profile.description)"
        )
    if not profile.get("displayName"):
        raise click.ClickException("profile.displayName is required in magatama.jsonld")
    if not profile.get("description"):
        raise click.ClickException("profile.description is required in magatama.jsonld")


def _validate_required(cfg: dict) -> None:
    errors: list[str] = []
    if not cfg.get("governance"):
        errors.append("governance block is required (add governance.roles for RACI/RBAC)")
    if not cfg.get("convoSystemPrompt"):
        errors.append("convoSystemPrompt is required (DM agent conversation needs a system prompt)")
    profile = cfg.get("profile") or {}
    if not profile.get("capabilities"):
        errors.append("profile.capabilities is required (add capability tags for capability discovery)")
    triggers = cfg.get("triggers") or {}
    subscribe_repos = triggers.get("subscribeRepos") or {}
    if not subscribe_repos.get("collections"):
        errors.append("triggers.subscribeRepos.collections is required (reactive pipeline needs at least one collection)")
    if errors:
        raise click.ClickException(
            "magatama.jsonld missing required blocks:\n  - " + "\n  - ".join(errors)
        )


# ── wrangler.jsonc generation ──────────────────────────────────────────────────

def _actor_handle_from_cfg(cfg: dict, comp_dir: Path) -> str:
    profile = cfg.get("profile") or {}
    if h := profile.get("handle", "").strip():
        return h
    # derive from dir name etzhayyim-wasm-{slug}-{nanoid}
    m = re.match(r"etzhayyim-wasm-(.+?)-[a-z0-9]{8,}$", comp_dir.name)
    if m:
        return m.group(1)
    return ""


def _extract_wit_imports(comp_dir: Path) -> list[str]:
    world_path = comp_dir / "wit" / "world.wit"
    if not world_path.exists():
        return []
    imports = []
    for line in world_path.read_text(errors="replace").splitlines():
        line = line.strip()
        if line.startswith("import "):
            wit = line.removeprefix("import ").removesuffix(";").strip()
            if wit:
                imports.append(wit)
    return imports


def _find_host_sdk_path(git_root: Path | None) -> str:
    if git_root is None:
        return ""
    candidate = git_root / "20-actors" / "magatama" / "sdk" / "magatama-host-sdk" / "src" / "index.ts"
    return str(candidate) if candidate.exists() else ""


def _find_pg_alias(root: Path) -> str:
    direct = root / "node_modules" / "pg" / "lib" / "index.js"
    if direct.exists():
        return str(direct)
    for p in sorted((root / "node_modules" / ".pnpm").glob("pg@*/node_modules/pg/lib/index.js")):
        return str(p)
    return ""


def _find_xrpc_alias(root: Path) -> dict[str, str]:
    xrpc_dir = root / "10-protocol" / "xrpc" / "src"
    if not xrpc_dir.exists():
        return {}
    aliases: dict[str, str] = {}
    for sub in ["transport", "auth", "error", "nsid", "encode"]:
        p = xrpc_dir / f"{sub}.ts"
        if p.exists():
            aliases[f"@etzhayyim/xrpc/{sub}"] = str(p)
    return aliases


def generate_wrangler_jsonc(cfg: dict, comp_dir: Path, git_root: Path | None = None) -> str:
    app_id = _app_id(cfg)
    pds_service = _resolve_pds_service()

    # Routes
    routes = [f"{app_id}.etzhayyim.com/*"]
    explicit_routes = cfg.get("routes") or []
    if explicit_routes and explicit_routes[0].get("host"):
        for r in explicit_routes:
            if h := r.get("host", "").strip():
                routes.append(f"{h}/*")
    elif cfg.get("project") and cfg["project"] != app_id and cfg.get("name") == cfg["project"]:
        routes.append(f"{cfg['project']}.etzhayyim.com/*")

    # Dedup routes
    seen: set[str] = set()
    deduped: list[str] = []
    for r in routes:
        if r and r not in seen:
            seen.add(r)
            deduped.append(r)

    # Browser binding
    wit_imports = _extract_wit_imports(comp_dir)
    if cfg.get("needsBrowser"):
        wit_imports.append("magatama:browser/automation@1.0.0")
    needs_browser = "magatama:browser/automation@1.0.0" in wit_imports

    # Assets block
    assets_block = ""
    if _ui_type(cfg) != "yoro":
        assets_block = (
            '\n  "assets": {'
            '\n    "directory": "./svelte/build",'
            '\n    "binding": "ASSETS",'
            '\n    "html_handling": "auto-trailing-slash",'
            '\n    "not_found_handling": "single-page-application"'
            "\n  },"
        )

    # vars
    vars_dict: dict[str, str] = {}
    component = cfg.get("component") or {}
    for k, v in (component.get("env") or {}).items():
        vars_dict[k] = str(v)

    # Version metadata
    sha = _git_short_sha(comp_dir)
    if cfg.get("version") or cfg.get("template") or cfg.get("source"):
        vars_dict["APP_VERSION"] = cfg.get("version", "")
        vars_dict["APP_TEMPLATE"] = cfg.get("template", "")
        vars_dict["APP_SOURCE"] = cfg.get("source", "")
        vars_dict["APP_DEPLOY_SHA"] = sha
        vars_dict["APP_DEPLOY_AT"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    vars_dict["APP_NANOID"] = cfg.get("nanoid", "")
    vars_dict["APP_FRAMEWORK"] = cfg.get("framework") or "ts-native"
    profile = cfg.get("profile") or {}
    vars_dict["APP_DISPLAY_NAME"] = profile.get("displayName", "")
    vars_dict["APP_DESCRIPTION"] = profile.get("description", "")
    if h := _actor_handle_from_cfg(cfg, comp_dir):
        vars_dict["APP_ACTOR_HANDLE"] = h
    ui_type = cfg.get("uiType") or "appview"
    vars_dict["APP_UI_TYPE"] = ui_type
    vars_dict["APP_PERFORMER_TYPE"] = cfg.get("performerType", "")
    if profile.get("capabilities"):
        vars_dict["APP_CAPABILITIES"] = json.dumps(profile["capabilities"])
    if ui_type in ("iframe", "game", "fullapp", "full", "appview"):
        embed_url = cfg.get("embedUrl") or cfg.get("playUrl") or f"https://{cfg.get('nanoid', '')}.etzhayyim.com/?embed=1"
        vars_dict["APP_EMBED_URL"] = embed_url
    interfaces = cfg.get("interfaces") or {}
    if requires := interfaces.get("requires"):
        vars_dict["INTERFACES_REQUIRES"] = json.dumps(requires)
    for env_key in ("etzhayyim_SIGNING_PUBLIC_KEY", "SIGNING_PUBLIC_KEY"):
        if v := os.environ.get(env_key, ""):
            vars_dict["SIGNING_PUBLIC_KEY"] = v
            break

    # vars JSON block
    if vars_dict:
        entries = sorted(f'    {json.dumps(k)}: {json.dumps(v)}' for k, v in vars_dict.items())
        vars_block = '\n  "vars": {\n' + ",\n".join(entries) + "\n  },"
    else:
        vars_block = ""

    # secrets
    secret_entries = [
        f'    {{ "binding": {json.dumps(b)}, "store_id": {json.dumps(_SECRETS_STORE_ID)}, "secret_name": {json.dumps(s)} }}'
        for b, s in _WRANGLER_SHARED_SECRETS
    ]

    # routes
    route_entries = [
        f'    {{ "pattern": {json.dumps(r)}, "zone_name": "etzhayyim.com" }}'
        for r in deduped
    ]

    # browser binding
    browser_binding = '\n  "browser": { "binding": "HEADLESS_BROWSER" },' if needs_browser else ""

    # durable objects
    do_bindings = component.get("durableObjects") or []
    do_block = ""
    if do_bindings:
        tag = "v1"
        bindings_lines = []
        new_classes = []
        for d in do_bindings:
            bindings_lines.append(f'    {{ "name": {json.dumps(d["name"])}, "class_name": {json.dumps(d["className"])} }}')
            new_classes.append(json.dumps(d["className"]))
            if d.get("tag"):
                tag = d["tag"]
        do_block = (
            f'\n  "durable_objects": {{\n    "bindings": [\n'
            + ",\n".join(bindings_lines)
            + f'\n    ]\n  }},\n  "migrations": [\n    {{ "tag": {json.dumps(tag)}, "new_sqlite_classes": [{", ".join(new_classes)}] }}\n  ],'
        )

    # alias block
    alias_block = ""
    if git_root is None:
        git_root = _find_git_root(comp_dir)
    host_sdk = _find_host_sdk_path(git_root)
    if host_sdk and git_root:
        aliases: dict[str, str] = {"@etzhayyim/magatama-host-sdk": host_sdk}
        if pg := _find_pg_alias(git_root):
            aliases["pg"] = pg
        aliases.update(_find_xrpc_alias(git_root))
        alias_parts = ", ".join(f'{json.dumps(k)}: {json.dumps(v)}' for k, v in aliases.items())
        alias_block = f'\n  "alias": {{ {alias_parts} }},'

    return (
        "{\n"
        f'  "name": "magatama-{app_id}",\n'
        f'  "main": "src/app.ts",\n'
        f'  "compatibility_date": "2025-03-17",\n'
        f'  "compatibility_flags": ["nodejs_compat", "nodejs_als"],{alias_block}{assets_block}{vars_block}\n'
        f'  "r2_buckets": [\n'
        f'    {{ "binding": "YATA_R2", "bucket_name": "etzhayyim-cache" }},\n'
        f'    {{ "binding": "CACHE_R2", "bucket_name": "etzhayyim-cache" }}\n'
        f'  ],\n'
        f'  "hyperdrive": [\n'
        f'    {{ "binding": "HYPERDRIVE", "id": "e84c0a2babe44fc7b74818e394b4b896" }}\n'
        f'  ],\n'
        f'  "services": [\n'
        f'    {{ "binding": "PDS_SERVICE", "service": {json.dumps(pds_service)} }},\n'
        f'    {{ "binding": "PDS_RPC", "service": {json.dumps(pds_service)}, "entrypoint": "PdsRPC" }},\n'
        f'    {{ "binding": "MURAKUMO_SERVICE", "service": "etzhayyim-murakumo-2603241700" }},\n'
        f'    {{ "binding": "COMFYUI_SERVICE", "service": "etzhayyim-comfyui-2604221600" }}\n'
        f'  ],\n'
        f'  "secrets_store_secrets": [\n'
        + ",\n".join(secret_entries) + "\n"
        f'  ],\n'
        f'  "rules": [\n'
        f'    {{ "type": "CompiledWasm", "globs": ["**/*.wasm"] }}\n'
        f'  ],{browser_binding}{do_block}\n'
        f'  "routes": [\n'
        + ",\n".join(route_entries) + "\n"
        f'  ]\n'
        "}"
    )


def _git_short_sha(comp_dir: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(comp_dir), capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _evaluate_deps_score(url: str, timeout: int = 20) -> float | None:
    try:
        resp = httpx.get(url.rstrip("/") + "/score.json", timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("scoring", {}).get("overall_score", 0))
    except Exception:
        return None


def _post_deploy_announce(nanoid: str) -> None:
    heartbeat_url = f"https://{nanoid}.etzhayyim.com/_heartbeat"
    try:
        resp = httpx.post(heartbeat_url, json={}, timeout=15)
        if resp.status_code < 300:
            click.echo(f"==> deploy announce: heartbeat triggered ({heartbeat_url})", err=True)
        else:
            click.echo(f"  deploy announce: heartbeat HTTP {resp.status_code}", err=True)
    except Exception as e:
        click.echo(f"  deploy announce: heartbeat failed ({e})", err=True)


# ── build logic ────────────────────────────────────────────────────────────────

def _run_build(comp_dir: Path, *, no_svelte: bool, no_check: bool,
               deps_score: bool, deps_score_url: str, deps_score_min: float) -> None:
    # Validate app entry
    entry = comp_dir / "src" / "app.ts"
    if not entry.exists():
        raise click.ClickException(
            f"worker entry not found: {entry} (expected src/app.ts with createWorkerExport())"
        )

    # Svelte build
    svelte_dir = comp_dir / "svelte"
    if not no_svelte and svelte_dir.exists():
        click.echo("==> pnpm install (svelte)", err=True)
        try:
            _run_cmd(svelte_dir, "pnpm", "install", "--frozen-lockfile")
        except click.ClickException:
            _run_cmd(svelte_dir, "pnpm", "install", "--no-frozen-lockfile")
        if not no_check:
            click.echo("==> svelte-check (type validation)", err=True)
            _run_cmd(svelte_dir, "pnpm", "exec", "svelte-check", "--fail-on-warnings")
        click.echo("==> vite build (Svelte CSR)", err=True)
        _run_cmd(svelte_dir, "pnpm", "build")
        build_index = svelte_dir / "build" / "index.html"
        if not build_index.exists():
            if (svelte_dir / "dist" / "index.html").exists():
                raise click.ClickException(
                    "vite output went to svelte/dist/ instead of svelte/build/. Set outDir: 'build' in vite.config.ts"
                )
            raise click.ClickException(
                "svelte/build/index.html not found after vite build. Check vite.config.ts outDir"
            )
        build_assets = svelte_dir / "build" / "assets"
        if build_assets.exists():
            if not any(f.name.endswith(".css") for f in build_assets.iterdir() if f.is_file()):
                click.echo(
                    "  warning: no CSS file in svelte/build/assets/ — add app.css with @tailwind directives",
                    err=True,
                )
        click.echo("==> Svelte CSR → svelte/build/", err=True)

    # Deps score
    if deps_score:
        click.echo(f"==> evaluating deps score from {deps_score_url}", err=True)
        score = _evaluate_deps_score(deps_score_url)
        if score is None:
            click.echo("==> deps score: remote evaluation failed, continuing with warning", err=True)
        else:
            click.echo(f"==> deps score {score:.1f}", err=True)
            if deps_score_min > 0 and score < deps_score_min:
                raise click.ClickException(
                    f"deps score gate failed: got {score:.1f}, required >= {deps_score_min:.1f}"
                )


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.command("build")
@click.option("--dir", "comp_dir", default=".", show_default=True,
              help="Component source directory")
@click.option("--no-svelte", is_flag=True, default=False,
              help="Skip svelte/pnpm build")
@click.option("--no-check", is_flag=True, default=False,
              help="Skip svelte-check type validation")
@click.option("--deps-score/--no-deps-score", default=True, show_default=True,
              help="Evaluate deps score after build")
@click.option("--deps-score-url", default="https://deps.etzhayyim.com/", show_default=True)
@click.option("--deps-score-min", default=0.0, type=float, show_default=True,
              help="Minimum allowed deps score (0 disables)")
def build(comp_dir: str, no_svelte: bool, no_check: bool,
          deps_score: bool, deps_score_url: str, deps_score_min: float) -> None:
    """Build a magatama Worker (pnpm + svelte + deps score)."""
    path = Path(comp_dir).resolve()
    cfg = _read_magatama_jsonld(path)
    _validate_no_cors(path)
    _validate_no_pds_hardcode(path)
    _validate_governance_import(path)
    _validate_profile(cfg)
    _validate_required(cfg)
    _run_build(path, no_svelte=no_svelte, no_check=no_check,
               deps_score=deps_score, deps_score_url=deps_score_url,
               deps_score_min=deps_score_min)
    click.echo(f"==> build complete: {_app_id(cfg)}", err=True)


@click.command("deploy")
@click.option("--dir", "comp_dir", default=".", show_default=True,
              help="Component source directory")
@click.option("--no-svelte", is_flag=True, default=False,
              help="Skip svelte/pnpm build")
@click.option("--no-check", is_flag=True, default=False,
              help="Skip svelte-check type validation")
@click.option("--no-build", is_flag=True, default=False,
              help="Skip build step (only generate wrangler.jsonc and deploy)")
@click.option("--prune-cdn-immutable/--no-prune-cdn-immutable", default=True,
              help="Best-effort cleanup of stale CDN _app/immutable assets")
@click.option("--deps-score/--no-deps-score", default=True, show_default=True)
@click.option("--deps-score-url", default="https://deps.etzhayyim.com/", show_default=True)
@click.option("--deps-score-min", default=0.0, type=float, show_default=True)
@click.option("--no-announce", is_flag=True, default=False,
              help="Skip post-deploy heartbeat announce")
def deploy(comp_dir: str, no_svelte: bool, no_check: bool, no_build: bool,
           prune_cdn_immutable: bool, deps_score: bool, deps_score_url: str,
           deps_score_min: float, no_announce: bool) -> None:
    """Deploy a magatama Worker to Cloudflare via wrangler."""
    path = Path(comp_dir).resolve()
    cfg = _read_magatama_jsonld(path)
    app_id = _app_id(cfg)
    if not app_id:
        raise click.ClickException("nanoid required in magatama.jsonld")

    _validate_no_cors(path)
    _validate_no_pds_hardcode(path)
    _validate_governance_import(path)
    _validate_profile(cfg)
    _validate_required(cfg)

    if not no_build:
        _run_build(path, no_svelte=no_svelte, no_check=no_check,
                   deps_score=deps_score, deps_score_url=deps_score_url,
                   deps_score_min=deps_score_min)

    click.echo(f"==> deploying {app_id}", err=True)

    # Ensure svelte/build/ exists for Workers Assets (even if empty)
    if _ui_type(cfg) != "yoro":
        (path / "svelte" / "build").mkdir(parents=True, exist_ok=True)

    # Generate wrangler.jsonc
    git_root = _find_git_root(path)
    wrangler_json = generate_wrangler_jsonc(cfg, path, git_root)
    wrangler_path = path / "wrangler.jsonc"
    wrangler_path.write_text(wrangler_json)
    click.echo(f"==> generated wrangler.jsonc ({len(wrangler_json)} bytes)", err=True)

    # wrangler deploy
    _run_cmd(path, "npx", "wrangler", "deploy")

    click.echo(f"==> deployed magatama-{app_id}", err=True)
    click.echo(f"  https://{app_id}.etzhayyim.com/health", err=True)

    # Post-deploy announce
    if not no_announce:
        _post_deploy_announce(app_id)
