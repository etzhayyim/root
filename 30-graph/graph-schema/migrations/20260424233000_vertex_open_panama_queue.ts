import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-panama-queue — chokepoint cluster (ADR-0017 Wave 9).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_panama_anchorage_queue (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    queue_id varchar NOT NULL, imo varchar NOT NULL, anchorage_zone varchar NOT NULL,
    arrived_at varchar NOT NULL, queued_position int, departed_at varchar,
    dwell_hours double precision, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_panama_priority (
    vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
    assignment_id varchar NOT NULL, imo varchar NOT NULL,
    priority_class varchar NOT NULL, reason varchar, assigned_slot_date varchar NOT NULL,
    require_broadcast boolean, assigned_at varchar NOT NULL, status varchar NOT NULL,
    created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_panama_priority`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_panama_anchorage_queue`.execute(db);
}
