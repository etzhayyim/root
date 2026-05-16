import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 66 — stricter productivity_factor buckets.
 *
 * Phase 65 priority tweak (0.6 → 0.35) only cut Wikipedia's rank ~42%,
 * not enough because hours_since_fetch dominates. Tighter productivity
 * penalty (below) deprioritizes low-row-yield targets regardless of how
 * long they've been idle.
 *
 * Before (from migration 20260424290000):
 *   rows NULL  → 1.0
 *   rows >= 20 → 1.0
 *   rows 1-19  → 0.7
 *   rows = 0   → 0.3
 *
 * After:
 *   rows NULL  → 1.0  (give new targets a fair first fetch)
 *   rows >= 30 → 1.0  (robust producers)
 *   rows 10-29 → 0.5  (medium)
 *   rows 1-9   → 0.2  (low yield — Wikipedia's tier)
 *   rows 0     → 0.1  (empty)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_maps_coverage_gap_ranked`.execute(db);
  await sql`
    CREATE VIEW view_maps_coverage_gap_ranked AS
    SELECT
      vertex_id,
      source_did,
      label,
      collected_count,
      world_total,
      priority_weight,
      last_fetched_at,
      last_rows_written,
      last_run_at,
      ttl_hours,
      CASE
        WHEN last_fetched_at IS NULL THEN ttl_hours
        ELSE EXTRACT(EPOCH FROM (NOW() - last_fetched_at))::real / 3600.0
      END AS hours_since_fetch,
      CASE
        WHEN last_rows_written IS NULL THEN 1.0
        WHEN last_rows_written >= 30  THEN 1.0
        WHEN last_rows_written >= 10  THEN 0.5
        WHEN last_rows_written >= 1   THEN 0.2
        ELSE                               0.1
      END::real AS productivity_factor,
      maps_coverage_gap_score(
        collected_count,
        world_total,
        priority_weight,
        CASE
          WHEN last_fetched_at IS NULL THEN ttl_hours
          ELSE EXTRACT(EPOCH FROM (NOW() - last_fetched_at))::real / 3600.0
        END
      ) *
      (CASE
        WHEN last_rows_written IS NULL THEN 1.0
        WHEN last_rows_written >= 30  THEN 1.0
        WHEN last_rows_written >= 10  THEN 0.5
        WHEN last_rows_written >= 1   THEN 0.2
        ELSE                               0.1
      END)::double precision AS gap_score
    FROM vertex_maps_coverage_target
    ORDER BY gap_score DESC
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_maps_coverage_gap_ranked`.execute(db);
  // Re-apply original buckets via 20260424290000 rebuild if rolling back.
}
