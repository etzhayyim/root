import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0098 Repo-as-Attractor — D-obs: Φ influence propagation observation table.
//
// Records per-agent influence_delta_i = λ * Σ_j W_ij * (q_j - q_i) each tick.
// Observation-only (D-obs): does NOT feed back into wellbecoming event scores.
// Loop closure (D-feed) deferred until convergence monitoring confirms stability.
//
// PK = '{agent_did}:{tick_ms}' — time-bucketed, enables convergence trajectory
// queries: SELECT agent_did, influence_delta, tick_at ORDER BY tick_at.
//
// mv_belief_convergence tracks per-tick system-wide influence magnitude:
//   'converged'  → max |Δ| < 0.01  (belief differences negligible)
//   'converging' → max |Δ| < 0.05  (approaching equilibrium)
//   'active'     → max |Δ| ≥ 0.05  (significant propagation in progress)
//
// NOTE: RisingWave FILTER clause in COUNT/SUM in MVs is unsupported → use CASE WHEN.
// NOTE: No ON CONFLICT → use delete-then-insert in the Python primitive.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_belief_influence (
      vertex_id        VARCHAR PRIMARY KEY,
      agent_did        VARCHAR NOT NULL,
      influence_delta  DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      n_influencing    INT NOT NULL DEFAULT 0,
      lambda_lr        DOUBLE PRECISION NOT NULL DEFAULT 0.1,
      tick_at          TIMESTAMP NOT NULL,
      updated_at       TIMESTAMP NOT NULL,
      sensitivity_ord  INT NOT NULL DEFAULT 1,
      org_id           VARCHAR NOT NULL DEFAULT '',
      user_id          VARCHAR NOT NULL DEFAULT '',
      actor_id         VARCHAR NOT NULL DEFAULT 'sys.bpmn.wellbecoming'
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_vbi_agent
      ON vertex_belief_influence (agent_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_vbi_tick
      ON vertex_belief_influence (tick_at)
  `.execute(db);

  // Convergence monitor: system-wide influence magnitude summary.
  // FILTER unsupported in RW MV aggregates → CASE WHEN pattern.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_belief_convergence AS
    SELECT
      MAX(ABS(influence_delta))  AS max_abs_influence,
      AVG(ABS(influence_delta))  AS mean_abs_influence,
      SUM(CASE WHEN ABS(influence_delta) < 0.01 THEN 1 ELSE 0 END) AS n_converged,
      COUNT(*)                   AS n_agents,
      CASE
        WHEN MAX(ABS(influence_delta)) < 0.01 THEN 'converged'
        WHEN MAX(ABS(influence_delta)) < 0.05 THEN 'converging'
        ELSE 'active'
      END AS convergence_status
    FROM vertex_belief_influence
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_belief_convergence`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_belief_influence`.execute(db);
}
