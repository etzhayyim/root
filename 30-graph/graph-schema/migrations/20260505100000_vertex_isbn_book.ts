import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * isbn.gftd.ai Phase 1 — global library digital ingest schema
 * (ADR-0056 BPMN-as-actor, ISBN registry + PD fulltext).
 *
 * Tables:
 *   vertex_isbn_book          ISBN-13 master + bibliographic metadata
 *   vertex_isbn_publisher     Publisher prefix registry
 *   vertex_isbn_book_chapter  Chapter-level fulltext (chunked)
 *   vertex_isbn_book_fulltext Fulltext metadata (source, license, byte_size, b2_key)
 *   vertex_isbn_book_copyright Copyright status (pd / cc0 / cc_by / cc_by_sa / © )
 *   edge_isbn_book_publisher  book → publisher
 *
 * Streaming MV:
 *   mv_isbn_book_by_language     book counts per language + PD share
 *   mv_isbn_book_by_jurisdiction PD coverage per jurisdiction
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_isbn_book (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      isbn13 varchar NOT NULL, isbn10 varchar,
      title varchar, subtitle varchar,
      authors varchar, publisher_prefix varchar,
      publication_year int, language varchar,
      registration_group varchar, page_count int,
      bisac_subjects varchar, source varchar,
      source_url varchar, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_isbn_publisher (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      prefix varchar NOT NULL, name varchar,
      registration_group varchar, country varchar,
      website varchar, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_isbn_book_chapter (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      isbn13 varchar NOT NULL, chapter_number int NOT NULL,
      title varchar, text varchar,
      token_count int, byte_size int,
      language varchar, b2_key varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_isbn_book_fulltext (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      isbn13 varchar NOT NULL, source varchar NOT NULL,
      source_url varchar, format varchar,
      total_chapters int, total_tokens bigint,
      total_bytes bigint, b2_bucket varchar,
      b2_prefix varchar, license varchar,
      sha256 varchar, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_isbn_book_copyright (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      isbn13 varchar NOT NULL, status varchar NOT NULL,
      author_death_year int, jurisdiction varchar,
      pd_year int, license_url varchar,
      evidence_url varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_isbn_book_publisher (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_isbn_book_by_language AS
      SELECT
        b.language,
        COUNT(*) AS book_count,
        COUNT(c.isbn13) AS pd_count
      FROM vertex_isbn_book b
      LEFT JOIN vertex_isbn_book_copyright c
        ON c.isbn13 = b.isbn13 AND c.status IN ('pd','cc0','cc_by','cc_by_sa')
      WHERE b.status='active'
      GROUP BY b.language;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_isbn_book_by_jurisdiction AS
      SELECT
        c.jurisdiction,
        c.status AS copyright_status,
        COUNT(*) AS book_count
      FROM vertex_isbn_book_copyright c
      WHERE c.jurisdiction IS NOT NULL
      GROUP BY c.jurisdiction, c.status;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_isbn_book_by_jurisdiction`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_isbn_book_by_language`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_isbn_book_publisher`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_isbn_book_copyright`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_isbn_book_fulltext`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_isbn_book_chapter`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_isbn_publisher`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_isbn_book`.execute(db);
}
