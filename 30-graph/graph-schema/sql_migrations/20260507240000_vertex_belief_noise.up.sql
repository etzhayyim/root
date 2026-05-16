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
    );

CREATE INDEX IF NOT EXISTS idx_belief_noise_agent
      ON vertex_belief_noise (agent_did);

CREATE INDEX IF NOT EXISTS idx_belief_noise_tick
      ON vertex_belief_noise (tick_ms);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_belief_noise_summary AS
    SELECT
      COUNT(*)                          AS n_agents,
      AVG(xi_value)                     AS mean_xi,
      AVG(CASE WHEN xi_value >= 0 THEN xi_value ELSE -xi_value END) AS mean_abs_xi,
      MAX(CASE WHEN xi_value >= 0 THEN xi_value ELSE -xi_value END) AS max_abs_xi,
      AVG(xi_value * xi_value)          AS mean_xi_sq,
      MAX(tick_ms)                      AS latest_tick_ms
    FROM vertex_belief_noise;
