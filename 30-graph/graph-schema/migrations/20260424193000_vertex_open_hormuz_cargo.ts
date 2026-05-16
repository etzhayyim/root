import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-hormuz-cargo — Strait of Hormuz cargo workflow (ADR-0017 Maritime Cluster).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_hormuz_cargo_manifest (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      manifest_id varchar NOT NULL, imo varchar NOT NULL, voyage_id varchar,
      cargo_category varchar NOT NULL, hs_code varchar,
      origin_port_locode varchar, destination_port_locode varchar,
      volume_tonnes double precision NOT NULL, value_usd double precision,
      consignor_lei varchar, consignee_lei varchar,
      declared_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_hormuz_rerouting (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      rerouting_id varchar NOT NULL, manifest_vid varchar,
      original_route varchar NOT NULL, new_route varchar NOT NULL,
      reason varchar NOT NULL, additional_days double precision,
      additional_cost_usd double precision, bunker_fuel_extra_tonnes double precision,
      impact_tier varchar NOT NULL,
      decided_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_hormuz_cargo_hs (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_hormuz_cargo_by_category AS
      SELECT cargo_category, destination_port_locode, COUNT(*) AS manifest_count,
             SUM(volume_tonnes) AS total_volume, SUM(value_usd) AS total_value,
             MAX(declared_at) AS latest_declared
      FROM vertex_open_hormuz_cargo_manifest WHERE status='declared'
      GROUP BY cargo_category, destination_port_locode;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_hormuz_cargo_by_category`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_hormuz_cargo_hs`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_hormuz_rerouting`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_hormuz_cargo_manifest`.execute(db);
}
