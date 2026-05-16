import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C
/**
 * open-carrier-capacity — Wave 10 commercial carrier cluster.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_carrier_capacity_blanked (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      blanked_id varchar NOT NULL, carrier_code varchar NOT NULL, string_code varchar NOT NULL,
      skipped_weeks int NOT NULL, teu_removed_total double precision,
      reason varchar, impact_tier varchar NOT NULL, require_shipper_notice boolean,
      effective_from varchar NOT NULL, effective_until varchar, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_carrier_capacity_utilization (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      util_id varchar NOT NULL, carrier_code varchar NOT NULL, trade_lane varchar NOT NULL,
      period_week varchar NOT NULL, teu_offered double precision NOT NULL, teu_lifted double precision NOT NULL,
      utilization_pct double precision NOT NULL, saturation_tier varchar NOT NULL,
      reported_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_open_carrier_capacity_utilization`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_carrier_capacity_blanked`.execute(db);
}
