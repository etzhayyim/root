/**
 * SQL UDF: classify_coverage_recipe(domain text) → text
 * MV:      mv_coverage_gap_minimax
 *
 * ADR-0044: SQL UDF = rules/aggregate (plan-time inline).
 *           Python External UDF (io_threads=100) = LLM/IO — NOT mixed here.
 *
 * UDF returns the recipe_kind for a given domain (fast O(1) lookup for BPMN).
 * MV ranks (domain, authority_kind) by minimax regret = world_total × (1 − coverage)
 * so coverage.gap.scan can SELECT TOP-1 without a full table scan every cycle.
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // SQL UDF: classify_coverage_recipe
  // RisingWave does not support CREATE OR REPLACE FUNCTION — drop then create.
  await sql`DROP FUNCTION IF EXISTS classify_coverage_recipe(text)`.execute(db);
  await sql`
    CREATE FUNCTION classify_coverage_recipe(p_domain text)
    RETURNS text
    LANGUAGE sql
    AS $$
      SELECT COALESCE(
        (SELECT recipe_kind FROM vertex_coverage_recipe
         WHERE domain = p_domain AND authority_kind = 'world'
         LIMIT 1),
        'defer'
      )
    $$
  `.execute(db);

  // MV: mv_coverage_gap_minimax
  // Joins vertex_coverage_recipe with live world coverage stats.
  // Regret = world_total × (1 − coverage_rate): the larger, the worse the gap.
  // BPMN scan task runs: SELECT * FROM mv_coverage_gap_minimax
  //   WHERE recipe_kind != 'defer' ORDER BY regret DESC LIMIT 1
  //
  // NOTE: world coverage stats (coverage_rate, collected) come from etzhayyim CLI
  // which reads from the PDS graph. We approximate here using recipe world_total
  // and a fallback of 0 for collected (worst-case regret = world_total).
  // A future phase will join vertex_coverage_recipe with a live stats MV.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_coverage_gap_minimax AS
    SELECT
      r.domain,
      r.authority_kind,
      r.recipe_kind,
      r.source_url,
      r.llm_tier,
      r.langgraph_id,
      r.world_total,
      r.notes,
      -- regret = world_total * (1 - estimated_coverage)
      -- Phase 1: coverage estimated as 0 for zero-collected domains
      CAST(r.world_total AS double precision) AS regret,
      r.created_at
    FROM vertex_coverage_recipe r
    WHERE r.recipe_kind != 'defer'
    ORDER BY regret DESC
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_coverage_gap_minimax`.execute(db);
  await sql`DROP FUNCTION IF EXISTS classify_coverage_recipe(text)`.execute(db);
}
