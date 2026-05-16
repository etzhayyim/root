CREATE TABLE IF NOT EXISTS vertex_air_ops_flight_plan (
      vertex_id VARCHAR PRIMARY KEY,
      flight_id VARCHAR,
      carrier_code VARCHAR,
      flight_no VARCHAR,
      dep_date VARCHAR,
      origin VARCHAR,
      dest VARCHAR,
      dep_iata VARCHAR,
      arr_iata VARCHAR,
      route TEXT,
      alt_iata VARCHAR,
      altitude VARCHAR,
      altitude_ft BIGINT,
      speed VARCHAR,
      fuel_required DOUBLE PRECISION,
      fuel_on_board DOUBLE PRECISION,
      estimated_elapsed VARCHAR,
      estimated_flight_time VARCHAR,
      ifps_ref VARCHAR,
      captain_did VARCHAR,
      weather_summary TEXT,
      notam_count BIGINT,
      release_ref VARCHAR,
      iata_code VARCHAR,
      notam_type VARCHAR,
      valid_from VARCHAR,
      valid_to VARCHAR,
      report_type VARCHAR,
      valid_time VARCHAR,
      fuel_type VARCHAR,
      requested_kg DOUBLE PRECISION,
      uplift_ref VARCHAR,
      report_time VARCHAR,
      turbulence_level VARCHAR,
      icing_level VARCHAR,
      wind_speed BIGINT,
      wind_dir BIGINT,
      phase VARCHAR,
      delay_mins BIGINT,
      position_lat DOUBLE PRECISION,
      position_lon DOUBLE PRECISION,
      alert_level VARCHAR,
      status VARCHAR,
      filed_at VARCHAR,
      briefed_at VARCHAR,
      fetched_at VARCHAR,
      ordered_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_air_ops_dispatch_brief (
      vertex_id VARCHAR PRIMARY KEY,
      flight_no VARCHAR,
      dep_date VARCHAR,
      carrier_code VARCHAR,
      captain_did VARCHAR,
      fuel_planned DOUBLE PRECISION,
      alternate_airport VARCHAR,
      wx_minima_met BOOLEAN,
      ofp_version VARCHAR,
      released_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_air_ops_notam (
      vertex_id VARCHAR PRIMARY KEY,
      notam_id VARCHAR,
      location VARCHAR,
      notam_type VARCHAR,
      effective_from VARCHAR,
      effective_to VARCHAR,
      content_hash VARCHAR,
      priority VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_air_ops_pirep (
      vertex_id VARCHAR PRIMARY KEY,
      flight_no VARCHAR,
      dep_date VARCHAR,
      position VARCHAR,
      altitude VARCHAR,
      turbulence_severity VARCHAR,
      icing_severity VARCHAR,
      reported_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_air_ops_tech_log (
      vertex_id VARCHAR PRIMARY KEY,
      flight_no VARCHAR,
      dep_date VARCHAR,
      tail_number VARCHAR,
      defect_code VARCHAR,
      description TEXT,
      rectification TEXT,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_air_dispatch_brief_uses_flight_plan (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_air_ops_flight_plan_carrier_flight_date
      ON vertex_air_ops_flight_plan (carrier_code, flight_no, dep_date);

CREATE INDEX IF NOT EXISTS idx_air_ops_notam_id
      ON vertex_air_ops_notam (notam_id);

CREATE INDEX IF NOT EXISTS idx_air_ops_notam_location_from
      ON vertex_air_ops_notam (location, effective_from);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_air_flight_ops_status AS
    SELECT
      carrier_code,
      dep_date,
      COUNT(*) AS total_flights,
      COUNT(*) FILTER (WHERE status = 'active') AS active_flights
    FROM vertex_air_ops_dispatch_brief
    GROUP BY carrier_code, dep_date;
