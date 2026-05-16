CREATE VIEW IF NOT EXISTS v_rl_aif_convergence AS
    WITH belief_stats AS (
      SELECT
        actor_did,
        AVG(free_energy) AS avg_free_energy,
        MIN(free_energy) AS min_free_energy,
        MAX(updated_at)  AS last_belief_at
      FROM vertex_rl_aif_belief
      GROUP BY actor_did
    ),
    dispatch_stats AS (
      SELECT
        actor_did,
        COUNT(*)               AS dispatch_count,
        COUNT(outcome_step_id) AS causal_count,
        MAX(dispatched_at)     AS last_dispatch_at
      FROM vertex_rl_aif_dispatch_log
      GROUP BY actor_did
    ),
    efe_entropy AS (
      SELECT
        actor_did,
        -SUM(
          CASE WHEN policy_prob > 0
               THEN policy_prob * ln(policy_prob)
               ELSE 0.0 END
        ) AS policy_entropy
      FROM vertex_rl_aif_efe
      GROUP BY actor_did
    )
    SELECT
      b.actor_did,
      b.avg_free_energy,
      b.min_free_energy,
      COALESCE(ef.policy_entropy, 0.0) AS policy_entropy,
      COALESCE(d.dispatch_count, 0)    AS dispatch_count,
      COALESCE(d.causal_count, 0)      AS causal_count,
      CASE
        WHEN COALESCE(d.dispatch_count, 0) = 0 THEN 0.0
        ELSE CAST(COALESCE(d.causal_count, 0) AS DOUBLE PRECISION)
             / CAST(d.dispatch_count AS DOUBLE PRECISION)
      END                              AS causal_ratio,
      b.last_belief_at,
      d.last_dispatch_at
    FROM belief_stats b
    LEFT JOIN dispatch_stats d ON b.actor_did = d.actor_did
    LEFT JOIN efe_entropy    ef ON b.actor_did = ef.actor_did;
