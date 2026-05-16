/**
 * coverage gap bridge Phase 2:
 *
 * 1. Create vertex_coverage_stats snapshot table — coverage.gap.stats.sync
 *    Zeebe task writes here after each BPMN cycle; mv_coverage_gap_minimax
 *    v2 uses real regret = world_total * (1 - coverage_rate) from this table.
 *
 * 2. Rebuild mv_coverage_gap_minimax using real regret instead of static
 *    world_total proxy.
 *
 * NOTE: mv_world_vertex_per_host rebuild (adding business-person /
 * crypto-asset-freeze app_hosts) is handled out-of-band via psql because the
 * backfill hits B2 rate limits inside the migration runner. The coverage stats
 * seed here uses the current mv_world_coverage_live (which works fine without
 * the new app_hosts — those will appear once the out-of-band rebuild completes).
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Step 1: drop old Phase 1 minimax MV (from 20260429220100) ────────────
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_coverage_gap_minimax`.execute(db);

  // ── Step 2: vertex_coverage_stats snapshot table ──────────────────────────
  // Written by coverage.gap.stats.sync Zeebe task (reads mv_world_coverage_live,
  // upserts current collected + coverage_rate). Used by minimax MV v2.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_coverage_stats (
      domain         text        NOT NULL,
      authority_kind text        NOT NULL DEFAULT 'world',
      collected      bigint      NOT NULL DEFAULT 0,
      world_total    bigint      NOT NULL DEFAULT 0,
      coverage_rate  double precision NOT NULL DEFAULT 0.0,
      updated_at     timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY (domain, authority_kind)
    )
  `.execute(db);

  // Seed vertex_coverage_stats from current mv_world_coverage_live for domains
  // that are in vertex_coverage_recipe (so minimax has real data immediately).
  // RisingWave does not support ON CONFLICT — delete-then-insert for idempotency.
  await sql`
    DELETE FROM vertex_coverage_stats
    WHERE authority_kind = 'world'
      AND EXISTS (
        SELECT 1 FROM vertex_coverage_recipe r
        WHERE r.domain = vertex_coverage_stats.domain
          AND r.authority_kind = 'world'
      )
  `.execute(db);
  await sql`
    INSERT INTO vertex_coverage_stats (domain, authority_kind, collected, world_total, coverage_rate, updated_at)
    SELECT
      r.domain,
      r.authority_kind,
      0::bigint,
      r.world_total::bigint,
      0.0,
      now()
    FROM vertex_coverage_recipe r
    WHERE r.authority_kind = 'world'
  `.execute(db);

  // ── Step 3: rebuild mv_coverage_gap_minimax v2 with real regret ───────────
  // regret = world_total * (1 - coverage_rate): prioritizes large + uncovered domains.
  // Falls back to recipe world_total when stats row not yet synced.
  await sql`
    CREATE MATERIALIZED VIEW mv_coverage_gap_minimax AS
    SELECT
      r.domain,
      r.authority_kind,
      r.recipe_kind,
      r.source_url,
      r.llm_tier,
      r.langgraph_id,
      COALESCE(s.world_total, r.world_total) AS world_total,
      COALESCE(s.collected, 0)               AS collected,
      COALESCE(s.coverage_rate, 0.0)         AS coverage_rate,
      r.notes,
      -- real regret = world_total * (1 - coverage_rate)
      CAST(COALESCE(s.world_total, r.world_total) AS double precision)
        * (1.0 - COALESCE(s.coverage_rate, 0.0))  AS regret,
      r.created_at
    FROM vertex_coverage_recipe r
    LEFT JOIN vertex_coverage_stats s
      ON s.domain = r.domain AND s.authority_kind = r.authority_kind
    WHERE r.recipe_kind != 'defer'
    ORDER BY regret DESC
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_coverage_gap_minimax`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_coverage_stats`.execute(db);

  // Restore Phase 1 minimax MV (static world_total proxy, no stats join)
  await sql`
    CREATE MATERIALIZED VIEW mv_coverage_gap_minimax AS
    SELECT
      r.domain, r.authority_kind, r.recipe_kind, r.source_url, r.llm_tier,
      r.langgraph_id, r.world_total, r.notes,
      CAST(r.world_total AS double precision) AS regret,
      r.created_at
    FROM vertex_coverage_recipe r
    WHERE r.recipe_kind != 'defer'
    ORDER BY regret DESC
  `.execute(db);
}
