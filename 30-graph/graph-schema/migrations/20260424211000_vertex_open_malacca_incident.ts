import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * open-malacca-incident — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_malacca_piracy (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    incident_id varchar NOT NULL, imo varchar, vessel_name varchar, flag varchar,
    recaap_category varchar NOT NULL, lat double precision, lon double precision,
    narrative varchar, casualties int, cargo_stolen_usd double precision,
    severity varchar NOT NULL, require_recaap_notice boolean,
    occurred_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_malacca_nav_incident (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    incident_id varchar NOT NULL, imo varchar, incident_type varchar NOT NULL,
    lat double precision, lon double precision, narrative varchar,
    spill_volume_tonnes double precision, severity varchar NOT NULL, require_public_notice boolean,
    occurred_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_malacca_nav_incident`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_malacca_piracy`.execute(db);
}
