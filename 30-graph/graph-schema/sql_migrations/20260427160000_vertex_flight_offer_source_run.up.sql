CREATE TABLE IF NOT EXISTS vertex_flight_offer_source_run (
      vertex_id          VARCHAR PRIMARY KEY,
      run_id             VARCHAR,
      source_id          VARCHAR,
      resolved_source    VARCHAR,
      origin_iata        VARCHAR,
      destination_iata   VARCHAR,
      outbound_date      VARCHAR,
      return_date        VARCHAR,
      currency           VARCHAR,
      status             VARCHAR,
      error_class        VARCHAR,
      error_message      VARCHAR,
      offers_fetched     BIGINT,
      offers_written     BIGINT,
      latency_ms         BIGINT,
      observed_at        VARCHAR,
      sensitivity_ord    BIGINT,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_flight_offer_source_health AS
    SELECT
      source_id,
      COUNT(*)::BIGINT                                              AS runs_total,
      SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END)::BIGINT        AS runs_ok,
      SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END)::BIGINT     AS runs_error,
      SUM(CASE WHEN status = 'fallback' THEN 1 ELSE 0 END)::BIGINT  AS runs_fallback,
      AVG(latency_ms)::DOUBLE PRECISION                             AS avg_latency_ms,
      SUM(offers_written)::BIGINT                                   AS offers_written_total,
      MAX(observed_at)                                              AS last_run_at,
      MAX(CASE WHEN status = 'ok' THEN observed_at ELSE NULL END)   AS last_ok_at
    FROM vertex_flight_offer_source_run
    GROUP BY source_id;
