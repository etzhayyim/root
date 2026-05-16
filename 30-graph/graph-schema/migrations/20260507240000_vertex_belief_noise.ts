import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0098 F — ξ stochastic noise injection (Ornstein-Uhlenbeck).
// vertex_belief_noise: current OU state per agent (one row, delete+insert each tick).
// mv_belief_noise_summary: 1-row aggregate for monitoring noise amplitude.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_belief_noise (
      vertex_id        VARCHAR PRIMARY KEY,
      agent_did        VARCHAR,
      tick_ms          BIGINT,
      xi_value         DOUBLE PRECISION,
      sigma            DOUBLE PRECISION,
      ou_theta         DOUBLE PRECISION,
      created_at       VARCHAR,
      sensitivity_ord  INT,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_belief_noise_agent
      ON vertex_belief_noise (agent_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_belief_noise_tick
      ON vertex_belief_noise (tick_ms)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_belief_noise_summary AS
    SELECT
      COUNT(*)                          AS n_agents,
      AVG(xi_value)                     AS mean_xi,
      AVG(CASE WHEN xi_value >= 0 THEN xi_value ELSE -xi_value END) AS mean_abs_xi,
      MAX(CASE WHEN xi_value >= 0 THEN xi_value ELSE -xi_value END) AS max_abs_xi,
      AVG(xi_value * xi_value)          AS mean_xi_sq,
      MAX(tick_ms)                      AS latest_tick_ms
    FROM vertex_belief_noise
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_belief_noise_summary`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_belief_noise`.execute(db);
}
