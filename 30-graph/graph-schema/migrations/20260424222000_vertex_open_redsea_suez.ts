import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-redsea-suez — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_redsea_suez_transit (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    transit_id varchar NOT NULL, imo varchar NOT NULL, direction varchar NOT NULL,
    convoy_id varchar, scn_booked boolean, suez_toll_usd double precision,
    entered_at varchar NOT NULL, cleared_at varchar, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_redsea_suez_toll (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    toll_id varchar NOT NULL, effective_from varchar NOT NULL,
    vessel_type varchar NOT NULL, laden boolean, rate_usd_scnt double precision NOT NULL,
    discount_pct double precision, surcharge_pct double precision, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_redsea_suez_toll`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_redsea_suez_transit`.execute(db);
}
