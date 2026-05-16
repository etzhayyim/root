CREATE TABLE IF NOT EXISTS vertex_air_crew_roster (
      vertex_id VARCHAR PRIMARY KEY,
      crew_did VARCHAR,
      flight_no VARCHAR,
      flight_nos TEXT,
      dep_date VARCHAR,
      roster_period VARCHAR,
      crew_count BIGINT,
      flight_count BIGINT,
      pairing_ref VARCHAR,
      total_flight_hours DOUBLE PRECISION,
      hours_28_days DOUBLE PRECISION,
      hours_365_days DOUBLE PRECISION,
      ftl_compliant BOOLEAN,
      assessment_date VARCHAR,
      hours_last_24h DOUBLE PRECISION,
      hours_last_7d DOUBLE PRECISION,
      rest_hours_last DOUBLE PRECISION,
      risk_level VARCHAR,
      role VARCHAR,
      crew_role VARCHAR,
      deadhead_flight_no VARCHAR,
      travel_type VARCHAR,
      duty_date VARCHAR,
      duty_start_time VARCHAR,
      duty_end_time VARCHAR,
      flight_hours DOUBLE PRECISION,
      duty_hours DOUBLE PRECISION,
      limit_breach BOOLEAN,
      notification_type VARCHAR,
      message TEXT,
      duty_start VARCHAR,
      duty_end VARCHAR,
      base VARCHAR,
      status VARCHAR,
      published_by VARCHAR,
      published_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_air_crew_pairing (
      vertex_id VARCHAR PRIMARY KEY,
      pairing_id VARCHAR,
      carrier_code VARCHAR,
      crew_base VARCHAR,
      start_date VARCHAR,
      end_date VARCHAR,
      duration_days BIGINT,
      total_fdt_hours DOUBLE PRECISION,
      total_fdp_hours DOUBLE PRECISION,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_air_crew_duty_time (
      vertex_id VARCHAR PRIMARY KEY,
      crew_did VARCHAR,
      duty_date VARCHAR,
      fdp_hours DOUBLE PRECISION,
      fdt_hours DOUBLE PRECISION,
      rest_hours DOUBLE PRECISION,
      cumulative_28d DOUBLE PRECISION,
      cumulative_90d DOUBLE PRECISION,
      cumulative_365d DOUBLE PRECISION,
      limit_breach BOOLEAN,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_air_crew_qualification (
      vertex_id VARCHAR PRIMARY KEY,
      crew_did VARCHAR,
      aircraft_type VARCHAR,
      rating_type VARCHAR,
      qual_code VARCHAR,
      issued_at VARCHAR,
      expires_at VARCHAR,
      expiry_date VARCHAR,
      days_to_expiry BIGINT,
      status VARCHAR,
      issuing_authority VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_air_crew_roster_has_pairing (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_air_crew_roster_crew_date
      ON vertex_air_crew_roster (crew_did, dep_date);

CREATE INDEX IF NOT EXISTS idx_air_crew_pairing_carrier_id
      ON vertex_air_crew_pairing (carrier_code, pairing_id);

CREATE INDEX IF NOT EXISTS idx_air_crew_duty_time_crew_date
      ON vertex_air_crew_duty_time (crew_did, duty_date);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_air_crew_fatigue_risk AS
    SELECT
      crew_did,
      MAX(cumulative_28d) AS max_28d,
      MAX(cumulative_365d) AS max_365d,
      BOOL_OR(limit_breach) AS any_breach
    FROM vertex_air_crew_duty_time
    GROUP BY crew_did;
