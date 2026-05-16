CREATE TABLE IF NOT EXISTS vertex_actor_wellbecoming_profile (
      vertex_id     VARCHAR PRIMARY KEY,
      actor_did     VARCHAR NOT NULL,  -- agent that responded
      caller_did    VARCHAR NOT NULL,  -- person being served

      -- Running averages (updated each processMining run)
      avg_spirit            DOUBLE PRECISION,
      avg_wellbecoming      DOUBLE PRECISION,
      avg_feeling           DOUBLE PRECISION,
      avg_buffer            DOUBLE PRECISION,
      avg_total             DOUBLE PRECISION,
      avg_separation_delta  DOUBLE PRECISION,

      -- Bottleneck: which U axis is lowest right now
      bottleneck_axis       VARCHAR,  -- 'spirit'|'wellbecoming'|'feeling'|'buffer'|null

      -- Trend over last 24h
      separation_trend      VARCHAR DEFAULT 'stable',  -- 'improving'|'stable'|'degrading'
      at_risk               BOOLEAN DEFAULT false,     -- separation_delta < -0.3

      -- Counts
      event_count           BIGINT DEFAULT 0,
      floor_violation_count BIGINT DEFAULT 0,

      -- Proactive connection tracking
      last_proactive_at     TIMESTAMP,
      proactive_count       BIGINT DEFAULT 0,

      -- Timestamps
      last_scored_at        TIMESTAMP,
      updated_at            TIMESTAMP,
      created_at            TIMESTAMP NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_wbp_caller
      ON vertex_actor_wellbecoming_profile (caller_did);

CREATE INDEX IF NOT EXISTS idx_wbp_at_risk
      ON vertex_actor_wellbecoming_profile (at_risk, updated_at);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_wellbecoming_bottleneck_caller AS
    SELECT
      case_id                                                         AS caller_did,
      COUNT(*)                                                        AS event_count,
      AVG(score_spirit)       FILTER (WHERE scored = true)           AS avg_spirit,
      AVG(score_wellbecoming) FILTER (WHERE scored = true)           AS avg_wellbecoming,
      AVG(score_feeling)      FILTER (WHERE scored = true)           AS avg_feeling,
      AVG(score_buffer)       FILTER (WHERE scored = true)           AS avg_buffer,
      AVG(score_total)        FILTER (WHERE scored = true)           AS avg_total,
      AVG(separation_delta)   FILTER (WHERE separation_delta IS NOT NULL) AS avg_separation_delta,
      SUM(CASE WHEN floor_violated = true THEN 1 ELSE 0 END)         AS floor_violations,
      MAX(created_at)                                                 AS last_activity_at
    FROM vertex_wellbecoming_event
    GROUP BY case_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_wellbecoming_at_risk AS
    SELECT
      caller_did,
      avg_separation_delta,
      avg_spirit,
      avg_total,
      floor_violations,
      last_activity_at
    FROM mv_wellbecoming_bottleneck_caller
    WHERE avg_separation_delta < -0.3
       OR floor_violations > 0;
