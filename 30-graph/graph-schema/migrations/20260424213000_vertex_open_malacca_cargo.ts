import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * open-malacca-cargo — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_malacca_container_flow (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    flow_id varchar NOT NULL, terminal_code varchar NOT NULL,
    imo varchar NOT NULL, teu_in int NOT NULL, teu_out int NOT NULL,
    call_date varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_malacca_bunker_delivery (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    delivery_id varchar NOT NULL, imo varchar NOT NULL, bunker_type varchar NOT NULL,
    volume_tonnes double precision NOT NULL, price_usd_tonne double precision,
    supplier varchar, delivered_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_malacca_bunker_delivery`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_malacca_container_flow`.execute(db);
}
