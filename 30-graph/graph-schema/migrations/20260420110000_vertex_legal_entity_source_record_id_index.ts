import { Kysely, sql } from 'kysely';

/**
 * Index on `vertex_legal_entity.source_record_id`.
 *
 * Blocker incident (2026-04-19): yabai phishing-infra tool emitted 5-6 parallel
 *
 *   DELETE FROM vertex_legal_entity WHERE source_record_id IN (...);
 *
 * without an index on `source_record_id`. vertex_legal_entity has 123.5M rows
 * (bulk-stream-ingest-vertex-legal-entity migration), so each DELETE was a
 * full scan reading the entire Hummock LSM state from Linode Object Storage.
 * With the bucket-wide ~75 rps quota, 5 concurrent scans instantly saturated
 * S3 → 503 SlowDown storm → 63-min stuck sessions → every other query queued
 * behind.
 *
 * With this index the same DELETE becomes O(log N) point-lookup.
 *
 * APPLY NOTE: 123.5M rows. Must be applied under BACKGROUND DDL with
 * locality_backfill + no other concurrent heavy backfills:
 *
 *   -- preflight: wait until `SELECT COUNT(*)` on the DB works without S3
 *   -- SlowDown (i.e. the yabai DELETEs have cleared or been aborted).
 *   SET enable_locality_backfill = true;
 *   SET background_ddl = true;
 *   -- run this migration
 *   SET background_ddl = false;
 *   -- monitor: SELECT * FROM rw_catalog.rw_ddl_progress;
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_legal_entity_source_record_id ON vertex_legal_entity (source_record_id)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_legal_entity_source_record_id`.execute(db);
}
