import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * NDL image-first ingest schema.
 *
 * Scope:
 *   - NDL Digital Collections (ndl-dl)
 *   - NDL Digital Collections (Online Publications) (ndl-dl-online)
 *   - NDL Digital Collections (Open Data) (ndl-dl-open)
 *
 * The durable body-of-record for page images is B2/WebP. RisingWave keeps
 * catalog metadata, page manifests, image hashes, OCR text, and run/cursor
 * state so downstream graph/training views can read text without fetching B2.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ndl_digital_item (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      pid varchar NOT NULL,
      provider_id varchar NOT NULL,
      repository_no varchar,
      title varchar,
      creator varchar,
      issued varchar,
      language varchar,
      material_type varchar,
      access_scope varchar,
      content_license varchar,
      source_url varchar,
      manifest_url varchar,
      record_xml_sha256 varchar,
      status varchar NOT NULL,
      discovered_at varchar,
      updated_at varchar,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ndl_digital_page (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      pid varchar NOT NULL,
      provider_id varchar NOT NULL,
      page_index int NOT NULL,
      source_image_url varchar NOT NULL,
      webp_sha256 varchar,
      webp_cid_v1 varchar,
      webp_b2_bucket varchar,
      webp_b2_key varchar,
      webp_byte_size bigint,
      width_px int,
      height_px int,
      ocr_status varchar NOT NULL,
      status varchar NOT NULL,
      created_at varchar,
      updated_at varchar,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ndl_ocr_text (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      pid varchar NOT NULL,
      page_index int NOT NULL,
      ocr_engine varchar NOT NULL,
      ocr_model varchar,
      ocr_text varchar,
      ocr_json varchar,
      warnings varchar,
      text_sha256 varchar,
      text_byte_size bigint,
      status varchar NOT NULL,
      created_at varchar,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ndl_ingest_cursor (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      provider_id varchar NOT NULL,
      query varchar NOT NULL,
      next_start_record bigint NOT NULL,
      last_run_id varchar,
      status varchar NOT NULL,
      updated_at varchar,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ndl_ingest_run (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      run_id varchar NOT NULL,
      provider_id varchar NOT NULL,
      query varchar NOT NULL,
      start_record bigint,
      max_records int,
      max_items int,
      max_pages_per_item int,
      items_seen int,
      items_inserted int,
      pages_inserted int,
      pages_processed int,
      ocr_inserted int,
      bytes_webp bigint,
      status varchar NOT NULL,
      error varchar,
      started_at varchar,
      finished_at varchar,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_ndl_image_ocr_coverage AS
      SELECT
        i.provider_id,
        COUNT(DISTINCT i.pid) AS item_count,
        COUNT(p.vertex_id) AS page_count,
        COUNT(o.vertex_id) AS ocr_page_count,
        SUM(p.webp_byte_size) AS webp_bytes
      FROM vertex_ndl_digital_item i
      LEFT JOIN vertex_ndl_digital_page p ON p.pid = i.pid
      LEFT JOIN vertex_ndl_ocr_text o ON o.pid = p.pid AND o.page_index = p.page_index
      WHERE i.status = 'active'
      GROUP BY i.provider_id;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_ndl_image_ocr_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ndl_ingest_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ndl_ingest_cursor`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ndl_ocr_text`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ndl_digital_page`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ndl_digital_item`.execute(db);
}
