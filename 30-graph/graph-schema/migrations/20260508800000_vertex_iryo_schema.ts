import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B  (hospital ops — bed/encounter/staff/claim. PHI is hash-only at
//          Tier 1 in Phase 1; Tier 3 patient table is deferred to Phase 2.)

/**
 * iryo.gftd.ai Phase 1 — hospital operations schema
 * (ADR-2605080800 + ADR-0036 Worker-direct Hyperdrive +
 *  ADR-0056 BPMN-as-actor + ADR-2604282300 T2 = pymagatama + Zeebe).
 *
 * Tables (9 vertex + 4 edge):
 *   vertex_iryo_hospital     hospital roster (300-bed seed in Phase 1)
 *   vertex_iryo_dept         clinical department (cardiology, icu, ...)
 *   vertex_iryo_ward         physical bed group inside a dept
 *   vertex_iryo_bed          individual bed unit
 *   vertex_iryo_staff        clinical / admin staff
 *   vertex_iryo_encounter    admission-discharge cycle
 *   vertex_iryo_drg_claim    DRG-coded claim per discharge
 *   vertex_iryo_staff_shift  shift roster (8h block)
 *   vertex_iryo_health_kpi   ingested WHO/OECD/MHLW indicator value
 *
 *   edge_iryo_dept_in_hospital   dept → hospital
 *   edge_iryo_ward_in_dept       ward → dept (1:N)
 *   edge_iryo_bed_in_ward        bed → ward
 *   edge_iryo_encounter_in_bed   encounter → bed (current/last placement)
 *
 * Streaming MVs (5):
 *   mv_iryo_bed_occupancy_now         per-ward occupancy snapshot (low cardinality, ~tens of wards)
 *   mv_iryo_los_by_drg_daily          avg/median LOS per drg_code per day (bounded by drg cardinality)
 *   mv_iryo_admission_count_by_dept   per-dept admit count rolling 30d (bounded by dept count)
 *   mv_iryo_drg_pnl_daily             package_points × tariff − cost estimate per day
 *   mv_iryo_staff_coverage_gap        shifts where required headcount > rostered (low cardinality)
 *
 * All MVs respect the "no high-cardinality GROUP BY + wide MAX" guardrail
 * (graph-schema/CLAUDE.md §MV Memory Safety Guardrails).
 *
 * PII tier (ADR-0018):
 *   - Tier 1 (federable): hospital / dept / ward / bed / staff / health_kpi
 *   - vertex_iryo_encounter.patient_did is opaque hash (sha256 of synthetic
 *     identity + admission ms). Real PHI table deferred to Phase 2 with a
 *     separate Tier-3 vertex_iryo_patient_pii.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Vertex tables ──────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_iryo_hospital (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      hospital_did varchar NOT NULL,
      slug varchar NOT NULL,
      name varchar NOT NULL,
      country varchar,
      iso3166_code varchar,
      bed_capacity int NOT NULL,
      level varchar,
      tariff_system varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_iryo_dept (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      dept_did varchar NOT NULL,
      slug varchar NOT NULL,
      hospital_slug varchar NOT NULL,
      name varchar NOT NULL,
      specialty_code varchar,
      icd10_chapter varchar,
      head_staff_did varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_iryo_ward (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      slug varchar NOT NULL,
      hospital_slug varchar NOT NULL,
      dept_slug varchar NOT NULL,
      name varchar NOT NULL,
      ward_kind varchar,
      bed_count int NOT NULL,
      required_rn_per_shift int,
      required_md_per_shift int,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_iryo_bed (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      slug varchar NOT NULL,
      hospital_slug varchar NOT NULL,
      ward_slug varchar NOT NULL,
      bed_kind varchar,
      monitor_class varchar,
      occupied boolean NOT NULL,
      current_encounter_id varchar,
      last_changed_at_ms bigint,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_iryo_staff (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      staff_did varchar NOT NULL,
      hospital_slug varchar NOT NULL,
      dept_slug varchar,
      role varchar NOT NULL,
      employment_kind varchar,
      license_kind varchar,
      hired_at varchar,
      terminated_at varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_iryo_encounter (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      encounter_id varchar NOT NULL,
      patient_did varchar NOT NULL,
      hospital_slug varchar NOT NULL,
      dept_slug varchar NOT NULL,
      ward_slug varchar NOT NULL,
      bed_slug varchar,
      admission_type varchar NOT NULL,
      age_band varchar,
      sex varchar,
      severity_tier int,
      principal_diagnosis_code varchar,
      secondary_diagnosis_codes_json varchar,
      drg_code varchar,
      length_of_stay_days int,
      discharge_disposition varchar,
      admitted_at_ms bigint NOT NULL,
      discharged_at_ms bigint,
      status varchar NOT NULL,
      data_source varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_iryo_drg_claim (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      claim_id varchar NOT NULL,
      encounter_id varchar NOT NULL,
      hospital_slug varchar NOT NULL,
      dept_slug varchar NOT NULL,
      drg_code varchar NOT NULL,
      principal_diagnosis_code varchar NOT NULL,
      secondary_diagnosis_codes_json varchar,
      specialty_code varchar,
      length_of_stay_days int,
      severity_tier int,
      package_points double precision,
      tariff_system varchar NOT NULL,
      cost_estimate double precision,
      auditor_did varchar,
      submitted_at_ms bigint,
      status varchar NOT NULL,
      denial_reason varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_iryo_staff_shift (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      shift_id varchar NOT NULL,
      hospital_slug varchar NOT NULL,
      dept_slug varchar NOT NULL,
      ward_slug varchar NOT NULL,
      shift_date date NOT NULL,
      shift_block varchar NOT NULL,
      role varchar NOT NULL,
      required_count int NOT NULL,
      rostered_count int NOT NULL,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_iryo_health_kpi (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      source varchar NOT NULL,
      indicator_code varchar NOT NULL,
      country varchar,
      iso3166_code varchar,
      year int,
      value double precision,
      unit varchar,
      raw_json varchar,
      ingested_at_ms bigint NOT NULL,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Edges ──────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS edge_iryo_dept_in_hospital (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_iryo_ward_in_dept (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_iryo_bed_in_ward (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_iryo_encounter_in_bed (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  // ── Streaming MVs ──────────────────────────────────────────────────
  // Cardinality budget:
  //   wards          ~50 per hospital × ~few hospitals → ~hundreds
  //   depts          ~30 per hospital → ~hundreds
  //   drg_code       ~500-1500 codes
  //   shift × date   ~365 × ~50 wards × 3 blocks → ~55K rows/yr
  // All bounded; safe per MV memory guardrails.

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_iryo_bed_occupancy_now AS
      SELECT
        hospital_slug,
        ward_slug,
        COUNT(*) AS total_beds,
        SUM(CASE WHEN occupied THEN 1 ELSE 0 END) AS occupied_beds,
        safe_divide(
          SUM(CASE WHEN occupied THEN 1.0 ELSE 0.0 END),
          COUNT(*)::double precision,
          0.0
        ) AS utilization
      FROM vertex_iryo_bed
      WHERE status='active'
      GROUP BY hospital_slug, ward_slug;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_iryo_los_by_drg_daily AS
      SELECT
        created_date,
        drg_code,
        COUNT(*) AS discharge_count,
        AVG(length_of_stay_days::double precision) AS avg_los_days,
        MIN(length_of_stay_days) AS min_los_days,
        MAX(length_of_stay_days) AS max_los_days
      FROM vertex_iryo_encounter
      WHERE status='closed' AND drg_code IS NOT NULL AND length_of_stay_days IS NOT NULL
      GROUP BY created_date, drg_code;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_iryo_admission_count_by_dept AS
      SELECT
        hospital_slug,
        dept_slug,
        created_date,
        COUNT(*) AS admit_count,
        SUM(CASE WHEN admission_type='emergency' THEN 1 ELSE 0 END) AS emergency_count,
        SUM(CASE WHEN admission_type='elective'  THEN 1 ELSE 0 END) AS elective_count,
        SUM(CASE WHEN admission_type='transfer'  THEN 1 ELSE 0 END) AS transfer_count
      FROM vertex_iryo_encounter
      GROUP BY hospital_slug, dept_slug, created_date;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_iryo_drg_pnl_daily AS
      SELECT
        created_date,
        hospital_slug,
        dept_slug,
        drg_code,
        tariff_system,
        COUNT(*) AS claim_count,
        SUM(COALESCE(package_points, 0)) AS gross_points,
        SUM(COALESCE(cost_estimate, 0)) AS cost_estimate_total,
        SUM(COALESCE(package_points, 0) - COALESCE(cost_estimate, 0)) AS margin_points
      FROM vertex_iryo_drg_claim
      WHERE status IN ('submitted', 'paid')
      GROUP BY created_date, hospital_slug, dept_slug, drg_code, tariff_system;
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_iryo_staff_coverage_gap AS
      SELECT
        hospital_slug,
        dept_slug,
        ward_slug,
        shift_date,
        shift_block,
        role,
        SUM(required_count) AS required_total,
        SUM(rostered_count) AS rostered_total,
        SUM(required_count) - SUM(rostered_count) AS gap
      FROM vertex_iryo_staff_shift
      WHERE status='active'
      GROUP BY hospital_slug, dept_slug, ward_slug, shift_date, shift_block, role;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_iryo_staff_coverage_gap`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_iryo_drg_pnl_daily`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_iryo_admission_count_by_dept`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_iryo_los_by_drg_daily`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_iryo_bed_occupancy_now`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_iryo_encounter_in_bed`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_iryo_bed_in_ward`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_iryo_ward_in_dept`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_iryo_dept_in_hospital`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_iryo_health_kpi`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_iryo_staff_shift`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_iryo_drg_claim`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_iryo_encounter`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_iryo_staff`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_iryo_bed`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_iryo_ward`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_iryo_dept`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_iryo_hospital`.execute(db);
}
