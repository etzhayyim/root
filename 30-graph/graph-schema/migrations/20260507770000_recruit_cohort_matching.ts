import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Recruit cohort matching.
 *
 * This is intentionally cohort-first: it joins public job postings to aggregate
 * talent supply/demand signals and never reads or writes individual profile PII.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_recruit_match_proposal (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      proposal_id       VARCHAR NOT NULL,
      posting_id        VARCHAR NOT NULL,
      posting_vid       VARCHAR,
      cohort_vid        VARCHAR,
      isco_code         VARCHAR,
      country           VARCHAR,
      match_score       DOUBLE PRECISION,
      rationale         VARCHAR,
      proposal_state    VARCHAR,
      decision_reason   VARCHAR,
      created_at        VARCHAR,
      decided_at        VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_recruit_match_proposal_posting ON vertex_recruit_match_proposal (posting_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_recruit_match_proposal_state ON vertex_recruit_match_proposal (proposal_state, match_score)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_recruit_match_proposal_cohort ON vertex_recruit_match_proposal (isco_code, country)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_recruit_match_decision_event (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      event_id          VARCHAR NOT NULL,
      proposal_id       VARCHAR NOT NULL,
      proposal_state    VARCHAR NOT NULL,
      decision_reason   VARCHAR,
      decided_at        VARCHAR,
      decided_by        VARCHAR,
      privacy_mode      VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_recruit_match_decision_event_proposal ON vertex_recruit_match_decision_event (proposal_id, decided_at)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_recruit_match_for_posting (
      edge_id      VARCHAR PRIMARY KEY,
      src_vid      VARCHAR,
      dst_vid      VARCHAR,
      proposal_id  VARCHAR,
      posting_vid  VARCHAR,
      posting_id   VARCHAR,
      match_score  DOUBLE PRECISION,
      created_at   VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_recruit_match_for_posting ON edge_recruit_match_for_posting (proposal_id, posting_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_recruit_match_for_cohort (
      edge_id      VARCHAR PRIMARY KEY,
      src_vid      VARCHAR,
      dst_vid      VARCHAR,
      proposal_id  VARCHAR,
      cohort_vid   VARCHAR,
      isco_code    VARCHAR,
      country      VARCHAR,
      match_score  DOUBLE PRECISION,
      created_at   VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_recruit_match_for_cohort ON edge_recruit_match_for_cohort (proposal_id, isco_code, country)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_recruit_cohort_match_candidate AS
    SELECT
      p.vertex_id AS posting_vid,
      COALESCE(p.source_id, p.vertex_id) AS posting_id,
      p.title,
      p.employer_did,
      p.employer_name,
      p.source,
      p.source_url,
      p.isco_code,
      p.country,
      p.location,
      p.remote_allowed,
      p.employment_type,
      p.salary_min,
      p.salary_max,
      p.salary_currency,
      p.posted_at,
      c.vertex_id AS cohort_vid,
      c.source AS cohort_source,
      c.size_thousands AS supply_size_thousands,
      c.time_period AS cohort_period,
      d.vertex_id AS demand_forecast_vid,
      COALESCE(d.demand_score, 0.0) AS demand_score,
      COALESCE(d.press_signal_count, 0) AS press_signal_count,
      COALESCE(d.posting_count, 0) AS demand_posting_count,
      d.typical_salary,
      d.top_skills,
      (
        CASE WHEN p.employer_did IS NOT NULL AND p.employer_did <> '' THEN 20.0 ELSE 0.0 END
        + CASE WHEN p.source_url IS NOT NULL AND p.source_url <> '' THEN 10.0 ELSE 0.0 END
        + CASE WHEN c.size_thousands IS NOT NULL THEN 20.0 ELSE 0.0 END
        + LEAST(40.0, COALESCE(d.demand_score, 0.0) * 40.0)
        + LEAST(10.0, COALESCE(d.posting_count, 0)::DOUBLE PRECISION)
      ) AS match_score
    FROM vertex_job_posting p
    JOIN vertex_talent_cohort c
      ON c.isco_code = p.isco_code
     AND c.country = p.country
    LEFT JOIN vertex_demand_forecast d
      ON d.isco_code = p.isco_code
     AND d.country = p.country
    WHERE p.isco_code IS NOT NULL
      AND p.isco_code <> ''
      AND p.country IS NOT NULL
      AND p.country <> ''
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_mv_recruit_cohort_match_posting ON mv_recruit_cohort_match_candidate (posting_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_mv_recruit_cohort_match_filter ON mv_recruit_cohort_match_candidate (isco_code, country, match_score)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_mv_recruit_cohort_match_filter`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_mv_recruit_cohort_match_posting`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_recruit_cohort_match_candidate`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_recruit_match_for_cohort`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_recruit_match_for_cohort`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_recruit_match_for_posting`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_recruit_match_for_posting`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_recruit_match_decision_event_proposal`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_recruit_match_decision_event`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_recruit_match_proposal_cohort`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_recruit_match_proposal_state`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_recruit_match_proposal_posting`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_recruit_match_proposal`.execute(db);
}
