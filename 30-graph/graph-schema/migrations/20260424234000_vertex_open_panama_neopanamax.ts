import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-panama-neopanamax — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_panama_locks_passage (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    passage_id varchar NOT NULL, imo varchar NOT NULL, locks varchar NOT NULL,
    vessel_class varchar NOT NULL, beam_meters double precision, loa_meters double precision,
    started_at varchar NOT NULL, completed_at varchar, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_panama_transfer_cost (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    cost_id varchar NOT NULL, imo varchar NOT NULL,
    alternative_route varchar, days_penalty double precision, cost_delta_usd double precision,
    impact_tier varchar NOT NULL, decided_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_panama_transfer_cost`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_panama_locks_passage`.execute(db);
}
