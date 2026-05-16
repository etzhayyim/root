import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Lead ────────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_sales_lead (
      vertex_id VARCHAR PRIMARY KEY,
      lead_id VARCHAR NOT NULL,
      full_name VARCHAR NOT NULL,
      email VARCHAR,
      company VARCHAR,
      source VARCHAR,
      lead_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      status VARCHAR NOT NULL DEFAULT 'new',
      assigned_did VARCHAR,
      notes VARCHAR,
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Contact ─────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_sales_contact (
      vertex_id VARCHAR PRIMARY KEY,
      contact_id VARCHAR NOT NULL,
      full_name VARCHAR NOT NULL,
      email VARCHAR,
      phone VARCHAR,
      account_did VARCHAR,
      role VARCHAR,
      linkedin_url VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Account ─────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_sales_account (
      vertex_id VARCHAR PRIMARY KEY,
      account_id VARCHAR NOT NULL,
      company_name VARCHAR NOT NULL,
      domain VARCHAR,
      industry VARCHAR,
      employee_count INTEGER,
      arr_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      tier VARCHAR NOT NULL DEFAULT 'prospect',
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Opportunity ──────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_sales_opportunity (
      vertex_id VARCHAR PRIMARY KEY,
      opp_id VARCHAR NOT NULL,
      account_did VARCHAR,
      title VARCHAR NOT NULL,
      stage VARCHAR NOT NULL DEFAULT 'prospecting',
      probability_pct DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      amount_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      close_date VARCHAR,
      owner_did VARCHAR,
      lost_reason VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'open',
      created_at VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Activity ─────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_sales_activity (
      vertex_id VARCHAR PRIMARY KEY,
      activity_id VARCHAR NOT NULL,
      opp_did VARCHAR,
      contact_did VARCHAR,
      kind VARCHAR NOT NULL,
      summary VARCHAR NOT NULL,
      outcome VARCHAR,
      logged_by VARCHAR NOT NULL,
      logged_at VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Quote ────────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_sales_quote (
      vertex_id VARCHAR PRIMARY KEY,
      quote_id VARCHAR NOT NULL,
      opp_did VARCHAR NOT NULL,
      total_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      currency VARCHAR NOT NULL DEFAULT 'USD',
      valid_until VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'draft',
      line_items_json VARCHAR,
      llm_summary VARCHAR,
      created_at VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Forecast ─────────────────────────────────────────────────────────────

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_sales_forecast (
      vertex_id VARCHAR PRIMARY KEY,
      forecast_id VARCHAR NOT NULL,
      period VARCHAR NOT NULL,
      pipeline_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      weighted_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      closed_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      ai_forecast_usd DOUBLE PRECISION,
      confidence_pct DOUBLE PRECISION,
      notes VARCHAR,
      created_at VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 0,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`FLUSH`.execute(db);

  // ── Materialized Views ───────────────────────────────────────────────────

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_sales_pipeline_health AS
    SELECT
      stage,
      count(*) AS opp_count,
      sum(amount_usd) AS total_pipeline_usd,
      avg(probability_pct) AS avg_probability_pct,
      sum(amount_usd * probability_pct / 100.0) AS weighted_usd
    FROM vertex_open_sales_opportunity
    WHERE status = 'open'
    GROUP BY stage
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_sales_stage_velocity AS
    SELECT
      stage,
      count(*) AS opp_count,
      avg(amount_usd) AS avg_deal_size_usd,
      sum(CASE WHEN status = 'won' THEN 1 ELSE 0 END) AS won_count,
      sum(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) AS lost_count
    FROM vertex_open_sales_opportunity
    GROUP BY stage
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_sales_activity_summary AS
    SELECT
      opp_did,
      kind,
      count(*) AS activity_count
    FROM vertex_open_sales_activity
    GROUP BY opp_did, kind
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const mv of [
    "mv_open_sales_activity_summary",
    "mv_open_sales_stage_velocity",
    "mv_open_sales_pipeline_health",
  ]) {
    await sql`DROP MATERIALIZED VIEW IF EXISTS ${sql.raw(mv)}`.execute(db);
  }

  for (const t of [
    "vertex_open_sales_forecast",
    "vertex_open_sales_quote",
    "vertex_open_sales_activity",
    "vertex_open_sales_opportunity",
    "vertex_open_sales_account",
    "vertex_open_sales_contact",
    "vertex_open_sales_lead",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.raw(t)}`.execute(db);
  }
}
