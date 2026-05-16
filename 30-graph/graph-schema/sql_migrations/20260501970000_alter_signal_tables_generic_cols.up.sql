DROP MATERIALIZED VIEW IF EXISTS mv_signal_area_integral;

DROP MATERIALIZED VIEW IF EXISTS mv_signal_entropy;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_signal_entropy AS
    SELECT
      signal_axis,
      tick,
      AVG(entropy_h)           AS h_avg,
      MAX(h_max)               AS h_max,
      AVG(eta)                 AS eta,
      SUM(axis_weight * eta)   AS area_contrib
    FROM (
      SELECT 'attention' AS signal_axis,
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)) AS tick,
             entropy_h, COALESCE(h_max, 10.0) AS h_max, eta, COALESCE(axis_weight, 1.45) AS axis_weight
        FROM vertex_signal_attention
      UNION ALL
      SELECT 'request',
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)),
             entropy_h, COALESCE(h_max, 9.0), eta, COALESCE(axis_weight, 1.35)
        FROM vertex_signal_request
      UNION ALL
      SELECT 'money',
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)),
             entropy_h, COALESCE(h_max, 6.6), eta, COALESCE(axis_weight, 1.45)
        FROM vertex_signal_money
      UNION ALL
      SELECT 'emotion',
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)),
             entropy_h, COALESCE(h_max, 6.0), eta, COALESCE(axis_weight, 1.55)
        FROM vertex_signal_emotion
      UNION ALL
      SELECT 'market',
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)),
             entropy_h, COALESCE(h_max, 7.6), eta, COALESCE(axis_weight, 1.35)
        FROM vertex_signal_market
      UNION ALL
      SELECT 'influence',
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)),
             entropy_h, COALESCE(h_max, 6.6), eta, COALESCE(axis_weight, 1.80)
        FROM vertex_signal_influence
    ) t
    GROUP BY signal_axis, tick;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_signal_area_integral AS
    SELECT
      tick,
      SUM(area_contrib)         AS a_info,
      SUM(area_contrib) / 4.475 AS eta_global,
      CASE
        WHEN SUM(area_contrib) < 1.567 THEN 'BELOW_BASELINE'
        WHEN SUM(area_contrib) < 3.0   THEN 'PARTIAL'
        ELSE 'OPTIMAL'
      END                       AS coverage_grade
    FROM mv_signal_entropy
    GROUP BY tick;
