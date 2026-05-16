import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Schema optimization follow-up from the 2026-04-26 live audit.
 *
 * Scope:
 * - add secondary indexes for small / bounded tables and LEI projection tables;
 * - remove the stale maps `mv_` VIEW alias now that the canonical
 *   `view_maps_coverage_gap_ranked` exists;
 * - add a canonical `view_world_coverage_live` alias while keeping the legacy
 *   `mv_world_coverage_live` name for current readers.
 *
 * Do not add `vertex_legal_entity(lei)` here. That table is 100M+ rows in live
 * RisingWave and must be submitted through the serialized heavy DDL queue with
 * BACKGROUND_DDL and rw_ddl_progress monitoring.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // maps coverage frontier: small table, used by advanceCoverage filters.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_coverage_target_source_label
      ON vertex_maps_coverage_target (source_did, label)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_coverage_target_last_fetched
      ON vertex_maps_coverage_target (last_fetched_at)
  `.execute(db);

  // contracts projection: resolver fallback and backfill reconciliation.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_contracts_org_source_record_id
      ON vertex_contracts_organization (source_record_id)
  `.execute(db);

  // Open LEI tables: bounded projection path for LEI lookups and ownership graph.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_open_lei_entity_lei
      ON vertex_open_lei_entity (lei)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_open_lei_entity_country_status
      ON vertex_open_lei_entity (country, status)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_open_lei_ownership_parent
      ON vertex_open_lei_ownership (parent_lei)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_open_lei_ownership_child
      ON vertex_open_lei_ownership (child_lei)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_open_lei_ownership_pair_src
      ON edge_open_lei_ownership_pair (src_vid)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_open_lei_ownership_pair_dst
      ON edge_open_lei_ownership_pair (dst_vid)
  `.execute(db);

  // LEI-bearing domain tables observed in the live audit.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_ads_operated_by_lei
      ON edge_ads_operated_by (lei)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_hospitality_lei_bridge_lei
      ON edge_hospitality_lei_bridge (lei)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_hc_sp_application_lei
      ON vertex_hc_sp_application (lei)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_open_carrier_fleet_carrier_lei
      ON vertex_open_carrier_fleet_carrier (lei)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_real_estate_party_lei
      ON vertex_real_estate_party (lei)
  `.execute(db);

  // Canonical view names. `mv_maps_coverage_gap_ranked` is a stale VIEW alias.
  await sql`DROP VIEW IF EXISTS mv_maps_coverage_gap_ranked`.execute(db);
  await sql`DROP VIEW IF EXISTS view_world_coverage_live`.execute(db);
  await sql`
    CREATE VIEW view_world_coverage_live AS
    SELECT * FROM mv_world_coverage_live
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_world_coverage_live`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_real_estate_party_lei`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_open_carrier_fleet_carrier_lei`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_hc_sp_application_lei`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_hospitality_lei_bridge_lei`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_ads_operated_by_lei`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_open_lei_ownership_pair_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_open_lei_ownership_pair_src`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_open_lei_ownership_child`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_open_lei_ownership_parent`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_open_lei_entity_country_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_open_lei_entity_lei`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_contracts_org_source_record_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_maps_coverage_target_last_fetched`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_maps_coverage_target_source_label`.execute(db);
}
