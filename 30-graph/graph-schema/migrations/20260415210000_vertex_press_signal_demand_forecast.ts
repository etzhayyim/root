import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Migration 20260415210000: vertex_press_signal + vertex_demand_forecast.
 *
 * vertex_press_signal — Press release hiring signals (PR TIMES, BusinessWire, Globe Newswire).
 *   Extracts trigger_type (hiring|expansion|funding|new_product|office_open) from RSS feeds.
 *   ISCO codes are matched from headline/body text against vertex_occupation names.
 *   ADR-0018: aggregate demand signals only — no individual PII stored.
 *
 * vertex_demand_forecast — Cohort × press signal → demand prediction.
 *   Computed from vertex_talent_cohort (supply) × press signal velocity (demand trigger)
 *   × vertex_occupation_bls (wage benchmark). Used to auto-generate engagement opportunities.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_press_signal (
      vertex_id         VARCHAR PRIMARY KEY,
      source            VARCHAR,
      source_url        VARCHAR,
      source_license    VARCHAR,
      company_name      VARCHAR,
      company_did       VARCHAR,
      headline          VARCHAR,
      body_snippet      VARCHAR,
      trigger_type      VARCHAR,
      trigger_score     DOUBLE PRECISION,
      isco_codes        VARCHAR,
      country           VARCHAR,
      published_at      VARCHAR,
      detected_at       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_demand_forecast (
      vertex_id           VARCHAR PRIMARY KEY,
      isco_code           VARCHAR,
      country             VARCHAR,
      period              VARCHAR,
      demand_score        DOUBLE PRECISION,
      supply_size_k       DOUBLE PRECISION,
      typical_salary      DOUBLE PRECISION,
      salary_currency     VARCHAR,
      engagement_types    VARCHAR,
      top_skills          VARCHAR,
      press_signal_count  BIGINT,
      posting_count       BIGINT,
      computed_at         VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_demand_forecast`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_press_signal`.execute(db);
}
