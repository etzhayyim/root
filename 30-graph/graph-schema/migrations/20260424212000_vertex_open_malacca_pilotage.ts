import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-malacca-pilotage — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_malacca_pilotage (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    pilotage_id varchar NOT NULL, imo varchar NOT NULL, authority varchar NOT NULL,
    pilot_station varchar, boarding_at varchar NOT NULL, disembark_at varchar,
    status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_malacca_anchorage (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    anchorage_id varchar NOT NULL, imo varchar NOT NULL, anchorage_zone varchar NOT NULL,
    arrived_at varchar NOT NULL, departed_at varchar, dwell_hours double precision,
    purpose varchar, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_malacca_anchorage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_malacca_pilotage`.execute(db);
}
