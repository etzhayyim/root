import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_aidesk_job_status AS
    SELECT
      j.actor_did,
      j.status,
      j.license_tier,
      COUNT(*) AS job_count,
      MAX(j.created_at) AS last_activity
    FROM vertex_aidesk_design_job j
    GROUP BY j.actor_did, j.status, j.license_tier
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_aidesk_job_status`.execute(db);
}
