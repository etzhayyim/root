import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-panama-drought — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_panama_lake_level (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    measurement_id varchar NOT NULL, lake varchar NOT NULL,
    level_feet_pld double precision NOT NULL, level_normal_feet double precision,
    drought_tier varchar NOT NULL, require_restriction_notice boolean,
    measured_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_panama_draft_restriction (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    restriction_id varchar NOT NULL, lane varchar NOT NULL,
    max_draft_feet double precision NOT NULL, max_slots_per_day int,
    reason varchar NOT NULL, impact_tier varchar NOT NULL,
    effective_from varchar NOT NULL, effective_until varchar,
    status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_panama_draft_restriction`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_panama_lake_level`.execute(db);
}
