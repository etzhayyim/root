import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-redsea-naval — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_redsea_patrol (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    patrol_id varchar NOT NULL, operation varchar NOT NULL,
    flag varchar NOT NULL, vessel_class varchar,
    area_code varchar NOT NULL, started_at varchar NOT NULL, ended_at varchar,
    status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_redsea_escort (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    escort_id varchar NOT NULL, protected_imo varchar NOT NULL,
    escort_patrol_vid varchar, from_waypoint varchar NOT NULL, to_waypoint varchar NOT NULL,
    started_at varchar NOT NULL, ended_at varchar, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_redsea_escort`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_redsea_patrol`.execute(db);
}
