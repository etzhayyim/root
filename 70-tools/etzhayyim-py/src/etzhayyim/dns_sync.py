"""dns-sync — ADR-0013 Phase 3: sync deps.toml [[mitama_actors]] + [[legacy_nanoids]]
to Cloudflare DNS records.

Records managed (comment prefix etzhayyim:adr-0013:):
  _atproto.{handle}.etzhayyim.com  TXT   "did={did}"       (AT Protocol handle verification)
  {legacy_nanoid}.etzhayyim.com    CNAME {handle}.etzhayyim.com  (Phase 3 grace, 2026-10-01 deletion)

Only records matching the etzhayyim-managed comment prefix are affected; manual records
are preserved. Default mode is dry-run (preview). Pass --apply to execute.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click
import httpx

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

from .shannon import _resolve_root

_DNS_COMMENT_PREFIX = "etzhayyim:adr-0013:"
_DNS_TXT_COMMENT = _DNS_COMMENT_PREFIX + "atproto-verify"
_DNS_CNAME_COMMENT = _DNS_COMMENT_PREFIX + "legacy-nanoid"


@dataclass
class _IdActor:
    name: str = ""
    domain: str = ""
    nanoid: str = ""
    did: str = ""
    handles: list[str] = field(default_factory=list)


@dataclass
class _IdLegacy:
    actor: str = ""
    nanoid: str = ""
    handle: str = ""
    did: str = ""


def _parse_identifier_tables(deps_path: Path) -> tuple[list[_IdActor], list[_IdLegacy]]:
    """Parse [[mitama_actors]] and [[legacy_nanoids]] from deps.toml."""
    if not deps_path.exists():
        return [], []
    if tomllib is None:
        return [], []
    try:
        data = tomllib.loads(deps_path.read_text())
    except Exception:
        return [], []
    actors = [
        _IdActor(
            name=a.get("name", ""),
            domain=a.get("domain", ""),
            nanoid=a.get("nanoid", ""),
            did=a.get("did", ""),
            handles=list(a.get("handles", [])),
        )
        for a in data.get("mitama_actors", [])
        if a.get("name")
    ]
    legacies = [
        _IdLegacy(
            actor=l.get("actor", ""),
            nanoid=l.get("nanoid", ""),
            handle=l.get("handle", ""),
            did=l.get("did", ""),
        )
        for l in data.get("legacy_nanoids", [])
        if l.get("actor")
    ]
    return actors, legacies


def _resolve_cf_token() -> tuple[str, str]:
    """Resolve Cloudflare API token. Returns (token, source_key)."""
    for key in ("CLOUDFLARE_API_TOKEN", "CF_API_TOKEN", "etzhayyim_CLOUDFLARE_API_TOKEN"):
        val = os.environ.get(key, "").strip()
        if val:
            return val, key
    # Try wrangler OAuth token
    home = Path.home()
    wrangler_cfg = home / "Library" / "Preferences" / ".wrangler" / "config" / "default.toml"
    if wrangler_cfg.exists():
        try:
            text = wrangler_cfg.read_text()
            m = re.search(r'oauth_token\s*=\s*"([^"]+)"', text)
            if m:
                return m.group(1), "wrangler_oauth"
        except Exception:
            pass
    return "", ""


def _build_desired_records(
    actors: list[_IdActor],
    legacies: list[_IdLegacy],
    include_txt: bool,
    include_nanoid: bool,
    zone_name: str,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    zone_suffix = "." + zone_name
    for a in actors:
        handle = a.domain or (a.handles[0] if a.handles else "")
        if not handle or not handle.endswith(zone_suffix):
            continue
        if include_txt and a.did:
            recs.append({
                "type": "TXT",
                "name": f"_atproto.{handle}",
                "content": f'"did={a.did}"',
                "ttl": 3600,
                "proxied": False,
                "comment": _DNS_TXT_COMMENT,
            })
    if include_nanoid:
        for l in legacies:
            if not l.handle or not l.handle.endswith(zone_suffix):
                continue
            recs.append({
                "type": "CNAME",
                "name": f"{l.nanoid}{zone_suffix}",
                "content": l.handle,
                "ttl": 3600,
                "proxied": True,
                "comment": _DNS_CNAME_COMMENT,
            })
    recs.sort(key=lambda r: (r["name"], r["type"]))
    return recs


def _diff_records(
    desired: list[dict[str, Any]],
    existing: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    existing_map: dict[tuple[str, str], dict[str, Any]] = {
        (r["name"], r["type"]): r for r in existing
    }
    plan: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for d in desired:
        k = (d["name"], d["type"])
        seen.add(k)
        if k in existing_map:
            e = existing_map[k]
            if e.get("content") == d["content"] and e.get("comment") == d.get("comment"):
                plan.append({"action": "keep", "record": d, "existing": e})
            else:
                upd = {**d, "id": e.get("id", "")}
                plan.append({
                    "action": "update",
                    "record": upd,
                    "existing": e,
                    "reason": f"content {e.get('content')!r} → {d['content']!r}",
                })
        else:
            plan.append({"action": "create", "record": d, "reason": "missing"})
    for k, e in existing_map.items():
        if k not in seen:
            plan.append({
                "action": "delete",
                "record": e,
                "existing": e,
                "reason": "orphan (not in deps.toml)",
            })
    return plan


def _cf_get(token: str, url: str) -> dict[str, Any]:
    resp = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _resolve_zone(token: str, zone_name: str) -> str:
    import urllib.parse
    url = f"https://api.cloudflare.com/client/v4/zones?name={urllib.parse.quote(zone_name)}"
    body = _cf_get(token, url)
    if not body.get("success") or not body.get("result"):
        raise click.ClickException(f"zone {zone_name!r} not found: {body.get('errors')}")
    return body["result"][0]["id"]


def _list_managed_records(token: str, zone_id: str) -> list[dict[str, Any]]:
    all_recs: list[dict[str, Any]] = []
    page = 1
    while True:
        url = (
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
            f"?per_page=1000&page={page}"
        )
        body = _cf_get(token, url)
        for r in body.get("result", []):
            if r.get("comment", "").startswith(_DNS_COMMENT_PREFIX):
                all_recs.append(r)
        ri = body.get("result_info", {})
        if ri.get("page", 1) >= ri.get("total_pages", 1):
            break
        page += 1
    return all_recs


def _apply_one(token: str, zone_id: str, plan_item: dict[str, Any]) -> None:
    action = plan_item["action"]
    rec = plan_item["record"]
    base = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if action == "create":
        resp = httpx.post(base, json=rec, headers=headers, timeout=15)
    elif action == "update":
        resp = httpx.patch(f"{base}/{rec['id']}", json=rec, headers=headers, timeout=15)
    elif action == "delete":
        resp = httpx.delete(f"{base}/{rec['id']}", headers=headers, timeout=15)
    else:
        return
    if resp.status_code >= 400:
        raise click.ClickException(f"CF API {resp.status_code}: {resp.text}")


def _emit_routing_map_ts(legacies: list[_IdLegacy]) -> str:
    sorted_l = sorted(legacies, key=lambda l: l.nanoid)
    lines = [
        "// legacy-nanoid-map.ts — Phase 3 grace period mapping table.\n",
        "//\n",
        "// Auto-generated by `etzhayyim dns-sync --emit-routing-map`. DO NOT EDIT BY HAND.\n",
        "// Source: deps.toml [[legacy_nanoids]]\n",
        "// Phase 4 cutover (2026-10-01, ADR-0021): this file is renamed to\n",
        "// legacy-nanoid-map.archived.ts and the import in worker.ts is removed.\n\n",
        "export const LEGACY_NANOID_MAP: Record<string, string> = {\n",
    ]
    for l in sorted_l:
        lines.append(f"  {json.dumps(l.nanoid)}: {json.dumps(l.handle)},\n")
    lines += [
        "}\n\n",
        "/**\n",
        " * Phase 4 deprecation window: when current time exceeds this, every legacy\n",
        " * lookup logs a high-severity warning. Intended to fire alarms in CF Analytics.\n",
        " */\n",
        "export const PHASE4_DEPRECATE_AT = new Date('2026-10-01T00:00:00Z')\n",
    ]
    return "".join(lines)


def _emit_yoro_mirror_ts(legacies: list[_IdLegacy]) -> str:
    sorted_l = sorted(legacies, key=lambda l: l.nanoid)
    lines = [
        "// legacy-nanoid-map.ts — Phase 3 grace period mapping table (yoro mirror).\n",
        "//\n",
        "// MIRROR OF: 50-infra/cloudflare/workers/routing-gateway/src/legacy-nanoid-map.ts\n",
        "// Both files are auto-generated from deps.toml [[legacy_nanoids]] by\n",
        "// `etzhayyim dns-sync --emit-routing-map`. Keep in sync until Phase 4 cutover\n",
        "// (2026-10-01, ADR-0021).\n",
        "//\n",
        "// Used by: routes/profile/[handle]/+page.server.ts to 301 redirect\n",
        "// /profile/{nanoid}.etzhayyim.com → /profile/{handle}.etzhayyim.com\n\n",
        "export const LEGACY_NANOID_MAP: Record<string, string> = {\n",
    ]
    for l in sorted_l:
        lines.append(f"  {json.dumps(l.nanoid)}: {json.dumps(l.handle)},\n")
    lines += [
        "};\n\n",
        "/**\n",
        " * Resolve `{nanoid}.etzhayyim.com` to canonical handle, or null if not a legacy nanoid.\n",
        " * Used by /profile/[handle] SSR redirect.\n",
        " */\n",
        "export function resolveLegacyHandle(handle: string): string | null {\n",
        "  const match = handle.match(/^([a-z0-9-]+)\\.etzhayyim\\.ai$/i);\n",
        "  if (!match) return null;\n",
        "  const nanoid = match[1].toLowerCase();\n",
        "  return LEGACY_NANOID_MAP[nanoid] ?? null;\n",
        "}\n",
    ]
    return "".join(lines)


def _find_services_range(src: str) -> tuple[int, int] | None:
    """Locate '"services": [...]' in JSONC. Returns (key_start, bracket_close+1) or None."""
    key = '"services"'
    key_start = src.find(key)
    if key_start < 0:
        return None
    i = key_start + len(key)
    while i < len(src) and src[i] in " \t\r\n":
        i += 1
    if i >= len(src) or src[i] != ":":
        return None
    i += 1
    while i < len(src) and src[i] in " \t\r\n":
        i += 1
    if i >= len(src) or src[i] != "[":
        return None
    depth = 0
    in_string = False
    escaped = False
    in_line_comment = False
    in_block_comment = False
    j = i
    while j < len(src):
        c = src[j]
        nxt = src[j + 1] if j + 1 < len(src) else "\x00"
        if in_line_comment:
            if c == "\n":
                in_line_comment = False
            j += 1
            continue
        if in_block_comment:
            if c == "*" and nxt == "/":
                in_block_comment = False
                j += 2
                continue
            j += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == '"':
                in_string = False
            j += 1
            continue
        if c == "/" and nxt == "/":
            in_line_comment = True
            j += 2
            continue
        if c == "/" and nxt == "*":
            in_block_comment = True
            j += 2
            continue
        if c == '"':
            in_string = True
            j += 1
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return (key_start, j + 1)
        j += 1
    return None


def _patch_wrangler_bindings(path: Path, actors: list[_IdActor]) -> tuple[str, int]:
    src = path.read_text()
    sorted_actors = sorted(actors, key=lambda a: a.name)
    parts = [
        '"services": [\n',
        '    { "binding": "PDS_WORKER",    "service": "etzhayyim-pds-2603241700" },\n',
        '    { "binding": "PLC_DIRECTORY", "service": "etzhayyim-plc-directory" }',
    ]
    emitted = 2
    for a in sorted_actors:
        handle = a.domain or (a.handles[0] if a.handles else "")
        if not handle:
            continue
        label = handle.split(".")[0]
        binding = "WORKER_" + label.upper().replace("-", "_")
        service = "etzhayyim-actor-" + label
        parts.append(f',\n    {{ "binding": {json.dumps(binding)}, "service": {json.dumps(service)} }}')
        emitted += 1
    parts.append("\n  ]")
    new_services = "".join(parts)
    rng = _find_services_range(src)
    if rng:
        patched = src[: rng[0]] + new_services + src[rng[1] :]
    else:
        last_brace = src.rfind("}")
        if last_brace < 0:
            raise click.ClickException("wrangler.jsonc: no closing brace found")
        patched = src[:last_brace] + ",\n  " + new_services + "\n" + src[last_brace:]
    return patched, emitted


@click.command("dns-sync")
@click.option("--apply", is_flag=True, default=False, help="Apply changes (default: dry-run)")
@click.option("--json", "json_out", is_flag=True, default=False, help="Emit JSON plan")
@click.option("--zone-name", default="etzhayyim.com", show_default=True, help="Cloudflare zone name")
@click.option("--deps", "deps_path", default=None, help="Path to deps.toml")
@click.option("--include-nanoid/--no-include-nanoid", default=True, help="Include legacy nanoid CNAMEs")
@click.option("--include-txt/--no-include-txt", default=True, help="Include _atproto TXT records")
@click.option("--no-cf", is_flag=True, default=False, help="Offline mode: skip CF API, print desired records only")
@click.option("--emit-routing-map", "emit_map", default="", help="Write routing-gateway TS map to PATH and exit")
@click.option("--no-yoro-mirror", is_flag=True, default=False, help="Skip yoro mirror when --emit-routing-map is used")
@click.option(
    "--yoro-mirror-path",
    default="60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/server/legacy-nanoid-map.ts",
    help="Yoro mirror output path (relative to cwd)",
)
@click.option("--populate-bindings", "emit_bindings", default="", help="Patch wrangler.jsonc at PATH with Service Bindings and exit")
@click.option("--workspace-dir", default=None, help="Workspace root (default: git root)")
def dns_sync(
    apply: bool,
    json_out: bool,
    zone_name: str,
    deps_path: str | None,
    include_nanoid: bool,
    include_txt: bool,
    no_cf: bool,
    emit_map: str,
    no_yoro_mirror: bool,
    yoro_mirror_path: str,
    emit_bindings: str,
    workspace_dir: str | None,
) -> None:
    """DNS synchronization from deps.toml [[mitama_actors]] + [[legacy_nanoids]] to Cloudflare DNS."""
    ws = _resolve_root(workspace_dir)
    resolved_deps = Path(deps_path) if deps_path else ws / "deps.toml"

    actors, legacies = _parse_identifier_tables(resolved_deps)
    if not actors and not emit_map and not emit_bindings and not json_out:
        click.echo(f"no [[mitama_actors]] found in {resolved_deps}", err=True)

    # --emit-routing-map: generate TS files and exit
    if emit_map:
        ts = _emit_routing_map_ts(legacies)
        Path(emit_map).write_text(ts)
        click.echo(f"✓ routing-gateway map written: {emit_map} ({len(legacies)} entries)")
        if not no_yoro_mirror:
            yoro_ts = _emit_yoro_mirror_ts(legacies)
            Path(yoro_mirror_path).write_text(yoro_ts)
            click.echo(f"✓ yoro mirror written:        {yoro_mirror_path} ({len(legacies)} entries)")
        return

    # --populate-bindings: patch wrangler.jsonc and exit
    if emit_bindings:
        patched, count = _patch_wrangler_bindings(Path(emit_bindings), actors)
        Path(emit_bindings).write_text(patched)
        click.echo(f"✓ wrangler.jsonc bindings updated: {emit_bindings} ({count} Service Bindings)")
        return

    desired = _build_desired_records(actors, legacies, include_txt, include_nanoid, zone_name)

    # Offline mode
    if no_cf:
        actors_in_zone = sum(
            1 for a in actors
            if (a.domain or (a.handles[0] if a.handles else "")).endswith("." + zone_name)
        )
        if json_out:
            by_type: dict[str, int] = {}
            for r in desired:
                by_type[r["type"]] = by_type.get(r["type"], 0) + 1
            click.echo(json.dumps({
                "zone": zone_name,
                "mode": "offline",
                "actors": actors_in_zone,
                "actors_total": len(actors),
                "actors_in_zone": actors_in_zone,
                "actors_excluded": len(actors) - actors_in_zone,
                "legacy": len(legacies),
                "desired_count": len(desired),
                "desired": desired,
            }, ensure_ascii=False, indent=2))
        else:
            click.echo("etzhayyim dns-sync — offline mode (no Cloudflare API)")
            click.echo("================================================")
            click.echo(f"zone:    {zone_name}")
            click.echo(f"actors:  {actors_in_zone}  legacy: {len(legacies)}  desired: {len(desired)}")
            click.echo()
            by_type = {}
            for r in desired:
                by_type[r["type"]] = by_type.get(r["type"], 0) + 1
            click.echo(f"Records by type: TXT={by_type.get('TXT', 0)} CNAME={by_type.get('CNAME', 0)} A={by_type.get('A', 0)}")
            click.echo()
            for r in desired:
                click.echo(f"  {r['type']:<6}  {r['name']:<45}  {r['content']}")
        return

    # CF API mode
    token, token_src = _resolve_cf_token()
    if not token:
        raise click.ClickException(
            "no Cloudflare API token (CLOUDFLARE_API_TOKEN, CF_API_TOKEN, or wrangler OAuth)"
        )
    zone_id = _resolve_zone(token, zone_name)
    existing = _list_managed_records(token, zone_id)
    plan = _diff_records(desired, existing)

    actions: dict[str, int] = {}
    for p in plan:
        actions[p["action"]] = actions.get(p["action"], 0) + 1

    if json_out:
        click.echo(json.dumps({
            "zone": zone_name,
            "token_from": token_src,
            "actions": actions,
            "plan": plan,
            "apply": apply,
        }, ensure_ascii=False, indent=2))
        return

    click.echo("etzhayyim dns-sync — ADR-0013 Phase 3")
    click.echo("=================================")
    click.echo(f"zone:         {zone_name} (id={zone_id})")
    click.echo(f"token from:   {token_src}")
    click.echo(f"actors:       {len(actors)}")
    click.echo(f"legacy:       {len(legacies)}")
    click.echo(f"desired recs: {len(desired)}  existing managed: {len(existing)}")
    click.echo()
    click.echo(
        f"plan: create={actions.get('create', 0)} update={actions.get('update', 0)} "
        f"delete={actions.get('delete', 0)} keep={actions.get('keep', 0)}"
    )
    click.echo()

    for kind in ("create", "update", "delete"):
        items = [p for p in plan if p["action"] == kind]
        if not items:
            continue
        click.echo(f"── {kind.upper()} ({len(items)})")
        for p in items:
            click.echo(
                f"  {p['record']['type']:<6}  {p['record']['name']:<40}  "
                f"{p['record']['content']}  {p.get('reason', '')}"
            )
        click.echo()

    if not apply:
        click.echo("dry-run: no changes applied. Use --apply to execute.")
        return

    click.echo(f"Applying {actions.get('create', 0) + actions.get('update', 0) + actions.get('delete', 0)} changes...")
    applied = 0
    failed = 0
    for p in plan:
        if p["action"] == "keep":
            continue
        try:
            _apply_one(token, zone_id, p)
            click.echo(f"  OK   {p['action']} {p['record']['type']} {p['record']['name']}")
            applied += 1
            time.sleep(0.05)
        except Exception as exc:
            click.echo(f"  FAIL {p['action']} {p['record']['type']} {p['record']['name']}: {exc}", err=True)
            failed += 1
    click.echo(f"\napplied={applied} failed={failed}")
    if failed > 0:
        sys.exit(1)
