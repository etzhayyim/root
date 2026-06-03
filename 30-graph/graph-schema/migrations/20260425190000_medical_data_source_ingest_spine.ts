import { Kysely, sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * Medical data-source ingest spine.
 *
 * Raw source pages are persisted to B2 first; RisingWave stores only source
 * registry, raw asset lineage, runs, and cursors used by K8s ingesters.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_medical_data_source (
      vertex_id VARCHAR PRIMARY KEY,
      source_id VARCHAR NOT NULL,
      domain VARCHAR NOT NULL,
      target_collection VARCHAR NOT NULL,
      provider VARCHAR NOT NULL,
      label VARCHAR NOT NULL,
      display_name VARCHAR,
      source_kind VARCHAR NOT NULL,
      format VARCHAR NOT NULL,
      base_url TEXT NOT NULL,
      license VARCHAR,
      update_cadence VARCHAR,
      world_total_estimate BIGINT,
      b2_bucket VARCHAR NOT NULL,
      b2_prefix VARCHAR NOT NULL,
      status VARCHAR NOT NULL,
      priority BIGINT,
      metadata_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_medical_source_asset (
      vertex_id VARCHAR PRIMARY KEY,
      asset_id VARCHAR NOT NULL,
      source_id VARCHAR NOT NULL,
      run_id VARCHAR,
      asset_role VARCHAR NOT NULL,
      media_type VARCHAR NOT NULL,
      format VARCHAR NOT NULL,
      b2_bucket VARCHAR NOT NULL,
      b2_key TEXT NOT NULL,
      byte_size BIGINT,
      checksum_sha256 VARCHAR,
      source_url TEXT,
      record_count BIGINT,
      source_offset BIGINT,
      metadata_json TEXT,
      status VARCHAR NOT NULL,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_medical_ingest_cursor (
      vertex_id VARCHAR PRIMARY KEY,
      source_id VARCHAR NOT NULL,
      target_collection VARCHAR NOT NULL,
      cursor_json TEXT NOT NULL,
      source_offset BIGINT,
      last_run_id VARCHAR,
      last_asset_id VARCHAR,
      last_b2_key TEXT,
      last_success_at VARCHAR,
      status VARCHAR NOT NULL,
      error TEXT,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_medical_ingest_run (
      vertex_id VARCHAR PRIMARY KEY,
      run_id VARCHAR NOT NULL,
      source_id VARCHAR NOT NULL,
      target_collection VARCHAR NOT NULL,
      status VARCHAR NOT NULL,
      started_at VARCHAR NOT NULL,
      finished_at VARCHAR,
      records_fetched BIGINT,
      records_inserted BIGINT,
      source_offset BIGINT,
      next_offset BIGINT,
      b2_bucket VARCHAR,
      b2_key TEXT,
      b2_bytes BIGINT,
      checksum_sha256 VARCHAR,
      error TEXT,
      metadata_json TEXT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_medical_source_targets_collection (
      edge_id VARCHAR PRIMARY KEY,
      source_id VARCHAR NOT NULL,
      domain VARCHAR NOT NULL,
      target_collection VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      status VARCHAR NOT NULL,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_medical_data_source_source_id ON vertex_medical_data_source (source_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_medical_source_asset_source_offset ON vertex_medical_source_asset (source_id, source_offset)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_medical_ingest_cursor_source ON vertex_medical_ingest_cursor (source_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_medical_ingest_run_source_started ON vertex_medical_ingest_run (source_id, started_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_medical_source_targets_collection ON edge_medical_source_targets_collection (target_collection)`.execute(db);

  await sql`
    INSERT INTO vertex_medical_data_source (
      vertex_id, source_id, domain, target_collection, provider, label, display_name,
      source_kind, format, base_url, license, update_cadence, world_total_estimate,
      b2_bucket, b2_prefix, status, priority, metadata_json, created_at, updated_at
    )
    VALUES
      ('medical-data-source:cms-pos-clinical-labs', 'cms-pos-clinical-labs', 'iryo_shisetsu', 'com.etzhayyim.apps.iryo.shisetsu', 'cms', 'CMS POS Clinical Laboratories', 'CMS Provider of Services - Clinical Laboratories', 'cms-data-api', 'json-page', 'https://data.cms.gov/data-api/v1/dataset/d3eb38ac-d8e9-40d3-b7b7-6205d3d1dc16/data', 'US-PD', 'monthly', 676051, 'etzhayyim-nats', 'medical-sources/iryo-shisetsu', 'active', 100, '{"datasetId":"d3eb38ac-d8e9-40d3-b7b7-6205d3d1dc16"}', NOW()::VARCHAR, NOW()::VARCHAR),
      ('medical-data-source:cms-pos-iqies', 'cms-pos-iqies', 'iryo_shisetsu', 'com.etzhayyim.apps.iryo.shisetsu', 'cms', 'CMS POS IQIES', 'CMS Provider of Services - Internet Quality Improvement and Evaluation System', 'cms-data-api', 'json-page', 'https://data.cms.gov/data-api/v1/dataset/086e48c4-87a6-4be1-8823-29e8da8f225b/data', 'US-PD', 'monthly', 77283, 'etzhayyim-nats', 'medical-sources/iryo-shisetsu', 'active', 90, '{"datasetId":"086e48c4-87a6-4be1-8823-29e8da8f225b"}', NOW()::VARCHAR, NOW()::VARCHAR),
      ('medical-data-source:cms-pos-qies', 'cms-pos-qies', 'iryo_shisetsu', 'com.etzhayyim.apps.iryo.shisetsu', 'cms', 'CMS POS QIES', 'CMS Provider of Services - Quality Improvement and Evaluation System', 'cms-data-api', 'json-page', 'https://data.cms.gov/data-api/v1/dataset/8ba0f9b4-9493-4aa0-9f82-44ea9468d1b5/data', 'US-PD', 'monthly', 44429, 'etzhayyim-nats', 'medical-sources/iryo-shisetsu', 'active', 80, '{"datasetId":"8ba0f9b4-9493-4aa0-9f82-44ea9468d1b5"}', NOW()::VARCHAR, NOW()::VARCHAR)
  `.execute(db);

  await sql`
    INSERT INTO edge_medical_source_targets_collection (
      edge_id, source_id, domain, target_collection, relation_kind, status, created_at, updated_at
    )
    VALUES
      ('medical-source-target:cms-pos-clinical-labs:iryo-shisetsu', 'cms-pos-clinical-labs', 'iryo_shisetsu', 'com.etzhayyim.apps.iryo.shisetsu', 'fillsCoverageGap', 'active', NOW()::VARCHAR, NOW()::VARCHAR),
      ('medical-source-target:cms-pos-iqies:iryo-shisetsu', 'cms-pos-iqies', 'iryo_shisetsu', 'com.etzhayyim.apps.iryo.shisetsu', 'fillsCoverageGap', 'active', NOW()::VARCHAR, NOW()::VARCHAR),
      ('medical-source-target:cms-pos-qies:iryo-shisetsu', 'cms-pos-qies', 'iryo_shisetsu', 'com.etzhayyim.apps.iryo.shisetsu', 'fillsCoverageGap', 'active', NOW()::VARCHAR, NOW()::VARCHAR)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_medical_source_targets_collection`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_medical_ingest_run_source_started`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_medical_ingest_cursor_source`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_medical_source_asset_source_offset`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_medical_data_source_source_id`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_medical_source_targets_collection`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_medical_ingest_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_medical_ingest_cursor`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_medical_source_asset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_medical_data_source`.execute(db);
}
