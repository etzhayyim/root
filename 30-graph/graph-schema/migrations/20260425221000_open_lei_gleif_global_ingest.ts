import { Kysely, sql } from 'kysely';

/**
 * GLEIF global LEI ingest control plane.
 *
 * Official source design:
 *   - Level 1 LEI-CDF v3.1: legal entity reference data
 *   - Level 2 RR-CDF v2.1: direct/ultimate parent relationships
 *   - Level 2 Reporting Exceptions v2.1
 *
 * Raw daily files are content-addressed in blob storage; graph tables keep
 * manifest, shard, exception, EMS matching, and lineage metadata.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_lei_gleif_file (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      file_id VARCHAR,
      dataset_kind VARCHAR,
      cdf_version VARCHAR,
      as_of_date VARCHAR,
      download_url VARCHAR,
      api_endpoint VARCHAR,
      blob_key VARCHAR,
      sha256 VARCHAR,
      compressed_bytes BIGINT,
      record_count BIGINT,
      source_status VARCHAR,
      fetched_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_lei_gleif_file_dataset_date ON vertex_open_lei_gleif_file (dataset_kind, as_of_date)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_lei_gleif_file_sha ON vertex_open_lei_gleif_file (sha256)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_lei_gleif_shard (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      shard_id VARCHAR,
      file_id VARCHAR,
      dataset_kind VARCHAR,
      as_of_date VARCHAR,
      shard_no BIGINT,
      shard_count BIGINT,
      request_url VARCHAR,
      next_url VARCHAR,
      start_offset BIGINT,
      end_offset BIGINT,
      records_read BIGINT,
      records_written BIGINT,
      records_skipped BIGINT,
      error_count BIGINT,
      shard_status VARCHAR,
      started_at VARCHAR,
      finished_at VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_lei_gleif_shard_file ON vertex_open_lei_gleif_shard (file_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_lei_gleif_shard_status ON vertex_open_lei_gleif_shard (dataset_kind, shard_status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_lei_reporting_exception (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      lei VARCHAR NOT NULL,
      exception_category VARCHAR,
      exception_reason VARCHAR,
      parent_type VARCHAR,
      reference_period_start VARCHAR,
      reference_period_end VARCHAR,
      source_file_id VARCHAR,
      as_of_date VARCHAR,
      status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_lei_reporting_exception_lei ON vertex_open_lei_reporting_exception (lei)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_open_lei_reporting_exception_reason ON vertex_open_lei_reporting_exception (exception_category, exception_reason)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_open_lei_entity_source_file (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      lei VARCHAR,
      file_id VARCHAR,
      dataset_kind VARCHAR,
      as_of_date VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_open_lei_source_entity ON edge_open_lei_entity_source_file (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_open_lei_source_file ON edge_open_lei_entity_source_file (dst_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_open_lei_entity_ems_candidate (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      lei VARCHAR,
      ems_company_id VARCHAR,
      match_score DOUBLE PRECISION,
      matched_keywords_json VARCHAR,
      next_evidence_json VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_open_lei_ems_entity ON edge_open_lei_entity_ems_candidate (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_open_lei_ems_company ON edge_open_lei_entity_ems_candidate (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_open_lei_ems_score ON edge_open_lei_entity_ems_candidate (match_score)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_lei_gleif_ingest_status AS
      SELECT
        f.dataset_kind,
        f.as_of_date,
        COUNT(DISTINCT f.vertex_id) AS file_count,
        SUM(f.record_count) AS expected_record_count,
        COUNT(DISTINCT s.vertex_id) AS shard_count,
        SUM(s.records_read) AS records_read,
        SUM(s.records_written) AS records_written,
        SUM(s.error_count) AS error_count,
        MAX(f._seq) AS _seq
      FROM vertex_open_lei_gleif_file f
      LEFT JOIN vertex_open_lei_gleif_shard s ON s.file_id = f.file_id
      GROUP BY f.dataset_kind, f.as_of_date
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_lei_ems_candidates AS
      SELECT
        e.lei,
        e.legal_name,
        e.country,
        e.registration_status,
        c.ems_company_id,
        c.match_score,
        c.matched_keywords_json,
        c.next_evidence_json,
        MAX(c._seq) AS _seq
      FROM edge_open_lei_entity_ems_candidate c
      JOIN vertex_open_lei_entity e ON e.vertex_id = c.src_vid
      GROUP BY e.lei, e.legal_name, e.country, e.registration_status,
               c.ems_company_id, c.match_score, c.matched_keywords_json,
               c.next_evidence_json
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_lei_ems_candidates`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_lei_gleif_ingest_status`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_lei_entity_ems_candidate`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_lei_entity_source_file`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_lei_reporting_exception`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_lei_gleif_shard`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_lei_gleif_file`.execute(db);
}
