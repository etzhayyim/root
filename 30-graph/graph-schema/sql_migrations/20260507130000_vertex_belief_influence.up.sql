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
    );

CREATE INDEX IF NOT EXISTS idx_vbi_agent
      ON vertex_belief_influence (agent_did);

CREATE INDEX IF NOT EXISTS idx_vbi_tick
      ON vertex_belief_influence (tick_at);

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
    FROM vertex_belief_influence;
