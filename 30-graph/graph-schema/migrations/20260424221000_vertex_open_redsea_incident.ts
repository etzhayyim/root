import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * open-redsea-incident — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_redsea_houthi_attack (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    attack_id varchar NOT NULL, imo varchar, vessel_name varchar, flag varchar,
    weapon_type varchar NOT NULL, impact varchar NOT NULL,
    lat double precision, lon double precision, narrative varchar,
    casualties int, vessel_damaged boolean, vessel_sunk boolean,
    severity varchar NOT NULL, require_international_notice boolean,
    occurred_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_redsea_suez_approach_incident (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    incident_id varchar NOT NULL, imo varchar, incident_type varchar NOT NULL,
    lat double precision, lon double precision, narrative varchar,
    severity varchar NOT NULL, require_public_notice boolean,
    occurred_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_redsea_suez_approach_incident`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_redsea_houthi_attack`.execute(db);
}
