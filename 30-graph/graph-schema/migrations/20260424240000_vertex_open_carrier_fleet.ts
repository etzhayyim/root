import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C
/**
 * open-carrier-fleet — Wave 10 commercial carrier cluster.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_carrier_fleet_carrier (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      carrier_code varchar NOT NULL, carrier_name varchar NOT NULL, scac varchar, lei varchar,
      alliance varchar, hq_country varchar, vessel_count int, teu_capacity double precision,
      rank_tier varchar NOT NULL, registered_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_carrier_fleet_vessel (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      imo varchar NOT NULL, mmsi varchar, carrier_code varchar NOT NULL,
      vessel_name varchar, teu_capacity int, dwt_tonnes double precision, build_year int,
      vessel_class varchar, flag varchar, registered_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_carrier_fleet_vessel`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_carrier_fleet_carrier`.execute(db);
}
