import type { Kysely } from "kysely";
import { sql } from "kysely";

// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kaisya_org_snapshot (
      vertex_id          VARCHAR PRIMARY KEY,
      snapshot_at        TIMESTAMP NOT NULL,
      omega              DOUBLE PRECISION,
      eta_value          DOUBLE PRECISION,
      u_total            DOUBLE PRECISION,
      spirit_score       DOUBLE PRECISION,
      wellbecoming_score DOUBLE PRECISION,
      feeling_score      DOUBLE PRECISION,
      buffer_score       DOUBLE PRECISION,
      separation_delta   DOUBLE PRECISION,
      decisions_json     VARCHAR,
      actions_executed   INTEGER DEFAULT 0,
      tasks_created      INTEGER DEFAULT 0,
      agent_runs_24h     INTEGER DEFAULT 0,
      pending_tasks      INTEGER DEFAULT 0,
      at_risk_callers    INTEGER DEFAULT 0,
      open_legal_cases   INTEGER DEFAULT 0,
      floor_violated     BOOLEAN DEFAULT false,
      owner_did          VARCHAR NOT NULL,
      org_id             VARCHAR NOT NULL,
      user_id            VARCHAR NOT NULL,
      sensitivity_ord    INTEGER NOT NULL DEFAULT 1,
      created_at         TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kaisya_snapshot_at
      ON vertex_kaisya_org_snapshot (snapshot_at DESC)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kaisya_org_health AS
    SELECT
      COUNT(*)                                                              AS snapshot_count,
      AVG(omega)                                                            AS avg_omega,
      MIN(omega)                                                            AS min_omega,
      MAX(omega)                                                            AS max_omega,
      AVG(eta_value)                                                        AS avg_eta,
      AVG(u_total)                                                          AS avg_u_total,
      AVG(separation_delta) FILTER (WHERE separation_delta IS NOT NULL)    AS avg_separation_delta,
      SUM(actions_executed)                                                 AS total_actions,
      SUM(tasks_created)                                                    AS total_tasks_created,
      MAX(snapshot_at)                                                      AS latest_at
    FROM vertex_kaisya_org_snapshot
    WHERE snapshot_at >= NOW() - INTERVAL '24 hours'
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kaisya_org_health`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kaisya_org_snapshot`.execute(db);
}
