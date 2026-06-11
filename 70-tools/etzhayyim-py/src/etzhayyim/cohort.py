"""cohort — Cohort management (ADR-0028 cohort MV sharding).

Full sharding logic (bootstrap) requires the Go binary.
XRPC operations: seed, list, get, stats, create, fission, evidence, lineage,
lineage-stats, repair-edge, emit, dashboard, gen, forest, snapshot, diff, drift,
coverage, gap.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
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


@click.group("cohort")
def cohort() -> None:
    """Cohort management (ADR-0028 MV sharding)."""


@cohort.command("list")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--limit", default=50, type=int, show_default=True)
def cohort_list(pds: str | None, json_out: bool, limit: int) -> None:
    """List all cohorts."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.cohort.listCohorts",
                         params={"limit": limit}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            cohorts = data if isinstance(data, list) else data.get("cohorts", [])
            for c in cohorts:
                click.echo(f"  {c.get('id', '')}  {c.get('name', '')}  "
                           f"members={c.get('memberCount', '?')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@cohort.command("get")
@click.argument("cohort_id")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_get(cohort_id: str, pds: str | None, json_out: bool) -> None:
    """Get cohort details."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.cohort.getCohort",
                         params={"id": cohort_id}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@cohort.command("stats")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_stats(pds: str | None, json_out: bool) -> None:
    """Cohort sharding statistics."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.cohort.getStats",
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


@cohort.command("create")
@click.option("--name", required=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_create(name: str, pds: str | None, json_out: bool) -> None:
    """Create a new cohort."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(f"{pds_url}/xrpc/com.etzhayyim.cohort.createCohort",
                          json={"name": name}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"created cohort: {data.get('id', '')}  {name}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@cohort.command("seed")
@click.option("--segment", required=True, help="segment JSON or @file")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_seed(segment: str, pds: str | None, json_out: bool) -> None:
    """POST com.etzhayyim.cohort.seed — generate cohort from segment (idempotent)."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    if segment.startswith("@"):
        body = json.loads(Path(segment[1:]).read_text())
    else:
        body = json.loads(segment)
    try:
        resp = httpx.post(f"{pds_url}/xrpc/com.etzhayyim.cohort.seed",
                          json=body, headers=_auth_headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"seeded: {data.get('did', data.get('id', '?'))}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@cohort.command("gen")
@click.option("--pcf-l1", default="", help="PCF L1 category")
@click.option("--role", default="")
@click.option("--industry", default="")
@click.option("--seniority", default="")
@click.option("--locale", default="ja")
@click.option("-k", default=50, type=int, help="cohort size")
@click.option("--pds", default=None)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_gen(pcf_l1: str, role: str, industry: str, seniority: str,
               locale: str, k: int, pds: str | None, dry_run: bool, json_out: bool) -> None:
    """Build typed JSON-LD segment and seed as cohort."""
    segment = {
        "pcfL1": pcf_l1, "role": role, "industry": industry,
        "seniority": seniority, "locale": locale, "k": k,
    }
    if dry_run:
        click.echo(json.dumps(segment, ensure_ascii=False, indent=2))
        return
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(f"{pds_url}/xrpc/com.etzhayyim.cohort.seed",
                          json=segment, headers=_auth_headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"generated cohort: {data.get('did', data.get('id', '?'))}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@cohort.command("fission")
@click.option("--did", required=True, help="parent cohort DID")
@click.option("--pds", default=None)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_fission(did: str, pds: str | None, dry_run: bool, json_out: bool) -> None:
    """POST com.etzhayyim.cohort.fission — Phase C fission (posterior≥0.95 gate)."""
    if dry_run:
        click.echo(f"dry-run: would fission cohort {did}")
        return
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(f"{pds_url}/xrpc/com.etzhayyim.cohort.fission",
                          json={"did": did}, headers=_auth_headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            children = data.get("children", [])
            click.echo(f"fissioned {did} → {len(children)} children")
            for c in children:
                click.echo(f"  {c.get('did', c)}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@cohort.command("evidence")
@click.option("--cohort", "cohort_did", default="")
@click.option("--min-posterior", default=0.0, type=float)
@click.option("--judge", default="", help="filter by judge verdict")
@click.option("--limit", default=50, type=int)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_evidence(cohort_did: str, min_posterior: float, judge: str,
                    limit: int, pds: str | None, json_out: bool) -> None:
    """GET com.etzhayyim.cohort.listEvidence — list evidence records."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    params: dict = {"limit": limit}
    if cohort_did:
        params["cohort"] = cohort_did
    if min_posterior > 0:
        params["minPosterior"] = min_posterior
    if judge:
        params["judge"] = judge
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.cohort.listEvidence",
                         params=params, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            items = data if isinstance(data, list) else data.get("evidence", [])
            for ev in items:
                click.echo(f"  {ev.get('id', '')}  posterior={ev.get('posterior', '?')}"
                           f"  judge={ev.get('judge', '?')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@cohort.command("emit")
@click.option("--cohort", "cohort_did", required=True)
@click.option("--evidence", "evidence_json", required=True, help="evidence JSON or @file")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_emit(cohort_did: str, evidence_json: str, pds: str | None, json_out: bool) -> None:
    """POST com.etzhayyim.cohort.emitEvidence — Phase B evidence emission."""
    if evidence_json.startswith("@"):
        body = json.loads(Path(evidence_json[1:]).read_text())
    else:
        body = json.loads(evidence_json)
    body["cohort"] = cohort_did
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.post(f"{pds_url}/xrpc/com.etzhayyim.cohort.emitEvidence",
                          json=body, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"emitted evidence: {data.get('id', '?')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@cohort.command("lineage")
@click.option("--did", required=True)
@click.option("--depth", default=5, type=int, show_default=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_lineage(did: str, depth: int, pds: str | None, json_out: bool) -> None:
    """Traverse derived_from chain upward."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.cohort.getLineage",
                         params={"did": did, "depth": depth},
                         headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            chain = data if isinstance(data, list) else data.get("chain", [])
            for i, node in enumerate(chain):
                indent = "  " * i + ("└─ " if i > 0 else "")
                click.echo(f"  {indent}{node.get('did', node)}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@cohort.command("lineage-stats")
@click.option("--pcf-l1", default="")
@click.option("--min-children", default=1, type=int)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_lineage_stats(pcf_l1: str, min_children: int, pds: str | None, json_out: bool) -> None:
    """GET com.etzhayyim.cohort.lineageStats — mv_cohort_lineage_depth rank."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    params: dict = {"minChildren": min_children}
    if pcf_l1:
        params["pcfL1"] = pcf_l1
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.cohort.lineageStats",
                         params=params, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            rows = data if isinstance(data, list) else data.get("stats", [])
            for row in rows:
                click.echo(f"  {row.get('did', '?')}  depth={row.get('depth', '?')}"
                           f"  children={row.get('children', '?')}")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@cohort.command("repair-edge")
@click.option("--did", default="")
@click.option("--limit", default=100, type=int)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_repair_edge(did: str, limit: int, dry_run: bool, pds: str | None, json_out: bool) -> None:
    """POST com.etzhayyim.cohort.repairEdge — backfill edge_cohort_derived."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    body: dict = {"limit": limit, "dryRun": dry_run}
    if did:
        body["did"] = did
    try:
        resp = httpx.post(f"{pds_url}/xrpc/com.etzhayyim.cohort.repairEdge",
                          json=body, headers=_auth_headers(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if json_out:
            click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            click.echo(f"repaired: {data.get('repaired', '?')} edges")
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")


@cohort.command("forest")
@click.option("--pcf-l1", default="")
@click.option("--rooted", "rooted_did", default="")
@click.option("--pds", default=None)
def cohort_forest(pcf_l1: str, rooted_did: str, pds: str | None) -> None:
    """Cohort + descendant ASCII tree."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    params: dict = {"limit": 500}
    if pcf_l1:
        params["pcfL1"] = pcf_l1
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.cohort.listCohorts",
                         params=params, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        cohorts = data if isinstance(data, list) else data.get("cohorts", [])
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")

    by_parent: dict[str, list[dict]] = {}
    roots: list[dict] = []
    for c in cohorts:
        parent = c.get("derivedFrom", "")
        if parent:
            by_parent.setdefault(parent, []).append(c)
        else:
            roots.append(c)

    if rooted_did:
        roots = [c for c in cohorts if c.get("did") == rooted_did]

    def _print(node: dict, prefix: str = "", is_last: bool = True) -> None:
        connector = "└─ " if is_last else "├─ "
        did = node.get("did", "?")
        name = node.get("name", "")
        click.echo(f"{prefix}{connector}{did}  {name}")
        children = by_parent.get(did, [])
        child_prefix = prefix + ("   " if is_last else "│  ")
        for i, child in enumerate(children):
            _print(child, child_prefix, i == len(children) - 1)

    for i, root in enumerate(roots):
        _print(root, "", i == len(roots) - 1)


@cohort.command("dashboard")
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_dashboard(pds: str | None, json_out: bool) -> None:
    """Health check — total/cohort/fissioned/axis cardinalities."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.cohort.listCohorts",
                         params={"limit": 1000}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        cohorts = data if isinstance(data, list) else data.get("cohorts", [])
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")

    total = len(cohorts)
    fissioned = sum(1 for c in cohorts if c.get("kind") == "fissioned")
    base = total - fissioned
    fission_rate = fissioned / total if total else 0

    pcf_vals = set(c.get("pcfL1", "") for c in cohorts if c.get("pcfL1"))
    role_vals = set(c.get("role", "") for c in cohorts if c.get("role"))
    industry_vals = set(c.get("industry", "") for c in cohorts if c.get("industry"))
    locale_vals = set(c.get("locale", "") for c in cohorts if c.get("locale"))

    report = {
        "total": total, "cohort": base, "fissioned": fissioned,
        "fissionEnabledRate": round(fission_rate, 4),
        "axisPcfL1": len(pcf_vals), "axisRole": len(role_vals),
        "axisIndustry": len(industry_vals), "axisLocale": len(locale_vals),
    }
    if json_out:
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  total={total}  base={base}  fissioned={fissioned}"
                   f"  fission_rate={fission_rate:.1%}")
        click.echo(f"  axes: pcfL1={len(pcf_vals)}  role={len(role_vals)}"
                   f"  industry={len(industry_vals)}  locale={len(locale_vals)}")


@cohort.command("coverage")
@click.option("--axes", default="pcfL1,role", show_default=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_coverage(axes: str, pds: str | None, json_out: bool) -> None:
    """2D coverage matrix of cohort axis combinations."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    axis_list = [a.strip() for a in axes.split(",")][:2]
    if len(axis_list) < 2:
        axis_list = ["pcfL1", "role"]
    row_ax, col_ax = axis_list[0], axis_list[1]
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.cohort.listCohorts",
                         params={"limit": 1000}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        cohorts = data if isinstance(data, list) else data.get("cohorts", [])
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")

    matrix: dict[str, dict[str, int]] = {}
    row_vals: set[str] = set()
    col_vals: set[str] = set()
    for c in cohorts:
        rv = c.get(row_ax, "")
        cv = c.get(col_ax, "")
        if rv and cv:
            row_vals.add(rv)
            col_vals.add(cv)
            matrix.setdefault(rv, {}).setdefault(cv, 0)
            matrix[rv][cv] += 1

    if json_out:
        click.echo(json.dumps({"axes": [row_ax, col_ax], "matrix": matrix,
                               "rows": sorted(row_vals), "cols": sorted(col_vals)},
                              ensure_ascii=False, indent=2))
    else:
        cols = sorted(col_vals)
        header = f"{'':20}" + "".join(f"{c[:8]:10}" for c in cols)
        click.echo(header)
        for rv in sorted(row_vals):
            row_str = f"{rv[:20]:20}"
            for cv in cols:
                cnt = matrix.get(rv, {}).get(cv, 0)
                cell = str(cnt) if cnt else "."
                row_str += f"{cell:10}"
            click.echo(row_str)


@cohort.command("gap")
@click.option("--axes", default="pcfL1,role", show_default=True)
@click.option("--min-count", default=1, type=int)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_gap(axes: str, min_count: int, pds: str | None, json_out: bool) -> None:
    """List under-populated axis combinations (count < min-count)."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    axis_list = [a.strip() for a in axes.split(",")][:2]
    if len(axis_list) < 2:
        axis_list = ["pcfL1", "role"]
    row_ax, col_ax = axis_list[0], axis_list[1]
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.cohort.listCohorts",
                         params={"limit": 1000}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        cohorts = data if isinstance(data, list) else data.get("cohorts", [])
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")

    matrix: dict[str, dict[str, int]] = {}
    row_vals: set[str] = set()
    col_vals: set[str] = set()
    for c in cohorts:
        rv = c.get(row_ax, "")
        cv = c.get(col_ax, "")
        if rv and cv:
            row_vals.add(rv)
            col_vals.add(cv)
            matrix.setdefault(rv, {}).setdefault(cv, 0)
            matrix[rv][cv] += 1

    gaps = [
        {row_ax: rv, col_ax: cv, "count": matrix.get(rv, {}).get(cv, 0)}
        for rv in sorted(row_vals)
        for cv in sorted(col_vals)
        if matrix.get(rv, {}).get(cv, 0) < min_count
    ]
    if json_out:
        click.echo(json.dumps(gaps, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  gaps (count<{min_count}): {len(gaps)}")
        for g in gaps[:50]:
            click.echo(f"  {g[row_ax]:20}  {g[col_ax]:20}  count={g['count']}")


@cohort.command("snapshot")
@click.option("--axes", default="pcfL1,role,industry,seniority", show_default=True)
@click.option("--out-dir", default="data/cohort-coverage", show_default=True)
@click.option("--pds", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_snapshot(axes: str, out_dir: str, pds: str | None, json_out: bool) -> None:
    """Save 4-axis cohort aggregate to data/cohort-coverage/<ts>.json."""
    pds_url = (pds or resolve_pds()).rstrip("/")
    try:
        resp = httpx.get(f"{pds_url}/xrpc/com.etzhayyim.cohort.listCohorts",
                         params={"limit": 1000}, headers=_auth_headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        cohorts = data if isinstance(data, list) else data.get("cohorts", [])
    except httpx.HTTPError as e:
        raise click.ClickException(f"XRPC error: {e}")

    axis_list = [a.strip() for a in axes.split(",")]
    agg: dict[str, dict] = {}
    for c in cohorts:
        key = "|".join(str(c.get(ax, "")) for ax in axis_list)
        agg.setdefault(key, {"count": 0})
        agg[key]["count"] += 1
        for ax in axis_list:
            agg[key][ax] = c.get(ax, "")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot = {"ts": ts, "axes": axis_list, "aggregate": list(agg.values()),
                "total": len(cohorts)}
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    snap_file = out_path / f"{ts}.json"
    snap_file.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))

    if json_out:
        click.echo(json.dumps({"saved": str(snap_file), "total": len(cohorts)},
                              ensure_ascii=False))
    else:
        click.echo(f"saved snapshot → {snap_file}  total={len(cohorts)}")


@cohort.command("diff")
@click.argument("snap_a")
@click.argument("snap_b")
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_diff(snap_a: str, snap_b: str, json_out: bool) -> None:
    """Diff two snapshot files axis by axis."""
    a = json.loads(Path(snap_a).read_text())
    b = json.loads(Path(snap_b).read_text())
    delta = {"from": a.get("ts"), "to": b.get("ts"),
             "total_delta": b.get("total", 0) - a.get("total", 0)}
    if json_out:
        click.echo(json.dumps(delta, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  from={delta['from']}  to={delta['to']}"
                   f"  total_delta={delta['total_delta']:+d}")


@cohort.command("drift")
@click.option("--window", default=7, type=int, show_default=True, help="days")
@click.option("--dir", "snap_dir", default="data/cohort-coverage", show_default=True)
@click.option("--json", "json_out", is_flag=True, default=False)
def cohort_drift(window: int, snap_dir: str, json_out: bool) -> None:
    """Auto-diff oldest vs newest snapshot in snapshot dir."""
    p = Path(snap_dir)
    if not p.exists():
        click.echo(f"snapshot dir not found: {snap_dir}", err=True)
        return
    files = sorted(p.glob("*.json"))
    if len(files) < 2:
        click.echo("need at least 2 snapshots for drift analysis", err=True)
        return
    a = json.loads(files[0].read_text())
    b = json.loads(files[-1].read_text())
    delta = {"from": a.get("ts"), "to": b.get("ts"),
             "total_delta": b.get("total", 0) - a.get("total", 0),
             "snapshots": len(files)}
    if json_out:
        click.echo(json.dumps(delta, ensure_ascii=False, indent=2))
    else:
        click.echo(f"  drift: {delta['from']} → {delta['to']}"
                   f"  total_delta={delta['total_delta']:+d}"
                   f"  over {len(files)} snapshots")


@cohort.command("bootstrap")
def cohort_bootstrap() -> None:
    """Bootstrap all cohort actors from deps.toml (requires Go binary)."""
    click.echo(
        "cohort bootstrap reads deps.toml [[cohort_actors]] and requires the Go binary. "
        "Run: etzhayyim cohort bootstrap",
        err=True,
    )
    sys.exit(1)
