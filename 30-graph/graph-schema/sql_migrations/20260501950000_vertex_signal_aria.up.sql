CREATE TABLE IF NOT EXISTS vertex_signal_attention (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      source_url       VARCHAR,
      topic            VARCHAR,
      search_volume    BIGINT DEFAULT 0,
      impression_count BIGINT DEFAULT 0,
      velocity         DOUBLE PRECISION DEFAULT 0.0,
      magnitude        DOUBLE PRECISION DEFAULT 0.0,
      valence          DOUBLE PRECISION DEFAULT 0.0,
      entropy_h        DOUBLE PRECISION DEFAULT 0.0,
      h_max            DOUBLE PRECISION DEFAULT 10.0,
      eta              DOUBLE PRECISION DEFAULT 0.0,
      axis_weight      DOUBLE PRECISION DEFAULT 1.45,
      captured_at      TIMESTAMPTZ
    );

CREATE TABLE IF NOT EXISTS vertex_signal_request (
      vertex_id      VARCHAR PRIMARY KEY,
      _seq           BIGINT,
      nsid           VARCHAR,
      caller_did     VARCHAR,
      call_count     BIGINT DEFAULT 0,
      intent_cluster VARCHAR,
      magnitude      DOUBLE PRECISION DEFAULT 0.0,
      valence        DOUBLE PRECISION DEFAULT 0.0,
      entropy_h      DOUBLE PRECISION DEFAULT 0.0,
      h_max          DOUBLE PRECISION DEFAULT 9.0,
      eta            DOUBLE PRECISION DEFAULT 0.0,
      axis_weight    DOUBLE PRECISION DEFAULT 1.35,
      captured_at    TIMESTAMPTZ
    );

CREATE TABLE IF NOT EXISTS vertex_signal_money (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      currency_pair   VARCHAR DEFAULT 'BTC/USD',
      volume_usd      DOUBLE PRECISION DEFAULT 0.0,
      flow_direction  VARCHAR DEFAULT 'neutral',
      settlement_type VARCHAR DEFAULT 'onchain',
      magnitude       DOUBLE PRECISION DEFAULT 0.0,
      valence         DOUBLE PRECISION DEFAULT 0.0,
      entropy_h       DOUBLE PRECISION DEFAULT 0.0,
      h_max           DOUBLE PRECISION DEFAULT 6.6,
      eta             DOUBLE PRECISION DEFAULT 0.0,
      axis_weight     DOUBLE PRECISION DEFAULT 1.45,
      captured_at     TIMESTAMPTZ
    );

CREATE TABLE IF NOT EXISTS vertex_signal_emotion (
      vertex_id     VARCHAR PRIMARY KEY,
      _seq          BIGINT,
      source_did    VARCHAR,
      emotion_label VARCHAR,
      magnitude     DOUBLE PRECISION DEFAULT 0.0,
      valence       DOUBLE PRECISION DEFAULT 0.0,
      entropy_h     DOUBLE PRECISION DEFAULT 0.0,
      h_max         DOUBLE PRECISION DEFAULT 6.0,
      eta           DOUBLE PRECISION DEFAULT 0.0,
      axis_weight   DOUBLE PRECISION DEFAULT 1.55,
      captured_at   TIMESTAMPTZ
    );

CREATE TABLE IF NOT EXISTS vertex_signal_market (
      vertex_id    VARCHAR PRIMARY KEY,
      _seq         BIGINT,
      asset_pair   VARCHAR,
      price_usd    DOUBLE PRECISION DEFAULT 0.0,
      change_24h   DOUBLE PRECISION DEFAULT 0.0,
      volatility   DOUBLE PRECISION DEFAULT 0.0,
      magnitude    DOUBLE PRECISION DEFAULT 0.0,
      valence      DOUBLE PRECISION DEFAULT 0.0,
      entropy_h    DOUBLE PRECISION DEFAULT 0.0,
      h_max        DOUBLE PRECISION DEFAULT 7.6,
      eta          DOUBLE PRECISION DEFAULT 0.0,
      axis_weight  DOUBLE PRECISION DEFAULT 1.35,
      captured_at  TIMESTAMPTZ
    );

CREATE TABLE IF NOT EXISTS vertex_signal_influence (
      vertex_id           VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      actor_did           VARCHAR,
      follower_count      BIGINT DEFAULT 0,
      repost_velocity     DOUBLE PRECISION DEFAULT 0.0,
      network_centrality  DOUBLE PRECISION DEFAULT 0.0,
      magnitude           DOUBLE PRECISION DEFAULT 0.0,
      valence             DOUBLE PRECISION DEFAULT 0.0,
      entropy_h           DOUBLE PRECISION DEFAULT 0.0,
      h_max               DOUBLE PRECISION DEFAULT 6.6,
      eta                 DOUBLE PRECISION DEFAULT 0.0,
      axis_weight         DOUBLE PRECISION DEFAULT 1.80,
      captured_at         TIMESTAMPTZ
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_signal_entropy AS
    SELECT
      signal_type,
      tick,
      AVG(entropy_h)              AS h_avg,
      MAX(h_max)                  AS h_max,
      AVG(eta)                    AS eta,
      SUM(axis_weight * eta)      AS area_contrib
    FROM (
      SELECT 'attention' AS signal_type,
             DATE_TRUNC('minute', captured_at) AS tick,
             entropy_h, h_max, eta, axis_weight
        FROM vertex_signal_attention
      UNION ALL
      SELECT 'request',
             DATE_TRUNC('minute', captured_at),
             entropy_h, h_max, eta, axis_weight
        FROM vertex_signal_request
      UNION ALL
      SELECT 'money',
             DATE_TRUNC('minute', captured_at),
             entropy_h, h_max, eta, axis_weight
        FROM vertex_signal_money
      UNION ALL
      SELECT 'emotion',
             DATE_TRUNC('minute', captured_at),
             entropy_h, h_max, eta, axis_weight
        FROM vertex_signal_emotion
      UNION ALL
      SELECT 'market',
             DATE_TRUNC('minute', captured_at),
             entropy_h, h_max, eta, axis_weight
        FROM vertex_signal_market
      UNION ALL
      SELECT 'influence',
             DATE_TRUNC('minute', captured_at),
             entropy_h, h_max, eta, axis_weight
        FROM vertex_signal_influence
    ) t
    GROUP BY signal_type, tick;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_signal_area_integral AS
    SELECT
      tick,
      SUM(area_contrib)           AS a_info,
      SUM(area_contrib) / 4.475   AS eta_global,
      CASE
        WHEN SUM(area_contrib) < 1.567 THEN 'BELOW_BASELINE'
        WHEN SUM(area_contrib) < 3.0   THEN 'PARTIAL'
        ELSE 'OPTIMAL'
      END                         AS coverage_grade
    FROM mv_signal_entropy
    GROUP BY tick;
