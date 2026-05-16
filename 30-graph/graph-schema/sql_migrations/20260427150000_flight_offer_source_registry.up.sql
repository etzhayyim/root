CREATE TABLE IF NOT EXISTS vertex_airline (
      vertex_id          VARCHAR PRIMARY KEY,
      iata_code          VARCHAR,
      icao_code          VARCHAR,
      name               VARCHAR,
      country_code       VARCHAR,
      alliance           VARCHAR,
      accepts_ndc        VARCHAR,
      ingest_status      VARCHAR,
      created_at         VARCHAR,
      sensitivity_ord    BIGINT,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_flight_offer_source (
      vertex_id          VARCHAR PRIMARY KEY,
      source_id          VARCHAR,
      source_type        VARCHAR,
      adapter_key        VARCHAR,
      base_url           VARCHAR,
      auth_scheme        VARCHAR,
      auth_env_key       VARCHAR,
      cadence_minutes    BIGINT,
      rate_limit_rpm     BIGINT,
      airlines_count     BIGINT,
      coverage_note      VARCHAR,
      status             VARCHAR,
      created_at         VARCHAR,
      sensitivity_ord    BIGINT,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_flight_offer_source_covers_airline (
      edge_id            VARCHAR PRIMARY KEY,
      src_vertex_id      VARCHAR,
      dst_vertex_id      VARCHAR,
      source_id          VARCHAR,
      iata_code          VARCHAR,
      coverage_class     VARCHAR,
      observed_at        VARCHAR,
      created_at         VARCHAR,
      sensitivity_ord    BIGINT,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_flight_offer_source_coverage AS
    SELECT
      provider AS source_id,
      airline AS iata_code,
      COUNT(*)::BIGINT AS offers_observed,
      MIN(total_price)::DOUBLE PRECISION AS min_total_price,
      MAX(observed_at) AS last_observed_at
    FROM vertex_flight_offer
    WHERE provider IS NOT NULL AND provider <> ''
      AND airline IS NOT NULL AND airline <> ''
    GROUP BY provider, airline;
