CREATE TABLE IF NOT EXISTS vertex_aircraft (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      label              VARCHAR,
      did                VARCHAR,
      tail_number        VARCHAR,
      icao24             VARCHAR,
      mode_s             VARCHAR,
      registration_country VARCHAR,
      manufacturer       VARCHAR,
      model              VARCHAR,
      aircraft_type      VARCHAR,
      operator_did       VARCHAR,
      legal_owner_did    VARCHAR,
      in_service_at      VARCHAR,
      retired_at         VARCHAR,
      useful_life_years  DOUBLE PRECISION,
      seat_capacity      BIGINT,
      cargo_capacity_kg  DOUBLE PRECISION,
      status             VARCHAR,
      source_url         VARCHAR,
      source_license     VARCHAR,
      props              VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_flight_operation (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      label                VARCHAR,
      did                  VARCHAR,
      flight_number        VARCHAR,
      callsign             VARCHAR,
      aircraft_did         VARCHAR,
      route_did            VARCHAR,
      operator_did         VARCHAR,
      legal_owner_did      VARCHAR,
      origin_airport_did   VARCHAR,
      destination_airport_did VARCHAR,
      status               VARCHAR,
      scheduled_departure_at VARCHAR,
      actual_departure_at  VARCHAR,
      scheduled_arrival_at VARCHAR,
      actual_arrival_at    VARCHAR,
      delay_minutes        BIGINT,
      occupancy_rate       DOUBLE PRECISION,
      passengers           BIGINT,
      seat_capacity        BIGINT,
      revenue              DOUBLE PRECISION,
      cost                 DOUBLE PRECISION,
      profit               DOUBLE PRECISION,
      currency             VARCHAR,
      as_of                VARCHAR,
      source               VARCHAR,
      source_url           VARCHAR,
      source_license       VARCHAR,
      props                VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_aircraft_owned_by (
      edge_id             VARCHAR PRIMARY KEY,
      src_vid             VARCHAR,
      dst_vid             VARCHAR,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      effective_from      VARCHAR,
      effective_to        VARCHAR,
      ownership_share_pct DOUBLE PRECISION,
      source_url          VARCHAR,
      source_license      VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_aircraft_operated_by (
      edge_id             VARCHAR PRIMARY KEY,
      src_vid             VARCHAR,
      dst_vid             VARCHAR,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      effective_from      VARCHAR,
      effective_to        VARCHAR,
      source_url          VARCHAR,
      source_license      VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_flight_uses_aircraft (
      edge_id             VARCHAR PRIMARY KEY,
      src_vid             VARCHAR,
      dst_vid             VARCHAR,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      as_of               VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_flight_operated_by (
      edge_id             VARCHAR PRIMARY KEY,
      src_vid             VARCHAR,
      dst_vid             VARCHAR,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      as_of               VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_flight_departs_from (
      edge_id             VARCHAR PRIMARY KEY,
      src_vid             VARCHAR,
      dst_vid             VARCHAR,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      as_of               VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_flight_arrives_at (
      edge_id             VARCHAR PRIMARY KEY,
      src_vid             VARCHAR,
      dst_vid             VARCHAR,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      as_of               VARCHAR
    );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_flight_operation_latest_by_aircraft AS
    SELECT
      aircraft_did,
      MAX(as_of) AS as_of_latest,
      MAX(delay_minutes) AS delay_minutes_latest,
      MAX(occupancy_rate) AS occupancy_rate_latest,
      MAX(status) AS status_latest,
      MAX(operator_did) AS operator_did_latest
    FROM vertex_flight_operation
    WHERE aircraft_did IS NOT NULL AND aircraft_did <> ''
    GROUP BY aircraft_did;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_flight_operator_kpi_daily AS
    SELECT
      operator_did,
      SUBSTRING(COALESCE(as_of, created_date::VARCHAR), 1, 10) AS day,
      COUNT(*)::BIGINT AS flight_count,
      AVG(delay_minutes)::DOUBLE PRECISION AS avg_delay_minutes,
      AVG(occupancy_rate)::DOUBLE PRECISION AS avg_occupancy_rate,
      SUM(COALESCE(revenue, 0))::DOUBLE PRECISION AS total_revenue,
      SUM(COALESCE(cost, 0))::DOUBLE PRECISION AS total_cost,
      SUM(COALESCE(profit, COALESCE(revenue, 0) - COALESCE(cost, 0)))::DOUBLE PRECISION AS total_profit
    FROM vertex_flight_operation
    WHERE operator_did IS NOT NULL AND operator_did <> ''
    GROUP BY operator_did, SUBSTRING(COALESCE(as_of, created_date::VARCHAR), 1, 10);
