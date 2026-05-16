import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Intermediate MVs for canonical DID pre-computation + page count VIEW.
 *
 * Option A design (2026-04-16): vertex_page (985M rows) is NOT scanned by
 * any streaming MV. Page-count statistics are exposed as a plain VIEW
 * (view_page_count_by_canonical_did) that executes at query time.
 *
 * Objects added:
 *
 *   view_page_count_by_canonical_did  (plain VIEW — query-time)
 *     canonical_actor_did, page_count — calls normalize_actor_did() over
 *     vertex_page at query time. No backfill, no streaming state.
 *
 *   mv_actor_canonical_did  (streaming MV)
 *     (raw_did, canonical_did) — actor sources only (social + governance +
 *     tools). vertex_page is intentionally excluded to avoid the 985M-row
 *     backfill that caused repeated cluster failovers.
 *     Narrow: 2 varchar columns, ~few thousand distinct rows.
 *     Downstream: any future actor-aggregation MV.
 *
 *   mv_did_web_root_index  (streaming MV)
 *     (sub_did, root_did) — maps every did:web DID to its 3-segment root.
 *     Source: vertex_did WHERE did LIKE 'did:web:%' (~16K rows).
 *     Downstream: mv_actor_repo_stats hierarchy lookups.
 *
 * Memory safety (post-0026-v1 guardrails):
 *   - Both MVs source from small tables (< 500K rows, < 500K distinct keys).
 *   - No MAX(varchar) over wide payload columns.
 *   - vertex_page is VIEW-only — never scanned by a streaming MV.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── view_page_count_by_canonical_did ──────────────────────────────────────
  // Plain VIEW: page counts aggregated by canonical owner DID.
  // Executes at query time — vertex_page (985M rows) is never held in MV state.
  await sql`DROP VIEW IF EXISTS view_page_count_by_canonical_did`.execute(db);
  await sql`
    CREATE VIEW view_page_count_by_canonical_did AS
    SELECT
      normalize_actor_did(owner_did) AS canonical_actor_did,
      CAST(COUNT(*) AS BIGINT) AS page_count
    FROM vertex_page
    WHERE owner_did IS NOT NULL AND owner_did <> ''
    GROUP BY 1
  `.execute(db);

  // ── mv_actor_canonical_did ─────────────────────────────────────────────────
  // Pre-compute normalize_actor_did() once per unique raw DID across actor
  // sources. Actor sources only — vertex_page excluded (985M rows, Option A).
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_canonical_did`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_canonical_did AS
    SELECT DISTINCT
      raw_did,
      normalize_actor_did(raw_did) AS canonical_did
    FROM (
      SELECT actor_did AS raw_did FROM mv_actor_social_stats
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_governance_policy
      UNION ALL
      SELECT actor_did AS raw_did FROM mv_actor_tool_grants
    ) s
  `.execute(db);

  // ── mv_did_web_root_index ──────────────────────────────────────────────────
  // Pre-compute did_web_root() once per unique did:web DID in vertex_did.
  // Provides a stable (sub_did → root_did) index for tree-hierarchy lookups in
  // mv_actor_repo_stats without repeating the SPLIT_PART concatenation.
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_did_web_root_index`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_did_web_root_index AS
    SELECT DISTINCT
      did  AS sub_did,
      did_web_root(did) AS root_did
    FROM vertex_did
    WHERE did LIKE 'did:web:%'
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_did_web_root_index`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_canonical_did`.execute(db);
  await sql`DROP VIEW IF EXISTS view_page_count_by_canonical_did`.execute(db);
}
