import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Streaming MV `mv_shinshi_coverage_buckets` — second-level aggregate of
 * `mv_shinshi_repo_stats`.
 *
 * Holds 4 numbers (zero/partial/complete/total) over the 1,649-row source MV.
 * Coverage query goes from "scan 1649 + COUNT FILTER bucket" (4s pureQuery
 * under RW load, observed 2026-05-09) to "read 1 row" (<50ms expected).
 *
 * Built on top of `mv_shinshi_repo_stats` (migration 20260509001000), so RW
 * maintains it incrementally — no re-scan of `vertex_repo_record` needed.
 *
 * Cardinality: 1 row. Memory footprint negligible. Safe per CLAUDE.md MV
 * memory guardrails (no high-cardinality GROUP BY, no MAX(varchar)).
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinshi_coverage_buckets AS
    SELECT
      COUNT(*) FILTER (WHERE post_count = 0) AS zero,
      COUNT(*) FILTER (WHERE post_count BETWEEN 1 AND 4) AS partial,
      COUNT(*) FILTER (WHERE post_count >= 5) AS complete,
      COUNT(*) AS total
    FROM mv_shinshi_repo_stats
    WHERE model_profile_count > 0
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shinshi_coverage_buckets`.execute(db);
}
