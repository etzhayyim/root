import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-orcid Phase 1 — write NSID vertex tables (ADR-0056 Wave 5).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_orcid_researcher (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      orcid_id varchar NOT NULL, given_name varchar, family_name varchar,
      primary_email varchar, country varchar, biography varchar,
      verification varchar NOT NULL, status varchar NOT NULL,
      registered_at varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_orcid_affiliation (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      orcid_id varchar NOT NULL, org_ror_id varchar, org_name varchar NOT NULL,
      role varchar, affiliation_type varchar NOT NULL,
      start_date varchar, end_date varchar,
      confidence double precision, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_orcid_researcher_org (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_orcid_by_country AS
      SELECT country, verification, COUNT(*) AS researcher_count,
             MAX(registered_at) AS latest_registered_at
      FROM vertex_open_orcid_researcher WHERE status='active'
      GROUP BY country, verification;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_orcid_by_country`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_orcid_researcher_org`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_orcid_affiliation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_orcid_researcher`.execute(db);
}
