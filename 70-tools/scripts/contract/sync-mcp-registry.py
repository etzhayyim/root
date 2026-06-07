#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
Sync app lexicon JSON files on disk → `vertex_mcp_tool_def`.

Replaces the build-time codegen path (`gen-tool-manifest.mjs`) with a
runtime DB-backed registry. host-sdk `/mcp` reads this table via Kysely
+ 60s in-memory cache to answer `tools/list`. Runtime input validation
for `tools/call` stays inside `app.handleXRPC` →
`parseLexiconInput(nsid, body)` against the generated
`LEXICON_INPUT_SCHEMA` (separate codegen we still keep). The DB
`input_schema` column is the MCP-published surface; the TS validator is
runtime enforcement. Both come from the same lexicon JSON.

See: 90-docs/adr/2604261000-mcp-registry-via-kysely-schema.md
     90-docs/adr/0087-magatama-mcp-tool-facade.md (amended D3)
     ADR-0056 — same `INSERT N rows` pattern as BPMN-as-actor

Convention:
  vertex_id = at://did:web:{actor-host}/com.etzhayyim.mcp.toolDef/{slug}
    where slug = nsid.replace(".", "-")
  actor_did  = did:web:{actor-host}.etzhayyim.com
    where actor-host = the 4th NSID segment (`com.etzhayyim.apps.<actor>.<method>`)

Behavior:
  --apply    : upsert rows
  (default)  : dry-run diff
  --strict   : exit 1 if any drift detected (CI gate)
  --only-drift: only print rows that differ from disk
  --only NS  : restrict to lexicons under 00-contracts/lexicons/com/etzhayyim/apps/{NS}/
               or special state actor roots such as govInd/govAfg

Never deletes. Honors `enabled=false` on the row (won't flip back).

Env:
  KOTOBA_URL   postgresql://…  ;  default from Keychain etzhayyim.rw/ROOT_URL
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
LEX_ROOT = REPO_ROOT / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "apps"
GOVIND_LEX_ROOT = REPO_ROOT / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "govInd"
GOVAFG_LEX_ROOT = REPO_ROOT / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "govAfg"
TOOL_REPO_PREFIX = "at://did:web:{host}.etzhayyim.com/com.etzhayyim.mcp.toolDef"


# ─── Keychain / psql ───────────────────────────────────────────────────


def rw_url() -> str:
    if url := os.environ.get("KOTOBA_URL"):
        return url
    out = subprocess.check_output(
        ["security", "find-generic-password", "-s", "etzhayyim.rw", "-a", "ROOT_URL", "-w"],
        text=True,
    ).strip()
    if not out:
        raise SystemExit("KOTOBA_URL not in env and not in Keychain (etzhayyim.rw/ROOT_URL)")
    return out


# ─── Lexicon parse ─────────────────────────────────────────────────────


@dataclass
class ParsedTool:
    nsid: str
    actor: str  # 4th NSID segment
    rel_path: str
    lexicon_type: str  # 'procedure' | 'query'
    description: str
    input_schema_json: str
    output_schema_json: str
    schema_hash: str

    @property
    def actor_did(self) -> str:
        if self.actor == "govInd":
            return "did:web:ind-state.etzhayyim.com"
        if self.actor == "govAfg":
            return "did:web:afg-state.etzhayyim.com"
        return f"did:web:{self.actor}.etzhayyim.com"

    @property
    def actor_host(self) -> str:
        if self.actor == "govInd":
            return "ind-state.etzhayyim.com"
        if self.actor == "govAfg":
            return "afg-state.etzhayyim.com"
        return f"{self.actor}.etzhayyim.com"

    @property
    def vertex_id(self) -> str:
        slug = self.nsid.replace(".", "-")
        if self.actor == "govInd":
            host = "ind-state"
        elif self.actor == "govAfg":
            host = "afg-state"
        else:
            host = self.actor
        return f"{TOOL_REPO_PREFIX.format(host=host)}/{slug}"


def parse_lexicon(path: Path) -> ParsedTool | None:
    """Parse a lexicon JSON. Return None if not an MCP-exposable
    procedure/query (records, permission-sets, etc are skipped)."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(doc, dict):
        return None
    nsid = doc.get("id")
    if not isinstance(nsid, str) or not (
        nsid.startswith("com.etzhayyim.apps.")
        or nsid.startswith("com.etzhayyim.govInd.")
        or nsid.startswith("com.etzhayyim.govAfg.")
    ):
        return None
    parts = nsid.split(".")
    if nsid.startswith("com.etzhayyim.apps.") and len(parts) < 5:
        return None
    if nsid.startswith("com.etzhayyim.govInd."):
        actor = "govInd"
    elif nsid.startswith("com.etzhayyim.govAfg."):
        actor = "govAfg"
    else:
        actor = parts[3]
    method_def = (doc.get("defs") or {}).get("main") or {}
    lex_type = method_def.get("type")
    if lex_type not in ("procedure", "query"):
        return None

    if lex_type == "query":
        input_schema = method_def.get("parameters") or {}
    else:
        input_schema = (method_def.get("input") or {}).get("schema") or {}
    output_schema = (method_def.get("output") or {}).get("schema") or {}
    description = method_def.get("description") or doc.get("description") or ""

    input_json = json.dumps(input_schema, sort_keys=True, separators=(",", ":"))
    output_json = json.dumps(output_schema, sort_keys=True, separators=(",", ":"))
    schema_hash = hashlib.sha256(
        (description + "\x00" + input_json + "\x00" + output_json).encode("utf-8")
    ).hexdigest()[:16]

    return ParsedTool(
        nsid=nsid,
        actor=actor,
        rel_path=str(path.relative_to(REPO_ROOT)),
        lexicon_type=lex_type,
        description=description,
        input_schema_json=input_json,
        output_schema_json=output_json,
        schema_hash=schema_hash,
    )


def walk_lexicons(only_ns: str | None) -> list[ParsedTool]:
    out: list[ParsedTool] = []
    if only_ns:
        if only_ns == "govInd":
            roots = [GOVIND_LEX_ROOT]
        elif only_ns == "govAfg":
            roots = [GOVAFG_LEX_ROOT]
        else:
            roots = [LEX_ROOT / only_ns]
    else:
        roots = [LEX_ROOT, GOVIND_LEX_ROOT, GOVAFG_LEX_ROOT]
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.json"):
            parsed = parse_lexicon(path)
            if parsed is not None:
                out.append(parsed)
    return out


# ─── DB read/write ─────────────────────────────────────────────────────


def psql_run(sql: str) -> list[list[str]]:
    args = ["psql", rw_url(), "-tA", "-F", "\t", "-c", sql]
    out = subprocess.check_output(args, text=True, stderr=subprocess.PIPE, timeout=30)
    rows: list[list[str]] = []
    for line in out.splitlines():
        if line:
            rows.append(line.split("\t"))
    return rows


def load_existing() -> dict[str, dict[str, Any]]:
    """vertex_id → {nsid, schema_hash, enabled, version}."""
    rows = psql_run(
        "SELECT vertex_id, nsid, COALESCE(schema_hash,''), "
        "COALESCE(enabled, TRUE)::text, COALESCE(version, 1) "
        "FROM vertex_mcp_tool_def"
    )
    return {
        r[0]: {
            "vertex_id": r[0],
            "nsid": r[1],
            "schema_hash": r[2],
            "enabled": r[3] in ("t", "true", "TRUE"),
            "version": int(r[4]),
        }
        for r in rows
    }


def apply_batch(diffs: list[Diff], batch_size: int = 5) -> int:
    """Apply all drifted rows on a single connection in batched
    multi-row INSERTs (batch_size per statement) and per-row UPDATEs.

    RisingWave issues a barrier per write; large bulk INSERTs trigger
    a barrier storm and tip the cluster into recovery. Per
    `[[conventions]] rw-bulk-insert-throttle`, we cap with
    `SET dml_rate_limit` and use small batches with a brief
    inter-batch sleep so the streaming graph can drain.

    Returns the number of rows applied.
    """
    import time

    import psycopg2  # lazy import — only needed in --apply

    inserts = [d.parsed for d in diffs if d.action == "insert"]
    updates = [d.parsed for d in diffs if d.action == "update"]
    applied = 0

    conn = psycopg2.connect(rw_url())
    # RisingWave buffers DML until a checkpoint. Without implicit flush (or an
    # explicit FLUSH), INSERT can return success while a later read still sees
    # no row, and the buffered write can be lost on recovery.
    conn.autocommit = True
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SET statement_timeout = '90s'")
            cur.execute("SET RW_IMPLICIT_FLUSH = true")
            cur.execute("SET dml_rate_limit = 1000")  # rows/sec/parallelism
            for i in range(0, len(inserts), batch_size):
                chunk = inserts[i : i + batch_size]
                values_sql = ",".join(
                    cur.mogrify(
                        "(%s,%s,%s,%s,%s,%s,%s,%s,%s,'public',1,TRUE,%s,%s,%s,0,to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"'))",
                        (
                            p.vertex_id,
                            p.nsid,
                            p.actor_did,
                            p.actor_host,
                            p.lexicon_type,
                            p.description,
                            p.input_schema_json,
                            p.output_schema_json,
                            p.nsid,
                            p.rel_path,
                            p.schema_hash,
                            p.actor_did,
                        ),
                    ).decode()
                    for p in chunk
                )
                cur.execute(
                    "INSERT INTO vertex_mcp_tool_def ("
                    "vertex_id, nsid, actor_did, actor_host, lexicon_type, "
                    "description, input_schema, output_schema, lxm_scope, "
                    "visibility, version, enabled, source_path, schema_hash, "
                    "owner_did, sensitivity_ord, created_at) VALUES " + values_sql
                )
                cur.execute("FLUSH")
                applied += len(chunk)
                print(f"  inserted {applied}/{len(inserts)}", file=sys.stderr)
                time.sleep(0.25)  # let streaming graph drain between batches

            for p in updates:
                cur.execute(
                    'UPDATE vertex_mcp_tool_def SET '
                    '"description" = %s, '
                    '"input_schema" = %s, '
                    '"output_schema" = %s, '
                    '"lexicon_type" = %s, '
                    '"source_path" = %s, '
                    '"schema_hash" = %s, '
                    '"deployed_at" = NULL '
                    'WHERE "vertex_id" = %s',
                    (
                        p.description,
                        p.input_schema_json,
                        p.output_schema_json,
                        p.lexicon_type,
                        p.rel_path,
                        p.schema_hash,
                        p.vertex_id,
                    ),
                )
                applied += 1
            if updates:
                cur.execute("FLUSH")
    finally:
        conn.close()
    return applied


# ─── Diff / report ─────────────────────────────────────────────────────


@dataclass
class Diff:
    parsed: ParsedTool
    action: str  # 'insert' | 'update' | 'unchanged'
    reason: str


def diff_tools(parsed_list: list[ParsedTool], existing: dict[str, dict[str, Any]]) -> list[Diff]:
    diffs: list[Diff] = []
    for p in parsed_list:
        row = existing.get(p.vertex_id)
        if row is None:
            diffs.append(Diff(p, "insert", "new"))
        elif row["schema_hash"] != p.schema_hash:
            diffs.append(Diff(p, "update", f"schema_hash {row['schema_hash']!r} → {p.schema_hash!r}"))
        else:
            diffs.append(Diff(p, "unchanged", ""))
    return diffs


# ─── CLI ───────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="upsert rows (default: dry-run)")
    ap.add_argument("--only", help="restrict to a single namespace (e.g. yoro)")
    ap.add_argument("--only-drift", action="store_true", help="omit unchanged rows from output")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any drift (CI gate)")
    ap.add_argument("--json", action="store_true", help="machine output")
    ap.add_argument(
        "--lint-only",
        action="store_true",
        help="parse + structurally validate lexicons, no DB connection (fork-safe PR gate)",
    )
    args = ap.parse_args()

    parsed_list = walk_lexicons(args.only)
    if not parsed_list:
        msg = f"no app lexicons found under {LEX_ROOT}" + (f" (only={args.only})" if args.only else "")
        print(msg, file=sys.stderr)
        return 0

    if args.lint_only:
        print(f"{len(parsed_list)} lexicons parsed cleanly", file=sys.stderr)
        seen_nsid: dict[str, str] = {}
        problems: list[str] = []
        for p in parsed_list:
            if p.nsid in seen_nsid:
                problems.append(f"  duplicate NSID {p.nsid}: {seen_nsid[p.nsid]} <-> {p.rel_path}")
            else:
                seen_nsid[p.nsid] = p.rel_path
            if p.lexicon_type not in ("procedure", "query"):
                problems.append(f"  invalid lexicon_type {p.lexicon_type!r} in {p.rel_path}")
        if problems:
            print("lexicon lint failures:", file=sys.stderr)
            for line in problems:
                print(line, file=sys.stderr)
            return 1
        return 0

    existing = load_existing()
    diffs = diff_tools(parsed_list, existing)

    drifted = [d for d in diffs if d.action != "unchanged"]
    shown = drifted if args.only_drift else diffs

    if args.json:
        out = [
            {
                "nsid": d.parsed.nsid,
                "actor_did": d.parsed.actor_did,
                "vertex_id": d.parsed.vertex_id,
                "lexicon_type": d.parsed.lexicon_type,
                "schema_hash": d.parsed.schema_hash,
                "action": d.action,
                "reason": d.reason,
            }
            for d in shown
        ]
        print(json.dumps(out, indent=2))
    else:
        for d in shown:
            tag = {"insert": "+", "update": "~", "unchanged": "="}[d.action]
            print(f"{tag} {d.parsed.nsid} ({d.parsed.actor_did}) {d.reason}")
        print(
            f"\n{len(parsed_list)} lexicons, "
            f"{sum(1 for d in diffs if d.action == 'insert')} insert, "
            f"{sum(1 for d in diffs if d.action == 'update')} update, "
            f"{sum(1 for d in diffs if d.action == 'unchanged')} unchanged",
            file=sys.stderr,
        )

    if args.apply:
        applied = apply_batch(drifted)
        remaining = [d for d in diff_tools(parsed_list, load_existing()) if d.action != "unchanged"]
        if remaining:
            print(
                f"apply verification failed: {len(remaining)} row(s) still drift after apply",
                file=sys.stderr,
            )
            return 2
        print(f"applied {applied} rows", file=sys.stderr)

    if args.strict and drifted and not args.apply:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
