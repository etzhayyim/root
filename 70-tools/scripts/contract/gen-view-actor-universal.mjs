#!/usr/bin/env node
// Codegen: view_actor_universal + SQL UDF derive_did / derive_handle.
//
// Introspects live RisingWave `information_schema` and emits a Kysely
// migration that builds a plain VIEW unioning every `vertex_*` table that
// carries both a `vertex_id` PK and at least one human-readable text column.
//
// Plain VIEW (not MATERIALIZED) by design: 305 sources include vertex_page
// (985M rows). Query-time UNION with optimizer `kind`-filter pruning avoids
// 250 GB streaming state. See 30-graph/graph-schema/CLAUDE.md §MV Memory
// Safety Guardrails and §Option A (vertex_page never scanned by streaming MV).
//
// Exit policy: emits migration path on stdout. Re-run after any new
// `vertex_*` table to refresh the union; check the diff before committing.
//
// Usage:
//   DATABASE_URL=postgresql://... node 70-tools/scripts/contract/gen-view-actor-universal.mjs

import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import pg from "pg";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const migrationsDir = path.join(repoRoot, "30-graph/graph-schema/migrations");

const DATABASE_URL = process.env.DATABASE_URL;
if (!DATABASE_URL) {
  console.error("DATABASE_URL required (RisingWave PG wire, e.g. REDACTED_USE_DATABASE_URL_ENV)");
  process.exit(2);
}

// Skip these: too large to UNION in a plain VIEW read path, or not a domain
// actor (commit log / raw block store / page index dumping ground).
// Excluding vertex_page (985M rows) avoids P95 query blowup; page actors
// surface through a dedicated `kind=page` shard in L3 IVF later.
const EXCLUDE = new Set([
  "vertex_repo_commit",      // commit log (ADR-0041 content-PK), not an actor
  "vertex_repo_block",       // block store (CID blobs), not an actor
  "vertex_repo_record",      // raw AT Record dump (superset of actor tables)
  "vertex_page",             // 985M rows — separate IVF shard later
  "vertex_page_count_cache", // 1-row cache
  // MV-ish targets that would cause recursive self-scan
  "vertex_actor_universal",
]);

// Columns we search / project from source tables. First non-null wins.
const NAME_COLS  = ["display_name", "name", "title", "label"];
const DESC_COLS  = ["description", "summary", "body", "text", "content", "bio"];
const AVATAR_COLS = ["avatar_cid"];
const CREATED_COLS = ["created_at", "indexed_at"];
const UPDATED_COLS = ["updated_at", "indexed_at"];

async function main() {
  const client = new pg.Client({ connectionString: DATABASE_URL });
  await client.connect();

  const { rows } = await client.query(`
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema='public' AND table_name LIKE 'vertex_%'
  `);

  // table_name → Set<column_name>
  const cols = new Map();
  for (const r of rows) {
    if (!cols.has(r.table_name)) cols.set(r.table_name, new Set());
    cols.get(r.table_name).add(r.column_name);
  }

  // Filter: must have vertex_id and at least one text column.
  const sources = [];
  for (const [tbl, colset] of cols.entries()) {
    if (EXCLUDE.has(tbl)) continue;
    if (!colset.has("vertex_id")) continue;
    const hasName = NAME_COLS.some((c) => colset.has(c));
    const hasDesc = DESC_COLS.some((c) => colset.has(c));
    if (!hasName && !hasDesc) continue;
    sources.push({ tbl, cols: colset });
  }
  sources.sort((a, b) => a.tbl.localeCompare(b.tbl));
  await client.end();

  const pickFirst = (colset, cands) => {
    for (const c of cands) if (colset.has(c)) return c;
    return null;
  };

  // Emit SQL with a trailing cast only when the expression isn't already typed.
  // Avoids `NULL::VARCHAR::VARCHAR` double-cast noise.
  const coalesceCast = (colset, cands) => {
    const present = cands.filter((c) => colset.has(c));
    if (present.length === 0) return "NULL::VARCHAR";
    if (present.length === 1) return `${present[0]}::VARCHAR`;
    return `COALESCE(${present.join(", ")})::VARCHAR`;
  };

  const kindOf = (tbl) => tbl.replace(/^vertex_/, "");

  const branches = sources.map(({ tbl, cols }) => {
    const didExpr     = cols.has("did")        ? "did::VARCHAR"        : `derive_did(vertex_id, '${kindOf(tbl)}')`;
    const handleExpr  = cols.has("handle")     ? "handle::VARCHAR"     : `derive_handle(vertex_id, '${kindOf(tbl)}')`;
    const nameExpr    = coalesceCast(cols, NAME_COLS);
    const descExpr    = coalesceCast(cols, DESC_COLS);
    const avatarExpr  = coalesceCast(cols, AVATAR_COLS);
    const createdExpr = coalesceCast(cols, CREATED_COLS);
    const updatedExpr = coalesceCast(cols, UPDATED_COLS);
    const ptype       = cols.has("performer_type") ? "performer_type::VARCHAR" : "'service'::VARCHAR";
    const parentDid   = `'did:web:actor.etzhayyim.com:${kindOf(tbl)}'::VARCHAR`;
    return `  SELECT
    ${didExpr}     AS did,
    ${handleExpr}  AS handle,
    ${nameExpr}    AS display_name,
    ${descExpr}    AS description,
    ${avatarExpr}  AS avatar_cid,
    '${kindOf(tbl)}'::VARCHAR AS kind,
    ${parentDid}   AS parent_did,
    vertex_id::VARCHAR AS vertex_id,
    ${ptype}       AS performer_type,
    ${createdExpr} AS created_at,
    ${updatedExpr} AS updated_at
  FROM ${tbl}`;
  });

  const ts = (() => {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}${pad(d.getUTCHours())}${pad(d.getUTCMinutes())}${pad(d.getUTCSeconds())}`;
  })();
  const filename = `${ts}_view_actor_universal.ts`;
  const outPath = path.join(migrationsDir, filename);

  const header = `// tier: C
// Generated by 70-tools/scripts/contract/gen-view-actor-universal.mjs
// Source: information_schema @ ${new Date().toISOString()}
// Sources: ${sources.length} vertex_* tables (vertex_id + name|desc column present)
// Excluded: ${[...EXCLUDE].join(", ")}
//
// DO NOT HAND-EDIT. Regenerate with:
//   DATABASE_URL=... node 70-tools/scripts/contract/gen-view-actor-universal.mjs
//
// Plain VIEW (not MATERIALIZED) — see 30-graph/graph-schema/CLAUDE.md
// §MV Memory Safety Guardrails. Optimizer prunes branches when caller
// filters by \`kind\`.
//
// L1 of the 6-layer actor topology (see ADR draft 0061-every-vertex-as-actor):
//   L0 Identity  — derived path-DID (derive_did / derive_handle UDFs)
//   L1 Profile   — THIS FILE (plain VIEW view_actor_universal)
//   L2 Embedding — mv_actor_embedding (later, 384d multilingual-e5-small)
//   L3 Registry  — mv_actor_capability + per-kind IVF_PQ (later)
//   L4 MCP       — did-resolver + mcp-facade Workers (later)
//   L5 BPMN      — inherited from kind (existing ADR-0056)
//   L6 Discovery — registry.etzhayyim.com meta-MCP (later)
import { Kysely, sql } from "kysely";

`;

  const upFn = `export async function up(db: Kysely<unknown>): Promise<void> {
  // ── SQL UDFs: path-DID synthesis (ADR-0019 / ADR-0029 path-form sub-DID) ──
  // Input vertex_id is an AT URI "at://<authority>/<collection>/<rkey>" OR
  // a legacy opaque string. regexp_replace strips everything up to and
  // including the final '/', yielding <rkey> (or the full string if no /).
  // Parent DID = did:web:actor.etzhayyim.com:<kind> (depth-2 path root).
  // SQL UDF per ADR-0044 (plan-time inline, native vector eval).
  await sql\`DROP FUNCTION IF EXISTS derive_did(varchar, varchar)\`.execute(db);
  await sql\`
    CREATE FUNCTION derive_did(vertex_id varchar, kind varchar)
    RETURNS varchar
    LANGUAGE sql
    AS $$
      SELECT 'did:web:actor.etzhayyim.com:' || kind || ':' ||
        regexp_replace(vertex_id, '^.*/', '')
    $$
  \`.execute(db);
  await sql\`FLUSH\`.execute(db);

  await sql\`DROP FUNCTION IF EXISTS derive_handle(varchar, varchar)\`.execute(db);
  await sql\`
    CREATE FUNCTION derive_handle(vertex_id varchar, kind varchar)
    RETURNS varchar
    LANGUAGE sql
    AS $$
      SELECT regexp_replace(vertex_id, '^.*/', '') || '.' || kind || '.etzhayyim.com'
    $$
  \`.execute(db);
  await sql\`FLUSH\`.execute(db);

  // ── view_actor_universal: ${sources.length}-source UNION ALL (plain VIEW) ──
  // No materialization → 0 streaming state, instant create, no backfill.
  // Optimizer prunes inactive branches on \`kind = '...'\` filter.
  await sql\`CREATE VIEW view_actor_universal AS
${branches.join("\n  UNION ALL\n")}\`.execute(db);
  await sql\`FLUSH\`.execute(db);
}

`;

  const downFn = `export async function down(db: Kysely<unknown>): Promise<void> {
  await sql\`DROP VIEW IF EXISTS view_actor_universal\`.execute(db);
  await sql\`FLUSH\`.execute(db);
  await sql\`DROP FUNCTION IF EXISTS derive_handle(VARCHAR, VARCHAR)\`.execute(db);
  await sql\`DROP FUNCTION IF EXISTS derive_did(VARCHAR, VARCHAR)\`.execute(db);
  await sql\`FLUSH\`.execute(db);
}
`;

  const content = header + upFn + downFn;

  if (!existsSync(migrationsDir)) mkdirSync(migrationsDir, { recursive: true });
  writeFileSync(outPath, content);
  console.log(`[codegen] wrote ${sources.length} sources → ${outPath}`);
}

main().catch((e) => { console.error(e); process.exit(1); });
