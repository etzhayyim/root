import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * open-panama-transit — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_panama_transit (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    transit_id varchar NOT NULL, imo varchar NOT NULL, direction varchar NOT NULL,
    lane varchar NOT NULL, reservation_id varchar,
    entered_at varchar NOT NULL, cleared_at varchar, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_panama_reservation (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    reservation_id varchar NOT NULL, imo varchar NOT NULL, booking_type varchar NOT NULL,
    slot_date varchar NOT NULL, lane varchar NOT NULL, auction_price_usd double precision,
    priority_tier varchar NOT NULL, booked_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_panama_reservation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_panama_transit`.execute(db);
}
