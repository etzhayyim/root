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
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_status`)} ON ${sql.table(table)} (status)`.execute(db);
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
  await baseVertex(db, "vertex_kami_eng_eda_schematic");
  await sql`ALTER TABLE vertex_kami_eng_eda_schematic ADD COLUMN IF NOT EXISTS name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kami_eng_eda_schematic ADD COLUMN IF NOT EXISTS sheet_size VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kami_eng_eda_schematic ADD COLUMN IF NOT EXISTS grid_spacing VARCHAR`.execute(db);

  await baseVertex(db, "vertex_kami_eng_cad_model");
  await sql`ALTER TABLE vertex_kami_eng_cad_model ADD COLUMN IF NOT EXISTS name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kami_eng_cad_model ADD COLUMN IF NOT EXISTS model_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kami_eng_cad_model ADD COLUMN IF NOT EXISTS unit VARCHAR`.execute(db);

  await baseVertex(db, "vertex_kami_eng_cad_feature");
  await sql`ALTER TABLE vertex_kami_eng_cad_feature ADD COLUMN IF NOT EXISTS model_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kami_eng_cad_feature ADD COLUMN IF NOT EXISTS feature_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kami_eng_cad_feature ADD COLUMN IF NOT EXISTS feature_order DOUBLE PRECISION`.execute(db);

  await baseVertex(db, "vertex_kami_eng_cam_job");
  await sql`ALTER TABLE vertex_kami_eng_cam_job ADD COLUMN IF NOT EXISTS model_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kami_eng_cam_job ADD COLUMN IF NOT EXISTS machine VARCHAR`.execute(db);

  await baseVertex(db, "vertex_kami_eng_rtl_module_ref");
  await sql`ALTER TABLE vertex_kami_eng_rtl_module_ref ADD COLUMN IF NOT EXISTS module_id VARCHAR`.execute(db);

  await baseVertex(db, "vertex_kami_eng_rtl_simulation");
  await sql`ALTER TABLE vertex_kami_eng_rtl_simulation ADD COLUMN IF NOT EXISTS module_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kami_eng_rtl_simulation ADD COLUMN IF NOT EXISTS duration VARCHAR`.execute(db);

  await baseVertex(db, "vertex_kami_eng_cae_analysis");
  await sql`ALTER TABLE vertex_kami_eng_cae_analysis ADD COLUMN IF NOT EXISTS model_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_kami_eng_cae_analysis ADD COLUMN IF NOT EXISTS analysis_type VARCHAR`.execute(db);

  await baseEdge(db, "edge_kami_eng_cad_model_feature");
  await baseEdge(db, "edge_kami_eng_cad_model_cam_job");
  await baseEdge(db, "edge_kami_eng_rtl_module_simulation");
  await baseEdge(db, "edge_kami_eng_cad_model_cae_analysis");

  await sql`CREATE INDEX IF NOT EXISTS idx_kami_eng_feature_model ON vertex_kami_eng_cad_feature (model_id, feature_order)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kami_eng_cam_model ON vertex_kami_eng_cam_job (model_id, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kami_eng_rtl_sim_module ON vertex_kami_eng_rtl_simulation (module_id, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kami_eng_cae_model ON vertex_kami_eng_cae_analysis (model_id, analysis_type, status)`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kami_eng_workbench_counts`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_kami_eng_workbench_counts AS
    SELECT 'eda_schematic' AS workbench_kind, status, count(*)::BIGINT AS record_count FROM vertex_kami_eng_eda_schematic GROUP BY status
    UNION ALL
    SELECT 'cad_model', status, count(*)::BIGINT FROM vertex_kami_eng_cad_model GROUP BY status
    UNION ALL
    SELECT 'cad_feature', status, count(*)::BIGINT FROM vertex_kami_eng_cad_feature GROUP BY status
    UNION ALL
    SELECT 'cam_job', status, count(*)::BIGINT FROM vertex_kami_eng_cam_job GROUP BY status
    UNION ALL
    SELECT 'rtl_simulation', status, count(*)::BIGINT FROM vertex_kami_eng_rtl_simulation GROUP BY status
    UNION ALL
    SELECT 'cae_analysis', status, count(*)::BIGINT FROM vertex_kami_eng_cae_analysis GROUP BY status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kami_eng_workbench_counts`.execute(db);
  for (const table of [
    "edge_kami_eng_cad_model_cae_analysis",
    "edge_kami_eng_rtl_module_simulation",
    "edge_kami_eng_cad_model_cam_job",
    "edge_kami_eng_cad_model_feature",
    "vertex_kami_eng_cae_analysis",
    "vertex_kami_eng_rtl_simulation",
    "vertex_kami_eng_rtl_module_ref",
    "vertex_kami_eng_cam_job",
    "vertex_kami_eng_cad_feature",
    "vertex_kami_eng_cad_model",
    "vertex_kami_eng_eda_schematic",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
}
