import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-doi Phase 1 — write NSID vertex tables (ADR-0056 Wave 5).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_doi_doi (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      doi varchar NOT NULL, doi_prefix varchar NOT NULL, doi_suffix varchar NOT NULL,
      registrant_org_id varchar NOT NULL, title varchar,
      publication_type varchar NOT NULL, publisher varchar,
      published_at varchar, authors_orcid varchar,
      verification varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_doi_citation (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      citing_doi varchar NOT NULL, cited_doi varchar NOT NULL,
      citation_type varchar, confidence double precision, source varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_doi_citation_pair (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_doi_by_publisher AS
      SELECT publisher, publication_type, COUNT(*) AS doi_count,
             MAX(published_at) AS latest_published_at
      FROM vertex_open_doi_doi WHERE status='active'
      GROUP BY publisher, publication_type;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_doi_by_publisher`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_doi_citation_pair`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_doi_citation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_doi_doi`.execute(db);
}
