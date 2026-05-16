import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Phase 0 of the 24h coverage acceleration plan — surface the existing
 * 190M+ legal_entity + 828K accommodation rows as a unified spatial query
 * surface, without re-crawling them.
 *
 * Plain VIEW (not MATERIALIZED VIEW) per CLAUDE.md MV memory guardrails:
 *   - vertex_legal_entity at 190M rows would create > 50 GiB hash agg state
 *     in any MV that touches it; compute pod limit is 24 GiB.
 *   - VIEWs are query-time only — zero streaming state, zero backfill cost.
 *
 * Use cases this enables:
 *   - cmdGetCoverageStatus + frontier dashboards can include LE/hotel rows
 *     without writing them to vertex_spatial again (avoids 190M dup writes)
 *   - downstream MV (`mv_maps_collected_per_source_label_canonical`) can
 *     be re-built later to include `external_existing` source DIDs without
 *     scanning legal_entity directly.
 *
 * Also: deactivate the now-redundant `registry:gleif` coverage target —
 * we already have full GLEIF in vertex_legal_entity (190M LEI records),
 * the dispatch was duplicating effort at 60 rows / 8h.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_maps_spatial_unified`.execute(db);
  await sql`
    CREATE VIEW view_maps_spatial_unified AS
    SELECT
      vertex_id,
      name,
      label,
      lat,
      lng AS lon,
      source_did,
      'vertex_spatial' AS origin
    FROM vertex_spatial
    UNION ALL
    SELECT
      vertex_id,
      name,
      'LegalEntity'::varchar AS label,
      NULL::real AS lat,
      NULL::real AS lon,
      'did:web:legal-entity.gftd.ai'::varchar AS source_did,
      'vertex_legal_entity'::varchar AS origin
    FROM vertex_legal_entity
    UNION ALL
    SELECT
      vertex_id,
      name,
      'Hotel'::varchar AS label,
      lat,
      lon,
      'did:web:hospitality.gftd.ai'::varchar AS source_did,
      'vertex_accommodation'::varchar AS origin
    FROM vertex_accommodation
  `.execute(db);

  // Mark GLEIF as superseded — set priority_weight to 0 so it never
  // wins an advance pick. Don't delete (keeps history); operator can
  // re-enable by raising priority if needed.
  await sql`
    UPDATE vertex_maps_coverage_target
       SET priority_weight = 0.0
     WHERE source_did = 'did:web:maps.gftd.ai:registry:gleif'
  `.execute(db);

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_maps_spatial_unified`.execute(db);
  await sql`
    UPDATE vertex_maps_coverage_target
       SET priority_weight = 0.6
     WHERE source_did = 'did:web:maps.gftd.ai:registry:gleif'
  `.execute(db);
}
