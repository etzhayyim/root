import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-redsea-rerouting — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_redsea_cape_diversion (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    diversion_id varchar NOT NULL, imo varchar NOT NULL,
    original_route varchar NOT NULL, additional_days double precision,
    additional_cost_usd double precision, bunker_fuel_extra_tonnes double precision,
    impact_tier varchar NOT NULL, decided_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_redsea_reinsurance (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    reinsurance_id varchar NOT NULL, insurer_lei varchar,
    vessel_type varchar NOT NULL, original_premium_bps double precision NOT NULL,
    adjusted_premium_bps double precision NOT NULL, premium_delta_bps double precision NOT NULL,
    rate_shock_tier varchar NOT NULL, require_market_notice boolean,
    effective_from varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_redsea_reinsurance`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_redsea_cape_diversion`.execute(db);
}
