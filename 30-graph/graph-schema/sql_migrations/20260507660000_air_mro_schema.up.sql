CREATE TABLE IF NOT EXISTS vertex_air_mro_work_order (
      vertex_id VARCHAR PRIMARY KEY,
      wo_no VARCHAR,
      work_order_ref VARCHAR,
      aircraft_reg VARCHAR,
      tail_number VARCHAR,
      flight_no VARCHAR,
      task_type VARCHAR,
      check_type VARCHAR,
      station VARCHAR,
      description TEXT,
      priority VARCHAR,
      due_date VARCHAR,
      check_date VARCHAR,
      expiry_date VARCHAR,
      inspector VARCHAR,
      days_until_due BIGINT,
      occurrence_date VARCHAR,
      category VARCHAR,
      report_ref VARCHAR,
      scheduled_date VARCHAR,
      estimated_days BIGINT,
      hangar_code VARCHAR,
      report_period VARCHAR,
      dispatch_reliability DOUBLE PRECISION,
      technical_delay_count BIGINT,
      pireps BIGINT,
      gse_id VARCHAR,
      gse_type VARCHAR,
      iata_code VARCHAR,
      service_date VARCHAR,
      next_service_date VARCHAR,
      operational_status VARCHAR,
      status VARCHAR,
      opened_at VARCHAR,
      closed_at VARCHAR,
      man_hours DOUBLE PRECISION,
      actor_did VARCHAR,
      org_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_air_mro_component (
      vertex_id VARCHAR PRIMARY KEY,
      part_no VARCHAR,
      part_number VARCHAR,
      serial_no VARCHAR,
      serial_number VARCHAR,
      aircraft_reg VARCHAR,
      tail_number VARCHAR,
      mpd_task VARCHAR,
      ttl_hours DOUBLE PRECISION,
      tti_hours DOUBLE PRECISION,
      cycles_since_new BIGINT,
      hours_since_new DOUBLE PRECISION,
      install_date VARCHAR,
      last_insp_at VARCHAR,
      next_due_at VARCHAR,
      next_due_date VARCHAR,
      days_to_next_due BIGINT,
      quantity BIGINT,
      supplier_code VARCHAR,
      urgency VARCHAR,
      work_order_ref VARCHAR,
      aog_escalated BOOLEAN,
      ordered_at VARCHAR,
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

CREATE TABLE IF NOT EXISTS vertex_air_mro_ad_compliance (
      vertex_id VARCHAR PRIMARY KEY,
      ad_no VARCHAR,
      aircraft_reg VARCHAR,
      compliance_method VARCHAR,
      compliance_date VARCHAR,
      due_at VARCHAR,
      recurrence_interval VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_air_mro_reliability_report (
      vertex_id VARCHAR PRIMARY KEY,
      aircraft_type VARCHAR,
      carrier_code VARCHAR,
      period VARCHAR,
      dispatch_reliability DOUBLE PRECISION,
      mtbf_hours DOUBLE PRECISION,
      pirep_rate DOUBLE PRECISION,
      ata_chapter VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_air_work_order_on_component (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_air_mro_work_order_reg_status
      ON vertex_air_mro_work_order (aircraft_reg, status);

CREATE INDEX IF NOT EXISTS idx_air_mro_component_part_serial
      ON vertex_air_mro_component (part_no, serial_no);

CREATE INDEX IF NOT EXISTS idx_air_mro_ad_compliance_ad_no
      ON vertex_air_mro_ad_compliance (ad_no);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_air_fleet_dispatch_reliability AS
    SELECT
      aircraft_type,
      carrier_code,
      AVG(dispatch_reliability) AS avg_dispatch_reliability,
      AVG(mtbf_hours) AS avg_mtbf
    FROM vertex_air_mro_reliability_report
    GROUP BY aircraft_type, carrier_code;
