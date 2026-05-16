import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_sms_safety_report (
      vertex_id VARCHAR PRIMARY KEY,
      report_id VARCHAR,
      report_ref VARCHAR,
      reporter_did_hash VARCHAR,
      reporter_did VARCHAR,
      category VARCHAR,
      severity VARCHAR,
      occurrence TEXT,
      station VARCHAR,
      description TEXT,
      likelihood VARCHAR,
      risk_score BIGINT,
      risk_level VARCHAR,
      mitigations TEXT,
      audit_ref VARCHAR,
      finding_ref VARCHAR,
      iosa_category VARCHAR,
      finding_type VARCHAR,
      due_date VARCHAR,
      regulatory_body VARCHAR,
      filing_type VARCHAR,
      filing_ref VARCHAR,
      period_start VARCHAR,
      period_end VARCHAR,
      occurrence_ref VARCHAR,
      occurrence_type VARCHAR,
      occurrence_date VARCHAR,
      bulletin_ref VARCHAR,
      bulletin_type VARCHAR,
      subject TEXT,
      target_audience VARCHAR,
      effective_date VARCHAR,
      dep_date VARCHAR,
      dg_class VARCHAR,
      un_number VARCHAR,
      quantity DOUBLE PRECISION,
      unit VARCHAR,
      notoc_ref VARCHAR,
      alert_ref VARCHAR,
      threat_type VARCHAR,
      threat_level VARCHAR,
      description_hash VARCHAR,
      reported_at VARCHAR,
      submitted_at VARCHAR,
      filed_at VARCHAR,
      distributed_at VARCHAR,
      status VARCHAR,
      flight_no VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_sms_risk_assessment (
      vertex_id VARCHAR PRIMARY KEY,
      risk_id VARCHAR,
      hazard VARCHAR,
      likelihood VARCHAR,
      severity VARCHAR,
      risk_score BIGINT,
      mitigation TEXT,
      status VARCHAR,
      assessed_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_sms_iosa_finding (
      vertex_id VARCHAR PRIMARY KEY,
      finding_id VARCHAR,
      standard_ref VARCHAR,
      category VARCHAR,
      description_hash VARCHAR,
      car_due_at VARCHAR,
      status VARCHAR,
      audit_date VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_sms_occurrence (
      vertex_id VARCHAR PRIMARY KEY,
      occ_id VARCHAR,
      flight_no VARCHAR,
      occ_type VARCHAR,
      location VARCHAR,
      injuries VARCHAR,
      damage_level VARCHAR,
      reported_at VARCHAR,
      state_authority VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_air_safety_report_triggers_risk (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_sms_safety_report_id
      ON vertex_air_sms_safety_report (report_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_sms_safety_report_category_severity
      ON vertex_air_sms_safety_report (category, severity, status)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_sms_occurrence_id
      ON vertex_air_sms_occurrence (occ_id)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_air_safety_risk_matrix AS
    SELECT
      category,
      severity,
      COUNT(*) AS report_count
    FROM vertex_air_sms_safety_report
    GROUP BY category, severity
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_air_safety_risk_matrix`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_sms_occurrence_id`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_sms_safety_report_category_severity`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_sms_safety_report_id`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_air_safety_report_triggers_risk`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_sms_occurrence`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_sms_iosa_finding`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_sms_risk_assessment`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_sms_safety_report`.execute(db);
}
