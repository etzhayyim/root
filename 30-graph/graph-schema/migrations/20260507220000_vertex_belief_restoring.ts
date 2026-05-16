import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0098 Repo-as-Attractor — γ restoring force (homeostasis term).
// vertex_belief_baseline: write-once q_i^0 per agent (first observed score).
// vertex_belief_restoring: per-tick restoring_delta_i = -γ * (q_i - q_i^0).
// mv_belief_restoring_summary: deviation convergence status for D-feed gate.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_belief_baseline (
      vertex_id        VARCHAR PRIMARY KEY,
      agent_did        VARCHAR NOT NULL,
      q0               DOUBLE PRECISION NOT NULL,
      captured_at      TIMESTAMP NOT NULL,
      updated_at       TIMESTAMP NOT NULL,
      sensitivity_ord  INT NOT NULL DEFAULT 1,
      org_id           VARCHAR NOT NULL DEFAULT '',
      user_id          VARCHAR NOT NULL DEFAULT '',
      actor_id         VARCHAR NOT NULL DEFAULT 'sys.bpmn.wellbecoming'
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_belief_baseline_agent
    ON vertex_belief_baseline (agent_did)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_belief_restoring (
      vertex_id        VARCHAR PRIMARY KEY,
      agent_did        VARCHAR NOT NULL,
      q_current        DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      q0               DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      deviation        DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      restoring_delta  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      gamma_lr         DOUBLE PRECISION NOT NULL DEFAULT 0.05,
      tick_at          TIMESTAMP NOT NULL,
      updated_at       TIMESTAMP NOT NULL,
      sensitivity_ord  INT NOT NULL DEFAULT 1,
      org_id           VARCHAR NOT NULL DEFAULT '',
      user_id          VARCHAR NOT NULL DEFAULT '',
      actor_id         VARCHAR NOT NULL DEFAULT 'sys.bpmn.wellbecoming'
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_belief_restoring_agent
    ON vertex_belief_restoring (agent_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_belief_restoring_tick
    ON vertex_belief_restoring (tick_at DESC)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_belief_restoring_summary AS
    SELECT
      MAX(ABS(deviation))       AS max_abs_deviation,
      AVG(ABS(deviation))       AS mean_abs_deviation,
      MAX(ABS(restoring_delta)) AS max_abs_restoring,
      AVG(ABS(restoring_delta)) AS mean_abs_restoring,
      SUM(CASE WHEN ABS(deviation) < 0.01 THEN 1 ELSE 0 END) AS n_at_baseline,
      COUNT(*)                  AS n_agents,
      CASE
        WHEN MAX(ABS(deviation)) < 0.01 THEN 'at_baseline'
        WHEN MAX(ABS(deviation)) < 0.05 THEN 'near_baseline'
        ELSE 'drifting'
      END AS deviation_status
    FROM vertex_belief_restoring
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_belief_restoring_summary`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_belief_restoring`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_belief_baseline`.execute(db);
}
