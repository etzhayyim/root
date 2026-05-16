CREATE MATERIALIZED VIEW IF NOT EXISTS mv_attractor_stability AS
    SELECT
      COUNT(*)                                                                     AS total_events,
      SUM(CASE WHEN scored = true THEN 1 ELSE 0 END)                              AS scored_events,
      COUNT(DISTINCT agent_did)                                                    AS n_agents,
      COUNT(DISTINCT case_id)                                                      AS n_callers,

      -- entropy_spread = SQRT(E[X^2] - E[X]^2) ≈ stddev（GREATEST で負数回避）
      SQRT(GREATEST(
        AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
        - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
        * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
        0.0
      ))                                                                           AS entropy_spread,

      AVG(CASE WHEN scored = true THEN score_total        ELSE NULL END)          AS mean_score_total,
      AVG(CASE WHEN scored = true THEN score_spirit       ELSE NULL END)          AS mean_spirit,
      AVG(CASE WHEN scored = true THEN score_wellbecoming ELSE NULL END)          AS mean_wellbecoming,
      AVG(CASE WHEN scored = true THEN score_feeling      ELSE NULL END)          AS mean_feeling,
      AVG(CASE WHEN scored = true THEN score_buffer       ELSE NULL END)          AS mean_buffer,
      AVG(CASE WHEN separation_delta IS NOT NULL THEN separation_delta ELSE NULL END) AS mean_separation_delta,

      CAST(SUM(CASE WHEN floor_violated = true THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(SUM(CASE WHEN scored = true THEN 1 ELSE 0 END), 0)                 AS floor_violation_rate,

      -- attractor_status: ρ(J) < 1 の代理指標
      --   spread < 0.05  → 'stable'     (tight cluster around q*)
      --   spread < 0.15  → 'converging' (ρ(J) < 1 推定)
      --   spread ≥ 0.15  → 'diverging'  (ρ(J) → 1 警告)
      CASE
        WHEN SQRT(GREATEST(
               AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
               - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
               * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
               0.0
             )) < 0.05 THEN 'stable'
        WHEN SQRT(GREATEST(
               AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
               - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
               * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
               0.0
             )) < 0.15 THEN 'converging'
        ELSE 'diverging'
      END                                                                          AS attractor_status,

      MAX(created_at)                                                              AS last_event_at
    FROM vertex_wellbecoming_event;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_attractor_stability_by_agent AS
    SELECT
      agent_did,
      SUM(CASE WHEN scored = true THEN 1 ELSE 0 END)                              AS scored_events,
      SQRT(GREATEST(
        AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
        - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
        * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
        0.0
      ))                                                                           AS entropy_spread,
      AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)                 AS mean_score_total,
      AVG(CASE WHEN separation_delta IS NOT NULL THEN separation_delta ELSE NULL END) AS mean_separation_delta,
      SUM(CASE WHEN floor_violated = true THEN 1 ELSE 0 END)                      AS floor_violations,
      CASE
        WHEN SQRT(GREATEST(
               AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
               - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
               * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
               0.0
             )) < 0.05 THEN 'stable'
        WHEN SQRT(GREATEST(
               AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
               - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
               * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
               0.0
             )) < 0.15 THEN 'converging'
        ELSE 'diverging'
      END                                                                          AS attractor_status,
      MAX(created_at)                                                              AS last_event_at
    FROM vertex_wellbecoming_event
    GROUP BY agent_did;
