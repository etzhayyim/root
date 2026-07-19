"""dodaf — DoDAF DM2 architecture model commands.

Scans workspace for DoDAF artifacts (lexicons, ADRs, actor definitions).
Queries TV-1/AV-2/OV-5 Parquet registries via duckdb CLI.
Full diagram generation requires the Go binary.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import click

from .shannon import _resolve_root


_SKIP_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build"}

# DoDAF viewpoint patterns
_VIEWPOINTS = {
    "AV-1": "Overview and Summary",
    "AV-2": "Integrated Dictionary",
    "OV-1": "High-Level Operational Concept",
    "OV-2": "Operational Resource Flow",
    "OV-5": "Operational Activity Model",
    "SV-1": "Systems Interface",
    "SV-4": "Systems Functionality",
    "SvcV-1": "Services Context",
    "SvcV-4": "Services Functionality",
    "DIV-1": "Conceptual Data Model",
    "DIV-2": "Logical Data Model",
    "DIV-3": "Physical Data Model",
}

_RE_VIEWPOINT = re.compile(
    r'\b(AV-[12]|OV-[125]|SV-[14]|SvcV-[14]|DIV-[123])\b'
)


def _scan_dodaf_artifacts(ws: Path) -> list[dict]:
    artifacts = []

    # ADRs
    adr_dir = ws / "90-docs" / "adr"
    if adr_dir.exists():
        for f in sorted(adr_dir.glob("*.md")):
            try:
                content = f.read_text(errors="replace")
                viewpoints = list(set(_RE_VIEWPOINT.findall(content)))
                artifacts.append({
                    "type": "adr",
                    "path": str(f.relative_to(ws)),
                    "title": f.stem,
                    "viewpoints": viewpoints,
                })
            except OSError:
                pass

    # Lexicons
    lexicon_dir = ws / "00-contracts" / "lexicons"
    if lexicon_dir.exists():
        for f in lexicon_dir.rglob("*.json"):
            if any(d in f.parts for d in _SKIP_DIRS):
                continue
            try:
                data = json.loads(f.read_text(errors="replace"))
                lexicon_id = data.get("id", "")
                defs = list(data.get("defs", {}).keys())
                artifacts.append({
                    "type": "lexicon",
                    "path": str(f.relative_to(ws)),
                    "lexicon_id": lexicon_id,
                    "defs": defs[:5],
                })
            except (OSError, json.JSONDecodeError):
                pass

    # Actor definitions (kotodama.jsonld)
    apps_dir = ws / "60-apps"
    if apps_dir.exists():
        for f in apps_dir.rglob("kotodama.jsonld"):
            try:
                data = json.loads(f.read_text(errors="replace"))
                artifacts.append({
                    "type": "actor",
                    "path": str(f.relative_to(ws)),
                    "nanoid": data.get("nanoid", ""),
                    "name": data.get("name", ""),
                    "performer_type": data.get("performerType", ""),
                })
            except (OSError, json.JSONDecodeError):
                pass

    return artifacts


# ── CLI ────────────────────────────────────────────────────────────────────────

@click.group("dodaf", invoke_without_command=True)
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.pass_context
def dodaf(ctx: click.Context, workspace_dir: str | None, json_out: bool) -> None:
    """DoDAF DM2 architecture model scanning and reporting."""
    if ctx.invoked_subcommand is not None:
        return
    ws = _resolve_root(workspace_dir)
    artifacts = _scan_dodaf_artifacts(ws)
    counts = {}
    for a in artifacts:
        counts[a["type"]] = counts.get(a["type"], 0) + 1
    if json_out:
        click.echo(json.dumps({"total": len(artifacts), "counts": counts}, ensure_ascii=False, indent=2))
    else:
        click.echo(f"dodaf: {len(artifacts)} artifacts  " +
                   "  ".join(f"{k}={v}" for k, v in counts.items()))


@dodaf.command("scan")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--type", "artifact_type", default="", help="Filter by type (adr/lexicon/actor)")
def dodaf_scan(workspace_dir: str | None, json_out: bool, artifact_type: str) -> None:
    """Scan workspace for DoDAF artifacts."""
    ws = _resolve_root(workspace_dir)
    artifacts = _scan_dodaf_artifacts(ws)
    if artifact_type:
        artifacts = [a for a in artifacts if a["type"] == artifact_type]
    if json_out:
        click.echo(json.dumps(artifacts, ensure_ascii=False, indent=2))
    else:
        for a in artifacts:
            click.echo(f"  [{a['type']:8}] {a.get('path', '')}")


@dodaf.command("viewpoints")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def dodaf_viewpoints(workspace_dir: str | None, json_out: bool) -> None:
    """Show DoDAF viewpoint coverage across ADRs."""
    ws = _resolve_root(workspace_dir)
    artifacts = [a for a in _scan_dodaf_artifacts(ws) if a["type"] == "adr"]
    coverage: dict[str, list[str]] = {vp: [] for vp in _VIEWPOINTS}
    for a in artifacts:
        for vp in a.get("viewpoints", []):
            if vp in coverage:
                coverage[vp].append(a["title"])
    if json_out:
        click.echo(json.dumps(coverage, ensure_ascii=False, indent=2))
    else:
        for vp, desc in _VIEWPOINTS.items():
            refs = coverage.get(vp, [])
            status = f"{len(refs)} refs" if refs else "NONE"
            click.echo(f"  {vp:8}  {desc:<35}  {status}")


@dodaf.command("generate")
@click.option("--workspace-dir", default=None)
def dodaf_generate(workspace_dir: str | None) -> None:
    """Generate DoDAF diagram files (requires Go binary)."""
    click.echo(
        "etzhayyim dodaf generate requires the Go binary. Run: etzhayyim dodaf generate",
        err=True,
    )
    sys.exit(1)


# ── DuckDB helpers ─────────────────────────────────────────────────────────────

def _require_duckdb() -> str:
    """Return duckdb binary path or exit with helpful message."""
    p = shutil.which("duckdb")
    if not p:
        click.echo("duckdb not found — install: brew install duckdb", err=True)
        sys.exit(1)
    return p


def _dodaf_data_dir(ws: Path) -> Path:
    return ws / "80-data" / "dodaf"


def _dodaf_parquet(ws: Path, view: str) -> Path:
    return _dodaf_data_dir(ws) / f"{view}.parquet"


def _duckdb_query(sql: str) -> None:
    """Run a SELECT and stream output to stdout."""
    duckdb = _require_duckdb()
    subprocess.run([duckdb, "-c", sql], check=False)


def _duckdb_query_json(sql: str) -> list[dict]:
    """Run a SELECT and return JSON rows (handles both JSON array and NDJSON output)."""
    duckdb = _require_duckdb()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        wrap = f"COPY ({sql.rstrip(';')}) TO '{tmp_path}' (FORMAT JSON);"
        r = subprocess.run([duckdb, "-c", wrap], capture_output=True, text=True)
        if r.returncode != 0:
            click.echo(f"duckdb error: {r.stderr.strip()}", err=True)
            return []
        if not tmp_path.exists():
            return []
        text = tmp_path.read_text()
        if not text.strip():
            return []
        try:
            # Try JSON array first
            parsed = json.loads(text)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            # Fall back to NDJSON (one object per line)
            rows = []
            for line in text.splitlines():
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return rows
    finally:
        tmp_path.unlink(missing_ok=True)


def _write_json_to_parquet(rows: list[dict], parquet_path: Path) -> None:
    """Write rows as JSON then convert to Parquet via duckdb CLI."""
    duckdb = _require_duckdb()
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_json = parquet_path.with_suffix(".tmp.json")
    try:
        tmp_json.write_text(json.dumps(rows, ensure_ascii=False))
        sql = (
            f"COPY (SELECT * FROM read_json_auto('{tmp_json}')) TO '{parquet_path}' "
            f"(FORMAT PARQUET, COMPRESSION ZSTD);"
        )
        r = subprocess.run([duckdb, "-c", sql], capture_output=True, text=True)
        if r.returncode != 0:
            click.echo(f"duckdb parquet write error: {r.stderr.strip()}", err=True)
            sys.exit(1)
    finally:
        tmp_json.unlink(missing_ok=True)


def _build_tag_cond(tag_col: str, tag_list: list[str]) -> str:
    if not tag_list:
        return ""
    parts = [f"list_contains({tag_col}, '{t.replace(chr(39), chr(39)*2)}')" for t in tag_list]
    return "(" + " OR ".join(parts) + ")"


def _build_path_cond(folder_col: str, path_val: str) -> str:
    if not path_val or not folder_col:
        return ""
    escaped = path_val.replace("'", "''")
    return (
        f"(len({folder_col}) = 0 OR EXISTS "
        f"(SELECT 1 FROM unnest({folder_col}) AS t(f) WHERE '{escaped}' LIKE f || '%'))"
    )


def _build_where(tag_col: str, folder_col: str, tag_list: list[str], path_val: str) -> str:
    parts = []
    if tc := _build_tag_cond(tag_col, tag_list):
        parts.append(tc)
    if pc := _build_path_cond(folder_col, path_val):
        parts.append(pc)
    return ("WHERE " + " AND ".join(parts)) if parts else ""


# ── dodaf init ────────────────────────────────────────────────────────────────

def _dodaf_seed_tv1(now: str) -> list[dict]:
    return [
        {"id": "cf-wasm-no-dynamic-compile", "view": "TV-1", "title": "CF Workers: WebAssembly.compile() blocked at runtime", "standard_ref": "Cloudflare Workers V8 embedder policy", "rule": "WebAssembly.compile(bytes) called at request time returns CompileError: 'Wasm code generation disallowed by embedder'. Only static WASM imports via CompiledWasm wrangler rule are supported.", "severity": "critical", "permitted": False, "scope_folders": ["60-apps/", "_archive/30-graph/kagami-live-260414/wasm/"], "scope_tags": ["cloudflare", "wasm", "assemblyscript"], "scope_exts": [".ts", ".wasm", ".jsonc"], "evidence": "h0g3t3st.etzhayyim.com/xrpc/com.etzhayyim.apps.hoge.wasmEval — validated 2026-04-08", "status": "[PRODUCTION]", "source": "orgs/etzhayyim/com-etzhayyim-app-hoge/appview/src/index.ts", "alternative": "", "created_at": now},
        {"id": "cf-wasm-static-import-ok", "view": "TV-1", "title": "CF Workers: static WASM import via CompiledWasm rule works", "standard_ref": "Cloudflare Workers CompiledWasm rule", "rule": "Static WASM import with CompiledWasm wrangler rule works correctly. new WebAssembly.Instance(MODULE, imports) per-request instantiation is ~0ms.", "severity": "info", "permitted": True, "scope_folders": ["60-apps/", "_archive/30-graph/kagami-live-260414/wasm/"], "scope_tags": ["cloudflare", "wasm", "assemblyscript"], "scope_exts": [".ts", ".jsonc"], "evidence": "h0g3t3st.etzhayyim.com/xrpc/com.etzhayyim.apps.hoge.wasmTest — validated 2026-04-08", "status": "[PRODUCTION]", "source": "orgs/etzhayyim/com-etzhayyim-app-hoge/appview/src/index.ts", "alternative": "", "created_at": now},
        {"id": "cf-worker-no-kv", "view": "TV-1", "title": "CF Workers: KV usage prohibited", "standard_ref": "W Protocol Event Stream architecture", "rule": "kotodama.KvGet() / kotodama.KvPut() are prohibited. All data must flow through W Protocol Event Stream (ComAtprotoRepoCreateRecord / Preferences). Use PDS_SERVICE service binding for all data access.", "severity": "critical", "permitted": False, "scope_folders": ["60-apps/"], "scope_tags": ["cloudflare", "typescript", "kotodama"], "scope_exts": [".ts"], "evidence": "70-tools/etzhayyim/etzhayyim/code_quality.go kv-usage rule", "status": "[PRODUCTION]", "source": "60-apps/CLAUDE.md", "alternative": "", "created_at": now},
        {"id": "cf-worker-pds-gateway-only", "view": "TV-1", "title": "CF Workers: all data access via PDS_SERVICE binding only", "standard_ref": "PDS Gateway Pattern", "rule": "App Workers must use env.PDS_SERVICE service binding for all data access. Direct graph RPC binding in app Workers is prohibited. globalThis.fetch() to llm.etzhayyim.com or other internal services is prohibited.", "severity": "critical", "permitted": False, "scope_folders": ["60-apps/"], "scope_tags": ["cloudflare", "typescript", "kotodama", "pds"], "scope_exts": [".ts", ".jsonc"], "evidence": "50-infra/CLAUDE.md §PDS Gateway Pattern", "status": "[PRODUCTION]", "source": "50-infra/CLAUDE.md", "alternative": "", "created_at": now},
        {"id": "xrpc-sole-api", "view": "TV-1", "title": "XRPC (/xrpc/{NSID}) is the sole external API surface", "standard_ref": "AT Protocol XRPC standard", "rule": "All public API endpoints must use /xrpc/{NSID} format (AT Protocol native). REST endpoints for business mutations are prohibited.", "severity": "critical", "permitted": False, "scope_folders": ["60-apps/", "50-infra/"], "scope_tags": ["at-protocol", "xrpc", "typescript"], "scope_exts": [".ts"], "evidence": "CLAUDE.md root §XRPC = sole API", "status": "[PRODUCTION]", "source": "CLAUDE.md", "alternative": "", "created_at": now},
        {"id": "shannon-redundancy-prohibition", "view": "TV-1", "title": "Shannon Redundancy Prohibition: single source of truth", "standard_ref": "Shannon information theory", "rule": "Each rule/fact must appear in exactly one location in the hierarchy. Copying the same rule to multiple CLAUDE.md files is prohibited (entropy=0). Stale comments are prohibited.", "severity": "critical", "permitted": False, "scope_folders": [], "scope_tags": ["claude", "docs", "code-review"], "scope_exts": [".md", ".ts", ".go"], "evidence": "CLAUDE.md root §CRITICAL: Shannon Redundancy Prohibition", "status": "[PRODUCTION]", "source": "CLAUDE.md", "alternative": "", "created_at": now},
        {"id": "at-protocol-repo-always-public", "view": "TV-1", "title": "AT Protocol: Repo records are always public (federable)", "standard_ref": "AT Protocol specification", "rule": "AT Protocol Repo records (created via ComAtprotoRepoCreateRecord) are always public and federable. PII, financial data, and user config must use Preferences() (server-side, NOT in Repo). Never write PII to createRecord.", "severity": "critical", "permitted": False, "scope_folders": ["60-apps/"], "scope_tags": ["at-protocol", "privacy", "typescript"], "scope_exts": [".ts"], "evidence": "CLAUDE.md root §AT Protocol Faithful Public/Private", "status": "[PRODUCTION]", "source": "CLAUDE.md", "alternative": "", "created_at": now},
        {"id": "write-only-derived-architecture", "view": "TV-1", "title": "Write-Only Derived Architecture: handlers write only (η=100%)", "standard_ref": "260407-write-only-derived-architecture-design.md", "rule": "Handlers must only call writePublic() or writePrivate(). Calling postFeed(), sdk.hostImports.invoke(), or sdk.hostImports.appBskyFeedPost() inside a handler is prohibited.", "severity": "critical", "permitted": False, "scope_folders": ["60-apps/"], "scope_tags": ["at-protocol", "typescript", "kotodama", "design-e"], "scope_exts": [".ts", ".jsonld"], "evidence": "90-docs/260407-write-only-derived-architecture-design.md", "status": "[PRODUCTION]", "source": "CLAUDE.md", "alternative": "", "created_at": now},
        {"id": "no-synthetic-data-production", "view": "TV-1", "title": "No synthetic data in production API responses", "standard_ref": "Shannon information theory — entropy=0 for fabricated data", "rule": "200 OK responses must only contain data that actually exists in the graph/DB. Empty graph query → empty array. Unknown author/DID → empty string. Not found → 404 (never return fake record as 200).", "severity": "critical", "permitted": False, "scope_folders": ["60-apps/", "50-infra/"], "scope_tags": ["typescript", "api", "data-integrity"], "scope_exts": [".ts"], "evidence": "CLAUDE.md root §CRITICAL: No Synthetic Data in Production Responses", "status": "[PRODUCTION]", "source": "CLAUDE.md", "alternative": "", "created_at": now},
        {"id": "cf-wasm-component-model-not-supported", "view": "TV-1", "title": "CF Workers: WASM Component Model is not supported", "standard_ref": "Cloudflare Workers V8 runtime", "rule": "WASM Component Model (WIT-based components, wasmtime component instantiation) does NOT work on Cloudflare Workers (V8-based). Only basic WASM modules are supported.", "severity": "critical", "permitted": False, "scope_folders": ["60-apps/", "_archive/30-graph/kagami-live-260414/wasm/"], "scope_tags": ["cloudflare", "wasm", "assemblyscript"], "scope_exts": [".wasm", ".wit", ".ts"], "evidence": "Codebase search: zero Component Model usage in CF Workers — 2026-04-08", "status": "[PRODUCTION]", "source": "CLAUDE.md", "alternative": "", "created_at": now},
        {"id": "do-sqlite-prohibited", "view": "TV-1", "title": "CF Workers: Durable Object SQLite is prohibited", "standard_ref": "W Protocol Event Stream architecture", "rule": "DurableObjectState.storage.sql / durable-object-sql WIT / raw DO-sql-exec() direct calls are prohibited. All data goes through W Protocol Event Stream.", "severity": "critical", "permitted": False, "scope_folders": ["60-apps/", "50-infra/"], "scope_tags": ["cloudflare", "typescript", "durable-objects"], "scope_exts": [".ts"], "evidence": "70-tools/etzhayyim/etzhayyim/code_quality.go dosqlexec rule", "status": "[PRODUCTION]", "source": "60-apps/CLAUDE.md", "alternative": "", "created_at": now},
    ]


def _dodaf_seed_av2(now: str) -> list[dict]:
    return [
        {"id": "compiled-wasm", "term": "CompiledWasm", "definition": "Wrangler rule that converts .wasm ESM imports into WebAssembly.Module at bundle time. Declared in wrangler.jsonc as {\"rules\":[{\"type\":\"CompiledWasm\",\"globs\":[\"**/*.wasm\"]}]}. Allows static import of WASM modules that are instantiated per-request.", "aliases": ["CompiledWasm rule", "wasm static import"], "domain": "cloudflare", "scope_tags": ["cloudflare", "wasm"], "source": "orgs/etzhayyim/com-etzhayyim-app-hoge/appview/wrangler.jsonc", "status": "[PRODUCTION]", "created_at": now},
        {"id": "kotodama-app", "term": "App", "definition": "TS Native Cloudflare Worker app using @etzhayyim/kotodama-host-sdk with WIT contracts. Single-file architecture (src/app.ts). Deployed as account-level Worker with {nanoid}.etzhayyim.com/* route. createWorkerExport() is the entry point.", "aliases": ["kotodama", "TS native app", "kotodama component"], "domain": "platform", "scope_tags": ["typescript", "cloudflare", "kotodama"], "source": "40-engine/kotoba/crates/kotoba-kotodama/CLAUDE.md", "status": "[PRODUCTION]", "created_at": now},
        {"id": "xrpc", "term": "XRPC", "definition": "AT Protocol Remote Procedure Call format. All public APIs use /xrpc/{NSID} path. NSID format: {namespace}.{method} in camelCase (e.g. com.etzhayyim.apps.hoge.wasmTest). XRPC is the sole external API surface — no REST endpoints for business logic.", "aliases": ["XRPC", "AT Protocol RPC", "/xrpc/"], "domain": "at-protocol", "scope_tags": ["at-protocol", "xrpc", "api"], "source": "10-protocol/wproto/xrpc/", "status": "[PRODUCTION]", "created_at": now},
        {"id": "kagami", "term": "kagami", "definition": "Graph database using DuckDB + S3 Parquet on Linode LKE. P10v2 GraphAr-native typed columnar schema (1 AT record = 1 row). Accessed through the graph SQL path from the PDS Worker.", "aliases": ["graph SQL path", "Hyperdrive"], "domain": "infrastructure", "scope_tags": ["graph-db", "duckdb", "parquet"], "source": "_archive/30-graph/kagami-live-260414/CLAUDE.md", "status": "[PRODUCTION]", "created_at": now},
        {"id": "nanoid-did", "term": "nanoid DID", "definition": "Canonical DID format: did:web:{nanoid}.etzhayyim.com. AT Protocol repo always uses nanoid DID. Vanity domain (e.g. hoge.etzhayyim.com) is a handle/alias only — never used as repo DID.", "aliases": ["canonical DID", "did:web:{nanoid}.etzhayyim.com"], "domain": "at-protocol", "scope_tags": ["at-protocol", "did", "identity"], "source": "50-infra/CLAUDE.md §Canonical DID", "status": "[PRODUCTION]", "created_at": now},
        {"id": "w-protocol", "term": "W Protocol", "definition": "AT Protocol superset extending AT Protocol with Signal Protocol E2E encryption, WIT contracts, wRPC streaming, and Multi-DID per actor. All entities have AI Agent DIDs. Federable with AT Protocol network.", "aliases": ["W Protocol", "wproto"], "domain": "protocol", "scope_tags": ["at-protocol", "w-protocol", "protocol"], "source": "10-protocol/wproto/CLAUDE.md", "status": "[PRODUCTION]", "created_at": now},
        {"id": "pds-service", "term": "PDS_SERVICE", "definition": "Cloudflare Workers service binding from App Worker to PDS Worker. The sole data gateway for all read/write operations. Exposes: createRecord(), query(), batchImport(), updateRecord(), deleteRecord(), uploadBlob(). Direct graph RPC binding in app Workers is prohibited.", "aliases": ["PDS_SERVICE binding", "env.PDS_SERVICE"], "domain": "infrastructure", "scope_tags": ["cloudflare", "pds", "service-binding"], "source": "50-infra/CLAUDE.md §PDS Gateway Pattern", "status": "[PRODUCTION]", "created_at": now},
        {"id": "shannon-score", "term": "Shannon entropy score", "definition": "H = -Σ p(x)·log₂(p(x)). In the platform context: measures information density of code/docs (η=1 means no redundancy). Applied to: CLAUDE.md rules (single source of truth), code coupling (DSM), uncertainty propagation (BayesNet). Tools: etzhayyim shannon, etzhayyim mokuteki.", "aliases": ["Shannon entropy", "η", "information entropy"], "domain": "information-theory", "scope_tags": ["shannon", "metrics", "docs"], "source": "70-tools/etzhayyim/CLAUDE.md §etzhayyim shannon", "status": "[PRODUCTION]", "created_at": now},
        {"id": "dodaf-v2", "term": "DoDAF v2", "definition": "Department of Defense Architecture Framework version 2. Viewpoints: AV (All View), OV (Operational View), SV (Systems View), TV (Technical Standards View), CV (Capability View). Used for: AV-2 Integrated Dictionary (lexicon), TV-1 Technical Standards (constraints), OV-5 Operational Activities (permitted/prohibited).", "aliases": ["DoDAF", "Department of Defense Architecture Framework"], "domain": "architecture", "scope_tags": ["dodaf", "architecture", "docs"], "source": "70-tools/etzhayyim/etzhayyim/dodaf.go", "status": "[PRODUCTION]", "created_at": now},
    ]


def _dodaf_seed_ov5(now: str) -> list[dict]:
    return [
        {"id": "ov5-wasm-static-import", "action": "import MODULE from '*.wasm' (CompiledWasm rule)", "permitted": True, "reason": "Bundled at deploy time by wrangler CompiledWasm rule. Works on CF Workers V8.", "scope_tags": ["cloudflare", "wasm"], "alternative": "", "source": "orgs/etzhayyim/com-etzhayyim-app-hoge/appview/src/index.ts", "created_at": now},
        {"id": "ov5-wasm-dynamic-compile", "action": "WebAssembly.compile(userBytes) at request time", "permitted": False, "reason": "Blocked by CF Workers V8 embedder: 'Wasm code generation disallowed by embedder'.", "scope_tags": ["cloudflare", "wasm"], "alternative": "Pre-bundle WASM at deploy time via CompiledWasm rule", "source": "orgs/etzhayyim/com-etzhayyim-app-hoge/appview/src/index.ts", "created_at": now},
        {"id": "ov5-kv-usage", "action": "KvGet() / KvPut() in App", "permitted": False, "reason": "KV bypasses W Protocol Event Stream. All data must flow through PDS_SERVICE.", "scope_tags": ["cloudflare", "kotodama"], "alternative": "sdk.pds.createRecord() for write, sdk.graph.query() for read", "source": "60-apps/CLAUDE.md", "created_at": now},
        {"id": "ov5-synthetic-200", "action": "Return fabricated data in 200 OK response", "permitted": False, "reason": "No synthetic data principle: 200 OK must only contain data that exists in graph/DB.", "scope_tags": ["api", "data-integrity"], "alternative": "Return empty array [] or 404 when data does not exist", "source": "CLAUDE.md", "created_at": now},
        {"id": "ov5-pds-direct-fetch", "action": "globalThis.fetch('https://atproto.etzhayyim.com/...')", "permitted": False, "reason": "Direct HTTP to PDS from App Worker bypasses service binding RPC. same-zone fetch() is prohibited.", "scope_tags": ["cloudflare", "pds"], "alternative": "env.PDS_SERVICE.query() or env.PDS_SERVICE.createRecord()", "source": "50-infra/CLAUDE.md", "created_at": now},
        {"id": "ov5-shannon-copy-paste-rule", "action": "Copy a rule from parent CLAUDE.md into child CLAUDE.md", "permitted": False, "reason": "Shannon Redundancy Prohibition: each rule lives in exactly one location. Duplication = entropy=0.", "scope_tags": ["docs", "claude"], "alternative": "Write a 1-line pointer to the authoritative source in the child CLAUDE.md", "source": "CLAUDE.md", "created_at": now},
    ]


@dodaf.command("init")
@click.option("--workspace-dir", default=None)
@click.option("--force", is_flag=True, default=False, help="Overwrite existing Parquet files")
def dodaf_init(workspace_dir: str | None, force: bool) -> None:
    """Initialize Parquet files with seed data (TV-1, AV-2, OV-5)."""
    ws = _resolve_root(workspace_dir)
    _require_duckdb()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    views = [
        ("tv1_standards", _dodaf_seed_tv1(now)),
        ("av2_dictionary", _dodaf_seed_av2(now)),
        ("ov5_activities", _dodaf_seed_ov5(now)),
    ]

    for view_name, seed_fn in views:
        pf = _dodaf_parquet(ws, view_name)
        if not force and pf.exists():
            click.echo(f"skip (exists): {view_name} — use --force to overwrite", err=True)
            continue
        click.echo(f"writing {view_name} → {pf}", err=True)
        _write_json_to_parquet(seed_fn, pf)
        click.echo(f"ok: {view_name}", err=True)

    click.echo("\nDone. Query with:", err=True)
    click.echo("  etzhayyim dodaf tv1 query --tags cloudflare,wasm", err=True)
    click.echo("  etzhayyim dodaf av2 get CompiledWasm", err=True)
    click.echo("  etzhayyim dodaf rules context --path src/index.ts --tags cloudflare", err=True)


# ── dodaf tv1 ──────────────────────────────────────────────────────────────────

@dodaf.group("tv1")
def dodaf_tv1() -> None:
    """TV-1 Technical Standards registry queries."""


@dodaf_tv1.command("query")
@click.option("--id", "entry_id", default="", help="Look up by exact ID")
@click.option("--tags", default="", help="Comma-separated scope tags to filter")
@click.option("--path", "path_val", default="", help="File path for scope matching")
@click.option("--severity", default="", help="Filter by severity: critical|high|medium|info")
@click.option("--permitted", "permitted_str", default="", help="Filter by permitted: true|false")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
def dodaf_tv1_query(
    entry_id: str,
    tags: str,
    path_val: str,
    severity: str,
    permitted_str: str,
    json_out: bool,
    workspace_dir: str | None,
) -> None:
    """Query TV-1 technical standards / constraints."""
    ws = _resolve_root(workspace_dir)
    pf = _dodaf_parquet(ws, "tv1_standards")
    if not pf.exists():
        click.echo(f"tv1_standards.parquet not found — run: etzhayyim dodaf init\n(looked in {pf})", err=True)
        sys.exit(1)

    conditions: list[str] = []
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    if entry_id:
        eid = entry_id.replace("'", "''")
        conditions.append(f"id = '{eid}'")
    if severity:
        sev = severity.replace("'", "''")
        conditions.append(f"severity = '{sev}'")
    if permitted_str:
        conditions.append(f"permitted = {'true' if permitted_str.lower() == 'true' else 'false'}")
    if tag_list:
        if tc := _build_tag_cond("scope_tags", tag_list):
            conditions.append(tc)
    if path_val:
        if pc := _build_path_cond("scope_folders", path_val):
            conditions.append(pc)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    if json_out:
        rows = _duckdb_query_json(f"SELECT * FROM read_parquet('{pf}') {where} ORDER BY severity, id")
        click.echo(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        _duckdb_query(
            f"SELECT id, severity, permitted, title, status FROM read_parquet('{pf}') "
            f"{where} ORDER BY severity, id LIMIT 40;"
        )


# ── dodaf av2 ──────────────────────────────────────────────────────────────────

@dodaf.group("av2")
def dodaf_av2() -> None:
    """AV-2 Integrated Dictionary queries."""


@dodaf_av2.command("get")
@click.argument("term", default="")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
def dodaf_av2_get(term: str, json_out: bool, workspace_dir: str | None) -> None:
    """Look up a term in the AV-2 integrated dictionary."""
    ws = _resolve_root(workspace_dir)
    pf = _dodaf_parquet(ws, "av2_dictionary")
    if not pf.exists():
        click.echo(f"av2_dictionary.parquet not found — run: etzhayyim dodaf init\n(looked in {pf})", err=True)
        sys.exit(1)

    if not term:
        _duckdb_query(
            f"SELECT id, term, domain, left(definition, 80) AS definition_preview "
            f"FROM read_parquet('{pf}') ORDER BY domain, term;"
        )
        return

    esc = term.replace("'", "''")
    where = (
        f"WHERE lower(term) = lower('{esc}') OR lower(id) = lower('{esc}') "
        f"OR list_contains(aliases, '{esc}')"
    )
    if json_out:
        rows = _duckdb_query_json(f"SELECT * FROM read_parquet('{pf}') {where} LIMIT 5")
        click.echo(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        _duckdb_query(
            f"SELECT term, domain, definition, aliases, source, status "
            f"FROM read_parquet('{pf}') {where} LIMIT 5;"
        )


# ── dodaf rules ────────────────────────────────────────────────────────────────

@dodaf.group("rules")
def dodaf_rules() -> None:
    """Cross-view rules context queries."""


@dodaf_rules.command("context")
@click.option("--path", "path_val", default="", help="File path for scope matching")
@click.option("--tags", default="", help="Comma-separated tags")
@click.option("--json", "json_out", is_flag=True, default=False)
@click.option("--workspace-dir", default=None)
def dodaf_rules_context(path_val: str, tags: str, json_out: bool, workspace_dir: str | None) -> None:
    """All-views context query (TV-1 + AV-2 + OV-5) by path and/or tags."""
    ws = _resolve_root(workspace_dir)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    views = [
        ("standards", "tv1_standards", "scope_tags", "scope_folders"),
        ("dictionary", "av2_dictionary", "scope_tags", ""),
        ("activities", "ov5_activities", "scope_tags", ""),
    ]

    if json_out:
        result: dict = {}
        for view_name, view_file, tag_col, folder_col in views:
            pf = _dodaf_parquet(ws, view_file)
            if not pf.exists():
                continue
            where = _build_where(tag_col, folder_col, tag_list, path_val)
            rows = _duckdb_query_json(f"SELECT * FROM read_parquet('{pf}') {where} LIMIT 20")
            result[view_name] = rows
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    for header, view_file, tag_col, folder_col, select in [
        ("TV-1: Technical Standards", "tv1_standards", "scope_tags", "scope_folders",
         "SELECT id, severity, permitted, title, status"),
        ("AV-2: Dictionary", "av2_dictionary", "scope_tags", "",
         "SELECT term, domain, left(definition,60) AS def"),
        ("OV-5: Activities (Permitted/Prohibited)", "ov5_activities", "scope_tags", "",
         "SELECT permitted, action, left(reason,60) AS reason"),
    ]:
        click.echo(f"\n=== {header} ===")
        pf = _dodaf_parquet(ws, view_file)
        if pf.exists():
            where = _build_where(tag_col, folder_col, tag_list, path_val)
            _duckdb_query(
                f"{select} FROM read_parquet('{pf}') {where} "
                f"ORDER BY {'severity, id' if 'tv1' in view_file else 'id'} LIMIT 20;"
            )


# ── dodaf add ─────────────────────────────────────────────────────────────────

@dodaf.command("add")
@click.option("--view", default="tv1", type=click.Choice(["tv1", "av2", "ov5"]))
@click.option("--id", "entry_id", required=True, help="Unique ID (e.g. cf-wasm-no-dynamic-compile)")
@click.option("--title", default="", help="Short title")
@click.option("--rule", required=True, help="Full rule/definition text")
@click.option("--severity", default="high", type=click.Choice(["critical", "high", "medium", "info"]))
@click.option("--permitted/--prohibited", default=False)
@click.option("--tags", default="", help="Comma-separated scope tags")
@click.option("--evidence", default="", help="Evidence reference (file:line or URL)")
@click.option("--source", default="", help="Source CLAUDE.md file")
@click.option("--status", default="[PRODUCTION]")
@click.option("--workspace-dir", default=None)
def dodaf_add(
    view: str, entry_id: str, title: str, rule: str, severity: str,
    permitted: bool, tags: str, evidence: str, source: str, status: str,
    workspace_dir: str | None,
) -> None:
    """Add a new entry to a DoDAF view (tv1|av2|ov5)."""
    ws = _resolve_root(workspace_dir)
    _require_duckdb()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    view_map = {
        "tv1": ("tv1_standards", lambda rows: rows + [{
            "id": entry_id, "title": title, "view": "TV-1", "rule": rule,
            "severity": severity, "permitted": permitted,
            "scope_tags": tag_list, "scope_folders": [],
            "evidence": evidence, "source": source, "status": status, "created_at": now,
            "standard_ref": "", "alternative": "",
        }]),
        "av2": ("av2_dictionary", lambda rows: rows + [{
            "id": entry_id, "term": title, "domain": "", "definition": rule,
            "aliases": [], "scope_tags": tag_list, "source": source,
            "status": status, "created_at": now,
        }]),
        "ov5": ("ov5_activities", lambda rows: rows + [{
            "id": entry_id, "action": title, "reason": rule, "permitted": permitted,
            "alternative": "", "scope_tags": tag_list, "source": source, "created_at": now,
        }]),
    }

    view_file, make_rows = view_map[view]
    pf = _dodaf_parquet(ws, view_file)
    existing: list[dict] = []
    if pf.exists():
        existing = _duckdb_query_json(f"SELECT * FROM read_parquet('{pf}')")
    _write_json_to_parquet(make_rows(existing), pf)
    click.echo(f"added {view.upper()}-1: {entry_id} → {pf}", err=True)


# ── dodaf validate ────────────────────────────────────────────────────────────

@dodaf.command("validate")
@click.option("--workspace-dir", default=None)
@click.option("--json", "json_out", is_flag=True, default=False)
def dodaf_validate(workspace_dir: str | None, json_out: bool) -> None:
    """Scan CLAUDE.md files for CRITICAL sections not yet in TV-1 registry."""
    ws = _resolve_root(workspace_dir)
    _require_duckdb()
    pf = _dodaf_parquet(ws, "tv1_standards")
    if not pf.exists():
        click.echo(f"tv1_standards.parquet not found — run: etzhayyim dodaf init\n(looked in {pf})", err=True)
        sys.exit(1)

    rows = _duckdb_query_json(f"SELECT id FROM read_parquet('{pf}')")
    registered = {r["id"] for r in rows if r.get("id")}

    _RE_CRITICAL = re.compile(r'^#{1,6}\s+CRITICAL:\s*(.+)$', re.MULTILINE)
    unregistered: list[dict] = []

    for claude_md in ws.rglob("CLAUDE.md"):
        try:
            content = claude_md.read_text(errors="replace")
        except OSError:
            continue
        for m in _RE_CRITICAL.finditer(content):
            heading = m.group(1).strip()
            # Derive ID: lowercase, replace spaces/special chars with hyphens
            candidate_id = re.sub(r'[^a-z0-9]+', '-', heading.lower()).strip('-')
            if candidate_id not in registered:
                unregistered.append({
                    "id": candidate_id,
                    "heading": heading,
                    "file": str(claude_md.relative_to(ws)),
                })

    if json_out:
        click.echo(json.dumps({
            "total_registered": len(registered),
            "unregistered": unregistered,
        }, indent=2, ensure_ascii=False))
    else:
        click.echo(f"registered TV-1 rules: {len(registered)}")
        click.echo(f"unregistered CRITICAL sections: {len(unregistered)}")
        for u in unregistered:
            click.echo(f"  [{u['file']}] {u['heading']}")
        if not unregistered:
            click.echo("ok: all CRITICAL sections are registered in TV-1")


# ── dodaf migrate ─────────────────────────────────────────────────────────────

def _extract_critical_sections(content: str, rel_path: str) -> list[dict]:
    """Extract ## CRITICAL: sections from CLAUDE.md content."""
    lines = content.split("\n")
    sections: list[dict] = []
    cur: dict | None = None
    for line in lines:
        if line.startswith("## CRITICAL:"):
            if cur is not None:
                cur["rule_text"] = _extract_prose(cur["body"])
                sections.append(cur)
            title = line.removeprefix("## CRITICAL:").strip()
            cur = {"file": rel_path, "title": title, "body": "", "rule_text": ""}
        elif cur is not None:
            if line.startswith("## ") or line.startswith("# "):
                cur["rule_text"] = _extract_prose(cur["body"])
                sections.append(cur)
                cur = None
            else:
                cur["body"] += line + "\n"
    if cur is not None:
        cur["rule_text"] = _extract_prose(cur["body"])
        sections.append(cur)
    return sections


def _extract_prose(body: str) -> str:
    lines = body.split("\n")
    in_code = False
    prose: list[str] = []
    for line in lines:
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        trimmed = line.strip()
        if trimmed == "":
            if prose:
                break
            continue
        if trimmed.startswith("|") or trimmed.startswith("-"):
            continue
        prose.append(trimmed)
    rule = " ".join(prose)
    return rule[:800] + "..." if len(rule) > 800 else rule


def _dodaf_id_from_title(rel_path: str, title: str) -> str:
    parts = Path(rel_path).parts
    base = parts[-2] if len(parts) >= 2 else "root"
    if base in (".", ""):
        base = "root"
    slug = title.lower()
    for ch, rep in [(" ", "-"), ("/", "-"), ("（", ""), ("）", ""), ("(", ""), (")", ""),
                    ("→", ""), ("`", ""), ("'", ""), ('"', ""), (".", "-"), (":", ""),
                    ("　", "-"), ("—", "-"), ("・", "-")]:
        slug = slug.replace(ch, rep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")[:50].strip("-")
    id_ = (base + "-" + slug)[:60].strip("-")
    return id_


def _dodaf_tags_for_file(rel_path: str) -> list[str]:
    tags = ["claude", "docs"]
    if "60-apps/" in rel_path:
        tags += ["at-protocol", "kotodama", "typescript"]
    if "50-infra/" in rel_path:
        tags += ["cloudflare", "infrastructure"]
    if "orgs/etzhayyim/com-etzhayyim-svelte-" in rel_path or "orgs/etzhayyim/com-etzhayyim-vite-plugin-safe-builder" in rel_path:
        tags += ["svelte", "frontend"]
    if "30-graph/" in rel_path:
        tags += ["graph-db", "duckdb"]
    if "70-tools/" in rel_path:
        tags += ["etzhayyim-cli", "tooling"]
    if rel_path == "CLAUDE.md":
        tags += ["root-policy"]
    return tags


@dodaf.command("migrate")
@click.option("--workspace-dir", default=None)
@click.option("--dry-run", "dry_run", is_flag=True, default=False,
              help="print plan without modifying files")
@click.option("--skip-pointer", "skip_pointer", is_flag=True, default=False,
              help="only update Parquet, do not rewrite CLAUDE.md files")
def dodaf_migrate(workspace_dir: str | None, dry_run: bool, skip_pointer: bool) -> None:
    """Extract ## CRITICAL: sections from CLAUDE.md → TV-1 Parquet, replace body with pointer."""
    _require_duckdb()
    ws = _resolve_root(workspace_dir)
    pf = _dodaf_parquet(ws, "tv1_standards")
    if not pf.exists():
        click.echo("tv1_standards.parquet not found — run: etzhayyim dodaf init", err=True)
        sys.exit(1)

    existing_rows = _duckdb_query_json(f"SELECT * FROM read_parquet('{pf}')")
    registered: set[str] = {r["id"] for r in existing_rows if r.get("id")}
    tv1_rows = list(existing_rows)

    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_count = 0
    rewrite_count = 0

    _skip = {"node_modules", ".git", "__pycache__", ".venv", "dist", "build", ".turbo"}

    def _should_skip(path: Path) -> bool:
        return any(p in _skip for p in path.parts)

    for claude_md in sorted(ws.rglob("CLAUDE.md")):
        if _should_skip(claude_md.relative_to(ws)):
            continue
        try:
            content = claude_md.read_text(errors="replace")
        except OSError:
            continue
        rel_path = str(claude_md.relative_to(ws))
        sections = _extract_critical_sections(content, rel_path)
        if not sections:
            continue

        new_content = content
        modified = False

        for sec in sections:
            id_ = _dodaf_id_from_title(rel_path, sec["title"])
            orig_id = id_
            for i in range(2, 20):
                if id_ not in registered:
                    break
                id_ = f"{orig_id}-{i}"

            rule_text = sec["rule_text"] or sec["title"]
            tags = _dodaf_tags_for_file(rel_path)

            if id_ not in registered:
                tv1_rows.append({
                    "id": id_,
                    "title": sec["title"],
                    "view": "TV-1",
                    "standard_ref": "CLAUDE.md policy",
                    "rule": rule_text,
                    "severity": "high",
                    "permitted": False,
                    "scope_tags": ",".join(tags),
                    "evidence": rel_path,
                    "status": "[PRODUCTION]",
                    "source": rel_path,
                    "created_at": now,
                })
                registered.add(id_)
                new_count += 1
                if dry_run:
                    click.echo(f"+ TV-1 [{id_}] {sec['title']}")
                    click.echo(f"  rule: {rule_text[:100]}")

            if not skip_pointer:
                header = f"## CRITICAL: {sec['title']}"
                pointer = f"→ `etzhayyim dodaf tv1 query --id {id_}` / MCP `etzhayyim.dodaf.tv1.query`"
                old_block = header + "\n" + sec["body"]
                new_block = header + "\n\n" + pointer + "\n\n"
                if old_block in new_content:
                    new_content = new_content.replace(old_block, new_block, 1)
                    modified = True
                    rewrite_count += 1
                    if dry_run:
                        click.echo(f"~ CLAUDE.md pointer: {rel_path}")

        if modified and not dry_run:
            try:
                claude_md.write_text(new_content)
            except OSError as e:
                click.echo(f"warn: failed to rewrite {rel_path}: {e}", err=True)

    if dry_run:
        click.echo(f"\n[dry-run] would add {new_count} TV-1 entries, update {rewrite_count} CLAUDE.md files")
        click.echo("Run without --dry-run to apply.")
        return

    if new_count > 0:
        _write_json_to_parquet(tv1_rows, pf)

    click.echo(f"migrated: {new_count} new TV-1 entries added, {rewrite_count} CLAUDE.md files updated with pointers")


# ── dodaf seed ────────────────────────────────────────────────────────────────

@dodaf.command("seed")
@click.option("--workspace-dir", default=None)
@click.option("--pds", "pds_url", default="https://atproto.etzhayyim.com", show_default=True)
@click.option("--dry-run", "dry_run", is_flag=True, default=False,
              help="print records without seeding to PDS")
def dodaf_seed(workspace_dir: str | None, pds_url: str, dry_run: bool) -> None:
    """Push TV-1 registry to kagami/PDS for MCP etzhayyim.dodaf.tv1.query access."""
    import os as _os
    import urllib.request as _req
    _require_duckdb()
    ws = _resolve_root(workspace_dir)
    pf = _dodaf_parquet(ws, "tv1_standards")
    if not pf.exists():
        click.echo("tv1_standards.parquet not found — run: etzhayyim dodaf init", err=True)
        sys.exit(1)

    token = (_os.environ.get("etzhayyim_TOKEN") or "").strip()
    if not token and not dry_run:
        click.echo("auth required — run: etzhayyim authn signin  (or set etzhayyim_TOKEN)", err=True)
        sys.exit(1)

    rows = _duckdb_query_json(f"SELECT * FROM read_parquet('{pf}') LIMIT 100")
    click.echo(f"seeding {len(rows)} TV-1 constraints to {pds_url} ...", err=True)

    seeded = 0
    url = pds_url.rstrip("/") + "/xrpc/com.atproto.repo.createRecord"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    for row in rows:
        record = {
            "$type": "com.etzhayyim.dodaf.tv1Standard",
            "dodaf_id": row.get("id"),
            "title": row.get("title"),
            "rule": row.get("rule"),
            "severity": row.get("severity"),
            "permitted": row.get("permitted"),
            "scope_tags": row.get("scope_tags"),
            "evidence": row.get("evidence"),
            "status": row.get("status"),
            "created_at": row.get("created_at"),
        }
        if dry_run:
            click.echo(f"  [dry-run] {row.get('id')}")
            click.echo(f"  {json.dumps(record, indent=4, ensure_ascii=False)}")
            continue
        payload = json.dumps({
            "repo": "",
            "collection": "com.etzhayyim.dodaf.tv1Standard",
            "record": record,
        }).encode()
        try:
            req = _req.Request(url, data=payload, headers=headers, method="POST")
            with _req.urlopen(req, timeout=15):
                pass
            seeded += 1
        except Exception as e:
            click.echo(f"warn: seed failed for {row.get('id')}: {e}", err=True)

    if not dry_run:
        click.echo(f"seeded: {seeded}/{len(rows)} TV-1 constraints", err=True)
