import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-gs1 Phase 1 — write NSID vertex tables (ADR-0056 Wave 5).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_gs1_gtin (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      gtin varchar NOT NULL, gtin_format varchar NOT NULL,
      brand_org_id varchar NOT NULL, product_name varchar,
      product_category varchar, country_of_origin varchar,
      net_weight_g double precision, container_type varchar,
      check_digit_valid boolean, status varchar NOT NULL,
      registered_at varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_gs1_mapping (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      gtin varchar NOT NULL, unspsc_code varchar NOT NULL,
      confidence double precision, mapper_did varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_gs1_gtin_unspsc (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_gs1_by_category AS
      SELECT product_category, country_of_origin, COUNT(*) AS gtin_count,
             MAX(registered_at) AS latest_registered_at
      FROM vertex_open_gs1_gtin WHERE status='active'
      GROUP BY product_category, country_of_origin;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_gs1_by_category`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_gs1_gtin_unspsc`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_gs1_mapping`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_gs1_gtin`.execute(db);
}
