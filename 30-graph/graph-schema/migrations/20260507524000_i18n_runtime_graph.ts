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
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_record_id`)} ON ${sql.table(table)} (record_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_created`)} ON ${sql.table(table)} (created_at)`.execute(db);
}

async function baseEdge(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await baseVertex(db, "vertex_i18n_project");
  await sql`ALTER TABLE vertex_i18n_project ADD COLUMN IF NOT EXISTS project_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_i18n_project ADD COLUMN IF NOT EXISTS project_path TEXT`.execute(db);
  await sql`ALTER TABLE vertex_i18n_project ADD COLUMN IF NOT EXISTS total_keys BIGINT`.execute(db);

  await baseVertex(db, "vertex_i18n_project_translation");
  await sql`ALTER TABLE vertex_i18n_project_translation ADD COLUMN IF NOT EXISTS project_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_i18n_project_translation ADD COLUMN IF NOT EXISTS lang VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_i18n_project_translation ADD COLUMN IF NOT EXISTS message_count BIGINT`.execute(db);

  await baseVertex(db, "vertex_i18n_translation_memory");
  await sql`ALTER TABLE vertex_i18n_translation_memory ADD COLUMN IF NOT EXISTS source_hash VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_i18n_translation_memory ADD COLUMN IF NOT EXISTS source_lang VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_i18n_translation_memory ADD COLUMN IF NOT EXISTS target_lang VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_i18n_translation_memory ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_i18n_translation_memory ADD COLUMN IF NOT EXISTS source VARCHAR`.execute(db);

  await baseVertex(db, "vertex_i18n_text_node");
  await sql`ALTER TABLE vertex_i18n_text_node ADD COLUMN IF NOT EXISTS node_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_i18n_text_node ADD COLUMN IF NOT EXISTS node_kind VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_i18n_text_node ADD COLUMN IF NOT EXISTS lang VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_i18n_text_node ADD COLUMN IF NOT EXISTS text_value TEXT`.execute(db);

  await baseVertex(db, "vertex_i18n_credit_job");
  await sql`ALTER TABLE vertex_i18n_credit_job ADD COLUMN IF NOT EXISTS job_kind VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_i18n_credit_job ADD COLUMN IF NOT EXISTS credit_estimate BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_i18n_credit_job ADD COLUMN IF NOT EXISTS workload_units BIGINT`.execute(db);

  await baseEdge(db, "edge_i18n_project_translation");
  await baseEdge(db, "edge_i18n_translation_text");
  await baseEdge(db, "edge_i18n_text_language");

  await sql`CREATE INDEX IF NOT EXISTS idx_i18n_project_id ON vertex_i18n_project (project_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_i18n_project_translation_project_lang ON vertex_i18n_project_translation (project_id, lang)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_i18n_tm_lookup ON vertex_i18n_translation_memory (source_hash, target_lang, updated_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_i18n_text_lang ON vertex_i18n_text_node (lang, node_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_i18n_credit_job_status ON vertex_i18n_credit_job (status, job_kind)`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_i18n_project_translation_coverage`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_i18n_project_translation_coverage AS
    SELECT p.project_id, p.total_keys, t.lang, t.message_count
    FROM vertex_i18n_project p
    LEFT JOIN vertex_i18n_project_translation t ON t.project_id = p.project_id
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_i18n_tm_quality_by_lang`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_i18n_tm_quality_by_lang AS
    SELECT source_lang, target_lang, source, count(*)::BIGINT AS entry_count, avg(quality_score) AS avg_quality_score
    FROM vertex_i18n_translation_memory
    GROUP BY source_lang, target_lang, source
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_i18n_tm_quality_by_lang`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_i18n_project_translation_coverage`.execute(db);
  for (const table of [
    "edge_i18n_text_language",
    "edge_i18n_translation_text",
    "edge_i18n_project_translation",
    "vertex_i18n_credit_job",
    "vertex_i18n_text_node",
    "vertex_i18n_translation_memory",
    "vertex_i18n_project_translation",
    "vertex_i18n_project",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
}
