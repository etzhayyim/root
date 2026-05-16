import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * isbn.gftd.ai Phase 2 — image + body extension.
 *
 *  vertex_isbn_book_image     表紙 + 各ページのスキャン画像 (B2 content-addressed by CIDv1)
 *  edge_isbn_book_image       book → image (role: cover / page / figure / illustration)
 *
 * Existing vertex_isbn_book_fulltext + vertex_isbn_book_chapter cover
 * the body text path. This migration adds the image surface.
 *
 * Image rows are content-addressed: `b2_key = images/{sha256_hex}` so
 * the same image (same bytes) referenced from multiple sources is
 * de-duplicated automatically. mime_type / width / height / byte_size
 * are captured at ingest time.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_isbn_book_image (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      isbn13 varchar NOT NULL,
      role varchar NOT NULL,
      page_index int,
      sha256 varchar NOT NULL,
      cid_v1 varchar,
      b2_bucket varchar,
      b2_key varchar,
      source varchar NOT NULL,
      source_url varchar,
      mime_type varchar,
      width_px int,
      height_px int,
      byte_size bigint,
      license varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_isbn_book_image (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_isbn_book_image_coverage AS
      SELECT
        source,
        role,
        COUNT(*) AS image_count,
        SUM(byte_size) AS total_bytes
      FROM vertex_isbn_book_image
      WHERE status='active'
      GROUP BY source, role;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_isbn_book_image_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_isbn_book_image`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_isbn_book_image`.execute(db);
}
