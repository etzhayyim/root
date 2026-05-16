import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * open-panama-toll — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_panama_toll_payment (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    payment_id varchar NOT NULL, transit_vid varchar, imo varchar NOT NULL,
    base_toll_usd double precision NOT NULL, auction_premium_usd double precision,
    total_toll_usd double precision NOT NULL, paid_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_panama_auction (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    auction_id varchar NOT NULL, slot_date varchar NOT NULL, lane varchar NOT NULL,
    winning_bid_usd double precision NOT NULL, bidder_imo varchar, bid_count int,
    closed_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_panama_auction`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_panama_toll_payment`.execute(db);
}
