import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * gyosei legal source graph spine.
 *
 * - vertex_gyosei_source_blob     : archived legal / agency source snapshot metadata
 * - edge_gyosei_case_source       : gyosei caseId -> source snapshot references
 * - edge_gyosei_precedent_source  : gyosei precedent memo -> source snapshot references
 */
// tier: C
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_gyosei_source_blob (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      owner_did VARCHAR,
      source_id VARCHAR,
      category VARCHAR,
      mode VARCHAR,
      source_url VARCHAR,
      source_title VARCHAR,
      source_issuer VARCHAR,
      source_date DATE,
      captured_at TIMESTAMPTZ,
      previous_captured_at TIMESTAMPTZ,
      status VARCHAR,
      source_sha256 VARCHAR,
      source_bytes BIGINT,
      b2_bucket VARCHAR,
      b2_endpoint VARCHAR,
      b2_prefix VARCHAR,
      b2_key_original VARCHAR,
      b2_key_derivative VARCHAR,
      b2_key_thumbnail VARCHAR,
      b2_key_metadata VARCHAR,
      page_count INTEGER,
      width INTEGER,
      height INTEGER,
      created_at TIMESTAMPTZ,
      updated_at TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_gyosei_case_source (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      owner_did VARCHAR,
      case_id VARCHAR,
      source_vertex_id VARCHAR,
      relation VARCHAR,
      note VARCHAR,
      created_at TIMESTAMPTZ
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_gyosei_precedent_source (
      edge_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      owner_did VARCHAR,
      memo_id VARCHAR,
      case_id VARCHAR,
      source_vertex_id VARCHAR,
      relation VARCHAR,
      note VARCHAR,
      created_at TIMESTAMPTZ
    )
  `.execute(db);

  // RisingWave does not implement CREATE UNIQUE INDEX (feature not yet
  // implemented per sql_parser). Downgrade to a plain CREATE INDEX; the
  // uniqueness invariant is enforced in the ingest path (callers of the
  // gyosei source capture) instead. Track upgrade in deps.toml
  // [[migrations]] once RW ships unique-index support.
  await sql`CREATE INDEX IF NOT EXISTS idx_gyosei_source_blob_source_id ON vertex_gyosei_source_blob (source_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_gyosei_source_blob_status ON vertex_gyosei_source_blob (status, captured_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_gyosei_source_blob_category ON vertex_gyosei_source_blob (category, source_issuer)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_gyosei_case_source_case_id ON edge_gyosei_case_source (case_id, relation)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_gyosei_case_source_source_vertex ON edge_gyosei_case_source (source_vertex_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_gyosei_precedent_source_memo_id ON edge_gyosei_precedent_source (memo_id, relation)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_gyosei_precedent_source_case_id ON edge_gyosei_precedent_source (case_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_gyosei_precedent_source_source_vertex ON edge_gyosei_precedent_source (source_vertex_id)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_gyosei_precedent_source_source_vertex`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gyosei_precedent_source_case_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gyosei_precedent_source_memo_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gyosei_case_source_source_vertex`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gyosei_case_source_case_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gyosei_source_blob_category`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gyosei_source_blob_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_gyosei_source_blob_source_id`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gyosei_precedent_source`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_gyosei_case_source`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_gyosei_source_blob`.execute(db);
}
