import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Per-source productivity weighting: track last_rows_written / last_run_at
 * per frontier target, multiply into gap_score so consistently-0 sources
 * get deprioritized and productive sources picked more often.
 *
 * Observation (iter 37): many niche Wikidata profiles (salt_pond /
 * tea_garden / bakehouse / fishery / cableCar / oilField / busRoute) return
 * 0 rows because matching entities are sparse in current bbox rotation.
 * CronJob keeps picking them, wasting Wikidata rate budget.
 *
 * Productivity factor:
 *   last_rows_written >= 20  → 1.0  (productive)
 *   last_rows_written 1-19   → 0.7  (marginal)
 *   last_rows_written =  0   → 0.3  (penalty — picked occasionally, not always)
 *   last_rows_written NULL   → 1.0  (new row, give it a full chance)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_maps_coverage_target ADD COLUMN IF NOT EXISTS last_rows_written integer`.execute(db);
  await sql`ALTER TABLE vertex_maps_coverage_target ADD COLUMN IF NOT EXISTS last_run_at timestamp`.execute(db);

  // Rebuild the ranked view with productivity factor baked into gap_score.
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
        WHEN last_rows_written IS NULL                THEN 1.0
        WHEN last_rows_written >= 20                  THEN 1.0
        WHEN last_rows_written >= 1                   THEN 0.7
        ELSE                                               0.3
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
        WHEN last_rows_written IS NULL                THEN 1.0
        WHEN last_rows_written >= 20                  THEN 1.0
        WHEN last_rows_written >= 1                   THEN 0.7
        ELSE                                               0.3
      END)::double precision AS gap_score
    FROM vertex_maps_coverage_target
    ORDER BY gap_score DESC
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_maps_coverage_gap_ranked`.execute(db);
  // Original view rebuild would be needed — for now leave dropped; re-apply
  // 20260424080000 manually if rolling back.
}
