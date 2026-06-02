import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * RisingWave streaming MV — live collected_count per (source_did, label)
 * for the maps coverage frontier.
 *
 * Backs `com.etzhayyim.apps.maps.refreshCoverageStats` XRPC which writes the MV
 * rows back into `vertex_maps_coverage_target.collected_count`, closing
 * the feedback loop started by the `advanceCoverage` frontier.
 *
 * MV memory safety (per `30-graph/graph-schema/CLAUDE.md §MV Memory Safety`):
 *   - GROUP BY is (source_did, label) — both are low-cardinality promoted
 *     columns on vertex_spatial. Expected group count: at most a few
 *     hundred (~22 source DIDs × ~51 labels = 1,122 theoretical, in
 *     practice ~50 live combinations). Hash-agg state well under 1 MiB.
 *   - No MAX(varchar) over wide columns — COUNT(*) only. No OOM risk.
 *   - Backfill over vertex_spatial is bounded (the table is small — graph
 *     worker writes ~100/s, not webpage scale). No BACKGROUND DDL needed.
 *
 * Does NOT filter `source_did IS NOT NULL` in a WHERE clause because the
 * graph-schema compat rule says: streaming MVs with WHERE clauses on
 * nullable promoted columns force RW to re-evaluate the predicate on
 * every row; GROUP BY is cheaper. Null-source rows are naturally
 * aggregated under a `(null, null)` group which the refresh handler
 * ignores.
 *
 * Staleness: RisingWave streaming MVs update on barrier cycle
 * (`barrier_interval_ms = 5000` system-wide → ~5s freshness). Ample for
 * a 15-minute refresh cadence.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_maps_collected_per_source_label`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_maps_collected_per_source_label AS
    SELECT
      source_did,
      label,
      COUNT(*)::bigint AS collected_count
    FROM vertex_spatial
    GROUP BY source_did, label
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_maps_collected_per_source_label`.execute(db);
}
