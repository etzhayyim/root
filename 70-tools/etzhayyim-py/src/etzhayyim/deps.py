"""deps — deps.toml analysis, drift detection, and KV sync.

Reads deps.toml from workspace root and reports on components, migrations,
conventions, and drift between declared and actual state.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import click
import httpx

from .shannon import _resolve_root

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


def _load(ws: Path) -> dict:
    deps = ws / "deps.toml"
    if not deps.exists() or tomllib is None:
        return {}
    try:
        return tomllib.loads(deps.read_text())
    except Exception:
        return {}


@click.group("deps", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def deps(ctx: click.Context, workspace_dir: str | None, json_out: bool) -> None:
    """deps.toml analysis — migrations, conventions, component registry."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    data = _load(ws)
    if json_out:
        summary = {
            "has_deps_toml": bool(data),
            "migrations": len(data.get("migrations", [])),
            "conventions": len(data.get("conventions", [])),
            "projects": len(data.get("projects", [])),
            "mitama_actors": len(data.get("mitama_actors", [])),
        }
        click.echo(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        click.echo(f"deps.toml: {'found' if data else 'not found'}")
        if data:
            click.echo(f"  migrations: {len(data.get('migrations', []))}")
            click.echo(f"  conventions: {len(data.get('conventions', []))}")
            click.echo(f"  projects: {len(data.get('projects', []))}")
            click.echo(f"  mitama_actors: {len(data.get('mitama_actors', []))}")


@deps.command("migrations")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--status", "filter_status", default="",
              help="Filter by status (pending/done/blocked)")
def deps_migrations(workspace_dir: str | None, json_out: bool, filter_status: str) -> None:
    """List migrations from deps.toml."""
    ws = _resolve_root(workspace_dir)
    data = _load(ws)
    migrations = data.get("migrations", [])
    if filter_status:
        migrations = [m for m in migrations if m.get("status") == filter_status]
    if json_out:
        click.echo(json.dumps(migrations, ensure_ascii=False, indent=2))
    else:
        click.echo(f"migrations: {len(migrations)}")
        for m in migrations:
            status = m.get("status", "?")
            name = m.get("id") or m.get("name", "?")
            click.echo(f"  [{status:8}] {name}")


@deps.command("conventions")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def deps_conventions(workspace_dir: str | None, json_out: bool) -> None:
    """List conventions from deps.toml."""
    ws = _resolve_root(workspace_dir)
    data = _load(ws)
    conventions = data.get("conventions", [])
    if json_out:
        click.echo(json.dumps(conventions, ensure_ascii=False, indent=2))
    else:
        for c in conventions:
            name = c.get("id") or c.get("name", "?")
            desc = c.get("description", "")[:60]
            click.echo(f"  {name}  {desc}")


@deps.command("projects")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--filter", "filter_text", default="")
def deps_projects(workspace_dir: str | None, json_out: bool, filter_text: str) -> None:
    """List projects from deps.toml."""
    ws = _resolve_root(workspace_dir)
    data = _load(ws)
    projects = data.get("projects", [])
    if filter_text:
        projects = [p for p in projects if filter_text in str(p)]
    if json_out:
        click.echo(json.dumps(projects, ensure_ascii=False, indent=2))
    else:
        click.echo(f"projects: {len(projects)}")
        for p in projects:
            name = p.get("id") or p.get("name", str(p)[:40]) if isinstance(p, dict) else str(p)
            click.echo(f"  {name}")


@deps.command("actors")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def deps_actors(workspace_dir: str | None, json_out: bool) -> None:
    """List Mitama actors from deps.toml."""
    ws = _resolve_root(workspace_dir)
    data = _load(ws)
    actors = data.get("mitama_actors", [])
    if json_out:
        click.echo(json.dumps(actors, ensure_ascii=False, indent=2))
    else:
        click.echo(f"mitama_actors: {len(actors)}")
        for a in actors:
            nanoid = a.get("nanoid", "?") if isinstance(a, dict) else str(a)
            name = a.get("name", "") if isinstance(a, dict) else ""
            click.echo(f"  {nanoid}  {name}")


def _resolve_cf_token_deps() -> str:
    for var in ("CLOUDFLARE_API_TOKEN", "CF_API_TOKEN", "etzhayyim_CLOUDFLARE_API_TOKEN"):
        t = os.environ.get(var, "").strip()
        if t:
            return t
    return ""


def _build_kv_records(actors: list[dict]) -> list[dict]:
    sorted_actors = sorted(actors, key=lambda a: a.get("name", "") if isinstance(a, dict) else "")
    entries = []
    names = []
    for a in sorted_actors:
        if not isinstance(a, dict):
            continue
        name = a.get("name", "")
        if not name:
            continue
        handles = a.get("handles", [])
        handle = a.get("domain", "") or (handles[0] if handles else "")
        rec = {"name": name, "did": a.get("did", ""), "handle": handle}
        nanoid = a.get("nanoid", "")
        if nanoid:
            rec["nanoid"] = nanoid
        legacy = a.get("legacy_did_web", "")
        if legacy:
            rec["legacyDidWeb"] = legacy
        desc = a.get("description", "")
        if desc:
            rec["description"] = desc
        entries.append({"key": f"actor:{name}", "value": json.dumps(rec)})
        names.append(name)
    entries.append({"key": "actors:index", "value": json.dumps(names)})
    return entries


def _cf_kv_list(token: str, account_id: str, namespace_id: str) -> dict[str, bool]:
    existing: dict[str, bool] = {}
    cursor = ""
    while True:
        url = (f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
               f"/storage/kv/namespaces/{namespace_id}/keys?limit=1000")
        if cursor:
            url += f"&cursor={cursor}"
        resp = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        for k in body.get("result", []):
            n = k.get("name", "")
            if n.startswith("actor:") or n.startswith("actors:"):
                existing[n] = True
        cursor = body.get("result_info", {}).get("cursor", "")
        if not cursor:
            break
    return existing


def _cf_kv_bulk_put(token: str, account_id: str, namespace_id: str,
                    entries: list[dict]) -> None:
    url = (f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
           f"/storage/kv/namespaces/{namespace_id}/bulk")
    resp = httpx.put(url, json=entries,
                     headers={"Authorization": f"Bearer {token}",
                              "Content-Type": "application/json"}, timeout=60)
    if resp.status_code >= 400:
        raise click.ClickException(f"CF API {resp.status_code}: {resp.text[:200]}")


@deps.command("kv-sync")
@click.option("--apply", is_flag=True, default=False,
              help="PUT keys to Cloudflare KV (default: dry-run)")
@click.option("--diff", "show_diff", is_flag=True, default=False,
              help="Fetch existing KV state and report add/update/delete plan")
@click.option("--no-cf", "no_cf", is_flag=True, default=False,
              help="Offline: print desired payload only, skip CF API")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--account-id", default=None, envvar="CF_ACCOUNT_ID")
@click.option("--namespace-id", default=None, envvar="CF_DEPS_REGISTRY_KV_ID")
@click.option("--workspace-dir", default=None)
@click.option("--deps", "deps_path", default=None,
              help="Path to deps.toml (default: workspace root deps.toml)")
def deps_kv_sync(apply: bool, show_diff: bool, no_cf: bool, json_out: bool,
                 account_id: str | None, namespace_id: str | None,
                 workspace_dir: str | None, deps_path: str | None) -> None:
    """Sync [[mitama_actors]] from deps.toml to Cloudflare KV DEPS_REGISTRY."""
    ws = _resolve_root(workspace_dir)
    if deps_path:
        toml_path = Path(deps_path)
    else:
        toml_path = ws / "deps.toml"

    if tomllib is None:
        raise click.ClickException("tomllib not available (Python < 3.11 requires tomli)")
    if not toml_path.exists():
        raise click.ClickException(f"deps.toml not found: {toml_path}")

    try:
        data = tomllib.loads(toml_path.read_text())
    except Exception as e:
        raise click.ClickException(f"parse deps.toml: {e}")

    actors = data.get("mitama_actors", [])
    if not actors:
        raise click.ClickException("no [[mitama_actors]] in deps.toml")

    entries = _build_kv_records(actors)

    if no_cf:
        if json_out:
            click.echo(json.dumps({
                "mode": "offline",
                "actors": len(actors),
                "desired_count": len(entries),
                "desired": entries,
            }, ensure_ascii=False, indent=2))
        else:
            click.echo("etzhayyim deps kv-sync — offline (no Cloudflare API)")
            click.echo("=" * 48)
            click.echo(f"actors:          {len(actors)}")
            click.echo(f"desired KV keys: {len(entries)}  ({len(actors)} actors + 1 actors:index)\n")
            for e in entries[:15]:
                val = e["value"]
                if len(val) > 80:
                    val = val[:80] + "…"
                click.echo(f"  PUT  {e['key']:<28}  {val}")
            if len(entries) > 15:
                click.echo(f"  ... ({len(entries) - 15} more)")
        return

    # CF API needed
    token = _resolve_cf_token_deps()
    if not token:
        raise click.ClickException(
            "no Cloudflare API token (CLOUDFLARE_API_TOKEN, CF_API_TOKEN)")
    acct = account_id or os.environ.get("CF_ACCOUNT_ID", "").strip()
    if not acct:
        raise click.ClickException("--account-id required (or set CF_ACCOUNT_ID)")
    ns = namespace_id or os.environ.get("CF_DEPS_REGISTRY_KV_ID", "").strip()
    if not ns:
        raise click.ClickException("--namespace-id required (or set CF_DEPS_REGISTRY_KV_ID)")

    if show_diff:
        try:
            existing = _cf_kv_list(token, acct, ns)
        except httpx.HTTPError as e:
            raise click.ClickException(f"list KV: {e}")
        desired_set = {e["key"] for e in entries}
        plan = []
        action_counts: dict[str, int] = {"add": 0, "update": 0, "delete": 0}
        for e in entries:
            action = "update" if e["key"] in existing else "add"
            plan.append({"action": action, "key": e["key"]})
            action_counts[action] += 1
        for k in sorted(existing):
            if k not in desired_set:
                plan.append({"action": "delete", "key": k})
                action_counts["delete"] += 1
        if json_out:
            click.echo(json.dumps({
                "account": acct, "namespace": ns,
                "existing": len(existing), "desired": len(entries),
                "by_action": action_counts, "plan": plan,
            }, ensure_ascii=False, indent=2))
        else:
            click.echo("etzhayyim deps kv-sync --diff")
            click.echo("=" * 25)
            click.echo(f"account:  {acct}")
            click.echo(f"KV ns:    {ns}")
            click.echo(f"existing: {len(existing)} keys  desired: {len(entries)}")
            click.echo(f"plan: add={action_counts['add']} update={action_counts['update']} "
                       f"delete={action_counts['delete']}\n")
            for p in plan:
                if p["action"] != "keep":
                    click.echo(f"  {p['action'].upper():<6}  {p['key']}")
        return

    if not apply:
        click.echo("etzhayyim deps kv-sync — dry-run")
        click.echo("=" * 27)
        click.echo(f"account: {acct}")
        click.echo(f"KV ns:   {ns}")
        click.echo(f"actors:  {len(actors)}")
        click.echo(f"desired: {len(entries)} KV keys (would PUT)")
        click.echo("\nUse --apply to execute, or --diff to see existing-vs-desired plan.")
        return

    click.echo(f"Applying KV bulk PUT ({len(entries)} keys)...")
    try:
        _cf_kv_bulk_put(token, acct, ns, entries)
    except httpx.HTTPError as e:
        raise click.ClickException(f"bulk PUT: {e}")
    click.echo(f"✓ DEPS_REGISTRY KV synced: {len(entries)} keys")


@deps.command("drift")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def deps_drift(workspace_dir: str | None, json_out: bool) -> None:
    """Check for drift between deps.toml and working tree (basic checks)."""
    ws = _resolve_root(workspace_dir)
    data = _load(ws)
    issues = []

    # Check for done migrations still present
    done = [m for m in data.get("migrations", []) if m.get("status") == "done"]
    if done:
        issues.append({"type": "stale_done_migrations", "count": len(done)})

    # Check if projects in deps.toml exist on disk
    apps_dir = ws / "60-apps"
    for proj in data.get("projects", []):
        proj_name = proj.get("id") or proj.get("name", "") if isinstance(proj, dict) else str(proj)
        if proj_name and apps_dir.exists():
            match = list(apps_dir.glob(f"*{proj_name}*"))
            if not match:
                issues.append({"type": "missing_project_dir", "project": proj_name})

    if json_out:
        click.echo(json.dumps({"issues": issues}, ensure_ascii=False, indent=2))
    else:
        if not issues:
            click.echo("  no drift detected")
        else:
            for issue in issues:
                click.echo(f"  {issue['type']}: {issue}")


# ── deps mv ────────────────────────────────────────────────────────────────────

_DEPS_MV_STATEMENTS = [
    """\
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deps_component_live AS
WITH components AS (
  SELECT did AS component_did FROM vertex_actor WHERE did IS NOT NULL
  UNION
  SELECT did AS component_did FROM vertex_actor_manifest WHERE did IS NOT NULL
  UNION
  SELECT did AS component_did FROM vertex_capability WHERE did IS NOT NULL
  UNION
  SELECT did AS component_did FROM vertex_raci WHERE did IS NOT NULL
  UNION
  SELECT repo AS component_did FROM vertex_did WHERE repo LIKE 'did:%'
  UNION
  SELECT src_vid AS component_did FROM edge_capability WHERE src_vid LIKE 'did:%'
  UNION
  SELECT dst_vid AS component_did FROM edge_capability WHERE dst_vid LIKE 'did:%'
  UNION
  SELECT src_vid AS component_did FROM edge_governance WHERE src_vid LIKE 'did:%'
  UNION
  SELECT dst_vid AS component_did FROM edge_governance WHERE dst_vid LIKE 'did:%'
  UNION
  SELECT src_vid AS component_did FROM edge_requires WHERE src_vid LIKE 'did:%'
  UNION
  SELECT dst_vid AS component_did FROM edge_requires WHERE dst_vid LIKE 'did:%'
  UNION
  SELECT src_vid AS component_did FROM edge_in_app WHERE src_vid LIKE 'did:%'
  UNION
  SELECT dst_vid AS component_did FROM edge_in_app WHERE dst_vid LIKE 'did:%'
  UNION
  SELECT src_vid AS component_did FROM edge_in_project WHERE src_vid LIKE 'did:%'
  UNION
  SELECT dst_vid AS component_did FROM edge_in_project WHERE dst_vid LIKE 'did:%'
),
actor_meta AS (
  SELECT
    did AS component_did,
    MAX(COALESCE(display_name, name, handle)) AS component_name,
    MAX(COALESCE(project, '')) AS project,
    MAX(COALESCE(nanoid, '')) AS nanoid
  FROM vertex_actor
  WHERE did IS NOT NULL
  GROUP BY did
),
manifest_meta AS (
  SELECT
    did AS component_did,
    MAX(COALESCE(display_name, name)) AS component_name,
    MAX(COALESCE(nanoid, '')) AS nanoid
  FROM vertex_actor_manifest
  WHERE did IS NOT NULL
  GROUP BY did
),
capability_vertex_counts AS (
  SELECT did AS component_did, COUNT(*)::bigint AS capability_vertex_count
  FROM vertex_capability WHERE did IS NOT NULL GROUP BY did
),
capability_edge_counts AS (
  SELECT component_did, COUNT(*)::bigint AS capability_edge_count
  FROM (
    SELECT src_vid AS component_did FROM edge_capability WHERE src_vid LIKE 'did:%'
    UNION ALL
    SELECT dst_vid AS component_did FROM edge_capability WHERE dst_vid LIKE 'did:%'
  ) s GROUP BY component_did
),
raci_counts AS (
  SELECT did AS component_did, COUNT(*)::bigint AS raci_count
  FROM vertex_raci WHERE did IS NOT NULL GROUP BY did
),
governance_vertex_counts AS (
  SELECT component_did, SUM(governance_vertex_count)::bigint AS governance_vertex_count
  FROM (
    SELECT repo AS component_did, COUNT(*)::bigint AS governance_vertex_count
    FROM vertex_governance WHERE repo LIKE 'did:%' GROUP BY repo
    UNION ALL
    SELECT repo AS component_did, COUNT(*)::bigint AS governance_vertex_count
    FROM vertex_governance_contract WHERE repo LIKE 'did:%' GROUP BY repo
  ) s GROUP BY component_did
),
governance_edge_counts AS (
  SELECT component_did, COUNT(*)::bigint AS governance_edge_count
  FROM (
    SELECT src_vid AS component_did FROM edge_governance WHERE src_vid LIKE 'did:%'
    UNION ALL
    SELECT dst_vid AS component_did FROM edge_governance WHERE dst_vid LIKE 'did:%'
  ) s GROUP BY component_did
),
dependency_edge_counts AS (
  SELECT component_did, COUNT(*)::bigint AS dependency_edge_count
  FROM (
    SELECT src_vid AS component_did FROM edge_requires WHERE src_vid LIKE 'did:%'
    UNION ALL
    SELECT dst_vid AS component_did FROM edge_requires WHERE dst_vid LIKE 'did:%'
  ) s GROUP BY component_did
),
resource_flow_counts AS (
  SELECT component_did, COUNT(*)::bigint AS resource_flow_count
  FROM (
    SELECT src_vid AS component_did FROM edge_in_app WHERE src_vid LIKE 'did:%'
    UNION ALL
    SELECT dst_vid AS component_did FROM edge_in_app WHERE dst_vid LIKE 'did:%'
    UNION ALL
    SELECT src_vid AS component_did FROM edge_in_project WHERE src_vid LIKE 'did:%'
    UNION ALL
    SELECT dst_vid AS component_did FROM edge_in_project WHERE dst_vid LIKE 'did:%'
  ) s GROUP BY component_did
)
SELECT
  c.component_did,
  COALESCE(a.component_name, m.component_name, c.component_did) AS component_name,
  COALESCE(a.project, '') AS project,
  COALESCE(a.nanoid, m.nanoid, '') AS nanoid,
  COALESCE(cv.capability_vertex_count, 0) AS capability_vertex_count,
  COALESCE(ce.capability_edge_count, 0) AS capability_edge_count,
  COALESCE(r.raci_count, 0) AS raci_count,
  COALESCE(gv.governance_vertex_count, 0) AS governance_vertex_count,
  COALESCE(ge.governance_edge_count, 0) AS governance_edge_count,
  COALESCE(dep.dependency_edge_count, 0) AS dependency_edge_count,
  COALESCE(flow.resource_flow_count, 0) AS resource_flow_count,
  CASE
    WHEN COALESCE(cv.capability_vertex_count, 0)
       + COALESCE(ce.capability_edge_count, 0)
       + COALESCE(r.raci_count, 0)
       + COALESCE(gv.governance_vertex_count, 0)
       + COALESCE(ge.governance_edge_count, 0)
       + COALESCE(dep.dependency_edge_count, 0)
       + COALESCE(flow.resource_flow_count, 0) = 0
    THEN true ELSE false
  END AS isolated
FROM components c
LEFT JOIN actor_meta a ON a.component_did = c.component_did
LEFT JOIN manifest_meta m ON m.component_did = c.component_did
LEFT JOIN capability_vertex_counts cv ON cv.component_did = c.component_did
LEFT JOIN capability_edge_counts ce ON ce.component_did = c.component_did
LEFT JOIN raci_counts r ON r.component_did = c.component_did
LEFT JOIN governance_vertex_counts gv ON gv.component_did = c.component_did
LEFT JOIN governance_edge_counts ge ON ge.component_did = c.component_did
LEFT JOIN dependency_edge_counts dep ON dep.component_did = c.component_did
LEFT JOIN resource_flow_counts flow ON flow.component_did = c.component_did""",
    """\
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_deps_summary_live AS
SELECT
  COUNT(*)::bigint AS total_components,
  SUM(CASE WHEN capability_vertex_count + capability_edge_count > 0 THEN 1 ELSE 0 END)::bigint AS capability_ready_components,
  SUM(CASE WHEN governance_vertex_count + governance_edge_count > 0 THEN 1 ELSE 0 END)::bigint AS governance_ready_components,
  SUM(CASE WHEN raci_count > 0 THEN 1 ELSE 0 END)::bigint AS raci_ready_components,
  SUM(CASE WHEN dependency_edge_count > 0 THEN 1 ELSE 0 END)::bigint AS dependency_ready_components,
  SUM(CASE WHEN resource_flow_count > 0 THEN 1 ELSE 0 END)::bigint AS resource_flow_ready_components,
  SUM(CASE WHEN isolated THEN 1 ELSE 0 END)::bigint AS isolated_components,
  ROUND(100.0 * SUM(CASE WHEN capability_vertex_count + capability_edge_count > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS capability_coverage,
  ROUND(100.0 * SUM(CASE WHEN governance_vertex_count + governance_edge_count > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS governance_coverage,
  ROUND(100.0 * SUM(CASE WHEN raci_count > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS raci_coverage,
  ROUND(100.0 * SUM(CASE WHEN dependency_edge_count > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS dependency_coverage,
  ROUND(100.0 * SUM(CASE WHEN resource_flow_count > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS resource_flow_coverage,
  ROUND(
    GREATEST(0, (
      (100.0 * SUM(CASE WHEN capability_vertex_count + capability_edge_count > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) +
      (100.0 * SUM(CASE WHEN governance_vertex_count + governance_edge_count > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) +
      (100.0 * SUM(CASE WHEN raci_count > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) +
      (100.0 * SUM(CASE WHEN dependency_edge_count > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) +
      (100.0 * SUM(CASE WHEN resource_flow_count > 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0))
    ) / 5.0 -
    (100.0 * SUM(CASE WHEN isolated THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) * 0.2),
    1
  ) AS overall_score
FROM mv_deps_component_live""",
]


def _deps_mv_name(stmt: str) -> str:
    words = stmt.split()
    for i, word in enumerate(words):
        if word.upper() == "EXISTS" and i + 1 < len(words):
            return words[i + 1].rstrip(";").strip()
        if word.upper() == "VIEW" and i + 1 < len(words) and words[i + 1].upper() not in ("IF",):
            return words[i + 1].rstrip(";").strip()
    return "?"


@deps.command("mv")
@click.option("--apply", "apply_", is_flag=True, default=False,
              help="apply DDL to RisingWave (requires etzhayyim Go CLI)")
@click.option("--format", "fmt", default="sql", type=click.Choice(["sql", "text"]),
              show_default=True)
def deps_mv(apply_: bool, fmt: str) -> None:
    """Generate RisingWave MVs for deps live read models from vertex_/edge_ tables.

    Use --apply with the Go CLI: etzhayyim deps mv --apply
    """
    if apply_:
        raise click.ClickException(
            "--apply requires a live RisingWave connection. Use: etzhayyim deps mv --apply"
        )
    if fmt == "sql":
        click.echo("-- etzhayyim deps mv")
        click.echo("-- Generated from RisingWave vertex_/edge_ tables. No JSON snapshot dependency.")
        for stmt in _DEPS_MV_STATEMENTS:
            click.echo()
            click.echo(f"{stmt};")
    else:
        click.echo("deps_mv:")
        click.echo(f"  views: {len(_DEPS_MV_STATEMENTS)}")
        click.echo("  generated_from: risingwave vertex_* / edge_* tables only")
        for stmt in _DEPS_MV_STATEMENTS:
            click.echo(f"  - {_deps_mv_name(stmt)}")


# ── deps graph ─────────────────────────────────────────────────────────────────

def _load_layer_rules(ws: Path) -> list[dict]:
    """Load [app_layer.*] + [infra_layer.*] entries from deps.toml."""
    deps_file = ws / "deps.toml"
    if not deps_file.exists():
        return []
    try:
        data = tomllib.loads(deps_file.read_text(encoding="utf-8"))
    except Exception:
        return []
    layers = []
    for section_key, section_label in (("app_layer", "packages"), ("infra_layer", "infra")):
        section = data.get(section_key, {})
        for name, entry in section.items():
            if not isinstance(entry, dict):
                continue
            layers.append({
                "name": name,
                "layer": entry.get("layer", 0),
                "tags": entry.get("tags", []),
                "description": entry.get("description", ""),
                "depends_on": entry.get("depends_on", []),
                "paths": entry.get("paths", []),
                "section": section_label,
            })
    layers.sort(key=lambda l: (l["layer"], l["name"]))
    return layers


def _filter_layers(layers: list[dict], section: str, tag: str) -> list[dict]:
    if section not in ("all", ""):
        layers = [l for l in layers if l["section"] == section]
    if tag:
        layers = [l for l in layers if tag in l.get("tags", [])]
    return layers


def _render_deps_tree(layers: list[dict], section: str) -> str:
    by_layer: dict[int, list[dict]] = {}
    for l in layers:
        by_layer.setdefault(l["layer"], []).append(l)
    lines = [f"deps layer DAG  [{section}]", ""]
    for layer_num in sorted(by_layer):
        lines.append(f"Layer {layer_num}:")
        for entry in by_layer[layer_num]:
            dep_str = f"  ← {', '.join(entry['depends_on'])}" if entry["depends_on"] else ""
            tag_str = f"  [{','.join(entry['tags'])}]" if entry["tags"] else ""
            lines.append(f"  {entry['name']:<30}  {entry['description'][:40]}{tag_str}{dep_str}")
        lines.append("")
    return "\n".join(lines)


def _render_deps_mermaid(layers: list[dict], section: str) -> str:
    lines = [f"# deps layer DAG [{section}]", "", "```mermaid", "graph BT"]
    for entry in layers:
        safe = entry["name"].replace("-", "_").replace(".", "_")
        label = entry["name"]
        lines.append(f'  {safe}["{label}"]')
    lines.append("")
    for entry in layers:
        safe = entry["name"].replace("-", "_").replace(".", "_")
        for dep in entry["depends_on"]:
            dep_safe = dep.replace("-", "_").replace(".", "_")
            lines.append(f"  {dep_safe} --> {safe}")
    lines += ["```", ""]
    return "\n".join(lines)


@deps.command("governance-wit")
@click.option("--component-dir", "component_dir", default=".", show_default=True,
              help="App component directory (must contain wit/world.wit and src/app.ts)")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]),
              show_default=True)
def deps_governance_wit(component_dir: str, fmt: str) -> None:
    """Check app component WIT + governance compliance (local file analysis)."""
    import re
    import datetime

    comp = Path(component_dir).resolve()
    wit_file = comp / "wit" / "world.wit"
    app_ts = comp / "src" / "app.ts"
    manifest = comp / "magatama.jsonld"

    findings: list[str] = []
    world: dict = {"imports": [], "exports": [], "includes": []}
    mf: dict = {}

    if wit_file.exists():
        text = wit_file.read_text(errors="replace")
        world["imports"] = re.findall(r"^\s*import\s+([^;]+);", text, re.MULTILINE)
        world["exports"] = re.findall(r"^\s*export\s+([^;]+);", text, re.MULTILINE)
        world["includes"] = re.findall(r"^\s*include\s+([^;]+);", text, re.MULTILINE)
    else:
        findings.append("missing wit/world.wit")

    cmd_count = 0
    handle_count = 0
    explicit_governed = 0
    approval_count = 0
    traceability_count = 0
    auto_manifest = False

    if app_ts.exists():
        src = app_ts.read_text(errors="replace")
        cmd_count = len(re.findall(r'\.command\s*\(', src))
        handle_count = len(re.findall(r'\.(?:handle|handleStream)\s*\(', src))
        explicit_governed = len(re.findall(r'"governed"\s*:', src))
        approval_count = len(re.findall(r'"approval"\s*:', src))
        traceability_count = len(re.findall(r'"traceability"\s*:', src))
        auto_manifest = bool(re.search(r'registerManifest|auto.*manifest', src, re.IGNORECASE))
    else:
        findings.append("missing src/app.ts")

    if manifest.exists():
        try:
            mf = json.loads(manifest.read_text())
        except json.JSONDecodeError:
            findings.append("magatama.jsonld is not valid JSON")

    gov = mf.get("governance", {})
    raci = gov.get("raci", "")
    classification = gov.get("classification", "")
    if not raci:
        findings.append("governance.raci missing in magatama.jsonld")
    if not classification:
        findings.append("governance.classification missing in magatama.jsonld")

    wit_ok = wit_file.exists()
    app_ok = app_ts.exists()
    gov_ok = bool(raci and classification)

    n_checks = 3
    score = (int(wit_ok) + int(app_ok) + int(gov_ok)) / n_checks * 100
    if findings:
        verdict = "not-suitable" if score < 60 else "partial"
    else:
        verdict = "suitable"

    report = {
        "evaluatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "componentDir": str(comp),
        "score": round(score, 1),
        "verdict": verdict,
        "world": world,
        "manifest": {"raci": raci, "classification": classification},
        "implementation": {
            "runtime": mf.get("runtime", "unknown"),
            "path": str(app_ts) if app_ts.exists() else "",
            "commandCount": cmd_count,
            "handleCount": handle_count,
            "explicitGovernedCount": explicit_governed,
            "approvalCount": approval_count,
            "traceabilityCount": traceability_count,
            "autoManifestRegistered": auto_manifest,
        },
        "findings": findings,
    }

    if fmt == "json":
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        click.echo(f"component:    {comp}")
        click.echo(f"score:        {score:.1f}")
        click.echo(f"verdict:      {verdict}")
        click.echo(f"WIT imports:  {len(world['imports'])}")
        click.echo(f"commands:     {cmd_count}  handles: {handle_count}")
        click.echo(f"governance:   raci={raci or 'MISSING'}  class={classification or 'MISSING'}")
        if findings:
            click.echo("findings:")
            for f in findings:
                click.echo(f"  - {f}")
        if verdict == "not-suitable":
            raise SystemExit(1)


@deps.command("graph")
@click.option("--format", "fmt", default="tree",
              type=click.Choice(["tree", "mermaid", "json"]), show_default=True)
@click.option("--section", default="all",
              type=click.Choice(["packages", "infra", "all"]), show_default=True)
@click.option("--tag", default="", help="filter by tag")
@click.option("--workspace-dir", default=None)
def deps_graph(fmt: str, section: str, tag: str, workspace_dir: str | None) -> None:
    """Visualize the layer DAG from deps.toml [app_layer.*] + [infra_layer.*]."""
    ws = _resolve_root(workspace_dir)
    layers = _load_layer_rules(ws)
    layers = _filter_layers(layers, section, tag)

    if not layers:
        click.echo(json.dumps({"layers": [], "section": section}))
        return

    if fmt == "json":
        click.echo(json.dumps({"section": section, "layers": layers}, ensure_ascii=False, indent=2))
    elif fmt == "mermaid":
        click.echo(_render_deps_mermaid(layers, section))
    else:
        click.echo(_render_deps_tree(layers, section))


# ── deps score ──────────────────────────────────────────────────────────────────

def _fetch_deps_graph(base_url: str, timeout: int) -> dict:
    url = base_url.rstrip("/") + "/api/deps/graph"
    try:
        resp = httpx.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        raise click.ClickException(f"fetch {url}: {e}")
    except Exception as e:
        raise click.ClickException(f"parse deps graph JSON: {e}")


def _summarize_deps_graph(graph: dict) -> dict:
    summary = graph.get("summary", {})
    linker = graph.get("linkerStatus", {})
    lk_summary = linker.get("summary", {})
    total = lk_summary.get("totalLinks", 0) or summary.get("totalResolvedLinks", 0) + summary.get("totalUnresolvedLinks", 0)
    resolved = lk_summary.get("resolvedLinks", 0) or summary.get("totalResolvedLinks", 0)
    unresolved = lk_summary.get("unresolvedLinks", 0) or summary.get("totalUnresolvedLinks", 0)
    coverage = round(resolved / total, 4) if total else 0.0
    scorecard = graph.get("scorecard", {}) or {}
    return {
        "generatedAt": graph.get("generatedAt", ""),
        "totalLinks": total,
        "resolvedLinks": resolved,
        "unresolvedLinks": unresolved,
        "linkCoverageRate": coverage,
        "totalComponents": lk_summary.get("totalComponents", summary.get("totalLinkerComponents", 0)),
        "isolatedCount": summary.get("totalIsolatedComponents", scorecard.get("isolatedComponentsCount", 0)),
        "governanceUnresolved": summary.get("governanceUnresolvedCount", 0),
        "workerRegisteredApps": summary.get("totalRegisteredApps", scorecard.get("workerRegisteredAppCount", 0)),
        "workerDeployedApps": summary.get("totalWorkerDeployedApps", scorecard.get("workerDeployedAppCount", 0)),
        "workerDeployCoverage": round(summary.get("workerDeployCoverageRate", scorecard.get("workerDeployCoverageRate", 0.0)), 4),
        "governanceCoverage": round(summary.get("governanceCoverageRate", scorecard.get("governanceCoverageRate", 0.0)), 4),
        "wprotoIntegrationScore": round(summary.get("wProtoIntegrationScore", scorecard.get("wProtoIntegrationScore", 0.0)), 1),
    }


@deps.command("score")
@click.option("--url", "base_url", default="https://deps.etzhayyim.com/",
              show_default=True, help="deps base URL")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]),
              show_default=True)
@click.option("--timeout-sec", "timeout_sec", default=20, type=int, show_default=True)
def deps_score(base_url: str, fmt: str, timeout_sec: int) -> None:
    """Fetch deps.etzhayyim.com graph and compute link coverage score."""
    graph = _fetch_deps_graph(base_url, timeout_sec)
    s = _summarize_deps_graph(graph)
    if fmt == "json":
        click.echo(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        click.echo(f"deps_score:")
        click.echo(f"  source_url: {base_url}")
        click.echo(f"  generated_at: {s['generatedAt']}")
        click.echo(f"  total_links: {s['totalLinks']}")
        click.echo(f"  resolved: {s['resolvedLinks']}")
        click.echo(f"  unresolved: {s['unresolvedLinks']}")
        click.echo(f"  link_coverage_rate: {s['linkCoverageRate']:.4f}")
        click.echo(f"  total_components: {s['totalComponents']}")
        click.echo(f"  isolated_count: {s['isolatedCount']}")
        click.echo(f"  governance_unresolved_count: {s['governanceUnresolved']}")
        click.echo(f"  worker_registered_app_count: {s['workerRegisteredApps']}")
        click.echo(f"  worker_deployed_app_count: {s['workerDeployedApps']}")
        click.echo(f"  worker_deploy_coverage: {s['workerDeployCoverage']:.4f}")
        click.echo(f"  governance_coverage: {s['governanceCoverage']:.4f}")
        click.echo(f"  wproto_integration_score: {s['wprotoIntegrationScore']:.1f}")


@deps.command("audit")
@click.option("--url", "base_url", default="https://deps.etzhayyim.com/",
              show_default=True, help="deps base URL")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]),
              show_default=True)
@click.option("--timeout-sec", "timeout_sec", default=20, type=int, show_default=True)
@click.option("--full-audit/--no-full-audit", default=True, show_default=True,
              help="trigger manual_refresh before score evaluation")
@click.option("--event", default="manual_refresh", show_default=True,
              help="hook event name")
@click.option("--app-id", "app_id", default="deps", show_default=True,
              help="app_id in hook payload")
@click.option("--wait-sec", "wait_sec", default=2, type=int, show_default=True,
              help="seconds to wait after refresh before fetching score")
def deps_audit(base_url: str, fmt: str, timeout_sec: int, full_audit: bool,
               event: str, app_id: str, wait_sec: int) -> None:
    """Trigger deps full-audit refresh and evaluate score."""
    import time
    refresh: dict = {"triggered": False, "status": "skipped", "event": event, "appId": app_id}

    if full_audit:
        hook_url = base_url.rstrip("/") + "/api/hooks/component"
        try:
            resp = httpx.post(
                hook_url,
                json={"schema": "etzhayyim:wproto/hook-envelope@v1", "event": event, "app": {"app_id": app_id}},
                timeout=timeout_sec,
            )
            msg = resp.text[:200] if resp.text else ""
            if resp.is_success:
                refresh = {"triggered": True, "hookUrl": hook_url, "status": "accepted",
                           "event": event, "appId": app_id, "message": msg}
            else:
                refresh = {"triggered": True, "hookUrl": hook_url, "status": "failed",
                           "event": event, "appId": app_id, "message": msg}
                raise click.ClickException(f"manual refresh hook failed: {msg}")
        except httpx.HTTPError as e:
            raise click.ClickException(f"post {hook_url}: {e}")
        if wait_sec > 0:
            time.sleep(wait_sec)

    graph = _fetch_deps_graph(base_url, timeout_sec)
    s = _summarize_deps_graph(graph)
    audit = {"mode": "full-audit" if full_audit else "score-only", "refresh": refresh, "score": s}

    if fmt == "json":
        click.echo(json.dumps(audit, ensure_ascii=False, indent=2))
    else:
        click.echo(f"deps_audit:")
        click.echo(f"  mode: {audit['mode']}")
        click.echo(f"  refresh_status: {refresh['status']}")
        if refresh.get("hookUrl"):
            click.echo(f"  refresh_hook_url: {refresh['hookUrl']}")
        if refresh.get("message"):
            click.echo(f"  refresh_message: {refresh['message']}")
        click.echo(f"  total_links: {s['totalLinks']}")
        click.echo(f"  resolved: {s['resolvedLinks']}")
        click.echo(f"  unresolved: {s['unresolvedLinks']}")
        click.echo(f"  link_coverage_rate: {s['linkCoverageRate']:.4f}")


@deps.command("export")
@click.option("--url", "base_url", default="https://deps.etzhayyim.com/",
              show_default=True, help="deps base URL")
@click.option("--out-dir", "out_dir", default="src/lib/data", show_default=True,
              help="output directory for exported JSON files")
@click.option("--score-name", "score_name", default="deps-score.json", show_default=True)
@click.option("--audit-name", "audit_name", default="deps-audit.json", show_default=True)
@click.option("--apps-name", "apps_name", default="deps-apps.json", show_default=True)
@click.option("--top", "top_n", default=15, type=int, show_default=True,
              help="number of top unresolved nodes to include")
@click.option("--timeout-sec", "timeout_sec", default=20, type=int, show_default=True)
@click.option("--no-refresh", "no_refresh", is_flag=True, default=False,
              help="skip fetching fresh graph from remote")
def deps_export(base_url: str, out_dir: str, score_name: str, audit_name: str,
                apps_name: str, top_n: int, timeout_sec: int, no_refresh: bool) -> None:
    """Export deps score/audit/apps JSON files for the frontend visualizer."""
    import time as _time
    output_path = Path(out_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    graph = {} if no_refresh else _fetch_deps_graph(base_url, timeout_sec)
    s = _summarize_deps_graph(graph)
    nodes: list[dict] = graph.get("nodes", [])

    unresolved = [n for n in nodes if not n.get("resolved", True)]
    unresolved.sort(key=lambda n: n.get("inDegree", 0), reverse=True)
    top_unresolved = unresolved[:top_n]

    score_data = {
        "evaluatedAt": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
        "sourceURL": base_url.rstrip("/") + "/api/deps/graph",
        "totalLinks": s["totalLinks"],
        "resolvedLinks": s["resolvedLinks"],
        "unresolvedLinks": s["unresolvedLinks"],
        "linkCoverageRate": s["linkCoverageRate"],
        "isolatedCount": s.get("isolatedCount", 0),
        "workerDeployCoverage": s.get("workerDeployCoverage", 0.0),
        "governanceCoverage": s.get("governanceCoverage", 0.0),
        "wprotoIntegrationScore": s.get("wprotoIntegrationScore", 0.0),
        "topUnresolvedNodes": top_unresolved,
        "hints": [],
    }
    audit_data = {
        "mode": "export",
        "refresh": {"triggered": False, "status": "skipped", "event": "export", "appId": "deps"},
        "score": score_data,
    }
    apps_data = {
        "apps": [
            {"did": n.get("id", ""), "label": n.get("label", ""), "resolved": n.get("resolved", True)}
            for n in nodes if n.get("type") == "app"
        ]
    }

    (output_path / score_name).write_text(json.dumps(score_data, ensure_ascii=False, indent=2))
    (output_path / audit_name).write_text(json.dumps(audit_data, ensure_ascii=False, indent=2))
    (output_path / apps_name).write_text(json.dumps(apps_data, ensure_ascii=False, indent=2))

    click.echo(f"deps_export:")
    click.echo(f"  score: {output_path / score_name}")
    click.echo(f"  audit: {output_path / audit_name}")
    click.echo(f"  apps: {output_path / apps_name}")
    click.echo(f"  total_links: {s['totalLinks']}  resolved: {s['resolvedLinks']}"
               f"  coverage: {s['linkCoverageRate']:.4f}")
    click.echo(f"  top_{top_n}_unresolved: {len(top_unresolved)}")


@deps.command("sql")
@click.option("--filter", "filter_did", default="", help="filter DIDs by prefix (e.g. did:web:isic)")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]),
              show_default=True)
@click.option("--timeout-sec", "timeout_sec", default=15, type=int, show_default=True)
def deps_sql(filter_did: str, fmt: str, timeout_sec: int) -> None:
    """DID-based SQL deps scoring from mv_deps_component_live (requires Go binary + RisingWave)."""
    raise click.ClickException(
        "deps sql requires direct RisingWave access (pgxpool). Use the Go binary: etzhayyim deps sql"
    )
