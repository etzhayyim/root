import type { Kysely } from "kysely";
import { sql } from "kysely";

async function baseVertex(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      record_id VARCHAR,
      owner_did VARCHAR,
      label VARCHAR,
      status VARCHAR,
      stream_id VARCHAR,
      agent_did VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_record_id`)} ON ${sql.table(table)} (record_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_stream`)} ON ${sql.table(table)} (stream_id, created_at)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  // contentengine — Personalized Content Engine (ADR-2605072000)
  // No individual PII — cohort-level personalization only (sensitivity_ord=0, ADR-0018)

  // Cohort content profiles (no PII — cohort aggregate)
  await baseVertex(db, "vertex_contentengine_cohort_profile");
  await sql`ALTER TABLE vertex_contentengine_cohort_profile ADD COLUMN IF NOT EXISTS cohort_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_cohort_profile ADD COLUMN IF NOT EXISTS interests TEXT`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_cohort_profile ADD COLUMN IF NOT EXISTS reading_level VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_cohort_profile ADD COLUMN IF NOT EXISTS preferred_formats TEXT`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_cohort_profile ADD COLUMN IF NOT EXISTS industry_context VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cten_cohort_name ON vertex_contentengine_cohort_profile (cohort_name)`.execute(db);

  // Generated content pieces
  await baseVertex(db, "vertex_contentengine_content");
  await sql`ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS content_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS cohort_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS content_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS topic VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS tone VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS title VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS body TEXT`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS relevance_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS include_sponsor_slot BOOLEAN`.execute(db);
  await sql`ALTER TABLE vertex_contentengine_content ADD COLUMN IF NOT EXISTS ad_campaign_id VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cten_content_id ON vertex_contentengine_content (content_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cten_content_cohort ON vertex_contentengine_content (cohort_name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cten_content_type ON vertex_contentengine_content (content_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cten_content_status ON vertex_contentengine_content (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_cten_content_score ON vertex_contentengine_content (quality_score)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_contentengine_content`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_contentengine_cohort_profile`.execute(db);
}
