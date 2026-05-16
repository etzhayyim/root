import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C
/**
 * open-carrier-esg — Wave 10 commercial carrier cluster.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_carrier_esg_cii (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      cii_id varchar NOT NULL, carrier_code varchar NOT NULL, period_year varchar NOT NULL,
      fleet_cii double precision NOT NULL, rating varchar NOT NULL, rating_tier varchar NOT NULL,
      poseidon_aligned boolean, reported_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_carrier_esg_green_bunker (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      report_id varchar NOT NULL, carrier_code varchar NOT NULL, period_quarter varchar NOT NULL,
      total_bunker_tonnes double precision NOT NULL, lng_share_pct double precision,
      methanol_share_pct double precision, biofuel_share_pct double precision,
      green_share_total_pct double precision NOT NULL, transition_tier varchar NOT NULL,
      reported_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_carrier_esg_green_bunker`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_carrier_esg_cii`.execute(db);
}
