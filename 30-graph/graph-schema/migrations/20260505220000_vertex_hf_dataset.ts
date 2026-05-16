import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * adsk.gftd.ai — HuggingFace dataset ingest schema (Phase 1: text/code).
 *
 * Generic catalog so any HF org's text/code datasets can land in the
 * same two tables; ADSKAILab is the seed customer (CAD code +
 * narrative-planning + DSL eval). 3D / voxel binary blobs are out of
 * scope (Phase 2 → B2).
 *
 * Tables:
 *   vertex_hf_dataset         catalog row per HF dataset slug
 *   vertex_hf_dataset_record  per-row training record (one row = one
 *                             training sample, derived text in
 *                             text_for_training, original payload kept
 *                             as raw_json for downstream re-derivation)
 *
 * Streaming MV:
 *   mv_hf_dataset_text_for_training  joins record→catalog so the
 *                                    existing v_training_text VIEW
 *                                    can UNION ALL it cheaply (label
 *                                    column = `hf:{slug}`)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hf_dataset (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      slug varchar NOT NULL,
      org varchar,
      name varchar,
      modality varchar,
      license varchar,
      hf_url varchar,
      task_categories varchar,
      tags varchar,
      row_count_expected bigint,
      row_count_ingested bigint,
      last_synced_at varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_hf_dataset_record (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      slug varchar NOT NULL,
      record_id varchar NOT NULL,
      split varchar,
      lang varchar,
      text_for_training varchar,
      text_byte_size int,
      raw_json varchar,
      source_uri varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hf_dataset_text_for_training AS
      SELECT
        r.vertex_id                       AS vertex_id,
        'hf:' || r.slug                   AS label,
        r.text_for_training               AS content,
        r.lang                            AS lang,
        r.split                           AS split,
        CAST(r.created_date AS VARCHAR)   AS created_date
      FROM vertex_hf_dataset_record r
      WHERE r.sensitivity_ord = 0
        AND r.text_for_training IS NOT NULL
        AND r.text_for_training NOT LIKE 'signal:v1:%'
        AND LENGTH(r.text_for_training) >= 20;
  `.execute(db);

  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_hf_dataset TO root`.execute(db);
  await sql`GRANT SELECT, INSERT, UPDATE ON vertex_hf_dataset TO kaisya_app`.execute(db);
  await sql`GRANT SELECT, INSERT ON vertex_hf_dataset_record TO root`.execute(db);
  await sql`GRANT SELECT, INSERT ON vertex_hf_dataset_record TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`REVOKE ALL ON vertex_hf_dataset_record FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_hf_dataset_record FROM root`.execute(db);
  await sql`REVOKE ALL ON vertex_hf_dataset FROM kaisya_app`.execute(db);
  await sql`REVOKE ALL ON vertex_hf_dataset FROM root`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_hf_dataset_text_for_training`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_hf_dataset_record`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_hf_dataset`.execute(db);
}
