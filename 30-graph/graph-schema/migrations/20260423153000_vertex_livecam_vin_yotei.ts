import type { Kysely } from 'kysely';
import { sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * Typed vertex tables for Livecam / VIN / Yotei read paths.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // --- Livecam ---
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_livecam_camera (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      slug VARCHAR,
      name VARCHAR,
      url VARCHAR,
      protocol VARCHAR,
      lat DOUBLE PRECISION,
      lon DOUBLE PRECISION,
      zone_slug VARCHAR,
      resolution_w BIGINT,
      resolution_h BIGINT,
      fps DOUBLE PRECISION,
      description VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_camera_slug ON vertex_livecam_camera (slug)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_camera_zone_created ON vertex_livecam_camera (zone_slug, created_at)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_livecam_zone (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      slug VARCHAR,
      name VARCHAR,
      country VARCHAR,
      region VARCHAR,
      municipality VARCHAR,
      lat DOUBLE PRECISION,
      lon DOUBLE PRECISION,
      radius_m DOUBLE PRECISION,
      crowd_threshold BIGINT,
      description VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_zone_slug ON vertex_livecam_zone (slug)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_zone_name ON vertex_livecam_zone (name)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_livecam_person_cohort (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      cohort_hash VARCHAR,
      zone_slug VARCHAR,
      dimensions_json VARCHAR,
      count BIGINT,
      first_seen VARCHAR,
      last_seen VARCHAR,
      avg_dwell_seconds DOUBLE PRECISION,
      natural_person_cohort_hash VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_person_cohort_hash ON vertex_livecam_person_cohort (cohort_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_person_zone_last_seen ON vertex_livecam_person_cohort (zone_slug, last_seen)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_livecam_vehicle_cohort (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      cohort_hash VARCHAR,
      zone_slug VARCHAR,
      dimensions_json VARCHAR,
      count BIGINT,
      first_seen VARCHAR,
      last_seen VARCHAR,
      avg_speed_kmh DOUBLE PRECISION,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_vehicle_cohort_hash ON vertex_livecam_vehicle_cohort (cohort_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_vehicle_zone_last_seen ON vertex_livecam_vehicle_cohort (zone_slug, last_seen)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_livecam_detection_event (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      camera_slug VARCHAR,
      frame_ts BIGINT,
      person_count BIGINT,
      vehicle_count BIGINT,
      detections_json VARCHAR,
      model_version VARCHAR,
      inference_ms BIGINT,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_detection_id ON vertex_livecam_detection_event (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_detection_camera_frame ON vertex_livecam_detection_event (camera_slug, frame_ts)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_livecam_anomaly (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      zone_slug VARCHAR,
      anomaly_type VARCHAR,
      severity VARCHAR,
      detected_at VARCHAR,
      description VARCHAR,
      camera_slug VARCHAR,
      resolved_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_anomaly_id ON vertex_livecam_anomaly (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_anomaly_zone_detected ON vertex_livecam_anomaly (zone_slug, detected_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_anomaly_severity ON vertex_livecam_anomaly (severity)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_livecam_summary (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      zone_slug VARCHAR,
      period VARCHAR,
      start_at VARCHAR,
      end_at VARCHAR,
      person_count BIGINT,
      vehicle_count BIGINT,
      event_count BIGINT,
      anomaly_count BIGINT,
      detections_count BIGINT,
      summary_json VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_livecam_summary_zone_period_created ON vertex_livecam_summary (zone_slug, period, created_at)`.execute(db);

  // --- VIN ---
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_vin_vehicle (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      vin VARCHAR,
      make VARCHAR,
      model VARCHAR,
      year BIGINT,
      plant VARCHAR,
      wmi VARCHAR,
      vds VARCHAR,
      vis VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_vehicle_vin ON vertex_vin_vehicle (vin)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_vehicle_make ON vertex_vin_vehicle (make)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_vehicle_wmi ON vertex_vin_vehicle (wmi)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_vin_license_plate (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      plate VARCHAR,
      jurisdiction VARCHAR,
      vin VARCHAR,
      first_seen VARCHAR,
      last_seen VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_plate_jur_plate ON vertex_vin_license_plate (jurisdiction, plate)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_plate_vin ON vertex_vin_license_plate (vin)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_vin_jurisdiction_registry (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      country_code VARCHAR,
      authority_name VARCHAR,
      plate_format VARCHAR,
      vin_required VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_jurisdiction_country_code ON vertex_vin_jurisdiction_registry (country_code)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_vin_manufacturer (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      name VARCHAR,
      manufacturer_name VARCHAR,
      country VARCHAR,
      wmi_codes VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_manufacturer_name ON vertex_vin_manufacturer (name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_manufacturer_country ON vertex_vin_manufacturer (country)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_vin_wmi_code (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      code VARCHAR,
      manufacturer_name VARCHAR,
      region VARCHAR,
      vehicle_type VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_wmi_code ON vertex_vin_wmi_code (code)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_wmi_manufacturer ON vertex_vin_wmi_code (manufacturer_name)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_vin_vehicle_type (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      type_code VARCHAR,
      body_style VARCHAR,
      segment VARCHAR,
      fuel_type VARCHAR,
      drive_type VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_vehicle_type_code ON vertex_vin_vehicle_type (type_code)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_vehicle_type_segment ON vertex_vin_vehicle_type (segment)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_vin_production_plant (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      plant_code VARCHAR,
      name VARCHAR,
      country VARCHAR,
      manufacturer_name VARCHAR,
      capacity_annual BIGINT,
      lat DOUBLE PRECISION,
      lng DOUBLE PRECISION,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_plant_code ON vertex_vin_production_plant (plant_code)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_plant_manufacturer ON vertex_vin_production_plant (manufacturer_name)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_vin_production_line (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      line_id VARCHAR,
      plant_code VARCHAR,
      vehicle_types VARCHAR,
      throughput_per_hour BIGINT,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_line_plant_code ON vertex_vin_production_line (plant_code)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_line_line_id ON vertex_vin_production_line (line_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_vin_shipment_volume (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      plant_code VARCHAR,
      jurisdiction VARCHAR,
      year BIGINT,
      month BIGINT,
      vehicle_type VARCHAR,
      volume BIGINT,
      source VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_shipment_year_jur_type ON vertex_vin_shipment_volume (year, jurisdiction, vehicle_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_shipment_plant_code ON vertex_vin_shipment_volume (plant_code)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_vin_cohort_registration (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      vin VARCHAR,
      cohort_did VARCHAR,
      label_name VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_cohort_registration_cohort_did ON vertex_vin_cohort_registration (cohort_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vin_cohort_registration_vin ON vertex_vin_cohort_registration (vin)`.execute(db);

  // --- Yotei ---
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yotei_calendar (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      owner_did_ref VARCHAR,
      name VARCHAR,
      timezone VARCHAR,
      default_duration_min BIGINT,
      booking_page_enabled BOOLEAN,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yotei_calendar_id ON vertex_yotei_calendar (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yotei_calendar_owner ON vertex_yotei_calendar (owner_did_ref)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yotei_availability (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      calendar_id VARCHAR,
      day_of_week BIGINT,
      start_time VARCHAR,
      end_time VARCHAR,
      specific_date VARCHAR,
      recurring BOOLEAN,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yotei_availability_calendar_day ON vertex_yotei_availability (calendar_id, day_of_week)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yotei_availability_specific_date ON vertex_yotei_availability (specific_date)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yotei_event (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      calendar_id VARCHAR,
      title VARCHAR,
      start_at VARCHAR,
      end_at VARCHAR,
      location VARCHAR,
      description VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yotei_event_calendar_start ON vertex_yotei_event (calendar_id, start_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yotei_event_status ON vertex_yotei_event (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yotei_event_id ON vertex_yotei_event (id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_yotei_booking (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      calendar_id VARCHAR,
      event_id VARCHAR,
      requester_did VARCHAR,
      responder_did VARCHAR,
      duration_min BIGINT,
      proposed_slots VARCHAR,
      confirmed_slot VARCHAR,
      message VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yotei_booking_calendar_status ON vertex_yotei_booking (calendar_id, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_yotei_booking_id ON vertex_yotei_booking (id)`.execute(db);

  // --- Count MVs ---
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_livecam_detection_event_count AS
    SELECT actor_id, camera_slug, count(*)::bigint AS cnt
    FROM vertex_livecam_detection_event
    GROUP BY actor_id, camera_slug
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_livecam_anomaly_count AS
    SELECT actor_id, zone_slug, severity, count(*)::bigint AS cnt
    FROM vertex_livecam_anomaly
    GROUP BY actor_id, zone_slug, severity
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_vin_vehicle_count AS
    SELECT actor_id, make, count(*)::bigint AS cnt
    FROM vertex_vin_vehicle
    GROUP BY actor_id, make
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_vin_shipment_volume_count AS
    SELECT actor_id, year, jurisdiction, vehicle_type, count(*)::bigint AS cnt, sum(volume)::bigint AS total_volume
    FROM vertex_vin_shipment_volume
    GROUP BY actor_id, year, jurisdiction, vehicle_type
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_yotei_booking_count AS
    SELECT actor_id, calendar_id, status, count(*)::bigint AS cnt
    FROM vertex_yotei_booking
    GROUP BY actor_id, calendar_id, status
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_yotei_event_count AS
    SELECT actor_id, calendar_id, status, count(*)::bigint AS cnt
    FROM vertex_yotei_event
    GROUP BY actor_id, calendar_id, status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_yotei_event_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_yotei_booking_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_vin_shipment_volume_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_vin_vehicle_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_livecam_anomaly_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_livecam_detection_event_count`.execute(db);

  await sql`DROP TABLE IF EXISTS vertex_yotei_booking`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yotei_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yotei_availability`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yotei_calendar`.execute(db);

  await sql`DROP TABLE IF EXISTS vertex_vin_cohort_registration`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vin_shipment_volume`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vin_production_line`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vin_production_plant`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vin_vehicle_type`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vin_wmi_code`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vin_manufacturer`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vin_jurisdiction_registry`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vin_license_plate`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_vin_vehicle`.execute(db);

  await sql`DROP TABLE IF EXISTS vertex_livecam_summary`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_livecam_anomaly`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_livecam_detection_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_livecam_vehicle_cohort`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_livecam_person_cohort`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_livecam_zone`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_livecam_camera`.execute(db);
}
